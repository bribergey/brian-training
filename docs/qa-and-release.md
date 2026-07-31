# QA And Release

## Baseline Checks

Before production-impacting work:

1. Check `git status --short --branch`.
2. Identify the active branch and target deploy branch.
3. Inspect the relevant HTML config block: `ENV`, `AUTH_REDIRECT_URL`, `APP_USERS_TABLE`, fallback flags.
4. Confirm whether the task touches production data, auth, RLS, or deploy workflows.
5. Record important work in Notion.

## Staging QA

For auth/data work, staging should prove:

- signed-out users do not see Brian data
- mapped users resolve to the correct `user_id`
- synthetic users cannot read Brian staging rows
- forged writes to another user return 403 or fail RLS
- training queue renders for the mapped user
- analytics/history do not leak other users
- Me tab profile/measurements are scoped to the mapped user
- onboarding runbook steps work for a synthetic mapped user before any real production user is created
- coach/Telegram write instructions include an explicit environment, target `user_id`, and narrow table list

Use synthetic staging users where possible. Clean up test rows after write tests.

For every UI or data branch, refresh the durable `codex_qa` fixture before
interactive staging QA by following
[`scripts/qa/README.md`](../scripts/qa/README.md). The fixture mirrors Brian's
production data shapes under an isolated user ID, strips production food-photo
references, and gives Codex enough realistic data to exercise history,
analytics, Daily Log, program, workout, and profile views. Branch-specific
test writes must remain scoped to `codex_qa`.

## Production QA

Production QA should be as read-only as possible.

Expected checks after auth/RLS work:

- production URL remains `https://briqtraining.com/`
- legacy GitHub Pages URL redirects to the custom domain
- no staging badge/text appears
- signed-in header resolves to Brian
- production session count matches DB read-check
- `app_users` mapping exists and is active
- anon cannot read production user-owned tables
- anon can still read shared `exercises`
- authenticated Brian can read production sessions/profile/measurements/program

Only do production write tests with explicit approval.

Brian has approved realistic production QA under the isolated `codex_qa`
account. After every production publish, refresh the fixture and verify the
released flow while signed in as `dev@lostplate.com`. Never use Brian's login
for Codex browser testing, and never mutate `user_id = 'brian'` rows. Sign out
after QA.

## Deployment Verification

After pushing to `main` or `staging`:

- Check GitHub Actions status.
- Fetch the public deployed HTML and verify the expected marker/config.
- Use a cache-buster URL for browser QA.
- If GitHub Pages serves old HTML, wait and re-check before diagnosing app behavior.
- Refresh and use the isolated `codex_qa` data as described in
  [`scripts/qa/README.md`](../scripts/qa/README.md).

## Final Handoff

Final updates should include:

- what changed
- what was verified
- what was not verified
- any user action needed
- links to PRs/Notion where useful
