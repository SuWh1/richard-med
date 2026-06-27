from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_should_return_price_stats_with_valid_ranges():
    resp = client.get("/api/v1/analytics/price-stats")
    assert resp.status_code == 200
    stats = resp.json()
    assert stats
    for s in stats:
        assert s["clinic_count"] >= 1
        assert s["price_count"] >= 1
        assert s["min_kzt"] <= s["avg_kzt"] <= s["max_kzt"]
        assert s["min_kzt"] <= s["median_kzt"] <= s["max_kzt"]
        assert s["category"] in {"лаборатория", "приём врача", "диагностика", "процедура"}


def test_should_aggregate_oak_across_multiple_clinics():
    resp = client.get("/api/v1/analytics/price-stats")
    assert resp.status_code == 200
    oak = next((s for s in resp.json() if "ОАК" in s["service_name"]), None)
    assert oak is not None
    assert oak["clinic_count"] >= 2
    assert oak["min_kzt"] < oak["max_kzt"]


def test_should_filter_price_stats_by_category():
    resp = client.get("/api/v1/analytics/price-stats", params={"category": "лаборатория"})
    assert resp.status_code == 200
    stats = resp.json()
    assert stats
    assert all(s["category"] == "лаборатория" for s in stats)


def test_should_filter_price_stats_by_city():
    resp = client.get("/api/v1/analytics/price-stats", params={"city": "Астана"})
    assert resp.status_code == 200
    stats = resp.json()
    assert stats
    assert all(s["city"] == "Астана" for s in stats)


def test_should_reject_invalid_category():
    resp = client.get("/api/v1/analytics/price-stats", params={"category": "не-категория"})
    assert resp.status_code == 422


def test_should_return_overview_with_categories_and_cities():
    resp = client.get("/api/v1/analytics/overview")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_prices"] >= 1
    assert body["total_services"] >= 1
    assert body["categories"]
    for c in body["categories"]:
        assert c["min_kzt"] <= c["median_kzt"] <= c["max_kzt"]
        assert c["service_count"] >= 1
    cities = [c["city"] for c in body["cities"]]
    assert "Астана" in cities


def test_should_exclude_stale_from_overview_by_default():
    default = client.get("/api/v1/analytics/overview").json()
    with_stale = client.get(
        "/api/v1/analytics/overview", params={"include_stale": "true"}
    ).json()
    assert with_stale["total_prices"] >= default["total_prices"]
