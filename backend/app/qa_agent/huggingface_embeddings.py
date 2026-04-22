"""
Hugging Face Embeddings Service - Free Alternative to OpenAI
"""

import asyncio
import logging
from typing import List, Optional

import aiohttp

logger = logging.getLogger(__name__)


class HuggingFaceEmbeddingService:
    """
    Free embedding service using Hugging Face Inference API.
    Uses sentence-transformers/all-MiniLM-L6-v2 model (free, no API key needed).
    """

    def __init__(self):
        self.model_name = "sentence-transformers/all-MiniLM-L6-v2"
        self.api_url = (
            f"https://api-inference.huggingface.co/pipeline/feature-extraction/{self.model_name}"
        )
        self.embedding_dimension = 384  # MiniLM-L6-v2 dimension
        self.max_retries = 3
        self.timeout = 30

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Input text to embed

        Returns:
            List of floats representing the embedding
        """
        if not text or not text.strip():
            return [0.0] * self.embedding_dimension

        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    payload = {"inputs": text.strip()[:512]}  # Limit to 512 chars

                    async with session.post(
                        self.api_url,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=self.timeout),
                    ) as response:
                        if response.status == 200:
                            result = await response.json()

                            # Handle different response formats
                            if isinstance(result, list) and len(result) > 0:
                                if isinstance(result[0], list):
                                    embedding = result[0]  # First sentence embedding
                                else:
                                    embedding = result

                                # Ensure correct dimension
                                if len(embedding) == self.embedding_dimension:
                                    logger.debug(f"Generated embedding for text: {text[:50]}...")
                                    return embedding
                                else:
                                    logger.warning(
                                        f"Unexpected embedding dimension: {len(embedding)}"
                                    )

                        elif response.status == 503:
                            # Model loading, wait and retry
                            wait_time = 2**attempt
                            logger.info(
                                f"Model loading, waiting {wait_time}s before retry {attempt + 1}"
                            )
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            error_text = await response.text()
                            logger.error(f"HuggingFace API error {response.status}: {error_text}")

            except asyncio.TimeoutError:
                logger.warning(f"Embedding request timeout on attempt {attempt + 1}")
            except Exception as e:
                logger.error(f"Embedding generation error on attempt {attempt + 1}: {e}")

            if attempt < self.max_retries - 1:
                await asyncio.sleep(1)

        # Return zero vector on failure
        logger.error(f"Failed to generate embedding after {self.max_retries} attempts")
        return [0.0] * self.embedding_dimension

    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embeddings
        """
        embeddings = []

        # Process in small batches to avoid rate limits
        batch_size = 5
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]

            # Generate embeddings concurrently for the batch
            tasks = [self.generate_embedding(text) for text in batch]
            batch_embeddings = await asyncio.gather(*tasks)
            embeddings.extend(batch_embeddings)

            # Small delay between batches
            if i + batch_size < len(texts):
                await asyncio.sleep(0.5)

        return embeddings

    def get_embedding_dimension(self) -> int:
        """Get the embedding dimension."""
        return self.embedding_dimension

    async def health_check(self) -> bool:
        """Check if the service is available."""
        try:
            test_embedding = await self.generate_embedding("test")
            return len(test_embedding) == self.embedding_dimension
        except Exception as e:
            logger.error(f"HuggingFace embedding service health check failed: {e}")
            return False


# Global instance
_hf_embedding_service: Optional[HuggingFaceEmbeddingService] = None


def get_huggingface_embedding_service() -> HuggingFaceEmbeddingService:
    """Get the global HuggingFace embedding service instance."""
    global _hf_embedding_service
    if _hf_embedding_service is None:
        _hf_embedding_service = HuggingFaceEmbeddingService()
    return _hf_embedding_service
