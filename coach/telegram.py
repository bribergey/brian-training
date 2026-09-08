"""Telegram transport; tokens never appear in exception messages or logs."""
import json
import urllib.error
import urllib.request
import uuid


class Telegram:
    def __init__(self,token):self.token=token

    def call(self,method,payload=None,timeout=45):
        req=urllib.request.Request('https://api.telegram.org/bot'+self.token+'/'+method,
            data=json.dumps(payload or {}).encode(),
            headers={'Content-Type':'application/json','User-Agent':'BRIQ-Coach/0.1'})
        try:
            with urllib.request.urlopen(req,timeout=timeout) as response:result=json.loads(response.read())
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f'Telegram {method} failed (HTTP {exc.code})') from None
        except OSError:
            raise RuntimeError(f'Telegram {method} connection failed') from None
        if not result.get('ok'):raise RuntimeError(f'Telegram {method} failed')
        return result['result']

    def send(self,chat_id,text,markup=None):
        # Count UTF-16 units, including astral emoji; never exceed Telegram's limit.
        chunks=[];chunk='';units=0
        for character in text:
            size=2 if ord(character)>0xffff else 1
            if units+size>3900:
                chunks.append(chunk);chunk='';units=0
            chunk+=character;units+=size
        if chunk:chunks.append(chunk)
        for i,part in enumerate(chunks):
            payload={'chat_id':chat_id,'text':part,'link_preview_options':{'is_disabled':True}}
            if markup and i==len(chunks)-1:payload['reply_markup']=markup
            result=self.call('sendMessage',payload)
        return result if chunks else None

    def document(self,chat_id,text,filename='workout-proposal.txt'):
        boundary='briq'+uuid.uuid4().hex
        body=(f'--{boundary}\r\nContent-Disposition: form-data; name="chat_id"\r\n\r\n{chat_id}\r\n'
              f'--{boundary}\r\nContent-Disposition: form-data; name="document"; filename="{filename}"\r\nContent-Type: text/plain; charset=utf-8\r\n\r\n{text}\r\n--{boundary}--\r\n').encode()
        req=urllib.request.Request('https://api.telegram.org/bot'+self.token+'/sendDocument',data=body,
            headers={'Content-Type':'multipart/form-data; boundary='+boundary,'User-Agent':'BRIQ-Coach/0.1'})
        try:
            with urllib.request.urlopen(req,timeout=60) as response:result=json.loads(response.read())
        except (urllib.error.HTTPError,OSError):
            raise RuntimeError('Telegram proposal attachment delivery failed') from None
        if not result.get('ok'):raise RuntimeError('Telegram proposal attachment delivery failed')
        return result['result']
