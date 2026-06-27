"""One-command data setup for a fresh database (run after `alembic upgrade head`).

Reproducible and idempotent: catalog → embeddings → prices (every source × city) →
branches. Geocoding (Yandex) and LLM alias verification (Gemini) are optional follow-ups,
run separately so this stays key-free and fast:

    python -m app.scripts.setup_data
    python -m app.scripts.geocode_branches    # optional, needs YANDEX_GEOCODER_API_KEY
    python -m app.scripts.verify_suggestions  # optional, needs GEMINI_API_KEY
"""

from app.core.cities import CITIES
from app.db.session import SessionLocal
from app.scrapers.registry import available_sources
from app.scripts import embed_services, import_branches, import_catalog
from app.services.pipeline import run_source


def main() -> None:
    print("1/4 importing service catalog…")
    import_catalog.main()

    print("2/4 embedding catalog (skips if fastembed absent)…")
    embed_services.main()

    print("3/4 parsing prices for every source × city…")
    session = SessionLocal()
    try:
        for source in available_sources():
            for city in CITIES:
                try:
                    result = run_source(session, source, city.name, embedder=None)
                    session.commit()
                    if result.items_saved:
                        print(f"   {source} / {city.name}: {result.items_saved}")
                except Exception as exc:  # noqa: BLE001 — one city/source must not abort setup
                    session.rollback()
                    print(f"   {source} / {city.name}: failed ({exc})")
    finally:
        session.close()

    print("4/4 importing clinic branches (with coordinates)…")
    import_branches.main()

    print("setup complete.")


if __name__ == "__main__":
    main()
