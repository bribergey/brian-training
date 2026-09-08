"""The complete model-facing capability surface: scoped reads and drafts."""
from datetime import datetime, timedelta
import json
from zoneinfo import ZoneInfo
from planning import calendar, prepare, render_proposal


def spec(name,description,properties,required=()):
    return {'type':'function','name':name,'description':description,'inputSchema':{
        'type':'object','properties':properties,'required':list(required),'additionalProperties':False}}


TOOLS=[
 spec('get_training_context','Read live profile, dated block/week overview, coaching memory and current local date. Do this before coaching or planning.',{}),
 spec('get_monthly_blueprint','Read all exercise slots and contracts for an existing month.',{'month':{'type':'integer'}},['month']),
 spec('get_exercise_history','Read complete prescribed/actual sets for an exact exercise, newest first. Includes comparable-history caveats; look beyond the last session.',{'exercise':{'type':'string'},'weeks':{'type':'integer','minimum':1,'maximum':52}},['exercise']),
 spec('get_exercise_catalog','Read exact exercise names, units and metadata; optionally filter names.',{'search':{'type':'string'}}),
 spec('get_week_calendar','Compute month/week/internal identifier and dates from live data and an explicit start date. Does not save anything.',{'start_date':{'type':'string'}},['start_date']),
 spec('get_program_rows','Read complete existing program rows for a specific internal week identifier. Use for exact adjustments; do not call the identifier a coaching week.',{'week_number':{'type':'integer'}},['week_number']),
 spec('prepare_program_proposal','Validate a complete weekly/monthly/adjustment draft. Returns errors to fix, or a proposal that the service presents for Brian approval. THIS DOES NOT WRITE WORKOUTS. Read the data contract in instructions.',{
     'kind':{'type':'string','enum':['week','month','adjustment']},'summary':{'type':'string'},
     'start_date':{'type':'string'},'block_name':{'type':'string'},'rows':{'type':'array','items':{'type':'object'}}},['kind','summary','rows']),
 spec('remember_coaching_fact','Save a dated preference, observed trend or decision with its source. Cannot change operating policy or program.',{'fact':{'type':'string'},'evidence':{'type':'string'},'review_date':{'type':['string','null']}},['fact','evidence'])
]


class CoachTools:
    def __init__(self,db,state,timezone):
        self.db=db;self.state=state;self.timezone=ZoneInfo(timezone)
        self.snapshot=None;self.proposals=[]

    def begin_turn(self):
        self.snapshot=None;self.proposals=[]

    def data(self):
        if self.snapshot is None:self.snapshot=self.db.snapshot()
        return self.snapshot['data']

    def __call__(self,name,args):
        if not isinstance(args,dict):raise ValueError('Tool arguments must be an object')
        if name=='remember_coaching_fact':return self.state.remember(**args)
        d=self.data()
        if name=='get_training_context':
            months={}
            for r in d['monthly_program']:
                m=months.setdefault(r['month'],{'month':r['month'],'label':r['month_label'],'status':r['status'],'days':{}})
                if r['week_type']=='normal':m['days'][r['day']]=r['session_label']
            weeks={}
            for r in d['program']:
                key=r.get('week_number');w=weeks.setdefault(key,{'internal_week_id':key,'display_week':r['week'],'dates':set()})
                if r.get('scheduled_date'):w['dates'].add(r['scheduled_date'])
            for w in weeks.values():w['dates']=sorted(w['dates'])
            return {'environment':self.db.environment,'user_id':self.db.user,
                'now':datetime.now(self.timezone).isoformat(),'timezone':str(self.timezone),
                'profile':d['user_profile'],'months':list(months.values()),
                'recent_weeks':sorted(weeks.values(),key=lambda w:w['dates'][-1] if w['dates'] else '',reverse=True)[:12],
                'latest_logged_date':max((s['date'] for s in d['sessions']),default=None),
                'measurements':sorted(d['user_measurements'],key=lambda r:str(r.get('date','')),reverse=True)[:20],
                'memory':self.state.memories()}
        if name=='get_monthly_blueprint':
            return [r for r in d['monthly_program'] if r['month']==args['month']]
        if name=='get_exercise_catalog':
            return [e for e in d['exercises'] if args.get('search','').lower() in e['name'].lower()]
        if name=='get_week_calendar':return calendar(d,args['start_date'])
        if name=='get_program_rows':return [r for r in d['program'] if r.get('week_number')==args['week_number']]
        if name=='get_exercise_history':
            weeks=args.get('weeks',12)
            if type(weeks) is not int or not 1<=weeks<=52:raise ValueError('History window must be 1–52 weeks')
            # Anchor to the latest log when there is a training break; expose both dates.
            today=datetime.now(self.timezone).date()
            cutoff=(today-timedelta(weeks=weeks)).isoformat()
            prescriptions={r.get('session_key'):r for r in d['program'] if r['exercise']==args['exercise']}
            history=[]
            for s in sorted(d['sessions'],key=lambda s:(s['date'],s.get('logged_at') or ''),reverse=True):
                if s['date']<cutoff or s.get('skipped'):continue
                for e in s.get('exercises') or []:
                    if (e.get('name') or e.get('exercise'))==args['exercise']:
                        p=prescriptions.get(s.get('program_session_key'))
                        history.append({'date':s['date'],'session_id':s['id'],'actual':e,
                            'session_notes':s.get('notes'),'prescribed':p,
                            'deload':p.get('week')==5 if p else None,
                            'block_phase':'Unclassified unless supported by dated block/history context'})
            return {'exercise':args['exercise'],'since':cutoff,'history':history,
                'caveat':'Do not infer RIR, form, machine comparability or diagnosis from completed reps. Ask for older history up to 52 weeks when needed.'}
        if name=='prepare_program_proposal':
            p=prepare(self.snapshot,args,self.db.user,self.db.environment,datetime.now(self.timezone).date())
            self.state.proposal(p);self.proposals=[p]
            return {'proposal_id':p['id'],'validated':True,'saved_to_workout_database':False,
                'month':p.get('month'),'week':p.get('week'),'row_count':len(p['rows']),
                'next':'The service will send a full proposal and approval button after this turn. Tell Brian it is proposed, not saved.'}
        raise ValueError('Unknown coach tool')
