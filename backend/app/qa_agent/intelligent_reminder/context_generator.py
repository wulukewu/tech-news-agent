"""
Context Generator for the Intelligent Reminder Agent.
Generates rich, contextual reminder content with personalized recommendations.
"""
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from ...services.llm_service import LLMService
from ...services.supabase_service import SupabaseService
from .content_analyzer import ContentAnalyzer
from .models import ReminderContext, TechnologyVersion
from .version_tracker import VersionTracker

logger = logging.getLogger(__name__)


class ContentParser:
    """Parses and extracts key information from article content"""

    @staticmethod
    def parse_article_content(content: str) -> Dict[str, Any]:
        """Parse article content and extract structured information"""
        try:
            # Extract key information
            word_count = len(content.split())
            reading_time = max(1, word_count // 200)  # 200 words per minute

            # Simple keyword extraction
            keywords = ContentParser._extract_keywords(content)

            # Extract code snippets
            code_snippets = ContentParser._extract_code_snippets(content)

            return {
                "word_count": word_count,
                "reading_time": reading_time,
                "keywords": keywords,
                "code_snippets": code_snippets,
                "has_code": len(code_snippets) > 0,
                "complexity_score": ContentParser._calculate_complexity(content),
            }

        except Exception as e:
            logger.error(f"Error parsing article content: {e}")
            return {
                "word_count": 0,
                "reading_time": 5,
                "keywords": [],
                "code_snippets": [],
                "has_code": False,
                "complexity_score": 0.5,
            }

    @staticmethod
    def _extract_keywords(content: str) -> List[str]:
        """Extract technical keywords from content"""
        # Common technical terms
        tech_keywords = [
            "python",
            "javascript",
            "react",
            "node",
            "docker",
            "kubernetes",
            "aws",
            "azure",
            "gcp",
            "api",
            "database",
            "sql",
            "nosql",
            "machine learning",
            "ai",
            "blockchain",
            "microservices",
            "typescript",
            "vue",
            "angular",
            "django",
            "flask",
            "fastapi",
        ]

        content_lower = content.lower()
        found_keywords = []

        for keyword in tech_keywords:
            if keyword in content_lower:
                found_keywords.append(keyword)

        return found_keywords[:10]  # Limit to top 10

    @staticmethod
    def _extract_code_snippets(content: str) -> List[str]:
        """Extract code snippets from content"""
        import re

        # Match code blocks (```...```)
        code_blocks = re.findall(r"```[\s\S]*?```", content)

        # Match inline code (`...`)
        inline_code = re.findall(r"`[^`]+`", content)

        return code_blocks + inline_code

    @staticmethod
    def _calculate_complexity(content: str) -> float:
        """Calculate content complexity score (0-1)"""
        complexity_indicators = [
            "advanced",
            "complex",
            "architecture",
            "design pattern",
            "optimization",
            "performance",
            "scalability",
            "enterprise",
        ]

        content_lower = content.lower()
        complexity_score = 0.0

        for indicator in complexity_indicators:
            if indicator in content_lower:
                complexity_score += 0.1

        # Boost score for code presence
        if "```" in content or "`" in content:
            complexity_score += 0.2

        return min(1.0, complexity_score)


class ContentFormatter:
    """Formats reminder content for different output formats"""

    @staticmethod
    def format_to_text(context: ReminderContext) -> str:
        """Format reminder context to plain text"""
        text = f"{context.title}\n\n{context.description}\n"

        if context.related_articles:
            text += "\nRelated Articles:\n"
            for i, article in enumerate(context.related_articles[:3], 1):
                text += f"{i}. {article.get('title', 'Untitled')}\n"

        if context.version_info:
            version_info = context.version_info
            text += f"\nVersion Update: {version_info.get('technology')} "
            text += f"{version_info.get('new_version')}\n"

        if context.reading_time_estimate:
            text += f"\nEstimated reading time: {context.reading_time_estimate} minutes\n"

        if context.action_url:
            text += f"\nRead more: {context.action_url}\n"

        return text

    @staticmethod
    def format_to_html(context: ReminderContext) -> str:
        """Format reminder context to HTML"""
        html = f"<h2>{context.title}</h2>\n<p>{context.description}</p>\n"

        if context.related_articles:
            html += "<h3>Related Articles:</h3>\n<ul>\n"
            for article in context.related_articles[:3]:
                title = article.get("title", "Untitled")
                url = article.get("url", "#")
                html += f'<li><a href="{url}">{title}</a></li>\n'
            html += "</ul>\n"

        if context.version_info:
            version_info = context.version_info
            html += "<h3>Version Update</h3>\n"
            html += f"<p><strong>{version_info.get('technology')}</strong> "
            html += f"updated to version <strong>{version_info.get('new_version')}</strong></p>\n"

        if context.reading_time_estimate:
            html += (
                f"<p><em>Estimated reading time: {context.reading_time_estimate} minutes</em></p>\n"
            )

        if context.action_url:
            html += f'<p><a href="{context.action_url}">Read more</a></p>\n'

        return html


class ContentPrettyPrinter:
    """Pretty prints structured reminder data back to readable format"""

    @staticmethod
    def pretty_print(context: ReminderContext) -> str:
        """Convert structured reminder context back to readable format"""
        output = []

        output.append(f"📋 {context.title}")
        output.append("=" * len(context.title))
        output.append("")
        output.append(context.description)
        output.append("")

        if context.related_articles:
            output.append("🔗 Related Articles:")
            for i, article in enumerate(context.related_articles, 1):
                title = article.get("title", "Untitled")
                confidence = article.get("confidence_score", 0)
                output.append(f"  {i}. {title} (confidence: {confidence:.2f})")
            output.append("")

        if context.version_info:
            version_info = context.version_info
            output.append("🆕 Version Update:")
            output.append(f"  Technology: {version_info.get('technology')}")
            output.append(f"  New Version: {version_info.get('new_version')}")
            if version_info.get("previous_version"):
                output.append(f"  Previous: {version_info.get('previous_version')}")
            output.append(f"  Type: {version_info.get('version_type', 'unknown')}")
            output.append("")

        if context.reading_time_estimate:
            output.append(f"⏱️ Estimated reading time: {context.reading_time_estimate} minutes")
            output.append("")

        output.append(f"🎯 Priority Score: {context.priority_score:.2f}")

        if context.action_url:
            output.append(f"🔗 Action URL: {context.action_url}")

        return "\n".join(output)


class ContextGenerator:
    """Generates rich contextual reminders with personalized content"""

    def __init__(
        self,
        llm_service: Optional[LLMService] = None,
        supabase_service: Optional[SupabaseService] = None,
        content_analyzer: Optional[ContentAnalyzer] = None,
        version_tracker: Optional[VersionTracker] = None,
    ):
        self.llm_service = llm_service or LLMService()
        self.supabase_service = supabase_service or SupabaseService()
        self.content_analyzer = content_analyzer or ContentAnalyzer(llm_service, supabase_service)
        self.version_tracker = version_tracker or VersionTracker(supabase_service)

    async def generate_article_relation_reminder(
        self, user_id: UUID, article_id: UUID, relationship_type: str
    ) -> ReminderContext:
        """Generate reminder for related articles"""
        try:
            # Get article and related articles
            article = await self._get_article(article_id)
            if not article:
                return self._create_fallback_context("Article not found")

            related_articles = await self.content_analyzer.get_related_articles(
                article_id, [relationship_type] if relationship_type else None
            )

            # Get user preferences for personalization
            user_interests = await self._get_user_interests(user_id)

            # Generate personalized context
            context = await self._generate_personalized_article_context(
                article, related_articles, relationship_type, user_interests
            )

            return context

        except Exception as e:
            logger.error(f"Error generating article relation reminder: {e}")
            return self._create_fallback_context("Error generating reminder")

    async def generate_version_update_reminder(
        self, user_id: UUID, tech_version: TechnologyVersion
    ) -> ReminderContext:
        """Generate reminder for technology version updates"""
        try:
            # Check if user is interested in this technology
            user_interests = await self._get_user_interests(user_id)

            # Generate version update context
            context = await self.version_tracker.generate_version_update_context(tech_version)

            # Personalize based on user's technical level and interests
            if tech_version.technology_name.lower() in [
                interest.lower() for interest in user_interests
            ]:
                context.priority_score = min(1.0, context.priority_score + 0.2)
                context.description += f"\n\nThis update is particularly relevant to your interests in {tech_version.technology_name}."

            # Add personalized reading suggestions
            related_articles = await self._find_related_articles_for_technology(
                tech_version.technology_name
            )
            if related_articles:
                context.related_articles = related_articles[:3]
                context.description += (
                    f"\n\nWe found {len(related_articles)} related articles in your reading list."
                )

            return context

        except Exception as e:
            logger.error(f"Error generating version update reminder: {e}")
            return self._create_fallback_context("Version update available")

    async def generate_learning_path_reminder(
        self, user_id: UUID, learning_goal: str, next_articles: List[Dict[str, Any]]
    ) -> ReminderContext:
        """Generate reminder for learning path progression"""
        try:
            # Get user's learning progress
            progress = await self._get_learning_progress(user_id, learning_goal)

            title = f"Continue your {learning_goal} learning journey"
            description = f"You're making great progress! Here are the next recommended articles in your {learning_goal} learning path."

            if progress:
                completion_rate = progress.get("completion_rate", 0)
                description += f"\n\nYou've completed {completion_rate:.0%} of your learning goals."

            # Calculate total reading time
            total_reading_time = sum(
                self._estimate_reading_time(article.get("content", ""))
                for article in next_articles[:3]
            )

            return ReminderContext(
                title=title,
                description=description,
                related_articles=next_articles[:3],
                reading_time_estimate=total_reading_time,
                priority_score=0.7,  # Learning path reminders are generally high priority
                action_url=f"/learning-path/{learning_goal}",
            )

        except Exception as e:
            logger.error(f"Error generating learning path reminder: {e}")
            return self._create_fallback_context("Continue your learning journey")

    async def _generate_personalized_article_context(
        self,
        article: Dict[str, Any],
        related_articles: List[Dict[str, Any]],
        relationship_type: str,
        user_interests: List[str],
    ) -> ReminderContext:
        """Generate personalized context for article reminders"""

        # Parse article content
        parsed_content = ContentParser.parse_article_content(
            article.get("content", "") or article.get("ai_summary", "")
        )

        # Generate title based on relationship type
        if relationship_type == "prerequisite":
            title = f"Prerequisites for: {article['title']}"
            description = "We found some articles that will help you better understand this topic."
        elif relationship_type == "follow_up":
            title = f"Continue reading: {article['title']}"
            description = "Ready to dive deeper? Here are some follow-up articles."
        else:
            title = f"Related to: {article['title']}"
            description = "You might find these related articles interesting."

        # Add personalization based on user interests
        article_keywords = parsed_content.get("keywords", [])
        matching_interests = set(article_keywords) & set(
            [interest.lower() for interest in user_interests]
        )

        if matching_interests:
            description += (
                f"\n\nThis content matches your interests in: {', '.join(matching_interests)}."
            )

        # Add complexity note
        complexity = parsed_content.get("complexity_score", 0.5)
        if complexity > 0.7:
            description += "\n\nNote: This content is marked as advanced level."
        elif complexity < 0.3:
            description += "\n\nThis is beginner-friendly content."

        return ReminderContext(
            title=title,
            description=description,
            related_articles=related_articles[:3],
            reading_time_estimate=parsed_content.get("reading_time", 5),
            priority_score=min(1.0, 0.5 + len(matching_interests) * 0.1),
            action_url=f"/articles/{article['id']}",
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

    async def _get_user_interests(self, user_id: UUID) -> List[str]:
        """Get user's technical interests from reading history"""
        try:
            # Get highly rated articles
            query = """
            SELECT a.title, a.ai_summary
            FROM reading_list rl
            JOIN articles a ON a.id = rl.article_id
            WHERE rl.user_id = $1 AND rl.rating >= 4
            ORDER BY rl.updated_at DESC
            LIMIT 10
            """

            result = await self.supabase_service.client.rpc(
                "execute_sql", {"query": query, "params": [str(user_id)]}
            ).execute()

            interests = []
            if result.data:
                # Extract keywords from highly rated content
                all_content = " ".join(
                    [
                        (row.get("title", "") + " " + row.get("ai_summary", "")).lower()
                        for row in result.data
                    ]
                )

                # Common technical terms
                tech_terms = [
                    "python",
                    "javascript",
                    "react",
                    "node",
                    "docker",
                    "kubernetes",
                    "aws",
                    "azure",
                    "gcp",
                    "machine learning",
                    "ai",
                    "blockchain",
                    "typescript",
                    "vue",
                    "angular",
                    "django",
                    "flask",
                    "fastapi",
                ]

                for term in tech_terms:
                    if term in all_content:
                        interests.append(term)

            return interests

        except Exception as e:
            logger.error(f"Error getting user interests for {user_id}: {e}")
            return []

    async def _find_related_articles_for_technology(
        self, technology_name: str
    ) -> List[Dict[str, Any]]:
        """Find articles related to a specific technology"""
        try:
            search_term = f"%{technology_name}%"

            result = (
                await self.supabase_service.client.table("articles")
                .select("id, title, url, ai_summary")
                .or_(f"title.ilike.{search_term},ai_summary.ilike.{search_term}")
                .order("published_at", desc=True)
                .limit(5)
                .execute()
            )

            return result.data if result.data else []

        except Exception as e:
            logger.error(f"Error finding articles for technology {technology_name}: {e}")
            return []

    async def _get_learning_progress(
        self, user_id: UUID, learning_goal: str
    ) -> Optional[Dict[str, Any]]:
        """Get user's learning progress for a specific goal"""
        try:
            # This would integrate with the learning path system
            # For now, return a simple mock
            return {"completion_rate": 0.6, "articles_completed": 8, "total_articles": 12}

        except Exception as e:
            logger.error(f"Error getting learning progress: {e}")
            return None

    def _estimate_reading_time(self, content: str) -> int:
        """Estimate reading time in minutes"""
        if not content:
            return 5

        word_count = len(content.split())
        return max(1, word_count // 200)  # 200 words per minute

    def _create_fallback_context(self, message: str) -> ReminderContext:
        """Create a fallback context when generation fails"""
        return ReminderContext(
            title="New Content Available",
            description=message,
            reading_time_estimate=5,
            priority_score=0.5,
        )
