import logging
import re
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Clinic,
    ClinicBranch,
    ClinicServicePrice,
    ParseRun,
    PriceHistory,
    RawDocument,
    RawPriceItem,
    UnmatchedService,
)
from app.scrapers.base import RawPriceItem as RawItem
from app.scrapers.registry import get_adapter
from app.services.normalization import FUZZY_AUTO, ServiceMatcher

logger = logging.getLogger(__name__)
# Only auto-save confident matches; 0.75–0.88 "suggest" matches go to the queue (§9).
MATCH_FLOOR = FUZZY_AUTO

_DURATION_RE = re.compile(r"\d+")


def _parse_duration(raw: str | None) -> tuple[int | None, int | None]:
    """Turn '1' → (1, 1) and '1-3' → (1, 3); unparseable → (None, None)."""
    if not raw:
        return None, None
    nums = _DURATION_RE.findall(raw)
    if not nums:
        return None, None
    if len(nums) == 1:
        return int(nums[0]), int(nums[0])
    return int(nums[0]), int(nums[1])


@dataclass(frozen=True)
class RunResult:
    run_id: int
    source_name: str
    city: str
    status: str
    items_found: int
    items_saved: int
    unmatched: int
    errors: str | None


def _get_or_create_clinic(
    session: Session, source_name: str, name: str, website: str | None
) -> Clinic:
    clinic = session.scalars(
        select(Clinic).where(Clinic.source_name == source_name, Clinic.name == name)
    ).first()
    if clinic is None:
        clinic = Clinic(name=name, source_name=source_name, website_url=website)
        session.add(clinic)
        session.flush()
    return clinic


def _get_or_create_branch(
    session: Session, clinic_id: int, meta: dict, city: str
) -> ClinicBranch | None:
    branch_city = meta.get("city") or city
    address = meta.get("address")
    query = select(ClinicBranch).where(
        ClinicBranch.clinic_id == clinic_id, ClinicBranch.city == branch_city
    )
    if address:
        query = query.where(ClinicBranch.address == address)
    branch = session.scalars(query).first()
    if branch is None:
        branch = ClinicBranch(
            clinic_id=clinic_id,
            city=branch_city,
            address=address,
            lat=meta.get("lat"),
            lng=meta.get("lng"),
            phone=meta.get("phone"),
        )
        session.add(branch)
        session.flush()
    return branch


def _save_raw_document(session: Session, source_name: str, doc) -> RawDocument:
    existing = session.scalars(
        select(RawDocument).where(
            RawDocument.source_url == doc.source_url,
            RawDocument.content_hash == doc.content_hash,
        )
    ).first()
    if existing is not None:
        return existing
    row = RawDocument(
        source_name=source_name,
        source_url=doc.source_url,
        city=doc.city,
        content_hash=doc.content_hash,
        raw_html=doc.raw_html,
        status_code=doc.status_code,
        fetched_at=datetime.now(UTC),
    )
    session.add(row)
    session.flush()
    return row


def _upsert_price(
    session: Session,
    *,
    clinic_id: int,
    branch_id: int | None,
    service_id: int,
    price_kzt: int,
    item: RawItem,
    raw_item_id: int,
    content_hash: str,
    confidence: float,
    method: str,
    duration_min: int | None,
    duration_max: int | None,
    now: datetime,
) -> tuple[bool, int | None]:
    """Insert or version a price. Returns (price_id_seen, existing_id_deactivated_or_none)."""
    existing = session.scalars(
        select(ClinicServicePrice).where(
            ClinicServicePrice.clinic_id == clinic_id,
            ClinicServicePrice.service_id == service_id,
            ClinicServicePrice.branch_id == branch_id,
            ClinicServicePrice.is_active.is_(True),
        )
    ).first()

    if existing is not None and existing.price_kzt == price_kzt:
        existing.parsed_at = now
        existing.source_url = item.source_url
        existing.match_confidence = confidence
        existing.match_method = method
        existing.duration_min = duration_min
        existing.duration_max = duration_max
        return existing.id, existing.id

    if existing is not None:
        session.add(
            PriceHistory(
                source_key=f"{clinic_id}:{service_id}:{branch_id}",
                old_price=existing.price_kzt,
                new_price=price_kzt,
                percent_change=round(
                    (price_kzt - existing.price_kzt) / existing.price_kzt * 100, 2
                )
                if existing.price_kzt
                else None,
                changed_at=now,
            )
        )
        existing.is_active = False

    fresh = ClinicServicePrice(
        clinic_id=clinic_id,
        branch_id=branch_id,
        service_id=service_id,
        raw_price_item_id=raw_item_id,
        price_kzt=price_kzt,
        duration_min=duration_min,
        duration_max=duration_max,
        service_name_raw=item.service_name_raw,
        content_hash=content_hash,
        match_confidence=confidence,
        match_method=method,
        source_url=item.source_url,
        parsed_at=now,
        is_active=True,
    )
    session.add(fresh)
    session.flush()
    return fresh.id, existing.id if existing else None


def run_source(
    session: Session,
    source_name: str,
    city: str,
    adapter=None,
    publish: bool = False,
    embedder=None,
) -> RunResult:
    """Run one source for one city through the full pipeline with error isolation.

    `adapter` is injectable for tests; in production it is resolved from the registry.
    `embedder` enables the matcher's semantic stage (offline only); tests leave it None.
    When `publish` is set (background runs), the "running" row is committed up front so
    pollers see live progress; tests leave it off to keep transaction isolation.
    """
    now = datetime.now(UTC)
    run = ParseRun(source_name=source_name, city=city, status="running", started_at=now)
    session.add(run)
    session.flush()
    if publish:
        session.commit()

    if adapter is None:
        adapter = get_adapter(source_name)
    items_found = 0
    seen_price_ids: set[int] = set()
    # One active price per (clinic, service, branch) per run; keep the cheapest so
    # distinct raw names mapping to the same catalog service don't thrash history.
    run_prices: dict[tuple[int, int, int | None], ClinicServicePrice] = {}
    unmatched = 0
    errors: list[str] = []

    try:
        docs = adapter.fetch(city)
    except Exception as exc:  # noqa: BLE001 — one source failing must not abort others
        logger.exception("fetch failed for %s/%s", source_name, city)
        run.status = "failed"
        run.finished_at = datetime.now(UTC)
        run.errors = f"fetch: {exc}"
        session.flush()
        return RunResult(run.id, source_name, city, "failed", 0, 0, 0, str(exc))

    matcher = ServiceMatcher(session, embedder=embedder)
    queued_unmatched = set(
        session.scalars(select(UnmatchedService.raw_name)).all()
    )

    for doc in docs:
        try:
            raw_doc = _save_raw_document(session, source_name, doc)
            parsed = [adapter.clean(it) for it in adapter.parse(doc)]
        except Exception as exc:  # noqa: BLE001
            logger.exception("parse failed for %s", doc.source_url)
            errors.append(f"{doc.source_url}: {exc}")
            continue

        for item in parsed:
            items_found += 1
            try:
                price = int(item.price_raw) if item.price_raw else 0
                if price <= 0 or not item.service_name_raw:
                    continue

                raw_row = RawPriceItem(
                    raw_document_id=raw_doc.id,
                    clinic_raw=item.clinic_raw,
                    service_name_raw=item.service_name_raw,
                    price_raw=item.price_raw,
                    duration_raw=item.duration_raw,
                    metadata_json=item.metadata or None,
                )
                session.add(raw_row)
                session.flush()

                result = matcher.match(item.service_name_raw)
                # Semantic matches are suggestions only — generic embeddings can't reliably
                # distinguish specific lab analytes, so they go to the review queue with a
                # suggested_service_id rather than auto-publishing a possibly-wrong price.
                auto_match = (
                    result.service_id is not None
                    and result.confidence >= MATCH_FLOOR
                    and result.method != "semantic"
                )
                if not auto_match:
                    if item.service_name_raw not in queued_unmatched:
                        session.add(
                            UnmatchedService(
                                raw_item_id=raw_row.id,
                                raw_name=item.service_name_raw,
                                suggested_service_id=result.service_id,
                                confidence=result.confidence,
                            )
                        )
                        queued_unmatched.add(item.service_name_raw)
                        unmatched += 1
                    continue

                clinic = _get_or_create_clinic(
                    session, source_name, item.clinic_raw or source_name, None
                )
                branch = _get_or_create_branch(session, clinic.id, item.metadata or {}, city)
                branch_id = branch.id if branch else None
                key = (clinic.id, result.service_id, branch_id)

                duration_min, duration_max = _parse_duration(item.duration_raw)
                duplicate = run_prices.get(key)
                if duplicate is not None:
                    if price < duplicate.price_kzt:
                        duplicate.price_kzt = price
                        duplicate.source_url = item.source_url
                        duplicate.service_name_raw = item.service_name_raw
                        duplicate.match_confidence = result.confidence
                        duplicate.match_method = result.method
                        duplicate.raw_price_item_id = raw_row.id
                        duplicate.duration_min = duration_min
                        duplicate.duration_max = duration_max
                    continue

                price_id, _ = _upsert_price(
                    session,
                    clinic_id=clinic.id,
                    branch_id=branch_id,
                    service_id=result.service_id,
                    price_kzt=price,
                    item=item,
                    raw_item_id=raw_row.id,
                    content_hash=raw_doc.content_hash,
                    confidence=result.confidence,
                    method=result.method,
                    duration_min=duration_min,
                    duration_max=duration_max,
                    now=now,
                )
                seen_price_ids.add(price_id)
                run_prices[key] = session.get(ClinicServicePrice, price_id)
            except Exception as exc:  # noqa: BLE001
                logger.exception("item failed: %s", item.service_name_raw)
                errors.append(f"{item.service_name_raw}: {exc}")

    _deactivate_stale(session, source_name, city, seen_price_ids, now)

    run.status = "partial" if errors else "success"
    run.finished_at = datetime.now(UTC)
    run.items_found = items_found
    run.items_saved = len(seen_price_ids)
    run.errors = "\n".join(errors[:20]) or None
    session.flush()
    return RunResult(
        run_id=run.id,
        source_name=source_name,
        city=city,
        status=run.status,
        items_found=items_found,
        items_saved=len(seen_price_ids),
        unmatched=unmatched,
        errors=run.errors,
    )


def _deactivate_stale(
    session: Session, source_name: str, city: str, seen_ids: set[int], now: datetime
) -> None:
    """A price that vanished from the source this run is deactivated, not deleted."""
    clinic_ids = session.scalars(
        select(Clinic.id).where(Clinic.source_name == source_name)
    ).all()
    if not clinic_ids:
        return
    active = session.scalars(
        select(ClinicServicePrice).where(
            ClinicServicePrice.clinic_id.in_(clinic_ids),
            ClinicServicePrice.is_active.is_(True),
        )
    ).all()
    for price in active:
        if price.id not in seen_ids and (price.branch is None or price.branch.city == city):
            price.is_active = False
