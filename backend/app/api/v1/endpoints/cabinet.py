from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.auth import require_user
from app.db.session import get_db
from app.schemas.cabinet import (
    CabinetDashboard,
    SavedServiceCreate,
    SavedServiceUpdate,
    SavedServiceWatch,
    SearchHistoryCreate,
    SearchHistoryItem,
)
from app.services import cabinet

router = APIRouter()


def _user_id(claims: dict) -> int:
    return int(claims["sub"])


@router.get("", response_model=CabinetDashboard)
def get_cabinet(
    claims: dict = Depends(require_user),
    db: Session = Depends(get_db),
) -> CabinetDashboard:
    return cabinet.dashboard(db, _user_id(claims))


@router.post("/saved-services", response_model=SavedServiceWatch)
def save_service(
    body: SavedServiceCreate,
    claims: dict = Depends(require_user),
    db: Session = Depends(get_db),
) -> SavedServiceWatch:
    watch = cabinet.save_service(db, _user_id(claims), body)
    if watch is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Услуга не найдена")
    return watch


@router.patch("/saved-services/{watch_id}", response_model=SavedServiceWatch)
def update_saved_service(
    watch_id: int,
    body: SavedServiceUpdate,
    claims: dict = Depends(require_user),
    db: Session = Depends(get_db),
) -> SavedServiceWatch:
    watch = cabinet.set_notify(db, _user_id(claims), watch_id, body.notify_enabled)
    if watch is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Сохранённая услуга не найдена")
    return watch


@router.post("/saved-services/{watch_id}/mark-seen", response_model=SavedServiceWatch)
def mark_saved_service_seen(
    watch_id: int,
    claims: dict = Depends(require_user),
    db: Session = Depends(get_db),
) -> SavedServiceWatch:
    watch = cabinet.mark_seen(db, _user_id(claims), watch_id)
    if watch is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Сохранённая услуга не найдена")
    return watch


@router.delete("/saved-services/{watch_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_saved_service(
    watch_id: int,
    claims: dict = Depends(require_user),
    db: Session = Depends(get_db),
) -> Response:
    if not cabinet.delete_watch(db, _user_id(claims), watch_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Сохранённая услуга не найдена")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/search-history", response_model=SearchHistoryItem)
def record_search_history(
    body: SearchHistoryCreate,
    claims: dict = Depends(require_user),
    db: Session = Depends(get_db),
) -> SearchHistoryItem:
    if len(body.q.strip()) < 2 or not body.city.strip():
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Некорректный запрос")
    return cabinet.record_search(db, _user_id(claims), body)
