"""Seed clinic-branch ratings + reviews from a pre-collected 2GIS snapshot (offline).

The snapshot is gathered out-of-band and committed as JSON; this loader never fetches
from 2GIS at runtime (keeps the user/search path free of third-party calls). Idempotent:
re-running replaces a branch's 2GIS reviews rather than duplicating them.
"""

import json
import logging
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import Clinic, ClinicBranch, ClinicReview

logger = logging.getLogger(__name__)

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "data" / "2gis_reviews.json"
SOURCE = "2gis"


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).replace(tzinfo=UTC)
    except ValueError:
        return None


def parse_review(raw: dict) -> dict:
    return {
        "author": raw.get("user"),
        "rating": raw.get("rating"),
        "text": raw.get("text"),
        "review_date": _parse_date(raw.get("date")),
    }


def row_rating(row: dict) -> tuple[int, str | None, float | None, int | None] | None:
    """(branch_id, firm_id, rating, reviews_count) for a resolved row, else None."""
    if row.get("status") != "ok":
        return None
    try:
        branch_id = int(row["id"])
    except (KeyError, ValueError, TypeError):
        return None
    return branch_id, row.get("firm_id"), row.get("rating"), row.get("reviews_count")


def _branch_index(session) -> dict[tuple[str, str | None, str | None], int]:
    """(clinic_name, city, address) -> branch_id. Stable across DB re-imports, where
    autoincrement ids in the snapshot would otherwise drift onto the wrong clinic."""
    rows = session.execute(
        select(Clinic.name, ClinicBranch.city, ClinicBranch.address, ClinicBranch.id)
        .join(ClinicBranch, ClinicBranch.clinic_id == Clinic.id)
    ).all()
    return {(name, city, address): bid for name, city, address, bid in rows}


def load(path: Path = DEFAULT_PATH) -> tuple[int, int]:
    rows = json.loads(Path(path).read_text(encoding="utf-8"))
    session = SessionLocal()
    branches_updated = 0
    reviews_inserted = 0
    now = datetime.now(UTC)
    try:
        index = _branch_index(session)
        for row in rows:
            parsed = row_rating(row)
            if parsed is None:
                continue
            _, firm_id, rating, reviews_count = parsed
            key = (row.get("clinic"), row.get("city"), row.get("address"))
            branch_id = index.get(key)
            if branch_id is None:
                continue
            branch = session.get(ClinicBranch, branch_id)
            if branch is None:
                continue
            branch.twogis_firm_id = firm_id
            branch.rating = rating
            branch.reviews_count = reviews_count
            branch.rating_synced_at = now
            branches_updated += 1

            session.query(ClinicReview).filter(
                ClinicReview.branch_id == branch_id,
                ClinicReview.source == SOURCE,
            ).delete(synchronize_session=False)
            for raw in row.get("sample") or []:
                fields = parse_review(raw)
                if not fields["text"]:
                    continue
                session.add(
                    ClinicReview(
                        branch_id=branch_id,
                        source=SOURCE,
                        synced_at=now,
                        **fields,
                    )
                )
                reviews_inserted += 1
        session.commit()
    finally:
        session.close()
    return branches_updated, reviews_inserted


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    branches, reviews = load()
    logger.info("2GIS seed: %d branches rated, %d reviews inserted", branches, reviews)
    print(f"2GIS seed: {branches} branches rated, {reviews} reviews inserted")


if __name__ == "__main__":
    main()
