import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import SessionLocal, get_db
from app.schemas.admin import (
    ParseRunDetail,
    ParseRunSummary,
    RunTrigger,
    SourceHealth,
)
from app.scrapers.registry import available_sources
from app.services import admin
from app.services.embeddings import get_embedder
from app.services.pipeline import run_source

logger = logging.getLogger(__name__)
router = APIRouter()


def _run_sources(source_names: list[str], city: str) -> None:
    session = SessionLocal()
    embedder = get_embedder()
    try:
        for source in source_names:
            try:
                run_source(session, source, city, publish=True, embedder=embedder)
                session.commit()
            except Exception:  # noqa: BLE001 — isolate one source from the rest
                logger.exception("background run failed for %s", source)
                session.rollback()
    finally:
        session.close()


@router.post("/parsers/run", response_model=RunTrigger)
def trigger_run(
    background_tasks: BackgroundTasks,
    source: str | None = Query(None, description="Source name; omit to run all sources"),
    city: str = Query("Астана"),
) -> RunTrigger:
    sources = available_sources() if source is None else [source]
    unknown = [s for s in sources if s not in available_sources()]
    if unknown:
        raise HTTPException(status_code=404, detail=f"Unknown source(s): {unknown}")

    background_tasks.add_task(_run_sources, sources, city)
    return RunTrigger(
        accepted=True,
        source_names=sources,
        city=city,
        message=f"Запущен парсинг ({', '.join(sources)}) для города {city}.",
    )


@router.get("/source-health", response_model=list[SourceHealth])
def get_source_health(db: Session = Depends(get_db)) -> list[SourceHealth]:
    return admin.source_health(db)


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
