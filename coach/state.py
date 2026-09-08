"""Private durable inbox, proposals, coaching memory, and receipts."""
import json
from pathlib import Path
import sqlite3
import threading
import time


class State:
    def __init__(self, path):
        self.lock=threading.RLock()
        self.db=sqlite3.connect(path,check_same_thread=False)
        Path(path).chmod(0o600)
        self.db.execute('pragma journal_mode=WAL')
        self.db.executescript('''
          create table if not exists kv(key text primary key,value text not null);
          create table if not exists inbox(id integer primary key,payload text not null,status text not null default 'pending');
          create table if not exists proposals(id text primary key,payload text not null,status text not null,created real not null,receipt text);
          create table if not exists memory(id integer primary key,created real not null,fact text not null,evidence text not null,review_date text);
          create table if not exists conversation(id integer primary key,created real not null,role text not null,content text not null);
        ''')
        self.db.commit()

    def get(self,key,default=None):
        with self.lock:
            row=self.db.execute('select value from kv where key=?',(key,)).fetchone()
        return json.loads(row[0]) if row else default

    def set(self,key,value):
        with self.lock,self.db:
            self.db.execute('insert into kv values(?,?) on conflict(key) do update set value=excluded.value',(key,json.dumps(value)))

    def enqueue(self,update):
        with self.lock,self.db:
            self.db.execute('insert or ignore into inbox(id,payload) values(?,?)',(update['update_id'],json.dumps(update)))
            self.db.execute('insert into kv values(?,?) on conflict(key) do update set value=excluded.value',('offset',json.dumps(update['update_id']+1)))

    def pending(self):
        with self.lock:
            row=self.db.execute("select id,payload from inbox where status='pending' order by id limit 1").fetchone()
        return (row[0],json.loads(row[1])) if row else None

    def finish(self,update_id,status='done'):
        with self.lock,self.db:
            self.db.execute('update inbox set status=? where id=?',(status,update_id))

    def proposal(self,p):
        with self.lock,self.db:
            self.db.execute("update proposals set status='superseded' where status in ('draft','presented')")
            self.db.execute('insert into proposals(id,payload,status,created) values(?,?,?,?)',(p['id'],json.dumps(p),'draft',time.time()))

    def load_proposal(self,proposal_id):
        with self.lock:
            row=self.db.execute('select payload,status,created,receipt from proposals where id=?',(proposal_id,)).fetchone()
        if not row:raise ValueError('Proposal not found')
        return {'payload':json.loads(row[0]),'status':row[1],'created':row[2], 'receipt':json.loads(row[3]) if row[3] else None}

    def proposal_status(self,proposal_id,status,receipt=None):
        with self.lock,self.db:
            self.db.execute('update proposals set status=?,receipt=coalesce(?,receipt) where id=?',(status,json.dumps(receipt) if receipt else None,proposal_id))

    def remember(self,fact,evidence,review_date=None):
        if not isinstance(fact,str) or not isinstance(evidence,str) or not 1<=len(fact)<=3000 or not 1<=len(evidence)<=1000:
            raise ValueError('Memory needs a concise fact and its source/date')
        with self.lock,self.db:
            self.db.execute('insert into memory(created,fact,evidence,review_date) values(?,?,?,?)',(time.time(),fact,evidence,review_date))
        return {'stored':True}

    def memories(self):
        with self.lock:
            rows=self.db.execute('select created,fact,evidence,review_date from memory order by id desc limit 100').fetchall()
        return [dict(zip(('created','fact','evidence','review_date'),r)) for r in rows]

    def message(self,role,content):
        with self.lock,self.db:
            self.db.execute('insert into conversation(created,role,content) values(?,?,?)',(time.time(),role,content))

    def recent(self,limit=12):
        with self.lock:
            rows=self.db.execute('select role,content from conversation order by id desc limit ?',(limit,)).fetchall()
        return [dict(zip(('role','content'),r)) for r in reversed(rows)]
