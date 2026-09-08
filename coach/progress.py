"""Visible progress for long Codex turns; transport failures never abort coaching."""
import logging
import threading
import time


class TurnProgress:
    def __init__(self, telegram, chat_id, state):
        self.telegram=telegram;self.chat_id=chat_id;self.state=state
        self.stop=threading.Event();self.lock=threading.Lock()
        self.last_notice=time.monotonic();self.thread=None

    def notice(self, text, record=False):
        if not text or self.stop.is_set():return
        with self.lock:
            if self.stop.is_set():return
            try:
                self.telegram.send(self.chat_id,text)
                self.last_notice=time.monotonic()
                if record:self.state.message('assistant_progress',text)
            except Exception:
                logging.warning('Coach progress notice unavailable')

    def commentary(self, text):
        # Only completed, user-facing commentary enters here. Never reasoning.
        self.notice(text,record=True)

    def tick(self, now=None):
        if self.stop.is_set():return
        try:self.telegram.call('sendChatAction',{'chat_id':self.chat_id,'action':'typing'},timeout=8)
        except Exception:logging.info('Typing indicator unavailable')
        if (time.monotonic() if now is None else now)-self.last_notice>=90:
            self.notice('I’m still working on your request. I’ll send the result when it’s ready; you don’t need to resend it.')

    def _run(self):
        while not self.stop.wait(4):self.tick()

    def __enter__(self):
        self.notice('Got your message. I’m working on it.')
        self.thread=threading.Thread(target=self._run,daemon=True)
        self.thread.start()
        return self

    def __exit__(self,*args):
        self.stop.set()
        # If a transport request is in flight, wait for it before the final reply.
        if self.thread:self.thread.join(timeout=55)
