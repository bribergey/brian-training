# Project Context

## Product

Brian's Training Hub is a personal training app used for real workouts. It includes training queue, workout logging, history, analytics, profile/body composition, and program data. It should evolve like a real product: careful releases, durable architecture, and production safety.

## Repo And Branch Shape

The app is currently a static HTML/Supabase application.

- Local repo path: `/Users/brianlostplate/Projects/Brian Training`.
- Local migration notes: `docs/local-migration.md`.
- On `main`, `index.html` is the production marketing source and `app/index.html` is the only production app source.
- On `staging`, `marketing_STAGING.html` is the staging marketing source and `brian_STAGING.html` is the only staging app source.
- Parallel app copies such as `brian_master.html` and `brian_PRODUCTION.html` are intentionally removed.
- `APP_SOURCES.md`: source-of-truth rules enforced by the app-contract workflow.
- `.github/workflows/deploy-production.yml`: copies production marketing and app routes to `gh-pages`.
- `.github/workflows/deploy-staging.yml`: copies staging marketing and app routes to `gh-pages`.
- `supabase/migrations/`: migration history for schema/RLS/auth work.
- `AGENTS.md` and the core `docs/` files should exist on both `main` and `staging`; keep them synchronized when operating guidance changes.

Branch roles:

- `main`: reviewed production source; pushes trigger the production deploy workflow.
- `staging`: reviewed staging source; pushes trigger the staging deploy workflow.
- `gh-pages`: generated hosting output only. Never develop or hand-edit source here.
- `codex/...`: temporary focused work branches; remove them after merge.

## Environments

Production:

- URL: `https://briqtraining.com/app/`
- Marketing URL: `https://briqtraining.com/`
- Legacy redirect URL: `https://bribergey.github.io/brian-training/`
- Source branch: `main`
- Deployed file: `gh-pages/app/index.html`
- App `ENV`: `production`
- Production tables include `sessions`, `program`, `monthly_program`, `user_profile`, `user_measurements`, `daily_logs`, and related views.
- Food photos use the private `daily-log-food-photos` Storage bucket under the `production/` path prefix.

Staging:

- URL: `https://briqtraining.com/staging/app/`
- Marketing URL: `https://briqtraining.com/staging/`
- Legacy redirect URL: `https://bribergey.github.io/brian-training/staging/`
- Source branch: `staging`
- Deployed file: `gh-pages/staging/app/index.html`
- App `ENV`: `staging`
- Staging tables generally use `_staging` suffixes.
- Food photos use the same private bucket under the `staging/` path prefix.

## Current Product Milestone

Phase 3 multi-user auth was completed on 2026-06-19. Daily Log, food photos, Analytics repairs, and app-refresh stability fixes were released by 2026-07-13. Production login works for Brian with strict auth and RLS. Future work should be treated as Phase 4+:

- smoother onboarding/admin flow
- real second-user onboarding
- Telegram coach multi-user instructions
- iPhone Home Screen/PWA login polish
- longer-term environment cleanup

Active Phase 4 work starts from:

- `docs/phase4-onboarding-runbook.md`: repeatable staging-first onboarding/admin workflow.
- `docs/coach-multi-user-operations.md`: coach and Telegram guardrails for multi-user reads/writes.
- `docs/phase4-5-coach-rollout.md`: user-specific coach templates and test prompts.
