"""Backfill clinic-branch coordinates via the Yandex Geocoder (offline, key-gated).

Run manually or from a scheduled job. No key configured → no-op, leaving seeded demo
coordinates untouched.
"""

import logging
import time

from sqlalchemy import or_, select

from app.core.config import settings
from app.db.session import SessionLocal
from app.models import ClinicBranch
from app.scrapers.http import PoliteClient
from app.services.geocoding import (
    GeocoderRateLimited,
    YandexGeocoder,
    geocode_branch,
)

logger = logging.getLogger(__name__)


def main() -> None:
    if not settings.YANDEX_GEOCODER_API_KEY:
        print("YANDEX_GEOCODER_API_KEY not set — skipping geocoding (using seeded coords).")
        return

    session = SessionLocal()
    client = PoliteClient(delay=1.0)
    geocoder = YandexGeocoder(
        settings.YANDEX_GEOCODER_API_KEY, settings.YANDEX_GEOCODER_URL, client
    )
    updated = 0
    try:
        branches = session.scalars(
            select(ClinicBranch).where(
                ClinicBranch.address.is_not(None),
                or_(ClinicBranch.lat.is_(None), ClinicBranch.lng.is_(None)),
            )
        ).all()
        for branch in branches:
            try:
                if geocode_branch(branch, geocoder):
                    updated += 1
            except GeocoderRateLimited:
                logger.warning("rate limited — backing off 5s")
                time.sleep(5)
        session.commit()
    finally:
        client.close()
        session.close()

    print(f"geocoded {updated} branch(es)")


if __name__ == "__main__":
    main()
