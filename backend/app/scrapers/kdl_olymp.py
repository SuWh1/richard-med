import json
import re
from pathlib import Path
from urllib.parse import urlencode

from app.core.cities import kdl_city_id, kdl_slug
from app.scrapers.base import (
    BaseSourceAdapter,
    BranchHit,
    RawDocument,
    RawPriceItem,
    SnapshotResult,
)
from app.scrapers.http import PoliteClient, content_hash

BASE_URL = "https://kdlolymp.kz"
API_URL = f"{BASE_URL}/api/analysis-data"
BRANCHES_URL = f"{BASE_URL}/api/procedure-cabinet"
CLINIC_NAME = "KDL Olymp"
_FIXTURE = (
    Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "kdl_analysis_data_astana.json"
)

# KDL's internal JSON price API. `per-page` counts categories (49 total), so one page
# with per-page=100 returns the whole catalog. Public, unauthenticated, robots-clean.
_DIGITS = re.compile(r"\d+")


def _working_hours(schedules: list | None) -> str | None:
    for schedule in schedules or []:
        if schedule.get("type") != "working_hours":
            continue
        parts = []
        if schedule.get("weekday_start") and schedule.get("weekday_end"):
            parts.append(f"Пн-Пт {schedule['weekday_start']}-{schedule['weekday_end']}")
        if schedule.get("saturday_start") and schedule.get("saturday_end"):
            parts.append(f"Сб {schedule['saturday_start']}-{schedule['saturday_end']}")
        return ", ".join(parts) or None
    return None


def _duration_str(min_d: int | None, max_d: int | None) -> str | None:
    if min_d is None and max_d is None:
        return None
    if min_d is not None and max_d is not None and min_d != max_d:
        return f"{min_d}-{max_d}"
    return str(max_d if max_d is not None else min_d)


class KdlOlympAdapter(BaseSourceAdapter):
    """KDL Olymp lab catalog via its internal `analysis-data` JSON API."""

    def __init__(self, client: PoliteClient | None = None):
        self._client = client

    def identity(self) -> str:
        return "kdl_olymp"

    def _url(self, slug: str) -> str:
        params = {"per-page": 100, "lang": "ru-RU", "city_slug": slug, "page": 1}
        return f"{API_URL}?{urlencode(params)}"

    def fetch(self, city: str) -> list[RawDocument]:
        slug = kdl_slug(city)
        if slug is None:
            return []
        url = self._url(slug)
        client = self._client or PoliteClient()
        try:
            response = client.get(url)
        finally:
            if self._client is None:
                client.close()
        text = response.text
        return [
            RawDocument(
                source_name=self.identity(),
                source_url=url,
                city=city,
                raw_html=text,
                content_hash=content_hash(text),
                status_code=response.status_code,
                fetched_at="",
            )
        ]

    def parse(self, raw_doc: RawDocument) -> list[RawPriceItem]:
        payload = json.loads(raw_doc.raw_html)
        items: list[RawPriceItem] = []
        for category in payload.get("data", []):
            category_title = (category.get("translation") or {}).get("title")
            for analysis in category.get("analysis", []):
                title = (analysis.get("translation") or {}).get("title")
                price_block = analysis.get("price") or {}
                price = price_block.get("price")
                if not title or not price:
                    continue
                # "(динамика)" are cheap re-test variants that falsely match the base service.
                if "динамика" in title.lower():
                    continue
                slug = analysis.get("slug") or ""
                item_url = f"{BASE_URL}/analysis/{slug}" if slug else raw_doc.source_url
                min_d = price_block.get("min_duration")
                max_d = price_block.get("max_duration")
                items.append(
                    RawPriceItem(
                        source_url=item_url,
                        clinic_raw=CLINIC_NAME,
                        service_name_raw=title,
                        price_raw=str(price),
                        duration_raw=_duration_str(min_d, max_d),
                        metadata={
                            "category": category_title,
                            "code": analysis.get("code"),
                            "city": raw_doc.city,
                        },
                    )
                )
        return items

    def clean(self, raw_item: RawPriceItem) -> RawPriceItem:
        digits = "".join(_DIGITS.findall(raw_item.price_raw or ""))
        return RawPriceItem(
            source_url=raw_item.source_url,
            clinic_raw=(raw_item.clinic_raw or "").strip() or CLINIC_NAME,
            service_name_raw=" ".join((raw_item.service_name_raw or "").split()),
            price_raw=digits,
            duration_raw=raw_item.duration_raw,
            metadata=raw_item.metadata,
        )

    def brand_name(self) -> str:
        return CLINIC_NAME

    def default_category(self) -> str:
        return "лаборатория"  # KDL is a lab; uncategorized analytes are lab tests

    def fetch_branches(self, city: str) -> list[BranchHit]:
        city_id = kdl_city_id(city)
        if city_id is None:
            return []
        url = f"{BRANCHES_URL}?lang=ru-RU&city_id={city_id}"
        client = self._client or PoliteClient()
        try:
            response = client.get(url)
        finally:
            if self._client is None:
                client.close()
        return self.parse_branches(response.text, city)

    def parse_branches(self, text: str, city: str) -> list[BranchHit]:
        payload = json.loads(text)
        hits: list[BranchHit] = []
        for cabinet in payload.get("data", []):
            lat, lng = cabinet.get("latitude"), cabinet.get("longitude")
            if not lat or not lng:
                continue
            translation = cabinet.get("translation") or {}
            hits.append(
                BranchHit(
                    external_id=str(cabinet.get("slug") or cabinet.get("id")),
                    name=translation.get("title") or CLINIC_NAME,
                    city=city,
                    address=translation.get("address"),
                    lat=float(lat),
                    lng=float(lng),
                    phone=cabinet.get("phone"),
                    working_hours=_working_hours(cabinet.get("schedules")),
                )
            )
        return hits

    def test_snapshot(self) -> SnapshotResult:
        text = _FIXTURE.read_text(encoding="utf-8")
        doc = RawDocument(
            source_name=self.identity(),
            source_url=self._url("astana"),
            city="Астана",
            raw_html=text,
            content_hash=content_hash(text),
            status_code=200,
            fetched_at="",
        )
        items = [self.clean(item) for item in self.parse(doc)]
        return SnapshotResult(item_count=len(items), sample_items=items[:3])
