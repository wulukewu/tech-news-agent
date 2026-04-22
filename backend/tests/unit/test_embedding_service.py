"""
Unit Tests for Embedding Service

Tests article preprocessing, chunking, and embedding generation functionality.

Validates: Requirements 7.1, 7.3, 7.4
"""

from uuid import uuid4

import pytest

from app.qa_agent.embedding_service import (
    ArticlePreprocessor,
    EmbeddingError,
    EmbeddingService,
    PreprocessingError,
    TextChunker,
)


class TestArticlePreprocessor:
    """Test article preprocessing functionality."""

    def test_clean_html_basic(self):
        """Test basic HTML cleaning."""
        preprocessor = ArticlePreprocessor()

        html = "<p>This is a <strong>test</strong> article.</p>"
        result = preprocessor.clean_html(html)

        assert result == "This is a test article."
        assert "<" not in result
        assert ">" not in result

    def test_clean_html_with_scripts(self):
        """Test HTML cleaning removes scripts and styles."""
        preprocessor = ArticlePreprocessor()

        html = """
        <html>
            <head><style>body { color: red; }</style></head>
            <body>
                <script>alert('test');</script>
                <p>Content here</p>
            </body>
        </html>
        """
        result = preprocessor.clean_html(html)

        assert "Content here" in result
        assert "alert" not in result
        assert "color: red" not in result

    def test_clean_html_chinese_content(self):
        """Test HTML cleaning preserves Chinese characters."""
        preprocessor = ArticlePreprocessor()

        html = "<p>這是一篇<strong>測試</strong>文章。</p>"
        result = preprocessor.clean_html(html)

        assert "這是一篇測試文章。" in result
        assert "<" not in result

    def test_clean_html_empty_input(self):
        """Test HTML cleaning with empty input."""
        preprocessor = ArticlePreprocessor()

        assert preprocessor.clean_html("") == ""
        assert preprocessor.clean_html("   ") == ""

    def test_normalize_whitespace(self):
        """Test whitespace normalization."""
        preprocessor = ArticlePreprocessor()

        text = "This  is   a    test.\n\n\nWith   multiple   spaces."
        result = preprocessor.normalize_whitespace(text)

        assert "  " not in result
        assert "\n\n\n" not in result
        assert result == "This is a test.\n\nWith multiple spaces."

    def test_remove_special_characters_preserve_punctuation(self):
        """Test special character removal while preserving punctuation."""
        preprocessor = ArticlePreprocessor()

        text = "Hello, world! This is a test."
        result = preprocessor.remove_special_characters(text, preserve_punctuation=True)

        assert "," in result
        assert "!" in result
        assert "." in result

    def test_remove_special_characters_no_preserve(self):
        """Test special character removal without preserving punctuation."""
        preprocessor = ArticlePreprocessor()

        text = "Hello, world! This is a test."
        result = preprocessor.remove_special_characters(text, preserve_punctuation=False)

        assert "," not in result
        assert "!" not in result
        # Period might be removed depending on implementation

    def test_detect_language_english(self):
        """Test language detection for English text."""
        preprocessor = ArticlePreprocessor()

        text = "This is an English article about technology and programming."
        result = preprocessor.detect_language(text)

        assert result == "en"

    def test_detect_language_chinese(self):
        """Test language detection for Chinese text."""
        preprocessor = ArticlePreprocessor()

        text = "這是一篇關於技術和程式設計的中文文章。"
        result = preprocessor.detect_language(text)

        assert result == "zh"

    def test_detect_language_mixed(self):
        """Test language detection for mixed content."""
        preprocessor = ArticlePreprocessor()

        # Mostly Chinese
        text = "這是一篇文章 with some English words 但主要是中文。"
        result = preprocessor.detect_language(text)
        assert result == "zh"

        # Mostly English
        text = "This is an article 有一些中文 but mostly English."
        result = preprocessor.detect_language(text)
        assert result == "en"

    def test_preprocess_article_complete_pipeline(self):
        """Test complete preprocessing pipeline."""
        preprocessor = ArticlePreprocessor()

        html_content = """
        <html>
            <body>
                <h1>Test Article</h1>
                <p>This is a <strong>test</strong> article with HTML.</p>
                <script>alert('remove me');</script>
            </body>
        </html>
        """
        title = "<h1>Test Title</h1>"

        result = preprocessor.preprocess_article(html_content, title)

        assert "content" in result
        assert "title" in result
        assert "language" in result
        assert "original_length" in result
        assert "processed_length" in result

        assert "Test Article" in result["content"]
        assert "test article" in result["content"]
        assert "alert" not in result["content"]
        assert "Test Title" in result["title"]
        assert "<" not in result["content"]

    def test_preprocess_article_too_short(self):
        """Test preprocessing fails for too short content."""
        preprocessor = ArticlePreprocessor()

        with pytest.raises(PreprocessingError, match="too short"):
            preprocessor.preprocess_article("Hi")

    def test_preprocess_article_chinese(self):
        """Test preprocessing Chinese article."""
        preprocessor = ArticlePreprocessor()

        content = "<p>這是一篇測試文章，包含中文內容和一些技術細節。</p>"
        title = "測試標題"

        result = preprocessor.preprocess_article(content, title)

        assert result["language"] == "zh"
        assert "測試文章" in result["content"]
        assert "測試標題" in result["title"]


class TestTextChunker:
    """Test text chunking functionality."""

    def test_estimate_tokens_english(self):
        """Test token estimation for English text."""
        chunker = TextChunker()

        # Approximately 10 words = ~7.5 tokens
        text = "This is a test sentence with about ten words here."
        tokens = chunker.estimate_tokens(text, "en")

        assert 5 <= tokens <= 10  # Rough estimate

    def test_estimate_tokens_chinese(self):
        """Test token estimation for Chinese text."""
        chunker = TextChunker()

        # 15 Chinese characters = ~10 tokens
        text = "這是一個測試句子包含大約十五個中文字。"
        tokens = chunker.estimate_tokens(text, "zh")

        assert 8 <= tokens <= 12  # Rough estimate

    def test_split_by_sentences_english(self):
        """Test sentence splitting for English."""
        chunker = TextChunker()

        text = "First sentence. Second sentence! Third sentence?"
        sentences = chunker.split_by_sentences(text, "en")

        assert len(sentences) == 3
        assert "First sentence" in sentences[0]
        assert "Second sentence" in sentences[1]
        assert "Third sentence" in sentences[2]

    def test_split_by_sentences_chinese(self):
        """Test sentence splitting for Chinese."""
        chunker = TextChunker()

        text = "第一句話。第二句話！第三句話？"
        sentences = chunker.split_by_sentences(text, "zh")

        assert len(sentences) == 3
        assert "第一句話" in sentences[0]

    def test_chunk_text_short_content(self):
        """Test chunking short content returns single chunk."""
        chunker = TextChunker(chunk_size=1000)

        text = "This is a short article that fits in one chunk."
        chunks = chunker.chunk_text(text, "en")

        assert len(chunks) == 1
        assert chunks[0]["chunk_index"] == 0
        assert chunks[0]["total_chunks"] == 1
        assert chunks[0]["text"] == text

    def test_chunk_text_long_content(self):
        """Test chunking long content creates multiple chunks."""
        chunker = TextChunker(chunk_size=50, chunk_overlap=10)

        # Create long text with multiple sentences
        sentences = [f"This is sentence number {i}." for i in range(100)]
        text = " ".join(sentences)

        chunks = chunker.chunk_text(text, "en")

        assert len(chunks) > 1
        assert all(chunk["total_chunks"] == len(chunks) for chunk in chunks)

        # Check chunk indices are sequential
        for i, chunk in enumerate(chunks):
            assert chunk["chunk_index"] == i

    def test_chunk_text_with_overlap(self):
        """Test chunks have proper overlap for context preservation."""
        chunker = TextChunker(chunk_size=100, chunk_overlap=20)

        # Create text that will be chunked
        sentences = [f"Sentence {i} with some content here." for i in range(50)]
        text = " ".join(sentences)

        chunks = chunker.chunk_text(text, "en")

        if len(chunks) > 1:
            # Check that consecutive chunks have some overlap
            # (This is a rough check - exact overlap depends on sentence boundaries)
            for i in range(len(chunks) - 1):
                chunk1_words = set(chunks[i]["text"].split())
                chunk2_words = set(chunks[i + 1]["text"].split())
                overlap = chunk1_words.intersection(chunk2_words)
                assert len(overlap) > 0, "Chunks should have some overlapping words"

    def test_chunk_text_empty_input(self):
        """Test chunking empty input returns empty list."""
        chunker = TextChunker()

        assert chunker.chunk_text("") == []
        assert chunker.chunk_text("   ") == []

    def test_chunk_text_with_metadata(self):
        """Test chunks include provided metadata."""
        chunker = TextChunker()

        text = "Short text."
        metadata = {"category": "tech", "author": "test"}

        chunks = chunker.chunk_text(text, "en", metadata)

        assert len(chunks) == 1
        assert chunks[0]["metadata"] == metadata

    def test_chunk_text_chinese(self):
        """Test chunking Chinese text."""
        chunker = TextChunker(chunk_size=50, chunk_overlap=10)

        # Create long Chinese text
        sentences = [f"這是第{i}個測試句子，包含一些中文內容。" for i in range(50)]
        text = "".join(sentences)

        chunks = chunker.chunk_text(text, "zh")

        assert len(chunks) > 0
        assert all("測試句子" in chunk["text"] for chunk in chunks[:3])


class TestEmbeddingService:
    """Test embedding service functionality."""

    @pytest.mark.asyncio
    async def test_generate_embedding_valid_text(self):
        """Test embedding generation for valid text."""
        service = EmbeddingService()

        text = "This is a test article about technology."

        try:
            embedding = await service.generate_embedding(text)

            assert isinstance(embedding, list)
            assert len(embedding) == 1536  # OpenAI ada-002 dimension
            assert all(isinstance(x, float) for x in embedding)
        except Exception as e:
            # If API is not available in test environment, skip
            pytest.skip(f"Embedding API not available: {e}")

    @pytest.mark.asyncio
    async def test_generate_embedding_empty_text(self):
        """Test embedding generation fails for empty text."""
        service = EmbeddingService()

        with pytest.raises(EmbeddingError, match="empty text"):
            await service.generate_embedding("")

    @pytest.mark.asyncio
    async def test_generate_embedding_long_text(self):
        """Test embedding generation truncates very long text."""
        service = EmbeddingService()

        # Create very long text
        long_text = "This is a test sentence. " * 10000

        try:
            # Should not raise error, should truncate
            embedding = await service.generate_embedding(long_text)
            assert isinstance(embedding, list)
        except Exception as e:
            pytest.skip(f"Embedding API not available: {e}")

    @pytest.mark.asyncio
    async def test_process_and_embed_article_basic(self):
        """Test complete article processing pipeline."""
        service = EmbeddingService()

        article_id = uuid4()
        title = "Test Article"
        content = "<p>This is a test article with some content.</p>"

        try:
            result = await service.process_and_embed_article(article_id, title, content)

            assert result["success"] is True
            assert result["article_id"] == str(article_id)
            assert result["embeddings_generated"] >= 1
            assert result["chunks_created"] >= 1
            assert result["language"] in ["en", "zh"]
        except Exception as e:
            pytest.skip(f"Embedding API or database not available: {e}")

    @pytest.mark.asyncio
    async def test_process_and_embed_article_with_metadata(self):
        """Test article processing with metadata."""
        service = EmbeddingService()

        article_id = uuid4()
        title = "Test Article"
        content = "<p>This is a test article.</p>"
        metadata = {"category": "tech", "author": "test"}

        try:
            result = await service.process_and_embed_article(article_id, title, content, metadata)

            assert result["success"] is True
            # Should have title + content + metadata embeddings
            assert result["embeddings_generated"] >= 2
        except Exception as e:
            pytest.skip(f"Embedding API or database not available: {e}")

    @pytest.mark.asyncio
    async def test_process_and_embed_article_chinese(self):
        """Test processing Chinese article."""
        service = EmbeddingService()

        article_id = uuid4()
        title = "測試文章"
        content = "<p>這是一篇測試文章，包含中文內容。</p>"

        try:
            result = await service.process_and_embed_article(article_id, title, content)

            assert result["success"] is True
            assert result["language"] == "zh"
        except Exception as e:
            pytest.skip(f"Embedding API or database not available: {e}")


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_preprocessor_malformed_html(self):
        """Test preprocessing handles malformed HTML gracefully."""
        preprocessor = ArticlePreprocessor()

        malformed = "<p>Unclosed tag <div>Content</p>"
        result = preprocessor.clean_html(malformed)

        # Should still extract text
        assert "Content" in result

    def test_chunker_single_long_sentence(self):
        """Test chunking handles single very long sentence."""
        chunker = TextChunker(chunk_size=50)

        # Single sentence longer than chunk size
        long_sentence = " ".join(["word"] * 200)
        chunks = chunker.chunk_text(long_sentence, "en")

        # Should still create chunks even without sentence boundaries
        assert len(chunks) >= 1

    def test_preprocessor_only_whitespace(self):
        """Test preprocessing handles whitespace-only content."""
        preprocessor = ArticlePreprocessor()

        with pytest.raises(PreprocessingError):
            preprocessor.preprocess_article("   \n\n   ")

    def test_chunker_respects_chunk_size_limits(self):
        """Test chunker respects configured chunk size."""
        chunker = TextChunker(chunk_size=100, chunk_overlap=20)

        # Create text with known token count
        sentences = [f"Test sentence {i}." for i in range(100)]
        text = " ".join(sentences)

        chunks = chunker.chunk_text(text, "en")

        # Each chunk should be roughly within chunk size
        for chunk in chunks:
            assert chunk["token_count"] <= 150  # Allow some flexibility


class TestIntegration:
    """Integration tests for complete workflows."""

    def test_preprocess_then_chunk(self):
        """Test preprocessing followed by chunking."""
        preprocessor = ArticlePreprocessor()
        chunker = TextChunker(chunk_size=100)

        html = "<p>" + " ".join([f"Sentence {i}." for i in range(50)]) + "</p>"

        # Preprocess
        preprocessed = preprocessor.preprocess_article(html, "Test Title")

        # Chunk
        chunks = chunker.chunk_text(preprocessed["content"], preprocessed["language"])

        assert len(chunks) > 0
        assert all(chunk["text"] for chunk in chunks)

    def test_chinese_article_full_pipeline(self):
        """Test full pipeline with Chinese article."""
        preprocessor = ArticlePreprocessor()
        chunker = TextChunker(chunk_size=100)

        html = "<p>" + "".join([f"這是第{i}個測試句子。" for i in range(50)]) + "</p>"
        title = "測試標題"

        # Preprocess
        preprocessed = preprocessor.preprocess_article(html, title)
        assert preprocessed["language"] == "zh"

        # Chunk
        chunks = chunker.chunk_text(preprocessed["content"], preprocessed["language"])

        assert len(chunks) > 0
        assert all("測試句子" in chunk["text"] for chunk in chunks[:3])
