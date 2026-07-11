# Infrastructure

## Supabase

Primary project:

- Name: `brian-training`
- Ref/project id: `mimvmaotzmacgiziovvi`
- Region: `us-west-2`
- Database: Postgres 17

Use the Supabase connector/CLI for read checks and migrations. Follow the Supabase skill guidance when doing auth, RLS, schema, or database work.

Canonical app data lives in the dedicated `training` schema. The legacy `public`
table names are compatibility views for cached clients and older tooling; new
code, coach instructions, and SQL should use `training.*`.

## Auth Model

The app uses Supabase Auth and an app-user mapping table.

- Production mapping table: `training.app_users`
- Staging mapping table: `training.app_users_staging`
- Brian production app identity: `user_id = brian`
- Brian auth user id as of Phase 3: `8d28136d-e06c-49fb-b4f8-0fa7788068d7`

The frontend resolves the active app user from the authenticated Supabase session, then scopes table access by `user_id`. Legacy anonymous Brian fallback is disabled in production.

Supabase Auth URL settings should include:

- Site URL: `https://briqtraining.com/`
- Redirect allow-list:
  - `https://briqtraining.com/`
  - `https://briqtraining.com/staging/`
  - `https://bribergey.github.io/brian-training/`
  - `https://bribergey.github.io/brian-training/staging/`

## Data Model Notes

Production user-owned tables in `training`:

- `sessions`
- `program`
- `monthly_program`
- `user_profile`
- `user_measurements`

Staging user-owned tables in `training`:

- `sessions_staging`
- `program_staging`
- `monthly_program_staging`
- `user_profile_staging`
- `user_measurements_staging`

Shared/global:

- `exercises` is intentionally shared and readable as a catalog. If one user adds a global exercise, it can affect all users unless future work changes that model.

Views:

- Production includes `program_full`, `monthly_program_full`.
- Staging includes `program_staging_full`, `monthly_program_staging_full`.

## RLS And Grants

Expected Phase 3 posture:

- All user-owned production and staging tables have RLS enabled.
- Anonymous users cannot read or write user-owned data.
- Authenticated users can read/write only rows mapped to their app user.
- `anon` can read `exercises`.
- `authenticated` can read `exercises`.

Before changing RLS, verify policies and grants with read-only SQL. Do not rely only on UI behavior.

## GitHub Pages Deployment

Production deploy:

- Push to `main`.
- Workflow copies `index.html` to `gh-pages/index.html`.
- Public URL is `https://briqtraining.com/`.
- Legacy GitHub Pages URL redirects from `https://bribergey.github.io/brian-training/`.

Staging deploy:

- Push to `staging`.
- Workflow copies `brian_STAGING.html` to `gh-pages/staging/index.html`.
- Public URL is `https://briqtraining.com/staging/`.
- Legacy GitHub Pages staging URL redirects from `https://bribergey.github.io/brian-training/staging/`.

GitHub Pages cache can lag briefly. Use cache-buster query strings during QA, for example `?v=qa-YYYYMMDD`.
