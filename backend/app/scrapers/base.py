from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass(frozen=True)
class RawDocument:
    """A fetched source page, retained as raw evidence before any parsing."""

    source_name: str
    source_url: str
    city: str | None
    raw_html: str
    content_hash: str
    status_code: int
    fetched_at: str


@dataclass(frozen=True)
class RawPriceItem:
    """One price row extracted from a RawDocument, before normalization."""

    source_url: str
    clinic_raw: str
    service_name_raw: str
    price_raw: str
    duration_raw: str | None = None
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class SnapshotResult:
    """Outcome of parsing a saved HTML fixture, for adapter regression tests."""

    item_count: int
    sample_items: list[RawPriceItem]


@dataclass(frozen=True)
class BranchHit:
    """One physical collection point / clinic location, for the map."""

    external_id: str  # stable source id (e.g. KDL cabinet slug) for dedup
    name: str
    city: str
    address: str | None
    lat: float | None
    lng: float | None
    phone: str | None
    working_hours: str | None


class BaseSourceAdapter(ABC):
    """One adapter per source domain. Adding a source must not touch the pipeline.

    The pipeline owns persistence: adapters never write to the DB. `fetch` produces
    raw evidence, `parse` extracts rows from one document, `clean` canonicalizes a row.
    """

    @abstractmethod
    def identity(self) -> str:
        """Stable source name used for Source Health and provenance (e.g. 'kdl_olymp')."""
        raise NotImplementedError

    @abstractmethod
    def fetch(self, city: str) -> list[RawDocument]:
        """Fetch source pages for a city and return them as raw evidence."""
        raise NotImplementedError

    @abstractmethod
    def parse(self, raw_doc: RawDocument) -> list[RawPriceItem]:
        """Extract raw price rows from one document. No DB writes."""
        raise NotImplementedError

    @abstractmethod
    def clean(self, raw_item: RawPriceItem) -> RawPriceItem:
        """Canonicalize a raw row (trim, normalize price/duration) without matching."""
        raise NotImplementedError

    @abstractmethod
    def test_snapshot(self) -> SnapshotResult:
        """Parse a saved HTML fixture and return counts + samples for regression tests."""
        raise NotImplementedError

    def fetch_branches(self, city: str) -> list[BranchHit]:
        """This clinic's physical points in a city. Default: none — override if available."""
        return []

    def brand_name(self) -> str | None:
        """Clinic brand whose branches `fetch_branches` returns; None for multi-clinic sources."""
        return None
