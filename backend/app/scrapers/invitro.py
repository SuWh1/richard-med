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

BASE_URL = "https://invitro.kz"
# The full "for doctors" catalog renders every product server-side as <a class="analysis">
# anchors with data-product-* attributes. No query string (robots disallows /*?), and the
# city/ variant 301-redirects here — Invitro KZ publishes one national list (Almaty-priced).
CATALOG_URL = f"{BASE_URL}/analizes/for-doctors/"
CLINIC_NAME = "Invitro"
# Invitro KZ publishes ONE national price list with unified pricing (verified: Astana shows
# the same prices as Almaty). It operates in these canonical cities (invitro.kz CITY_NAME
# slugs ∩ core/cities.py); the same national list is served for each so a city the chain
# actually serves isn't left empty. Almaty-only suburb towns and non-canonical cities
# (Семей, Уральск, Талдыкорган) are excluded.
SUPPORTED_CITIES = frozenset(
    {
        "Алматы", "Астана", "Актау", "Актобе", "Атырау", "Караганда", "Костанай",
        "Кызылорда", "Павлодар", "Петропавловск", "Шымкент", "Тараз", "Темиртау",
        "Усть-Каменогорск",
    }
)
_FIXTURE = (
    Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "invitro_analizes_almaty.html"
)
_DIGITS = re.compile(r"\d+")


class InvitroAdapter(BaseSourceAdapter):
    """Invitro KZ lab catalog, parsed from the server-rendered `for-doctors` price page."""

    def __init__(self, client: PoliteClient | None = None):
        self._client = client

    def identity(self) -> str:
        return "invitro"

    def fetch(self, city: str) -> list[RawDocument]:
        if city not in SUPPORTED_CITIES:
            return []
        client = self._client or PoliteClient()
        try:
            response = client.get(CATALOG_URL)
        finally:
            if self._client is None:
                client.close()
        text = response.text
        return [
            RawDocument(
                source_name=self.identity(),
                source_url=CATALOG_URL,
                city=city,
                raw_html=text,
                content_hash=content_hash(text),
                status_code=response.status_code,
                fetched_at="",
            )
        ]

    def parse(self, raw_doc: RawDocument) -> list[RawPriceItem]:
        soup = BeautifulSoup(raw_doc.raw_html, "html.parser")
        items: list[RawPriceItem] = []
        for el in soup.select("a.analysis[data-product-price]"):
            name = el.get("data-product-name")
            price = el.get("data-product-price")
            if not name or not price or not any(c in "123456789" for c in price):
                continue
            href = el.get("href") or ""
            # The per-item href resolves in a browser (verified 200); fall back to the
            # catalog page if a row ever ships without one.
            item_url = f"{BASE_URL}{href}" if href.startswith("/") else (href or CATALOG_URL)
            items.append(
                RawPriceItem(
                    source_url=item_url,
                    clinic_raw=CLINIC_NAME,
                    service_name_raw=name,
                    price_raw=str(price),
                    metadata={
                        "article": el.get("data-product-article"),
                        "category_id": el.get("data-category-id"),
                        "city": raw_doc.city,
                    },
                )
            )
        return items

    def clean(self, raw_item: RawPriceItem) -> RawPriceItem:
        digits = "".join(_DIGITS.findall(raw_item.price_raw or ""))
        # Drop the trailing English gloss in parens so the matcher sees the Russian name.
        name = re.sub(r"\s*\([A-Za-z][^)]*\)\s*$", "", raw_item.service_name_raw or "")
        return RawPriceItem(
            source_url=raw_item.source_url,
            clinic_raw=(raw_item.clinic_raw or "").strip() or CLINIC_NAME,
            service_name_raw=" ".join(name.split()),
            price_raw=digits,
            duration_raw=raw_item.duration_raw,
            metadata=raw_item.metadata,
        )

    def brand_name(self) -> str:
        return CLINIC_NAME

    def default_category(self) -> str:
        return "лаборатория"

    def test_snapshot(self) -> SnapshotResult:
        text = _FIXTURE.read_text(encoding="utf-8")
        doc = RawDocument(
            source_name=self.identity(),
            source_url=CATALOG_URL,
            city="Алматы",
            raw_html=text,
            content_hash=content_hash(text),
            status_code=200,
            fetched_at="",
        )
        items = [self.clean(item) for item in self.parse(doc)]
        return SnapshotResult(item_count=len(items), sample_items=items[:5])
