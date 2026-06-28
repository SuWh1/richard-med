from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.core.auth import create_token, require_admin
from app.models import User


def _client() -> TestClient:
    app = FastAPI()

    @app.get("/protected")
    def protected(claims: dict = Depends(require_admin)) -> dict:
        return {"ok": True, "role": claims.get("role")}

    return TestClient(app)


def _token(role: str) -> str:
    return create_token(User(id=1, email="x@y.z", password_hash="", name=None, role=role))


def test_should_reject_request_without_a_token():
    assert _client().get("/protected").status_code == 401


def test_should_reject_an_invalid_token():
    resp = _client().get("/protected", headers={"Authorization": "Bearer garbage"})
    assert resp.status_code == 401


def test_should_forbid_a_non_admin():
    resp = _client().get(
        "/protected", headers={"Authorization": f"Bearer {_token('user')}"}
    )
    assert resp.status_code == 403


def test_should_allow_an_admin():
    resp = _client().get(
        "/protected", headers={"Authorization": f"Bearer {_token('admin')}"}
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "admin"
