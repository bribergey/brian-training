"""Opt-in ChatGPT-subscription rehearsal against in-memory synthetic data only."""
import copy
from datetime import datetime
import json
from pathlib import Path
import sys
import tempfile
from zoneinfo import ZoneInfo
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parent))
from codex_client import CodexClient
from tools import CoachTools, TOOLS
from state import State
from test_coach import snapshot

runtime=Path.home()/'.local/share/briq-coach'
source=Path(__file__).resolve().parents[1]
s=snapshot()
s['data']['monthly_program']=[{**r,'month_label':'Synthetic previous block','session_label':'Chest / Arms'} for r in s['data']['monthly_program']]
class Fixture:
    environment='staging';user='codex_qa'
    def snapshot(self):return copy.deepcopy(s)
with tempfile.TemporaryDirectory() as folder:
    state=State(Path(folder)/'state.sqlite')
    handler=CoachTools(Fixture(),state,'America/Los_Angeles')
    client=CodexClient('/Applications/ChatGPT.app/Contents/Resources/codex',runtime,handler)
    try:
        client.account()
        instructions='\n\n'.join((source/'instructions'/f).read_text() for f in ('COACH.md','DATA_CONTRACT.md'))
        thread=client.start('gpt-6-astra',instructions,TOOLS)
        result=client.run(thread,'This is a synthetic QA athlete, not Brian. Create a new monthly proposal using Test press only: one Monday training day, 3 straight sets of 5 at 40 kg with 2-minute rests for normal; 2 straight sets of 5 at 30 kg with 2-minute rests for deload. No warm-up catalog row exists. Goal strength, pain none, equipment known in 5 kg increments, no prior actual evidence. Set a concrete exercise effort target, progression condition and missed-target fallback. Treat these inputs as confirmed. Use the actual proposal tool, but do not apply or write a program. Do not ask about the personal hiking context: this fixture is synthetic.',timeout=600)
        assert len(handler.proposals)==1, 'Model did not produce a valid proposal'
        proposal=handler.proposals[0]
        assert proposal['kind']=='month' and len(proposal['rows'])==2
        assert state.load_proposal(proposal['id'])['status']=='draft'
        report={'passed':True,'tested_at':datetime.now(ZoneInfo('UTC')).isoformat(), 'tools':result['tools'],'response':result['text'],'proposal':proposal}
        path=runtime/'state/model-tool-rehearsal.json';path.write_text(json.dumps(report,indent=2));path.chmod(0o600)
        print(json.dumps({k:report[k] for k in ('passed','tools','response')},indent=2))
    finally:client.close();state.db.close()
