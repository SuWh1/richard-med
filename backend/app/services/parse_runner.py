"""Shared parse-run orchestration used by both the admin trigger and the nightly cron.

One run = for each city/source: fetch + parse + publish, then drain the unmatched queue
into the catalog and re-parse, then refresh 2GIS ratings. Synchronous and sequential by
design (slow-moving prices, off-peak, polite per-source delays). A process-wide lock makes
overlapping triggers a no-op so the admin button and the cron can never double-run.
"""

import logging
import threading

from sqlalchemy.orm import Session

from app.core.cities import CITY_NAMES
from app.db.session import SessionLocal
from app.scrapers.registry import available_sources
from app.services.catalog_grow import grow_catalog
from app.services.embeddings import get_embedder
from app.services.llm_verify import get_verifier
from app.services.pipeline import run_source
from app.services.twogis_sync import refresh_reviews

logger = logging.getLogger(__name__)

_GROW_BATCH = 25
_run_lock = threading.Lock()


def is_running() -> bool:
    return _run_lock.locked()


def _grow_and_reparse(
    session: Session, source_names: list[str], cities: list[str], embedder
) -> None:
    """After a run, drain the unmatched queue into the catalog and re-parse so the
    newly-added services match instead of lingering as pending suggestions."""
    try:
        grow_catalog(session)  # "nothing similar" rows — no AI, one transaction
        session.commit()
        verifier = get_verifier()
        if verifier is not None:
            while True:
                batch = grow_catalog(session, verifier=verifier, limit=_GROW_BATCH)
                session.commit()
                if batch["aliased"] + batch["added"] + batch["deferred"] == 0:
                    break
        for city in cities:
            for source in source_names:
                run_source(session, source, city, publish=True, embedder=embedder)
                session.commit()
    except Exception:  # noqa: BLE001 — growth is best-effort; the run already published
        logger.exception("catalog grow / re-parse failed for %s/%s", source_names, cities)
        session.rollback()


def _refresh_twogis_reviews(session: Session) -> None:
    """Keep 2GIS ratings/reviews current alongside the price parse. Step B only —
    plain HTTP off each branch's stored firm_id, no browser. Firm-id discovery
    (Step A) is a separate offline job (app.scripts.discover_2gis_firms)."""
    try:
        refresh_reviews(session)
    except Exception:  # noqa: BLE001 — ratings are best-effort; prices already published
        logger.exception("2GIS reviews refresh failed")
        session.rollback()


def run_sources(source_names: list[str], cities: list[str]) -> bool:
    """Run a parse for the given sources × cities. Returns False (a no-op) if another
    run is already in progress."""
    if not _run_lock.acquire(blocking=False):
        logger.warning("parse run skipped — another run is already in progress")
        return False
    try:
        session = SessionLocal()
        embedder = get_embedder()
        try:
            for city in cities:
                for source in source_names:
                    try:
                        run_source(session, source, city, publish=True, embedder=embedder)
                        session.commit()
                    except Exception:  # noqa: BLE001 — isolate one source/city from the rest
                        logger.exception("background run failed for %s/%s", source, city)
                        session.rollback()
            _grow_and_reparse(session, source_names, cities, embedder)
            _refresh_twogis_reviews(session)
        finally:
            session.close()
        return True
    finally:
        _run_lock.release()


def run_all_cities() -> bool:
    """Every registered source across every supported city — the nightly cron target."""
    return run_sources(available_sources(), list(CITY_NAMES))
