from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import app
from app.models import Clinic, ClinicBranch, ClinicServicePrice, Service
from app.services.search import map_pins

client = TestClient(app)


def _unseeded_service_id(session) -> int:
    """A catalog service with no existing prices, so our test rows stand alone."""
    return session.scalars(
        select(Service.id)
        .outerjoin(ClinicServicePrice, ClinicServicePrice.service_id == Service.id)
        .where(ClinicServicePrice.id.is_(None))
        .limit(1)
    ).one()


def _seed_price(
    session,
    service_id,
    *,
    price,
    city="Астана",
    lat=51.1282,
    lng=71.4307,
    age_days=1,
    address="addr",
):
    clinic = Clinic(name=f"Clinic {price}", source_name="test_map")
    session.add(clinic)
    session.flush()
    branch = ClinicBranch(clinic_id=clinic.id, city=city, address=address, lat=lat, lng=lng)
    session.add(branch)
    session.flush()
    price_row = ClinicServicePrice(
        clinic_id=clinic.id,
        branch_id=branch.id,
        service_id=service_id,
        price_kzt=price,
        source_url="https://example.kz/x",
        parsed_at=datetime.now(UTC) - timedelta(days=age_days),
        is_active=True,
        match_confidence=1.0,
    )
    session.add(price_row)
    session.flush()
    return price_row


def test_should_return_pins_with_coords_and_flag_cheapest(db_session):
    sid = _unseeded_service_id(db_session)
    _seed_price(db_session, sid, price=1880, lng=71.4307)
    _seed_price(db_session, sid, price=2050, lng=71.4400)

    pins = map_pins(db_session, sid)

    assert len(pins) == 2
    assert all(p.lat is not None and p.lng is not None for p in pins)
    cheapest = [p for p in pins if p.is_cheapest]
    assert len(cheapest) == 1
    assert cheapest[0].price_kzt == 1880


def test_should_exclude_branch_without_coordinates(db_session):
    sid = _unseeded_service_id(db_session)
    _seed_price(db_session, sid, price=1880)
    _seed_price(db_session, sid, price=999, lat=None, lng=None)

    pins = map_pins(db_session, sid)

    assert len(pins) == 1
    assert pins[0].price_kzt == 1880


def test_should_exclude_stale_pins_from_map(db_session):
    sid = _unseeded_service_id(db_session)
    _seed_price(db_session, sid, price=1880, age_days=1)
    _seed_price(db_session, sid, price=1500, age_days=40)

    pins = map_pins(db_session, sid)

    assert len(pins) == 1
    assert pins[0].freshness == "fresh"


def test_should_filter_pins_by_city(db_session):
    sid = _unseeded_service_id(db_session)
    _seed_price(db_session, sid, price=1880, city="Астана", lat=51.13, lng=71.43)
    _seed_price(db_session, sid, price=2050, city="Алматы", lat=43.23, lng=76.94)

    pins = map_pins(db_session, sid, city="Алматы")

    assert len(pins) == 1
    assert pins[0].city == "Алматы"


def test_should_filter_pins_by_bbox(db_session):
    sid = _unseeded_service_id(db_session)
    _seed_price(db_session, sid, price=1880, city="Астана", lat=51.13, lng=71.43)
    _seed_price(db_session, sid, price=2050, city="Алматы", lat=43.23, lng=76.94)

    # bbox = (min_lng, min_lat, max_lng, max_lat) — Leaflet's toBBoxString order.
    pins = map_pins(db_session, sid, bbox=(71.0, 50.5, 72.0, 51.6))

    assert len(pins) == 1
    assert pins[0].city == "Астана"


def test_should_return_map_pins_endpoint_for_oak():
    resolved = client.get("/api/v1/search", params={"q": "ОАК", "city": "Астана"}).json()
    service_id = resolved["resolved_service"]["id"]

    resp = client.get("/api/v1/search/map", params={"service_id": service_id, "city": "Астана"})

    assert resp.status_code == 200
    pins = resp.json()
    assert len(pins) >= 2
    assert all(p["lat"] is not None and p["lng"] is not None for p in pins)
    assert sum(1 for p in pins if p["is_cheapest"]) == 1


def test_should_reject_map_request_without_service_id():
    resp = client.get("/api/v1/search/map")
    assert resp.status_code == 422


def test_should_reject_bbox_with_non_finite_values():
    resp = client.get(
        "/api/v1/search/map", params={"service_id": 1, "bbox": "0,0,nan,90"}
    )
    assert resp.status_code == 422


def test_should_reject_malformed_bbox():
    resp = client.get("/api/v1/search/map", params={"service_id": 1, "bbox": "1,2,3"})
    assert resp.status_code == 422
