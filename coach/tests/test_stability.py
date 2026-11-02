import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from codex_client import CodexAuthError, CodexClient, CodexError
from health import read_report, report
from pin_runtime import ENTRY, pin, verify
from service import Service
from state import State


def update(identifier, text):
    return {'update_id': identifier, 'message': {'text': text,
        'from': {'id': 7}, 'chat': {'id': 7, 'type': 'private'}}}


class FakeTelegram:
    def __init__(self): self.sent=[]; self.updates=[]
    def send(self, chat, text, markup=None): self.sent.append(text)
    def call(self, method, payload, **kwargs):
        if method == 'getUpdates':
            result, self.updates = self.updates, []
            return result
        return True


class FakeCodex:
    def __init__(self, *args):
        self.proc=Mock(); self.proc.poll.return_value=None; self.closed=False
    def account(self): return {'type': 'chatgpt'}
    def start(self, model, instructions, tools, thread_id=None): return thread_id or 'new'
    def close(self): self.closed=True


class StabilityTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.root=Path(self.temp.name)
        (self.root/'state').mkdir()
        self.s=Service.__new__(Service)
        self.s.runtime=self.root; self.s.state=State(self.root/'state/coach.sqlite')
        self.s.config={'codex_binary':'missing-test-binary','model':'fixture',
            'timezone':'Asia/Shanghai','telegram_user_id':7,'telegram_chat_id':7,
            'telegram_enabled':True,'environment':'staging'}
        self.s.codex=None; self.s.tools=Mock(); self.s.tools.proposals=[]
        self.s.telegram=FakeTelegram(); self.s.db=Mock()
        self.s.state.set('thread_id','preserved-conversation')
        self.s.state.set('thread_has_started_turn',True)

    def tearDown(self): self.s.state.db.close(); self.temp.cleanup()

    def test_failed_auth_closes_client_and_later_reconnects_saved_conversation(self):
        bad=FakeCodex(); bad.account=Mock(side_effect=CodexAuthError('sign-in required'))
        with patch('service.CodexClient',return_value=bad):
            with self.assertRaises(CodexAuthError): self.s.engine()
        self.assertTrue(bad.closed); self.assertIsNone(self.s.codex)
        self.assertEqual(self.s.state.get('model_state'),'sign_in_required')
        good=FakeCodex()
        with patch('service.CodexClient',return_value=good): self.s.engine()
        self.assertEqual(self.s.thread,'preserved-conversation')
        self.assertEqual(self.s.state.get('model_state'),'ready')

    def test_dead_model_process_is_recreated_without_resetting_history(self):
        dead=FakeCodex(); dead.proc.poll.return_value=1; self.s.codex=dead
        with patch('service.CodexClient',FakeCodex): self.s.engine()
        self.assertTrue(dead.closed)
        self.assertEqual(self.s.thread,'preserved-conversation')

    def test_missing_runtime_does_not_drop_telegram_question_silently(self):
        message=update(1,'A synthetic question')
        self.s.state.enqueue(message)
        with patch('service.CodexClient',side_effect=FileNotFoundError('missing')):
            with self.assertLogs(level='ERROR'):
                self.s.process(self.s.state.pending(claim=True))
        self.assertIn('Got your message',self.s.telegram.sent[0])
        self.assertTrue(any('runtime needs repair' in text for text in self.s.telegram.sent))
        self.assertEqual(self.s.state.counts(),{'failed':1})
        self.s.db.apply.assert_not_called()

    def test_status_bypasses_busy_worker_and_reports_auth_failure(self):
        self.s.state.enqueue(update(1,'Long request'))
        self.s.state.pending(claim=True)
        self.s.state.set('active_since',time.time())
        self.s.state.set('model_state','sign_in_required')
        self.s.telegram.updates=[update(2,'/status')]
        with patch.object(self.s,'engine',side_effect=AssertionError('Status must not call the model')):
            self.s.poll_once()
        self.assertIn('sign-in needs restoring',self.s.telegram.sent[0])
        self.assertIn('Working on a request',self.s.telegram.sent[0])
        self.assertEqual(self.s.state.counts(),{'done':1,'processing':1})

    def test_polling_starts_even_when_model_cannot_start(self):
        self.s.telegram.updates=[update(1,'/status')]
        real_poll=self.s.poll_once
        def once(): real_poll(); raise KeyboardInterrupt()
        with patch('service.threading.Thread') as thread, patch.object(self.s,'poll_once',side_effect=once), patch.object(self.s,'engine',side_effect=CodexAuthError('no auth')):
            thread.return_value.is_alive.return_value=True
            with self.assertRaises(KeyboardInterrupt): self.s.run()
        self.assertIn('Telegram is online',self.s.telegram.sent[0])
        self.assertIn('not checked since restart',self.s.telegram.sent[0])

    def test_restart_does_not_replay_claimed_question_or_approved_write(self):
        self.s.state.enqueue(update(1,'question'))
        self.s.state.pending(claim=True)
        self.s.state.enqueue({'update_id':2,'callback_query':{
            'from':{'id':7},'data':'approve:existing-proposal',
            'message':{'chat':{'id':7,'type':'private'}}}})
        self.s.state.pending(claim=True)
        self.s.state.enqueue(update(3,'Not started yet'))
        self.s.state.db.close(); self.s.state=State(self.root/'state/coach.sqlite')
        self.s.state.recover_interrupted()
        with patch.object(self.s,'handle',side_effect=AssertionError('Must not replay')):
            self.s.recover()
        self.assertEqual(len(self.s.telegram.sent),2)
        self.assertEqual(self.s.state.counts(),{'failed':2,'pending':1})
        self.assertEqual(self.s.state.pending()[0],3)
        self.s.db.apply.assert_not_called()

    def test_recovery_notice_retry_does_not_interrupt_a_new_active_request(self):
        self.s.state.enqueue(update(1,'interrupted'))
        self.s.state.pending(claim=True); self.s.state.recover_interrupted()
        self.s.telegram.send=Mock(side_effect=OSError('offline'))
        with self.assertLogs(level='WARNING'): self.s.recover()
        self.s.state.enqueue(update(2,'new request')); self.s.state.pending(claim=True)
        self.s.telegram=FakeTelegram(); self.s.recover()
        self.assertEqual(self.s.state.counts(),{'failed':1,'processing':1})

    def test_control_queue_survives_restart_and_duplicate_delivery(self):
        message=update(1,'/status')
        self.s.state.enqueue(message,'control'); self.s.state.enqueue(message,'control')
        self.s.state.db.close(); self.s.state=State(self.root/'state/coach.sqlite')
        self.s.poll_once(); self.s.telegram.updates=[message]; self.s.poll_once()
        self.assertEqual(len(self.s.telegram.sent),1)
        self.assertEqual(self.s.state.counts(),{'done':1})

    def test_poll_failure_keeps_offset_and_can_recover(self):
        self.s.state.set('offset',10)
        with patch.object(self.s.telegram,'call',side_effect=OSError('offline')):
            with self.assertRaises(OSError): self.s.poll_once()
        self.assertEqual(self.s.state.get('offset'),10)
        self.s.telegram.updates=[update(10,'question')]; self.s.poll_once()
        self.assertEqual(self.s.state.get('offset'),11)
        self.assertEqual(self.s.state.pending()[0],10)

    def test_health_distinguishes_model_state_stale_poll_and_delivered_reply(self):
        now=time.time()
        for key,value in {'last_poll_ok':now,'worker_heartbeat':now,'model_state':'ready',
                          'last_model_success':now,'last_reply_delivered':now-10}.items(): self.s.state.set(key,value)
        self.assertEqual(read_report(self.root)['status'],'healthy')
        self.assertIn('telegram_poll_stale',report(self.s.state,now+121)['reasons'])
        self.s.state.set('model_state','sign_in_required')
        self.assertIn('sign_in_required',report(self.s.state)['reasons'])
        self.assertNotIn('content',json.dumps(report(self.s.state)))

    def test_initialize_failure_closes_spawned_process(self):
        process=Mock(); process.stdout=io.StringIO(''); process.poll.return_value=None
        with patch('codex_client.subprocess.Popen',return_value=process), patch.object(CodexClient,'request',side_effect=CodexError('initialize failed')):
            with self.assertRaises(CodexError): CodexClient('fixture',self.root)
        process.terminate.assert_called_once(); process.wait.assert_called_once()

    def test_managed_auth_requests_refresh_without_api_fallback(self):
        client=CodexClient.__new__(CodexClient)
        client.request=Mock(return_value={'account':None})
        with self.assertRaises(CodexAuthError): client.account()
        client.request.assert_called_once_with('account/read',{'refreshToken':True})

    def test_pinned_package_survives_source_removal_and_detects_tampering(self):
        source=self.root/'installed'; binary=source/ENTRY
        binary.parent.mkdir(parents=True)
        binary.write_text('#!/bin/sh\necho codex-cli-test\n'); binary.chmod(0o755)
        (source/'helper').write_text('versioned dependency')
        pinned,version=pin(source,self.root)
        self.assertEqual(pin(source,self.root)[0],pinned)
        shutil.rmtree(source)
        self.assertEqual(verify(pinned,self.root)['version'],version)
        pinned.write_text('changed')
        with self.assertRaisesRegex(ValueError,'integrity'): verify(pinned,self.root)


if __name__=='__main__': unittest.main()
