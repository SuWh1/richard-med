from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app
from app.models import Clinic, ClinicServicePrice, Service, ServiceCategory


@pytest.fixture
def client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    yield TestClient(app)
    app.dependency_overrides.pop(get_db, None)


def _token(client: TestClient, email: str = "cabinet@user.dev") -> str:
    resp = client.post(
        "/api/v1/auth/signup",
        json={"email": email, "password": "password123", "name": "Cabinet"},
    )
    assert resp.status_code == 200
    return resp.json()["token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _service(db_session, key: str = "t-cabinet"):
    service = Service(
        service_key=key,
        name_ru=f"Ззз кабинет {key}",
        category=ServiceCategory.laboratory,
    )
    db_session.add(service)
    db_session.flush()
    return service


def _price(db_session, service_id: int, *, price: int, days_old: int = 1):
    clinic = Clinic(name=f"Clinic {price}", source_name="cabinet_test")
    db_session.add(clinic)
    db_session.flush()
    db_session.add(
        ClinicServicePrice(
            clinic_id=clinic.id,
            branch_id=None,
            service_id=service_id,
            city="Астана",
            price_kzt=price,
            source_url="https://example.kz/cabinet",
            parsed_at=datetime.now(UTC) - timedelta(days=days_old),
            is_active=True,
            match_confidence=1.0,
        )
    )
    db_session.flush()


def test_should_require_auth_for_cabinet(client):
    resp = client.get("/api/v1/cabinet")
    assert resp.status_code == 401


def test_should_create_list_toggle_delete_and_mark_seen_saved_service(client, db_session):
    service = _service(db_session, "t-cabinet-crud")
    _price(db_session, service.id, price=4000)
    token = _token(client)

    created = client.post(
        "/api/v1/cabinet/saved-services",
        headers=_auth(token),
        json={"service_id": service.id, "city": "Астана"},
    )
    assert created.status_code == 200
    watch = created.json()
    assert watch["current_min_price"] == 4000
    assert watch["clinic_count"] == 1

    dashboard = client.get("/api/v1/cabinet", headers=_auth(token)).json()
    assert len(dashboard["saved_services"]) == 1

    toggled = client.patch(
        f"/api/v1/cabinet/saved-services/{watch['id']}",
        headers=_auth(token),
        json={"notify_enabled": False},
    )
    assert toggled.status_code == 200
    assert toggled.json()["notify_enabled"] is False

    seen = client.post(
        f"/api/v1/cabinet/saved-services/{watch['id']}/mark-seen",
        headers=_auth(token),
    )
    assert seen.status_code == 200
    assert seen.json()["last_seen_min_price"] == 4000

    deleted = client.delete(
        f"/api/v1/cabinet/saved-services/{watch['id']}",
        headers=_auth(token),
    )
    assert deleted.status_code == 204
    dashboard = client.get("/api/v1/cabinet", headers=_auth(token)).json()
    assert dashboard["saved_services"] == []


def test_should_compute_current_price_from_fresh_prices_only(client, db_session):
    service = _service(db_session, "t-cabinet-fresh")
    _price(db_session, service.id, price=100, days_old=45)
    _price(db_session, service.id, price=3000, days_old=1)
    token = _token(client, "fresh@user.dev")

    resp = client.post(
        "/api/v1/cabinet/saved-services",
        headers=_auth(token),
        json={"service_id": service.id, "city": "Астана"},
    )

    assert resp.status_code == 200
    assert resp.json()["current_min_price"] == 3000


def test_should_derive_price_change_notification(client, db_session):
    service = _service(db_session, "t-cabinet-notify")
    _price(db_session, service.id, price=5000)
    token = _token(client, "notify@user.dev")
    watch = client.post(
        "/api/v1/cabinet/saved-services",
        headers=_auth(token),
        json={"service_id": service.id, "city": "Астана"},
    ).json()

    _price(db_session, service.id, price=4500)
    dashboard = client.get("/api/v1/cabinet", headers=_auth(token)).json()
    assert dashboard["notifications"][0]["watch_id"] == watch["id"]
    assert dashboard["notifications"][0]["previous_min_price"] == 5000
    assert dashboard["notifications"][0]["current_min_price"] == 4500
    assert dashboard["notifications"][0]["delta_kzt"] == -500

    client.post(
        f"/api/v1/cabinet/saved-services/{watch['id']}/mark-seen",
        headers=_auth(token),
    )
    dashboard = client.get("/api/v1/cabinet", headers=_auth(token)).json()
    assert dashboard["notifications"] == []


def test_should_record_and_dedupe_recent_search_history(client, db_session):
    service = _service(db_session, "t-cabinet-history")
    token = _token(client, "history@user.dev")
    payload = {
        "q": "ОАК",
        "city": "Астана",
        "service_id": service.id,
        "result_count": 2,
    }

    first = client.post("/api/v1/cabinet/search-history", headers=_auth(token), json=payload)
    second = client.post(
        "/api/v1/cabinet/search-history",
        headers=_auth(token),
        json={**payload, "result_count": 5},
    )
    dashboard = client.get("/api/v1/cabinet", headers=_auth(token)).json()

    assert first.status_code == 200
    assert second.status_code == 200
    assert len(dashboard["recent_searches"]) == 1
    assert dashboard["recent_searches"][0]["result_count"] == 5


def _priced_clinic(db_session, service_id, *, price, name, city="Астана"):
    clinic = Clinic(name=name, source_name="cabinet_test")
    db_session.add(clinic)
    db_session.flush()
    db_session.add(
        ClinicServicePrice(
            clinic_id=clinic.id,
            branch_id=None,
            service_id=service_id,
            city=city,
            price_kzt=price,
            source_url="https://example.kz/cabinet",
            parsed_at=datetime.now(UTC) - timedelta(days=1),
            is_active=True,
            match_confidence=1.0,
        )
    )
    db_session.flush()
    return clinic


def test_should_save_a_specific_clinic_offer(client, db_session):
    service = _service(db_session, "t-clinic-save")
    clinic = _priced_clinic(db_session, service.id, price=4200, name="Лучшая клиника")
    token = _token(client, "clinicsave@user.dev")

    resp = client.post(
        "/api/v1/cabinet/saved-services",
        headers=_auth(token),
        json={"service_id": service.id, "clinic_id": clinic.id, "city": "Астана"},
    )

    assert resp.status_code == 200
    watch = resp.json()
    assert watch["clinic_id"] == clinic.id
    assert watch["clinic_name"] == "Лучшая клиника"
    assert watch["current_min_price"] == 4200


def test_should_track_only_the_saved_clinics_price(client, db_session):
    service = _service(db_session, "t-clinic-track")
    _priced_clinic(db_session, service.id, price=3000, name="Дешёвая")
    pricey = _priced_clinic(db_session, service.id, price=5000, name="Дорогая")
    token = _token(client, "clinictrack@user.dev")

    resp = client.post(
        "/api/v1/cabinet/saved-services",
        headers=_auth(token),
        json={"service_id": service.id, "clinic_id": pricey.id, "city": "Астана"},
    )

    assert resp.status_code == 200
    # The saved clinic's price, not the cheapest in the city.
    assert resp.json()["current_min_price"] == 5000


def test_should_save_same_service_at_two_clinics_separately(client, db_session):
    service = _service(db_session, "t-clinic-two")
    a = _priced_clinic(db_session, service.id, price=3000, name="Клиника А")
    b = _priced_clinic(db_session, service.id, price=5000, name="Клиника Б")
    token = _token(client, "clinictwo@user.dev")

    for clinic in (a, b):
        r = client.post(
            "/api/v1/cabinet/saved-services",
            headers=_auth(token),
            json={"service_id": service.id, "clinic_id": clinic.id, "city": "Астана"},
        )
        assert r.status_code == 200

    dashboard = client.get("/api/v1/cabinet", headers=_auth(token)).json()
    saved = dashboard["saved_services"]
    assert len(saved) == 2
    assert {s["clinic_id"] for s in saved} == {a.id, b.id}
