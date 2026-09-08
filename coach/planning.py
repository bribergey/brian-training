"""Deterministic proposal construction and per-set validation."""
from datetime import date, timedelta
import hashlib
import json
import math
import re
import uuid

from data import PROGRAM_FIELDS, MONTH_FIELDS


def require(condition, message):
    if not condition:
        raise ValueError(message)


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def iso_date(value):
    require(isinstance(value, str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}', value), 'Use an exact YYYY-MM-DD date')
    return date.fromisoformat(value)


def current_month(data):
    values = {r['month'] for r in data['monthly_program'] if r['status'] == 'current'}
    require(len(values) == 1, 'Exactly one current month is required; PM must resolve the state')
    return next(iter(values))


def calendar(data, start_date):
    month = current_month(data)
    rows = data['program']
    require(rows, 'No programming baseline; PM must establish initial block/week')
    dated = [r for r in rows if r.get('scheduled_date') and r.get('week_number') is not None]
    require(dated, 'No dated programming baseline')
    last_date = max(r['scheduled_date'] for r in dated)
    latest = [r for r in dated if r['scheduled_date'] == last_date]
    require(len({(r['week'],r['week_number']) for r in latest}) == 1, 'Ambiguous latest week')
    # A newly created month has no weekly rows yet. Its creation time must be newer
    # than every existing program row, rather than relying on MAX(week_number).
    template_created = min(r.get('created_at') or '' for r in data['monthly_program'] if r['month'] == month)
    latest_created = max(r.get('created_at') or '' for r in rows)
    week = 1 if template_created > latest_created else latest[0]['week'] + 1
    require(1 <= week <= 5, 'Current block is complete; prepare a new monthly blueprint first')
    start = iso_date(start_date)
    require(start > iso_date(last_date), 'New week must start after the last scheduled week; handle outstanding sessions explicitly')
    profile = data['user_profile'][0] if data['user_profile'] else {}
    preferred = profile.get('preferred_days') or []
    require(preferred and len(set(preferred)) == len(preferred), 'Preferred training days need clarification')
    require(profile.get('training_days_per_week') == len(preferred), 'Profile frequency and preferred days disagree')
    weekdays = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
    require(all(d in weekdays for d in preferred), 'Unrecognized preferred weekday')
    dates = [start + timedelta(days=i) for i in range(7) if weekdays[(start + timedelta(days=i)).weekday()] in preferred]
    template = [r for r in data['monthly_program'] if r['month']==month and r['week_type']==('deload' if week==5 else 'normal')]
    days = sorted({r['day'] for r in template})
    require(len(days)==len(dates), 'Monthly split and profile frequency disagree')
    return {'month':month, 'week':week, 'week_number':max(r['week_number'] for r in dated)+1,
            'dates':dict(zip(days,[d.isoformat() for d in dates]))}


def validate_sets(row, exercise, scheme):
    if exercise['rep_type'] == 'info':
        require(nonempty(row.get('coach_notes')), 'Warm-up needs an actual routine')
        require(row.get('suggested_sets') in (None, []), 'Warm-up working sets must be empty')
        return
    sets = row.get('suggested_sets')
    require(isinstance(sets,list) and len(sets)>0, 'Missing suggested_sets for '+row['exercise'])
    require(type(row.get('sets')) is int and row['sets']==len(sets), 'Working set count does not match presets')
    require(nonempty(row.get('reps')), 'Missing row reps')
    require(number(row.get('weight')) and row['weight']>=0, 'Missing/invalid row weight')
    require(nonempty(row.get('rest')), 'Missing rest target')
    require(nonempty(row.get('coach_notes')), 'Missing coach notes')
    for index, s in enumerate(sets,1):
        require(set(s)=={'set','reps','weight','rest'}, 'Each set needs exactly set, reps, weight, rest')
        require(type(s['set']) is int and s['set']==index, 'Set numbers must be consecutive')
        require(nonempty(s['reps']), 'Every set needs an explicit positive rep/time target')
        # The app uses numeric inputs. Ranges or unit suffixes silently render blank.
        require(re.fullmatch(r'\d+(?:\.\d+)?',s['reps']) is not None,
                'Each preset needs one numeric target; put ranges and units in coaching notes')
        amount=float(s['reps'])
        require(math.isfinite(amount) and amount>0, 'Set targets must be positive')
        if exercise['rep_type']=='reps':
            require(amount.is_integer(), 'Reps must be whole numbers')
        require(number(s['weight']) and s['weight']>=0, 'Every set needs a numeric weight; use 0 for bodyweight')
        require(nonempty(s['rest']) and re.fullmatch(r'\d{1,2}:[0-5]\d',s['rest']), 'Set rest must be M:SS')
        if exercise['unit']=='BW':
            require(s['weight']==0, 'Bodyweight exercise must use 0; weighted variants require correct catalog units')
    weights=[s['weight'] for s in sets]
    if scheme=='straight':
        require(len(set(weights))==1, 'Straight sets contain inconsistent weights')
    elif scheme=='top_backoff':
        require(len(weights)>=2 and weights[0]>max(weights[1:]) and len(set(weights[1:]))==1,
                'Top/back-off scheme needs a heavier first set and consistent lighter back-off sets')
    elif scheme=='ramp':
        require(weights==sorted(weights) and len(set(weights))>1, 'Ramp scheme must increase load')
    else:
        require(scheme=='bodyweight' and exercise['unit']=='BW' and all(w==0 for w in weights), 'Bodyweight scheme requires an unweighted bodyweight exercise')
    require(row['weight']==max(weights), 'Row summary weight must equal the highest prescribed working weight')
    # Derive display summaries from the exact presets: no second conflicting truth.
    targets=[s['reps'] for s in sets]
    row['reps']=targets[0] if len(set(targets))==1 else ' / '.join(targets)
    rests=[s['rest'] for s in sets]
    row['rest']=rests[0] if len(set(rests))==1 else ' / '.join(rests)


def template_contract(row):
    try:
        contract=json.loads(row.get('internal_notes') or '{}')
    except ValueError:
        return None
    return contract if isinstance(contract,dict) and contract.get('version')==2 else None


def prepare(snapshot, args, user, environment, today):
    require(isinstance(args,dict), 'Proposal must be an object')
    kind=args.get('kind')
    require(kind in ('week','month','adjustment'), 'Choose week, month or adjustment')
    data=snapshot['data']; catalog={e['name']:e for e in data['exercises']}
    proposal_id=str(uuid.uuid4())
    raw=args.get('rows')
    require(isinstance(raw,list) and 0<len(raw)<=250, 'Provide 1–250 complete exercise rows')
    require(nonempty(args.get('summary')), 'A coaching analysis/summary is required')
    p={'id':proposal_id,'kind':kind,'fingerprint':snapshot['fingerprint'],'rows':[],
       'summary':args['summary'],'environment':environment,'user_id':user,
       'units':{e['name']:e['unit'] for e in data['exercises']}}
    if kind=='week':
        meta=calendar(data,args.get('start_date'));p.update(meta)
        require(iso_date(args['start_date'])>=today, 'New weeks cannot start in the past')
    elif kind=='month':
        p['previous_month']=current_month(data)
        p['month']=max(r['month'] for r in data['monthly_program'])+1
        require(nonempty(args.get('block_name')), 'Monthly blueprint needs a block name')
        p['month_label']=f"Month {p['month']} — {args['block_name']}"
    else:
        require(all(nonempty(r.get('id')) for r in raw), 'Adjustment needs exact existing row IDs')
    template={(r['day'],r['order_index']):r for r in data['monthly_program']
        if r['month']==p.get('month') and r['week_type']==('deload' if p.get('week')==5 else 'normal')}
    existing={r['id']:r for r in data['program']}
    slots=set()
    for index, item in enumerate(raw):
        require(isinstance(item,dict), 'Each row must be an object')
        require(item.get('exercise') in catalog, 'Exercise missing from shared catalog; PM must review additions')
        e=catalog[item['exercise']]
        require(nonempty(item.get('day')) and type(item.get('order_index')) is int and item['order_index']>=0, 'Day and nonnegative order_index required')
        slot=(item.get('week_type') if kind=='month' else None,item['day'],item['order_index'])
        require(slot not in slots,'Duplicate exercise slot');slots.add(slot)
        fields=MONTH_FIELDS if kind=='month' else PROGRAM_FIELDS
        row={k:item.get(k) for k in fields}
        row.update(id=str(uuid.uuid5(uuid.UUID(proposal_id),str(index))),user_id=user)
        require(nonempty(row['session_label']) and not re.search(r'\b(?:month|week|upper [a-d]|lower [a-d]|day [a-d])\b',row['session_label'],re.I), 'Use a descriptive day-focus label')
        require(row['superset_group'] is None or nonempty(row['superset_group']), 'Invalid superset group')
        if kind=='month':
            require(item.get('week_type') in ('normal','deload'), 'Month needs normal and deload templates')
            contract=item.get('contract')
            require(isinstance(contract,dict) and all(nonempty(contract.get(k)) for k in ['scheme','reps','effort','progression','fallback','rationale']), 'Monthly rows need scheme/reps/effort/progression/fallback/rationale')
            # Validate the fully specified example week even though monthly DB rows
            # have no reps or per-set columns. Persist those targets in internal_notes.
            check={**item,'coach_notes':contract['rationale']}
            validate_sets(check,e,contract['scheme'])
            contract={**contract,'version':2,'reps':check.get('reps'),'suggested_sets':item.get('suggested_sets')}
            row.update(month=p['month'],month_label=p['month_label'],status='current',internal_notes=json.dumps(contract,allow_nan=False))
        else:
            if kind=='week':
                source=template.get((row['day'],row['order_index']))
                require(source and source['exercise']==row['exercise'] and source.get('superset_group')==row['superset_group'], 'Week must match monthly exercise slots and supersets')
                contract=template_contract(source)
                require(contract is not None, 'Monthly template has no reviewed set contract; prepare the new monthly blueprint first')
                require(item.get('scheme')==contract['scheme'], 'Weekly set scheme differs from monthly blueprint')
                row.update(week=p['week'],week_number=p['week_number'],scheduled_date=p['dates'][row['day']])
            else:
                source=existing.get(item['id']);require(source is not None,'Adjustment row not found')
                require(not any(s.get('program_session_key')==source.get('session_key') for s in data['sessions']), 'Cannot edit a logged/skipped session')
                for k in ('id','week','week_number','day','scheduled_date','order_index','exercise','superset_group'):
                    require(item.get(k,source[k])==source[k], 'Adjustment cannot move or replace exercise slots')
                    row[k]=source[k]
                require(nonempty(item.get('change_reason')), 'Adjustment requires a reason')
                require(iso_date(row['scheduled_date'])>=today, 'Cannot adjust a past workout')
            validate_sets(row,e,item.get('scheme'))
            require(e['rep_type']=='info' or nonempty(item.get('evidence')), 'Every exercise needs its actual prior performance evidence or an explicit missing-evidence statement')
            if e['rep_type']!='info':
                row['coach_notes']=item['evidence']+'\n'+row['coach_notes']
        p['rows'].append(row)
    if kind=='week':
        require({(r['day'],r['order_index']) for r in p['rows']}==set(template), 'Weekly proposal omits or adds monthly exercise slots')
    if kind=='month':
        normal={(r['day'],r['order_index']):(r['exercise'],r['superset_group']) for r in p['rows'] if r['week_type']=='normal'}
        deload={(r['day'],r['order_index']):(r['exercise'],r['superset_group']) for r in p['rows'] if r['week_type']=='deload'}
        require(normal and normal==deload,'Deload must mirror normal exercise slots and supersets')
        profile=data['user_profile'][0] if data['user_profile'] else {}
        require(len({k[0] for k in normal})==profile.get('training_days_per_week'), 'Monthly split must match confirmed profile frequency')
    # One label and date per day; never use arbitrary model-generated counters.
    for day in {r['day'] for r in p['rows']}:
        require(len({r['session_label'] for r in p['rows'] if r['day']==day})==1,'Inconsistent day labels')
    p['digest']=hashlib.sha256(json.dumps(p,sort_keys=True,allow_nan=False).encode()).hexdigest()
    return p


def render_proposal(p):
    title=p.get('month_label') or f"Month {p.get('month','current')}, Week {p.get('week','adjustment')}"
    lines=[f"PROPOSED — {title}",p['summary'],f"{p['environment']} • {len(p['rows'])} exercise rows"]
    for r in sorted(p['rows'],key=lambda r:(r.get('week_type',''),r['day'],r['order_index'])):
        label=(r.get('scheduled_date') or r.get('week_type'))+' / '+r['day']+' / '+r['session_label']
        lines.append('\n'+label+'\n'+r['exercise'])
        contract=template_contract(r) if p['kind']=='month' else None
        sets=contract.get('suggested_sets') if contract else r.get('suggested_sets')
        if sets:
            lines.extend(f"Set {s['set']}: {s['reps']} @ {s['weight']} {p.get('units',{}).get(r['exercise'],'')} • rest {s['rest']}" for s in sets)
        lines.append(r.get('coach_notes') or (contract.get('rationale') if contract else '') or '')
        if contract:
            lines.extend(f"{key}: {contract[key]}" for key in ('scheme','effort','progression','fallback'))
    lines.append('\nNothing saved yet. Approve only if these exact exercises, sets and dates are right.')
    return '\n'.join(lines)
