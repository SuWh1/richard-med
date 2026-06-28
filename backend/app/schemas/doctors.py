from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.search import PriceCard


class DoctorDetailItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    detail_type: str
    detail_type_id: int | None
    info: str
    year: str | None


class DoctorReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    score: float | None
    text: str | None
    text_ru: str | None
    service_name: str | None
    client_name: str | None
    waiting_time: int | None
    clinic_reply: str | None
    source: str | None
    created_at: datetime | None


class DoctorReviewPage(BaseModel):
    total: int
    items: list[DoctorReviewOut]


class DoctorProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    doq_id: int
    slug: str | None
    name: str
    avatar_url: str | None
    experience_years: int | None
    rating: float | None
    review_count: int | None
    gender: str | None
    languages: list[str] | None
    photos: list[str] | None
    details: list[DoctorDetailItem]
    prices: list[PriceCard]
