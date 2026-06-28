"""2GIS ratings/reviews — offline only, never called in the user/search path.

Two stages (see docs in load_2gis_reviews / discover script):
  A. Firm-id discovery: a 2GIS firm is matched to one of our branches by name + geo
     proximity. Heavy (needs the browser collector); a firm_id is stable, so it runs
     once per branch and is cached on `clinic_branches.twogis_firm_id`.
  B. Reviews refresh: given a firm_id, pull aggregate rating + recent reviews from the
     public reviews API over plain HTTP. Light, no browser — this is what the daily
     parser calls to keep ratings current.

This module holds the pure logic (name match, geo pick, payload parse) and the Step-B
HTTP client. DB writes live in `twogis_sync`.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime

import httpx

from app.core.config import settings

_CYR_TO_LAT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
    "ж": "zh", "з": "z", "и": "i", "й": "i", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "h", "ц": "c", "ч": "ch", "ш": "sh", "щ": "sch", "ъ": "",
    "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
}
# Generic words that must not, on their own, make two clinics "match".
_STOPWORDS = {
    "med", "medical", "medicinskii", "medicinskij", "clinic", "klinika", "centr",
    "center", "laboratoriya", "laboratornyi", "set", "set'", "ooo", "too", "ip",
    "company", "kompaniya", "filial", "otdelenie", "diagnostika", "diagnosticheskii",
    "lab", "labs", "i", "and", "the", "na", "v",
}


def translit(text: str) -> str:
    return "".join(_CYR_TO_LAT.get(ch, ch) for ch in (text or "").lower())


def name_tokens(name: str) -> set[str]:
    latin = translit(name)
    raw = re.split(r"[^a-z0-9]+", latin)
    return {t for t in raw if len(t) >= 2 and t not in _STOPWORDS}


def name_matches(our_name: str, firm_name: str) -> bool:
    """True when the two names share at least one distinctive (non-generic) token."""
    ours = name_tokens(our_name)
    theirs = name_tokens(firm_name)
    return bool(ours and theirs and (ours & theirs))


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6_371_000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = math.sin(d_lat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(d_lon / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))


@dataclass(frozen=True)
class Firm:
    firm_id: str
    name: str
    address: str | None
    lat: float
    lon: float
    rating: float | None = None
    reviews_count: int | None = None


@dataclass(frozen=True)
class FirmMatch:
    firm: Firm
    distance_m: float


def pick_firm(
    branch_name: str,
    branch_lat: float,
    branch_lon: float,
    firms: list[Firm],
    radius_m: int | None = None,
) -> FirmMatch | None:
    """Nearest firm that BOTH name-matches the clinic and sits within radius. The
    name gate is what stops a different clinic 50 m away from being mis-matched."""
    radius = radius_m if radius_m is not None else settings.TWOGIS_MATCH_RADIUS_M
    best: FirmMatch | None = None
    for firm in firms:
        if not name_matches(branch_name, firm.name):
            continue
        dist = haversine_m(branch_lat, branch_lon, firm.lat, firm.lon)
        if dist > radius:
            continue
        if best is None or dist < best.distance_m:
            best = FirmMatch(firm=firm, distance_m=dist)
    return best


@dataclass(frozen=True)
class ReviewItem:
    external_id: str | None
    author: str | None
    rating: int | None
    text: str | None
    official_answer: str | None
    review_date: datetime | None


@dataclass(frozen=True)
class ReviewsResult:
    rating: float | None
    reviews_count: int | None
    reviews: list[ReviewItem] = field(default_factory=list)


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def parse_reviews_payload(payload: dict, sample: int | None = None) -> ReviewsResult:
    """Pure parse of the public reviews API response → aggregate + sample reviews."""
    meta = payload.get("meta") or {}
    rating = meta.get("branch_rating")
    if rating is None:
        rating = meta.get("org_rating")
    count = meta.get("branch_reviews_count")
    if count is None:
        count = meta.get("org_reviews_count")

    limit = sample if sample is not None else settings.TWOGIS_REVIEW_SAMPLE
    items: list[ReviewItem] = []
    for raw in payload.get("reviews") or []:
        text = (raw.get("text") or "").strip()
        if not text:
            continue
        user = raw.get("user") or {}
        answer = raw.get("official_answer") or {}
        items.append(
            ReviewItem(
                external_id=str(raw["id"]) if raw.get("id") is not None else None,
                author=user.get("name") or None,
                rating=raw.get("rating"),
                text=text,
                official_answer=(answer.get("text") or None),
                review_date=_parse_date(raw.get("date_created")),
            )
        )
        if len(items) >= limit:
            break

    return ReviewsResult(
        rating=float(rating) if rating is not None else None,
        reviews_count=int(count) if count is not None else None,
        reviews=items,
    )


def fetch_reviews(
    firm_id: str,
    *,
    client: httpx.Client | None = None,
    sample: int | None = None,
) -> ReviewsResult:
    """Step B: pull a firm's aggregate rating + recent reviews. Offline/background only."""
    limit = sample if sample is not None else settings.TWOGIS_REVIEW_SAMPLE
    params = {
        "key": settings.TWOGIS_REVIEWS_KEY,
        "limit": max(limit, 1),
        "sort_by": "date_created",
        "fields": (
            "meta.branch_rating,meta.branch_reviews_count,"
            "meta.org_rating,meta.org_reviews_count"
        ),
    }
    url = f"{settings.TWOGIS_REVIEWS_URL}/{firm_id}/reviews"
    owns = client is None
    client = client or httpx.Client(timeout=20.0)
    try:
        resp = client.get(url, params=params)
        resp.raise_for_status()
        return parse_reviews_payload(resp.json(), sample=limit)
    finally:
        if owns:
            client.close()
