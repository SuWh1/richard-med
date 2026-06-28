import json
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import httpx

from app.scrapers.base import RawDocument
from app.scrapers.doq import DoqAdapter, _sweep_url
from app.scrapers.http import content_hash
from app.scrapers.helix import HelixAdapter
from app.scrapers.invitro import InvitroAdapter
from app.scrapers.kdl_olymp import KdlOlympAdapter
from app.scrapers.registry import available_sources, get_adapter


def _doq_fixture_doc() -> RawDocument:
    text = (Path(__file__).parent / "fixtures" / "doq_doctors_astana.json").read_text(
        encoding="utf-8"
    )
    return RawDocument(
        source_name="doq",
        source_url=_sweep_url(1),
        city="Астана",
        raw_html=text,
        content_hash=content_hash(text),
        status_code=200,
        fetched_at="",
    )


class _FakeResponse:
    text = '{"results": [], "next": null}'
    status_code = 200

    def json(self) -> dict:
        return {"results": [], "next": None}


class _PagedResponse:
    """One results page; reports a `next` so the sweep keeps paging up to `last`."""

    def __init__(self, offset: int, last: int):
        self.status_code = 200
        self._offset = offset
        self._last = last

    @property
    def text(self) -> str:
        return json.dumps(self._payload())

    def json(self) -> dict:
        return self._payload()

    def _payload(self) -> dict:
        nxt = None if self._offset >= self._last else "next"
        return {"results": [{"id": self._offset}], "next": nxt}


class _FlakyClient:
    """Serves paged sweep responses but raises for chosen offsets."""

    def __init__(self, fail_offsets: set[int], last: int):
        self._fail = fail_offsets
        self._last = last

    def get(self, url: str) -> _PagedResponse:
        offset = int(parse_qs(urlparse(url).query).get("offset", ["0"])[0])
        if offset in self._fail:
            raise httpx.ConnectError("boom")
        return _PagedResponse(offset, self._last)

    def close(self) -> None:
        pass


def test_should_isolate_doq_fetch_failures_per_page():
    # The first sweep page fails; offsets are deterministic, so later pages still load.
    adapter = DoqAdapter(client=_FlakyClient(fail_offsets={0}, last=200))

    docs = adapter.fetch("Астана")

    assert len(docs) == 2  # offsets 100 and 200 survive; offset 0 was skipped
    assert all("offset=0&" not in d.source_url for d in docs)


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


def test_should_extract_doq_prices_with_real_service_name():
    result = DoqAdapter().test_snapshot()
    assert result.item_count >= 1
    item = result.sample_items[0]
    assert item.price_raw.isdigit() and int(item.price_raw) > 0
    assert item.clinic_raw
    # The raw service name is DOQ's own (matched/grown against the catalog downstream),
    # not a hand-curated specialization label.
    assert item.service_name_raw == item.metadata["doq_service_name"]
    assert item.metadata["lat"] and item.metadata["lng"]


def test_should_parse_doq_diagnostic_procedures_not_just_visits():
    # The old adapter crawled 9 doctor specializations, so diagnostics like Флюорография
    # were missed entirely. A full doctor sweep now surfaces them.
    items = DoqAdapter().parse(_doq_fixture_doc())
    flu = [i for i in items if i.service_name_raw == "Флюорография"]
    assert flu, "fluorography must now be parsed from DOQ"
    assert flu[0].metadata["category"] == "процедура"
    assert flu[0].metadata["doq_type"] == "procedure"


def test_should_skip_doq_offers_without_a_price():
    # The fixture includes an appointment offer with a null price; it must be dropped.
    items = DoqAdapter().parse(_doq_fixture_doc())
    assert all(i.price_raw for i in items)
    assert all(i.metadata["doq_service_name"] != "Рентгенолог" for i in items)


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
