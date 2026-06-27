"""Grow the catalog from real source data so every scraped service can be shown.

When a scraped test has no catalog home, we add it as a new entry; when it has a
look-alike, an LLM arbitrates alias-vs-new. The given catalog is the seed, not the cap
(the brief asks the team to *form* the catalog). Offline + idempotent.
"""

import hashlib
import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import RawPriceItem, Service, ServiceAlias, ServiceCategory, UnmatchedService
from app.services.normalization import canonical_clean

logger = logging.getLogger(__name__)

_CATEGORY_KEYWORDS = (
    (ServiceCategory.diagnostic, ("узи", "кт", "мрт", "рентген", "эндоскоп", "диагност")),
    (ServiceCategory.doctor_visit, ("прием", "приём", "консультац", "врач")),
    (ServiceCategory.procedure, ("массаж", "процедур", "инъекц", "перевяз", "забор")),
)


class _Verifier:
    def verify(self, raw_name: str, candidate_name: str) -> bool | None: ...


def _map_category(raw_category: str | None) -> ServiceCategory:
    text = (raw_category or "").lower()
    for category, keywords in _CATEGORY_KEYWORDS:
        if any(keyword in text for keyword in keywords):
            return category
    return ServiceCategory.laboratory


def _category_for(session: Session, raw_item_id: int | None) -> ServiceCategory:
    if raw_item_id is None:
        return ServiceCategory.laboratory
    item = session.get(RawPriceItem, raw_item_id)
    raw_category = (item.metadata_json or {}).get("category") if item else None
    return _map_category(raw_category)


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


def grow_catalog(session: Session, verifier: _Verifier | None = None) -> dict[str, int]:
    """Process the pending unmatched queue into new catalog entries or aliases."""
    rows = session.scalars(
        select(UnmatchedService).where(UnmatchedService.status == "pending")
    ).all()
    added = aliased = skipped = 0

    for item in rows:
        if item.suggested_service_id is None:
            _ensure_service(session, item.raw_name, _category_for(session, item.raw_item_id))
            item.status = "added"
            added += 1
            continue

        if verifier is None:
            skipped += 1
            continue

        candidate = session.get(Service, item.suggested_service_id)
        verdict = verifier.verify(item.raw_name, candidate.name_ru) if candidate else None
        if verdict is True:
            _add_alias(session, candidate.id, item.raw_name)
            item.status = "matched"
            aliased += 1
        elif verdict is False:
            _ensure_service(session, item.raw_name, _category_for(session, item.raw_item_id))
            item.status = "added"
            added += 1
        else:
            skipped += 1

    return {"added": added, "aliased": aliased, "skipped": skipped}
