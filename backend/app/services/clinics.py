from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import Float, case, func, select
from sqlalchemy.orm import Session

from app.models import (
    Clinic,
    ClinicBranch,
    ClinicReview,
    ClinicServicePrice,
    Service,
)
from app.services.search import STALE_DAYS, _freshness


@dataclass(frozen=True)
class BranchInfo:
    id: int
    city: str | None
    address: str | None
    lat: float | None
    lng: float | None
    phone: str | None
    working_hours: str | None
    rating: float | None
    reviews_count: int | None


@dataclass(frozen=True)
class ClinicDetail:
    id: int
    name: str
    website_url: str | None
    source_name: str
    rating: float | None
    reviews_count: int
    branches: list[BranchInfo]


@dataclass(frozen=True)
class ReviewRow:
    id: int
    author: str | None
    rating: int | None
    text: str | None
    official_answer: str | None
    review_date: datetime | None
    source: str
    branch_id: int
    city: str | None


@dataclass(frozen=True)
class ClinicServiceRow:
    service_id: int
    service_name: str
    category: str
    price_kzt: int
    parsed_at: datetime
    age_days: int
    freshness: str
    source_url: str
    city: str | None
    branch_id: int | None


@dataclass(frozen=True)
class CompareRow:
    clinic_id: int
    clinic_name: str
    branch_id: int | None
    city: str | None
    address: str | None
    price_kzt: int
    duration_min: int | None
    duration_max: int | None
    parsed_at: datetime
    age_days: int
    freshness: str
    source_url: str
    is_cheapest: bool
    price_delta: int
    delta_pct: float
    price_rank: int


@dataclass(frozen=True)
class CompareResult:
    service_id: int
    service_name: str
    rows: list[CompareRow]


def _age_expr():
    now = datetime.now(UTC)
    return func.floor(
        func.extract("epoch", now - ClinicServicePrice.parsed_at) / 86400.0
    ).cast(Float)


def _aggregate_rating(branches) -> tuple[float | None, int]:
    """Clinic rating = branch ratings weighted by each branch's review count."""
    weighted = sum(
        b.rating * b.reviews_count
        for b in branches
        if b.rating is not None and b.reviews_count
    )
    total = sum(b.reviews_count for b in branches if b.rating is not None and b.reviews_count)
    if total == 0:
        return None, 0
    return round(weighted / total, 2), total


def clinic_detail(session: Session, clinic_id: int) -> ClinicDetail | None:
    clinic = session.get(Clinic, clinic_id)
    if clinic is None:
        return None
    branches = session.scalars(
        select(ClinicBranch).where(ClinicBranch.clinic_id == clinic_id)
    ).all()
    rating, reviews_count = _aggregate_rating(branches)
    return ClinicDetail(
        id=clinic.id,
        name=clinic.name,
        website_url=clinic.website_url,
        source_name=clinic.source_name,
        rating=rating,
        reviews_count=reviews_count,
        branches=[
            BranchInfo(
                id=b.id,
                city=b.city,
                address=b.address,
                lat=b.lat,
                lng=b.lng,
                phone=b.phone,
                working_hours=b.working_hours,
                rating=b.rating,
                reviews_count=b.reviews_count,
            )
            for b in branches
        ],
    )


def clinic_reviews(
    session: Session, clinic_id: int, *, limit: int = 20, offset: int = 0
) -> list[ReviewRow]:
    stmt = (
        select(ClinicReview, ClinicBranch.city)
        .join(ClinicBranch, ClinicReview.branch_id == ClinicBranch.id)
        .where(ClinicBranch.clinic_id == clinic_id)
        .order_by(ClinicReview.review_date.desc().nulls_last(), ClinicReview.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return [
        ReviewRow(
            id=r.id,
            author=r.author,
            rating=r.rating,
            text=r.text,
            official_answer=r.official_answer,
            review_date=r.review_date,
            source=r.source,
            branch_id=r.branch_id,
            city=city,
        )
        for r, city in session.execute(stmt)
    ]


def clinic_services(
    session: Session, clinic_id: int, *, include_stale: bool = False
) -> list[ClinicServiceRow]:
    age = _age_expr()
    # DISTINCT ON keeps one row per service (its cheapest active offer), so a clinic
    # with many branches/cities doesn't return the same service dozens of times.
    stmt = (
        select(ClinicServicePrice, Service, ClinicBranch, age.label("age"))
        .join(Service, ClinicServicePrice.service_id == Service.id)
        .outerjoin(ClinicBranch, ClinicServicePrice.branch_id == ClinicBranch.id)
        .where(
            ClinicServicePrice.clinic_id == clinic_id,
            ClinicServicePrice.is_active.is_(True),
        )
        .order_by(ClinicServicePrice.service_id, ClinicServicePrice.price_kzt)
        .distinct(ClinicServicePrice.service_id)
    )
    if not include_stale:
        stmt = stmt.where(age <= STALE_DAYS)

    rows = [
        ClinicServiceRow(
            service_id=service.id,
            service_name=service.name_ru,
            category=service.category.value,
            price_kzt=price.price_kzt,
            parsed_at=price.parsed_at,
            age_days=int(age_days),
            freshness=_freshness(int(age_days)),
            source_url=price.source_url,
            city=branch.city if branch else None,
            branch_id=branch.id if branch else None,
        )
        for price, service, branch, age_days in session.execute(stmt)
    ]
    rows.sort(key=lambda r: r.price_kzt)
    return rows


def compare(
    session: Session,
    service_id: int,
    clinic_ids: list[int],
    city: str | None = None,
) -> CompareResult | None:
    service = session.get(Service, service_id)
    if service is None:
        return None

    age = _age_expr()
    stmt = (
        select(ClinicServicePrice, Clinic, ClinicBranch, age.label("age"))
        .join(Clinic, ClinicServicePrice.clinic_id == Clinic.id)
        .outerjoin(ClinicBranch, ClinicServicePrice.branch_id == ClinicBranch.id)
        .where(
            ClinicServicePrice.service_id == service_id,
            ClinicServicePrice.clinic_id.in_(clinic_ids),
            ClinicServicePrice.is_active.is_(True),
        )
    )
    if city:
        city_rank = case((ClinicServicePrice.city == city, 0), else_=1)
        stmt = stmt.order_by(city_rank, ClinicServicePrice.price_kzt)
    else:
        stmt = stmt.order_by(ClinicServicePrice.price_kzt)

    results = session.execute(stmt).all()
    if not results:
        return CompareResult(service_id=service.id, service_name=service.name_ru, rows=[])

    # Keep one row per clinic: the requested-city price when present, else its cheapest.
    seen: set[int] = set()
    chosen: list[tuple] = []
    for row in results:
        clinic_id = row[1].id
        if clinic_id in seen:
            continue
        seen.add(clinic_id)
        chosen.append(row)

    chosen.sort(key=lambda r: r[0].price_kzt)
    cheapest_price = chosen[0][0].price_kzt
    cheapest_id = chosen[0][0].id
    rows: list[CompareRow] = []
    for price, clinic, branch, age_days in chosen:
        delta = price.price_kzt - cheapest_price
        rows.append(
            CompareRow(
                clinic_id=clinic.id,
                clinic_name=clinic.name,
                branch_id=branch.id if branch else None,
                city=branch.city if branch else price.city,
                address=branch.address if branch else None,
                price_kzt=price.price_kzt,
                duration_min=price.duration_min,
                duration_max=price.duration_max,
                parsed_at=price.parsed_at,
                age_days=int(age_days),
                freshness=_freshness(int(age_days)),
                source_url=price.source_url,
                is_cheapest=price.id == cheapest_id,
                price_delta=delta,
                delta_pct=round(delta / cheapest_price * 100, 1) if cheapest_price else 0.0,
                price_rank=len(rows) + 1,
            )
        )
    return CompareResult(service_id=service.id, service_name=service.name_ru, rows=rows)
