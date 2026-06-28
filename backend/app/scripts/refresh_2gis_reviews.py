"""Refresh 2GIS ratings + reviews for every branch that already has a firm_id.

Step B only — plain HTTP to the public reviews API, no browser. Safe to run nightly
next to the price parser; this is the job that keeps ratings current. Firm-id discovery
(Step A, the browser collector) is a separate, occasional job: see discover_2gis_firms.py.

    python -m app.scripts.refresh_2gis_reviews            # all stale (ttl from settings)
    python -m app.scripts.refresh_2gis_reviews --all      # ignore ttl, refresh everything
    python -m app.scripts.refresh_2gis_reviews --limit 50
"""

import argparse
import logging

from app.db.session import SessionLocal
from app.services.twogis_sync import refresh_reviews


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh 2GIS ratings/reviews (Step B).")
    parser.add_argument("--all", action="store_true", help="ignore freshness TTL")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--delay", type=float, default=0.3, help="seconds between calls")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    session = SessionLocal()
    try:
        stats = refresh_reviews(
            session,
            ttl_days=0 if args.all else None,
            limit=args.limit,
            delay_sec=args.delay,
        )
    finally:
        session.close()
    print(
        f"2GIS refresh: {stats.updated}/{stats.attempted} branches updated, "
        f"{stats.reviews_written} reviews written, {stats.failed} failed"
    )


if __name__ == "__main__":
    main()
