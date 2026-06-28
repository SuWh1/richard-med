from app.core.cities import CITY_NAMES
from app.scrapers.registry import available_sources
from app.services import parse_runner, scheduler


def test_should_skip_when_a_run_is_already_in_progress():
    parse_runner._run_lock.acquire()
    try:
        assert parse_runner.run_sources(["kdl_olymp"], ["Астана"]) is False
        assert parse_runner.is_running() is True
    finally:
        parse_runner._run_lock.release()


def test_should_target_every_source_and_city_for_the_nightly_run(monkeypatch):
    captured = {}

    def fake_run_sources(sources, cities):
        captured["sources"] = sources
        captured["cities"] = cities
        return True

    monkeypatch.setattr(parse_runner, "run_sources", fake_run_sources)
    assert parse_runner.run_all_cities() is True
    assert captured["sources"] == available_sources()
    assert set(captured["cities"]) == set(CITY_NAMES)


def test_should_not_start_scheduler_when_cron_is_disabled(monkeypatch):
    monkeypatch.setattr(scheduler.settings, "PARSER_CRON_ENABLED", False)
    assert scheduler.create_scheduler() is None


def test_should_schedule_a_daily_all_cities_job_when_enabled(monkeypatch):
    monkeypatch.setattr(scheduler.settings, "PARSER_CRON_ENABLED", True)
    sch = scheduler.create_scheduler()
    try:
        assert sch is not None
        assert sch.get_job("parse_all_cities") is not None
    finally:
        if sch is not None:
            sch.shutdown(wait=False)
