from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_should_report_health_for_known_sources():
    resp = client.get("/api/v1/admin/source-health")
    assert resp.status_code == 200
    sources = {row["source_name"] for row in resp.json()}
    assert {"kdl_olymp", "doq"} <= sources
    row = resp.json()[0]
    assert "success_rate_7d" in row
    assert "active_prices" in row


def test_should_list_catalog_services_with_counts():
    resp = client.get("/api/v1/admin/services", params={"limit": 5})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 1
    assert len(body["items"]) <= 5
    row = body["items"][0]
    assert {"id", "name_ru", "category", "origin", "alias_count", "price_count"} <= row.keys()
    assert row["origin"] in ("catalog", "auto")


def test_should_filter_catalog_services_by_query():
    resp = client.get("/api/v1/admin/services", params={"q": "анализ", "limit": 10})
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert all("анализ" in r["name_ru"].lower() for r in items)


def test_should_list_unmatched_review_queue():
    resp = client.get("/api/v1/admin/unmatched", params={"status": "pending", "limit": 5})
    assert resp.status_code == 200
    body = resp.json()
    assert "total" in body and isinstance(body["items"], list)
    if body["items"]:
        row = body["items"][0]
        assert {"id", "raw_name", "suggested_name", "confidence", "status"} <= row.keys()
        assert row["status"] == "pending"


def test_should_list_recent_parse_runs():
    resp = client.get("/api/v1/admin/parse-runs", params={"limit": 5})
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_should_404_for_unknown_run():
    resp = client.get("/api/v1/admin/parse-runs/99999999")
    assert resp.status_code == 404


def test_should_reject_unknown_source_on_trigger():
    resp = client.post("/api/v1/admin/parsers/run", params={"source": "nope"})
    assert resp.status_code == 404


def test_should_accept_run_trigger_for_known_source(monkeypatch):
    # Stub the background worker so the test never performs a live fetch.
    calls = []
    monkeypatch.setattr(
        "app.api.v1.endpoints.admin._run_sources",
        lambda sources, city: calls.append((sources, city)),
    )
    resp = client.post(
        "/api/v1/admin/parsers/run", params={"source": "kdl_olymp", "city": "Астана"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["accepted"] is True
    assert body["source_names"] == ["kdl_olymp"]
    assert calls == [(["kdl_olymp"], ["Астана"])]


def test_should_expand_all_cities_sentinel_on_trigger(monkeypatch):
    from app.core.cities import CITY_NAMES

    calls = []
    monkeypatch.setattr(
        "app.api.v1.endpoints.admin._run_sources",
        lambda sources, cities: calls.append((sources, cities)),
    )
    resp = client.post(
        "/api/v1/admin/parsers/run", params={"source": "kdl_olymp", "city": "__all__"}
    )
    assert resp.status_code == 200
    assert calls == [(["kdl_olymp"], list(CITY_NAMES))]


def test_should_grow_catalog_and_reparse_after_running_sources(monkeypatch):
    from app.api.v1.endpoints import admin as admin_ep

    calls = []
    monkeypatch.setattr(
        admin_ep,
        "run_source",
        lambda session, source, city, **kw: calls.append(("run", source)),
    )
    monkeypatch.setattr(
        admin_ep,
        "grow_catalog",
        lambda session, **kw: calls.append(("grow", kw.get("verifier") is not None))
        or {"added": 0, "aliased": 0, "skipped": 0, "deferred": 0},
    )
    monkeypatch.setattr(admin_ep, "get_verifier", lambda: None)
    monkeypatch.setattr(admin_ep, "get_embedder", lambda: None)

    admin_ep._run_sources(["kdl_olymp"], ["Астана"])

    # Source runs, then catalog is grown, then the source is re-parsed so new entries match.
    assert calls == [
        ("run", "kdl_olymp"),
        ("grow", False),
        ("run", "kdl_olymp"),
    ]
