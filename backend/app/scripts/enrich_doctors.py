"""Enrich parsed DOQ doctors with their "О враче" details, photos and reviews.

Run after a DOQ parse seeds the `doctors` table:

    python -m app.scripts.enrich_doctors            # all not-yet-enriched doctors
    python -m app.scripts.enrich_doctors --limit 50 # cap the batch
    python -m app.scripts.enrich_doctors --all      # re-enrich everyone (refresh)
"""

import argparse

from app.db.session import SessionLocal
from app.services.doctor_enrich import enrich_doctors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument(
        "--all",
        action="store_true",
        help="re-enrich every doctor, not just those missing enrichment",
    )
    args = parser.parse_args()

    session = SessionLocal()
    try:
        result = enrich_doctors(
            session, limit=args.limit, only_missing=not args.all
        )
        session.commit()
    finally:
        session.close()

    print(
        f"doctors enriched: {result.doctors_enriched}, "
        f"details: +{result.details_saved}, reviews: +{result.reviews_saved}, "
        f"errors: {result.errors}"
    )


if __name__ == "__main__":
    main()
