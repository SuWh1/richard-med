import re
from pathlib import Path

from bs4 import BeautifulSoup

from app.scrapers.base import (
    BaseSourceAdapter,
    RawDocument,
    RawPriceItem,
    SnapshotResult,
)
from app.scrapers.http import PoliteClient, content_hash

BASE_URL = "https://kdlolymp.kz"
CLINIC_NAME = "KDL Olymp"
_FIXTURE = Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "kdl_pricelist_astana.html"

# KDL serves one price list per city under /pricelist/<slug>.
_CITY_SLUGS = {"Астана": "astana", "Алматы": "almaty"}
_DIGITS = re.compile(r"\d+")


class KdlOlympAdapter(BaseSourceAdapter):
    """KDL Olymp lab price list — server-rendered HTML, one `a.analysis` row per service."""

    def __init__(self, client: PoliteClient | None = None):
        self._client = client

    def identity(self) -> str:
        return "kdl_olymp"

    def fetch(self, city: str) -> list[RawDocument]:
        slug = _CITY_SLUGS.get(city)
        if slug is None:
            return []
        url = f"{BASE_URL}/pricelist/{slug}"
        client = self._client or PoliteClient()
        try:
            response = client.get(url)
        finally:
            if self._client is None:
                client.close()
        html = response.text
        return [
            RawDocument(
                source_name=self.identity(),
                source_url=url,
                city=city,
                raw_html=html,
                content_hash=content_hash(html),
                status_code=response.status_code,
                fetched_at="",
            )
        ]

    def parse(self, raw_doc: RawDocument) -> list[RawPriceItem]:
        soup = BeautifulSoup(raw_doc.raw_html, "html.parser")
        items: list[RawPriceItem] = []
        for row in soup.select("a.analysis"):
            title = row.select_one(".title")
            price = row.select_one(".price")
            if title is None or price is None:
                continue
            name = title.get_text(strip=True)
            if not name:
                continue
            category = row.select_one(".category")
            duration = row.select_one(".duration")
            href = row.get("href") or ""
            item_url = f"{BASE_URL}{href}" if href.startswith("/") else (href or raw_doc.source_url)
            items.append(
                RawPriceItem(
                    source_url=item_url,
                    clinic_raw=CLINIC_NAME,
                    service_name_raw=name,
                    price_raw=price.get_text(strip=True),
                    duration_raw=duration.get_text(strip=True) if duration else None,
                    metadata={
                        "category": category.get_text(strip=True) if category else None,
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
        html = _FIXTURE.read_text(encoding="utf-8")
        doc = RawDocument(
            source_name=self.identity(),
            source_url=f"{BASE_URL}/pricelist/astana",
            city="Астана",
            raw_html=html,
            content_hash=content_hash(html),
            status_code=200,
            fetched_at="",
        )
        items = [self.clean(item) for item in self.parse(doc)]
        return SnapshotResult(item_count=len(items), sample_items=items[:3])
