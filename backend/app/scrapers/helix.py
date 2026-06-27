import logging
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

logger = logging.getLogger(__name__)

BASE_URL = "https://helix.ru"
# helix.kz 301-redirects to helix.ru; the Almaty lab is served under the /almaty/ path
# prefix (prices in ₸). The bare /catalog/* path defaults to a Russian city (₽).
CITY_PREFIX = "/almaty"
CLINIC_NAME = "Хеликс"
SUPPORTED_CITY = "Алматы"

# robots.txt (User-agent: *) has `Disallow: *?*` — every query string is off-limits, so
# `?page=N` pagination cannot be fetched. We take the first (server-rendered) page of each
# themed category instead; overlapping items are deduped downstream by (clinic, service).
CATEGORIES = (
    "1-populyarnye-analizy",
    "3-obschij-analiz-krovi",
    "4-analizy-kala",
    "5-analizy-mochi",
    "6-analizy-spermy",
    "7-analizy-na-citologiyu-i-gistologiyu",
    "11-analizy-na-autoimmunnye-zabolevaniya",
    "12-immunogrammy-analizy-na-markery-immuniteta",
    "15-lekarstvennyj-monitoring",
    "16-analizy-na-tyazhelye-metally-i-mikroelementy",
    "22-analizy-na-genetiku",
    "23-analizy-na-infekcii",
    "24-analizy-dlya-beremennyh",
    "25-analizy-na-gruppu-krovi-i-rezus-faktor",
    "26-analizy-na-zppp-zabolevaniya-peredayuschiesya-polovym-putem",
    "28-biohimicheskie-analizy",
    "29-analizy-na-gormony",
    "30-analizy-na-allergiyu",
    "31-analizy-na-svertyvaemost-krovi",
    "32-bakteriologicheskie-issledovaniya-i-posevy",
    "34-kompleksy-analizov",
    "178-uzi-ultrazvukovye-issledovaniya",
    "179-ekg-elektrokardiogramma",
    "185-analizy-na-covid-19",
    "189-analizy-na-vitaminy",
    "191-vrachebnye-uslugi",
    "204-analizy-dlya-onkodiagnostiki",
    "205-preventivnaya-medicina-i-nutriciologiya",
)
_FIXTURE = (
    Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "helix_almaty_populyarnye.html"
)
_PRICE_RE = re.compile(r"(\d[\d\s ]*)₸")  # digits followed by ₸
_DURATION_RE = re.compile(r"До\s+(\d+)\s+(?:рабоч\w+\s+)?(?:сут|дн)", re.IGNORECASE)


def _category_url(slug: str) -> str:
    return f"{BASE_URL}{CITY_PREFIX}/catalog/{slug}"


class HelixAdapter(BaseSourceAdapter):
    """Хеликс (Helix) Almaty lab catalog, parsed from server-rendered category pages."""

    def __init__(self, client: PoliteClient | None = None):
        self._client = client

    def identity(self) -> str:
        return "helix"

    def fetch(self, city: str) -> list[RawDocument]:
        if city != SUPPORTED_CITY:
            return []
        client = self._client or PoliteClient()
        docs: list[RawDocument] = []
        try:
            for slug in CATEGORIES:
                url = _category_url(slug)
                try:
                    response = client.get(url)
                except Exception as exc:  # noqa: BLE001 — one bad category must not abort the rest
                    logger.warning("helix category fetch failed for %s (%s)", slug, type(exc).__name__)
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
        finally:
            if self._client is None:
                client.close()
        # Coverage is bounded to each category's first server-rendered page: robots.txt
        # disallows the `?page=N` pagination, so deeper items are intentionally skipped.
        logger.info("helix: fetched %d/%d categories (first page only, robots-bound)", len(docs), len(CATEGORIES))
        return docs

    def parse(self, raw_doc: RawDocument) -> list[RawPriceItem]:
        soup = BeautifulSoup(raw_doc.raw_html, "html.parser")
        items: list[RawPriceItem] = []
        for card in soup.select("a.card[href]"):
            price_text = card.find(string=_PRICE_RE)
            if not price_text:
                continue
            name = self._card_name(card)
            if not name:
                continue
            href = card.get("href") or ""
            # Per-item detail page; prefix with /almaty so the link a user clicks shows
            # Almaty prices (verified HTTP 200). Falls back to the category page.
            item_url = f"{BASE_URL}{CITY_PREFIX}{href}" if href.startswith("/") else raw_doc.source_url
            duration = self._card_duration(card)
            items.append(
                RawPriceItem(
                    source_url=item_url,
                    clinic_raw=CLINIC_NAME,
                    service_name_raw=name,
                    price_raw=price_text,
                    duration_raw=duration,
                    metadata={
                        "code": self._card_code(card),
                        "city": raw_doc.city,
                    },
                )
            )
        return items

    @staticmethod
    def _card_name(card) -> str | None:
        # The name is the headline that is neither bold (the price) nor empty.
        for el in card.select(".typography-headline"):
            if "typography-bold" in el.get("class", []):
                continue
            text = el.get_text(" ", strip=True)
            if text and "₸" not in text:
                return text
        return None

    @staticmethod
    def _card_code(card) -> str | None:
        tag = card.select_one("span.tag")
        return tag.get_text(strip=True) if tag else None

    @staticmethod
    def _card_duration(card) -> str | None:
        match = _DURATION_RE.search(card.get_text(" ", strip=True))
        return match.group(1) if match else None

    def clean(self, raw_item: RawPriceItem) -> RawPriceItem:
        digits = "".join(ch for ch in (raw_item.price_raw or "") if ch.isdigit())
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
        return "лаборатория"  # dominant; a few diagnostics/visits are matched by name

    def test_snapshot(self) -> SnapshotResult:
        text = _FIXTURE.read_text(encoding="utf-8")
        doc = RawDocument(
            source_name=self.identity(),
            source_url=_category_url("1-populyarnye-analizy"),
            city=SUPPORTED_CITY,
            raw_html=text,
            content_hash=content_hash(text),
            status_code=200,
            fetched_at="",
        )
        items = [self.clean(item) for item in self.parse(doc)]
        return SnapshotResult(item_count=len(items), sample_items=items[:5])
