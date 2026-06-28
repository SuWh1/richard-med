from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.cities import CITY_NAMES
from app.db.session import get_db
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
from app.services.parse_runner import run_sources

router = APIRouter()

ALL_CITIES = "__all__"  # sentinel: run every supported city


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
    background_tasks.add_task(run_sources, sources, cities)
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
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> UnmatchedPage:
    return admin.unmatched_queue(db, status=status, limit=limit, offset=offset)


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
