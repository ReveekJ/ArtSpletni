#!/bin/sh
set -e

uv sync --frozen --no-install-project --no-dev || uv sync --no-install-project --no-dev

uv run python -m app.core.db_guard

uv run alembic upgrade head

if [ "${UVICORN_RELOAD:-false}" = "true" ]; then
  exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
fi

exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
