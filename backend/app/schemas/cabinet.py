from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SavedServiceCreate(BaseModel):
    service_id: int
    clinic_id: int | None = None
    city: str
    notify_enabled: bool = True


class SavedServiceUpdate(BaseModel):
    notify_enabled: bool


class SearchHistoryCreate(BaseModel):
    q: str
    city: str
    service_id: int | None = None
    result_count: int = 0


class SavedServiceWatch(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    service_id: int
    service_name: str
    category: str
    clinic_id: int | None
    clinic_name: str | None
    city: str
    notify_enabled: bool
    baseline_min_price: int | None
    last_seen_min_price: int | None
    current_min_price: int | None
    clinic_count: int
    updated_at: datetime


class SearchHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    q: str
    city: str
    service_id: int | None
    service_name: str | None
    result_count: int
    created_at: datetime


class PriceNotification(BaseModel):
    watch_id: int
    service_id: int
    service_name: str
    city: str
    previous_min_price: int
    current_min_price: int
    delta_kzt: int
    delta_pct: float


class CabinetDashboard(BaseModel):
    saved_services: list[SavedServiceWatch]
    recent_searches: list[SearchHistoryItem]
    notifications: list[PriceNotification]
