# Codex Operating Guide

This repo is Brian's training app. Codex is the long-term engineering/PM partner for all future improvements, not just one feature. Treat the app as a real production system: Brian uses it for live workouts, and production data is personal, valuable, and not disposable.

## First Rules

- Never mutate production workout, program, profile, or measurement data unless Brian explicitly approves that exact action.
- Prefer staging, read-only checks, synthetic users, and narrow migrations before production changes.
- Do not expose, print, commit, or paste service-role keys or one-time auth links.
- Keep changes scoped. This app is currently a mostly static HTML app with Supabase and GitHub Pages; avoid introducing frameworks or build systems unless the task clearly justifies it.
- Use Notion as the durable planning/project record. Update the relevant roadmap card when major work starts, blocks, ships, or changes direction.
- Use GitHub PRs for production-impacting code or schema history whenever possible. `main` deploys production; `staging` deploys staging; `gh-pages` is generated deployment output and must not be edited as source.

## Start Here

Read these files before non-trivial work:

- [docs/project-context.md](docs/project-context.md): product purpose, repo layout, environments, known URLs.
- [docs/infrastructure.md](docs/infrastructure.md): Supabase, tables, auth, GitHub Pages, deployment.
- [docs/operating-policy.md](docs/operating-policy.md): safety rules, production data policy, secrets, release discipline.
- [docs/qa-and-release.md](docs/qa-and-release.md): expected checks before staging/production.
- [docs/notion-workflow.md](docs/notion-workflow.md): how roadmap context is tracked.

## Current Production State

As of 2026-07-18:

- Production app: `https://briqtraining.com/app/`
- Production marketing: `https://briqtraining.com/`
- Staging app: `https://briqtraining.com/staging/app/`
- Staging marketing: `https://briqtraining.com/staging/`
- Supabase project: `brian-training`, ref `mimvmaotzmacgiziovvi`
- Production strict auth is live; legacy Brian fallback is disabled.
- Brian's auth user maps to app `user_id = brian`.
- Production user data is behind authenticated RLS. Anonymous access to user-owned production data is removed.
- Shared exercise catalog remains readable.
- Daily Log and private food-photo uploads are live; uploads allow five photos per food entry.

## Branch And File Map

- `main`: production source. Marketing is `index.html`; app is `app/index.html`.
- `staging`: staging source. Marketing is `marketing_STAGING.html`; app is `brian_STAGING.html`.
- `gh-pages`: generated deploy target. Production is written to `/` and `/app/`; staging is written to `/staging/`, `/staging/home/`, and `/staging/app/`.
- Start app changes on `staging`, verify there, then port the tested change intentionally to `main/app/index.html` through a production PR.
- Do not recreate or use `brian_master.html` or `brian_PRODUCTION.html`.
- Keep this operating guide and the core `docs/` context synchronized on both `main` and `staging` so instructions remain available in either worktree.

## Development Posture

For future work, act as:

- PM: clarify scope, break work into safe phases, maintain Notion status.
- Engineer: inspect existing code first, make conservative changes, verify behavior.
- QA: test staging before production, check both UI and Supabase/RLS behavior when relevant.
- Release manager: know which branch deploys what, confirm deploy status, and summarize residual risk.

## Handoff Expectations

When wrapping up meaningful work, explicitly communicate full follow-through:

- State the relevant Notion card status and whether it was updated.
- State the exact PR, branch, commit, deployment, or staging status.
- Give Brian clear test steps with exact URLs and expected outcomes.
- Call out anything not completed, blocked, or still requiring Brian's approval.
