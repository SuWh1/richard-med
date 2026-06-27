from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.catalog import ServiceCategory
from app.schemas.analytics import AnalyticsOverview, ServicePriceStat
from app.services import analytics

router = APIRouter()


@router.get("/price-stats", response_model=list[ServicePriceStat])
def price_stats(
    city: str | None = None,
    category: ServiceCategory | None = None,
    include_stale: bool = False,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[ServicePriceStat]:
    return analytics.service_price_stats(
        db,
        city=city,
        category=category,
        include_stale=include_stale,
        limit=limit,
    )


@router.get("/overview", response_model=AnalyticsOverview)
def overview(
    city: str | None = None,
    include_stale: bool = False,
    db: Session = Depends(get_db),
) -> AnalyticsOverview:
    return analytics.category_overview(db, city=city, include_stale=include_stale)
