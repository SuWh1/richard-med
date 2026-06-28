from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import Float, desc, func, or_, select
from sqlalchemy.orm import Session

from app.core.cities import CITIES, City
from app.models import (
    Clinic,
    ClinicBranch,
    ClinicServicePrice,
    Doctor,
    RawPriceItem,
    Service,
    ServiceAlias,
    ServiceCategory,
)
from app.services.embeddings import get_embedder
from app.services.normalization import ServiceMatcher, canonical_clean

FRESH_DAYS = 7
STALE_DAYS = 30
RESOLVE_FLOOR = 0.2
# Quarantined catalog rows never appear in user-facing search/autocomplete/map.
HIDDEN_CATEGORIES = (ServiceCategory.other,)

# Best-Value weights (distance/duration omitted this round and renormalized — see §12).
W_PRICE = 0.55
W_FRESH = 0.30
W_CONF = 0.15


@dataclass(frozen=True)
class Suggestion:
    id: int
    name_ru: str
    category: str
    specialty: str | None
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
    rating: float | None
    reviews_count: int | None
    branch_count: int
    doctor_id: int | None = None
    doctor_avatar: str | None = None
    doctor_experience: int | None = None
    doctor_rating: float | None = None
    doctor_reviews: int | None = None
    qualification: str | None = None
    district: str | None = None
    base_price_kzt: int | None = None
    discount_percent: int | None = None
    source_category: str | None = None


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


def autocomplete(
    session: Session,
    q: str,
    limit: int = 10,
    category: str | None = None,
    city: str | None = None,
) -> list[Suggestion]:
    """Lexical autocomplete over service names + aliases. Never embeds.

    Prefix matches rank first, then services that have prices, then trigram score.
    Duplicate `name_ru` rows (same service under different specialties) collapse to a
    single suggestion — disambiguated by `specialty` — so the list never repeats a name.
    When `city` is given, `has_prices` reflects that city only, so a suggestion never
    claims availability the city-scoped price view can't honour.
    """
    q = (q or "").strip()
    if len(q) < 2:
        return []

    pattern = f"%{q}%"
    prefix = f"{q}%"
    name_sim = func.similarity(Service.name_ru, q)
    alias_sim = func.coalesce(func.max(func.similarity(ServiceAlias.alias, q)), 0.0)
    score = func.greatest(name_sim, alias_sim)
    is_prefix = func.coalesce(
        func.bool_or(
            Service.name_ru.ilike(prefix)
            | func.coalesce(ServiceAlias.alias.ilike(prefix), False)
        ),
        False,
    )
    price_filters = [
        ClinicServicePrice.service_id == Service.id,
        ClinicServicePrice.is_active.is_(True),
    ]
    if city:
        price_filters.append(ClinicServicePrice.city == city)
    price_count = (
        select(func.count(ClinicServicePrice.id))
        .where(*price_filters)
        .correlate(Service)
        .scalar_subquery()
    )

    filters = [
        Service.category.not_in(HIDDEN_CATEGORIES),
        or_(
            Service.name_ru.ilike(pattern),
            ServiceAlias.alias.ilike(pattern),
            name_sim > RESOLVE_FLOOR,
        ),
    ]
    if category:
        try:
            filters.append(Service.category == ServiceCategory(category))
        except ValueError:
            pass  # invalid category → endpoint rejects it; ignore defensively here

    grouped = (
        select(
            Service.id.label("id"),
            Service.name_ru.label("name_ru"),
            Service.category.label("category"),
            Service.specialty.label("specialty"),
            score.label("score"),
            price_count.label("price_count"),
            is_prefix.label("is_prefix"),
        )
        .outerjoin(ServiceAlias, ServiceAlias.service_id == Service.id)
        .where(*filters)
        .group_by(Service.id)
        .subquery()
    )
    # Keep the strongest row per name_ru (priced > prefix > score), then re-rank by
    # relevance across names and cap to `limit`.
    deduped = (
        select(grouped)
        .distinct(grouped.c.name_ru)
        .order_by(
            grouped.c.name_ru,
            (grouped.c.price_count > 0).desc(),
            grouped.c.is_prefix.desc(),
            grouped.c.score.desc(),
        )
        .subquery()
    )
    stmt = (
        select(deduped)
        .order_by(
            deduped.c.is_prefix.desc(),
            (deduped.c.price_count > 0).desc(),
            deduped.c.score.desc(),
            deduped.c.name_ru,
        )
        .limit(limit)
    )

    return [
        Suggestion(
            id=row.id,
            name_ru=row.name_ru,
            category=row.category.value,
            specialty=row.specialty,
            score=round(float(row.score), 3),
            has_prices=row.price_count > 0,
        )
        for row in session.execute(stmt)
    ]


_USE_DEFAULT_EMBEDDER = object()
# Lexical methods we trust enough to resolve directly to a price view.
_CONFIDENT_METHODS = {"exact", "alias", "fuzzy"}


def _has_active_prices(
    session: Session, service_id: int, city: str | None = None
) -> bool:
    filters = [
        ClinicServicePrice.service_id == service_id,
        ClinicServicePrice.is_active.is_(True),
    ]
    if city:
        filters.append(ClinicServicePrice.city == city)
    return bool(
        session.scalar(select(func.count(ClinicServicePrice.id)).where(*filters))
    )


def _suggestion_for(
    session: Session, service_id: int, score: float, city: str | None = None
) -> Suggestion | None:
    svc = session.get(Service, service_id)
    if svc is None:
        return None
    return Suggestion(
        id=svc.id,
        name_ru=svc.name_ru,
        category=svc.category.value,
        specialty=svc.specialty,
        score=round(float(score), 3),
        has_prices=_has_active_prices(session, service_id, city),
    )


def _canonical_service_id(
    session: Session, service_id: int, city: str | None = None
) -> int:
    """Among services sharing this name_ru, the one with the most active prices.

    Duplicate catalog rows (same name, different specialty) fragment prices; resolving
    onto the best-covered sibling avoids landing on an empty duplicate. Prices are not
    merged across siblings — only one service's prices are shown. With `city`, the
    best-covered sibling is judged within that city so the resolved row matches the
    city-scoped price view.
    """
    name = session.scalar(select(Service.name_ru).where(Service.id == service_id))
    if name is None:
        return service_id
    price_join = (ClinicServicePrice.service_id == Service.id) & (
        ClinicServicePrice.is_active.is_(True)
    )
    if city:
        price_join = price_join & (ClinicServicePrice.city == city)
    rows = session.execute(
        select(Service.id, func.count(ClinicServicePrice.id).label("n"))
        .outerjoin(ClinicServicePrice, price_join)
        .where(Service.name_ru == name)
        .group_by(Service.id)
        .order_by(func.count(ClinicServicePrice.id).desc(), Service.id)
    ).all()
    return rows[0][0] if rows else service_id


def cities_with_prices(
    session: Session, service_id: int, *, exclude_city: str | None = None
) -> list[tuple[str, int]]:
    """Cities with active, non-stale prices for a service, busiest first.

    Powers the cross-city hint: when the selected city has no prices, the user is told
    where the service is actually available instead of dead-ending on an empty result.
    """
    now = datetime.now(UTC)
    age_days = func.floor(
        func.extract("epoch", now - ClinicServicePrice.parsed_at) / 86400.0
    )
    count = func.count(ClinicServicePrice.id).label("n")
    filters = [
        ClinicServicePrice.service_id == service_id,
        ClinicServicePrice.is_active.is_(True),
        ClinicServicePrice.city.is_not(None),
        age_days <= STALE_DAYS,
    ]
    if exclude_city:
        filters.append(ClinicServicePrice.city != exclude_city)
    rows = session.execute(
        select(ClinicServicePrice.city, count)
        .where(*filters)
        .group_by(ClinicServicePrice.city)
        .order_by(count.desc(), ClinicServicePrice.city)
    ).all()
    return [(city, int(n)) for city, n in rows]


def _priced_fallback(q: str, suggestions: list[Suggestion]) -> Suggestion | None:
    """Best priced suggestion whose name contains every token of the query.

    When the lexical match lands on a catalog row that carries no prices (e.g. a bare
    "ЭКГ" entry that nothing was scraped against), the real prices often live on a
    longer relative — "Суточное мониторирование ЭКГ (по Холтеру)". Resolving to that
    priced relative beats a dead-end empty page. The whole-token requirement keeps it
    honest (§9): the user's full concept must appear as words in the candidate name, so
    we never drift to a loosely-fuzzy service.
    """
    q_tokens = set(canonical_clean(q).split())
    if not q_tokens:
        return None
    for s in suggestions:
        if s.has_prices and q_tokens <= set(canonical_clean(s.name_ru).split()):
            return s
    return None


def resolve_query(
    session: Session,
    q: str,
    category: str | None = None,
    embedder=_USE_DEFAULT_EMBEDDER,
    city: str | None = None,
) -> tuple[Suggestion | None, list[Suggestion]]:
    """Resolve a typed query to the best catalog service plus alternatives.

    Lexical exact/alias/fuzzy matches resolve directly. A semantic (embedding) hit is
    only ever offered as a *suggestion*, never silently resolved — generic embeddings
    can't reliably separate near-identical lab analytes, so a human confirms (§9).
    Below the lexical floor we resolve nothing and return "did you mean" suggestions.
    When the resolved row has no prices, fall back to a priced relative (see
    `_priced_fallback`) so an exact-but-empty catalog entry doesn't dead-end the search.
    """
    if embedder is _USE_DEFAULT_EMBEDDER:
        embedder = get_embedder()

    suggestions = autocomplete(session, q, limit=8, category=category, city=city)
    result = ServiceMatcher(session, embedder=embedder).match(q)

    resolved: Suggestion | None = None
    if result.service_id is not None and result.method in _CONFIDENT_METHODS:
        sid = _canonical_service_id(session, result.service_id, city)
        candidate = _suggestion_for(session, sid, result.confidence, city)
        if candidate is not None and not (category and candidate.category != category):
            resolved = candidate

    if result.method == "semantic" and result.service_id is not None:
        semantic = _suggestion_for(session, result.service_id, result.confidence, city)
        if semantic is not None and (not category or semantic.category == category):
            suggestions = [semantic] + [s for s in suggestions if s.id != semantic.id]

    if resolved is None or not resolved.has_prices:
        fallback = _priced_fallback(q, suggestions)
        if fallback is not None:
            resolved = fallback

    return resolved, suggestions


def _nearest_point(points, lat: float | None, lng: float | None):
    """The branch nearest the user, or a deterministic one when location is unknown."""
    if lat is None or lng is None:
        return min(points, key=lambda b: b.id)
    return min(points, key=lambda b: (b.lat - lat) ** 2 + (b.lng - lng) ** 2)


def prices_for_service(
    session: Session,
    service_id: int,
    *,
    city: str | None = None,
    sort: str = "best_value",
    include_stale: bool = False,
    price_min: int | None = None,
    price_max: int | None = None,
    lat: float | None = None,
    lng: float | None = None,
    source_category: str | None = None,
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
            Doctor,
        )
        .join(Clinic, ClinicServicePrice.clinic_id == Clinic.id)
        .join(Service, ClinicServicePrice.service_id == Service.id)
        .outerjoin(ClinicBranch, ClinicServicePrice.branch_id == ClinicBranch.id)
        .outerjoin(RawPriceItem, ClinicServicePrice.raw_price_item_id == RawPriceItem.id)
        .outerjoin(Doctor, ClinicServicePrice.doctor_id == Doctor.id)
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
    if source_category:
        stmt = stmt.where(ClinicServicePrice.source_category == source_category)
    if not include_stale:
        stmt = stmt.where(age_days <= STALE_DAYS)

    cards: list[PriceCard] = []
    for price, clinic, branch, service, metadata, age, doctor in session.execute(stmt):
        if branch is not None:
            cards.append(
                _build_card(price, clinic, branch, service, metadata, int(age), doctor=doctor)
            )
            continue
        # City-wide price (no branch): one card per clinic, bound to its nearest collection
        # point so the card carries real coords for distance, routing, and list<->map sync.
        points = session.scalars(
            select(ClinicBranch).where(
                ClinicBranch.clinic_id == clinic.id,
                ClinicBranch.city == (city or price.city),
                ClinicBranch.lat.is_not(None),
                ClinicBranch.lng.is_not(None),
            )
        ).all()
        if not points:
            cards.append(
                _build_card(
                    price, clinic, None, service, metadata, int(age),
                    doctor=doctor, branch_count=0,
                )
            )
            continue
        chosen = _nearest_point(points, lat, lng)
        cards.append(
            _build_card(
                price, clinic, chosen, service, metadata, int(age),
                doctor=doctor, branch_count=len(points),
            )
        )
    return _sort_cards(cards, sort)


def prices_for_doctor(
    session: Session, doctor_id: int, *, include_stale: bool = False
) -> list[PriceCard]:
    """All active services this doctor offers, as price cards (for the doctor page)."""
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
            Doctor,
        )
        .join(Clinic, ClinicServicePrice.clinic_id == Clinic.id)
        .join(Service, ClinicServicePrice.service_id == Service.id)
        .outerjoin(ClinicBranch, ClinicServicePrice.branch_id == ClinicBranch.id)
        .outerjoin(RawPriceItem, ClinicServicePrice.raw_price_item_id == RawPriceItem.id)
        .outerjoin(Doctor, ClinicServicePrice.doctor_id == Doctor.id)
        .where(
            ClinicServicePrice.doctor_id == doctor_id,
            ClinicServicePrice.is_active.is_(True),
        )
    )
    if not include_stale:
        stmt = stmt.where(age_days <= STALE_DAYS)

    cards = [
        _build_card(price, clinic, branch, service, metadata, int(age), doctor=doctor)
        for price, clinic, branch, service, metadata, age, doctor in session.execute(stmt)
    ]
    return _sort_cards(cards, "cheapest")


def _doctor_name(metadata: dict | None) -> str | None:
    name = (metadata or {}).get("doctor")
    return name.strip() if isinstance(name, str) and name.strip() else None


def _as_int(value: object) -> int | None:
    return int(value) if isinstance(value, (int, float)) else None


def _as_str(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _rating(value: object) -> float | None:
    return round(float(value), 1) if isinstance(value, (int, float)) else None


def _build_card(
    price: ClinicServicePrice,
    clinic: Clinic,
    branch: ClinicBranch | None,
    service: Service,
    metadata: dict | None,
    age_days: int,
    branch_count: int = 1,
    doctor: Doctor | None = None,
) -> PriceCard:
    meta = metadata or {}
    # The enriched `doctors` table is the source of truth for photo/rating/experience;
    # the price's raw metadata is only a fallback (it rarely carries an avatar).
    return PriceCard(
        price_id=price.id,
        service_id=service.id,
        service_name=service.name_ru,
        clinic_id=clinic.id,
        clinic_name=clinic.name,
        doctor_name=_doctor_name(metadata) or (doctor.name if doctor else None),
        doctor_id=doctor.id if doctor else _as_int(meta.get("doctor_id")),
        doctor_avatar=(doctor.avatar_url if doctor else None) or _as_str(meta.get("doctor_avatar")),
        doctor_experience=(doctor.experience_years if doctor else None)
        if (doctor and doctor.experience_years is not None)
        else _as_int(meta.get("doctor_experience")),
        doctor_rating=_rating(doctor.rating)
        if (doctor and doctor.rating is not None)
        else _rating(meta.get("doctor_rating")),
        doctor_reviews=(doctor.review_count if doctor else None)
        if (doctor and doctor.review_count is not None)
        else _as_int(meta.get("doctor_reviews")),
        qualification=_as_str(meta.get("qualification")),
        district=_as_str(meta.get("district")),
        base_price_kzt=_as_int(meta.get("base_price")),
        discount_percent=_as_int(meta.get("discount_percent")),
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
        source_category=price.source_category,
        content_hash=price.content_hash,
        match_confidence=price.match_confidence,
        match_method=price.match_method,
        rating=branch.rating if branch else None,
        reviews_count=branch.reviews_count if branch else None,
        branch_count=branch_count,
    )


def featured_cards(session: Session, limit: int = 6) -> list[PriceCard]:
    """Recognizable services for the landing page: the most widely-offered
    (multi-clinic) services, one cheapest fresh card each. DB-only (Rule 1)."""
    now = datetime.now(UTC)
    age_days = func.floor(
        func.extract("epoch", now - ClinicServicePrice.parsed_at) / 86400.0
    ).cast(Float)

    popular = (
        select(
            ClinicServicePrice.service_id,
            func.count(func.distinct(ClinicServicePrice.clinic_id)).label("clinics"),
        )
        .where(ClinicServicePrice.is_active.is_(True), age_days <= STALE_DAYS)
        .group_by(ClinicServicePrice.service_id)
        .order_by(desc("clinics"))
        .limit(limit)
    )
    ranked = {row.service_id: i for i, row in enumerate(session.execute(popular))}
    if not ranked:
        return []

    # DISTINCT ON (service_id) ordered by price → cheapest fresh card per service.
    stmt = (
        select(
            ClinicServicePrice,
            Clinic,
            ClinicBranch,
            Service,
            RawPriceItem.metadata_json,
            age_days.label("age"),
            Doctor,
        )
        .join(Clinic, ClinicServicePrice.clinic_id == Clinic.id)
        .join(Service, ClinicServicePrice.service_id == Service.id)
        .outerjoin(ClinicBranch, ClinicServicePrice.branch_id == ClinicBranch.id)
        .outerjoin(RawPriceItem, ClinicServicePrice.raw_price_item_id == RawPriceItem.id)
        .outerjoin(Doctor, ClinicServicePrice.doctor_id == Doctor.id)
        .where(
            ClinicServicePrice.is_active.is_(True),
            age_days <= STALE_DAYS,
            ClinicServicePrice.service_id.in_(ranked.keys()),
            Service.category.not_in(HIDDEN_CATEGORIES),
        )
        .order_by(
            ClinicServicePrice.service_id,
            ClinicServicePrice.price_kzt.asc(),
            ClinicServicePrice.id.desc(),
        )
        .distinct(ClinicServicePrice.service_id)
    )

    cards = [
        _build_card(price, clinic, branch, service, metadata, int(age), doctor=doctor)
        for price, clinic, branch, service, metadata, age, doctor in session.execute(stmt)
    ]
    cards.sort(key=lambda c: ranked.get(c.service_id, len(ranked)))
    return cards


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
