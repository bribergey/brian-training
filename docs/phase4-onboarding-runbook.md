# Phase 4 Onboarding And Admin Runbook

Phase 4 turns the Phase 3 strict-auth foundation into a repeatable operating process for adding real users. The goal is boring reliability: stage first, verify isolation, then touch production only with Brian's explicit approval for the exact account/data action.

## Safety Rules

- Do not mutate production workout, program, profile, measurement, or mapping data unless Brian approves the exact action.
- Do not paste service-role keys, admin-generated magic links, access tokens, or one-time auth URLs into chat, Notion, commits, or docs.
- Use staging users and staging tables for rehearsal.
- Keep every query and write scoped to one environment and one `user_id`.
- Treat the shared `exercises` catalog as global; changes there affect every user.
- Record major checkpoints on the Notion Phase 4 card.

## Current Architecture

Production user mapping lives in `training.app_users`.

Staging user mapping lives in `training.app_users_staging`.

The frontend resolves the signed-in Supabase Auth user to an app `user_id`, then all user-owned table reads and writes are scoped by that app user. Legacy `public.*` names exist as compatibility views, but new SQL should use `training.*`.

User-owned production tables in `training`:

- `sessions`
- `program`
- `monthly_program`
- `user_profile`
- `user_measurements`

User-owned staging tables in `training`:

- `sessions_staging`
- `program_staging`
- `monthly_program_staging`
- `user_profile_staging`
- `user_measurements_staging`

Shared table:

- `exercises`

## Required Inputs For A Real User

Before any real production onboarding, collect and confirm:

- Email address for Supabase Auth.
- Display name.
- Stable app `user_id`, lowercase with underscores if needed, for example `maya` or `client_jane`.
- Initial training program direction.
- Initial profile details Brian wants seeded, if any.
- Whether production account/data creation is approved now or staging rehearsal only.
- Cutover/QA window when Brian is not relying on the app for an active workout.

## Staging Rehearsal Checklist

Use this before creating a production user.

1. Confirm repo and deployment context:
   - `git status --short --branch`
   - target branch for staging changes is `staging`
   - staging app config uses `ENV = 'staging'`
   - staging app config uses `APP_USERS_TABLE = 'app_users_staging'`
   - `ALLOW_LEGACY_IDENTITY_FALLBACK = false`

2. Create or identify the staging Supabase Auth user without exposing secrets.

3. Insert or update exactly one `app_users_staging` mapping row:
   - `auth_user_id` is the staging Auth user UUID.
   - `email` matches the Auth user email.
   - `display_name` is human-readable.
   - `user_id` is the stable app user id.
   - `is_active = true`.

4. Seed staging-only user data:
   - create `user_profile_staging` row for the new `user_id`
   - create `user_measurements_staging` only if needed for QA
   - create `program_staging` and `monthly_program_staging` rows for the new `user_id`
   - do not copy Brian production data into another user unless Brian explicitly asks for that exact seed behavior

5. Run staging browser QA:
   - signed-out staging shows sign-in required and no Brian data
   - mapped staging user resolves to the expected display name and `user_id`
   - Training queue renders that user's program
   - History/Analytics do not show Brian sessions
   - Me tab shows that user's profile/measurements only
   - Sign out returns to the clean signed-out shell

6. Run staging RLS QA:
   - mapped user can read own staging rows
   - mapped user cannot read Brian staging sessions/profile/program rows
   - mapped user can insert an own staging session test row
   - forged insert with Brian's `user_id` fails RLS
   - delete the test session row after verification

7. Record QA results on the Phase 4 Notion card.

## Production Onboarding Gate

Production onboarding is blocked until Brian explicitly approves the exact production action. Once approved:

1. Reconfirm Brian production login works before the change.
2. Create or identify the production Supabase Auth user.
3. Add one `app_users` mapping row for the production Auth user.
4. Seed only the approved production rows for that user's `user_id`.
5. Run read-only production checks first.
6. Run a production write test only if Brian approved it.
7. Record counts, tested user, deployment state, and residual risk in Notion.

## Rollback Ideas

For a bad new-user mapping:

- Set `is_active = false` on the affected `app_users` or `app_users_staging` row.
- Do not delete the Auth user until sessions have been considered; deleting a user does not instantly invalidate existing access tokens.
- Remove or correct newly seeded staging rows as needed.
- For production rows, ask Brian before deleting or overwriting anything.

For app login polish regressions:

- Revert the HTML copy-only change on the feature branch.
- Redeploy staging before considering production.
