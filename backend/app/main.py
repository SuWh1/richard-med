import logging
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.session import SessionLocal
from app.services import embeddings
from app.services.catalog_import import ensure_catalog_loaded
from app.services.scheduler import create_scheduler

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    session = SessionLocal()
    try:
        stats = ensure_catalog_loaded(session)
        if stats is not None:
            logger.info(
                "Catalog was empty; imported %d services (%d aliases) from blueprint.",
                stats.services_inserted,
                stats.aliases_seeded,
            )
    except Exception:
        session.rollback()
        logger.exception("Catalog auto-import on startup failed; continuing without it.")
    finally:
        session.close()

    # Warm up off the startup path: a slow/failed model download must never block the
    # app from serving. The model still lazy-loads on first query if this hasn't finished.
    def _warmup():
        try:
            if embeddings.warmup():
                logger.info("Embedding model pre-loaded; semantic search ready.")
        except Exception:
            logger.exception("Embedding warmup failed; model will load on first query.")

    threading.Thread(target=_warmup, name="embeddings-warmup", daemon=True).start()

    scheduler = create_scheduler()
    try:
        yield
    finally:
        if scheduler is not None:
            scheduler.shutdown(wait=False)


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=settings.BACKEND_CORS_ORIGIN_REGEX or None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
