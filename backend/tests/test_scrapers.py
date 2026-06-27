from urllib.parse import parse_qs, urlparse

import httpx

from app.scrapers.doq import SPECIALIZATIONS, DoqAdapter
from app.scrapers.helix import HelixAdapter
from app.scrapers.invitro import InvitroAdapter
from app.scrapers.kdl_olymp import KdlOlympAdapter
from app.scrapers.registry import available_sources, get_adapter


class _FakeResponse:
    text = '{"results": [], "next": null}'
    status_code = 200

    def json(self) -> dict:
        return {"results": [], "next": None}


class _FlakyClient:
    """Raises for chosen specialization ids; serves an empty page otherwise."""

    def __init__(self, fail_service_ids: set[int]):
        self._fail = fail_service_ids

    def get(self, url: str) -> _FakeResponse:
        service_id = int(parse_qs(urlparse(url).query)["service"][0])
        if service_id in self._fail:
            raise httpx.ConnectError("boom")
        return _FakeResponse()

    def close(self) -> None:
        pass


def test_should_isolate_doq_fetch_failures_per_specialization():
    # The first specialization's request fails; the other eight must still be fetched.
    failing = next(iter(SPECIALIZATIONS))
    adapter = DoqAdapter(client=_FlakyClient(fail_service_ids={failing}))

    docs = adapter.fetch("Астана")

    assert len(docs) == len(SPECIALIZATIONS) - 1
    assert all(f"service={failing}&" not in d.source_url for d in docs)


def test_should_parse_kdl_json_rows():
    result = KdlOlympAdapter().test_snapshot()
    # 5 analyses in the fixture, one with a null price → skipped.
    assert result.item_count == 4
    first = result.sample_items[0]
    assert "анализ крови" in first.service_name_raw.lower()
    assert first.price_raw == "3980"
    assert first.clinic_raw == "KDL Olymp"
    assert first.source_url == "https://kdlolymp.kz/analysis/klinicheskiy-analiz-krovi-oak"
    assert first.duration_raw == "1"


def test_should_skip_kdl_analyses_without_a_price():
    items = KdlOlympAdapter().test_snapshot().sample_items
    assert all("без цены" not in item.service_name_raw.lower() for item in items)


def test_should_skip_kdl_dinamika_retest_variants():
    # "(динамика)" are cheap monitoring re-tests that falsely fuzzy-match the base service.
    result = KdlOlympAdapter().test_snapshot()
    assert result.item_count == 4
    assert all("динамика" not in item.service_name_raw.lower() for item in result.sample_items)


def test_should_strip_kdl_price_to_digits():
    items = KdlOlympAdapter().test_snapshot().sample_items
    assert all(item.price_raw.isdigit() for item in items)


def test_should_extract_doq_visit_prices_for_target_specialization():
    result = DoqAdapter().test_snapshot()
    assert result.item_count >= 1
    item = result.sample_items[0]
    assert item.price_raw.isdigit() and int(item.price_raw) > 0
    assert item.clinic_raw
    # Emits our canonical label (alias-matchable to "Прием терапевта"), keeps DOQ's
    # own service name as evidence.
    assert item.service_name_raw == "Терапевт"
    assert item.metadata["specialization"] == "Терапевт"
    assert item.metadata["doq_service_name"]
    assert item.metadata["lat"] and item.metadata["lng"]


def test_should_filter_doq_services_to_queried_specialization():
    # The terapevt query returns doctors whose services include procedures; only the
    # terapevt visit (service id 97) should survive the parse.
    items = DoqAdapter().test_snapshot().sample_items
    assert all(i.metadata["specialization"] == "Терапевт" for i in items)


def test_should_parse_kdl_branches_from_cabinet_json():
    from pathlib import Path

    fixture = Path(__file__).parent / "fixtures" / "kdl_cabinets_astana.json"
    hits = KdlOlympAdapter().parse_branches(fixture.read_text(encoding="utf-8"), "Астана")

    assert len(hits) == 2  # the null-coords cabinet is skipped
    first = hits[0]
    assert first.city == "Астана"
    assert first.lat == 51.128207 and first.lng == 71.430411
    assert first.address == "ул. Тестовая, 1"
    assert first.external_id == "procedurnyy-kabinet-test-1"
    assert "08:00" in (first.working_hours or "")


def test_should_have_no_branches_for_doq_by_default():
    assert DoqAdapter().fetch_branches("Астана") == []


def test_should_resolve_known_adapters_from_registry():
    assert set(available_sources()) == {"kdl_olymp", "doq", "invitro", "helix"}
    assert get_adapter("kdl_olymp").identity() == "kdl_olymp"
    assert get_adapter("doq").identity() == "doq"
    assert get_adapter("invitro").identity() == "invitro"
    assert get_adapter("helix").identity() == "helix"


def test_should_parse_helix_cards_with_name_and_price():
    result = HelixAdapter().test_snapshot()
    # 4 priced cards in the fixture; the price-less decoy is skipped.
    assert result.item_count == 4
    cbc = next(i for i in result.sample_items if "клинический анализ крови" in i.service_name_raw.lower())
    assert cbc.price_raw == "1900"
    assert cbc.clinic_raw == "Хеликс"
    assert cbc.metadata["code"] == "02-005"


def test_should_build_browsable_almaty_helix_source_urls():
    items = HelixAdapter().test_snapshot().sample_items
    # Links must carry the /almaty prefix so the clicked page shows Almaty (₸) prices.
    assert all(i.source_url.startswith("https://helix.ru/almaty/catalog/item/") for i in items)


def test_should_strip_helix_price_to_digits():
    items = HelixAdapter().test_snapshot().sample_items
    assert all(i.price_raw.isdigit() and int(i.price_raw) > 0 for i in items)


def test_should_have_no_helix_data_for_unsupported_city():
    assert HelixAdapter().fetch("Астана") == []


def test_should_parse_invitro_product_anchors():
    result = InvitroAdapter().test_snapshot()
    # 8 priced anchors in the fixture; the zero-price and the price-less decoys are skipped.
    assert result.item_count == 8
    cbc = next(i for i in result.sample_items if "общий анализ крови" in i.service_name_raw.lower())
    assert cbc.price_raw == "520"
    assert cbc.clinic_raw == "Invitro"


def test_should_build_browsable_invitro_source_urls():
    items = InvitroAdapter().test_snapshot().sample_items
    assert all(i.source_url.startswith("https://invitro.kz/analizes/for-doctors/") for i in items)


def test_should_strip_invitro_english_gloss_and_price_to_digits():
    items = InvitroAdapter().test_snapshot().sample_items
    assert all(i.price_raw.isdigit() for i in items)
    # The trailing English gloss "(Complete Blood Count, CBC)" is dropped; the legitimate
    # Russian qualifier "(без лейкоцитарной формулы и СОЭ)" is kept.
    cbc = next(i for i in items if "общий анализ крови" in i.service_name_raw.lower())
    assert "CBC" not in cbc.service_name_raw and "Complete Blood Count" not in cbc.service_name_raw
    assert cbc.service_name_raw.endswith("СОЭ)")


def test_should_have_no_invitro_data_for_unsupported_city():
    assert InvitroAdapter().fetch("Караганда") == []
