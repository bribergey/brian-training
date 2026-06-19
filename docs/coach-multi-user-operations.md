# Coach Multi-User Operations

These notes are for coach, Telegram, and Codex workflows that read or write Brian's Training Hub data. The app is now multi-user-aware, so every operation must be scoped to the intended environment and `user_id`.

## Golden Rules

- Always name the environment first: production or staging.
- Always name the target `user_id` before reading or writing.
- Never update all users at once.
- Never rely on email alone once inside the workout tables; workout ownership is by app `user_id`.
- Treat `exercises` as shared. A new exercise there is visible to every user.
- Prefer staging rehearsal for new program patterns and coach instructions.

## Table Map

Production:

- `app_users`
- `program`
- `monthly_program`
- `sessions`
- `user_profile`
- `user_measurements`
- `program_full`
- `monthly_program_full`

Staging:

- `app_users_staging`
- `program_staging`
- `monthly_program_staging`
- `sessions_staging`
- `user_profile_staging`
- `user_measurements_staging`
- `program_staging_full`
- `monthly_program_staging_full`

Shared:

- `exercises`

## Required Preflight

Before any coach write:

1. Confirm environment.
2. Confirm `user_id`.
3. Confirm target table names.
4. Count existing rows for that `user_id`.
5. Preview the exact rows that will be inserted or updated.
6. For production, confirm Brian approved the exact write.

## Query Patterns

Read one user's sessions:

```sql
select id, date, day, logged_at, skipped, program_session_key
from public.sessions
where user_id = '<target_user_id>'
order by date desc, logged_at desc
limit 20;
```

Read one user's current program:

```sql
select *
from public.program
where user_id = '<target_user_id>'
order by scheduled_date asc, day asc, order_index asc;
```

Read one user's profile:

```sql
select *
from public.user_profile
where user_id = '<target_user_id>'
limit 1;
```

Use the `_staging` table names for staging.

## Write Patterns

Every insert into user-owned tables must include the intended `user_id`.

Every update or delete must include a `where user_id = '<target_user_id>'` clause plus the narrow row key or date range.

Good update shape:

```sql
update public.program
set coach_notes = '<new note>'
where user_id = '<target_user_id>'
  and id = '<row_id>';
```

Bad update shape:

```sql
update public.program
set coach_notes = '<new note>';
```

Do not run broad updates like the bad example.

## Program Authoring Notes

- Keep `program_session_key` stable and user-scoped where the app already normalizes it.
- Use `order_index` to control exercise order.
- Use `scheduled_date`, `day`, and `session_label` consistently so the Training and Program tabs agree.
- Keep archived and current month rows explicit in `monthly_program` / `monthly_program_staging`.
- If adding exercises to the shared catalog, confirm the name, badge, unit, and coaching notes are suitable for all users.

## Telegram Prompt Guardrail

When asking a coach or Telegram agent to read/write data, include this header:

```text
Environment: production|staging
Target app user_id: <target_user_id>
Allowed tables: <exact table list>
Forbidden: reading or writing any other user_id; broad updates; production writes without Brian approval
```

If any of those fields are missing, pause and ask for them before acting.

