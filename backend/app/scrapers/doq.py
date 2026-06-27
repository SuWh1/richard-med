import json
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

from app.scrapers.base import (
    BaseSourceAdapter,
    RawDocument,
    RawPriceItem,
    SnapshotResult,
)
from app.scrapers.http import PoliteClient, content_hash

API_URL = "https://api.doq.kz/api/v1/doctors/"
_FIXTURE = (
    Path(__file__).resolve().parents[2]
    / "tests"
    / "fixtures"
    / "doq_doctors_terapevt_astana.json"
)

_CITY_IDS = {"Астана": 1, "Алматы": 3}

# DOQ aggregates many clinics; a doctor visit price lives per (doctor, service, branch).
# We scrape a curated set of common specializations rather than the full 1000+ catalog.
SPECIALIZATIONS = {
    97: "Терапевт",
    178: "Педиатр",
    20: "Гинеколог",
    84: "Невролог",
    26: "Кардиолог",
    9: "Эндокринолог",
    52: "Уролог",
    6: "Дерматолог",
    85: "Офтальмолог",
}

_PAGE_SIZE = 50
_MAX_PAGES = 4


def _query_url(city_id: int, service_id: int, *, limit: int = _PAGE_SIZE, offset: int = 0) -> str:
    params = {
        "city": city_id,
        "service": service_id,
        "expand": "services,clinic_branches",
        "limit": limit,
        "offset": offset,
    }
    return f"{API_URL}?{urlencode(params)}"


def _target_service_id(source_url: str) -> int | None:
    values = parse_qs(urlparse(source_url).query).get("service")
    return int(values[0]) if values else None


class DoqAdapter(BaseSourceAdapter):
    """DOQ doctor-visit prices via its JSON API. Each doctor's `services[]` carries
    base/discount price and a `clinic_branch` resolved from the expanded branch list."""

    def __init__(self, client: PoliteClient | None = None):
        self._client = client

    def identity(self) -> str:
        return "doq"

    def fetch(self, city: str) -> list[RawDocument]:
        city_id = _CITY_IDS.get(city)
        if city_id is None:
            return []
        client = self._client or PoliteClient()
        docs: list[RawDocument] = []
        try:
            for service_id in SPECIALIZATIONS:
                for page in range(_MAX_PAGES):
                    url = _query_url(city_id, service_id, offset=page * _PAGE_SIZE)
                    response = client.get(url)
                    text = response.text
                    docs.append(
                        RawDocument(
                            source_name=self.identity(),
                            source_url=url,
                            city=city,
                            raw_html=text,
                            content_hash=content_hash(text),
                            status_code=response.status_code,
                            fetched_at="",
                        )
                    )
                    if response.json().get("next") is None:
                        break
        finally:
            if self._client is None:
                client.close()
        return docs

    def parse(self, raw_doc: RawDocument) -> list[RawPriceItem]:
        target = _target_service_id(raw_doc.source_url)
        payload = json.loads(raw_doc.raw_html)
        items: list[RawPriceItem] = []
        for doctor in payload.get("results", []):
            branches = {b["id"]: b for b in doctor.get("clinic_branches", [])}
            for svc in doctor.get("services", []):
                service = svc.get("service") or {}
                if target is not None and service.get("id") != target:
                    continue
                branch = branches.get(svc.get("clinic_branch"))
                if branch is None:
                    continue
                price = svc.get("discount_price") or svc.get("base_price")
                if not price:
                    continue
                location = branch.get("location") or {}
                phones = branch.get("phones") or []
                items.append(
                    RawPriceItem(
                        source_url=f"https://doq.kz/doctors/{doctor.get('slug', '')}",
                        clinic_raw=branch.get("name"),
                        service_name_raw=service.get("name", ""),
                        price_raw=str(price),
                        metadata={
                            "specialization": SPECIALIZATIONS.get(target),
                            "doctor": doctor.get("name"),
                            "city": raw_doc.city,
                            "address": branch.get("address"),
                            "lat": location.get("lat"),
                            "lng": location.get("lng"),
                            "phone": phones[0] if phones else None,
                        },
                    )
                )
        return items

    def clean(self, raw_item: RawPriceItem) -> RawPriceItem:
        digits = "".join(ch for ch in (raw_item.price_raw or "") if ch.isdigit())
        return RawPriceItem(
            source_url=raw_item.source_url,
            clinic_raw=(raw_item.clinic_raw or "").strip() or None,
            service_name_raw=" ".join((raw_item.service_name_raw or "").split()),
            price_raw=digits,
            duration_raw=raw_item.duration_raw,
            metadata=raw_item.metadata,
        )

    def test_snapshot(self) -> SnapshotResult:
        text = _FIXTURE.read_text(encoding="utf-8")
        doc = RawDocument(
            source_name=self.identity(),
            source_url=_query_url(1, 97),
            city="Астана",
            raw_html=text,
            content_hash=content_hash(text),
            status_code=200,
            fetched_at="",
        )
        items = [self.clean(item) for item in self.parse(doc)]
        return SnapshotResult(item_count=len(items), sample_items=items[:3])
