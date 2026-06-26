from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class ScrapedPrice:
    """One raw price row as extracted from a source, before normalization."""

    source: str
    source_url: str
    clinic_name: str
    city: str | None
    service_name_raw: str
    price_kzt: float
    currency: str = "KZT"
    duration_days: int | None = None


class BaseScraper(ABC):
    """Pluggable scraper interface — one implementation per source.

    Adding a new source must not require changes to the core pipeline.
    """

    source: str

    @abstractmethod
    def scrape(self) -> list[ScrapedPrice]:
        """Fetch and parse the source, returning raw price rows."""
        raise NotImplementedError
