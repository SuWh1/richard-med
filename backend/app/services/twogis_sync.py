"""DB-facing side of the 2GIS integration: write firm matches and reviews to branches.

Offline/background only. `refresh_reviews` is the daily-parser hook — it needs no browser
because it works off the stable `twogis_firm_id` already stored on each branch.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import httpx
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import ClinicBranch, ClinicReview
from app.services.twogis import Firm, ReviewsResult, fetch_reviews

logger = logging.getLogger(__name__)
SOURCE = "2gis"


@dataclass
class RefreshStats:
    attempted: int = 0
    updated: int = 0
    reviews_written: int = 0
    failed: int = 0


def apply_firm_match(session: Session, branch: ClinicBranch, firm: Firm) -> None:
    """Persist a discovered firm-id + its catalog aggregate rating onto the branch."""
    branch.twogis_firm_id = firm.firm_id
    if firm.rating is not None:
        branch.rating = firm.rating
    if firm.reviews_count is not None:
        branch.reviews_count = firm.reviews_count
    branch.rating_synced_at = datetime.now(UTC)


def apply_reviews(
    session: Session, branch: ClinicBranch, result: ReviewsResult, now: datetime
) -> int:
    """Replace this branch's 2GIS reviews + refresh its aggregate rating. Idempotent."""
    if result.rating is not None:
        branch.rating = result.rating
    if result.reviews_count is not None:
        branch.reviews_count = result.reviews_count
    branch.rating_synced_at = now

    session.query(ClinicReview).filter(
        ClinicReview.branch_id == branch.id,
        ClinicReview.source == SOURCE,
    ).delete(synchronize_session=False)

    written = 0
    for item in result.reviews:
        session.add(
            ClinicReview(
                branch_id=branch.id,
                author=item.author,
                rating=item.rating,
                text=item.text,
                official_answer=item.official_answer,
                review_date=item.review_date,
                source=SOURCE,
                external_id=item.external_id,
                synced_at=now,
            )
        )
        written += 1
    return written


def _stale_branches(
    session: Session,
    ttl_days: int,
    limit: int | None,
    branch_ids: list[int] | None,
) -> list[ClinicBranch]:
    cutoff = datetime.now(UTC) - timedelta(days=ttl_days)
    stmt = (
        select(ClinicBranch)
        .where(
            ClinicBranch.twogis_firm_id.is_not(None),
            or_(
                ClinicBranch.rating_synced_at.is_(None),
                ClinicBranch.rating_synced_at < cutoff,
            ),
        )
        .order_by(ClinicBranch.rating_synced_at.asc().nulls_first())
    )
    if branch_ids is not None:
        stmt = stmt.where(ClinicBranch.id.in_(branch_ids))
    if limit:
        stmt = stmt.limit(limit)
    return list(session.scalars(stmt))


def refresh_reviews(
    session: Session,
    *,
    ttl_days: int | None = None,
    limit: int | None = None,
    branch_ids: list[int] | None = None,
    delay_sec: float = 0.3,
    client: httpx.Client | None = None,
) -> RefreshStats:
    """Step B for every branch with a firm_id whose reviews are missing/stale.

    No browser, no third-party calls in the user path — meant to run nightly alongside
    the price parser. Failures are isolated per branch so one bad firm never aborts the run.
    """
    ttl = ttl_days if ttl_days is not None else settings.TWOGIS_REVIEW_TTL_DAYS
    branches = _stale_branches(session, ttl, limit, branch_ids)
    stats = RefreshStats()
    owns = client is None
    client = client or httpx.Client(timeout=20.0)
    now = datetime.now(UTC)
    try:
        for branch in branches:
            stats.attempted += 1
            try:
                result = fetch_reviews(branch.twogis_firm_id, client=client)
            except (httpx.HTTPError, ValueError) as exc:
                stats.failed += 1
                logger.warning("2GIS reviews failed for branch %s: %s", branch.id, exc)
                continue
            stats.reviews_written += apply_reviews(session, branch, result, now)
            stats.updated += 1
            session.commit()
            if delay_sec:
                time.sleep(delay_sec)
    finally:
        if owns:
            client.close()
    logger.info(
        "2GIS reviews refresh: %d updated / %d attempted, %d reviews, %d failed",
        stats.updated, stats.attempted, stats.reviews_written, stats.failed,
    )
    return stats
