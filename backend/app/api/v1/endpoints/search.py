import math

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Service
from app.schemas.clinics import CompareInsight, CompareResult
from app.schemas.search import CityOut, MapPin, PriceCard, SearchResponse
from app.services import clinics, compare_insight, live_search, search

router = APIRouter()


@router.get("/cities", response_model=list[CityOut])
def list_cities(db: Session = Depends(get_db)) -> list[CityOut]:
    return search.available_cities(db)


def _parse_clinic_ids(clinic_ids: str) -> list[int]:
    try:
        ids = [int(p) for p in clinic_ids.split(",") if p.strip()]
    except ValueError as exc:
        raise HTTPException(
            status_code=422, detail="clinic_ids must be comma-separated integers"
        ) from exc
    if not ids:
        raise HTTPException(status_code=422, detail="clinic_ids must not be empty")
    return ids


def _parse_bbox(bbox: str | None) -> tuple[float, float, float, float] | None:
    if bbox is None:
        return None
    try:
        corners = tuple(float(p) for p in bbox.split(","))
    except ValueError as exc:
        raise HTTPException(
            status_code=422, detail="bbox must be 'min_lng,min_lat,max_lng,max_lat'"
        ) from exc
    if len(corners) != 4 or not all(math.isfinite(v) for v in corners):
        raise HTTPException(
            status_code=422, detail="bbox must be four finite numbers"
        )
    min_lng, min_lat, max_lng, max_lat = corners
    return (min_lng, min_lat, max_lng, max_lat)


@router.get("/featured", response_model=list[PriceCard])
def featured_services(
    limit: int = Query(6, ge=1, le=24),
    db: Session = Depends(get_db),
) -> list[PriceCard]:
    return search.featured_cards(db, limit=limit)


@router.get("", response_model=SearchResponse)
def search_services(
    q: str = Query(..., min_length=2),
    city: str | None = None,
    category: str | None = Query(
        None, pattern="^(лаборатория|приём врача|диагностика|процедура)$"
    ),
    sort: str = Query("best_value", pattern="^(best_value|cheapest|newest)$"),
    include_stale: bool = False,
    price_min: int | None = Query(None, ge=0),
    price_max: int | None = Query(None, ge=0),
    lat: float | None = Query(None, ge=-90, le=90),
    lng: float | None = Query(None, ge=-180, le=180),
    db: Session = Depends(get_db),
) -> SearchResponse:
    def _resolve_and_price() -> tuple:
        found, sugg = search.resolve_query(db, q, category=category)
        rows = (
            search.prices_for_service(
                db,
                found.id,
                city=city,
                sort=sort,
                include_stale=include_stale,
                price_min=price_min,
                price_max=price_max,
                lat=lat,
                lng=lng,
            )
            if found is not None
            else []
        )
        return found, sugg, rows

    resolved, suggestions, cards = _resolve_and_price()

    # On a miss, try a live DOQ lookup for the exact query: it persists the service and
    # its prices to the DB (source-backed, auditable), then we re-resolve so the user
    # gets real cards now. Best-effort and time-boxed — failure leaves the empty result.
    if not cards and live_search.live_fetch_doq(db, q, city) is not None:
        resolved, suggestions, cards = _resolve_and_price()

    return SearchResponse(
        query=q,
        resolved_service=resolved,
        suggestions=suggestions,
        cards=cards,
        count=len(cards),
    )


@router.get("/map", response_model=list[MapPin])
def map_prices(
    service_id: int = Query(..., ge=1),
    city: str | None = None,
    bbox: str | None = Query(None, description="min_lng,min_lat,max_lng,max_lat"),
    db: Session = Depends(get_db),
) -> list[MapPin]:
    return search.map_pins(db, service_id, city=city, bbox=_parse_bbox(bbox))


@router.get("/compare", response_model=CompareResult)
def compare_clinics(
    service_id: int = Query(..., ge=1),
    clinic_ids: str = Query(..., description="comma-separated clinic ids"),
    city: str | None = Query(None),
    db: Session = Depends(get_db),
) -> CompareResult:
    result = clinics.compare(db, service_id, _parse_clinic_ids(clinic_ids), city=city)
    if result is None:
        raise HTTPException(status_code=404, detail="Service not found")
    return result


@router.get("/compare/insight", response_model=CompareInsight)
def compare_insight_endpoint(
    service_id: int = Query(..., ge=1),
    clinic_ids: str = Query(..., description="comma-separated clinic ids"),
    db: Session = Depends(get_db),
) -> CompareInsight:
    service = db.get(Service, service_id)
    if service is None:
        raise HTTPException(status_code=404, detail="Service not found")
    try:
        return compare_insight.compare_insight(
            db,
            service_id,
            service.name_ru,
            _parse_clinic_ids(clinic_ids),
            llm=compare_insight.get_insighter(),
        )
    except compare_insight.InsightUnavailable as exc:
        raise HTTPException(
            status_code=503, detail="AI comparison temporarily unavailable"
        ) from exc
