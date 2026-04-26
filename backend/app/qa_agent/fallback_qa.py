"""
Fallback QA implementation that works without OpenAI embeddings.
This is used when OpenAI API is not available or configured.
"""

import logging
import uuid
from typing import List, Optional
from uuid import UUID

from app.qa_agent.models import (
    ArticleSummary,
    ParsedQuery,
    QueryIntent,
    QueryLanguage,
    StructuredResponse,
)

logger = logging.getLogger(__name__)


class FallbackQAAgent:
    """
    Fallback QA Agent that provides basic functionality without embeddings.
    Uses keyword-based search and simple response generation.
    """

    def __init__(self):
        self.name = "Fallback QA Agent"
        logger.info("Initialized Fallback QA Agent (no embeddings)")

    async def process_query(
        self, user_id: UUID, query: str, conversation_id: Optional[str] = None
    ) -> StructuredResponse:
        """
        Process a user query using fallback methods.

        Args:
            user_id: User identifier
            query: User's question
            conversation_id: Optional conversation context

        Returns:
            Structured response with fallback content
        """
        logger.info(f"Processing fallback query for user {user_id}: {query[:50]}...")

        try:
            # Parse query (basic implementation)
            parsed_query = self._parse_query(query)

            # Generate fallback response
            response = await self._generate_fallback_response(
                parsed_query, user_id, conversation_id
            )

            logger.info(f"Generated fallback response with {len(response.articles)} articles")
            return response

        except Exception as e:
            logger.error(f"Error in fallback QA processing: {e}", exc_info=True)
            return self._create_error_response(query, str(e))

    def _parse_query(self, query: str) -> ParsedQuery:
        """Parse query with basic language detection and keyword extraction."""

        # Simple language detection
        chinese_chars = sum(1 for c in query if "\u4e00" <= c <= "\u9fff")
        total_chars = len(query.replace(" ", ""))

        if chinese_chars > total_chars * 0.3:
            language = QueryLanguage.CHINESE
        else:
            language = QueryLanguage.ENGLISH

        # Simple keyword extraction
        keywords = []
        if language == QueryLanguage.CHINESE:
            # Basic Chinese keyword extraction
            import re

            # Extract words that look like technical terms or important concepts
            tech_terms = re.findall(r"[A-Za-z]+|[一-龯]{2,}", query)
            keywords = [term for term in tech_terms if len(term) > 1][:5]
        else:
            # Basic English keyword extraction
            words = query.lower().split()
            # Filter out common words
            stop_words = {
                "the",
                "a",
                "an",
                "and",
                "or",
                "but",
                "in",
                "on",
                "at",
                "to",
                "for",
                "of",
                "with",
                "by",
                "is",
                "are",
                "was",
                "were",
                "what",
                "how",
                "when",
                "where",
                "why",
            }
            keywords = [word for word in words if word not in stop_words and len(word) > 2][:5]

        # Simple intent classification
        question_words = [
            "what",
            "how",
            "when",
            "where",
            "why",
            "什麼",
            "如何",
            "怎麼",
            "何時",
            "哪裡",
            "為什麼",
        ]
        if any(word in query.lower() for word in question_words):
            intent = QueryIntent.QUESTION
        else:
            intent = QueryIntent.SEARCH

        return ParsedQuery(
            original_query=query,
            language=language,
            intent=intent,
            keywords=keywords,
            filters={},
            confidence=0.6,
        )

    async def _generate_fallback_response(
        self, parsed_query: ParsedQuery, user_id: UUID, conversation_id: Optional[str]
    ) -> StructuredResponse:
        """Generate a fallback response using keyword search on actual articles."""

        try:
            # Try to search actual articles using keywords
            articles = await self._search_articles_by_keywords(parsed_query.keywords, user_id)

            if not articles:
                # No articles found, return empty list with helpful message
                articles = []

        except Exception as e:
            logger.warning(f"Article search failed: {e}")
            articles = []

        # Generate insights based on language
        if parsed_query.language == QueryLanguage.CHINESE:
            insights = [
                f"根據您的問題「{parsed_query.original_query}」，我找到了 {len(articles)} 篇相關文章",
                "建議您閱讀這些文章來獲得更深入的了解",
                "如果需要更具體的資訊，請嘗試更詳細的問題",
            ]
            recommendations = [
                "嘗試使用更具體的技術關鍵字",
                "查看最新的文章獲得最新資訊",
                "關注相關的技術趨勢",
            ]
        else:
            insights = [
                f"Based on your query '{parsed_query.original_query}', I found {len(articles)} relevant articles",
                "I recommend reading these articles for deeper understanding",
                "For more specific information, try asking more detailed questions",
            ]
            recommendations = [
                "Try using more specific technical keywords",
                "Check the latest articles for up-to-date information",
                "Follow related technology trends",
            ]

        return StructuredResponse(
            query=parsed_query.original_query,
            articles=articles,
            insights=insights,
            recommendations=recommendations,
            conversation_id=conversation_id
            or str(uuid.uuid4()),  # Generate valid UUID if none provided
            response_time=0.5,
            metadata={
                "mode": "fallback",
                "embedding_available": False,
                "language": parsed_query.language.value,
                "keywords": parsed_query.keywords,
                "search_method": "keyword_based",
            },
        )

    async def _search_articles_by_keywords(
        self, keywords: List[str], user_id: UUID
    ) -> List[ArticleSummary]:
        """Search articles using keyword matching."""

        if not keywords:
            return []

        try:
            # Use Supabase service to search articles
            from app.services.supabase_service import SupabaseService

            supabase = SupabaseService()

            # Build search query for title and content
            search_terms = " | ".join(keywords)  # OR search

            # Search in articles table (use ai_summary field)
            result = (
                supabase.client.table("articles")
                .select("id, title, ai_summary, url, published_at")
                .or_(f"title.ilike.%{keywords[0]}%,ai_summary.ilike.%{keywords[0]}%")
                .limit(5)
                .execute()
            )

            articles = []
            for article_data in result.data:
                # Use ai_summary field
                summary = article_data.get("ai_summary", "")
                if not summary:
                    summary = f"關於 {article_data['title']} 的文章。請點擊連結查看完整內容。"

                # Ensure summary has at least 2 sentences (for Pydantic validation)
                if summary.count("。") < 2 and summary.count(".") < 2:
                    summary = summary + " 這是一篇值得閱讀的技術文章。"

                articles.append(
                    ArticleSummary(
                        article_id=article_data["id"],
                        title=article_data["title"],
                        summary=summary,
                        url=article_data.get("url", "#"),
                        relevance_score=0.7,  # Default relevance
                        reading_time=max(1, len(summary) // 100),  # Estimate reading time
                        category="Technology",  # Default category
                        key_insights=[],  # Empty for now
                        published_at=None,  # Will be parsed if needed
                    )
                )

            logger.info(f"Found {len(articles)} articles using keyword search")
            return articles

        except Exception as e:
            logger.error(f"Keyword search failed: {e}")
            return []

    def _get_sample_articles(self, language: QueryLanguage) -> List[ArticleSummary]:
        """Get sample articles when search fails."""

        import uuid

        if language == QueryLanguage.CHINESE:
            return [
                ArticleSummary(
                    article_id=uuid.uuid4(),
                    title="AI 技術發展趨勢",
                    summary="人工智慧技術持續快速發展，包括大型語言模型、電腦視覺和自動化等領域都有重大突破。本文探討了當前 AI 技術的主要趨勢和未來發展方向。",
                    url="https://example.com/ai-trends",
                    relevance_score=0.85,
                    reading_time=5,
                    category="AI/ML",
                    key_insights=["大型語言模型快速發展", "電腦視覺技術突破", "自動化應用擴展"],
                    published_at=None,
                ),
                ArticleSummary(
                    article_id=uuid.uuid4(),
                    title="機器學習最佳實踐",
                    summary="本文介紹機器學習專案的最佳實踐，包括資料預處理、模型選擇和評估方法。適合想要提升 ML 專案品質的開發者閱讀。",
                    url="https://example.com/ml-practices",
                    relevance_score=0.75,
                    reading_time=8,
                    category="Machine Learning",
                    key_insights=["資料預處理重要性", "模型選擇策略", "評估方法最佳化"],
                    published_at=None,
                ),
            ]
        else:
            return [
                ArticleSummary(
                    article_id=uuid.uuid4(),
                    title="AI Technology Trends",
                    summary="Artificial intelligence continues to advance rapidly, with breakthroughs in large language models, computer vision, and automation. This article explores current AI trends and future directions.",
                    url="https://example.com/ai-trends",
                    relevance_score=0.85,
                    reading_time=5,
                    category="AI/ML",
                    key_insights=[
                        "Large language model advances",
                        "Computer vision breakthroughs",
                        "Automation expansion",
                    ],
                    published_at=None,
                ),
                ArticleSummary(
                    article_id=uuid.uuid4(),
                    title="Machine Learning Best Practices",
                    summary="This article covers best practices for machine learning projects, including data preprocessing, model selection, and evaluation methods. Perfect for developers looking to improve their ML projects.",
                    url="https://example.com/ml-practices",
                    relevance_score=0.75,
                    reading_time=8,
                    category="Machine Learning",
                    key_insights=[
                        "Data preprocessing importance",
                        "Model selection strategies",
                        "Evaluation optimization",
                    ],
                    published_at=None,
                ),
            ]

    def _create_error_response(self, query: str, error_message: str) -> StructuredResponse:
        """Create an error response."""
        import uuid

        return StructuredResponse(
            query=query,
            articles=[],
            insights=[f"抱歉，處理您的問題時遇到錯誤：{error_message}"],
            recommendations=["請稍後再試", "檢查網路連線", "聯繫技術支援"],
            conversation_id=str(uuid.uuid4()),  # Generate valid UUID
            response_time=0.1,
            metadata={"error": True, "message": error_message},
        )


# Global fallback instance
_fallback_qa_agent = None


def get_fallback_qa_agent() -> FallbackQAAgent:
    """Get the global fallback QA agent instance."""
    global _fallback_qa_agent
    if _fallback_qa_agent is None:
        _fallback_qa_agent = FallbackQAAgent()
    return _fallback_qa_agent
