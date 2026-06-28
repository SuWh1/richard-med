from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.main import app
from app.models import Clinic, ClinicServicePrice, Service, ServiceCategory
from app.services import search

client = TestClient(app)


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
