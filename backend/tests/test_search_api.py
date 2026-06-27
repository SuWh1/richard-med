from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


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
