# QA And Release

## Baseline Checks

Before production-impacting work:

1. Check `git status --short --branch`.
2. Identify the active branch and target deploy branch.
3. Confirm the canonical source: `main/app/index.html` for production or `staging:brian_STAGING.html` for staging. Never use `gh-pages` as source.
4. Inspect the relevant HTML config block: `ENV`, `AUTH_REDIRECT_URL`, `APP_USERS_TABLE`, fallback flags, and environment-specific Storage prefix.
5. Confirm whether the task touches production data, auth, RLS, Storage, or deploy workflows.
6. Run `node scripts/check-app-contract.mjs` and record important work in Notion.

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

## Production QA

Production QA should be as read-only as possible.

Expected checks after auth/RLS work:

- production marketing remains `https://briqtraining.com/`
- production app remains `https://briqtraining.com/app/`
- legacy GitHub Pages URL redirects to the custom domain
- no staging badge/text appears
- signed-in header resolves to Brian
- production session count matches DB read-check
- `app_users` mapping exists and is active
- anon cannot read production user-owned tables
- anon can still read shared `exercises`
- authenticated Brian can read production sessions/profile/measurements/program

Only do production write tests with explicit approval.

## Deployment Verification

After pushing to `main` or `staging`:

- Check GitHub Actions status.
- For production, verify both `/` and `/app/`; for staging, verify `/staging/`, `/staging/home/`, and `/staging/app/`.
- Fetch the public deployed HTML and verify the expected `ENV`, route, and feature marker.
- Use a cache-buster URL for browser QA.
- If GitHub Pages serves old HTML, wait and re-check before diagnosing app behavior.
- Confirm all worktrees are clean, merged temporary branches are removed, and only intentional remote branches remain.

## Final Handoff

Final updates should include:

- what changed
- what was verified
- what was not verified
- any user action needed
- links to PRs/Notion where useful
