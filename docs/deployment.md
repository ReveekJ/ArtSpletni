# Deployment

The stack is `server/` (Litestar API) and `web/` (React SPA served by nginx, proxying `/api` and `/schema` to `server`).

## Local

```bash
cp .env.example .env
docker compose up --build
```

- `minio-init` creates the bucket; the server never creates it itself.
- Web: http://localhost:5174, API: http://localhost:8000, OpenAPI UI: http://localhost:8000/schema.

First run, inside the `server` container:

```bash
docker compose exec server uv run --no-dev litestar create-admin --email admin@example.com
docker compose exec server uv run --no-dev litestar seed-achievements
docker compose exec server uv run --no-dev litestar seed-demo-users
docker compose exec server uv run --no-dev litestar seed-demo-content
```

`seed-demo-users` creates quick-login accounts (admin, partner staff, several players) listed in
`server/app/domain/auth/demo.py`. The login page shows them only when `DEMO_LOGIN_ENABLED=true`;
anyone who opens the site can then log in as the demo admin.

`seed-demo-content` creates demo routes in Yekaterinburg and Moscow with points, covers, narrated audio,
partners and offers (`server/app/domain/demo/`), skips routes whose slug already exists and prints NFC scan links.

## Production (ansible)

Templates: `ansible/roles/stack/templates/compose.yml.j2`, `app.env.j2`.

- The schema starts from a fresh migration. A database created by the legacy backend contains its own
  `alembic_version` and tables, so it must be recreated before the first deploy of the new stack.
- `SECRET_KEY` must be at least 32 characters; the template falls back to `session_secret` when `secret_key` is not set.
- Optional integrations are enabled by defining variables: `yandex_client_id`/`yandex_client_secret`,
  `smtp_host` (+ `smtp_port`, `smtp_username`, `smtp_password`), `google_translate_project_id`
  (the service-account JSON must be mounted at `/run/secrets/google-translate.json`).
- The nearby-gossip feature needs `LLM__*` variables in `app.env` (see "Nearby gossip (LLM)" below).
- MinIO is published by traefik under `/<minio_bucket>/`, which matches presigned URLs on `https://<site_domain>`.
- After the first deploy run `create-admin` and `seed-achievements` in the `server` container.
- Yandex ID is off unless `yandex_client_id` is defined; the login page hides the button when it is off.
- Demo quick login is off unless `demo_login_enabled: true` (then run `seed-demo-users`).

## Nearby gossip (LLM)

Points show LLM-written stories about places around them (Wikipedia and Wikimedia Commons are the sources).
The feature is off until the server gets `LLM__BASE_URL` and `LLM__MODEL`; `LLM__BASE_URL` is any
OpenAI-compatible endpoint (the server calls `<base_url>/chat/completions`).

- Optional: `LLM__API_KEY`, `LLM__TIMEOUT_SECONDS` (120), `LLM__TEMPERATURE` (0.9), `LLM__JSON_MODE` (true),
  `LLM__EXTRA_BODY` (JSON merged into the request body, e.g. provider-specific options),
  `GOSSIP__RADIUS_M` (500), `GOSSIP__MAX_ITEMS` (8), `GOSSIP__FAILED_RETRY_MINUTES` (60).
- Generation runs in the API process as a background task, no queue or worker is needed. The first unlocked view
  of a point starts it; moving the point or an admin "Regenerate" starts it again. A run interrupted by a restart
  is retried on the next view once it is considered stale.
- The server needs outbound HTTPS to `*.wikipedia.org`, `commons.wikimedia.org` and the LLM endpoint.
- Admins review and hide stories in the point editor; players see the translations in their language.

## CI

`.github/workflows/build-images.yml` checks the server (ruff, mypy, pytest against a `postgres` service container)
and the web app (lint, build), then publishes `artspletni-backend` from `server/` and `artspletni-frontend` from `web/`.
The `validate` job relies on `services`, which the `arc-runners` runner must support.

## Legacy code

The previous `backend/` and `frontend/` were removed. The unfinished LLM gossip generation was ported to
`server/app/domain/gossip/` (no RabbitMQ worker, see above). The old sources remain in the git stash
(`git stash list`, message starting with "legacy backend/frontend").
