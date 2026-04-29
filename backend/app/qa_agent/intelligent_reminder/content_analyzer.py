"""
Content Analyzer for the Intelligent Reminder Agent.
Analyzes article relationships and builds the article graph.
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from ...services.llm_service import LLMService
from ...services.supabase_service import SupabaseService
from .models import ArticleRelationship, RelationshipType, ReminderContext

logger = logging.getLogger(__name__)


class ContentAnalyzer:
    """Analyzes article content and builds relationship graphs"""

    def __init__(
        self,
        llm_service: Optional[LLMService] = None,
        supabase_service: Optional[SupabaseService] = None,
    ):
        self.llm_service = llm_service or LLMService()
        self.supabase_service = supabase_service or SupabaseService()

    async def analyze_article_relationships(self, article_id: UUID) -> List[ArticleRelationship]:
        """
        Analyze relationships between an article and existing articles.
        Must complete within 5 seconds as per requirements.
        """
        try:
            # Get the target article
            article = await self._get_article(article_id)
            if not article:
                logger.warning(f"Article {article_id} not found")
                return []

            # Get recent articles for comparison (limit for performance)
            recent_articles = await self._get_recent_articles(limit=50)

            # Analyze relationships with timeout
            relationships = await asyncio.wait_for(
                self._analyze_relationships_batch(article, recent_articles),
                timeout=4.5,  # Leave 0.5s buffer
            )

            # Store relationships in database
            await self._store_relationships(relationships)

            return relationships

        except asyncio.TimeoutError:
            logger.warning(f"Relationship analysis for article {article_id} timed out")
            return []
        except Exception as e:
            logger.error(f"Error analyzing relationships for article {article_id}: {e}")
            return []

    async def update_article_graph(self, new_article_id: UUID) -> None:
        """Update the article graph when a new article is added"""
        relationships = await self.analyze_article_relationships(new_article_id)
        logger.info(f"Added {len(relationships)} relationships for article {new_article_id}")

    async def get_related_articles(
        self, article_id: UUID, relationship_types: Optional[List[RelationshipType]] = None
    ) -> List[Dict[str, Any]]:
        """Get articles related to the given article"""
        try:
            query = """
            SELECT ag.*, a.title, a.url, a.published_at, a.ai_summary
            FROM article_graph ag
            JOIN articles a ON a.id = ag.target_article_id
            WHERE ag.source_article_id = $1
            """
            params = [str(article_id)]

            if relationship_types:
                placeholders = ",".join(f"${i+2}" for i in range(len(relationship_types)))
                query += f" AND ag.relationship_type = ANY(ARRAY[{placeholders}])"
                params.extend([rt.value for rt in relationship_types])

            query += " ORDER BY ag.confidence_score DESC, a.published_at DESC"

            result = await self.supabase_service.client.rpc(
                "execute_sql", {"query": query, "params": params}
            ).execute()

            return result.data if result.data else []

        except Exception as e:
            logger.error(f"Error getting related articles for {article_id}: {e}")
            return []

    async def identify_prerequisites(self, article_id: UUID) -> List[Dict[str, Any]]:
        """Identify prerequisite articles for the given article"""
        return await self.get_related_articles(article_id, [RelationshipType.PREREQUISITE])

    async def identify_follow_ups(self, article_id: UUID) -> List[Dict[str, Any]]:
        """Identify follow-up articles for the given article"""
        return await self.get_related_articles(article_id, [RelationshipType.FOLLOW_UP])

    async def generate_reminder_context(
        self, article_id: UUID, relationship_type: RelationshipType
    ) -> ReminderContext:
        """Generate context for a reminder about related articles"""
        try:
            article = await self._get_article(article_id)
            related_articles = await self.get_related_articles(article_id, [relationship_type])

            if not article or not related_articles:
                return ReminderContext(
                    title="Related Content Available",
                    description="New related content has been found.",
                )

            # Generate context based on relationship type
            if relationship_type == RelationshipType.PREREQUISITE:
                title = f"Prerequisites for: {article['title']}"
                description = f"Found {len(related_articles)} prerequisite articles that might help you understand this topic better."
            elif relationship_type == RelationshipType.FOLLOW_UP:
                title = f"Follow-up reading for: {article['title']}"
                description = f"Found {len(related_articles)} articles that build upon this topic."
            else:
                title = f"Related to: {article['title']}"
                description = (
                    f"Found {len(related_articles)} related articles you might find interesting."
                )

            # Estimate reading time
            reading_time = sum(
                self._estimate_reading_time(ra.get("ai_summary", "")) for ra in related_articles[:3]
            )

            return ReminderContext(
                title=title,
                description=description,
                related_articles=related_articles[:3],  # Limit to top 3
                reading_time_estimate=reading_time,
                priority_score=min(related_articles[0]["confidence_score"], 1.0)
                if related_articles
                else 0.5,
                action_url=f"/articles/{article_id}",
            )

        except Exception as e:
            logger.error(f"Error generating reminder context: {e}")
            return ReminderContext(
                title="Related Content Available", description="New related content has been found."
            )

    async def _get_article(self, article_id: UUID) -> Optional[Dict[str, Any]]:
        """Get article by ID"""
        try:
            result = (
                await self.supabase_service.client.table("articles")
                .select("*")
                .eq("id", str(article_id))
                .execute()
            )
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error getting article {article_id}: {e}")
            return None

    async def _get_recent_articles(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent articles for relationship analysis"""
        try:
            result = (
                await self.supabase_service.client.table("articles")
                .select("id, title, content, ai_summary, published_at")
                .order("published_at", desc=True)
                .limit(limit)
                .execute()
            )
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Error getting recent articles: {e}")
            return []

    async def _analyze_relationships_batch(
        self, target_article: Dict[str, Any], candidate_articles: List[Dict[str, Any]]
    ) -> List[ArticleRelationship]:
        """Analyze relationships between target article and candidates using LLM"""
        relationships = []

        # Prepare prompt for LLM analysis
        prompt = self._build_relationship_analysis_prompt(target_article, candidate_articles)

        try:
            # Use LLM to analyze relationships
            response = await self.llm_service.generate_completion(
                prompt=prompt, max_tokens=1000, temperature=0.1
            )

            # Parse LLM response
            analysis_result = self._parse_relationship_analysis(response)

            # Convert to ArticleRelationship objects
            for rel_data in analysis_result:
                if rel_data.get("confidence", 0) >= 0.3:  # Minimum confidence threshold
                    relationships.append(
                        ArticleRelationship(
                            id=UUID(
                                "00000000-0000-0000-0000-000000000000"
                            ),  # Will be generated by DB
                            source_article_id=UUID(target_article["id"]),
                            target_article_id=UUID(rel_data["target_id"]),
                            relationship_type=RelationshipType(rel_data["type"]),
                            confidence_score=rel_data["confidence"],
                            analysis_metadata=rel_data.get("metadata", {}),
                            created_at=datetime.now(),
                            updated_at=datetime.now(),
                        )
                    )

        except Exception as e:
            logger.error(f"Error in LLM relationship analysis: {e}")

        return relationships

    def _build_relationship_analysis_prompt(
        self, target_article: Dict[str, Any], candidates: List[Dict[str, Any]]
    ) -> str:
        """Build prompt for LLM relationship analysis"""
        prompt = f"""Analyze the relationships between the target article and candidate articles.

Target Article:
Title: {target_article['title']}
Summary: {target_article.get('ai_summary', target_article.get('content', '')[:500])}

Candidate Articles:
"""

        for i, candidate in enumerate(candidates[:10]):  # Limit to 10 for prompt size
            prompt += f"{i+1}. ID: {candidate['id']}, Title: {candidate['title']}\n"
            prompt += (
                f"   Summary: {candidate.get('ai_summary', candidate.get('content', ''))[:200]}\n\n"
            )

        prompt += """
Identify relationships and return JSON array with format:
[
  {
    "target_id": "article_id",
    "type": "prerequisite|follow_up|related|update",
    "confidence": 0.0-1.0,
    "metadata": {"reason": "explanation"}
  }
]

Only include relationships with confidence >= 0.3.
"""

        return prompt

    def _parse_relationship_analysis(self, llm_response: str) -> List[Dict[str, Any]]:
        """Parse LLM response for relationship analysis"""
        try:
            # Extract JSON from response
            start_idx = llm_response.find("[")
            end_idx = llm_response.rfind("]") + 1

            if start_idx == -1 or end_idx == 0:
                return []

            json_str = llm_response[start_idx:end_idx]
            return json.loads(json_str)

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Error parsing LLM relationship analysis: {e}")
            return []

    async def _store_relationships(self, relationships: List[ArticleRelationship]) -> None:
        """Store relationships in the database"""
        if not relationships:
            return

        try:
            # Convert to database format
            data = []
            for rel in relationships:
                data.append(
                    {
                        "source_article_id": str(rel.source_article_id),
                        "target_article_id": str(rel.target_article_id),
                        "relationship_type": rel.relationship_type.value,
                        "confidence_score": rel.confidence_score,
                        "analysis_metadata": rel.analysis_metadata,
                    }
                )

            # Insert with conflict resolution (upsert)
            await self.supabase_service.client.table("article_graph").upsert(data).execute()

        except Exception as e:
            logger.error(f"Error storing relationships: {e}")

    def _estimate_reading_time(self, text: str) -> int:
        """Estimate reading time in minutes (200 words per minute)"""
        if not text:
            return 0
        word_count = len(text.split())
        return max(1, word_count // 200)
