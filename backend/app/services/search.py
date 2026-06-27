from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import Float, func, or_, select
from sqlalchemy.orm import Session

from app.core.cities import CITIES, City
from app.models import (
    Clinic,
    ClinicBranch,
    ClinicServicePrice,
    RawPriceItem,
    Service,
    ServiceAlias,
)

FRESH_DAYS = 7
STALE_DAYS = 30
RESOLVE_FLOOR = 0.2

# Best-Value weights (distance/duration omitted this round and renormalized — see §12).
W_PRICE = 0.55
W_FRESH = 0.30
W_CONF = 0.15


@dataclass(frozen=True)
class Suggestion:
    id: int
    name_ru: str
    category: str
    score: float
    has_prices: bool


@dataclass(frozen=True)
class PriceCard:
    price_id: int
    service_id: int
    service_name: str
    clinic_id: int
    clinic_name: str
    doctor_name: str | None
    branch_id: int | None
    city: str | None
    address: str | None
    lat: float | None
    lng: float | None
    price_kzt: int
    duration_min: int | None
    duration_max: int | None
    parsed_at: datetime
    age_days: int
    freshness: str  # fresh | recent | stale
    source_url: str
    service_name_raw: str | None
    content_hash: str | None
    match_confidence: float
    match_method: str | None


@dataclass(frozen=True)
class MapPin:
    price_id: int
    clinic_id: int
    clinic_name: str
    branch_id: int
    city: str | None
    address: str | None
    lat: float
    lng: float
    price_kzt: int
    parsed_at: datetime
    age_days: int
    freshness: str
    source_url: str
    is_cheapest: bool


def _freshness(age_days: int) -> str:
    if age_days <= FRESH_DAYS:
        return "fresh"
    if age_days <= STALE_DAYS:
        return "recent"
    return "stale"


def available_cities(session: Session) -> list[City]:
    """Canonical cities that currently have active prices, in canonical order."""
    present = set(
        session.scalars(
            select(ClinicServicePrice.city)
            .where(
                ClinicServicePrice.is_active.is_(True),
                ClinicServicePrice.city.is_not(None),
            )
            .distinct()
        ).all()
    )
    return [c for c in CITIES if c.name in present]


def autocomplete(session: Session, q: str, limit: int = 10) -> list[Suggestion]:
    """Lexical autocomplete over service names + aliases. Never embeds."""
    q = (q or "").strip()
    if len(q) < 2:
        return []

    pattern = f"%{q}%"
    name_sim = func.similarity(Service.name_ru, q)
    alias_sim = func.coalesce(func.max(func.similarity(ServiceAlias.alias, q)), 0.0)
    score = func.greatest(name_sim, alias_sim)
    price_count = (
        select(func.count(ClinicServicePrice.id))
        .where(
            ClinicServicePrice.service_id == Service.id,
            ClinicServicePrice.is_active.is_(True),
        )
        .correlate(Service)
        .scalar_subquery()
    )

    stmt = (
        select(
            Service.id,
            Service.name_ru,
            Service.category,
            score.label("score"),
            price_count.label("price_count"),
        )
        .outerjoin(ServiceAlias, ServiceAlias.service_id == Service.id)
        .where(
            or_(
                Service.name_ru.ilike(pattern),
                ServiceAlias.alias.ilike(pattern),
                name_sim > RESOLVE_FLOOR,
            )
        )
        .group_by(Service.id)
        .order_by((price_count > 0).desc(), score.desc(), Service.name_ru)
        .limit(limit)
    )

    return [
        Suggestion(
            id=row.id,
            name_ru=row.name_ru,
            category=row.category.value,
            score=round(float(row.score), 3),
            has_prices=row.price_count > 0,
        )
        for row in session.execute(stmt)
    ]


def resolve_query(session: Session, q: str) -> tuple[Suggestion | None, list[Suggestion]]:
    """Resolve a typed query to the best catalog service plus alternatives (lexical only)."""
    candidates = autocomplete(session, q, limit=8)
    if not candidates:
        return None, []
    return candidates[0], candidates


def prices_for_service(
    session: Session,
    service_id: int,
    *,
    city: str | None = None,
    sort: str = "best_value",
    include_stale: bool = False,
    price_min: int | None = None,
    price_max: int | None = None,
) -> list[PriceCard]:
    now = datetime.now(UTC)
    age_days = func.floor(
        func.extract("epoch", now - ClinicServicePrice.parsed_at) / 86400.0
    ).cast(Float)

    stmt = (
        select(
            ClinicServicePrice,
            Clinic,
            ClinicBranch,
            Service,
            RawPriceItem.metadata_json,
            age_days.label("age"),
        )
        .join(Clinic, ClinicServicePrice.clinic_id == Clinic.id)
        .join(Service, ClinicServicePrice.service_id == Service.id)
        .outerjoin(ClinicBranch, ClinicServicePrice.branch_id == ClinicBranch.id)
        .outerjoin(RawPriceItem, ClinicServicePrice.raw_price_item_id == RawPriceItem.id)
        .where(
            ClinicServicePrice.service_id == service_id,
            ClinicServicePrice.is_active.is_(True),
        )
    )
    if city:
        stmt = stmt.where(ClinicServicePrice.city == city)
    if price_min is not None:
        stmt = stmt.where(ClinicServicePrice.price_kzt >= price_min)
    if price_max is not None:
        stmt = stmt.where(ClinicServicePrice.price_kzt <= price_max)
    if not include_stale:
        stmt = stmt.where(age_days <= STALE_DAYS)

    cards = [
        _build_card(price, clinic, branch, service, metadata, int(age))
        for price, clinic, branch, service, metadata, age in session.execute(stmt)
    ]
    return _sort_cards(cards, sort)


def _doctor_name(metadata: dict | None) -> str | None:
    name = (metadata or {}).get("doctor")
    return name.strip() if isinstance(name, str) and name.strip() else None


def _build_card(
    price: ClinicServicePrice,
    clinic: Clinic,
    branch: ClinicBranch | None,
    service: Service,
    metadata: dict | None,
    age_days: int,
) -> PriceCard:
    return PriceCard(
        price_id=price.id,
        service_id=service.id,
        service_name=service.name_ru,
        clinic_id=clinic.id,
        clinic_name=clinic.name,
        doctor_name=_doctor_name(metadata),
        branch_id=branch.id if branch else None,
        city=branch.city if branch else price.city,
        address=branch.address if branch else None,
        lat=branch.lat if branch else None,
        lng=branch.lng if branch else None,
        price_kzt=price.price_kzt,
        duration_min=price.duration_min,
        duration_max=price.duration_max,
        parsed_at=price.parsed_at,
        age_days=age_days,
        freshness=_freshness(age_days),
        source_url=price.source_url,
        service_name_raw=price.service_name_raw,
        content_hash=price.content_hash,
        match_confidence=price.match_confidence,
        match_method=price.match_method,
    )


def featured_cards(session: Session, limit: int = 6) -> list[PriceCard]:
    """A random sample of fresh active prices for the landing page (no query)."""
    now = datetime.now(UTC)
    age_days = func.floor(
        func.extract("epoch", now - ClinicServicePrice.parsed_at) / 86400.0
    ).cast(Float)

    stmt = (
        select(
            ClinicServicePrice,
            Clinic,
            ClinicBranch,
            Service,
            RawPriceItem.metadata_json,
            age_days.label("age"),
        )
        .join(Clinic, ClinicServicePrice.clinic_id == Clinic.id)
        .join(Service, ClinicServicePrice.service_id == Service.id)
        .outerjoin(ClinicBranch, ClinicServicePrice.branch_id == ClinicBranch.id)
        .outerjoin(RawPriceItem, ClinicServicePrice.raw_price_item_id == RawPriceItem.id)
        .where(
            ClinicServicePrice.is_active.is_(True),
            age_days <= STALE_DAYS,
        )
        .order_by(func.random())
        .limit(limit)
    )

    return [
        _build_card(price, clinic, branch, service, metadata, int(age))
        for price, clinic, branch, service, metadata, age in session.execute(stmt)
    ]


def map_pins(
    session: Session,
    service_id: int,
    *,
    city: str | None = None,
    bbox: tuple[float, float, float, float] | None = None,
) -> list[MapPin]:
    """Active, fresh, geocoded prices for a service as map pins. DB-only (Rule 1).

    `bbox` is (min_lng, min_lat, max_lng, max_lat) — Leaflet's `toBBoxString` order.
    """
    now = datetime.now(UTC)
    age_days = func.floor(
        func.extract("epoch", now - ClinicServicePrice.parsed_at) / 86400.0
    ).cast(Float)

    # Clinics with an active, fresh, city-wide price for this service.
    price_stmt = (
        select(ClinicServicePrice, Clinic, age_days.label("age"))
        .join(Clinic, ClinicServicePrice.clinic_id == Clinic.id)
        .where(
            ClinicServicePrice.service_id == service_id,
            ClinicServicePrice.is_active.is_(True),
            age_days <= STALE_DAYS,
        )
    )
    if city:
        price_stmt = price_stmt.where(ClinicServicePrice.city == city)
    priced = session.execute(price_stmt).all()
    if not priced:
        return []

    cheapest_price = min(price.price_kzt for price, _clinic, _age in priced)
    pins: list[MapPin] = []
    for price, clinic, age in priced:
        # Fan the city-wide price out to every collection point of that clinic.
        branch_stmt = select(ClinicBranch).where(
            ClinicBranch.clinic_id == clinic.id,
            ClinicBranch.city == (city or price.city),
            ClinicBranch.lat.is_not(None),
            ClinicBranch.lng.is_not(None),
        )
        if bbox is not None:
            min_lng, min_lat, max_lng, max_lat = bbox
            branch_stmt = branch_stmt.where(
                ClinicBranch.lng >= min_lng,
                ClinicBranch.lng <= max_lng,
                ClinicBranch.lat >= min_lat,
                ClinicBranch.lat <= max_lat,
            )
        is_cheapest = price.price_kzt == cheapest_price
        for branch in session.scalars(branch_stmt):
            pins.append(
                MapPin(
                    price_id=price.id,
                    clinic_id=clinic.id,
                    clinic_name=clinic.name,
                    branch_id=branch.id,
                    city=branch.city,
                    address=branch.address,
                    lat=branch.lat,
                    lng=branch.lng,
                    price_kzt=price.price_kzt,
                    parsed_at=price.parsed_at,
                    age_days=int(age),
                    freshness=_freshness(int(age)),
                    source_url=price.source_url,
                    is_cheapest=is_cheapest,
                )
            )
    return pins


def _sort_cards(cards: list[PriceCard], sort: str) -> list[PriceCard]:
    if not cards:
        return cards
    if sort == "cheapest":
        return sorted(cards, key=lambda c: c.price_kzt)
    if sort == "newest":
        return sorted(cards, key=lambda c: c.age_days)

    prices = [c.price_kzt for c in cards]
    lo, hi = min(prices), max(prices)
    span = (hi - lo) or 1

    def value(c: PriceCard) -> float:
        price_score = (hi - c.price_kzt) / span
        fresh_score = 1.0 - min(c.age_days, STALE_DAYS) / STALE_DAYS
        return (
            W_PRICE * price_score
            + W_FRESH * fresh_score
            + W_CONF * c.match_confidence
        )

    return sorted(cards, key=value, reverse=True)
