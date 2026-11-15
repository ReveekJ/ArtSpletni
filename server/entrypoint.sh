#!/bin/sh
set -e

uv run --no-dev litestar database upgrade --no-prompt

exec uv run --no-dev uvicorn app.asgi:create_app --factory \
  --host 0.0.0.0 --port 8000 \
  --proxy-headers --forwarded-allow-ips="${FORWARDED_ALLOW_IPS:-127.0.0.1}"
