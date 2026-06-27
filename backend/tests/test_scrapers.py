from app.scrapers.doq import DoqAdapter
from app.scrapers.kdl_olymp import KdlOlympAdapter
from app.scrapers.registry import available_sources, get_adapter


def test_should_parse_kdl_snapshot_rows():
    result = KdlOlympAdapter().test_snapshot()
    assert result.item_count == 15
    first = result.sample_items[0]
    assert "анализ крови" in first.service_name_raw.lower()
    assert first.price_raw == "3980"
    assert first.clinic_raw == "KDL Olymp"
    assert first.source_url.startswith("https://kdlolymp.kz/services/")


def test_should_strip_kdl_price_to_digits():
    adapter = KdlOlympAdapter()
    result = adapter.test_snapshot()
    assert all(item.price_raw.isdigit() for item in result.sample_items)


def test_should_extract_doq_visit_prices_for_target_specialization():
    result = DoqAdapter().test_snapshot()
    assert result.item_count >= 1
    item = result.sample_items[0]
    assert item.price_raw.isdigit() and int(item.price_raw) > 0
    assert item.clinic_raw
    assert item.metadata["specialization"] == "Терапевт"
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
