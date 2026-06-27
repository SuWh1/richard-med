import re
from dataclasses import dataclass

from rapidfuzz import fuzz, process
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Service, ServiceAlias

FUZZY_AUTO = 0.88
FUZZY_SUGGEST = 0.75

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

    def __init__(self, session: Session):
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
            cleaned, self._fuzzy_choices.keys(), scorer=fuzz.token_set_ratio
        )
        if best is None:
            return MatchResult(None, 0.0, "none")
        choice, score, _ = best
        confidence = score / 100.0
        sid = self._fuzzy_choices[choice]
        if confidence >= FUZZY_AUTO:
            return MatchResult(sid, confidence, "fuzzy")
        if confidence >= FUZZY_SUGGEST:
            return MatchResult(sid, confidence, "suggest")
        return MatchResult(None, confidence, "none")


def match_service(raw_name: str, session: Session) -> MatchResult:
    """One-shot match. For batches, build a ServiceMatcher once and reuse it."""
    return ServiceMatcher(session).match(raw_name)
