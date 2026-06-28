from sqlalchemy import func, select

from app.models import ClinicServicePrice, Service, ServiceAlias
from app.services import live_search, search

_NOVEL = "Живой-тест услуга ЪЪЪ"  # unlikely to exist in the seeded catalog


def _provider_payload(service_id: int) -> dict:
    def doctor(slug, clinic, price, lat):
        return {
            "slug": slug,
            "name": f"Доктор {slug}",
            "clinic_branches": [
                {
                    "id": 1,
                    "name": clinic,
                    "address": f"ул. {clinic}",
                    "location": {"lat": lat, "lng": 71.4},
                    "phones": ["+7 700 000 00 00"],
                }
            ],
            "services": [
                {
                    "is_active": True,
                    "clinic_branch": 1,
                    "base_price": price + 100,
                    "discount_price": price,
                    "service": {"id": service_id, "name": _NOVEL, "type": "procedure"},
                }
            ],
        }

    return {"results": [doctor("a", "Клиника А", 1900, 51.1), doctor("b", "Клиника Б", 2500, 51.2)]}


def _patch_network(monkeypatch, service_id: int = 987654, payload: dict | None = None):
    monkeypatch.setattr(
        live_search,
        "_resolve_doq_service",
        lambda client, city_id, query: {"id": service_id, "name": _NOVEL, "type": "procedure"},
    )
    monkeypatch.setattr(
        live_search,
        "_fetch_providers",
        lambda client, city_id, sid: payload if payload is not None else _provider_payload(sid),
    )
    monkeypatch.setattr(live_search.httpx, "Client", lambda **_: _DummyClient())


class _DummyClient:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _active_prices_for(session, service_id):
    return session.scalars(
        select(ClinicServicePrice).where(
            ClinicServicePrice.service_id == service_id,
            ClinicServicePrice.is_active.is_(True),
        )
    ).all()


def test_should_persist_a_new_service_and_prices_on_a_live_miss(db_session, monkeypatch):
    _patch_network(monkeypatch)

    service_id = live_search.live_fetch_doq(db_session, "живой тест ъъъ", "Астана")

    assert service_id is not None
    service = db_session.get(Service, service_id)
    assert service.name_ru == _NOVEL
    assert service.category.value == "процедура"

    prices = _active_prices_for(db_session, service_id)
    assert len(prices) == 2  # one per clinic
    assert {p.price_kzt for p in prices} == {1900, 2500}
    assert all(p.match_method == "live" for p in prices)


def test_should_record_the_query_as_an_alias_so_it_resolves_next_time(db_session, monkeypatch):
    _patch_network(monkeypatch)

    service_id = live_search.live_fetch_doq(db_session, "слэнговый запрос ъъъ", "Астана")

    alias = db_session.scalars(
        select(ServiceAlias).where(ServiceAlias.service_id == service_id)
    ).first()
    assert alias is not None and alias.source == "live"
    # The newly-grown service is now resolvable from the DB (no network).
    resolved, _ = search.resolve_query(db_session, _NOVEL, embedder=None)
    assert resolved is not None and resolved.id == service_id


def test_should_keep_the_cheapest_offer_per_clinic(db_session, monkeypatch):
    payload = _provider_payload(987654)
    # add a second, pricier branch row for "Клиника А" — the 1900 one must win.
    payload["results"][0]["services"].append(
        {
            "is_active": True,
            "clinic_branch": 1,
            "base_price": 9999,
            "discount_price": 9999,
            "service": {"id": 987654, "name": _NOVEL, "type": "procedure"},
        }
    )
    _patch_network(monkeypatch, payload=payload)

    service_id = live_search.live_fetch_doq(db_session, "живой тест ъъъ", "Астана")
    prices = _active_prices_for(db_session, service_id)
    assert {p.price_kzt for p in prices} == {1900, 2500}


def test_should_return_none_when_no_providers_offer_the_service(db_session, monkeypatch):
    _patch_network(monkeypatch, payload={"results": []})

    assert live_search.live_fetch_doq(db_session, "ничего ъъъ", "Астана") is None
    assert not db_session.scalars(select(Service).where(Service.name_ru == _NOVEL)).all()


def test_should_skip_live_lookup_for_a_city_outside_doq_coverage(db_session, monkeypatch):
    called = {"n": 0}
    monkeypatch.setattr(
        live_search, "_resolve_doq_service", lambda *a: called.__setitem__("n", 1)
    )
    assert live_search.live_fetch_doq(db_session, "что угодно", "Туркестан") is None
    assert called["n"] == 0


def test_should_not_run_live_lookup_when_disabled(db_session, monkeypatch):
    monkeypatch.setattr(live_search.settings, "LIVE_FALLBACK_ENABLED", False)
    called = {"n": 0}
    monkeypatch.setattr(
        live_search, "_resolve_doq_service", lambda *a: called.__setitem__("n", 1)
    )
    assert live_search.live_fetch_doq(db_session, "что угодно", "Астана") is None
    assert called["n"] == 0
