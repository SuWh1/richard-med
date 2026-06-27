"""Local multilingual embeddings (offline only) for semantic service matching.

Uses fastembed (ONNX, no torch) with `multilingual-e5-small` (384-dim, matching the
`services.embedding` column). Never used in the user request path — only catalog
embedding (backfill) and the offline parse pipeline. Fully optional: if fastembed
isn't installed, `get_embedder()` returns None and the matcher skips the semantic stage.
"""

import logging
from collections.abc import Callable
from functools import lru_cache

logger = logging.getLogger(__name__)

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


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
    return TextEmbedding(model_name=MODEL_NAME)


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
