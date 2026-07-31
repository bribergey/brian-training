# Codex QA Data

The dedicated QA login is `dev@lostplate.com`, mapped to app user
`codex_qa` in production and staging. Its password is stored outside the
repository in macOS Keychain under service `briqtraining-qa`.

## Refresh

Run [`refresh-codex-qa-data.sql`](refresh-codex-qa-data.sql) as one request
through the connected Supabase SQL tool. Do not split the transaction into
individual statements.

The refresh:

- validates the production and staging `codex_qa` mappings;
- reads Brian's current production rows as realistic source fixtures;
- replaces only `user_id = 'codex_qa'` rows in both environments;
- assigns fresh database UUIDs;
- labels the copied profile `Codex QA`;
- strips Brian's food-photo paths and reusable-food IDs from copied Daily
  Logs, preventing QA actions from targeting Brian's storage or memory rows;
- copies reusable foods separately with new QA-owned IDs;
- verifies that Brian's source counts did not change; and
- reports expected and actual QA counts after commit.

This is operational fixture data, not a schema migration. Do not add it to
`supabase/migrations/` or schedule it to run automatically.

## Release Use

For each UI or data branch:

1. Refresh before staging browser QA.
2. Sign in to staging as `dev@lostplate.com`.
3. Verify the changed flow with realistic history, Daily Logs, nutrition,
   profile, program, and workout data.
4. Add any branch-specific QA data only under `codex_qa`.
5. Refresh again if a migration changes a copied table's columns.

For each production publish:

1. Complete the staging checks first.
2. Refresh after the production deployment.
3. Sign in to production as `dev@lostplate.com`.
4. Verify the released flow without using or modifying Brian's rows.
5. Sign out when browser QA is finished.

Never automate the refresh as part of a public deployment workflow: publishing
code should not implicitly copy personal production data.
