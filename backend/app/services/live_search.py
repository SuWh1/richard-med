"""Live on-miss lookup against DOQ.

When a user search finds no prices in the DB, we resolve the query to a single DOQ
catalog service, fetch its providers from DOQ's public API, persist everything as normal
source-backed records (raw document + raw items + catalog service + active prices), and
hand the new service id back so the endpoint can render real cards in the same response.

This is the *only* place the user path touches the network, and it is deliberately
narrow: DOQ only (KDL has no per-service query), one service, one page, hard time-box,
and a full DB write so the data is auditable and instantly available on the next search.
Any failure returns None and the caller falls back to the normal empty result.
"""

import logging
from datetime import UTC, datetime

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import RawPriceItem, ServiceAlias
from app.models.catalog import ServiceCategory
from app.scrapers.base import RawDocument
from app.scrapers.base import RawPriceItem as RawItem
from app.scrapers.doq import API_URL, _CITY_IDS, _TYPE_CATEGORY
from app.scrapers.http import content_hash
from app.services.catalog_grow import _ensure_service, _map_category
from app.services.normalization import canonical_clean
from app.services.pipeline import (
    _get_or_create_branch,
    _get_or_create_clinic,
    _parse_duration,
    _save_raw_document,
    _upsert_price,
)

logger = logging.getLogger(__name__)

SOURCE_NAME = "doq"
_SERVICES_URL = "https://api.doq.kz/api/v1/services/"
_DEFAULT_CITY = "Астана"
_PROVIDER_LIMIT = 50  # one page covers every clinic offering a single service


def _resolve_doq_service(client: httpx.Client, city_id: int, query: str) -> dict | None:
    """Map a typed query to one DOQ catalog service via its `?search=` endpoint.

    Prefers an exact name hit, then an adult (non-"детям") service, then the top result.
    """
    resp = client.get(
        _SERVICES_URL,
        params={"city": city_id, "search": query, "limit": 10},
        headers={"Accept": "application/json"},
    )
    resp.raise_for_status()
    results = [r for r in resp.json().get("results", []) if r.get("name")]
    if not results:
        return None
    cleaned = canonical_clean(query)
    exact = [r for r in results if canonical_clean(r["name"]) == cleaned]
    if exact:
        return exact[0]
    adult = [r for r in results if "детям" not in r["name"].lower()]
    return (adult or results)[0]


def _fetch_providers(client: httpx.Client, city_id: int, doq_service_id: int) -> dict:
    resp = client.get(
        API_URL,
        params={
            "city": city_id,
            "service": doq_service_id,
            "expand": "services,clinic_branches",
            "limit": _PROVIDER_LIMIT,
        },
        headers={"Accept": "application/json"},
    )
    resp.raise_for_status()
    return resp.json()


def _cheapest_offers(payload: dict, doq_service_id: int) -> list[dict]:
    """Extract one offer per clinic (the cheapest) for exactly the queried service."""
    by_clinic: dict[str, dict] = {}
    for doctor in payload.get("results", []):
        branches = {b["id"]: b for b in doctor.get("clinic_branches", [])}
        for svc in doctor.get("services", []):
            if not svc.get("is_active", True):
                continue
            if (svc.get("service") or {}).get("id") != doq_service_id:
                continue
            branch = branches.get(svc.get("clinic_branch"))
            if branch is None:
                continue
            price = svc.get("discount_price") or svc.get("base_price")
            if not price:
                continue
            clinic_name = branch.get("name") or SOURCE_NAME
            current = by_clinic.get(clinic_name)
            if current is not None and current["price"] <= int(price):
                continue
            location = branch.get("location") or {}
            phones = branch.get("phones") or []
            by_clinic[clinic_name] = {
                "clinic_name": clinic_name,
                "price": int(price),
                "source_url": f"https://doq.kz/doctor/{doctor.get('slug', '')}",
                "doctor": doctor.get("name"),
                "address": branch.get("address"),
                "lat": location.get("lat"),
                "lng": location.get("lng"),
                "phone": phones[0] if phones else None,
            }
    return list(by_clinic.values())


def _record_alias(session: Session, service_id: int, alias: str) -> None:
    alias = " ".join((alias or "").split())
    if not alias:
        return
    exists = session.scalars(
        select(ServiceAlias.id).where(
            ServiceAlias.service_id == service_id, ServiceAlias.alias == alias
        )
    ).first()
    if not exists:
        session.add(
            ServiceAlias(service_id=service_id, alias=alias, source="live", confidence=0.9)
        )


def live_fetch_doq(session: Session, query: str, city: str | None) -> int | None:
    """Fetch the queried service from DOQ live, persist it, return its catalog id.

    Returns None (no rows written) when live lookup is disabled, the city is outside
    DOQ's coverage, nothing matches, or any network/parse error occurs — the caller
    then serves the normal empty result.
    """
    if not settings.LIVE_FALLBACK_ENABLED:
        return None
    city = city or _DEFAULT_CITY
    city_id = _CITY_IDS.get(city)
    if city_id is None:
        return None

    try:
        with httpx.Client(timeout=settings.LIVE_FALLBACK_TIMEOUT_SEC) as client:
            doq_service = _resolve_doq_service(client, city_id, query)
            if doq_service is None:
                return None
            payload = _fetch_providers(client, city_id, doq_service["id"])
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning("live doq lookup failed for %r/%s (%s)", query, city, type(exc).__name__)
        return None

    offers = _cheapest_offers(payload, doq_service["id"])
    if not offers:
        return None

    name = doq_service["name"]
    category = _map_category(
        _TYPE_CATEGORY.get(doq_service.get("type")), name, fallback=ServiceCategory.other
    )

    try:
        return _persist(session, query, city, name, category, offers)
    except Exception:  # noqa: BLE001 — a live miss must never break the search response
        logger.exception("live doq persist failed for %r/%s", query, city)
        session.rollback()
        return None


def _persist(
    session: Session,
    query: str,
    city: str,
    name: str,
    category: ServiceCategory,
    offers: list[dict],
) -> int:
    now = datetime.now(UTC)
    service = _ensure_service(session, name, category)
    if canonical_clean(query) != canonical_clean(name):
        _record_alias(session, service.id, query)

    raw_html = '{"source": "live", "service": %s}' % service.id
    doc = RawDocument(
        source_name=SOURCE_NAME,
        source_url=f"https://doq.kz/search?q={name}",
        city=city,
        raw_html=raw_html,
        content_hash=content_hash(raw_html + now.isoformat()),
        status_code=200,
        fetched_at="",
    )
    raw_doc = _save_raw_document(session, SOURCE_NAME, doc)

    for offer in offers:
        meta = {
            "doq_service_name": name,
            "doctor": offer["doctor"],
            "city": city,
            "address": offer["address"],
            "lat": offer["lat"],
            "lng": offer["lng"],
            "phone": offer["phone"],
            "live": True,
        }
        raw_row = RawPriceItem(
            raw_document_id=raw_doc.id,
            clinic_raw=offer["clinic_name"],
            service_name_raw=name,
            price_raw=str(offer["price"]),
            metadata_json=meta,
        )
        session.add(raw_row)
        session.flush()

        clinic = _get_or_create_clinic(session, SOURCE_NAME, offer["clinic_name"], None)
        branch = None
        if meta["address"] or (meta["lat"] and meta["lng"]):
            branch = _get_or_create_branch(session, clinic.id, meta, city)
        duration_min, duration_max = _parse_duration(None)
        item = RawItem(
            source_url=offer["source_url"],
            clinic_raw=offer["clinic_name"],
            service_name_raw=name,
            price_raw=str(offer["price"]),
            metadata=meta,
        )
        _upsert_price(
            session,
            clinic_id=clinic.id,
            branch_id=branch.id if branch else None,
            service_id=service.id,
            price_kzt=offer["price"],
            item=item,
            raw_item_id=raw_row.id,
            content_hash=raw_doc.content_hash,
            confidence=1.0,
            method="live",
            duration_min=duration_min,
            duration_max=duration_max,
            city=city,
            now=now,
        )

    session.commit()
    return service.id
