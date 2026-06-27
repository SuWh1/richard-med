"""Grow the catalog from the unmatched queue, then re-parse so new entries match.

- Without GEMINI_API_KEY: adds the "nothing similar" tests as new catalog entries (free).
- With GEMINI_API_KEY: also arbitrates the look-alikes (alias to existing vs new entry).

Offline + idempotent. Run after a parse to lift coverage toward 100% of each source.
"""

from app.core.cities import CITIES
from app.db.session import SessionLocal
from app.scrapers.registry import available_sources
from app.services.catalog_grow import grow_catalog
from app.services.llm_verify import get_verifier
from app.services.pipeline import run_source


def main() -> None:
    session = SessionLocal()
    try:
        result = grow_catalog(session, verifier=get_verifier())
        session.commit()
        print(
            f"catalog grown: +{result['added']} new entries, "
            f"+{result['aliased']} aliases, {result['skipped']} left for AI"
        )

        print("re-parsing so the new entries match…")
        for source in available_sources():
            for city in CITIES:
                try:
                    run_source(session, source, city.name, embedder=None)
                    session.commit()
                except Exception as exc:  # noqa: BLE001 — one city must not abort the rest
                    session.rollback()
                    print(f"  {source} / {city.name}: failed ({exc})")
        print("done.")
    finally:
        session.close()


if __name__ == "__main__":
    main()
