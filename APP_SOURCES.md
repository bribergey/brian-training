# App source of truth

The `staging` branch deploys only these HTML sources:

- `marketing_STAGING.html` → `/staging/` and `/staging/home/`
- `brian_STAGING.html` → `/staging/app/`

Production deploys from the `main` branch only:

- `index.html` → `/`
- `app/index.html` → `/app/`

Do not create or edit parallel app copies such as `brian_master.html` or
`brian_PRODUCTION.html`. Changes must start in the canonical staging app,
pass the app-contract check and staging QA, then be intentionally ported to
`main/app/index.html` in a production pull request.
