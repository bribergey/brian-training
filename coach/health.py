"""Read-only operational health, without opening credentials or calling models."""
import argparse
import json
from pathlib import Path
import sqlite3
import time


def report(state, now=None):
    now = time.time() if now is None else now
    poll = state.get('last_poll_ok', 0)
    worker = state.get('worker_heartbeat', 0)
    active = state.get('active_since', 0)
    model = state.get('model_state', 'unchecked')
    reasons = []
    if not poll or now - poll > 120: reasons.append('telegram_poll_stale')
    if active:
        if now - active > 1200: reasons.append('request_overdue')
    elif not worker or now - worker > 240:
        reasons.append('worker_stale')
    if model in ('unavailable', 'sign_in_required', 'runtime_missing'):
        reasons.append(model)
    elif model in ('unchecked', 'connecting'):
        reasons.append('model_unchecked')
    return {'status': 'degraded' if reasons else 'healthy', 'reasons': reasons,
            'model': model, 'busy': bool(active), 'inbox': state.counts(),
            'last_poll_ok': poll, 'last_model_success': state.get('last_model_success'),
            'last_reply_delivered': state.get('last_reply_delivered'),
            'release': state.get('release'), 'started_at': state.get('started_at')}


def read_report(runtime):
    path = Path(runtime).expanduser() / 'state/coach.sqlite'
    db = sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)
    class ReadState:
        def get(self, key, default=None):
            row = db.execute('select value from kv where key=?', (key,)).fetchone()
            return json.loads(row[0]) if row else default
        def counts(self):
            return dict(db.execute('select status,count(*) from inbox group by status'))
    try: return report(ReadState())
    finally: db.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--runtime', type=Path, default=Path.home()/'.local/share/briq-coach')
    args = parser.parse_args()
    try: result = read_report(args.runtime.resolve())
    except (OSError, sqlite3.Error, ValueError):
        result = {'status': 'degraded', 'reasons': ['state_unavailable']}
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['status'] == 'healthy' else 1)
