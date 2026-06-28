"""Backfill clinic branches for sources that publish prices but no locations.

Хеликс ships a city-wide price list with no addresses, so its cards had no point to
route/zoom to. This seeds its real collection points (geocoded, with 2GIS ratings) from
a committed snapshot — offline, never fetched in the user path. Idempotent: a branch is
keyed by its 2GIS firm id, so re-running won't duplicate.
"""

import json
import logging
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import Clinic, ClinicBranch, ClinicReview
from app.scripts.load_2gis_reviews import parse_review

logger = logging.getLogger(__name__)

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "data" / "helix_branches.json"
SOURCE = "2gis"


def load(path: Path = DEFAULT_PATH) -> tuple[int, int]:
    rows = json.loads(Path(path).read_text(encoding="utf-8"))
    session = SessionLocal()
    branches_added = 0
    reviews_added = 0
    now = datetime.now(UTC)
    try:
        for row in rows:
            clinic = session.scalars(
                select(Clinic).where(Clinic.name == row["clinic_name"])
            ).first()
            if clinic is None or not row.get("twogis_firm_id"):
                continue
            exists = session.scalars(
                select(ClinicBranch.id).where(
                    ClinicBranch.twogis_firm_id == row["twogis_firm_id"]
                )
            ).first()
            if exists is not None:
                continue
            branch = ClinicBranch(
                clinic_id=clinic.id,
                city=row["city"],
                address=row.get("address"),
                lat=row.get("lat"),
                lng=row.get("lng"),
                twogis_firm_id=row["twogis_firm_id"],
                rating=row.get("rating"),
                reviews_count=row.get("reviews_count"),
                rating_synced_at=now,
            )
            session.add(branch)
            session.flush()
            branches_added += 1
            for raw in row.get("sample") or []:
                fields = parse_review(raw)
                if not fields["text"]:
                    continue
                session.add(
                    ClinicReview(
                        branch_id=branch.id, source=SOURCE, synced_at=now, **fields
                    )
                )
                reviews_added += 1
        session.commit()
    finally:
        session.close()
    return branches_added, reviews_added


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    branches, reviews = load()
    print(f"Branch backfill: {branches} branches added, {reviews} reviews inserted")


if __name__ == "__main__":
    main()
