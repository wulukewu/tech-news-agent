"""
Insight Report Generator

Orchestrates the full weekly insights pipeline and persists the report.
Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 6.1, 6.2, 6.3
"""

import json
import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from app.services.supabase_service import SupabaseService

from .article_analyzer import ArticleAnalyzer
from .article_collector import ArticleCollector
from .personalization_engine import PersonalizationEngine
from .theme_clusterer import ThemeClusterer
from .trend_detector import TrendDetector

logger = logging.getLogger(__name__)


class InsightReportGenerator:
    """Orchestrates the weekly insights pipeline."""

    def __init__(self, supabase_service: SupabaseService | None = None):
        self.supabase = supabase_service or SupabaseService()
        self.collector = ArticleCollector(self.supabase)
        self.analyzer = ArticleAnalyzer()
        self.clusterer = ThemeClusterer()
        self.trend_detector = TrendDetector(self.supabase)
        self.personalization = PersonalizationEngine(self.supabase)

    async def generate(
        self,
        days: int = 7,
        end_date: datetime | None = None,
        user_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Run the full pipeline and return a structured insight report.

        Args:
            days: Number of days to analyze (default 7).
            end_date: End of the analysis window (default: now UTC).
            user_id: Optional user ID for personalization.

        Returns:
            Report dict with keys: id, period_start, period_end, article_count,
            executive_summary, clusters, trends, missed_articles, trend_data,
            created_at.
        """
        if end_date is None:
            end_date = datetime.now(UTC)
        start_date = end_date - timedelta(days=days)

        logger.info("Generating weekly insights report (%d days)", days)

        # 1. Collect articles (cap at 30 to stay within Groq free tier TPM)
        articles = await self.collector.collect_weekly_articles(days=days, end_date=end_date)
        articles = articles[:30]
        if not articles:
            logger.warning("No articles found for the period")
            return self._empty_report(start_date, end_date)

        # 2. Analyze articles (extract themes/technologies)
        analyzed = await self.analyzer.analyze_articles(articles)

        # Fallback: if LLM analysis yielded no themes at all, use keyword-based analysis
        has_themes = any(a.get("themes") for a in analyzed)
        if not has_themes:
            logger.info("LLM analysis produced no themes, using keyword fallback")
            analyzed = [self._keyword_analyze(a) for a in articles]

        # 3. Cluster themes
        clusters = self.clusterer.cluster(analyzed)

        # 4. Detect trends
        historical = await self.trend_detector.load_historical_counts()
        trends = self.trend_detector.detect_trends(analyzed, historical)

        # 5. Personalization (optional)
        missed_articles: list[dict[str, Any]] = []
        if user_id:
            interests = await self.personalization.get_user_interests(user_id)
            clusters = self.personalization.personalize_clusters(clusters, interests)
            missed_articles = self.personalization.get_missed_articles(analyzed, interests)

        # 6. Build executive summary
        top_themes = [c["name"] for c in clusters[:3]]
        rising_trends = [t["name"] for t in trends if t["direction"] == "rising"][:3]
        executive_summary = self._build_summary(len(articles), top_themes, rising_trends)

        # 7. Serialize clusters (strip full article lists for storage, keep top 3)
        clusters_serializable = [
            {
                "name": c["name"],
                "article_count": c["article_count"],
                "strength": c["strength"],
                "top_keywords": c["top_keywords"],
                "top_articles": [
                    {"id": a.get("id"), "title": a.get("title"), "url": a.get("url")}
                    for a in c.get("articles", [])[:3]
                ],
            }
            for c in clusters[:10]
        ]

        report: dict[str, Any] = {
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "article_count": len(articles),
            "executive_summary": executive_summary,
            "clusters": clusters_serializable,
            "trends": trends[:20],
            "missed_articles": [
                {
                    "id": a.get("id"),
                    "title": a.get("title"),
                    "url": a.get("url"),
                    "tinkering_index": a.get("tinkering_index"),
                }
                for a in missed_articles
            ],
            "trend_data": trends[:20],  # stored for historical comparison
            "created_at": datetime.now(UTC).isoformat(),
        }

        # 8. Persist to Supabase
        report_id = await self._save_report(report)
        report["id"] = report_id

        logger.info("Weekly insights report generated (id=%s)", report_id)
        return report

    def _build_summary(
        self,
        article_count: int,
        top_themes: list[str],
        rising_trends: list[str],
    ) -> str:
        themes_str = ", ".join(top_themes) if top_themes else "various topics"
        trends_str = ", ".join(rising_trends) if rising_trends else "no clear emerging trends"
        return (
            f"This week's digest covers {article_count} articles. "
            f"Top themes: {themes_str}. "
            f"Rising trends: {trends_str}."
        )

    def _keyword_analyze(self, article: dict[str, Any]) -> dict[str, Any]:
        """
        Fallback keyword-based analysis when LLM is unavailable.
        Extracts themes/technologies from title + summary using simple keyword matching.
        """
        KEYWORD_MAP: dict[str, tuple[str, str]] = {
            # (domain, theme)
            "react": ("frontend", "React"),
            "vue": ("frontend", "Vue"),
            "angular": ("frontend", "Angular"),
            "next.js": ("frontend", "Next.js"),
            "typescript": ("frontend", "TypeScript"),
            "javascript": ("frontend", "JavaScript"),
            "css": ("frontend", "CSS"),
            "python": ("backend", "Python"),
            "rust": ("backend", "Rust"),
            "go": ("backend", "Go"),
            "java": ("backend", "Java"),
            "node": ("backend", "Node.js"),
            "fastapi": ("backend", "FastAPI"),
            "django": ("backend", "Django"),
            "docker": ("devops", "Docker"),
            "kubernetes": ("devops", "Kubernetes"),
            "ci/cd": ("devops", "CI/CD"),
            "github": ("devops", "GitHub"),
            "terraform": ("devops", "Terraform"),
            "llm": ("ai_ml", "LLM"),
            "gpt": ("ai_ml", "GPT"),
            "openai": ("ai_ml", "OpenAI"),
            "machine learning": ("ai_ml", "Machine Learning"),
            "deep learning": ("ai_ml", "Deep Learning"),
            "ai": ("ai_ml", "AI"),
            "neural": ("ai_ml", "Neural Networks"),
            "security": ("security", "Security"),
            "vulnerability": ("security", "Security"),
            "encryption": ("security", "Encryption"),
            "aws": ("cloud", "AWS"),
            "azure": ("cloud", "Azure"),
            "gcp": ("cloud", "GCP"),
            "cloud": ("cloud", "Cloud"),
            "ios": ("mobile", "iOS"),
            "android": ("mobile", "Android"),
            "swift": ("mobile", "Swift"),
            "flutter": ("mobile", "Flutter"),
            "postgresql": ("database", "PostgreSQL"),
            "mysql": ("database", "MySQL"),
            "redis": ("database", "Redis"),
            "mongodb": ("database", "MongoDB"),
        }
        text = ((article.get("title") or "") + " " + (article.get("ai_summary") or "")).lower()

        themes: list[str] = []
        technologies: list[str] = []
        domain = "other"
        keywords: list[str] = []

        for kw, (dom, theme) in KEYWORD_MAP.items():
            if kw in text:
                if theme not in themes:
                    themes.append(theme)
                if theme not in technologies:
                    technologies.append(theme)
                if domain == "other":
                    domain = dom
                if kw not in keywords:
                    keywords.append(kw)

        return {
            **article,
            "themes": themes[:5],
            "technologies": technologies[:5],
            "domain": domain,
            "keywords": keywords[:5],
        }

    def _empty_report(self, start_date: datetime, end_date: datetime) -> dict[str, Any]:
        return {
            "id": None,
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "article_count": 0,
            "executive_summary": "No articles found for this period.",
            "clusters": [],
            "trends": [],
            "missed_articles": [],
            "trend_data": [],
            "created_at": datetime.now(UTC).isoformat(),
        }

    async def _save_report(self, report: dict[str, Any]) -> str | None:
        """Persist the report to the weekly_insights table."""
        try:
            row = {
                "period_start": report["period_start"],
                "period_end": report["period_end"],
                "article_count": report["article_count"],
                "executive_summary": report["executive_summary"],
                "clusters": json.dumps(report["clusters"]),
                "trends": json.dumps(report["trends"]),
                "missed_articles": json.dumps(report["missed_articles"]),
                "trend_data": json.dumps(report["trend_data"]),
            }
            response = self.supabase.client.table("weekly_insights").insert(row).execute()
            rows = response.data or []
            return rows[0].get("id") if rows else None
        except Exception as exc:
            logger.error("Failed to save weekly insights report: %s", exc)
            return None
