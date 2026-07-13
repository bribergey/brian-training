# Project Context

## Product

Brian's Training Hub is a personal training app used for real workouts. It includes training queue, workout logging, history, analytics, profile/body composition, and program data. It should evolve like a real product: careful releases, durable architecture, and production safety.

## Repo Shape

The app is currently a static HTML/Supabase application.

- Local repo path: `/Users/brianlostplate/Projects/Brian Training`.
- Local migration notes: `docs/local-migration.md`.
- `index.html`: production marketing source. Pushing `main` deploys it to `/`.
- `app/index.html`: the only production app source. Pushing `main` deploys it to `/app/`.
- `marketing_STAGING.html`: staging marketing source. Pushing `staging` deploys it to `/staging/` and `/staging/home/`.
- `brian_STAGING.html`: the only staging app source. Pushing `staging` deploys it to `/staging/app/`.
- Parallel app copies such as `brian_master.html` and `brian_PRODUCTION.html` are intentionally removed.
- `APP_SOURCES.md`: source-of-truth rules enforced by the app-contract workflow.
- `.github/workflows/deploy-production.yml`: copies production marketing and app routes to `gh-pages`.
- `.github/workflows/deploy-staging.yml`: copies staging marketing and app routes to `gh-pages`.
- `supabase/migrations/`: migration history for schema/RLS/auth work.

## Environments

Production:

- URL: `https://briqtraining.com/app/`
- Marketing URL: `https://briqtraining.com/`
- Legacy redirect URL: `https://bribergey.github.io/brian-training/`
- Source branch: `main`
- Deployed file: `gh-pages/app/index.html`
- App `ENV`: `production`
- Production tables include `sessions`, `program`, `monthly_program`, `user_profile`, `user_measurements`, and related views.

Staging:

- URL: `https://briqtraining.com/staging/app/`
- Marketing URL: `https://briqtraining.com/staging/`
- Legacy redirect URL: `https://bribergey.github.io/brian-training/staging/`
- Source branch: `staging`
- Deployed file: `gh-pages/staging/app/index.html`
- App `ENV`: `staging`
- Staging tables generally use `_staging` suffixes.

## Current Product Milestone

Phase 3 multi-user auth was completed on 2026-06-19. Production login works for Brian with strict auth and RLS. Future work should be treated as Phase 4+:

- smoother onboarding/admin flow
- real second-user onboarding
- Telegram coach multi-user instructions
- iPhone Home Screen/PWA login polish
- longer-term environment cleanup

Active Phase 4 work starts from:

- `docs/phase4-onboarding-runbook.md`: repeatable staging-first onboarding/admin workflow.
- `docs/coach-multi-user-operations.md`: coach and Telegram guardrails for multi-user reads/writes.
- `docs/phase4-5-coach-rollout.md`: user-specific coach templates and test prompts.
