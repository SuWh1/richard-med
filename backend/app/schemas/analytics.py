from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ServicePriceStat(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    service_id: int
    service_name: str
    category: str
    city: str | None
    clinic_count: int
    price_count: int
    min_kzt: int
    max_kzt: int
    avg_kzt: int
    median_kzt: int
    spread_pct: float
    freshest_parsed_at: datetime


class CategoryStat(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    category: str
    service_count: int
    price_count: int
    min_kzt: int
    max_kzt: int
    median_kzt: int


class CityCoverage(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    city: str
    price_count: int
    service_count: int


class AnalyticsOverview(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    city: str | None
    total_prices: int
    total_services: int
    categories: list[CategoryStat]
    cities: list[CityCoverage]
