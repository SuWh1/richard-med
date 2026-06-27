"""Grow the catalog from real source data so every scraped service can be shown.

When a scraped test has no catalog home, we add it as a new entry; when it has a
look-alike, an LLM arbitrates alias-vs-new. The given catalog is the seed, not the cap
(the brief asks the team to *form* the catalog). Offline + idempotent.
"""

import hashlib
import logging
from functools import cache

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    RawDocument,
    RawPriceItem,
    Service,
    ServiceAlias,
    ServiceCategory,
    UnmatchedService,
)
from app.scrapers.registry import get_adapter
from app.services.llm_verify import TransientVerifyError
from app.services.normalization import canonical_clean

logger = logging.getLogger(__name__)

# Positive keywords for every category (matched against source label + service name),
# checked in order — first hit wins, so procedure ("забор крови") beats lab ("кровь").
# A row that matches none is genuinely unknown and is quarantined as `other`, never
# silently filed as a lab test.
_CATEGORY_KEYWORDS = (
    (
        ServiceCategory.diagnostic,
        ("узи", "кт ", "мрт", "рентген", "эндоскоп", "флюорограф", "маммограф",
         "денситометр", "диагност", "эхокард", "экг", "ээг", "холтер", "колоноскоп",
         "гастроскоп", "фгдс", "томограф"),
    ),
    (
        ServiceCategory.doctor_visit,
        ("прием", "приём", "консультац", "осмотр", "врач", "справк", "выезд"),
    ),
    (
        ServiceCategory.procedure,
        ("массаж", "процедур", "инъекц", "перевяз", "забор", "пункц", "биопси",
         "капельниц", "блокад", "удален", "вакцин", "прививк"),
    ),
    (
        ServiceCategory.laboratory,
        ("анализ", "кров", "моч", "гормон", "биохим", "гематолог", "иммун", "серолог",
         "пцр", "антител", "онкомаркер", "аллерг", "ферритин", "глюкоз", "холестерин",
         "оак", "оам", "ттг", "витамин", "микробиолог", "коагул", "мазок", "посев",
         "цитолог", "гистолог", "инфекц", "профил", "панель", "генетик", "хроматограф",
         "секвенир", "мутаци", "генотип", "полиморфизм", "транслокац", "аллел", "ифа",
         "igg", "igm", "iga", "ige", "антиген", "маркер", "аутоиммун", "комплемент"),
    ),
)


class _Verifier:
    def verify(self, raw_name: str, candidate_name: str) -> bool | None: ...


def _map_category(
    raw_category: str | None,
    name: str = "",
    fallback: ServiceCategory = ServiceCategory.other,
) -> ServiceCategory:
    text = f"{raw_category or ''} {name or ''}".lower()
    for category, keywords in _CATEGORY_KEYWORDS:
        if any(keyword in text for keyword in keywords):
            return category
    return fallback


@cache
def _source_default_category(source_name: str | None) -> ServiceCategory:
    """A known single-domain source (KDL=lab, DOQ=visits) sets the fallback for its own
    rows — so its specialized but keyword-less items aren't wrongly quarantined. An
    unknown/mixed source falls back to `other` for honest review."""
    if not source_name:
        return ServiceCategory.other
    try:
        value = get_adapter(source_name).default_category()
    except ValueError:
        return ServiceCategory.other
    return ServiceCategory(value) if value else ServiceCategory.other


def _category_for(session: Session, raw_item_id: int | None, name: str = "") -> ServiceCategory:
    raw_category = None
    source_name = None
    if raw_item_id is not None:
        item = session.get(RawPriceItem, raw_item_id)
        if item is not None:
            raw_category = (item.metadata_json or {}).get("category")
            doc = session.get(RawDocument, item.raw_document_id)
            source_name = doc.source_name if doc else None
    return _map_category(raw_category, name, fallback=_source_default_category(source_name))


def _service_key(name: str) -> str:
    return "auto-" + hashlib.sha1(canonical_clean(name).encode("utf-8")).hexdigest()[:12]


def _ensure_service(session: Session, name: str, category: ServiceCategory) -> Service:
    existing = session.scalars(select(Service).where(Service.name_ru == name)).first()
    if existing is not None:
        return existing
    key = _service_key(name)
    by_key = session.scalars(select(Service).where(Service.service_key == key)).first()
    if by_key is not None:
        return by_key
    service = Service(service_key=key, name_ru=name, category=category)
    session.add(service)
    session.flush()
    return service


def _add_alias(session: Session, service_id: int, alias: str) -> None:
    exists = session.scalars(
        select(ServiceAlias.id).where(
            ServiceAlias.service_id == service_id, ServiceAlias.alias == alias
        )
    ).first()
    if not exists:
        session.add(
            ServiceAlias(service_id=service_id, alias=alias, source="llm", confidence=0.95)
        )


def grow_catalog(
    session: Session, verifier: _Verifier | None = None, limit: int | None = None
) -> dict[str, int]:
    """Process the pending unmatched queue into new catalog entries or aliases.

    `limit` bounds how many rows a single call processes, so a caller can drive the
    slow AI path in committed batches (short transactions) without this function
    committing itself (tests rely on rollback isolation).
    """
    stmt = select(UnmatchedService).where(UnmatchedService.status == "pending")
    if limit is not None:
        stmt = stmt.limit(limit)
    rows = session.scalars(stmt).all()
    added = aliased = skipped = deferred = 0

    for item in rows:
        raw_category = _category_for(session, item.raw_item_id, item.raw_name)

        if item.suggested_service_id is None:
            _ensure_service(session, item.raw_name, raw_category)
            item.status = "added"
            added += 1
            continue

        candidate = session.get(Service, item.suggested_service_id)
        if candidate is None:
            item.status = "deferred"  # suggestion points at a deleted service
            deferred += 1
            continue

        # Category-mismatch prefilter (free, no AI): a suggestion in a different category
        # is almost always a token-overlap false positive (e.g. an antibody test matched
        # to an MRI scan). Resolve it as a new entry instead of spending a verify call.
        if raw_category != candidate.category:
            _ensure_service(session, item.raw_name, raw_category)
            item.status = "added"
            added += 1
            continue

        if verifier is None:
            skipped += 1  # same-category gray zone genuinely needs AI — leave pending
            continue

        try:
            verdict = verifier.verify(item.raw_name, candidate.name_ru)
        except TransientVerifyError:
            # Rate-limited / transient — stop here, leaving this and the rest pending
            # so the next run resumes instead of burning them as "deferred".
            break
        if verdict is True:
            _add_alias(session, candidate.id, item.raw_name)
            item.status = "matched"
            aliased += 1
        elif verdict is False:
            _ensure_service(session, item.raw_name, raw_category)
            item.status = "added"
            added += 1
        else:
            item.status = "deferred"  # AI undecided — don't re-spam it
            deferred += 1

    return {"added": added, "aliased": aliased, "skipped": skipped, "deferred": deferred}
