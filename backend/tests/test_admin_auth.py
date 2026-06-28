from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.core import auth as authmod
from app.core.auth import require_admin


def _client() -> TestClient:
    app = FastAPI()

    @app.get("/protected")
    def protected(claims: dict = Depends(require_admin)) -> dict:
        return {"ok": True, "role": claims.get("role")}

    return TestClient(app)


def test_should_reject_request_without_a_token():
    resp = _client().get("/protected")
    assert resp.status_code == 401


def test_should_reject_an_invalid_token():
    resp = _client().get("/protected", headers={"Authorization": "Bearer garbage"})
    assert resp.status_code == 401


def test_should_forbid_a_non_admin(monkeypatch):
    monkeypatch.setattr(authmod, "verify_jwt", lambda _t: {"role": "user"})
    resp = _client().get("/protected", headers={"Authorization": "Bearer ok"})
    assert resp.status_code == 403


def test_should_allow_an_admin(monkeypatch):
    monkeypatch.setattr(authmod, "verify_jwt", lambda _t: {"role": "admin"})
    resp = _client().get("/protected", headers={"Authorization": "Bearer ok"})
    assert resp.status_code == 200
    assert resp.json()["role"] == "admin"


def test_should_read_role_from_nested_user_claim(monkeypatch):
    monkeypatch.setattr(authmod, "verify_jwt", lambda _t: {"user": {"role": "admin"}})
    resp = _client().get("/protected", headers={"Authorization": "Bearer ok"})
    assert resp.status_code == 200
