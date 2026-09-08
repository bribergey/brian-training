import copy
from datetime import date
import json
from pathlib import Path
import tempfile
import time
import unittest
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from planning import prepare, calendar, validate_sets, render_proposal
from data import Database, literal
from state import State
from service import Service
from telegram import Telegram


def row(day='A',week_type='normal'):
    return {'day':day,'week_type':week_type,'order_index':0,'exercise':'Test press',
        'session_label':'Chest / Arms','superset_group':None,'sets':3,'reps':'5',
        'weight':40,'rest':'2:00','suggested_sets':[
            {'set':i,'reps':'5','weight':40,'rest':'2:00'} for i in range(1,4)],
        'scheme':'straight','coach_notes':'Aim for controlled hard reps. Next target 3x6. Stop if painful.',
        'evidence':'No direct prior non-deload log; synthetic fixture.',
        'contract':{'scheme':'straight','reps':'5','effort':'Two reps in reserve',
            'progression':'Build to 3x6 then reassess load','fallback':'Repeat if last rep missed',
            'rationale':'Synthetic fixture only'}}


def snapshot():
    return {'fingerprint':'abc','data':{
        'program':[{'id':'old','week':5,'week_number':15,'scheduled_date':'2026-08-16',
                    'created_at':'2026-08-10T00:00:00','exercise':'Test press','session_key':'old'}],
        'monthly_program':[{'month':4,'status':'current','week_type':t,'day':'A','order_index':0,
            'exercise':'Test press','superset_group':None,'created_at':'2026-07-01T00:00:00'} for t in ('normal','deload')],
        'sessions':[],'user_profile':[{'training_days_per_week':1,'preferred_days':['Mon']}],
        'user_measurements':[],
        'exercises':[{'name':'Test press','unit':'kg','rep_type':'reps'}]}}


def month_args():return {'kind':'month','block_name':'Synthetic','summary':'Test the delivery workflow','rows':[row(week_type=t) for t in ('normal','deload')]}


class PlanningTests(unittest.TestCase):
    def test_month_assigns_identity_and_saves_complete_contract(self):
        p=prepare(snapshot(),month_args(),'codex_qa','staging',date(2026,9,8))
        self.assertEqual(p['month'],5)
        self.assertEqual({r['user_id'] for r in p['rows']},{'codex_qa'})
        self.assertEqual(json.loads(p['rows'][0]['internal_notes'])['suggested_sets'][2]['reps'],'5')
        self.assertIn('40 kg',render_proposal(p))

    def test_missing_weight_reps_and_set_count_are_rejected(self):
        for field,value in [('weight',None),('reps',''),('weight',float('nan'))]:
            args=month_args();args['rows'][0]['suggested_sets'][1][field]=value
            with self.assertRaises(ValueError):prepare(snapshot(),args,'codex_qa','staging',date(2026,9,8))
        args=month_args();args['rows'][0]['sets']=4
        with self.assertRaises(ValueError):prepare(snapshot(),args,'codex_qa','staging',date(2026,9,8))

    def test_scheme_inconsistency_rejected_and_top_backoff_supported(self):
        r=row();r['suggested_sets'][0]['weight']=45;r['weight']=45
        e={'rep_type':'reps','unit':'kg'}
        with self.assertRaises(ValueError):validate_sets(r,e,'straight')
        validate_sets(r,e,'top_backoff')

    def test_presets_are_the_single_source_for_display_summaries(self):
        args=month_args();args['rows'][0]['reps']='99';args['rows'][0]['contract']['reps']='100'
        p=prepare(snapshot(),args,'codex_qa','staging',date(2026,9,8))
        self.assertEqual(json.loads(p['rows'][0]['internal_notes'])['reps'],'5')
        for invalid in ('abc1','0','8-5','5-8','2.5','5 km'):
            r=row();r['suggested_sets'][0]['reps']=invalid
            with self.assertRaises(ValueError):validate_sets(r,{'rep_type':'reps','unit':'kg'},'straight')

    def test_deload_missing_slot_is_rejected(self):
        args=month_args();args['rows'].pop()
        with self.assertRaises(ValueError):prepare(snapshot(),args,'codex_qa','staging',date(2026,9,8))

    def test_block_complete_cannot_be_week_six(self):
        with self.assertRaisesRegex(ValueError,'complete'):calendar(snapshot()['data'],'2026-09-14')

    def test_new_month_resets_display_week_not_internal_identifier(self):
        d=snapshot()['data']
        for r in d['monthly_program']:r.update(month=5,created_at='2026-09-08T00:00:00')
        result=calendar(d,'2026-09-14')
        self.assertEqual((result['month'],result['week'],result['week_number']),(5,1,16))
        self.assertEqual(result['dates'],{'A':'2026-09-14'})

    def test_month_five_week_one_advances_after_write(self):
        d=snapshot()['data']
        for r in d['monthly_program']:r.update(month=5,created_at='2026-09-08T00:00:00')
        d['program']=[{**d['program'][0],'week':1,'week_number':16,'scheduled_date':'2026-09-14','created_at':'2026-09-09T00:00:00'}]
        self.assertEqual(calendar(d,'2026-09-21')['week'],2)

    def test_unknown_catalog_and_duplicate_slots_rejected(self):
        args=month_args();args['rows'][0]['exercise']='Imaginary press'
        with self.assertRaises(ValueError):prepare(snapshot(),args,'codex_qa','staging',date(2026,9,8))
        args=month_args();args['rows'].append(copy.deepcopy(args['rows'][0]))
        with self.assertRaises(ValueError):prepare(snapshot(),args,'codex_qa','staging',date(2026,9,8))

    def test_week_must_preserve_template_scheme(self):
        s=snapshot();p=prepare(s,month_args(),'codex_qa','staging',date(2026,9,8))
        s['data']['monthly_program']=[{**r,'created_at':'2026-09-08T00:00:00'} for r in p['rows']]
        args={'kind':'week','start_date':'2026-09-14','summary':'Synthetic progression','rows':[row()]}
        self.assertEqual(prepare(s,args,'codex_qa','staging',date(2026,9,8))['week'],1)
        args['rows'][0]['scheme']='top_backoff'
        with self.assertRaisesRegex(ValueError,'scheme differs'):prepare(s,args,'codex_qa','staging',date(2026,9,8))


class StorageTests(unittest.TestCase):
    def test_duplicate_inbox_and_superseded_approval_survive_restart(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'state.sqlite';s=State(path)
            for _ in range(2):s.enqueue({'update_id':42,'message':{'text':'test'}})
            s.proposal({'id':'one'});s.proposal_status('one','presented');s.proposal({'id':'two'})
            s.db.close();s=State(path)
            self.assertEqual(s.get('offset'),43)
            self.assertEqual(s.load_proposal('one')['status'],'superseded')
            self.assertEqual(s.pending()[0],42);s.finish(42);self.assertIsNone(s.pending())
            s.db.close()

    def test_sql_literal_escapes_quote_and_transaction_delimiter(self):
        self.assertEqual(literal("Coach's note"),"'Coach''s note'")
        p=prepare(snapshot(),month_args(),'codex_qa','staging',date(2026,9,8))
        p['rows'][0]['internal_notes']="'; end $briq_coach$; delete from training.sessions; --"
        class FakeDB(Database):
            def query(self,sql,readonly=True):
                self.sql=sql;return [{'rows':p['rows']}]
        db=FakeDB('not-a-token');db.apply(p)
        self.assertIn('do $briq_coachx$',db.sql)
        self.assertIn("user_id='codex_qa'",db.sql)
        self.assertIn('begin isolation level serializable',db.sql)


class ApprovalTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory()
        self.service=Service.__new__(Service)
        self.service.state=State(Path(self.folder.name)/'state.sqlite')
        self.service.config={'writes_enabled':True,'telegram_user_id':7,'telegram_chat_id':7}
        class FakeDB:
            environment='staging';user='codex_qa';calls=0
            def apply(db,p):
                db.calls+=1
                return {'verified':True,'row_count':len(p['rows']),'environment':db.environment,'proposal_id':p['id']}
        self.service.db=FakeDB()
        self.p=prepare(snapshot(),month_args(),'codex_qa','staging',date(2026,9,8))
        self.service.state.proposal(self.p)

    def tearDown(self):
        self.service.state.db.close();self.folder.cleanup()

    def test_sender_and_private_chat_are_both_required(self):
        good={'from':{'id':7},'chat':{'id':7,'type':'private'}}
        self.assertTrue(self.service.allowed({'message':good}))
        self.assertFalse(self.service.allowed({'message':{**good,'from':{'id':8}}}))
        self.assertFalse(self.service.allowed({'message':{**good,'chat':{'id':7,'type':'group'}}}))
        self.assertFalse(self.service.allowed({'callback_query':{'from':{'id':8},'message':good}}))

    def test_unpresented_expired_and_tampered_proposals_cannot_write(self):
        with self.assertRaises(ValueError):self.service.approve(self.p['id'])
        self.service.state.proposal_status(self.p['id'],'presented')
        with self.service.state.db:
            self.service.state.db.execute('update proposals set created=?',(time.time()-49*3600,))
        with self.assertRaisesRegex(ValueError,'expired'):self.service.approve(self.p['id'])
        with self.service.state.db:
            self.p['rows'][0]['weight']=99
            self.service.state.db.execute('update proposals set created=?,payload=?',(time.time(),json.dumps(self.p)))
        with self.assertRaisesRegex(ValueError,'integrity'):self.service.approve(self.p['id'])
        self.assertEqual(self.service.db.calls,0)

    def test_verified_approval_replay_uses_saved_receipt(self):
        self.service.state.proposal_status(self.p['id'],'presented')
        first=self.service.approve(self.p['id']);second=self.service.approve(self.p['id'])
        self.assertEqual(first,second);self.assertEqual(self.service.db.calls,1)

    def test_environment_and_write_switch_gate_approval(self):
        self.service.state.proposal_status(self.p['id'],'presented')
        self.service.config['writes_enabled']=False
        with self.assertRaisesRegex(ValueError,'not enabled'):self.service.approve(self.p['id'])
        self.service.config['writes_enabled']=True;self.service.db.environment='production'
        with self.assertRaisesRegex(ValueError,'environment'):self.service.approve(self.p['id'])
        self.assertEqual(self.service.db.calls,0)

    def test_telegram_unicode_chunks_are_within_limit(self):
        class FakeTelegram(Telegram):
            def __init__(self):self.sent=[]
            def call(self,method,payload):self.sent.append(payload);return True
        telegram=FakeTelegram();source='hello\n'+'🏋'*7000
        telegram.send(7,source,{'inline_keyboard':[]})
        self.assertEqual(''.join(x['text'] for x in telegram.sent),source)
        self.assertTrue(all(len(x['text'].encode('utf-16-le'))//2<=4096 for x in telegram.sent))
        self.assertTrue(all('reply_markup' not in x for x in telegram.sent[:-1]))


if __name__=='__main__':unittest.main()
