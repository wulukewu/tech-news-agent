#!/usr/bin/env python3
"""
Enhanced RSS Processing Pipeline
Integrates content classification into the existing RSS processing workflow.
"""

import asyncio
import os
import sys

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.logger import get_logger
from app.schemas.article import ArticleSchema
from app.services.content_classification_service import ContentClassificationService
from app.services.llm_service import LLMService
from app.services.quality_assurance_system import QualityAssuranceSystem
from app.services.rss_service import RSSService
from app.services.supabase_service import SupabaseService

logger = get_logger(__name__)


class EnhancedRSSProcessor:
    """Enhanced RSS processor with content classification."""

    def __init__(self):
        self.supabase_service = SupabaseService()
        self.rss_service = RSSService(self.supabase_service)
        self.llm_service = LLMService()
        self.classifier = ContentClassificationService(self.llm_service, self.supabase_service)
        self.quality_system = QualityAssuranceSystem(self.supabase_service)

    async def process_all_feeds(self, classify_new_articles: bool = True) -> dict:
        """Process all feeds with enhanced classification."""
        try:
            logger.info("Starting enhanced RSS processing...")

            # Get all active feeds
            feeds_result = (
                self.supabase_service.client.table("feeds")
                .select("*")
                .eq("is_active", True)
                .execute()
            )

            if not feeds_result.data:
                logger.warning("No active feeds found")
                return {"success": False, "error": "No active feeds"}

            total_feeds = len(feeds_result.data)
            processed_feeds = 0
            total_articles = 0
            classified_articles = 0

            logger.info(f"Processing {total_feeds} active feeds...")

            for feed in feeds_result.data:
                try:
                    logger.info(f"Processing feed: {feed['name']}")

                    # Fetch articles using existing RSS service
                    articles = await self.rss_service.fetch_feed_articles(feed["url"])

                    if not articles:
                        logger.info(f"No new articles from {feed['name']}")
                        continue

                    # Process each article
                    for article_data in articles:
                        try:
                            # Create article schema
                            article = ArticleSchema(
                                id=article_data.get("id"),
                                title=article_data["title"],
                                url=article_data["url"],
                                content=article_data.get("content", ""),
                                published_at=article_data["published_at"],
                                feed_id=feed["id"],
                                tinkering_index=article_data.get("tinkering_index", 0),
                                ai_summary=article_data.get("ai_summary", ""),
                            )

                            # Classify article if requested and not already classified
                            if classify_new_articles:
                                existing_classification = (
                                    self.supabase_service.client.table("article_classifications")
                                    .select("id")
                                    .eq("article_id", article.id)
                                    .execute()
                                )

                                if not existing_classification.data:
                                    classification = await self.classifier.classify_article(article)
                                    classified_articles += 1
                                    logger.info(
                                        f"Classified article: {article.title[:50]}... "
                                        f"({classification.content_type.value}, "
                                        f"learning_value: {classification.learning_value_score:.2f})"
                                    )

                            total_articles += 1

                        except Exception as e:
                            logger.error(
                                f"Failed to process article {article_data.get('title', 'unknown')}: {e}"
                            )
                            continue

                    processed_feeds += 1
                    logger.info(f"Completed feed: {feed['name']} ({len(articles)} articles)")

                except Exception as e:
                    logger.error(f"Failed to process feed {feed['name']}: {e}")
                    continue

            logger.info(
                f"Enhanced RSS processing completed: {processed_feeds}/{total_feeds} feeds, {total_articles} articles, {classified_articles} classified"
            )

            return {
                "success": True,
                "processed_feeds": processed_feeds,
                "total_feeds": total_feeds,
                "total_articles": total_articles,
                "classified_articles": classified_articles,
            }

        except Exception as e:
            logger.error(f"Enhanced RSS processing failed: {e}")
            return {"success": False, "error": str(e)}

    async def classify_existing_articles(self, limit: int = 100) -> dict:
        """Classify existing articles that haven't been classified yet."""
        try:
            logger.info(f"Classifying up to {limit} existing articles...")

            # Get unclassified articles
            unclassified_result = (
                self.supabase_service.client.table("articles")
                .select("*")
                .not_.in_(
                    "id",
                    self.supabase_service.client.table("article_classifications").select(
                        "article_id"
                    ),
                )
                .limit(limit)
                .execute()
            )

            if not unclassified_result.data:
                logger.info("No unclassified articles found")
                return {"success": True, "classified": 0}

            classified_count = 0

            for article_data in unclassified_result.data:
                try:
                    article = ArticleSchema(**article_data)
                    classification = await self.classifier.classify_article(article)
                    classified_count += 1

                    logger.info(
                        f"Classified: {article.title[:50]}... "
                        f"({classification.content_type.value}, "
                        f"score: {classification.learning_value_score:.2f})"
                    )

                except Exception as e:
                    logger.error(
                        f"Failed to classify article {article_data.get('title', 'unknown')}: {e}"
                    )
                    continue

            logger.info(f"Classification completed: {classified_count} articles classified")

            return {"success": True, "classified": classified_count}

        except Exception as e:
            logger.error(f"Article classification failed: {e}")
            return {"success": False, "error": str(e)}

    async def get_processing_stats(self) -> dict:
        """Get processing and classification statistics."""
        try:
            # Get total articles
            total_articles_result = (
                self.supabase_service.client.table("articles").select("id", count="exact").execute()
            )
            total_articles = total_articles_result.count

            # Get classified articles
            classified_result = (
                self.supabase_service.client.table("article_classifications")
                .select("id", count="exact")
                .execute()
            )
            classified_articles = classified_result.count

            # Get educational content stats
            educational_result = (
                self.supabase_service.client.table("article_classifications")
                .select("content_type", count="exact")
                .in_("content_type", ["tutorial", "guide", "project", "reference"])
                .execute()
            )
            educational_articles = educational_result.count

            # Get quality overview
            quality_overview = await self.quality_system.get_quality_overview()

            return {
                "total_articles": total_articles,
                "classified_articles": classified_articles,
                "classification_rate": classified_articles / total_articles
                if total_articles > 0
                else 0,
                "educational_articles": educational_articles,
                "educational_ratio": educational_articles / classified_articles
                if classified_articles > 0
                else 0,
                "quality_overview": quality_overview,
            }

        except Exception as e:
            logger.error(f"Failed to get processing stats: {e}")
            return {"error": str(e)}


async def main():
    """Main function with command line options."""
    import argparse

    parser = argparse.ArgumentParser(description="Enhanced RSS Processing Pipeline")
    parser.add_argument(
        "--classify-existing", action="store_true", help="Classify existing unclassified articles"
    )
    parser.add_argument(
        "--limit", type=int, default=100, help="Limit for existing article classification"
    )
    parser.add_argument("--stats-only", action="store_true", help="Show processing statistics only")
    parser.add_argument(
        "--no-classify", action="store_true", help="Skip classification of new articles"
    )

    args = parser.parse_args()

    processor = EnhancedRSSProcessor()

    print("🔄 Enhanced RSS Processing Pipeline")
    print("=" * 50)

    if args.stats_only:
        print("📊 Getting processing statistics...")
        stats = await processor.get_processing_stats()

        if "error" in stats:
            print(f"❌ Error: {stats['error']}")
            return

        print(f"📰 Total articles: {stats['total_articles']}")
        print(
            f"🏷️  Classified articles: {stats['classified_articles']} ({stats['classification_rate']:.1%})"
        )
        print(
            f"📚 Educational articles: {stats['educational_articles']} ({stats['educational_ratio']:.1%})"
        )

        if "quality_overview" in stats and not stats["quality_overview"].get("error"):
            quality = stats["quality_overview"]
            print(f"⭐ Average learning value: {quality.get('average_learning_value', 0):.2f}")
            print(f"👥 User feedback items: {quality.get('total_feedback_items', 0)}")

        return

    if args.classify_existing:
        print(f"🏷️  Classifying up to {args.limit} existing articles...")
        result = await processor.classify_existing_articles(args.limit)

        if result["success"]:
            print(f"✅ Classified {result['classified']} articles")
        else:
            print(f"❌ Classification failed: {result['error']}")

        return

    # Process all feeds
    print("🔄 Processing all RSS feeds...")
    result = await processor.process_all_feeds(classify_new_articles=not args.no_classify)

    if result["success"]:
        print("✅ Success!")
        print(f"   📡 Processed {result['processed_feeds']}/{result['total_feeds']} feeds")
        print(f"   📰 Total articles: {result['total_articles']}")
        print(f"   🏷️  Classified articles: {result['classified_articles']}")
    else:
        print(f"❌ Failed: {result['error']}")


if __name__ == "__main__":
    asyncio.run(main())
