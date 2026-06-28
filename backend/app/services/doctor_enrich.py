"""Offline enrichment of DOQ doctors: pull the "О враче" block, photos and reviews.

Runs as a background/manual pass — never in the user path (Rule 1). Each doctor is
isolated: one failing fetch logs and is skipped, the rest continue. Doctors already
parsed into the `doctors` table (base fields) are topped up here with their detail and
feedback layers.

DOQ endpoints (see also the doq-api-enrichment-endpoints memory):
- detail:    GET /api/v1/doctors/{doq_id}/?expand=details,photo_versions,videos
- feedbacks: GET /api/v1/feedbacks/?doctor={doq_id}  (paginated, 20/page)
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime

import httpx
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import Doctor, DoctorDetail, DoctorReview
from app.scrapers.http import PoliteClient

logger = logging.getLogger(__name__)

DETAIL_URL = "https://api.doq.kz/api/v1/doctors/{doq_id}/?expand=details,photo_versions,videos"
FEEDBACKS_URL = "https://api.doq.kz/api/v1/feedbacks/?doctor={doq_id}&limit=50"
# Cap review pages per doctor so one prolific doctor can't dominate a run.
_MAX_FEEDBACK_PAGES = 4


@dataclass(frozen=True)
class EnrichResult:
    doctors_enriched: int
    details_saved: int
    reviews_saved: int
    errors: int


def _parse_created_at(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _apply_detail(session: Session, doctor: Doctor, payload: dict) -> int:
    pv = payload.get("photo_versions") or {}
    gallery = pv.get("gallery_photos")
    doctor.photos = gallery if isinstance(gallery, list) and gallery else None
    if isinstance(payload.get("gender_display"), str):
        doctor.gender = payload["gender_display"]
    if isinstance(payload.get("languages"), list):
        doctor.languages = payload["languages"]

    session.execute(
        delete(DoctorDetail).where(DoctorDetail.doctor_id == doctor.id)
    )
    saved = 0
    for item in payload.get("details") or []:
        info = (item.get("info") or "").strip()
        if not info:
            continue
        session.add(
            DoctorDetail(
                doctor_id=doctor.id,
                detail_type=item.get("detail_type") or "",
                detail_type_id=item.get("detail_type_id"),
                info=info,
                year=(item.get("year") or "").strip() or None,
            )
        )
        saved += 1
    return saved


def _apply_feedbacks(session: Session, doctor: Doctor, client: PoliteClient) -> int:
    existing = set(
        session.scalars(
            select(DoctorReview.doq_feedback_id).where(
                DoctorReview.doctor_id == doctor.id
            )
        ).all()
    )
    saved = 0
    url: str | None = FEEDBACKS_URL.format(doq_id=doctor.doq_id)
    for _ in range(_MAX_FEEDBACK_PAGES):
        if not url:
            break
        payload = client.get_json(url)
        for item in payload.get("results") or []:
            fid = item.get("id")
            if not isinstance(fid, int) or fid in existing:
                continue
            existing.add(fid)
            session.add(
                DoctorReview(
                    doctor_id=doctor.id,
                    doq_feedback_id=fid,
                    score=item.get("score"),
                    text=(item.get("text") or "").strip() or None,
                    text_ru=(item.get("text_translated") or "").strip() or None,
                    service_name=item.get("service_name"),
                    client_name=None if item.get("is_anonymous") else item.get("client_name"),
                    waiting_time=item.get("waiting_time"),
                    clinic_reply=(item.get("clinic_reply") or "").strip() or None,
                    source=item.get("source"),
                    created_at=_parse_created_at(item.get("created_at")),
                )
            )
            saved += 1
        url = payload.get("next")
    return saved


def enrich_doctors(
    session: Session,
    *,
    limit: int | None = None,
    only_missing: bool = True,
    client: PoliteClient | None = None,
) -> EnrichResult:
    """Enrich doctors with detail + reviews. By default only those not yet enriched."""
    query = select(Doctor).order_by(Doctor.id)
    if only_missing:
        query = query.where(Doctor.enriched_at.is_(None))
    if limit is not None:
        query = query.limit(limit)
    doctors = list(session.scalars(query))
    if not doctors:
        return EnrichResult(0, 0, 0, 0)

    owns_client = client is None
    client = client or PoliteClient()
    enriched = details_saved = reviews_saved = errors = 0
    now = datetime.now(UTC)
    try:
        for doctor in doctors:
            # A SAVEPOINT isolates each doctor: a mid-doctor failure rolls back only this
            # doctor's partial writes, never the run's already-enriched doctors.
            try:
                with session.begin_nested():
                    detail = client.get_json(DETAIL_URL.format(doq_id=doctor.doq_id))
                    d = _apply_detail(session, doctor, detail)
                    r = _apply_feedbacks(session, doctor, client)
                    doctor.enriched_at = now
                details_saved += d
                reviews_saved += r
                enriched += 1
            except (httpx.HTTPError, ValueError, KeyError) as exc:
                logger.warning(
                    "doctor enrich failed for doq_id=%s (%s)",
                    doctor.doq_id,
                    type(exc).__name__,
                )
                errors += 1
    finally:
        if owns_client:
            client.close()
    return EnrichResult(enriched, details_saved, reviews_saved, errors)
