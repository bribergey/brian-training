import logging
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from codex_client import CodexClient
from progress import TurnProgress


class FakeTelegram:
    def __init__(self):self.sent=[];self.actions=[]
    def send(self,chat,text):self.sent.append(text)
    def call(self,method,payload,**kwargs):self.actions.append(method)


class FakeState:
    def __init__(self):self.messages=[]
    def message(self,role,text):self.messages.append((role,text))


class ProgressTests(unittest.TestCase):
    def test_only_user_facing_commentary_is_forwarded_and_final_remains_separate(self):
        client=CodexClient.__new__(CodexClient);client.notifications=[]
        client.request=lambda *args,**kwargs:{'turn':{'id':'test-turn'}}
        def item(kind,text,phase=None):
            return {'method':'item/completed','params':{'turnId':'test-turn','item':{'type':kind,'text':text,'phase':phase}}}
        messages=iter([
            item('agentMessage','Ignore another turn','commentary')|{'params':{'turnId':'old-turn','item':{'type':'agentMessage','text':'Ignore another turn','phase':'commentary'}}},
            item('reasoning','Private reasoning'),
            item('agentMessage','Reviewing comparable logs.','commentary'),
            item('agentMessage','Here is the finished result.','final_answer'),
            {'method':'turn/completed','params':{'turn':{'id':'test-turn','status':'completed'}}}])
        client.receive=lambda timeout:next(messages)
        progress=[]
        result=client.run('thread','Synthetic request',on_progress=progress.append)
        self.assertEqual(progress,['Reviewing comparable logs.'])
        self.assertEqual(result['text'],'Here is the finished result.')

    def test_acknowledgment_heartbeat_and_commentary_stop_before_final(self):
        telegram=FakeTelegram();state=FakeState()
        with TurnProgress(telegram,7,state) as progress:
            self.assertEqual(telegram.sent,['Got your message. I’m working on it.'])
            progress.commentary('Reviewing your previous block.')
            progress.tick(progress.last_notice+91)
            self.assertEqual(telegram.actions,['sendChatAction'])
            self.assertEqual(state.messages,[('assistant_progress','Reviewing your previous block.')])
            self.assertIn('still working',telegram.sent[-1])
        count=len(telegram.sent)
        progress.tick(progress.last_notice+200);progress.commentary('Too late')
        self.assertEqual(len(telegram.sent),count)
        self.assertFalse(progress.thread.is_alive())

    def test_progress_transport_failure_does_not_abort_coaching(self):
        class Unavailable(FakeTelegram):
            def send(self,*args):raise RuntimeError('Transport unavailable')
            def call(self,*args,**kwargs):raise RuntimeError('Transport unavailable')
        with self.assertLogs(level='WARNING'):
            with TurnProgress(Unavailable(),7,FakeState()) as progress:
                progress.commentary('Still working')
                progress.tick(progress.last_notice+91)


if __name__=='__main__':unittest.main()
