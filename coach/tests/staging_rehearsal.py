"""Explicit synthetic staging rehearsal; never writes Brian's rows.

Refresh the documented QA fixture first and again after browser verification.
Run from the repo: python3 coach/tests/staging_rehearsal.py --runtime PATH
"""
import argparse
import copy
from datetime import date,timedelta
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from data import Database
from planning import prepare,template_contract


def run(runtime):
    secret=json.loads((runtime/'secrets.json').read_text())
    db=Database(secret['supabase_access_token'],'staging')
    production=Database(secret['supabase_access_token'],'production')
    before=production.snapshot()['fingerprint']
    today=date.today()
    start=today+timedelta(days=(7-today.weekday())%7 or 7)
    contract={'scheme':'straight','reps':'5','effort':'Synthetic test target',
              'progression':'Synthetic test; do not perform','fallback':'Synthetic test; do not perform',
              'rationale':'QA fixture only; validates exact persistence'}
    rows=[]
    for week_type in ['normal','deload']:
        for day in 'ABCD':
            weight=40 if week_type=='normal' else 25
            count=3 if week_type=='normal' else 2
            rows.append({'week_type':week_type,'day':day,'order_index':0,
                'exercise':'Barbell bench press','session_label':'QA Chest / Arms','superset_group':None,
                'sets':count,'reps':'5','weight':weight,'rest':'2:00',
                'suggested_sets':[{'set':i,'reps':'5','weight':weight,'rest':'2:00'} for i in range(1,count+1)],
                'contract':contract.copy()})
    p=prepare(db.snapshot(),{'kind':'month','block_name':'Synthetic Coach QA',
        'summary':'Synthetic end-to-end persistence rehearsal','rows':rows},db.user,db.environment,today)
    month_receipt=db.apply(p);assert db.apply(p)==month_receipt
    snap=db.snapshot();normal=[r for r in snap['data']['monthly_program'] if r['month']==p['month'] and r['week_type']=='normal']
    week_rows=[]
    for r in normal:
        c=template_contract(r)
        week_rows.append({**r,'reps':c['reps'],'rest':'2:00','suggested_sets':c['suggested_sets'],
                          'scheme':c['scheme'],'coach_notes':'Synthetic session. Do not perform.',
                          'evidence':'No actual performance: synthetic QA fixture.'})
    w=prepare(snap,{'kind':'week','start_date':start.isoformat(),'summary':'QA new week','rows':week_rows},db.user,db.environment,today)
    week_receipt=db.apply(w);assert db.apply(w)==week_receipt
    snap=db.snapshot();saved=[r for r in snap['data']['program'] if r['id']==w['rows'][0]['id']][0]
    adjust={**saved,'weight':45,'suggested_sets':[dict(s,weight=45) for s in saved['suggested_sets']],
            'scheme':'straight','evidence':'Synthetic QA comparison only.','change_reason':'Test a targeted adjustment'}
    a=prepare(snap,{'kind':'adjustment','summary':'QA adjustment','rows':[adjust]},db.user,db.environment,today)
    # A separate scoped staging edit invalidates the source snapshot.
    db.query("update training.program_staging set coach_notes='Synthetic concurrent change' where user_id='codex_qa' and id='"+saved['id']+"'::uuid",readonly=False)
    try:db.apply(a)
    except ValueError as exc:assert 'STALE_PROPOSAL' in str(exc)
    else:raise AssertionError('Stale proposal was not rejected')
    a=prepare(db.snapshot(),{'kind':'adjustment','summary':'QA adjustment refreshed','rows':[adjust]},db.user,db.environment,today)
    adjustment_receipt=db.apply(a);assert db.apply(a)==adjustment_receipt
    after=production.snapshot()['fingerprint'];assert before==after,'Brian data changed during rehearsal; investigate'
    report={'month':month_receipt,'week':week_receipt,'adjustment':adjustment_receipt,
        'idempotent_replays':3,'stale_proposal_rejected':True,'brian_snapshot_unchanged':True,
        'app_url':'https://briqtraining.com/staging/app/','week_start':start.isoformat()}
    (runtime/'state/staging-rehearsal.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--runtime',type=Path,required=True)
    run(parser.parse_args().runtime)
