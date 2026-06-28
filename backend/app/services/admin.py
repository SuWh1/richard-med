from datetime import UTC, datetime, timedelta

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import (
    Clinic,
    ClinicBranch,
    ClinicServicePrice,
    ParseRun,
    RawDocument,
    RawPriceItem,
    Service,
    ServiceAlias,
    ServiceCategory,
    UnmatchedService,
)
from app.schemas.admin import (
    CatalogPage,
    CatalogServiceRow,
    ParsedPriceSample,
    ParseRunDetail,
    ParseRunSummary,
    SourceHealth,
    UnmatchedPage,
    UnmatchedRow,
)
from app.scrapers.registry import available_sources

FRESH_DAYS = 7
STALE_DAYS = 30


def _aware(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def _age_days(parsed_at: datetime, now: datetime) -> int:
    return max(0, (now - _aware(parsed_at)).days)


def _freshness(age_days: int) -> str:
    if age_days <= FRESH_DAYS:
        return "fresh"
    if age_days <= STALE_DAYS:
        return "recent"
    return "stale"


def _summary(run: ParseRun) -> ParseRunSummary:
    started = _aware(run.started_at)
    finished = _aware(run.finished_at)
    duration = (finished - started).total_seconds() if finished and started else None
    return ParseRunSummary(
        id=run.id,
        source_name=run.source_name,
        city=run.city,
        status=run.status,
        started_at=run.started_at,
        finished_at=run.finished_at,
        duration_sec=round(duration, 1) if duration is not None else None,
        items_found=run.items_found,
        items_saved=run.items_saved,
        has_errors=bool(run.errors),
    )


def source_health(session: Session) -> list[SourceHealth]:
    now = datetime.now(UTC)
    week_ago = now - timedelta(days=7)
    out: list[SourceHealth] = []

    for source in available_sources():
        runs = session.scalars(
            select(ParseRun)
            .where(ParseRun.source_name == source)
            .order_by(ParseRun.started_at.desc())
        ).all()
        last = runs[0] if runs else None
        last_success = next((r for r in runs if r.status == "success"), None)
        recent = [r for r in runs if _aware(r.started_at) >= week_ago]
        ok = sum(1 for r in recent if r.status in ("success", "partial"))
        rate = ok / len(recent) if recent else 0.0

        clinic_ids = session.scalars(
            select(Clinic.id).where(Clinic.source_name == source)
        ).all()
        active = stale = 0
        if clinic_ids:
            prices = session.scalars(
                select(ClinicServicePrice).where(
                    ClinicServicePrice.clinic_id.in_(clinic_ids),
                    ClinicServicePrice.is_active.is_(True),
                )
            ).all()
            active = len(prices)
            stale = sum(1 for p in prices if _age_days(p.parsed_at, now) > STALE_DAYS)

        out.append(
            SourceHealth(
                source_name=source,
                last_run_at=last.started_at if last else None,
                last_success_at=last_success.started_at if last_success else None,
                last_status=last.status if last else None,
                success_rate_7d=round(rate, 2),
                runs_7d=len(recent),
                items_found_last=last.items_found if last else 0,
                items_saved_last=last.items_saved if last else 0,
                active_prices=active,
                stale_prices=stale,
                last_error=last.errors if last and last.errors else None,
            )
        )
    return out


def catalog_services(
    session: Session,
    q: str | None = None,
    category: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> CatalogPage:
    """Live view of the catalog: each service with its alias + active-price counts.

    `origin` distinguishes seeded/imported entries from ones the pipeline grew from
    real source data (their `service_key` is hashed with an `auto-` prefix)."""
    alias_counts = (
        select(ServiceAlias.service_id, func.count().label("n"))
        .group_by(ServiceAlias.service_id)
        .subquery()
    )
    price_counts = (
        select(ClinicServicePrice.service_id, func.count().label("n"))
        .where(ClinicServicePrice.is_active.is_(True))
        .group_by(ClinicServicePrice.service_id)
        .subquery()
    )

    filters = []
    if q:
        filters.append(Service.name_ru.ilike(f"%{q.strip()}%"))
    if category:
        try:
            filters.append(Service.category == ServiceCategory(category))
        except ValueError:
            pass  # unknown category → no extra filter, the table just shows everything

    total = session.scalar(
        select(func.count()).select_from(Service).where(*filters)
    )

    rows = session.execute(
        select(
            Service.id,
            Service.name_ru,
            Service.category,
            Service.service_key,
            func.coalesce(alias_counts.c.n, 0),
            func.coalesce(price_counts.c.n, 0),
        )
        .outerjoin(alias_counts, alias_counts.c.service_id == Service.id)
        .outerjoin(price_counts, price_counts.c.service_id == Service.id)
        .where(*filters)
        .order_by(func.coalesce(price_counts.c.n, 0).desc(), Service.name_ru)
        .limit(limit)
        .offset(offset)
    ).all()

    items = [
        CatalogServiceRow(
            id=sid,
            name_ru=name,
            category=cat.value,
            origin="auto" if key.startswith("auto-") else "catalog",
            alias_count=aliases,
            price_count=prices,
        )
        for sid, name, cat, key, aliases, prices in rows
    ]
    return CatalogPage(total=total or 0, items=items)


def unmatched_queue(
    session: Session,
    status: str = "pending",
    q: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> UnmatchedPage:
    """The review queue: raw scraped names paired with their best catalog candidate.

    These are the gray-zone matches the pipeline refused to auto-apply — an operator
    (or the AI verifier) decides alias-vs-new. Highest confidence first.

    `q` searches the whole queue (server-side, not just the current page) across both
    the raw source name and the suggested catalog candidate, case-insensitively."""
    filters = []
    if status:
        filters.append(UnmatchedService.status == status)
    if q and q.strip():
        needle = f"%{q.strip()}%"
        filters.append(
            or_(
                UnmatchedService.raw_name.ilike(needle),
                Service.name_ru.ilike(needle),
            )
        )

    total = session.scalar(
        select(func.count())
        .select_from(UnmatchedService)
        .outerjoin(Service, Service.id == UnmatchedService.suggested_service_id)
        .where(*filters)
    )

    rows = session.execute(
        select(UnmatchedService, Service.name_ru, Service.category)
        .outerjoin(Service, Service.id == UnmatchedService.suggested_service_id)
        .where(*filters)
        .order_by(UnmatchedService.confidence.desc(), UnmatchedService.id)
        .limit(limit)
        .offset(offset)
    ).all()

    items = [
        UnmatchedRow(
            id=u.id,
            raw_name=u.raw_name,
            suggested_name=name,
            suggested_category=cat.value if cat else None,
            confidence=u.confidence,
            status=u.status,
        )
        for u, name, cat in rows
    ]
    return UnmatchedPage(total=total or 0, items=items)


def list_runs(session: Session, limit: int = 20) -> list[ParseRunSummary]:
    runs = session.scalars(
        select(ParseRun).order_by(ParseRun.started_at.desc()).limit(limit)
    ).all()
    return [_summary(r) for r in runs]


def run_detail(session: Session, run_id: int) -> ParseRunDetail | None:
    run = session.get(ParseRun, run_id)
    if run is None:
        return None
    now = datetime.now(UTC)
    errors = run.errors.split("\n") if run.errors else []

    unmatched_q = (
        select(UnmatchedService.raw_name)
        .join(RawPriceItem, UnmatchedService.raw_item_id == RawPriceItem.id)
        .join(RawDocument, RawPriceItem.raw_document_id == RawDocument.id)
        .where(RawDocument.source_name == run.source_name)
    )
    unmatched_names = session.scalars(unmatched_q).all()

    rows = session.execute(
        select(ClinicServicePrice, Service, Clinic, ClinicBranch)
        .join(Service, ClinicServicePrice.service_id == Service.id)
        .join(Clinic, ClinicServicePrice.clinic_id == Clinic.id)
        .join(ClinicBranch, ClinicServicePrice.branch_id == ClinicBranch.id, isouter=True)
        .where(
            Clinic.source_name == run.source_name,
            ClinicServicePrice.is_active.is_(True),
        )
        .order_by(ClinicServicePrice.parsed_at.desc())
        .limit(15)
    ).all()

    samples = []
    for price, service, clinic, branch in rows:
        age = _age_days(price.parsed_at, now)
        samples.append(
            ParsedPriceSample(
                service_name=service.name_ru,
                service_name_raw=price.service_name_raw,
                clinic_name=clinic.name,
                city=branch.city if branch else None,
                price_kzt=price.price_kzt,
                match_confidence=price.match_confidence,
                match_method=price.match_method,
                age_days=age,
                freshness=_freshness(age),
                source_url=price.source_url,
            )
        )

    return ParseRunDetail(
        run=_summary(run),
        errors=errors,
        unmatched_count=len(unmatched_names),
        unmatched_samples=list(unmatched_names[:10]),
        price_samples=samples,
    )
