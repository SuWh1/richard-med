"""Local multilingual embeddings for semantic service matching.

Uses fastembed (ONNX, no torch) with `multilingual-e5-small` (384-dim, matching the
`services.embedding` column). Used for catalog embedding (backfill), the offline parse
pipeline, and the semantic fallback in user search (only when lexical+fuzzy miss — the
model is local, so no third-party call). The model loads lazily on first use and is
cached; `warmup()` pre-loads it at startup so the first query isn't slow. Fully optional:
if fastembed isn't installed, `get_embedder()` returns None and the matcher skips the
semantic stage.
"""

import logging
import os
from collections.abc import Callable
from functools import lru_cache

logger = logging.getLogger(__name__)

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# Persist the downloaded model outside the container's ephemeral FS so a rebuild
# doesn't re-download it (see the matching volume in docker-compose.yml).
CACHE_DIR = os.getenv("FASTEMBED_CACHE_DIR") or None


def available() -> bool:
    try:
        import fastembed  # noqa: F401
    except ImportError:
        return False
    return True


@lru_cache(maxsize=1)
def _model():
    from fastembed import TextEmbedding

    logger.info("loading embedding model %s", MODEL_NAME)
    return TextEmbedding(model_name=MODEL_NAME, cache_dir=CACHE_DIR)


def embed_passages(texts: list[str]) -> list[list[float]]:
    """Embed catalog service names."""
    return [vec.tolist() for vec in _model().embed(texts)]


def embed_query(text: str) -> list[float]:
    """Embed a raw scraped name."""
    return next(iter(_model().embed([text]))).tolist()


def get_embedder() -> Callable[[str], list[float]] | None:
    """The query embedder for the matcher, or None when embeddings are unavailable."""
    if not available():
        return None
    return embed_query


def warmup() -> bool:
    """Pre-load the model so the first search doesn't pay the load/download cost.

    No-op (returns False) when fastembed isn't installed. Idempotent: `_model()` is
    cached, so repeated calls are cheap.
    """
    if not available():
        return False
    _model()
    return True
