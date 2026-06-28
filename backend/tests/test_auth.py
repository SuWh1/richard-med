import pytest
from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app

SIGNUP = "/api/v1/auth/signup"
LOGIN = "/api/v1/auth/login"
ME = "/api/v1/auth/me"


@pytest.fixture
def client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    yield TestClient(app)
    app.dependency_overrides.pop(get_db, None)


def test_should_register_a_user_and_return_a_token(client):
    resp = client.post(
        SIGNUP, json={"email": "new@user.dev", "password": "password123", "name": "New"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["token"]
    assert body["user"]["email"] == "new@user.dev"
    assert body["user"]["role"] == "user"


def test_should_grant_admin_role_to_an_allowlisted_email(client):
    resp = client.post(
        SIGNUP, json={"email": "apasdauren70@gmail.com", "password": "password123"}
    )
    assert resp.json()["user"]["role"] == "admin"


def test_should_reject_a_duplicate_email(client):
    client.post(SIGNUP, json={"email": "dup@user.dev", "password": "password123"})
    resp = client.post(SIGNUP, json={"email": "dup@user.dev", "password": "password123"})
    assert resp.status_code == 409


def test_should_reject_a_too_short_password(client):
    resp = client.post(SIGNUP, json={"email": "short@user.dev", "password": "123"})
    assert resp.status_code == 422


def test_should_log_in_with_the_correct_password(client):
    client.post(SIGNUP, json={"email": "login@user.dev", "password": "password123"})
    resp = client.post(LOGIN, json={"email": "login@user.dev", "password": "password123"})
    assert resp.status_code == 200
    assert resp.json()["token"]


def test_should_reject_a_wrong_password(client):
    client.post(SIGNUP, json={"email": "wp@user.dev", "password": "password123"})
    resp = client.post(LOGIN, json={"email": "wp@user.dev", "password": "nope"})
    assert resp.status_code == 401


def test_should_return_the_current_user_from_me(client):
    token = client.post(
        SIGNUP, json={"email": "me@user.dev", "password": "password123"}
    ).json()["token"]
    resp = client.get(ME, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "me@user.dev"


def test_should_reject_me_without_a_token(client):
    assert client.get(ME).status_code == 401
