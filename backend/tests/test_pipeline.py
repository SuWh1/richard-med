from pathlib import Path

from app.models import ClinicServicePrice, ParseRun, RawDocument
from app.scrapers.base import RawDocument as RawDoc
from app.scrapers.doq import DoqAdapter, _query_url
from app.scrapers.http import content_hash
from app.scrapers.kdl_olymp import KdlOlympAdapter
from app.services.pipeline import _parse_duration, run_source

_FIXTURE = Path(__file__).parent / "fixtures" / "doq_doctors_terapevt_astana.json"
_KDL_FIXTURE = Path(__file__).parent / "fixtures" / "kdl_analysis_data_astana.json"


def test_should_parse_single_value_duration():
    assert _parse_duration("1") == (1, 1)


def test_should_parse_range_duration():
    assert _parse_duration("2-3") == (2, 3)


def test_should_handle_missing_or_unparseable_duration():
    assert _parse_duration(None) == (None, None)
    assert _parse_duration("срочно") == (None, None)


class _StubKdlAdapter(KdlOlympAdapter):
    """Real KDL JSON parse/clean, fetch serves the saved fixture."""

    def fetch(self, city: str) -> list[RawDoc]:
        text = _KDL_FIXTURE.read_text(encoding="utf-8")
        return [
            RawDoc(
                source_name=self.identity(),
                source_url=self._url("astana"),
                city=city,
                raw_html=text,
                content_hash=content_hash(text),
                status_code=200,
                fetched_at="",
            )
        ]


def test_should_persist_kdl_durations_from_json(db_session):
    result = run_source(db_session, "kdl_olymp", "Астана", adapter=_StubKdlAdapter())
    assert result.status == "success"
    assert result.items_saved >= 1
    priced = (
        db_session.query(ClinicServicePrice)
        .filter(ClinicServicePrice.duration_min.is_not(None))
        .all()
    )
    assert priced  # durations were extracted and stored


class _StubDoqAdapter(DoqAdapter):
    """Real DOQ parse/clean, but fetch serves the saved fixture instead of the network."""

    def fetch(self, city: str) -> list[RawDoc]:
        text = _FIXTURE.read_text(encoding="utf-8")
        return [
            RawDoc(
                source_name=self.identity(),
                source_url=_query_url(1, 97),
                city=city,
                raw_html=text,
                content_hash=content_hash(text),
                status_code=200,
                fetched_at="",
            )
        ]


def test_should_run_doq_pipeline_and_persist_prices(db_session):
    result = run_source(db_session, "doq", "Астана", adapter=_StubDoqAdapter())

    assert result.status == "success"
    assert result.items_found >= 1
    assert result.items_saved >= 1

    run = db_session.get(ParseRun, result.run_id)
    assert run.status == "success"
    assert run.finished_at is not None

    prices = (
        db_session.query(ClinicServicePrice)
        .filter(ClinicServicePrice.id.in_(_run_price_ids(db_session)))
        .all()
    )
    assert any(p.match_confidence > 0 for p in prices)


def test_should_save_raw_document_evidence(db_session):
    run_source(db_session, "doq", "Астана", adapter=_StubDoqAdapter())
    docs = db_session.query(RawDocument).filter(RawDocument.source_name == "doq").all()
    assert docs
    assert all(d.content_hash and d.raw_html for d in docs)


def test_should_be_idempotent_on_rerun(db_session):
    first = run_source(db_session, "doq", "Астана", adapter=_StubDoqAdapter())
    second = run_source(db_session, "doq", "Астана", adapter=_StubDoqAdapter())
    active = (
        db_session.query(ClinicServicePrice)
        .filter(ClinicServicePrice.is_active.is_(True))
        .count()
    )
    # A second identical run refreshes rather than duplicates active prices.
    assert second.items_saved == first.items_saved
    assert active >= first.items_saved


def test_should_isolate_a_failing_source(db_session):
    class _BrokenAdapter(DoqAdapter):
        def fetch(self, city: str):
            raise RuntimeError("source down")

    result = run_source(db_session, "doq", "Астана", adapter=_BrokenAdapter())
    assert result.status == "failed"
    assert "source down" in (result.errors or "")
    run = db_session.get(ParseRun, result.run_id)
    assert run.status == "failed"


def _run_price_ids(session):
    return [r.id for r in session.query(ClinicServicePrice).all()]
