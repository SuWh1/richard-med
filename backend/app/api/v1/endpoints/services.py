from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.search import PriceCard, Suggestion
from app.services import search

router = APIRouter()


@router.get("", response_model=list[Suggestion])
def autocomplete_services(
    q: str = Query(..., min_length=2),
    limit: int = Query(10, ge=1, le=25),
    category: str | None = Query(
        None, pattern="^(лаборатория|приём врача|диагностика|процедура)$"
    ),
    db: Session = Depends(get_db),
) -> list[Suggestion]:
    return search.autocomplete(db, q, limit=limit, category=category)


@router.get("/{service_id}/prices", response_model=list[PriceCard])
def service_prices(
    service_id: int,
    city: str | None = None,
    sort: str = Query("best_value", pattern="^(best_value|cheapest|newest)$"),
    include_stale: bool = False,
    price_min: int | None = Query(None, ge=0),
    price_max: int | None = Query(None, ge=0),
    db: Session = Depends(get_db),
) -> list[PriceCard]:
    return search.prices_for_service(
        db,
        service_id,
        city=city,
        sort=sort,
        include_stale=include_stale,
        price_min=price_min,
        price_max=price_max,
    )
