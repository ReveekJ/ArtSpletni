# Project structure

## Backend (`server/`)

Litestar + Advanced Alchemy (SQLAlchemy 2, PostgreSQL), msgspec schemas, uv.

```text
server/
├── app/
│   ├── asgi.py              # create_app(): plugins, middleware, controllers, CLI commands
│   ├── config.py            # SQLAlchemy config, session/rate-limit stores, e-mail
│   ├── lib/                 # cross-cutting: settings, errors, i18n type, security, request typing
│   ├── db/
│   │   ├── models/          # ORM models (one module per aggregate)
│   │   └── migrations/      # Alembic (via `litestar database ...`)
│   └── domain/<name>/       # one package per domain
│       ├── controllers.py   # HTTP layer only: parse input, call a service, map to schema
│       ├── services.py      # business rules; raise ApplicationError subclasses
│       ├── repositories.py  # data access (Advanced Alchemy repositories, SQL)
│       ├── schemas.py       # msgspec request/response contracts (camelCase on the wire)
│       └── deps.py          # Litestar DI providers
└── tests/                   # pytest, one marker per domain (see pyproject.toml)
```

### Layering rules

- Controller → service → repository → model. Controllers never touch repositories or SQL.
- Authorization lives in guards (`domain/auth/guards.py`, `domain/partners/guards.py`), never in handler bodies.
- Services raise `app.lib.exceptions.ApplicationError` subclasses; the handler maps them to `{detail, code}` JSON.
  `code` is a stable machine-readable key for the frontend.
- Cross-domain reactions go through `ProgressEventBus` (`domain/runs/events.py`):
  scans publish `PointUnlocked` / `StopVisited` / `RouteCompleted`; offers and achievements subscribe.
- Guest data is merged into an account through `GuestDataMerger` implementations registered in
  `domain/auth/deps.py::provide_guest_mergers`. Any new per-user table must add a merger.

### Domains

| Domain | Responsibility |
| --- | --- |
| `auth`, `users` | email/password, Yandex ID (state + PKCE), guests, sessions, password reset, `create-admin` CLI |
| `media` | presigned direct uploads to S3, private/public assets |
| `i18n` | content languages, `LocalizedText`, machine translation provider |
| `points`, `nfc` | points with content blocks, NFC tag secrets (hash only), collection |
| `routes` | route building, ordering modes, dependency graph validation (`progress.py`) |
| `runs`, `scans` | scan resolution, route runs, map visibility, progress events |
| `partners`, `offers` | partners and staff, offers, grants, QR/code redemption |
| `achievements` | rule-based achievements, rewards, `seed-achievements` CLI |
| `gossip` | LLM-written stories about the surroundings of a point: Wikimedia context, OpenAI-compatible writer, background generation, admin moderation |
| `submissions`, `analytics` | user stories with moderation, playback and admin dashboards |

### Commands

```bash
cd server && uv sync
uv run ruff check . && uv run ruff format --check . && uv run mypy app tests
TEST_DATABASE_URL=postgresql+asyncpg://user@host:port/db uv run pytest -m runs
LITESTAR_APP=app.asgi:create_app uv run litestar database make-migrations -m "message"
LITESTAR_APP=app.asgi:create_app uv run litestar database upgrade
LITESTAR_APP=app.asgi:create_app uv run litestar create-admin --email admin@example.com
LITESTAR_APP=app.asgi:create_app uv run litestar seed-achievements
```

Without `TEST_DATABASE_URL` the tests start PostgreSQL through `pytest-databases` (Docker).
