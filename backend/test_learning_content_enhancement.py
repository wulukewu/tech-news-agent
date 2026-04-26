#!/usr/bin/env python3
"""
Learning Content Enhancement System Test
Comprehensive test of all components in the learning content enhancement system.
"""

import asyncio
import os
import sys

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.logger import get_logger
from app.schemas.article import ArticleSchema
from app.services.content_classification_service import ContentClassificationService, ContentType
from app.services.educational_rss_manager import EducationalRSSManager
from app.services.enhanced_recommendation_engine import EnhancedRecommendationEngine
from app.services.llm_service import LLMService
from app.services.quality_assurance_system import ContentFeedback, QualityAssuranceSystem
from app.services.supabase_service import SupabaseService

logger = get_logger(__name__)


class LearningContentEnhancementTest:
    """Comprehensive test suite for learning content enhancement system."""

    def __init__(self):
        self.supabase = SupabaseService()
        self.llm = LLMService()
        self.rss_manager = EducationalRSSManager(self.supabase)
        self.classifier = ContentClassificationService(self.llm, self.supabase)
        self.recommender = EnhancedRecommendationEngine(self.supabase, self.classifier)
        self.quality_system = QualityAssuranceSystem(self.supabase)

        self.test_results = {
            "database_setup": False,
            "educational_feeds": False,
            "content_classification": False,
            "enhanced_recommendations": False,
            "quality_assurance": False,
            "api_endpoints": False,
        }

    async def test_database_setup(self) -> bool:
        """Test database tables and schema."""
        try:
            print("🗄️  Testing database setup...")

            # Test each new table
            tables_to_test = [
                "feed_categories",
                "article_classifications",
                "content_feedback",
                "user_learning_preferences",
                "content_quality_metrics",
            ]

            for table in tables_to_test:
                try:
                    result = self.supabase.client.table(table).select("*").limit(1).execute()
                    print(f"   ✅ Table {table}: OK")
                except Exception as e:
                    print(f"   ❌ Table {table}: {e}")
                    return False

            print("   ✅ All database tables accessible")
            return True

        except Exception as e:
            print(f"   ❌ Database setup test failed: {e}")
            return False

    async def test_educational_feeds(self) -> bool:
        """Test educational RSS feed management."""
        try:
            print("📡 Testing educational RSS feeds...")

            # Test getting educational feeds
            feeds = await self.rss_manager.get_educational_feeds()
            print(f"   📊 Found {len(feeds)} educational feeds")

            if len(feeds) == 0:
                print("   ⚠️  No educational feeds found - run seed script first")
                return False

            # Test feed categorization
            educational_count = len([f for f in feeds if f.get("feed_type") == "educational"])
            official_count = len([f for f in feeds if f.get("feed_type") == "official"])
            community_count = len([f for f in feeds if f.get("feed_type") == "community"])

            print(f"   📚 Educational: {educational_count}")
            print(f"   🏛️  Official: {official_count}")
            print(f"   👥 Community: {community_count}")

            # Test quality scoring
            if feeds:
                sample_feed_id = feeds[0].get("feed_id")
                if sample_feed_id:
                    quality_score = await self.rss_manager.calculate_feed_quality_score(
                        sample_feed_id
                    )
                    print(f"   ⭐ Sample quality score: {quality_score:.2f}")

            print("   ✅ Educational RSS feeds working")
            return True

        except Exception as e:
            print(f"   ❌ Educational feeds test failed: {e}")
            return False

    async def test_content_classification(self) -> bool:
        """Test content classification service."""
        try:
            print("🏷️  Testing content classification...")

            # Get a sample article for testing
            articles_result = self.supabase.client.table("articles").select("*").limit(1).execute()

            if not articles_result.data:
                print("   ⚠️  No articles found for testing")
                return False

            article_data = articles_result.data[0]
            article = ArticleSchema(**article_data)

            print(f"   📰 Testing with article: {article.title[:50]}...")

            # Test classification
            classification = await self.classifier.classify_article(article)

            print(f"   🏷️  Content type: {classification.content_type.value}")
            print(f"   📊 Difficulty level: {classification.difficulty_level.value}")
            print(f"   📈 Learning value: {classification.learning_value_score:.2f}")
            print(f"   🎯 Confidence: {classification.confidence_score:.2f}")

            # Test educational features
            features = classification.educational_features
            print(f"   💻 Has code examples: {features.has_code_examples}")
            print(f"   📝 Has step-by-step: {features.has_step_by_step}")
            print(f"   ⏱️  Reading time: {features.estimated_reading_time} min")

            # Test getting educational articles
            educational_articles = await self.classifier.get_educational_articles(
                content_types=[ContentType.TUTORIAL, ContentType.GUIDE], limit=5
            )
            print(f"   📚 Found {len(educational_articles)} educational articles")

            print("   ✅ Content classification working")
            return True

        except Exception as e:
            print(f"   ❌ Content classification test failed: {e}")
            return False

    async def test_enhanced_recommendations(self) -> bool:
        """Test enhanced recommendation engine."""
        try:
            print("🎯 Testing enhanced recommendations...")

            # Get a test user
            users_result = self.supabase.client.table("users").select("*").limit(1).execute()

            if not users_result.data:
                print("   ⚠️  No users found for testing")
                return False

            user_id = str(users_result.data[0]["id"])
            print(f"   👤 Testing with user: {user_id}")

            # Test getting recommendations
            recommendations = await self.recommender.get_learning_recommendations(
                user_id=user_id, limit=5
            )

            print(f"   📋 Generated {len(recommendations)} recommendations")

            if recommendations:
                for i, rec in enumerate(recommendations[:3], 1):
                    article = rec["article"]
                    score = rec["score"]
                    print(f"   {i}. {article['title'][:40]}... (score: {score:.2f})")

            # Test user preferences
            preferences = await self.recommender._get_user_preferences(user_id)
            print(
                f"   ⚙️  User preferences: {[ct.value for ct in preferences.preferred_content_types]}"
            )

            print("   ✅ Enhanced recommendations working")
            return True

        except Exception as e:
            print(f"   ❌ Enhanced recommendations test failed: {e}")
            return False

    async def test_quality_assurance(self) -> bool:
        """Test quality assurance system."""
        try:
            print("🔍 Testing quality assurance...")

            # Get test data
            users_result = self.supabase.client.table("users").select("*").limit(1).execute()
            articles_result = self.supabase.client.table("articles").select("*").limit(1).execute()

            if not users_result.data or not articles_result.data:
                print("   ⚠️  No test data available")
                return False

            user_id = str(users_result.data[0]["id"])
            article_id = str(articles_result.data[0]["id"])

            # Test feedback collection
            test_feedback = ContentFeedback(
                user_id=user_id,
                article_id=article_id,
                educational_value_rating=4,
                difficulty_accuracy=True,
                content_type_accuracy=True,
                completion_status="completed",
                time_spent_minutes=15,
                feedback_text="Great tutorial with clear examples",
            )

            success = await self.quality_system.collect_user_feedback(test_feedback)
            print(f"   📝 Feedback collection: {'✅' if success else '❌'}")

            # Test quality score calculation
            quality_score = await self.quality_system.calculate_content_quality_score(article_id)
            print(f"   ⭐ Quality score: {quality_score:.2f}")

            # Test quality overview
            overview = await self.quality_system.get_quality_overview()
            if "error" not in overview:
                print(f"   📊 Total articles: {overview.get('total_articles', 0)}")
                print(f"   📚 Educational ratio: {overview.get('educational_content_ratio', 0):.1%}")
                print(f"   📈 Avg learning value: {overview.get('average_learning_value', 0):.2f}")

            print("   ✅ Quality assurance working")
            return True

        except Exception as e:
            print(f"   ❌ Quality assurance test failed: {e}")
            return False

    async def test_api_endpoints(self) -> bool:
        """Test API endpoints (basic connectivity)."""
        try:
            print("🌐 Testing API endpoints...")

            # This is a basic test - in a real scenario you'd use a test client
            # For now, we'll just verify the services can be instantiated

            from app.api.learning_content import (
                get_content_classifier,
                get_educational_rss_manager,
                get_enhanced_recommender,
                get_quality_system,
            )

            # Test service instantiation
            rss_manager = get_educational_rss_manager()
            classifier = get_content_classifier()
            recommender = get_enhanced_recommender()
            quality_system = get_quality_system()

            print("   ✅ All API services instantiated successfully")
            print("   ℹ️  Full API testing requires running server")

            return True

        except Exception as e:
            print(f"   ❌ API endpoints test failed: {e}")
            return False

    async def run_all_tests(self) -> dict:
        """Run all tests and return results."""
        print("🧪 Learning Content Enhancement System Test")
        print("=" * 60)

        # Run tests in order
        tests = [
            ("database_setup", self.test_database_setup),
            ("educational_feeds", self.test_educational_feeds),
            ("content_classification", self.test_content_classification),
            ("enhanced_recommendations", self.test_enhanced_recommendations),
            ("quality_assurance", self.test_quality_assurance),
            ("api_endpoints", self.test_api_endpoints),
        ]

        for test_name, test_func in tests:
            try:
                result = await test_func()
                self.test_results[test_name] = result
                print()
            except Exception as e:
                print(f"   ❌ Test {test_name} crashed: {e}")
                self.test_results[test_name] = False
                print()

        # Summary
        print("📋 Test Summary")
        print("-" * 30)

        passed = 0
        total = len(self.test_results)

        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name.replace('_', ' ').title()}: {status}")
            if result:
                passed += 1

        print(f"\nOverall: {passed}/{total} tests passed ({passed/total:.1%})")

        return {
            "passed": passed,
            "total": total,
            "success_rate": passed / total,
            "results": self.test_results,
        }


async def main():
    """Main test function."""
    tester = LearningContentEnhancementTest()
    results = await tester.run_all_tests()

    if results["success_rate"] == 1.0:
        print("\n🎉 All tests passed! Learning Content Enhancement System is ready.")
        sys.exit(0)
    else:
        print(
            f"\n⚠️  {results['total'] - results['passed']} tests failed. Please check the issues above."
        )
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
