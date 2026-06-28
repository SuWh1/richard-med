from contextlib import contextmanager
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.session import SessionLocal

from app.main import app
from app.models import (
    Clinic,
    ClinicBranch,
    ClinicReview,
    ClinicServicePrice,
    Service,
)
from app.services.clinics import (
    clinic_detail,
    clinic_reviews,
    clinic_services,
    compare,
)

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


def _add_review(session, branch, *, rating, text, days_ago=1, author="Гость"):
    review = ClinicReview(
        branch_id=branch.id,
        author=author,
        rating=rating,
        text=text,
        review_date=datetime.now(UTC) - timedelta(days=days_ago),
        source="2gis",
        synced_at=datetime.now(UTC),
    )
    session.add(review)
    session.flush()
    return review


def test_should_aggregate_branch_ratings_weighted_by_review_count(db_session):
    clinic, branches = _make_clinic(db_session, "Клиника Рейтинг", branches=2)
    branches[0].rating, branches[0].reviews_count = 5.0, 100
    branches[1].rating, branches[1].reviews_count = 4.0, 300
    db_session.flush()

    detail = clinic_detail(db_session, clinic.id)

    assert detail is not None
    assert detail.reviews_count == 400
    # weighted: (5*100 + 4*300) / 400 = 4.25
    assert detail.rating == 4.25
    assert {b.rating for b in detail.branches} == {5.0, 4.0}


def test_should_report_no_rating_when_no_branch_has_reviews(db_session):
    clinic, _ = _make_clinic(db_session, "Без отзывов")

    detail = clinic_detail(db_session, clinic.id)

    assert detail is not None
    assert detail.rating is None
    assert detail.reviews_count == 0


def test_should_return_clinic_reviews_newest_first(db_session):
    clinic, branches = _make_clinic(db_session, "Клиника Отзывы")
    _add_review(db_session, branches[0], rating=4, text="нормально", days_ago=10)
    _add_review(db_session, branches[0], rating=5, text="отлично", days_ago=1)

    reviews = clinic_reviews(db_session, clinic.id, limit=10, offset=0)

    assert [r.text for r in reviews] == ["отлично", "нормально"]
    assert reviews[0].rating == 5


def test_should_paginate_clinic_reviews(db_session):
    clinic, branches = _make_clinic(db_session, "Много отзывов")
    for i in range(5):
        _add_review(db_session, branches[0], rating=5, text=f"r{i}", days_ago=i)

    page = clinic_reviews(db_session, clinic.id, limit=2, offset=2)

    assert len(page) == 2


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


def test_should_compute_cost_feedback_relative_to_cheapest(db_session):
    sid = _service_ids(db_session, 1)[0]
    clinic_a, a_branches = _make_clinic(db_session, "Клиника А")
    clinic_b, b_branches = _make_clinic(db_session, "Клиника Б")
    _price(db_session, clinic_a, a_branches[0], sid, price=2200)
    _price(db_session, clinic_b, b_branches[0], sid, price=2000)

    result = compare(db_session, sid, [clinic_a.id, clinic_b.id])

    assert result is not None
    by_clinic = {r.clinic_id: r for r in result.rows}
    cheapest = by_clinic[clinic_b.id]
    pricier = by_clinic[clinic_a.id]

    assert cheapest.price_delta == 0
    assert cheapest.delta_pct == 0.0
    assert cheapest.price_rank == 1

    assert pricier.price_delta == 200
    assert pricier.delta_pct == 10.0
    assert pricier.price_rank == 2


def test_should_rank_single_clinic_as_cheapest(db_session):
    sid = _service_ids(db_session, 1)[0]
    clinic, branches = _make_clinic(db_session, "Клиника А")
    _price(db_session, clinic, branches[0], sid, price=1880)

    result = compare(db_session, sid, [clinic.id])

    assert result is not None
    row = result.rows[0]
    assert row.price_delta == 0
    assert row.delta_pct == 0.0
    assert row.price_rank == 1


def test_should_fall_back_to_price_city_when_no_branch(db_session):
    sid = _service_ids(db_session, 1)[0]
    clinic, _ = _make_clinic(db_session, "KDL Olymp")
    _price(db_session, clinic, None, sid, price=6600, city="Шымкент")

    result = compare(db_session, sid, [clinic.id])

    assert result is not None
    assert result.rows[0].branch_id is None
    assert result.rows[0].city == "Шымкент"


def test_should_prefer_prices_in_the_requested_city(db_session):
    sid = _service_ids(db_session, 1)[0]
    a, _ = _make_clinic(db_session, "Invitro")
    b, _ = _make_clinic(db_session, "KDL Olymp")
    _price(db_session, a, None, sid, price=2200, city="Астана")
    _price(db_session, a, None, sid, price=2000, city="Костанай")
    _price(db_session, b, None, sid, price=6600, city="Астана")
    _price(db_session, b, None, sid, price=6000, city="Костанай")

    result = compare(db_session, sid, [a.id, b.id], city="Астана")

    assert result is not None
    by_clinic = {r.clinic_id: r for r in result.rows}
    assert by_clinic[a.id].city == "Астана"
    assert by_clinic[b.id].city == "Астана"
    assert by_clinic[a.id].price_kzt == 2200
    assert by_clinic[b.id].price_kzt == 6600
    assert by_clinic[a.id].is_cheapest is True


def test_should_fall_back_to_cheapest_when_clinic_has_no_price_in_city(db_session):
    sid = _service_ids(db_session, 1)[0]
    a, _ = _make_clinic(db_session, "Invitro")
    _price(db_session, a, None, sid, price=3000, city="Алматы")

    result = compare(db_session, sid, [a.id], city="Астана")

    assert result is not None
    assert result.rows[0].city == "Алматы"
    assert result.rows[0].price_kzt == 3000


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


@contextmanager
def _committed_clinic(name, *, rating=None, reviews_count=None, review_text=None):
    """HTTP tests hit a separate DB connection, so seed with a real commit and clean up."""
    session = SessionLocal()
    try:
        clinic, branches = _make_clinic(session, name)
        if rating is not None:
            branches[0].rating = rating
            branches[0].reviews_count = reviews_count
        if review_text is not None:
            _add_review(session, branches[0], rating=5, text=review_text)
        session.commit()
        clinic_id = clinic.id
        yield clinic_id
    finally:
        obj = session.get(Clinic, clinic_id)
        if obj is not None:
            session.delete(obj)
            session.commit()
        session.close()


def test_should_return_clinic_reviews_endpoint():
    with _committed_clinic(
        "Эндпоинт Отзывы", rating=4.8, reviews_count=2, review_text="супер"
    ) as clinic_id:
        resp = client.get(f"/api/v1/clinics/{clinic_id}/reviews")

        assert resp.status_code == 200
        body = resp.json()
        assert body[0]["text"] == "супер"
        assert body[0]["rating"] == 5


def test_should_404_reviews_for_unknown_clinic():
    assert client.get("/api/v1/clinics/9999999/reviews").status_code == 404


def test_should_expose_rating_on_clinic_detail_endpoint():
    with _committed_clinic("Рейтинг Эндпоинт", rating=4.9, reviews_count=50) as clinic_id:
        body = client.get(f"/api/v1/clinics/{clinic_id}").json()

        assert body["rating"] == 4.9
        assert body["reviews_count"] == 50
        assert body["branches"][0]["rating"] == 4.9


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
