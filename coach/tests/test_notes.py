import copy
from datetime import date
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from data import Database
from planning import prepare, render_proposal, validate_coach_note
from state import State
from tools import CoachTools
from test_coach import month_args, row, snapshot


def weekly_fixture():
    snap=snapshot()
    month=prepare(snap,month_args(),'codex_qa','staging',date(2026,9,8))
    snap['data']['monthly_program']=[{**r,'created_at':'2026-09-08T00:00:00'}for r in month['rows']]
    args={'kind':'week','start_date':'2026-09-14','summary':'A purposeful synthetic progression.','rows':[row()]}
    return snap,args


class NotesTests(unittest.TestCase):
    def test_later_coaching_reads_latest_applied_reason_without_changing_app_note(self):
        snap,args=weekly_fixture();p=prepare(snap,args,'codex_qa','staging',date(2026,9,8))
        saved={**p['rows'][0],'session_key':'fixture-key'}
        snap['data']['program']=[saved]
        from datetime import datetime
        snap['data']['sessions']=[{'id':'logged','date':datetime.now().date().isoformat(),
            'program_session_key':'fixture-key','exercises':[{'name':saved['exercise']}]}]
        class Fixture:
            def snapshot(self):return snap
        with tempfile.TemporaryDirectory() as folder:
            state=State(Path(folder)/'state.sqlite')
            try:
                state.proposal(p);state.proposal_status(p['id'],'applied')
                revised=copy.deepcopy(p);revised['id']='adjusted'
                revised['coaching_evidence'][saved['id']]['evidence']='Latest approved reasoning'
                state.proposal(revised);state.proposal_status(revised['id'],'applied')
                unapproved=copy.deepcopy(revised);unapproved['id']='unsaved'
                unapproved['coaching_evidence'][saved['id']]['evidence']='Unapproved draft reasoning'
                state.proposal(unapproved)
                # A legacy receipt without separate evidence stays compatible.
                state.proposal({'id':'legacy'});state.proposal_status('legacy','applied')
                handler=CoachTools(Fixture(),state,'UTC')
                row=handler('get_program_rows',{'week_number':saved['week_number']})[0]
                history=handler('get_exercise_history',{'exercise':saved['exercise']})['history'][0]
                for result in (row,history['prescribed']):
                    self.assertEqual(result['private_coaching_evidence']['evidence'],'Latest approved reasoning')
                    self.assertEqual(result['coach_notes'],saved['coach_notes'])
                self.assertNotIn('private_coaching_evidence',snap['data']['program'][0])
            finally:state.db.close()

    def test_evidence_stays_private_and_saved_field_is_authored_note(self):
        snap,args=weekly_fixture()
        note='Warm up 20×8, 30×4 kg; keep two reps spare.'
        evidence='2026-09-01: 40 kg 5/5/5; this is private analysis. '*40
        args['rows'][0].update(coach_notes=note,evidence=evidence)
        p=prepare(snap,args,'codex_qa','staging',date(2026,9,8))
        r=p['rows'][0]
        self.assertEqual(r['coach_notes'],note)
        self.assertEqual(p['coaching_evidence'][r['id']]['evidence'],evidence)
        self.assertNotIn(evidence,render_proposal(p))
        original=p.pop('digest')
        self.assertEqual(original,hashlib.sha256(json.dumps(p,sort_keys=True,allow_nan=False).encode()).hexdigest())
        p['coaching_evidence'][r['id']]['evidence']='tampered'
        self.assertNotEqual(original,hashlib.sha256(json.dumps(p,sort_keys=True,allow_nan=False).encode()).hexdigest())

    def test_adjustment_keeps_evidence_and_reason_out_of_note(self):
        snap,args=weekly_fixture();p=prepare(snap,args,'codex_qa','staging',date(2026,9,8))
        saved={**p['rows'][0],'session_key':'fixture-key'};snap['data']['program']=[saved]
        changed={**saved,'scheme':'straight','coach_notes':'Keep the bar close on the lowering phase.',
                 'evidence':'Previous synthetic session: 40 kg 5/5/5.', 'change_reason':'Shorten the displayed instruction'}
        a=prepare(snap,{'kind':'adjustment','summary':'Shorter note','rows':[changed]},'codex_qa','staging',date(2026,9,8))
        self.assertEqual(a['rows'][0]['coach_notes'],changed['coach_notes'])
        self.assertEqual(a['coaching_evidence'][saved['id']]['change_reason'],changed['change_reason'])
        self.assertEqual(a['rows'][0]['suggested_sets'],saved['suggested_sets'])

    def test_rejects_walls_of_text_without_truncating_and_allows_varied_short_notes(self):
        for invalid in ['Cue\nAnother cue','Control the lowering. Keep two reps spare.',
                        'Warm up; '+('do this next; '*35),'word '*41,'x'*241]:
            with self.subTest(invalid=invalid[:30]),self.assertRaises(ValueError):validate_coach_note(invalid)
        for note in ['Stop before your lower back arches.',
                     'Last time was easy—aim for twenty without bouncing.',
                     'Warm up 12.5×8 kg per hand; leave two reps spare.',
                     'Use a stable box for foot-assisted reps if strict pull-ups stop.']:
            validate_coach_note(note)

    def test_warmup_row_has_same_readability_guard(self):
        snap,args=weekly_fixture()
        snap['data']['exercises'][0].update(rep_type='info')
        for template in snap['data']['monthly_program']:
            contract=json.loads(template['internal_notes']);contract['scheme']='warmup'
            template['internal_notes']=json.dumps(contract)
        args['rows'][0].update(scheme='warmup',suggested_sets=None,sets=None,
                              coach_notes='Walk easily for five minutes. Then do squats.')
        with self.assertRaisesRegex(ValueError,'one sentence'):
            prepare(snap,args,'codex_qa','staging',date(2026,9,8))

    def test_backend_sql_writes_exact_note_and_never_private_evidence(self):
        snap,args=weekly_fixture()
        args['rows'][0]['evidence']='PRIVATE_EVIDENCE_MARKER'
        p=prepare(snap,args,'codex_qa','staging',date(2026,9,8))
        class FakeDB(Database):
            def query(self,sql,readonly=True):self.sql=sql;return [{'rows':copy.deepcopy(p['rows'])}]
        db=FakeDB('fixture');db.apply(p)
        self.assertIn(p['rows'][0]['coach_notes'],db.sql)
        self.assertNotIn('PRIVATE_EVIDENCE_MARKER',db.sql)


if __name__=='__main__':unittest.main()
