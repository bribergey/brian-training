"""Small stdio client for the pinned Codex app-server protocol.

The model has no environment access or credentials. Only the explicitly supplied
dynamic tools and hosted web search are available. No write tool is registered.
"""
import json
import os
from pathlib import Path
import queue
import subprocess
import threading
import time


class CodexError(RuntimeError):
    pass


class CodexClient:
    def __init__(self, binary, runtime, handler=None):
        self.runtime = Path(runtime)
        self.handler = handler
        # Do not inherit database, Telegram, OpenRouter, or OpenAI API secrets.
        env = {k: os.environ[k] for k in ('HOME', 'PATH', 'TMPDIR', 'LANG',
               'SSL_CERT_FILE', 'SSL_CERT_DIR') if k in os.environ}
        env['CODEX_HOME'] = str(self.runtime / 'codex')
        self.proc = subprocess.Popen([binary, 'app-server', '--stdio'], env=env,
            cwd=self.runtime / 'workspace', stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1)
        self.messages = queue.Queue()
        self.serial = 0
        self.notifications = []
        threading.Thread(target=self._reader, daemon=True).start()
        self.request('initialize', {'clientInfo': {'name': 'briq_coach',
            'title': 'BRIQ Training Coach', 'version': '0.1.0'},
            'capabilities': {'experimentalApi': True}})
        self.send({'method': 'initialized'})

    def _reader(self):
        try:
            for line in self.proc.stdout:
                try:
                    self.messages.put(json.loads(line))
                except ValueError:
                    continue
        finally:
            self.messages.put(None)

    def send(self, message):
        self.proc.stdin.write(json.dumps(message) + '\n')
        self.proc.stdin.flush()

    def receive(self, timeout):
        try:
            message = self.messages.get(timeout=max(0.01, timeout))
        except queue.Empty:
            raise CodexError('Codex response timed out') from None
        if message is None:
            raise CodexError('Codex process stopped')
        if 'method' in message and 'id' in message:
            if message['method'] == 'item/tool/call':
                try:
                    p = message['params']
                    if not self.handler:
                        raise ValueError('No tools enabled')
                    result = self.handler(p['tool'], p['arguments'])
                    response = {'success': True, 'contentItems': [
                        {'type': 'inputText', 'text': json.dumps(result)}]}
                except Exception as exc:
                    # Tool handlers expose only intentional validation messages.
                    detail = str(exc) if isinstance(exc, ValueError) else 'Tool failed; no success verified'
                    response = {'success': False, 'contentItems': [
                        {'type': 'inputText', 'text': detail}]}
                self.send({'id': message['id'], 'result': response})
            else:
                # The coach never grants itself shell, filesystem or connector access.
                self.send({'id': message['id'], 'error': {'code': -32601,
                    'message': 'This capability is not enabled for the coach'}})
        return message

    def request(self, method, params, timeout=60):
        self.serial += 1
        request_id = self.serial
        self.send({'id': request_id, 'method': method, 'params': params})
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            message = self.receive(deadline - time.monotonic())
            if message.get('id') == request_id and 'method' not in message:
                if 'error' in message:
                    raise CodexError(str(message['error']))
                return message.get('result', {})
            self.notifications.append(message)
        raise CodexError('Codex request timed out')

    def account(self):
        account = self.request('account/read', {'refreshToken': False}).get('account')
        if not account or account.get('type') != 'chatgpt':
            raise CodexError('Coach requires ChatGPT sign-in; API billing is disabled')
        return {'type': account['type'], 'planType': account.get('planType')}

    def start(self, model, instructions, tools, thread_id=None):
        common = {'model': model, 'modelProvider': 'openai',
            'cwd': str(self.runtime / 'workspace'), 'approvalPolicy': 'never',
            'sandbox': 'read-only', 'baseInstructions': instructions,
            'config': {'features.shell_tool': False, 'features.apps': False,
                       'features.multi_agent': False, 'web_search': 'live'}}
        if thread_id:
            result = self.request('thread/resume', {**common, 'threadId': thread_id,
                'excludeTurns': True})
        else:
            result = self.request('thread/start', {**common, 'environments': [],
                'dynamicTools': tools, 'selectedCapabilityRoots': [],
                'allowProviderModelFallback': False})
        return result['thread']['id']

    def run(self, thread_id, text, timeout=600, on_progress=None):
        self.notifications.clear()
        result = self.request('turn/start', {'threadId': thread_id,
            'input': [{'type': 'text', 'text': text}], 'environments': [],
            'effort': 'high'})
        turn_id = result['turn']['id']
        deadline = time.monotonic() + timeout
        final = []
        tool_names = []
        while time.monotonic() < deadline:
            message = self.notifications.pop(0) if self.notifications else self.receive(deadline - time.monotonic())
            p = message.get('params', {})
            if p.get('turnId') not in (None, turn_id):
                continue
            if message.get('method') == 'item/completed':
                item = p.get('item', {})
                if item.get('type') == 'agentMessage' and item.get('phase') in (None, 'final_answer'):
                    final.append(item.get('text', ''))
                elif item.get('type') == 'agentMessage' and item.get('phase') == 'commentary':
                    if on_progress:on_progress(item.get('text', ''))
                elif item.get('type') == 'dynamicToolCall':
                    tool_names.append(item.get('tool'))
            if message.get('method') == 'turn/completed' and p.get('turn', {}).get('id') == turn_id:
                turn = p['turn']
                if turn.get('status') != 'completed':
                    raise CodexError('Coach turn failed; no completion claimed')
                return {'text': '\n\n'.join(final), 'tools': tool_names}
        try:
            self.request('turn/interrupt', {'threadId': thread_id, 'turnId': turn_id}, timeout=10)
        finally:
            raise CodexError('Coach turn timed out; no completion claimed')

    def close(self):
        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.proc.kill()
