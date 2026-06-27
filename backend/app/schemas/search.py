from datetime import datetime

from pydantic import BaseModel, ConfigDict


class Suggestion(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name_ru: str
    category: str
    specialty: str | None
    score: float
    has_prices: bool


class PriceCard(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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
    freshness: str
    source_url: str
    service_name_raw: str | None
    content_hash: str | None
    match_confidence: float
    match_method: str | None


class SearchResponse(BaseModel):
    query: str
    resolved_service: Suggestion | None
    suggestions: list[Suggestion]
    cards: list[PriceCard]
    count: int


class CityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    lat: float
    lng: float


class MapPin(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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
