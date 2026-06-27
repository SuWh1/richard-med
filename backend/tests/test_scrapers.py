from app.scrapers.doq import DoqAdapter
from app.scrapers.kdl_olymp import KdlOlympAdapter
from app.scrapers.registry import available_sources, get_adapter


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


def test_should_resolve_known_adapters_from_registry():
    assert set(available_sources()) == {"kdl_olymp", "doq"}
    assert get_adapter("kdl_olymp").identity() == "kdl_olymp"
    assert get_adapter("doq").identity() == "doq"
