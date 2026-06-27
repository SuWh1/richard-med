"""Backfill catalog embeddings so the matcher's semantic stage can run.

Offline, idempotent (re-embeds all services). No-op if fastembed isn't installed.
"""

from app.db.session import SessionLocal
from app.models import Service
from app.services import embeddings

_BATCH = 256


def main() -> None:
    if not embeddings.available():
        print("fastembed not installed — skipping embeddings (semantic matching disabled).")
        return

    session = SessionLocal()
    try:
        services = session.query(Service).all()
        total = len(services)
        for start in range(0, total, _BATCH):
            chunk = services[start : start + _BATCH]
            vectors = embeddings.embed_passages([s.name_ru for s in chunk])
            for service, vector in zip(chunk, vectors, strict=True):
                service.embedding = vector
            session.commit()
            print(f"embedded {min(start + _BATCH, total)}/{total}")
    finally:
        session.close()


if __name__ == "__main__":
    main()
