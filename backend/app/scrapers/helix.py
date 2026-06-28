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
# helix.kz (expired cert, redirects here) serves each KZ city's lab catalog under a path
# prefix in ₸; the page is genuinely per-city (h1 "...в Астане"/"...в Алматы"). The bare
# /catalog/* path defaults to a Russian city (₽). Павлодар's pages exist but ship no
# catalog cards, so only the two cities with real data are mapped.
_CITY_SLUG = {"Алматы": "almaty", "Астана": "astana"}
CLINIC_NAME = "Хеликс"

# robots.txt (User-agent: *) has `Disallow: *?*` — every query string is off-limits, so
# `?page=N` pagination cannot be fetched. We take the first (server-rendered) page of each
# themed category instead; overlapping items are deduped downstream by (clinic, service).
# slug → source-native category title. We fetch one page per category, so the section
# a row belongs to is known from its document URL — we carry that human title through to
# the price row instead of re-deriving a coarse enum from keywords.
CATEGORIES: dict[str, str] = {
    "1-populyarnye-analizy": "Популярные анализы",
    "3-obschij-analiz-krovi": "Общий анализ крови",
    "4-analizy-kala": "Анализы кала",
    "5-analizy-mochi": "Анализы мочи",
    "6-analizy-spermy": "Анализы спермы",
    "7-analizy-na-citologiyu-i-gistologiyu": "Цитология и гистология",
    "11-analizy-na-autoimmunnye-zabolevaniya": "Аутоиммунные заболевания",
    "12-immunogrammy-analizy-na-markery-immuniteta": "Иммунитет (иммунограммы)",
    "15-lekarstvennyj-monitoring": "Лекарственный мониторинг",
    "16-analizy-na-tyazhelye-metally-i-mikroelementy": "Тяжёлые металлы и микроэлементы",
    "22-analizy-na-genetiku": "Генетика",
    "23-analizy-na-infekcii": "Инфекции",
    "24-analizy-dlya-beremennyh": "Анализы для беременных",
    "25-analizy-na-gruppu-krovi-i-rezus-faktor": "Группа крови и резус-фактор",
    "26-analizy-na-zppp-zabolevaniya-peredayuschiesya-polovym-putem": "ЗППП",
    "28-biohimicheskie-analizy": "Биохимические анализы",
    "29-analizy-na-gormony": "Гормоны",
    "30-analizy-na-allergiyu": "Аллергия",
    "31-analizy-na-svertyvaemost-krovi": "Свёртываемость крови",
    "32-bakteriologicheskie-issledovaniya-i-posevy": "Бактериология и посевы",
    "34-kompleksy-analizov": "Комплексы анализов",
    "178-uzi-ultrazvukovye-issledovaniya": "УЗИ",
    "179-ekg-elektrokardiogramma": "ЭКГ",
    "185-analizy-na-covid-19": "COVID-19",
    "189-analizy-na-vitaminy": "Витамины",
    "191-vrachebnye-uslugi": "Врачебные услуги",
    "204-analizy-dlya-onkodiagnostiki": "Онкодиагностика",
    "205-preventivnaya-medicina-i-nutriciologiya": "Превентивная медицина и нутрициология",
}


def _category_title(source_url: str) -> str | None:
    slug = source_url.rstrip("/").rsplit("/catalog/", 1)[-1]
    return CATEGORIES.get(slug)
_FIXTURE = (
    Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "helix_almaty_populyarnye.html"
)
_PRICE_RE = re.compile(r"(\d[\d\s ]*)₸")  # digits followed by ₸
_DURATION_RE = re.compile(r"До\s+(\d+)\s+(?:рабоч\w+\s+)?(?:сут|дн)", re.IGNORECASE)


def _category_url(city_slug: str, slug: str) -> str:
    return f"{BASE_URL}/{city_slug}/catalog/{slug}"


class HelixAdapter(BaseSourceAdapter):
    """Хеликс (Helix) Almaty lab catalog, parsed from server-rendered category pages."""

    def __init__(self, client: PoliteClient | None = None):
        self._client = client

    def identity(self) -> str:
        return "helix"

    def fetch(self, city: str) -> list[RawDocument]:
        city_slug = _CITY_SLUG.get(city)
        if city_slug is None:
            return []
        client = self._client or PoliteClient()
        docs: list[RawDocument] = []
        try:
            for slug in CATEGORIES:
                url = _category_url(city_slug, slug)
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
        city_slug = _CITY_SLUG.get(raw_doc.city, "almaty")
        category = _category_title(raw_doc.source_url)
        items: list[RawPriceItem] = []
        for card in soup.select("a.card[href]"):
            price_text = card.find(string=_PRICE_RE)
            if not price_text:
                continue
            name = self._card_name(card)
            if not name:
                continue
            href = card.get("href") or ""
            # Per-item detail page; carry the same city prefix so the link a user clicks
            # shows that city's prices (verified HTTP 200). Falls back to the category page.
            item_url = f"{BASE_URL}/{city_slug}{href}" if href.startswith("/") else raw_doc.source_url
            duration = self._card_duration(card)
            items.append(
                RawPriceItem(
                    source_url=item_url,
                    clinic_raw=CLINIC_NAME,
                    service_name_raw=name,
                    price_raw=price_text,
                    duration_raw=duration,
                    metadata={
                        "category": category,
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
            source_url=_category_url("almaty", "1-populyarnye-analizy"),
            city="Алматы",
            raw_html=text,
            content_hash=content_hash(text),
            status_code=200,
            fetched_at="",
        )
        items = [self.clean(item) for item in self.parse(doc)]
        return SnapshotResult(item_count=len(items), sample_items=items[:5])
