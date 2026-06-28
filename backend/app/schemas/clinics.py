from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BranchInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    city: str | None
    address: str | None
    lat: float | None
    lng: float | None
    phone: str | None
    working_hours: str | None
    rating: float | None = None
    reviews_count: int | None = None


class ClinicDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    website_url: str | None
    source_name: str
    rating: float | None = None
    reviews_count: int = 0
    branches: list[BranchInfo]


class ReviewRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    author: str | None
    rating: int | None
    text: str | None
    official_answer: str | None
    review_date: datetime | None
    source: str
    branch_id: int
    city: str | None


class ClinicServiceRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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


class CompareRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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


class CompareResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    service_id: int
    service_name: str
    rows: list[CompareRow]
