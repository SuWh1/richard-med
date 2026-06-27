from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import ClinicServicePrice, Service
from app.models.catalog import ServiceCategory
from app.services.search import STALE_DAYS


@dataclass(frozen=True)
class ServicePriceStat:
    service_id: int
    service_name: str
    category: str
    city: str | None
    clinic_count: int
    price_count: int
    min_kzt: int
    max_kzt: int
    avg_kzt: int
    median_kzt: int
    spread_pct: float
    freshest_parsed_at: datetime


@dataclass(frozen=True)
class CategoryStat:
    category: str
    service_count: int
    price_count: int
    min_kzt: int
    max_kzt: int
    median_kzt: int


@dataclass(frozen=True)
class CityCoverage:
    city: str
    price_count: int
    service_count: int


@dataclass(frozen=True)
class AnalyticsOverview:
    city: str | None
    total_prices: int
    total_services: int
    categories: list[CategoryStat]
    cities: list[CityCoverage]


def _age_days():
    now = datetime.now(UTC)
    return func.floor(
        func.extract("epoch", now - ClinicServicePrice.parsed_at) / 86400.0
    )


def _spread_pct(min_kzt: int, max_kzt: int) -> float:
    if min_kzt <= 0:
        return 0.0
    return round((max_kzt - min_kzt) / min_kzt * 100, 1)


def _base_where(stmt, *, include_stale: bool):
    stmt = stmt.where(ClinicServicePrice.is_active.is_(True))
    if not include_stale:
        stmt = stmt.where(_age_days() <= STALE_DAYS)
    return stmt


def service_price_stats(
    session: Session,
    *,
    city: str | None = None,
    category: ServiceCategory | None = None,
    include_stale: bool = False,
    limit: int = 50,
) -> list[ServicePriceStat]:
    """Per-service price aggregation across clinics — avg/min/max/median over the same service."""
    median = func.percentile_cont(0.5).within_group(ClinicServicePrice.price_kzt)
    stmt = (
        select(
            Service.id,
            Service.name_ru,
            Service.category,
            func.count(func.distinct(ClinicServicePrice.clinic_id)).label("clinic_count"),
            func.count(ClinicServicePrice.id).label("price_count"),
            func.min(ClinicServicePrice.price_kzt).label("min_kzt"),
            func.max(ClinicServicePrice.price_kzt).label("max_kzt"),
            func.avg(ClinicServicePrice.price_kzt).label("avg_kzt"),
            median.label("median_kzt"),
            func.max(ClinicServicePrice.parsed_at).label("freshest"),
        )
        .join(Service, ClinicServicePrice.service_id == Service.id)
        .group_by(Service.id)
        .order_by(func.count(ClinicServicePrice.id).desc(), Service.name_ru)
        .limit(limit)
    )
    stmt = _base_where(stmt, include_stale=include_stale)
    if city:
        stmt = stmt.where(ClinicServicePrice.city == city)
    if category is not None:
        stmt = stmt.where(Service.category == category)

    return [
        ServicePriceStat(
            service_id=row.id,
            service_name=row.name_ru,
            category=row.category.value,
            city=city,
            clinic_count=row.clinic_count,
            price_count=row.price_count,
            min_kzt=int(row.min_kzt),
            max_kzt=int(row.max_kzt),
            avg_kzt=round(float(row.avg_kzt)),
            median_kzt=round(float(row.median_kzt)),
            spread_pct=_spread_pct(int(row.min_kzt), int(row.max_kzt)),
            freshest_parsed_at=row.freshest,
        )
        for row in session.execute(stmt)
    ]


def category_overview(
    session: Session,
    *,
    city: str | None = None,
    include_stale: bool = False,
) -> AnalyticsOverview:
    """Category-level ranges (never a blended average) plus per-city coverage counts."""
    median = func.percentile_cont(0.5).within_group(ClinicServicePrice.price_kzt)
    cat_stmt = (
        select(
            Service.category,
            func.count(func.distinct(ClinicServicePrice.service_id)).label("service_count"),
            func.count(ClinicServicePrice.id).label("price_count"),
            func.min(ClinicServicePrice.price_kzt).label("min_kzt"),
            func.max(ClinicServicePrice.price_kzt).label("max_kzt"),
            median.label("median_kzt"),
        )
        .join(Service, ClinicServicePrice.service_id == Service.id)
        .group_by(Service.category)
        .order_by(func.count(ClinicServicePrice.id).desc())
    )
    cat_stmt = _base_where(cat_stmt, include_stale=include_stale)
    if city:
        cat_stmt = cat_stmt.where(ClinicServicePrice.city == city)

    categories = [
        CategoryStat(
            category=row.category.value,
            service_count=row.service_count,
            price_count=row.price_count,
            min_kzt=int(row.min_kzt),
            max_kzt=int(row.max_kzt),
            median_kzt=round(float(row.median_kzt)),
        )
        for row in session.execute(cat_stmt)
    ]

    city_stmt = (
        select(
            ClinicServicePrice.city,
            func.count(ClinicServicePrice.id).label("price_count"),
            func.count(func.distinct(ClinicServicePrice.service_id)).label("service_count"),
        )
        .where(ClinicServicePrice.city.is_not(None))
        .group_by(ClinicServicePrice.city)
        .order_by(func.count(ClinicServicePrice.id).desc())
    )
    city_stmt = _base_where(city_stmt, include_stale=include_stale)
    if city:
        city_stmt = city_stmt.where(ClinicServicePrice.city == city)

    cities = [
        CityCoverage(
            city=row.city,
            price_count=row.price_count,
            service_count=row.service_count,
        )
        for row in session.execute(city_stmt)
    ]

    return AnalyticsOverview(
        city=city,
        total_prices=sum(c.price_count for c in categories),
        total_services=sum(c.service_count for c in categories),
        categories=categories,
        cities=cities,
    )
