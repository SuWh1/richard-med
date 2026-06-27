from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import app
from app.models import Clinic, ClinicBranch, ClinicServicePrice, Service
from app.services.clinics import clinic_detail, clinic_services, compare

client = TestClient(app)


def _service_ids(session, n=2):
    return session.scalars(
        select(Service.id)
        .outerjoin(ClinicServicePrice, ClinicServicePrice.service_id == Service.id)
        .where(ClinicServicePrice.id.is_(None))
        .limit(n)
    ).all()


def _make_clinic(session, name, *, branches=1):
    clinic = Clinic(name=name, source_name="test_clinics", website_url="https://x.kz")
    session.add(clinic)
    session.flush()
    made = []
    for i in range(branches):
        branch = ClinicBranch(
            clinic_id=clinic.id,
            city="Астана",
            address=f"ул. Тест {i}",
            lat=51.1,
            lng=71.4,
            phone="+7 700 000 0000",
        )
        session.add(branch)
        session.flush()
        made.append(branch)
    return clinic, made


def _price(session, clinic, branch, service_id, *, price, age_days=1, city="Астана"):
    row = ClinicServicePrice(
        clinic_id=clinic.id,
        branch_id=branch.id if branch else None,
        service_id=service_id,
        city=branch.city if branch else city,
        price_kzt=price,
        source_url="https://x.kz/p",
        parsed_at=datetime.now(UTC) - timedelta(days=age_days),
        is_active=True,
        match_confidence=1.0,
    )
    session.add(row)
    session.flush()
    return row


def test_should_return_clinic_detail_with_branches(db_session):
    clinic, _ = _make_clinic(db_session, "Клиника А", branches=2)

    detail = clinic_detail(db_session, clinic.id)

    assert detail is not None
    assert detail.name == "Клиника А"
    assert len(detail.branches) == 2
    assert detail.branches[0].city == "Астана"


def test_should_return_none_for_unknown_clinic(db_session):
    assert clinic_detail(db_session, 9_999_999) is None


def test_should_list_active_services_for_a_clinic(db_session):
    sid1, sid2 = _service_ids(db_session, 2)
    clinic, branches = _make_clinic(db_session, "Клиника Б")
    _price(db_session, clinic, branches[0], sid1, price=1880)
    _price(db_session, clinic, branches[0], sid2, price=3200)

    rows = clinic_services(db_session, clinic.id)

    assert len(rows) == 2
    assert {r.price_kzt for r in rows} == {1880, 3200}
    assert all(r.freshness == "fresh" for r in rows)


def test_should_compare_service_across_clinics_and_flag_cheapest(db_session):
    sid = _service_ids(db_session, 1)[0]
    clinic_a, a_branches = _make_clinic(db_session, "Клиника А")
    clinic_b, b_branches = _make_clinic(db_session, "Клиника Б")
    _price(db_session, clinic_a, a_branches[0], sid, price=2050)
    _price(db_session, clinic_b, b_branches[0], sid, price=1880)

    result = compare(db_session, sid, [clinic_a.id, clinic_b.id])

    assert result is not None
    assert len(result.rows) == 2
    cheapest = [r for r in result.rows if r.is_cheapest]
    assert len(cheapest) == 1
    assert cheapest[0].clinic_id == clinic_b.id


def test_should_return_none_comparing_unknown_service(db_session):
    assert compare(db_session, 9_999_999, [1]) is None


def test_should_404_for_unknown_clinic_endpoint():
    assert client.get("/api/v1/clinics/9999999").status_code == 404


def test_should_return_clinic_detail_endpoint():
    cards = client.get("/api/v1/search", params={"q": "ОАК", "city": "Астана"}).json()["cards"]
    clinic_id = cards[0]["clinic_id"]

    resp = client.get(f"/api/v1/clinics/{clinic_id}")

    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == clinic_id
    assert isinstance(body["branches"], list)


def test_should_compare_endpoint_across_clinics():
    search = client.get("/api/v1/search", params={"q": "ОАК", "city": "Астана"}).json()
    service_id = search["resolved_service"]["id"]
    clinic_ids = [c["clinic_id"] for c in search["cards"][:2]]
    assert len(clinic_ids) == 2

    resp = client.get(
        "/api/v1/search/compare",
        params={"service_id": service_id, "clinic_ids": ",".join(map(str, clinic_ids))},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert len(body["rows"]) == 2
    assert sum(1 for r in body["rows"] if r["is_cheapest"]) == 1
