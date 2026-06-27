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


class ClinicDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    website_url: str | None
    source_name: str
    branches: list[BranchInfo]


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


class CompareResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    service_id: int
    service_name: str
    rows: list[CompareRow]
