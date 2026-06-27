import json
import re
from pathlib import Path
from urllib.parse import urlencode

from app.scrapers.base import (
    BaseSourceAdapter,
    RawDocument,
    RawPriceItem,
    SnapshotResult,
)
from app.scrapers.http import PoliteClient, content_hash

BASE_URL = "https://kdlolymp.kz"
API_URL = f"{BASE_URL}/api/analysis-data"
CLINIC_NAME = "KDL Olymp"
_FIXTURE = (
    Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "kdl_analysis_data_astana.json"
)

# KDL's internal JSON price API. `per-page` counts categories (49 total), so one page
# with per-page=100 returns the whole catalog. Public, unauthenticated, robots-clean.
_CITY_SLUGS = {"Астана": "astana", "Алматы": "almaty"}
_DIGITS = re.compile(r"\d+")


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
        slug = _CITY_SLUGS.get(city)
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
