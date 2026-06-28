import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.cities import CITY_NAMES
from app.db.session import SessionLocal, get_db
from app.schemas.admin import (
    CatalogPage,
    ParseRunDetail,
    ParseRunSummary,
    RunTrigger,
    SourceHealth,
    UnmatchedPage,
)
from app.scrapers.registry import available_sources
from app.services import admin
from app.services.catalog_grow import grow_catalog
from app.services.embeddings import get_embedder
from app.services.llm_verify import get_verifier
from app.services.pipeline import run_source
from app.services.twogis_sync import refresh_reviews

logger = logging.getLogger(__name__)
router = APIRouter()

_GROW_BATCH = 25
ALL_CITIES = "__all__"  # sentinel: run every supported city


def _grow_and_reparse(
    session, source_names: list[str], cities: list[str], embedder
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


def _run_sources(source_names: list[str], cities: list[str]) -> None:
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


def _refresh_twogis_reviews(session) -> None:
    """Keep 2GIS ratings/reviews current alongside the price parse. Step B only —
    plain HTTP off each branch's stored firm_id, no browser. Firm-id discovery
    (Step A) is a separate offline job (app.scripts.discover_2gis_firms)."""
    try:
        refresh_reviews(session)
    except Exception:  # noqa: BLE001 — ratings are best-effort; prices already published
        logger.exception("2GIS reviews refresh failed")
        session.rollback()


@router.post("/parsers/run", response_model=RunTrigger)
def trigger_run(
    background_tasks: BackgroundTasks,
    source: str | None = Query(None, description="Source name; omit to run all sources"),
    city: str = Query("Астана", description=f"City name, or '{ALL_CITIES}' for every city"),
) -> RunTrigger:
    sources = available_sources() if source is None else [source]
    unknown = [s for s in sources if s not in available_sources()]
    if unknown:
        raise HTTPException(status_code=404, detail=f"Unknown source(s): {unknown}")

    cities = list(CITY_NAMES) if city == ALL_CITIES else [city]
    background_tasks.add_task(_run_sources, sources, cities)
    where = "всех городов" if city == ALL_CITIES else f"города {city}"
    return RunTrigger(
        accepted=True,
        source_names=sources,
        city=city,
        message=f"Запущен парсинг ({', '.join(sources)}) для {where}.",
    )


@router.get("/source-health", response_model=list[SourceHealth])
def get_source_health(db: Session = Depends(get_db)) -> list[SourceHealth]:
    return admin.source_health(db)


@router.get("/services", response_model=CatalogPage)
def get_catalog_services(
    q: str | None = Query(None, description="Filter by name substring"),
    category: str | None = Query(None, description="Filter by category value"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> CatalogPage:
    return admin.catalog_services(db, q=q, category=category, limit=limit, offset=offset)


@router.get("/unmatched", response_model=UnmatchedPage)
def get_unmatched_queue(
    status: str = Query("pending", description="Queue status to list"),
    q: str | None = Query(None, description="Search raw name or suggested candidate"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> UnmatchedPage:
    return admin.unmatched_queue(db, status=status, q=q, limit=limit, offset=offset)


@router.get("/parse-runs", response_model=list[ParseRunSummary])
def get_parse_runs(
    limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)
) -> list[ParseRunSummary]:
    return admin.list_runs(db, limit=limit)


@router.get("/parse-runs/{run_id}", response_model=ParseRunDetail)
def get_parse_run(run_id: int, db: Session = Depends(get_db)) -> ParseRunDetail:
    detail = admin.run_detail(db, run_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return detail
