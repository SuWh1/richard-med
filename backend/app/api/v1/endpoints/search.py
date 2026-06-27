import math

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.clinics import CompareResult
from app.schemas.search import CityOut, MapPin, PriceCard, SearchResponse
from app.services import clinics, search

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
    sort: str = Query("best_value", pattern="^(best_value|cheapest|newest)$"),
    include_stale: bool = False,
    price_min: int | None = Query(None, ge=0),
    price_max: int | None = Query(None, ge=0),
    db: Session = Depends(get_db),
) -> SearchResponse:
    resolved, suggestions = search.resolve_query(db, q)
    cards = []
    if resolved is not None:
        cards = search.prices_for_service(
            db,
            resolved.id,
            city=city,
            sort=sort,
            include_stale=include_stale,
            price_min=price_min,
            price_max=price_max,
        )
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
    db: Session = Depends(get_db),
) -> CompareResult:
    result = clinics.compare(db, service_id, _parse_clinic_ids(clinic_ids))
    if result is None:
        raise HTTPException(status_code=404, detail="Service not found")
    return result
