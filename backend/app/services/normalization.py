import logging
import re
from collections.abc import Callable
from dataclasses import dataclass

from rapidfuzz import fuzz, process
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Service, ServiceAlias

logger = logging.getLogger(__name__)

FUZZY_AUTO = 0.88
FUZZY_SUGGEST = 0.75
SEMANTIC_THRESHOLD = 0.88

# A callable that turns a service name into an embedding vector (or None if unavailable).
Embedder = Callable[[str], list[float] | None]

# Latin letters that share a glyph with a Cyrillic letter. Folded symmetrically on
# both the query and the catalog side, so mixed-script duplicates collapse together.
_HOMOGLYPHS = str.maketrans(
    {
        "a": "а", "c": "с", "e": "е", "o": "о", "p": "р", "x": "х",
        "y": "у", "k": "к", "m": "м", "t": "т", "h": "н", "b": "в",
    }
)

_PUNCT = re.compile(r"[^0-9a-zа-я]+")


def canonical_clean(name: str) -> str:
    """Lowercase, fold ё→е and Latin/Cyrillic homoglyphs, strip punctuation/extra spaces."""
    if not name:
        return ""
    text = name.lower().replace("ё", "е").translate(_HOMOGLYPHS)
    text = _PUNCT.sub(" ", text)
    return " ".join(text.split())


def _discriminating_score(query: str, choice: str, **_kwargs) -> float:
    """Fuzzy score that won't inflate when the candidate is a tiny token-subset.

    token_set_ratio alone rewards a single shared generic token: "Витамин D" scores
    ~88% against any "Витамин B6 …" because the common "витамин" carries the match and
    the discriminating tokens (B6, D) are ignored. Blending with token_sort_ratio — which
    does penalize the extra/different tokens — forces a real overlap: a short catalog
    name can only auto-match a long raw name when they genuinely share most of their words.
    """
    return min(
        fuzz.token_set_ratio(query, choice),
        fuzz.token_sort_ratio(query, choice),
    )


@dataclass(frozen=True)
class MatchResult:
    service_id: int | None
    confidence: float
    method: str  # exact | alias | fuzzy | suggest | none


class ServiceMatcher:
    """Loads the catalog once and matches raw names through the waterfall.

    Reuse a single instance across a batch (import, seeding, a parse run) — it builds
    in-memory indexes on construction.
    """

    def __init__(self, session: Session, embedder: Embedder | None = None):
        self._session = session
        self._embedder = embedder
        self._exact: dict[str, int] = {}
        self._alias: dict[str, tuple[int, float]] = {}
        self._fuzzy_choices: dict[str, int] = {}

        for sid, name in session.execute(select(Service.id, Service.name_ru)).all():
            cleaned = canonical_clean(name)
            self._exact.setdefault(cleaned, sid)
            self._fuzzy_choices.setdefault(cleaned, sid)

        rows = session.execute(
            select(ServiceAlias.service_id, ServiceAlias.alias, ServiceAlias.confidence)
        ).all()
        for sid, alias, conf in rows:
            cleaned = canonical_clean(alias)
            self._alias.setdefault(cleaned, (sid, conf))
            self._fuzzy_choices.setdefault(cleaned, sid)

    def match(self, raw_name: str) -> MatchResult:
        cleaned = canonical_clean(raw_name)
        if not cleaned:
            return MatchResult(None, 0.0, "none")

        if cleaned in self._exact:
            return MatchResult(self._exact[cleaned], 1.0, "exact")

        if cleaned in self._alias:
            sid, conf = self._alias[cleaned]
            return MatchResult(sid, conf, "alias")

        best = process.extractOne(
            cleaned, self._fuzzy_choices.keys(), scorer=_discriminating_score
        )
        if best is not None:
            choice, score, _ = best
            confidence = score / 100.0
            sid = self._fuzzy_choices[choice]
            if confidence >= FUZZY_AUTO:
                return MatchResult(sid, confidence, "fuzzy")
        else:
            confidence, sid = 0.0, None

        # Semantic fallback (offline only) when exact/alias/fuzzy didn't auto-match.
        semantic = self._semantic_match(raw_name)
        if semantic is not None:
            return semantic

        if confidence >= FUZZY_SUGGEST:
            return MatchResult(sid, confidence, "suggest")
        return MatchResult(None, confidence, "none")

    def _semantic_match(self, raw_name: str) -> MatchResult | None:
        if self._embedder is None:
            return None
        try:
            vector = self._embedder(raw_name)
        except Exception:  # noqa: BLE001 — embedding must never break a parse run
            logger.exception("embedder failed for %r", raw_name)
            return None
        if vector is None:
            return None
        distance = Service.embedding.cosine_distance(vector)
        row = self._session.execute(
            select(Service.id, distance.label("dist"))
            .where(Service.embedding.is_not(None))
            .order_by(distance)
            .limit(1)
        ).first()
        if row is None:
            return None
        similarity = 1.0 - float(row.dist)
        if similarity >= SEMANTIC_THRESHOLD:
            return MatchResult(row.id, round(similarity, 4), "semantic")
        return None


def match_service(raw_name: str, session: Session) -> MatchResult:
    """One-shot match. For batches, build a ServiceMatcher once and reuse it."""
    return ServiceMatcher(session).match(raw_name)
