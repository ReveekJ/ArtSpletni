import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from app.lib.security import constant_time_equals, sign

CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
CODE_LENGTH = 10
QR_TOKEN_TTL = timedelta(minutes=5)


def generate_redemption_code() -> str:
    return "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))


def normalize_code(code: str) -> str:
    return code.strip().upper().replace("-", "").replace(" ", "")


def issue_qr_token(grant_id: UUID, key: str, now: datetime) -> tuple[str, datetime]:
    expires_at = now + QR_TOKEN_TTL
    payload = f"{grant_id}.{int(expires_at.timestamp())}"
    return f"{payload}.{sign(payload, key)[:32]}", expires_at


def verify_qr_token(token: str, key: str, now: datetime) -> UUID | None:
    parts = token.split(".")
    if len(parts) != 3:
        return None
    raw_id, raw_exp, signature = parts
    if not constant_time_equals(signature, sign(f"{raw_id}.{raw_exp}", key)[:32]):
        return None
    try:
        grant_id = UUID(raw_id)
        expires_at = datetime.fromtimestamp(int(raw_exp), UTC)
    except ValueError:
        return None
    return grant_id if expires_at > now else None
