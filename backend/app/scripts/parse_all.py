"""Parse every source × city into the DB — no AI, no network enrichment.

Catalog import (reads the blueprint xlsx) feeds the matcher, then each source is run
for each city with the semantic stage off (`embedder=None`), so no embedding model loads
and no third-party AI is called. Matching is exact → alias → fuzzy only. Idempotent.

    python -m app.scripts.parse_all          # all sources, all cities
    python -m app.scripts.parse_all kdl_olymp doq   # only the named sources
"""

import sys

from app.core.cities import CITIES
from app.db.session import SessionLocal
from app.scrapers.registry import available_sources
from app.scripts import import_catalog
from app.services.pipeline import run_source


def main(sources: list[str] | None = None) -> None:
    sources = sources or available_sources()

    print("importing service catalog…")
    import_catalog.main()

    print(f"parsing {len(sources)} source(s) × {len(CITIES)} cities (no AI)…")
    session = SessionLocal()
    saved_total = 0
    try:
        for source in sources:
            for city in CITIES:
                try:
                    result = run_source(session, source, city.name, embedder=None)
                    session.commit()
                    saved_total += result.items_saved
                    if result.items_saved:
                        print(f"   {source} / {city.name}: {result.items_saved}")
                except Exception as exc:  # noqa: BLE001 — one city/source must not abort the run
                    session.rollback()
                    print(f"   {source} / {city.name}: failed ({exc})")
    finally:
        session.close()

    print(f"done — {saved_total} prices saved.")


if __name__ == "__main__":
    main(sys.argv[1:] or None)
