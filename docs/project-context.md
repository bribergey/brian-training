# Project Context

## Product

Brian's Training Hub is a personal training app used for real workouts. It includes training queue, workout logging, history, analytics, profile/body composition, and program data. It should evolve like a real product: careful releases, durable architecture, and production safety.

## Repo Shape

The app is currently a static HTML/Supabase application.

- `index.html`: production app source. Pushing `main` deploys this to GitHub Pages root.
- `brian_STAGING.html`: staging app source. Pushing `staging` deploys this to `/staging/`.
- `brian_master.html`: mirror/copy used by earlier workflow; keep aligned when making app-wide HTML changes unless the project is intentionally simplified.
- `brian_PRODUCTION.html`: older production snapshot. Do not assume it is the active source.
- `.github/workflows/deploy-production.yml`: copies `index.html` from `main` to `gh-pages/index.html`.
- `.github/workflows/deploy-staging.yml`: copies `brian_STAGING.html` from `staging` to `gh-pages/staging/index.html`.
- `supabase/migrations/`: migration history for schema/RLS/auth work.

## Environments

Production:

- URL: `https://bribergey.github.io/brian-training/`
- Source branch: `main`
- Deployed file: `gh-pages/index.html`
- App `ENV`: `production`
- Production tables include `sessions`, `program`, `monthly_program`, `user_profile`, `user_measurements`, and related views.

Staging:

- URL: `https://bribergey.github.io/brian-training/staging/`
- Source branch: `staging`
- Deployed file: `gh-pages/staging/index.html`
- App `ENV`: `staging`
- Staging tables generally use `_staging` suffixes.

## Current Product Milestone

Phase 3 multi-user auth was completed on 2026-06-19. Production login works for Brian with strict auth and RLS. Future work should be treated as Phase 4+:

- smoother onboarding/admin flow
- real second-user onboarding
- Telegram coach multi-user instructions
- iPhone Home Screen/PWA login polish
- longer-term environment cleanup

