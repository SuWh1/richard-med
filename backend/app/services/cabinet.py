from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    Clinic,
    ClinicServicePrice,
    Service,
    UserSavedService,
    UserSearchHistory,
)
from app.schemas.cabinet import (
    CabinetDashboard,
    PriceNotification,
    SavedServiceCreate,
    SavedServiceWatch,
    SearchHistoryCreate,
    SearchHistoryItem,
)
from app.services.search import STALE_DAYS

HISTORY_DEDUPE_MINUTES = 15


def _fresh_cutoff() -> datetime:
    return datetime.now(UTC) - timedelta(days=STALE_DAYS)


def current_price_stats(
    session: Session, service_id: int, city: str
) -> tuple[int | None, int]:
    row = session.execute(
        select(
            func.min(ClinicServicePrice.price_kzt),
            func.count(func.distinct(ClinicServicePrice.clinic_id)),
        ).where(
            ClinicServicePrice.service_id == service_id,
            ClinicServicePrice.city == city,
            ClinicServicePrice.is_active.is_(True),
            ClinicServicePrice.parsed_at >= _fresh_cutoff(),
        )
    ).one()
    return row[0], int(row[1] or 0)


def clinic_price(
    session: Session, service_id: int, clinic_id: int, city: str
) -> int | None:
    return session.scalar(
        select(func.min(ClinicServicePrice.price_kzt)).where(
            ClinicServicePrice.service_id == service_id,
            ClinicServicePrice.clinic_id == clinic_id,
            ClinicServicePrice.city == city,
            ClinicServicePrice.is_active.is_(True),
            ClinicServicePrice.parsed_at >= _fresh_cutoff(),
        )
    )


def _tracked_price(
    session: Session, service_id: int, clinic_id: int | None, city: str
) -> int | None:
    """The price a watch tracks: the saved clinic's price, or the city-wide cheapest."""
    if clinic_id is not None:
        return clinic_price(session, service_id, clinic_id, city)
    price, _ = current_price_stats(session, service_id, city)
    return price


def _watch_out(
    session: Session, watch: UserSavedService, service: Service
) -> SavedServiceWatch:
    current = _tracked_price(session, watch.service_id, watch.clinic_id, watch.city)
    _, clinic_count = current_price_stats(session, watch.service_id, watch.city)
    clinic = session.get(Clinic, watch.clinic_id) if watch.clinic_id else None
    return SavedServiceWatch(
        id=watch.id,
        service_id=watch.service_id,
        service_name=service.name_ru,
        category=service.category.value,
        clinic_id=watch.clinic_id,
        clinic_name=clinic.name if clinic else None,
        city=watch.city,
        notify_enabled=watch.notify_enabled,
        baseline_min_price=watch.baseline_min_price,
        last_seen_min_price=watch.last_seen_min_price,
        current_min_price=current,
        clinic_count=clinic_count,
        updated_at=watch.updated_at,
    )


def _notification(watch: SavedServiceWatch) -> PriceNotification | None:
    previous = watch.last_seen_min_price
    current = watch.current_min_price
    if not watch.notify_enabled or previous is None or current is None or previous == current:
        return None
    delta = current - previous
    return PriceNotification(
        watch_id=watch.id,
        service_id=watch.service_id,
        service_name=watch.service_name,
        city=watch.city,
        previous_min_price=previous,
        current_min_price=current,
        delta_kzt=delta,
        delta_pct=round((delta / previous) * 100, 1) if previous else 0.0,
    )


def dashboard(session: Session, user_id: int) -> CabinetDashboard:
    watch_rows = session.execute(
        select(UserSavedService, Service)
        .join(Service, UserSavedService.service_id == Service.id)
        .where(UserSavedService.user_id == user_id)
        .order_by(UserSavedService.updated_at.desc(), UserSavedService.id.desc())
    ).all()
    saved = [_watch_out(session, watch, service) for watch, service in watch_rows]
    notifications = [n for watch in saved if (n := _notification(watch)) is not None]

    history_rows = session.execute(
        select(UserSearchHistory, Service)
        .outerjoin(Service, UserSearchHistory.service_id == Service.id)
        .where(UserSearchHistory.user_id == user_id)
        .order_by(UserSearchHistory.created_at.desc(), UserSearchHistory.id.desc())
        .limit(10)
    ).all()
    recent = [
        SearchHistoryItem(
            id=item.id,
            q=item.q,
            city=item.city,
            service_id=item.service_id,
            service_name=service.name_ru if service else None,
            result_count=item.result_count,
            created_at=item.created_at,
        )
        for item, service in history_rows
    ]
    return CabinetDashboard(
        saved_services=saved,
        recent_searches=recent,
        notifications=notifications,
    )


def save_service(
    session: Session, user_id: int, body: SavedServiceCreate
) -> SavedServiceWatch | None:
    service = session.get(Service, body.service_id)
    if service is None:
        return None
    if body.clinic_id is not None and session.get(Clinic, body.clinic_id) is None:
        return None

    city = body.city.strip()
    if not city:
        return None

    existing = session.scalar(
        select(UserSavedService).where(
            UserSavedService.user_id == user_id,
            UserSavedService.service_id == body.service_id,
            UserSavedService.clinic_id.is_(body.clinic_id)
            if body.clinic_id is None
            else UserSavedService.clinic_id == body.clinic_id,
            UserSavedService.city == city,
        )
    )
    current = _tracked_price(session, body.service_id, body.clinic_id, city)
    now = datetime.now(UTC)
    if existing is None:
        existing = UserSavedService(
            user_id=user_id,
            service_id=body.service_id,
            clinic_id=body.clinic_id,
            city=city,
            notify_enabled=body.notify_enabled,
            baseline_min_price=current,
            last_seen_min_price=current,
            created_at=now,
            updated_at=now,
        )
        session.add(existing)
    else:
        existing.notify_enabled = body.notify_enabled
        existing.updated_at = now
        if existing.baseline_min_price is None:
            existing.baseline_min_price = current
        if existing.last_seen_min_price is None:
            existing.last_seen_min_price = current

    session.commit()
    session.refresh(existing)
    return _watch_out(session, existing, service)


def set_notify(
    session: Session, user_id: int, watch_id: int, notify_enabled: bool
) -> SavedServiceWatch | None:
    watch = _watch_for_user(session, user_id, watch_id)
    if watch is None:
        return None
    service = session.get(Service, watch.service_id)
    if service is None:
        return None
    watch.notify_enabled = notify_enabled
    watch.updated_at = datetime.now(UTC)
    session.commit()
    session.refresh(watch)
    return _watch_out(session, watch, service)


def mark_seen(session: Session, user_id: int, watch_id: int) -> SavedServiceWatch | None:
    watch = _watch_for_user(session, user_id, watch_id)
    if watch is None:
        return None
    service = session.get(Service, watch.service_id)
    if service is None:
        return None
    watch.last_seen_min_price = _tracked_price(
        session, watch.service_id, watch.clinic_id, watch.city
    )
    watch.updated_at = datetime.now(UTC)
    session.commit()
    session.refresh(watch)
    return _watch_out(session, watch, service)


def delete_watch(session: Session, user_id: int, watch_id: int) -> bool:
    watch = _watch_for_user(session, user_id, watch_id)
    if watch is None:
        return False
    session.delete(watch)
    session.commit()
    return True


def record_search(
    session: Session, user_id: int, body: SearchHistoryCreate
) -> SearchHistoryItem:
    q = body.q.strip()
    city = body.city.strip()
    service = session.get(Service, body.service_id) if body.service_id else None
    cutoff = datetime.now(UTC) - timedelta(minutes=HISTORY_DEDUPE_MINUTES)
    existing = session.scalar(
        select(UserSearchHistory)
        .where(
            UserSearchHistory.user_id == user_id,
            func.lower(UserSearchHistory.q) == q.lower(),
            UserSearchHistory.city == city,
            UserSearchHistory.service_id.is_(body.service_id)
            if body.service_id is None
            else UserSearchHistory.service_id == body.service_id,
            UserSearchHistory.created_at >= cutoff,
        )
        .order_by(UserSearchHistory.created_at.desc())
    )

    if existing is None:
        existing = UserSearchHistory(
            user_id=user_id,
            q=q,
            city=city,
            service_id=body.service_id,
            result_count=body.result_count,
            created_at=datetime.now(UTC),
        )
        session.add(existing)
    else:
        existing.result_count = body.result_count
        existing.created_at = datetime.now(UTC)
    session.commit()
    session.refresh(existing)

    return SearchHistoryItem(
        id=existing.id,
        q=existing.q,
        city=existing.city,
        service_id=existing.service_id,
        service_name=service.name_ru if service else None,
        result_count=existing.result_count,
        created_at=existing.created_at,
    )


def _watch_for_user(
    session: Session, user_id: int, watch_id: int
) -> UserSavedService | None:
    return session.scalar(
        select(UserSavedService).where(
            UserSavedService.id == watch_id,
            UserSavedService.user_id == user_id,
        )
    )
