"""
Embedding Generation and Article Preprocessing Service

This module implements article content preprocessing, chunking strategy,
and embedding generation for the Intelligent Q&A Agent.

Validates: Requirements 7.1, 7.3, 7.4
"""

import logging
import re
from typing import Any, Dict, List, Optional
from uuid import UUID

from bs4 import BeautifulSoup
from openai import AsyncOpenAI

from app.core.config import settings
from app.qa_agent.vector_store import VectorStore, VectorStoreError

logger = logging.getLogger(__name__)

# Embedding configuration
EMBEDDING_MODEL = "text-embedding-ada-002"  # OpenAI embedding model
EMBEDDING_DIMENSION = 1536  # OpenAI ada-002 dimension
DEFAULT_CHUNK_SIZE = 1000  # tokens (approximately 750 words)
DEFAULT_CHUNK_OVERLAP = 200  # tokens overlap for context preservation


class PreprocessingError(Exception):
    """Exception raised during article preprocessing."""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error


class EmbeddingError(Exception):
    """Exception raised during embedding generation."""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error


class ArticlePreprocessor:
    """
    Handles article content preprocessing including HTML cleaning,
    text formatting, and normalization.

    Validates: Requirements 7.3
    """

    @staticmethod
    def clean_html(html_content: str) -> str:
        """
        Clean HTML tags and formatting from article content.

        Args:
            html_content: Raw HTML content

        Returns:
            Cleaned plain text

        Validates: Requirements 7.3
        """
        if not html_content or not html_content.strip():
            return ""

        try:
            # Parse HTML
            soup = BeautifulSoup(html_content, "html.parser")

            # Remove script and style elements
            for script in soup(["script", "style", "noscript"]):
                script.decompose()

            # Get text
            text = soup.get_text()

            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = " ".join(chunk for chunk in chunks if chunk)

            return text

        except Exception as e:
            logger.warning(f"Failed to parse HTML, falling back to regex: {e}")
            # Fallback to regex-based cleaning
            text = re.sub(r"<[^>]+>", "", html_content)
            return text.strip()

    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """
        Normalize whitespace and special characters.

        Args:
            text: Input text

        Returns:
            Normalized text

        Validates: Requirements 7.3
        """
        if not text:
            return ""

        # Replace multiple spaces with single space
        text = re.sub(r" +", " ", text)

        # Replace multiple newlines with double newline
        text = re.sub(r"\n\n+", "\n\n", text)

        # Remove leading/trailing whitespace from each line
        lines = [line.strip() for line in text.split("\n")]
        text = "\n".join(lines)

        # Normalize unicode characters
        text = text.strip()

        return text

    @staticmethod
    def remove_special_characters(text: str, preserve_punctuation: bool = True) -> str:
        """
        Remove or normalize special characters.

        Args:
            text: Input text
            preserve_punctuation: Whether to preserve punctuation marks

        Returns:
            Cleaned text
        """
        if not text:
            return ""

        if preserve_punctuation:
            # Only remove control characters and other non-printable characters
            text = re.sub(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]", "", text)
        else:
            # Remove all non-alphanumeric except spaces
            text = re.sub(r"[^\w\s\u4e00-\u9fff]", " ", text)
            text = re.sub(r" +", " ", text)

        return text.strip()

    @staticmethod
    def detect_language(text: str) -> str:
        """
        Detect if text is primarily Chinese or English.

        Args:
            text: Input text

        Returns:
            Language code ('zh' or 'en')
        """
        if not text:
            return "en"

        # Count Chinese characters
        chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
        # Count English letters
        english_chars = len(re.findall(r"[a-zA-Z]", text))

        # If more than 30% Chinese characters, consider it Chinese
        total_chars = chinese_chars + english_chars
        if total_chars == 0:
            return "en"

        chinese_ratio = chinese_chars / total_chars
        return "zh" if chinese_ratio > 0.3 else "en"

    def preprocess_article(
        self, content: str, title: Optional[str] = None, preserve_semantic_meaning: bool = True
    ) -> Dict[str, str]:
        """
        Complete preprocessing pipeline for article content.

        Args:
            content: Raw article content (may contain HTML)
            title: Optional article title
            preserve_semantic_meaning: Whether to preserve semantic structure

        Returns:
            Dictionary with preprocessed content and metadata

        Raises:
            PreprocessingError: If preprocessing fails

        Validates: Requirements 7.3
        """
        try:
            # Step 1: Clean HTML
            clean_content = self.clean_html(content)

            # Step 2: Normalize whitespace
            clean_content = self.normalize_whitespace(clean_content)

            # Step 3: Remove special characters (preserve punctuation for semantic meaning)
            clean_content = self.remove_special_characters(
                clean_content, preserve_punctuation=preserve_semantic_meaning
            )

            # Step 4: Detect language
            language = self.detect_language(clean_content)

            # Step 5: Process title if provided
            clean_title = ""
            if title:
                clean_title = self.clean_html(title)
                clean_title = self.normalize_whitespace(clean_title)
                clean_title = self.remove_special_characters(clean_title, preserve_punctuation=True)

            # Validate result
            if not clean_content or len(clean_content.strip()) < 10:
                raise PreprocessingError("Preprocessed content is too short or empty")

            return {
                "content": clean_content,
                "title": clean_title,
                "language": language,
                "original_length": len(content),
                "processed_length": len(clean_content),
            }

        except PreprocessingError:
            raise
        except Exception as e:
            logger.error(f"Article preprocessing failed: {e}", exc_info=True)
            raise PreprocessingError(f"Failed to preprocess article: {e}", original_error=e)


class TextChunker:
    """
    Implements chunking strategy for long articles with context preservation.

    Validates: Requirements 7.3
    """

    def __init__(
        self, chunk_size: int = DEFAULT_CHUNK_SIZE, chunk_overlap: int = DEFAULT_CHUNK_OVERLAP
    ):
        """
        Initialize text chunker.

        Args:
            chunk_size: Target chunk size in tokens (approximate)
            chunk_overlap: Number of tokens to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    @staticmethod
    def estimate_tokens(text: str, language: str = "en") -> int:
        """
        Estimate token count for text.

        For Chinese: ~1.5 characters per token
        For English: ~4 characters per token (roughly 0.75 words per token)

        Args:
            text: Input text
            language: Language code ('zh' or 'en')

        Returns:
            Estimated token count
        """
        if not text:
            return 0

        if language == "zh":
            # Chinese: count characters (excluding spaces)
            chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
            return int(chinese_chars / 1.5)
        else:
            # English: count words and convert to tokens
            words = len(text.split())
            return int(words * 0.75)

    def split_by_sentences(self, text: str, language: str = "en") -> List[str]:
        """
        Split text into sentences based on language.

        Args:
            text: Input text
            language: Language code

        Returns:
            List of sentences
        """
        if language == "zh":
            # Chinese sentence delimiters
            sentences = re.split(r"[。！？\n]+", text)
        else:
            # English sentence delimiters
            sentences = re.split(r"[.!?\n]+", text)

        # Clean and filter empty sentences
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences

    def chunk_text(
        self, text: str, language: str = "en", metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Chunk text into manageable pieces with overlap for context preservation.

        Args:
            text: Input text to chunk
            language: Language code ('zh' or 'en')
            metadata: Optional metadata to include with each chunk

        Returns:
            List of chunk dictionaries with text and metadata

        Validates: Requirements 7.3
        """
        if not text or not text.strip():
            return []

        # Estimate total tokens
        total_tokens = self.estimate_tokens(text, language)

        # If text is short enough, return as single chunk
        if total_tokens <= self.chunk_size:
            return [
                {
                    "text": text,
                    "chunk_index": 0,
                    "total_chunks": 1,
                    "token_count": total_tokens,
                    "metadata": metadata or {},
                }
            ]

        # Split into sentences
        sentences = self.split_by_sentences(text, language)

        chunks = []
        current_chunk = []
        current_tokens = 0
        chunk_index = 0

        for sentence in sentences:
            sentence_tokens = self.estimate_tokens(sentence, language)

            # If adding this sentence exceeds chunk size, save current chunk
            if current_tokens + sentence_tokens > self.chunk_size and current_chunk:
                chunk_text = " ".join(current_chunk)
                chunks.append(
                    {
                        "text": chunk_text,
                        "chunk_index": chunk_index,
                        "token_count": current_tokens,
                        "metadata": metadata or {},
                    }
                )

                # Start new chunk with overlap
                # Keep last few sentences for context
                overlap_sentences = []
                overlap_tokens = 0
                for s in reversed(current_chunk):
                    s_tokens = self.estimate_tokens(s, language)
                    if overlap_tokens + s_tokens <= self.chunk_overlap:
                        overlap_sentences.insert(0, s)
                        overlap_tokens += s_tokens
                    else:
                        break

                current_chunk = overlap_sentences
                current_tokens = overlap_tokens
                chunk_index += 1

            # Add sentence to current chunk
            current_chunk.append(sentence)
            current_tokens += sentence_tokens

        # Add final chunk if not empty
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append(
                {
                    "text": chunk_text,
                    "chunk_index": chunk_index,
                    "token_count": current_tokens,
                    "metadata": metadata or {},
                }
            )

        # Update total_chunks for all chunks
        total_chunks = len(chunks)
        for chunk in chunks:
            chunk["total_chunks"] = total_chunks

        logger.debug(
            f"Chunked text into {total_chunks} chunks "
            f"(total tokens: {total_tokens}, chunk size: {self.chunk_size})"
        )

        return chunks


from app.qa_agent._es_batch_mixin import EsBatchMixin


class EmbeddingService(EsBatchMixin):
    """
    Service for generating embeddings using OpenAI API (or Groq-compatible endpoint).

    Validates: Requirements 7.1, 7.4
    """

    def __init__(self):
        """Initialize embedding service with OpenAI client."""
        # Use Groq API endpoint (OpenAI-compatible)
        self.client = AsyncOpenAI(
            base_url="https://api.groq.com/openai/v1", api_key=settings.groq_api_key, timeout=30.0
        )
        self.preprocessor = ArticlePreprocessor()
        self.chunker = TextChunker()
        self.vector_store = VectorStore()

    async def generate_embedding(self, text: str, retry_count: int = 3) -> List[float]:
        """
        Generate embedding vector for text.

        Args:
            text: Input text
            retry_count: Number of retries on failure

        Returns:
            Embedding vector (1536 dimensions)

        Raises:
            EmbeddingError: If embedding generation fails

        Validates: Requirements 7.1
        """
        if not text or not text.strip():
            raise EmbeddingError("Cannot generate embedding for empty text")

        # Truncate text if too long (OpenAI limit is ~8191 tokens)
        max_chars = 30000  # Conservative limit
        if len(text) > max_chars:
            logger.warning(f"Text too long ({len(text)} chars), truncating to {max_chars}")
            text = text[:max_chars]

        last_error = None
        for attempt in range(retry_count):
            try:
                response = await self.client.embeddings.create(model=EMBEDDING_MODEL, input=text)

                embedding = response.data[0].embedding

                # Validate embedding
                if not embedding or len(embedding) != EMBEDDING_DIMENSION:
                    raise EmbeddingError(
                        f"Invalid embedding dimension: expected {EMBEDDING_DIMENSION}, "
                        f"got {len(embedding) if embedding else 0}"
                    )

                return embedding

            except Exception as e:
                last_error = e
                logger.warning(
                    f"Embedding generation attempt {attempt + 1}/{retry_count} failed: {e}"
                )

                if attempt < retry_count - 1:
                    # Wait before retry (exponential backoff)
                    import asyncio

                    await asyncio.sleep(2**attempt)

        # All retries failed
        logger.error(f"Failed to generate embedding after {retry_count} attempts")
        raise EmbeddingError(
            f"Failed to generate embedding: {last_error}", original_error=last_error
        )

    async def process_and_embed_article(
        self, article_id: UUID, title: str, content: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Complete pipeline: preprocess article, chunk if needed, and generate embeddings.

        This method implements separate vectorization for title, content, and metadata
        as specified in Requirement 7.4.

        Args:
            article_id: Article UUID
            title: Article title
            content: Article content (may contain HTML)
            metadata: Optional article metadata

        Returns:
            Dictionary with processing results

        Raises:
            PreprocessingError: If preprocessing fails
            EmbeddingError: If embedding generation fails
            VectorStoreError: If storage fails

        Validates: Requirements 7.1, 7.3, 7.4
        """
        try:
            # Step 1: Preprocess article
            logger.info(f"Preprocessing article {article_id}")
            preprocessed = self.preprocessor.preprocess_article(content, title)

            clean_content = preprocessed["content"]
            clean_title = preprocessed["title"]
            language = preprocessed["language"]

            # Step 2: Generate title embedding (separate vectorization)
            logger.info(f"Generating title embedding for article {article_id}")
            title_embedding = await self.generate_embedding(clean_title)

            # Store title embedding with special metadata
            await self.vector_store.store_embedding(
                article_id=article_id,
                embedding=title_embedding,
                chunk_index=-1,  # Special index for title
                chunk_text=clean_title,
                metadata={**(metadata or {}), "type": "title", "language": language},
            )

            # Step 3: Chunk content if necessary
            logger.info(f"Chunking content for article {article_id}")
            chunks = self.chunker.chunk_text(clean_content, language=language, metadata=metadata)

            # Step 4: Generate embeddings for each chunk
            logger.info(f"Generating embeddings for {len(chunks)} chunks")
            embeddings_generated = 0

            for chunk in chunks:
                chunk_text = chunk["text"]
                chunk_index = chunk["chunk_index"]

                # Generate embedding
                embedding = await self.generate_embedding(chunk_text)

                # Store embedding
                await self.vector_store.store_embedding(
                    article_id=article_id,
                    embedding=embedding,
                    chunk_index=chunk_index,
                    chunk_text=chunk_text,
                    metadata={
                        **chunk["metadata"],
                        "type": "content",
                        "language": language,
                        "token_count": chunk["token_count"],
                        "total_chunks": chunk["total_chunks"],
                    },
                )

                embeddings_generated += 1

            # Step 5: Generate metadata embedding if metadata provided
            if metadata:
                # Create searchable metadata text
                metadata_text = " ".join(
                    [
                        f"{key}: {value}"
                        for key, value in metadata.items()
                        if isinstance(value, (str, int, float))
                    ]
                )

                if metadata_text:
                    logger.info(f"Generating metadata embedding for article {article_id}")
                    metadata_embedding = await self.generate_embedding(metadata_text)

                    await self.vector_store.store_embedding(
                        article_id=article_id,
                        embedding=metadata_embedding,
                        chunk_index=-2,  # Special index for metadata
                        chunk_text=metadata_text,
                        metadata={**(metadata or {}), "type": "metadata", "language": language},
                    )
                    embeddings_generated += 1

            result = {
                "article_id": str(article_id),
                "success": True,
                "embeddings_generated": embeddings_generated,
                "chunks_created": len(chunks),
                "language": language,
                "original_length": preprocessed["original_length"],
                "processed_length": preprocessed["processed_length"],
            }

            logger.info(
                f"Successfully processed article {article_id}: "
                f"{embeddings_generated} embeddings generated"
            )

            return result

        except (PreprocessingError, EmbeddingError, VectorStoreError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error processing article {article_id}: {e}", exc_info=True)
            raise EmbeddingError(f"Failed to process and embed article: {e}", original_error=e)


def get_embedding_service() -> EmbeddingService:
    """
    Get an EmbeddingService instance.

    Returns:
        EmbeddingService instance
    """
    return EmbeddingService()
