from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.search import PriceCard, SearchResponse
from app.services import search

router = APIRouter()


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
