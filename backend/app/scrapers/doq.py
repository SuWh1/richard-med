import json
import logging
from pathlib import Path
from urllib.parse import urlencode

import httpx

from app.scrapers.base import (
    BaseSourceAdapter,
    RawDocument,
    RawPriceItem,
    SnapshotResult,
)
from app.scrapers.http import PoliteClient, content_hash

logger = logging.getLogger(__name__)

API_URL = "https://api.doq.kz/api/v1/doctors/"
_FIXTURE = (
    Path(__file__).resolve().parents[2]
    / "tests"
    / "fixtures"
    / "doq_doctors_astana.json"
)

# DOQ city IDs (from api.doq.kz/api/v1/cities/), restricted to cities in our canonical
# spine (core/cities.py). DOQ also serves Семей, omitted because it is absent from that
# spine (no map center / KDL coverage). Each city carries genuinely distinct doctors.
_CITY_IDS = {
    "Астана": 1,
    "Алматы": 3,
    "Караганда": 4,
    "Шымкент": 5,
    "Актау": 6,
    "Актобе": 10,
    "Павлодар": 12,
    "Тараз": 13,
    "Кызылорда": 14,
    "Усть-Каменогорск": 15,
    "Кокшетау": 16,
}

# DOQ's full service catalog (~1000 entries) is exposed per doctor: a single sweep of
# every doctor in a city yields each one's `services[]` — appointments *and* procedures
# (УЗИ, рентген, флюорография, ЭКГ, …) — so we no longer crawl a curated specialization
# subset. Each priced offer carries a `clinic_branch` resolved from the expanded list.
_PAGE_SIZE = 100
_MAX_PAGES = 40  # ~2k doctors/city today; cap guards against a runaway loop.

# DOQ tags each catalog service with a coarse type; map it to our category enum so
# procedures aren't filed under doctor visits. Diagnostic vs procedure is then refined
# downstream by service-name keywords (catalog_grow).
_TYPE_CATEGORY = {
    "initial-appointment": "приём врача",
    "procedure": "процедура",
}


def _sweep_url(city_id: int, *, limit: int = _PAGE_SIZE, offset: int = 0) -> str:
    params = {
        "city": city_id,
        "expand": "services,clinic_branches",
        "limit": limit,
        "offset": offset,
    }
    return f"{API_URL}?{urlencode(params)}"


class DoqAdapter(BaseSourceAdapter):
    """DOQ prices via its JSON API. A city sweep returns every doctor with their full
    `services[]` (appointments + procedures); each offer carries base/discount price and
    a `clinic_branch` resolved from the expanded branch list."""

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
            for page in range(_MAX_PAGES):
                url = _sweep_url(city_id, offset=page * _PAGE_SIZE)
                try:
                    response = client.get(url)
                except httpx.HTTPError as exc:
                    # One flaky page must not lose the rest of the sweep: offsets are
                    # deterministic, so skip it and keep paging (Rule: isolate failures).
                    logger.warning(
                        "doq fetch failed for page=%s (%s)", page, type(exc).__name__
                    )
                    continue
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
                payload = response.json()
                if payload.get("next") is None or not payload.get("results"):
                    break
        finally:
            if self._client is None:
                client.close()
        return docs

    def parse(self, raw_doc: RawDocument) -> list[RawPriceItem]:
        payload = json.loads(raw_doc.raw_html)
        items: list[RawPriceItem] = []
        for doctor in payload.get("results", []):
            branches = {b["id"]: b for b in doctor.get("clinic_branches", [])}
            for svc in doctor.get("services", []):
                if not svc.get("is_active", True):
                    continue
                service = svc.get("service") or {}
                name = service.get("name")
                if not name:
                    continue
                branch = branches.get(svc.get("clinic_branch"))
                if branch is None:
                    continue
                price = svc.get("discount_price") or svc.get("base_price")
                if not price:
                    continue
                location = branch.get("location") or {}
                phones = branch.get("phones") or []
                city_area = branch.get("city_area") or {}
                base_price = svc.get("base_price")
                items.append(
                    RawPriceItem(
                        source_url=f"https://doq.kz/doctor/{doctor.get('slug', '')}",
                        clinic_raw=branch.get("name"),
                        service_name_raw=name,
                        price_raw=str(price),
                        metadata={
                            "doq_service_name": name,
                            "doq_type": service.get("type"),
                            "category": _TYPE_CATEGORY.get(service.get("type")),
                            "doctor": doctor.get("name"),
                            "city": raw_doc.city,
                            "address": branch.get("address"),
                            "lat": location.get("lat"),
                            "lng": location.get("lng"),
                            "phone": phones[0] if phones else None,
                            "doctor_id": doctor.get("id"),
                            "doctor_slug": doctor.get("slug"),
                            "doctor_avatar": doctor.get("avatar_url"),
                            "doctor_experience": doctor.get("experience"),
                            "doctor_rating": doctor.get("feedback_score"),
                            "doctor_reviews": doctor.get("feedback_count"),
                            "qualification": svc.get("qualification_display"),
                            "base_price": base_price,
                            "discount_percent": svc.get("discount_percent") or None,
                            "district": city_area.get("name"),
                        },
                    )
                )
        return items

    def default_category(self) -> str | None:
        # DOQ now spans every category; per-row type/keywords decide. No blanket fallback.
        return None

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
            source_url=_sweep_url(1),
            city="Астана",
            raw_html=text,
            content_hash=content_hash(text),
            status_code=200,
            fetched_at="",
        )
        items = [self.clean(item) for item in self.parse(doc)]
        return SnapshotResult(item_count=len(items), sample_items=items[:3])
