"""AI comparison of clinics by rating + recent reviews (on demand, key-gated).

Triggered by an explicit "compare with AI" action on the compare page — never in the
search path (Rule 1). Reads reviews already stored in our DB (no live 2GIS), sends the
ratings + last few review texts to Gemini, and returns a per-clinic summary plus an
overall verdict. Fully optional: disabled when no GEMINI_API_KEY is set.
"""

import json
import logging
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from typing import Protocol

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import CompareInsightCache
from app.services.clinics import clinic_detail, clinic_reviews

logger = logging.getLogger(__name__)

REVIEWS_PER_CLINIC = 5
_RETRYABLE_STATUS = frozenset({429, 500, 502, 503, 504})


@dataclass(frozen=True)
class ClinicReviewData:
    clinic_id: int
    name: str
    rating: float | None
    reviews_count: int | None
    reviews: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ClinicInsight:
    clinic_id: int
    clinic_name: str
    rating: float | None
    reviews_count: int | None
    summary: str


@dataclass(frozen=True)
class CompareInsight:
    available: bool
    service_name: str
    clinics: list[ClinicInsight]
    verdict: str | None
    best_clinic_id: int | None
    reason: str | None = None  # "no_data" | "no_ai" when available is False


class InsightUnavailable(Exception):
    """The LLM was called but failed/returned junk — transient, the caller should retry."""


def gather_review_data(
    session: Session, clinic_ids: list[int]
) -> list[ClinicReviewData]:
    out: list[ClinicReviewData] = []
    for clinic_id in clinic_ids:
        detail = clinic_detail(session, clinic_id)
        if detail is None:
            continue
        reviews = clinic_reviews(session, clinic_id, limit=REVIEWS_PER_CLINIC)
        texts = [r.text.strip() for r in reviews if r.text and r.text.strip()]
        out.append(
            ClinicReviewData(
                clinic_id=detail.id,
                name=detail.name,
                rating=detail.rating,
                reviews_count=detail.reviews_count,
                reviews=texts,
            )
        )
    return out


def build_prompt(service_name: str, clinics: list[ClinicReviewData]) -> str:
    lines = [f"Услуга: {service_name}", "", "Клиники для сравнения:"]
    for i, c in enumerate(clinics):
        rating = f"{c.rating:.1f}" if c.rating is not None else "нет рейтинга"
        lines.append(f"\n{i}. {c.name} — рейтинг {rating} ({c.reviews_count or 0} отзывов)")
        if c.reviews:
            lines.append("Последние отзывы:")
            lines.extend(f"- {text}" for text in c.reviews)
        else:
            lines.append("Отзывов нет.")
    instructions = (
        "\nТы — медицинский консультант. На основе рейтинга и последних отзывов сравни "
        "эти клиники. Для каждой клиники дай краткое резюме (одно предложение на русском) "
        "о качестве по отзывам. Затем выбери лучшую с учётом рейтинга и отзывов и кратко "
        "обоснуй выбор (1–2 предложения).\n"
        'Ответь строго в JSON без markdown: '
        '{"summaries": ["...", ...], "best_index": <индекс>, "verdict": "..."}. '
        "Число элементов в summaries должно совпадать с числом клиник."
    )
    return "\n".join(lines) + "\n" + instructions


def parse_insight(
    raw: str, clinics: list[ClinicReviewData], service_name: str
) -> CompareInsight | None:
    try:
        data = json.loads(raw)
        summaries = data["summaries"]
    except (ValueError, KeyError, TypeError):
        return None
    if not isinstance(summaries, list) or len(summaries) != len(clinics):
        return None

    items = [
        ClinicInsight(
            clinic_id=c.clinic_id,
            clinic_name=c.name,
            rating=c.rating,
            reviews_count=c.reviews_count,
            summary=str(summary).strip(),
        )
        for c, summary in zip(clinics, summaries, strict=True)
    ]
    best_index = data.get("best_index")
    best_clinic_id = (
        clinics[best_index].clinic_id
        if isinstance(best_index, int) and 0 <= best_index < len(clinics)
        else None
    )
    return CompareInsight(
        available=True,
        service_name=service_name,
        clinics=items,
        verdict=(data.get("verdict") or None),
        best_clinic_id=best_clinic_id,
    )


class _PostClient(Protocol):
    def post(self, url: str, json: dict | None = None) -> httpx.Response: ...


class InsightLlm:
    def __init__(self, api_key: str, model: str, base_url: str, client: _PostClient):
        self._api_key = api_key
        self._model = model
        self._base_url = base_url
        self._client = client

    def generate(self, prompt: str) -> str | None:
        url = f"{self._base_url}/{self._model}:generateContent?key={self._api_key}"
        body = {
            "contents": [{"parts": [{"text": prompt}]}],
            # A response schema constrains the model to clean JSON, so it can't dump its
            # chain-of-thought into the text output.
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseSchema": {
                    "type": "OBJECT",
                    "properties": {
                        "summaries": {"type": "ARRAY", "items": {"type": "STRING"}},
                        "best_index": {"type": "INTEGER"},
                        "verdict": {"type": "STRING"},
                    },
                    "required": ["summaries", "best_index", "verdict"],
                },
            },
        }
        # Never log the exception or URL — the URL carries the API key.
        try:
            response = self._client.post(url, json=body)
            response.raise_for_status()
            return response.json()["candidates"][0]["content"]["parts"][0]["text"]
        except httpx.HTTPStatusError as exc:
            logger.warning("gemini insight failed (HTTP %s)", exc.response.status_code)
            return None
        except (httpx.TransportError, KeyError, IndexError, ValueError) as exc:
            logger.warning("gemini insight error (%s)", type(exc).__name__)
            return None


def get_insighter(
    factory: Callable[[], InsightLlm | None] | None = None,
) -> InsightLlm | None:
    if factory is not None:
        return factory()
    if not settings.GEMINI_API_KEY:
        return None
    return InsightLlm(
        settings.GEMINI_API_KEY,
        settings.GEMINI_MODEL,
        settings.GEMINI_URL,
        httpx.Client(timeout=30.0),
    )


def cache_key(service_id: int, clinic_ids: list[int]) -> str:
    ids = ",".join(str(i) for i in sorted(set(clinic_ids)))
    return f"{service_id}:{ids}"


def _serialize(insight: CompareInsight) -> str:
    return json.dumps(asdict(insight), ensure_ascii=False)


def _deserialize(payload: str) -> CompareInsight:
    data = json.loads(payload)
    clinics = [ClinicInsight(**c) for c in data["clinics"]]
    return CompareInsight(**{**data, "clinics": clinics})


def _read_cache(session: Session, key: str) -> CompareInsight | None:
    row = session.scalar(
        select(CompareInsightCache).where(CompareInsightCache.cache_key == key)
    )
    if row is None:
        return None
    try:
        return _deserialize(row.payload)
    except (ValueError, TypeError, KeyError):
        return None


def _write_cache(session: Session, key: str, insight: CompareInsight) -> None:
    session.add(CompareInsightCache(cache_key=key, payload=_serialize(insight)))
    session.commit()


def compare_insight(
    session: Session,
    service_id: int,
    service_name: str,
    clinic_ids: list[int],
    *,
    llm: InsightLlm | None,
) -> CompareInsight:
    key = cache_key(service_id, clinic_ids)
    cached = _read_cache(session, key)
    if cached is not None:
        return cached

    clinics = gather_review_data(session, clinic_ids)
    has_data = any(c.rating is not None or c.reviews for c in clinics)

    def unavailable(reason: str) -> CompareInsight:
        return CompareInsight(
            available=False,
            service_name=service_name,
            clinics=[],
            verdict=None,
            best_clinic_id=None,
            reason=reason,
        )

    # Don't cache no-data / no-key results: they're cheap and may change once reviews land.
    if not clinics or not has_data:
        return unavailable("no_data")
    if llm is None:
        return unavailable("no_ai")

    raw = llm.generate(build_prompt(service_name, clinics))
    parsed = parse_insight(raw or "", clinics, service_name) if raw else None
    if parsed is None:
        # We had data and a configured model, but the call failed — let the caller retry.
        raise InsightUnavailable("llm call failed or returned unparseable output")
    _write_cache(session, key, parsed)
    return parsed
