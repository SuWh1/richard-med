from datetime import datetime

from pydantic import BaseModel


class SourceHealth(BaseModel):
    source_name: str
    last_run_at: datetime | None
    last_success_at: datetime | None
    last_status: str | None
    success_rate_7d: float
    runs_7d: int
    items_found_last: int
    items_saved_last: int
    active_prices: int
    stale_prices: int
    last_error: str | None


class ParseRunSummary(BaseModel):
    id: int
    source_name: str
    city: str | None
    status: str
    started_at: datetime
    finished_at: datetime | None
    duration_sec: float | None
    items_found: int
    items_saved: int
    has_errors: bool


class ParsedPriceSample(BaseModel):
    service_name: str
    service_name_raw: str | None
    clinic_name: str
    city: str | None
    price_kzt: int
    match_confidence: float
    match_method: str | None
    age_days: int
    freshness: str
    source_url: str


class ParseRunDetail(BaseModel):
    run: ParseRunSummary
    errors: list[str]
    unmatched_count: int
    unmatched_samples: list[str]
    price_samples: list[ParsedPriceSample]


class RunTrigger(BaseModel):
    accepted: bool
    source_names: list[str]
    city: str
    message: str
