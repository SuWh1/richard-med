from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.session import get_db
from app.main import app
from app.models import (
    Clinic,
    ClinicBranch,
    ClinicServicePrice,
    Service,
    ServiceCategory,
)
from app.services import search

client = TestClient(app)


def _unseeded_service_id(session) -> int:
    return session.scalars(
        select(Service.id)
        .outerjoin(ClinicServicePrice, ClinicServicePrice.service_id == Service.id)
        .where(ClinicServicePrice.id.is_(None))
        .limit(1)
    ).one()


def _city_price(session, service_id, *, branches, city="Алматы", price=5000):
    """A city-wide price (branch_id NULL) for a clinic with N geocoded branches."""
    clinic = Clinic(name=f"Chain {price}", source_name="test_fanout")
    session.add(clinic)
    session.flush()
    for lat, lng, addr in branches:
        session.add(
            ClinicBranch(clinic_id=clinic.id, city=city, address=addr, lat=lat, lng=lng)
        )
    session.add(
        ClinicServicePrice(
            clinic_id=clinic.id,
            branch_id=None,
            service_id=service_id,
            city=city,
            price_kzt=price,
            source_url="https://example.kz/x",
            parsed_at=datetime.now(UTC) - timedelta(days=1),
            is_active=True,
            match_confidence=1.0,
        )
    )
    session.flush()
    return clinic


def test_should_collapse_city_wide_price_to_one_card_per_clinic(db_session):
    sid = _unseeded_service_id(db_session)
    _city_price(
        db_session,
        sid,
        branches=[(43.20, 76.90, "ул. A1"), (43.25, 76.95, "ул. A2")],
    )

    cards = search.prices_for_service(db_session, sid, city="Алматы")

    assert len(cards) == 1
    assert cards[0].branch_count == 2
    assert cards[0].branch_id is not None and cards[0].lat is not None
    assert cards[0].price_kzt == 5000


def test_should_bind_clinic_card_to_branch_nearest_to_user(db_session):
    sid = _unseeded_service_id(db_session)
    _city_price(
        db_session,
        sid,
        branches=[(43.20, 76.90, "ул. A1"), (43.25, 76.95, "ул. A2")],
    )

    cards = search.prices_for_service(
        db_session, sid, city="Алматы", lat=43.249, lng=76.949
    )

    assert len(cards) == 1
    assert cards[0].address == "ул. A2"


def test_should_keep_one_card_when_clinic_has_no_geocoded_branch(db_session):
    sid = _unseeded_service_id(db_session)
    _city_price(db_session, sid, branches=[])

    cards = search.prices_for_service(db_session, sid, city="Алматы")

    assert len(cards) == 1
    assert cards[0].branch_id is None
    assert cards[0].branch_count == 0


def test_should_exclude_quarantined_services_from_autocomplete(db_session):
    db_session.add_all(
        [
            Service(
                service_key="t-vis-lab",
                name_ru="Зззтест видимый анализ",
                category=ServiceCategory.laboratory,
            ),
            Service(
                service_key="t-vis-oth",
                name_ru="Зззтест скрытый прочее",
                category=ServiceCategory.other,
            ),
        ]
    )
    db_session.flush()

    results = search.autocomplete(db_session, "Зззтест", limit=10)
    names = {r.name_ru for r in results}

    assert "Зззтест видимый анализ" in names
    assert "Зззтест скрытый прочее" not in names


def test_should_autocomplete_known_alias():
    resp = client.get("/api/v1/services", params={"q": "CBC"})
    assert resp.status_code == 200
    names = [s["name_ru"] for s in resp.json()]
    assert any("ОАК" in n for n in names)


def test_should_reject_too_short_autocomplete():
    resp = client.get("/api/v1/services", params={"q": "о"})
    assert resp.status_code == 422


def test_should_search_oak_and_return_cards():
    resp = client.get("/api/v1/search", params={"q": "ОАК", "sort": "cheapest"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["resolved_service"] is not None
    assert body["count"] >= 2
    prices = [c["price_kzt"] for c in body["cards"]]
    assert prices == sorted(prices)
    card = body["cards"][0]
    assert card["source_url"]
    assert card["service_name_raw"]
    assert card["freshness"] in {"fresh", "recent", "stale"}


def test_should_hide_stale_by_default():
    default = client.get("/api/v1/search", params={"q": "УЗИ брюшной"}).json()
    with_stale = client.get(
        "/api/v1/search", params={"q": "УЗИ брюшной", "include_stale": "true"}
    ).json()
    assert with_stale["count"] >= default["count"]
    assert all(c["freshness"] != "stale" for c in default["cards"])


def test_should_return_empty_cards_for_unknown_query():
    resp = client.get("/api/v1/search", params={"q": "зззнесуществует"})
    assert resp.status_code == 200
    assert resp.json()["count"] == 0


def test_should_feature_distinct_fresh_services():
    resp = client.get("/api/v1/search/featured", params={"limit": 4})
    assert resp.status_code == 200
    cards = resp.json()
    assert 0 < len(cards) <= 4
    service_ids = [c["service_id"] for c in cards]
    assert len(service_ids) == len(set(service_ids))  # one card per service
    assert all(c["freshness"] != "stale" for c in cards)
# --- #1 category filter ---------------------------------------------------------


def test_should_filter_autocomplete_by_category(db_session):
    db_session.add_all(
        [
            Service(
                service_key="t-cat-lab",
                name_ru="Зззкат уникальный анализ",
                category=ServiceCategory.laboratory,
            ),
            Service(
                service_key="t-cat-diag",
                name_ru="Зззкат уникальное узи",
                category=ServiceCategory.diagnostic,
            ),
        ]
    )
    db_session.flush()

    lab = search.autocomplete(db_session, "Зззкат", category="лаборатория")
    names = {r.name_ru for r in lab}

    assert "Зззкат уникальный анализ" in names
    assert "Зззкат уникальное узи" not in names


def test_should_reject_invalid_search_category():
    resp = client.get("/api/v1/search", params={"q": "анализ", "category": "ззбогус"})
    assert resp.status_code == 422


def test_should_reject_hidden_search_category():
    resp = client.get("/api/v1/search", params={"q": "анализ", "category": "прочее"})
    assert resp.status_code == 422


# --- #2 confidence gate / did-you-mean -----------------------------------------


def test_should_resolve_exact_query(db_session):
    svc = Service(
        service_key="t-exact",
        name_ru="Зззэкзакт уникальное имя услуги",
        category=ServiceCategory.laboratory,
    )
    db_session.add(svc)
    db_session.flush()

    resolved, _ = search.resolve_query(db_session, "Зззэкзакт уникальное имя услуги")

    assert resolved is not None
    assert resolved.id == svc.id


def test_should_not_resolve_low_confidence_query(db_session):
    db_session.add(
        Service(
            service_key="t-gate",
            name_ru="Зззгейт уникальный лабораторный анализ",
            category=ServiceCategory.laboratory,
        )
    )
    db_session.flush()

    resolved, suggestions = search.resolve_query(db_session, "Зз")

    assert resolved is None  # never silently resolve a weak match
    assert any("Зззгейт" in s.name_ru for s in suggestions)


# --- #3 semantic fallback = suggestion-only ------------------------------------


def test_should_offer_semantic_match_as_suggestion(db_session):
    vec = [0.1] * 384
    svc = Service(
        service_key="t-sem",
        name_ru="Глюкоза зззсемантик",
        category=ServiceCategory.laboratory,
        embedding=vec,
    )
    db_session.add(svc)
    db_session.flush()

    resolved, suggestions = search.resolve_query(
        db_session, "Зззнетлексматча777", embedder=lambda _text: vec
    )

    assert resolved is None  # semantic must never silently resolve a price view
    assert suggestions
    assert suggestions[0].id == svc.id


def test_should_skip_semantic_when_no_embedder(db_session):
    resolved, _ = search.resolve_query(
        db_session, "Зззнетлексматча777", embedder=None
    )
    assert resolved is None


# --- #4 prefix-first ordering --------------------------------------------------


def test_should_rank_prefix_matches_first(db_session):
    db_session.add_all(
        [
            Service(
                service_key="t-pre",
                name_ru="Зззпреф уникальный тест",
                category=ServiceCategory.laboratory,
            ),
            Service(
                service_key="t-mid",
                name_ru="Уникальный тест зззпреф",
                category=ServiceCategory.laboratory,
            ),
        ]
    )
    db_session.flush()

    res = search.autocomplete(db_session, "Зззпреф")
    order = {r.name_ru: i for i, r in enumerate(res)}

    assert order["Зззпреф уникальный тест"] < order["Уникальный тест зззпреф"]


# --- #5 collapse duplicate names -----------------------------------------------


def test_should_collapse_duplicate_names_in_autocomplete(db_session):
    db_session.add_all(
        [
            Service(
                service_key="t-d1",
                name_ru="Зззддубль уникальный анализ",
                category=ServiceCategory.laboratory,
                specialty="Гематология",
            ),
            Service(
                service_key="t-d2",
                name_ru="Зззддубль уникальный анализ",
                category=ServiceCategory.laboratory,
                specialty="Биохимия",
            ),
        ]
    )
    db_session.flush()

    res = search.autocomplete(db_session, "Зззддубль")
    matching = [r for r in res if r.name_ru == "Зззддубль уникальный анализ"]

    assert len(matching) == 1
    assert matching[0].specialty in {"Гематология", "Биохимия"}


def test_should_resolve_to_most_priced_duplicate(db_session):
    s_few = Service(
        service_key="t-canon-few",
        name_ru="Зззканон уникальная услуга",
        category=ServiceCategory.laboratory,
    )
    s_many = Service(
        service_key="t-canon-many",
        name_ru="Зззканон уникальная услуга",
        category=ServiceCategory.laboratory,
    )
    db_session.add_all([s_few, s_many])
    db_session.flush()

    clinic = Clinic(name="Зззклиника тест", source_name="zzz-test")
    db_session.add(clinic)
    db_session.flush()
    db_session.add(
        ClinicServicePrice(
            clinic_id=clinic.id,
            service_id=s_many.id,
            city="Астана",
            price_kzt=1000,
            source_url="https://example.test/x",
            parsed_at=datetime.now(UTC),
            is_active=True,
        )
    )
    db_session.flush()

    resolved, _ = search.resolve_query(db_session, "Зззканон уникальная услуга")

    assert resolved is not None
    assert resolved.id == s_many.id  # canonicalize to the sibling that has prices


def test_should_carry_branch_rating_onto_search_card():
    from types import SimpleNamespace

    price = SimpleNamespace(
        id=1, price_kzt=1880, duration_min=None, duration_max=None,
        parsed_at=datetime.now(UTC), source_url="https://x.kz", service_name_raw=None,
        content_hash=None, match_confidence=1.0, match_method="exact", city="Астана",
        source_category=None,
    )
    clinic = SimpleNamespace(id=2, name="Клиника")
    branch = SimpleNamespace(
        id=3, city="Астана", address="ул. Тест", lat=51.1, lng=71.4,
        rating=4.7, reviews_count=120,
    )
    service = SimpleNamespace(id=4, name_ru="ОАК")

    card = search._build_card(price, clinic, branch, service, None, 1)

    assert card.rating == 4.7
    assert card.reviews_count == 120


def test_should_leave_card_rating_none_without_branch():
    from types import SimpleNamespace

    price = SimpleNamespace(
        id=1, price_kzt=1880, duration_min=None, duration_max=None,
        parsed_at=datetime.now(UTC), source_url="https://x.kz", service_name_raw=None,
        content_hash=None, match_confidence=1.0, match_method="exact", city="Астана",
        source_category=None,
    )
    clinic = SimpleNamespace(id=2, name="Клиника")
    service = SimpleNamespace(id=4, name_ru="ОАК")

    card = search._build_card(price, clinic, None, service, None, 1)

    assert card.rating is None
    assert card.reviews_count is None


def test_should_fall_back_to_priced_relative_when_exact_match_has_no_prices(db_session):
    # Plain query exact-matches a catalog row with no prices; the real prices live on a
    # longer relative whose name contains the query (e.g. ЭКГ → Холтер ЭКГ). Resolve to
    # the priced relative instead of dead-ending on the empty exact match.
    bare = Service(
        service_key="t-bare-zzzэкг",
        name_ru="Зззэкг",
        category=ServiceCategory.diagnostic,
    )
    priced = Service(
        service_key="t-priced-zzzэкг",
        name_ru="Суточное мониторирование Зззэкг (по Зззхолтеру)",
        category=ServiceCategory.diagnostic,
    )
    db_session.add_all([bare, priced])
    db_session.flush()

    clinic = Clinic(name="Зззклиника эхо", source_name="zzz-test")
    db_session.add(clinic)
    db_session.flush()
    db_session.add(
        ClinicServicePrice(
            clinic_id=clinic.id,
            service_id=priced.id,
            city="Астана",
            price_kzt=5000,
            source_url="https://example.test/holter",
            parsed_at=datetime.now(UTC),
            is_active=True,
        )
    )
    db_session.flush()

    resolved, _ = search.resolve_query(db_session, "Зззэкг")

    assert resolved is not None
    assert resolved.id == priced.id
    assert resolved.has_prices


def test_should_fall_back_to_priced_relative_outside_suggestion_window(db_session):
    # Many bare prefix entries crowd the priced relative out of the top-8 lexical window
    # (prefix matches rank first). The fallback must still find it by querying the
    # catalog, not just the suggestions it was handed — mirrors real "ЭКГ" with dozens of
    # bare ЭКГ-* rows pushing "Суточное мониторирование ЭКГ (по Холтеру)" out of view.
    bare = Service(
        service_key="t-bare-wide",
        name_ru="Зззшир",
        category=ServiceCategory.diagnostic,
    )
    db_session.add(bare)
    for i in range(10):
        db_session.add(
            Service(
                service_key=f"t-bare-wide-{i}",
                name_ru=f"Зззшир вариант {i}",
                category=ServiceCategory.diagnostic,
            )
        )
    priced = Service(
        service_key="t-priced-wide",
        name_ru="Суточное мониторирование Зззшир (по Зззхолтеру)",
        category=ServiceCategory.diagnostic,
    )
    db_session.add(priced)
    db_session.flush()

    clinic = Clinic(name="Зззклиника шир", source_name="zzz-test")
    db_session.add(clinic)
    db_session.flush()
    db_session.add(
        ClinicServicePrice(
            clinic_id=clinic.id,
            service_id=priced.id,
            city="Астана",
            price_kzt=5000,
            source_url="https://example.test/wide",
            parsed_at=datetime.now(UTC),
            is_active=True,
        )
    )
    db_session.flush()

    resolved, suggestions = search.resolve_query(db_session, "Зззшир")

    assert priced.id not in {s.id for s in suggestions}  # outside the lexical window
    assert resolved is not None
    assert resolved.id == priced.id  # ...yet still resolved via catalog-wide fallback
    assert resolved.has_prices


def _price_in(session, service_id, *, city, price=5000):
    clinic = Clinic(name=f"Зззгород {city}", source_name="zzz-city")
    session.add(clinic)
    session.flush()
    session.add(
        ClinicServicePrice(
            clinic_id=clinic.id,
            service_id=service_id,
            city=city,
            price_kzt=price,
            source_url=f"https://example.test/{city}",
            parsed_at=datetime.now(UTC),
            is_active=True,
            match_confidence=1.0,
        )
    )
    session.flush()


def test_should_make_autocomplete_has_prices_city_aware(db_session):
    svc = Service(
        service_key="t-zzzгород",
        name_ru="Зззгородуслуга уникальная",
        category=ServiceCategory.doctor_visit,
    )
    db_session.add(svc)
    db_session.flush()
    _price_in(db_session, svc.id, city="Караганда")

    in_astana = search.autocomplete(db_session, "Зззгородуслуга", city="Астана")
    in_karaganda = search.autocomplete(db_session, "Зззгородуслуга", city="Караганда")

    assert any(s.id == svc.id and not s.has_prices for s in in_astana)
    assert any(s.id == svc.id and s.has_prices for s in in_karaganda)


def test_should_list_other_cities_with_prices_excluding_selected(db_session):
    svc = Service(
        service_key="t-zzzмультигород",
        name_ru="Зззмультигород уникальная",
        category=ServiceCategory.doctor_visit,
    )
    db_session.add(svc)
    db_session.flush()
    _price_in(db_session, svc.id, city="Караганда")
    _price_in(db_session, svc.id, city="Темиртау")
    _price_in(db_session, svc.id, city="Темиртау")

    rows = search.cities_with_prices(db_session, svc.id, exclude_city="Астана")

    by_city = {city: count for city, count in rows}
    assert by_city == {"Темиртау": 2, "Караганда": 1}
    assert rows[0][0] == "Темиртау"


def test_should_return_other_cities_when_empty_in_selected_city(db_session):
    svc = Service(
        service_key="t-zzzпустойгород",
        name_ru="Зззпустойгород уникальная услуга",
        category=ServiceCategory.doctor_visit,
    )
    db_session.add(svc)
    db_session.flush()
    _price_in(db_session, svc.id, city="Караганда")

    app.dependency_overrides[get_db] = lambda: db_session
    try:
        resp = client.get(
            "/api/v1/search",
            params={"q": "Зззпустойгород уникальная услуга", "city": "Астана"},
        )
    finally:
        app.dependency_overrides.pop(get_db, None)

    assert resp.status_code == 200
    body = resp.json()
    assert body["count"] == 0
    assert body["resolved_service"] is not None
    assert body["resolved_service"]["id"] == svc.id
    cities = {c["name"]: c["count"] for c in body["other_cities"]}
    assert cities.get("Караганда") == 1
