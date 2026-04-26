"""
Voyage AI Embedding Service

Generates text embeddings using Voyage AI API (voyage-3 model, 1024 dimensions).
Used for semantic search in articles table via pgvector.

Free tier: 200M tokens — sufficient for personal use.
"""

import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_VOYAGE_API_URL = "https://api.voyageai.com/v1/embeddings"
_MODEL = "voyage-3"
_DIMENSIONS = 1024


async def embed_text(text: str) -> list[float] | None:
    """Generate embedding for a single text. Returns None on failure."""
    if not getattr(settings, "voyage_api_key", None):
        return None
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                _VOYAGE_API_URL,
                headers={"Authorization": f"Bearer {settings.voyage_api_key}"},
                json={"input": [text[:4000]], "model": _MODEL},
            )
            resp.raise_for_status()
            return resp.json()["data"][0]["embedding"]
    except Exception as exc:
        logger.warning("Voyage embedding failed: %s", exc)
        return None


async def embed_texts(texts: list[str]) -> list[list[float] | None]:
    """Generate embeddings for multiple texts in one API call (max 128)."""
    if not getattr(settings, "voyage_api_key", None):
        return [None] * len(texts)
    try:
        truncated = [t[:4000] for t in texts]
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                _VOYAGE_API_URL,
                headers={"Authorization": f"Bearer {settings.voyage_api_key}"},
                json={"input": truncated, "model": _MODEL},
            )
            resp.raise_for_status()
            data = resp.json()["data"]
            # data is sorted by index
            return [item["embedding"] for item in sorted(data, key=lambda x: x["index"])]
    except Exception as exc:
        logger.warning("Voyage batch embedding failed: %s", exc)
        return [None] * len(texts)
