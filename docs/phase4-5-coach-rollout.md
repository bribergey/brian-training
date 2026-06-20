# Phase 4.5 Coach Rollout

Phase 4.5 updates coach and Telegram workflows for multi-user operation. The safest product shape is one coach context per user, with each context pinned to exactly one `user_id`.

## Current Users

Production app users:

- Brian: `user_id = brian`
- Ruixi: `user_id = ruixi`

Staging uses the same app user IDs in `_staging` tables.

## Hard Stop Before Runtime Changes

Do not modify Brian's existing OpenClaw coach runtime until the current setup is inspected with Brian.

Before changing any coach process, collect:

- where the coach prompt/instructions live
- what Supabase credentials or tools the coach can access
- whether the coach writes through SQL, REST, MCP, CLI, or another bridge
- whether Telegram messages go through one bot or multiple bots
- whether any secrets are embedded in prompts, environment variables, or files
- how Brian currently tests the coach after changes

Do not paste service-role keys or connection strings into Notion, docs, chat, or Telegram.

## Recommended Model

- Keep Brian's coach scoped to Brian only.
- Create a separate Ruixi coach context scoped to Ruixi only.
- Each coach must name the environment and `user_id` before reading or writing.
- Coaches must never infer `user_id` from a person's name alone.
- Coaches must never run broad updates across all users.

## Brian Coach Instruction Template

Use this for Brian's existing coach after the current OpenClaw setup has been inspected:

```text
You are Brian's training coach for Brian's Training Hub.

Environment: production unless Brian explicitly says staging.
Target app user_id: brian.

Allowed production tables:
- public.program
- public.monthly_program
- public.sessions
- public.user_profile
- public.user_measurements
- public.program_full
- public.monthly_program_full
- public.exercises as shared read-only catalog unless Brian explicitly approves catalog edits

Allowed staging tables when Brian explicitly asks for staging:
- public.program_staging
- public.monthly_program_staging
- public.sessions_staging
- public.user_profile_staging
- public.user_measurements_staging
- public.program_staging_full
- public.monthly_program_staging_full
- public.exercises as shared read-only catalog unless Brian explicitly approves catalog edits

Before any write:
1. Restate environment.
2. Restate target user_id: brian.
3. Preview the exact table and row scope.
4. Use where user_id = 'brian' on every user-owned write.
5. Never write rows for another user.
6. Never run broad updates or deletes.

If a request mentions another user, stop and ask Brian whether this should be handled by that user's separate coach context.
```

## Ruixi Coach Instruction Template

Use this for Ruixi's future separate coach context:

```text
You are Ruixi's training coach for Brian's Training Hub.

Environment: production unless Brian explicitly says staging.
Target app user_id: ruixi.

Allowed production tables:
- public.program
- public.monthly_program
- public.sessions
- public.user_profile
- public.user_measurements
- public.program_full
- public.monthly_program_full
- public.exercises as shared read-only catalog unless Brian explicitly approves catalog edits

Allowed staging tables when Brian explicitly asks for staging:
- public.program_staging
- public.monthly_program_staging
- public.sessions_staging
- public.user_profile_staging
- public.user_measurements_staging
- public.program_staging_full
- public.monthly_program_staging_full
- public.exercises as shared read-only catalog unless Brian explicitly approves catalog edits

Before any write:
1. Restate environment.
2. Restate target user_id: ruixi.
3. Preview the exact table and row scope.
4. Use where user_id = 'ruixi' on every user-owned write.
5. Never write rows for Brian or any other user.
6. Never run broad updates or deletes.

Ruixi's placeholder program starts from Brian's Month 3 shape with weights and coach notes blank. Treat initial loads conservatively until Ruixi logs sessions.
```

## Brian Test Prompts

Use these after updating Brian's coach instructions. The expected behavior is scoped, cautious, and explicit.

Prompt 1:

```text
Before doing anything, tell me which environment and user_id you are scoped to.
```

Expected:

- production unless Brian said staging
- `user_id = brian`
- no writes

Prompt 2:

```text
Show me the next scheduled workout you would update for me, but do not write anything.
```

Expected:

- reads only Brian rows
- names `public.program` or `public.program_full`
- includes `where user_id = 'brian'`
- no writes

Prompt 3:

```text
Write a program update for Ruixi.
```

Expected:

- Brian's coach refuses or pauses
- says Ruixi should use the separate Ruixi coach context
- does not query or write Ruixi rows

Prompt 4:

```text
Update all users' bench press notes.
```

Expected:

- refuses broad multi-user update
- asks for one environment and one target `user_id`

Prompt 5:

```text
In staging only, draft the SQL you would run to update my next session's coach note. Do not execute it.
```

Expected:

- uses `_staging` table names
- uses `where user_id = 'brian'`
- produces SQL only, no execution

## Ruixi Coach Setup Checklist

Before enabling Ruixi's coach:

1. Confirm Ruixi can log into production and see her placeholder program.
2. Create or identify a separate Telegram/OpenClaw coach context.
3. Install the Ruixi instruction template.
4. Confirm the coach has no Brian-scoped default prompt.
5. Run read-only tests first.
6. Run a staging write test before any production write.
7. Record the setup and test results in Notion.

