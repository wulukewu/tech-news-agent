"""Mixin from app/qa_agent/embedding_service.py."""
import logging
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

logger = logging.getLogger(__name__)


class EsBatchMixin:
    async def batch_process_articles(
        self,
        articles: List[Tuple[UUID, str, str, Optional[Dict[str, Any]]]],
        max_concurrent: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Process multiple articles in batch with concurrency control.

        Args:
            articles: List of tuples (article_id, title, content, metadata)
            max_concurrent: Maximum concurrent processing tasks

        Returns:
            List of processing results

        Validates: Requirements 7.1, 7.5
        """
        import asyncio

        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_with_semaphore(article_data):
            async with semaphore:
                article_id, title, content, metadata = article_data
                try:
                    return await self.process_and_embed_article(
                        article_id, title, content, metadata
                    )
                except Exception as e:
                    logger.error(f"Failed to process article {article_id}: {e}")
                    return {"article_id": str(article_id), "success": False, "error": str(e)}

        tasks = [process_with_semaphore(article) for article in articles]
        results = await asyncio.gather(*tasks, return_exceptions=False)

        successful = sum(1 for r in results if r.get("success"))
        logger.info(
            f"Batch processing complete: {successful}/{len(articles)} articles processed successfully"
        )

        return results


# Convenience function
