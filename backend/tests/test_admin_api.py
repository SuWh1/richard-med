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
    assert calls == [(["kdl_olymp"], "Астана")]
