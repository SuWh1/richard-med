from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_should_list_public_sources_with_live_counts():
    resp = client.get("/api/v1/sources")

    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1

    names = {s["name"] for s in data}
    assert "kdl_olymp" in names

    for s in data:
        assert s["prices"] >= 1
        assert s["cities"] >= 1
        assert s["display_name"]
        assert s["kind"]
        assert "freshness" in s
        assert "website" in s


def test_should_sort_sources_by_price_count_desc():
    data = client.get("/api/v1/sources").json()
    prices = [s["prices"] for s in data]
    assert prices == sorted(prices, reverse=True)
