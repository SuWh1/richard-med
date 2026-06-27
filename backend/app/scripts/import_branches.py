"""Import clinic branches (collection points) for every source that exposes them.

Offline, idempotent. For each branch-capable source × canonical city, fetch the points
and upsert them into clinic_branches (with coordinates). Re-running is safe.
"""

from app.core.cities import CITIES
from app.db.session import SessionLocal
from app.scrapers.registry import available_sources, get_adapter
from app.services.branches import sync_branches


def main() -> None:
    session = SessionLocal()
    total = 0
    try:
        for source_name in available_sources():
            adapter = get_adapter(source_name)
            brand = adapter.brand_name()
            if not brand:
                continue
            for city in CITIES:
                try:
                    hits = adapter.fetch_branches(city.name)
                except Exception as exc:  # noqa: BLE001 — one city must not abort the rest
                    print(f"  {source_name}/{city.name}: fetch failed: {exc}")
                    continue
                if not hits:
                    continue
                added = sync_branches(session, source_name, brand, hits)
                session.commit()
                total += added
                print(f"  {brand} / {city.name}: {len(hits)} points ({added} new)")
    finally:
        session.close()
    print(f"done: {total} new branches")


if __name__ == "__main__":
    main()
