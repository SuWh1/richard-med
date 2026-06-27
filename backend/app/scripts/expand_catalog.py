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
        # Phase 1: the "nothing similar" tests — add all at once (no AI, one transaction).
        base = grow_catalog(session)
        session.commit()
        print(f"catalog grown: +{base['added']} new entries (nothing similar)")

        # Phase 2: the look-alikes — AI-arbitrated in committed batches (short transactions).
        verifier = get_verifier()
        if verifier is not None:
            aliased = added = deferred = 0
            while True:
                batch = grow_catalog(session, verifier=verifier, limit=25)
                session.commit()
                aliased += batch["aliased"]
                added += batch["added"]
                deferred += batch["deferred"]
                if batch["aliased"] + batch["added"] + batch["deferred"] == 0:
                    break
            print(f"AI gray-zone: +{aliased} aliases, +{added} entries, {deferred} undecided")
        else:
            print("(no GEMINI_API_KEY — look-alikes left pending)")

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
