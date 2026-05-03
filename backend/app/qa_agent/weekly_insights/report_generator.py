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

# If a pending record is older than this, assume it was interrupted
STALE_PENDING_MINUTES = 10


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

        Inserts a 'pending' row before starting so that a restart can detect
        and resume interrupted jobs via resume_if_needed().
        """
        if end_date is None:
            end_date = datetime.now(UTC)
        start_date = end_date - timedelta(days=days)

        logger.info("Generating weekly insights report (%d days)", days)

        pending_id = await self._insert_pending(start_date, end_date)

        try:
            report = await self._run_pipeline(
                days=days, start_date=start_date, end_date=end_date, user_id=user_id
            )
        except Exception as exc:
            if pending_id:
                await self._update_status(pending_id, "failed")
            raise exc

        report_id = await self._save_report(report, pending_id)
        report["id"] = report_id
        logger.info("Weekly insights report generated (id=%s)", report_id)
        return report

    async def resume_if_needed(self) -> None:
        """
        Called at startup. Checks for:
        1. Stale 'pending' records (interrupted mid-generation) → re-run
        2. Missing report for the current week → generate now

        This ensures a CD deploy that interrupted a job will self-heal.
        """
        try:
            now = datetime.now(UTC)
            stale_cutoff = now - timedelta(minutes=STALE_PENDING_MINUTES)

            response = (
                self.supabase.client.table("weekly_insights")
                .select("id, status, started_at, period_start, period_end")
                .in_("status", ["pending", "failed"])
                .execute()
            )
            rows = response.data or []

            for row in rows:
                started_at = row.get("started_at")
                if row["status"] == "pending" and started_at:
                    started_dt = datetime.fromisoformat(started_at)
                    if started_dt > stale_cutoff:
                        # Still within grace period, don't interrupt
                        continue
                logger.info(
                    "Resuming interrupted/failed insights job (id=%s, status=%s)",
                    row["id"],
                    row["status"],
                )
                await self._update_status(row["id"], "failed")  # mark old one as failed
                await self.generate()
                return  # one at a time

            # Check if current week is missing a completed report
            week_start = now - timedelta(days=now.weekday())  # Monday
            week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)

            response = (
                self.supabase.client.table("weekly_insights")
                .select("id")
                .eq("status", "completed")
                .gte("period_end", week_start.isoformat())
                .limit(1)
                .execute()
            )
            if not (response.data or []):
                logger.info("No completed report for current week — generating now")
                await self.generate()

        except Exception as exc:
            logger.error("resume_if_needed failed: %s", exc, exc_info=True)

    async def _run_pipeline(
        self,
        days: int,
        start_date: datetime,
        end_date: datetime,
        user_id: str | None,
    ) -> dict[str, Any]:
        # 1. Collect articles
        articles = await self.collector.collect_weekly_articles(days=days, end_date=end_date)
        if not articles:
            logger.warning("No articles found for the period")
            return self._empty_report(start_date, end_date)

        # 2. Analyze articles (extract themes/technologies)
        analyzed = await self.analyzer.analyze_articles(articles)

        # Fallback: apply keyword analysis to any article that has no themes
        analyzed = [a if a.get("themes") else self._keyword_analyze(a) for a in analyzed]

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

        return {
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
            "trend_data": trends[:20],
            "created_at": datetime.now(UTC).isoformat(),
        }

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

    async def _insert_pending(self, start_date: datetime, end_date: datetime) -> str | None:
        """Insert a pending record before generation starts."""
        try:
            response = (
                self.supabase.client.table("weekly_insights")
                .insert(
                    {
                        "period_start": start_date.isoformat(),
                        "period_end": end_date.isoformat(),
                        "article_count": 0,
                        "status": "pending",
                        "started_at": datetime.now(UTC).isoformat(),
                    }
                )
                .execute()
            )
            rows = response.data or []
            return rows[0].get("id") if rows else None
        except Exception as exc:
            logger.warning("Failed to insert pending record: %s", exc)
            return None

    async def _update_status(self, report_id: str, status: str) -> None:
        try:
            self.supabase.client.table("weekly_insights").update({"status": status}).eq(
                "id", report_id
            ).execute()
        except Exception as exc:
            logger.warning("Failed to update report status: %s", exc)

    async def _save_report(
        self, report: dict[str, Any], pending_id: str | None = None
    ) -> str | None:
        """Update the pending record with full data, or insert a new completed record."""
        row = {
            "period_start": report["period_start"],
            "period_end": report["period_end"],
            "article_count": report["article_count"],
            "executive_summary": report["executive_summary"],
            "clusters": json.dumps(report["clusters"]),
            "trends": json.dumps(report["trends"]),
            "missed_articles": json.dumps(report["missed_articles"]),
            "trend_data": json.dumps(report["trend_data"]),
            "status": "completed",
        }
        try:
            if pending_id:
                response = (
                    self.supabase.client.table("weekly_insights")
                    .update(row)
                    .eq("id", pending_id)
                    .execute()
                )
                rows = response.data or []
                return rows[0].get("id") if rows else pending_id
            else:
                response = self.supabase.client.table("weekly_insights").insert(row).execute()
                rows = response.data or []
                return rows[0].get("id") if rows else None
        except Exception as exc:
            logger.error("Failed to save weekly insights report: %s", exc)
            return pending_id
