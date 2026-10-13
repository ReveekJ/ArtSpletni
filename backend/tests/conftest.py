"""
Root pytest configuration.

Sets environment variables BEFORE any application imports so that
Settings / engine / db_guard all see the test configuration.

Registers conftest_db, conftest_storage, conftest_auth as pytest plugins.
"""

import os
import sys

os.environ["DB_GUARD_ENABLED"] = "false"
os.environ["DATABASE_URL"] = (
    "postgresql+asyncpg://test:test@localhost:5432/test-spletni"
)
os.environ["MINIO_ENDPOINT_INTERNAL"] = "localhost:9000"
os.environ["MINIO_ENDPOINT_PUBLIC"] = "localhost:9000"
os.environ["MINIO_ACCESS_KEY"] = "spletni"
os.environ["MINIO_SECRET_KEY"] = "spletni-minio-secret"
os.environ["MINIO_BUCKET"] = "tracks"
os.environ["MINIO_SECURE_INTERNAL"] = "false"
os.environ["MINIO_SECURE_PUBLIC"] = "false"
os.environ["SESSION_SECRET"] = "test-session-secret"
os.environ["ADMIN_USERNAME"] = "admin"
os.environ["ADMIN_PASSWORD"] = "admin-spletni"
os.environ["YANDEX_CLIENT_ID"] = "test-yandex-id"
os.environ["YANDEX_CLIENT_SECRET"] = "test-yandex-secret"
os.environ["YANDEX_REDIRECT_URI"] = (
    "http://localhost:5173/api/auth/yandex/callback"
)
os.environ["PUBLIC_BASE_URL"] = "http://localhost:5173"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import get_settings

get_settings.cache_clear()

pytest_plugins = [
    "tests.conftest_db",
    "tests.conftest_storage",
    "tests.conftest_auth",
]
