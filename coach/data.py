"""Backend-only database adapter. Model inputs never become SQL expressions."""
import json
import urllib.error
import urllib.request

PROJECT = 'mimvmaotzmacgiziovvi'
PROGRAM_FIELDS = ('id', 'user_id', 'week', 'week_number', 'day', 'exercise',
    'sets', 'reps', 'weight', 'rest', 'order_index', 'scheduled_date',
    'session_label', 'suggested_sets', 'coach_notes', 'superset_group')
MONTH_FIELDS = ('id', 'user_id', 'month', 'month_label', 'status', 'week_type',
    'day', 'order_index', 'exercise', 'sets', 'weight', 'internal_notes',
    'superset_group', 'session_label')


def literal(value):
    if value is None:
        return 'NULL'
    if isinstance(value, (dict, list)):
        value = json.dumps(value, allow_nan=False, separators=(',', ':'))
    return "'" + str(value).replace("'", "''") + "'"


class Database:
    def __init__(self, token, environment='staging'):
        if environment not in ('staging', 'production'):
            raise ValueError('Invalid environment')
        self.token = token
        self.environment = environment
        self.user = 'brian' if environment == 'production' else 'codex_qa'
        suffix = '' if environment == 'production' else '_staging'
        self.tables = {t: 'training.' + t + suffix for t in
            ('program', 'monthly_program', 'sessions', 'user_profile', 'user_measurements')}

    def query(self, sql, readonly=True):
        # The management credential stays in the service, never in Codex's env.
        req = urllib.request.Request(
            f'https://api.supabase.com/v1/projects/{PROJECT}/database/query',
            data=json.dumps({'query': sql, 'read_only': readonly}).encode(),
            headers={'Authorization': 'Bearer ' + self.token,
                     'Content-Type': 'application/json', 'User-Agent': 'BRIQ-Coach/0.1'})
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                return json.loads(response.read())
        except urllib.error.HTTPError as exc:
            body = exc.read().decode(errors='replace')
            for message in ('STALE_PROPOSAL', 'ALREADY_LOGGED', 'DUPLICATE_SESSION', 'VERIFY_FAILED'):
                if message in body:
                    raise ValueError(message + ': prepare a fresh proposal or inspect saved state') from None
            raise RuntimeError(f'Database request failed (HTTP {exc.code}); success not verified') from None

    def _snapshot_sql(self):
        parts = []
        for name, table in self.tables.items():
            parts.extend([literal(name), f"(select coalesce(jsonb_agg(to_jsonb(t) order by t.id),'[]'::jsonb) from {table} t where user_id={literal(self.user)})"])
        parts.extend(["'exercises'", "(select coalesce(jsonb_agg(to_jsonb(e) - 'photos' order by name),'[]'::jsonb) from training.exercises e)"])
        return 'jsonb_build_object(' + ','.join(parts) + ')'

    def snapshot(self):
        rows = self.query(f'with s as (select {self._snapshot_sql()} as data) select data,md5(data::text) as fingerprint from s')
        return rows[0]

    def apply(self, proposal):
        """Only called by authenticated Telegram approval, never by a model tool.

        UUIDs belong to this immutable proposal. A retry reads the committed rows
        before considering mutation, including after a lost HTTP response.
        """
        kind, rows = proposal['kind'], proposal['rows']
        if kind not in ('week', 'adjustment', 'month'):
            raise ValueError('Invalid proposal kind')
        table = self.tables['monthly_program' if kind == 'month' else 'program']
        fields = MONTH_FIELDS if kind == 'month' else PROGRAM_FIELDS
        if not rows or any(set(r) != set(fields) or r['user_id'] != self.user for r in rows):
            raise ValueError('Invalid write scope')
        ids = ','.join(literal(r['id']) + '::uuid' for r in rows)
        payload = literal(rows) + '::jsonb'
        field_list = ','.join(fields)
        # Compare only explicitly written fields; database trigger fields remain server-owned.
        saved_object = 'jsonb_build_object(' + ','.join(literal(k)+',t.'+k for k in fields) + ')'
        actual = f"(select coalesce(jsonb_agg({saved_object} order by id),'[]'::jsonb) from {table} t where user_id={literal(self.user)} and id in ({ids}))"
        expected = f"(select jsonb_agg(v order by v->>'id') from jsonb_array_elements({payload}) v)"
        same = f'{actual} = {expected}'
        if kind == 'month':
            same += f" and not exists(select 1 from {table} where user_id={literal(self.user)} and status='current' and month<>{int(proposal['month'])})"
        checks = [f"if md5(({self._snapshot_sql()})::text)<>{literal(proposal['fingerprint'])} then raise exception 'STALE_PROPOSAL'; end if;"]
        if kind in ('week', 'adjustment'):
            pairs = ' or '.join(f"(p.scheduled_date={literal(r['scheduled_date'])}::date and p.day={literal(r['day'])})" for r in rows)
            checks.append(f"if exists(select 1 from {self.tables['program']} p join {self.tables['sessions']} s on s.user_id=p.user_id and s.program_session_key=p.session_key where p.user_id={literal(self.user)} and ({pairs})) then raise exception 'ALREADY_LOGGED'; end if;")
            if kind == 'week':
                checks.append(f"if exists(select 1 from {table} p where user_id={literal(self.user)} and ({pairs})) then raise exception 'DUPLICATE_SESSION'; end if;")
        mutations = []
        if kind == 'month':
            mutations.append(f"update {table} set status='archived' where user_id={literal(self.user)} and status='current' and month={int(proposal['previous_month'])};")
        if kind == 'adjustment':
            for row in rows:
                assignments = ','.join(k+'='+literal(row[k])+('::jsonb' if k=='suggested_sets' else '') for k in fields if k not in ('id','user_id'))
                mutations.append(f"update {table} set {assignments} where user_id={literal(self.user)} and id={literal(row['id'])}::uuid;")
        else:
            for row in rows:
                values = ','.join(literal(row[k])+('::jsonb' if k=='suggested_sets' else '') for k in fields)
                mutations.append(f'insert into {table} ({field_list}) values ({values});')
        body = f"begin if not ({same}) then {''.join(checks)} {''.join(mutations)} end if; if not ({same}) then raise exception 'VERIFY_FAILED'; end if; end"
        # Dollar delimiter cannot be injected by notes, names, or JSON payloads.
        delimiter = '$briq_coach$'
        while delimiter in body:
            delimiter = delimiter[:-1] + 'x$'
        sql = f"begin isolation level serializable; set local standard_conforming_strings=on; select pg_advisory_xact_lock(hashtext('briq-coach:{self.environment}:{self.user}')); do {delimiter}{body}{delimiter}; commit; select {actual} as rows;"
        result = self.query(sql, readonly=False)
        saved = result[0]['rows']
        if sorted(saved,key=lambda r:r['id']) != sorted(rows,key=lambda r:r['id']):
            raise RuntimeError('Write response did not match proposal; inspect before retrying')
        return {'verified': True, 'row_count': len(saved), 'environment': self.environment,
                'user_id': self.user, 'proposal_id': proposal['id']}
