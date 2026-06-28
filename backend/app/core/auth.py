"""Verify Better Auth sessions on the backend.

The frontend gets a JWT from Better Auth (the `jwt` plugin) and sends it as a Bearer
token. We verify the signature against Better Auth's JWKS and gate admin endpoints on
the `role` claim — so /admin/* is protected server-side, not just in the UI.
"""

import os

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

_JWKS_URL = (
    os.environ.get("BETTER_AUTH_JWKS_URL") or "http://localhost:3001/api/auth/jwks"
)
# Lazy: no network call until the first token is verified.
_jwk_client = PyJWKClient(_JWKS_URL)
_bearer = HTTPBearer(auto_error=False)


def verify_jwt(token: str) -> dict:
    """Verify a Better Auth JWT against the JWKS. Raises on any failure."""
    signing_key = _jwk_client.get_signing_key_from_jwt(token).key
    return jwt.decode(
        token,
        signing_key,
        algorithms=["EdDSA"],
        options={"verify_aud": False},
    )


def _role_of(claims: dict) -> str | None:
    role = claims.get("role")
    if isinstance(role, str):
        return role
    user = claims.get("user")
    if isinstance(user, dict):
        return user.get("role")
    return None


def require_admin(
    cred: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict:
    """FastAPI dependency: a valid Better Auth session with the admin role."""
    # Local-dev only: open the admin API without a token (pairs with VITE_DEV_ADMIN).
    # Never set this in production. Off by default → admin endpoints stay protected.
    if os.environ.get("AUTH_DEV_BYPASS") == "true":
        return {"role": "admin", "id": "dev"}
    if cred is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Требуется авторизация")
    try:
        claims = verify_jwt(cred.credentials)
    except Exception as exc:  # noqa: BLE001 — any verification failure is unauthorized
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Недействительный токен"
        ) from exc
    if _role_of(claims) != "admin":
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Доступ только для администраторов"
        )
    return claims
