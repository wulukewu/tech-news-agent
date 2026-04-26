"""
Example Usage: Embedding Service

This example demonstrates how to use the embedding service for article
preprocessing, chunking, and embedding generation.

Requirements: 7.1, 7.3, 7.4
"""

import asyncio
from uuid import uuid4

from app.qa_agent.embedding_service import (
    ArticlePreprocessor,
    TextChunker,
    get_embedding_service,
)


async def example_basic_preprocessing():
    """Example: Basic article preprocessing."""
    print("\n=== Example 1: Basic Article Preprocessing ===\n")

    preprocessor = ArticlePreprocessor()

    # Sample HTML content
    html_content = """
    <html>
        <head><title>Tech Article</title></head>
        <body>
            <h1>Understanding Machine Learning</h1>
            <p>Machine learning is a subset of <strong>artificial intelligence</strong>.</p>
            <p>It enables computers to learn from data without explicit programming.</p>
            <script>console.log('This will be removed');</script>
        </body>
    </html>
    """

    title = "<h1>Understanding Machine Learning</h1>"

    # Preprocess the article
    result = preprocessor.preprocess_article(html_content, title)

    print(f"Original length: {result['original_length']} characters")
    print(f"Processed length: {result['processed_length']} characters")
    print(f"Detected language: {result['language']}")
    print(f"\nClean title: {result['title']}")
    print(f"\nClean content:\n{result['content'][:200]}...")


async def example_chinese_preprocessing():
    """Example: Chinese article preprocessing."""
    print("\n=== Example 2: Chinese Article Preprocessing ===\n")

    preprocessor = ArticlePreprocessor()

    html_content = """
    <div class="article">
        <h1>深度學習入門</h1>
        <p>深度學習是機器學習的一個分支，使用<strong>神經網路</strong>進行學習。</p>
        <p>它在圖像識別、自然語言處理等領域有廣泛應用。</p>
    </div>
    """

    title = "深度學習入門"

    result = preprocessor.preprocess_article(html_content, title)

    print(f"Detected language: {result['language']}")
    print(f"Clean title: {result['title']}")
    print(f"Clean content:\n{result['content']}")


async def example_text_chunking():
    """Example: Text chunking for long articles."""
    print("\n=== Example 3: Text Chunking ===\n")

    chunker = TextChunker(chunk_size=100, chunk_overlap=20)

    # Create a long article
    long_article = " ".join(
        [f"This is sentence number {i} in a long article about technology." for i in range(50)]
    )

    # Chunk the text
    chunks = chunker.chunk_text(long_article, language="en")

    print(f"Total chunks created: {len(chunks)}")
    print("\nFirst chunk:")
    print(f"  Index: {chunks[0]['chunk_index']}")
    print(f"  Token count: {chunks[0]['token_count']}")
    print(f"  Text preview: {chunks[0]['text'][:100]}...")

    if len(chunks) > 1:
        print("\nSecond chunk:")
        print(f"  Index: {chunks[1]['chunk_index']}")
        print(f"  Token count: {chunks[1]['token_count']}")
        print(f"  Text preview: {chunks[1]['text'][:100]}...")


async def example_chinese_chunking():
    """Example: Chinese text chunking."""
    print("\n=== Example 4: Chinese Text Chunking ===\n")

    chunker = TextChunker(chunk_size=50, chunk_overlap=10)

    # Create a long Chinese article
    long_article = "".join(
        [f"這是關於人工智慧的第{i}個段落，包含一些技術細節和應用案例。" for i in range(30)]
    )

    chunks = chunker.chunk_text(long_article, language="zh")

    print(f"Total chunks created: {len(chunks)}")
    print("\nFirst chunk:")
    print(f"  Index: {chunks[0]['chunk_index']}")
    print(f"  Token count: {chunks[0]['token_count']}")
    print(f"  Text: {chunks[0]['text'][:80]}...")


async def example_embedding_generation():
    """Example: Generate embeddings (requires API access)."""
    print("\n=== Example 5: Embedding Generation ===\n")

    service = get_embedding_service()

    text = "Machine learning is transforming the technology industry."

    try:
        embedding = await service.generate_embedding(text)

        print("Generated embedding:")
        print(f"  Dimension: {len(embedding)}")
        print(f"  First 5 values: {embedding[:5]}")
        print(f"  Data type: {type(embedding[0])}")
    except Exception as e:
        print("Note: Embedding generation requires API access")
        print(f"Error: {e}")


async def example_complete_pipeline():
    """Example: Complete article processing pipeline."""
    print("\n=== Example 6: Complete Article Processing Pipeline ===\n")

    service = get_embedding_service()

    # Sample article
    article_id = uuid4()
    title = "Introduction to Neural Networks"
    content = """
    <article>
        <h1>Introduction to Neural Networks</h1>
        <p>Neural networks are computing systems inspired by biological neural networks.</p>
        <p>They consist of interconnected nodes (neurons) that process information.</p>
        <p>Deep learning uses multiple layers of neural networks to learn complex patterns.</p>
    </article>
    """
    metadata = {
        "category": "AI/ML",
        "author": "Tech Writer",
        "tags": ["neural-networks", "deep-learning", "AI"],
    }

    try:
        result = await service.process_and_embed_article(
            article_id=article_id, title=title, content=content, metadata=metadata
        )

        print("Processing result:")
        print(f"  Article ID: {result['article_id']}")
        print(f"  Success: {result['success']}")
        print(f"  Embeddings generated: {result['embeddings_generated']}")
        print(f"  Chunks created: {result['chunks_created']}")
        print(f"  Language: {result['language']}")
        print(f"  Original length: {result['original_length']} chars")
        print(f"  Processed length: {result['processed_length']} chars")

        print("\nNote: This includes separate embeddings for:")
        print("  - Title (chunk_index = -1)")
        print("  - Content chunks (chunk_index = 0, 1, 2, ...)")
        print("  - Metadata (chunk_index = -2)")

    except Exception as e:
        print("Note: Complete pipeline requires database and API access")
        print(f"Error: {e}")


async def example_batch_processing():
    """Example: Batch process multiple articles."""
    print("\n=== Example 7: Batch Article Processing ===\n")

    service = get_embedding_service()

    # Sample articles
    articles = [
        (
            uuid4(),
            "Article 1: Python Programming",
            "<p>Python is a versatile programming language.</p>",
            {"category": "Programming"},
        ),
        (
            uuid4(),
            "Article 2: Web Development",
            "<p>Web development involves creating websites and applications.</p>",
            {"category": "Web"},
        ),
        (
            uuid4(),
            "Article 3: Data Science",
            "<p>Data science combines statistics and programming.</p>",
            {"category": "Data"},
        ),
    ]

    try:
        results = await service.batch_process_articles(articles, max_concurrent=2)

        print("Batch processing results:")
        print(f"  Total articles: {len(results)}")

        successful = sum(1 for r in results if r.get("success"))
        print(f"  Successful: {successful}")
        print(f"  Failed: {len(results) - successful}")

        for i, result in enumerate(results, 1):
            status = "✓" if result.get("success") else "✗"
            print(f"\n  {status} Article {i}:")
            if result.get("success"):
                print(f"    Embeddings: {result.get('embeddings_generated')}")
                print(f"    Chunks: {result.get('chunks_created')}")
            else:
                print(f"    Error: {result.get('error')}")

    except Exception as e:
        print("Note: Batch processing requires database and API access")
        print(f"Error: {e}")


async def example_preprocessing_only():
    """Example: Use preprocessing without embedding generation."""
    print("\n=== Example 8: Preprocessing Only (No API Required) ===\n")

    preprocessor = ArticlePreprocessor()
    chunker = TextChunker(chunk_size=200)

    # Sample article with HTML
    html_content = """
    <div class="blog-post">
        <h1>The Future of AI</h1>
        <p>Artificial intelligence is rapidly evolving.</p>
        <p>New breakthroughs are happening every day.</p>
        <p>From natural language processing to computer vision,
           AI is transforming industries.</p>
        <script>trackPageView();</script>
    </div>
    """

    # Step 1: Preprocess
    preprocessed = preprocessor.preprocess_article(html_content, "The Future of AI")

    print("Preprocessing complete:")
    print(f"  Language: {preprocessed['language']}")
    print(f"  Title: {preprocessed['title']}")
    print(f"  Content length: {preprocessed['processed_length']} chars")

    # Step 2: Chunk
    chunks = chunker.chunk_text(preprocessed["content"], preprocessed["language"])

    print("\nChunking complete:")
    print(f"  Total chunks: {len(chunks)}")

    for i, chunk in enumerate(chunks):
        print(f"\n  Chunk {i}:")
        print(f"    Tokens: {chunk['token_count']}")
        print(f"    Text: {chunk['text']}")


async def main():
    """Run all examples."""
    print("=" * 70)
    print("EMBEDDING SERVICE USAGE EXAMPLES")
    print("=" * 70)

    # Examples that don't require API access
    await example_basic_preprocessing()
    await example_chinese_preprocessing()
    await example_text_chunking()
    await example_chinese_chunking()
    await example_preprocessing_only()

    # Examples that require API access (will show errors if not configured)
    await example_embedding_generation()
    await example_complete_pipeline()
    await example_batch_processing()

    print("\n" + "=" * 70)
    print("EXAMPLES COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
