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
```

## Production (ansible)

Templates: `ansible/roles/stack/templates/compose.yml.j2`, `app.env.j2`.

- The schema starts from a fresh migration. A database created by the legacy backend contains its own
  `alembic_version` and tables, so it must be recreated before the first deploy of the new stack.
- `SECRET_KEY` must be at least 32 characters; the template falls back to `session_secret` when `secret_key` is not set.
- Optional integrations are enabled by defining variables: `yandex_client_id`/`yandex_client_secret`,
  `smtp_host` (+ `smtp_port`, `smtp_username`, `smtp_password`), `google_translate_project_id`
  (the service-account JSON must be mounted at `/run/secrets/google-translate.json`).
- MinIO is published by traefik under `/<minio_bucket>/`, which matches presigned URLs on `https://<site_domain>`.
- After the first deploy run `create-admin` and `seed-achievements` in the `server` container.

## CI

`.github/workflows/build-images.yml` checks the server (ruff, mypy, pytest against a `postgres` service container)
and the web app (lint, build), then publishes `artspletni-backend` from `server/` and `artspletni-frontend` from `web/`.
The `validate` job relies on `services`, which the `arc-runners` runner must support.

## Legacy code

The previous `backend/` and `frontend/`, including the unfinished LLM gossip generation, were removed.
Their last uncommitted state is kept in a git stash (`git stash list`, message starting with "legacy backend/frontend").
