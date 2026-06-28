from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SourcePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    display_name: str
    kind: str
    description: str
    website: str
    clinics: int
    prices: int
    cities: int
    last_parsed_at: datetime | None
    freshness: str | None
