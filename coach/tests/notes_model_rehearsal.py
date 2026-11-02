"""Opt-in live model check with synthetic data and no database-write capability."""
import argparse
import copy
from datetime import datetime,timedelta
import json
from pathlib import Path
import sys
import tempfile
from zoneinfo import ZoneInfo

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from codex_client import CodexClient
from planning import validate_coach_note
from state import State
from tools import CoachTools,TOOLS
from test_notes import weekly_fixture


def run(runtime):
    config=json.loads((runtime/'config.json').read_text())
    data,_=weekly_fixture()
    for r in data['data']['monthly_program']:r['month_label']='Synthetic strength block'
    data['data']['exercises'][0].update(badge='Upper body')
    today=datetime.now(ZoneInfo(config['timezone'])).date()
    start=today+timedelta(days=(7-today.weekday())%7 or 7)
    class Fixture:
        environment='staging';user='codex_qa'
        def snapshot(self):return copy.deepcopy(data)
    with tempfile.TemporaryDirectory() as folder:
        state=State(Path(folder)/'state.sqlite')
        handler=CoachTools(Fixture(),state,config['timezone'])
        client=CodexClient(str(Path(config['codex_binary']).expanduser()),runtime,handler)
        instructions='\n\n'.join((Path(__file__).resolve().parents[1]/'instructions'/f).read_text()
                                  for f in ('COACH.md','DATA_CONTRACT.md'))
        try:
            client.account();thread=client.start(config['model'],instructions,TOOLS)
            result=client.run(thread,
                f'Synthetic QA athlete, not Brian. Prepare the next week starting {start}. '
                'All fixture dates, one Monday session, usual equipment, symptom-free recovery '
                'and no outstanding workouts are confirmed. Use the approved one-exercise '
                'Test press blueprint: 3 working sets of 5 at 40 kg, two-minute rests. '
                'This is an editorial acceptance test, not permission to change the prescription. '
                'There is no recent actual performance to invent. Keep the app note to one '
                'individually chosen short cue; evidence and analysis stay private. '
                'I trust you to coach: explain briefly why the three-set dose has a purpose '
                'rather than saying the template forces it. Do you need Codex approval to '
                'shorten the note? Use the proposal tool and give me a concise answer.',timeout=300)
            assert len(handler.proposals)==1,'Expected one validated synthetic week'
            p=handler.proposals[0];r=p['rows'][0]
            validate_coach_note(r['coach_notes'])
            assert r['suggested_sets']==[{'set':i,'reps':'5','weight':40,'rest':'2:00'}for i in (1,2,3)]
            assert p['coaching_evidence'][r['id']]['evidence']
            assert p['coaching_evidence'][r['id']]['evidence'] not in r['coach_notes']
            assert state.load_proposal(p['id'])['status']=='draft'
            print(json.dumps({'passed':True,'tools':result['tools'],
                'note':r['coach_notes'],'response':result['text'],
                'prescription_unchanged':True,'workout_database_written':False},ensure_ascii=False,indent=2))
        finally:client.close();state.db.close()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--runtime',type=Path,required=True)
    run(parser.parse_args().runtime.expanduser())
