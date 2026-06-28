"""Native email/password auth: bcrypt hashing + our own HS256 JWT.

The frontend sends the JWT as a Bearer token; we verify it with our secret and gate
admin endpoints on the `role` claim — so /admin/* is protected server-side, not just
in the UI.
"""

from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings
from app.models import User

_ALGO = "HS256"
_TOKEN_TTL = timedelta(days=30)
_bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    except (ValueError, TypeError):
        return False


def role_for_email(email: str) -> str:
    return "admin" if email.strip().lower() in settings.admin_emails else "user"


def create_token(user: User) -> str:
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "iat": now,
            "exp": now + _TOKEN_TTL,
        },
        settings.AUTH_SECRET,
        algorithm=_ALGO,
    )


def verify_token(token: str) -> dict:
    return jwt.decode(token, settings.AUTH_SECRET, algorithms=[_ALGO])


def _claims(cred: HTTPAuthorizationCredentials | None) -> dict:
    if cred is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Требуется авторизация")
    try:
        return verify_token(cred.credentials)
    except Exception as exc:  # noqa: BLE001 — any verification failure is unauthorized
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Недействительный токен"
        ) from exc


def require_user(
    cred: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict:
    """Any signed-in user."""
    return _claims(cred)


def require_admin(
    cred: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict:
    """Admin role required."""
    claims = _claims(cred)
    if claims.get("role") != "admin":
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Доступ только для администраторов"
        )
    return claims
