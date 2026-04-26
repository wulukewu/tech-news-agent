import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List

from ..services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)


class FeedType(Enum):
    EDUCATIONAL = "educational"
    NEWS = "news"
    OFFICIAL = "official"
    COMMUNITY = "community"


class ContentFocus(Enum):
    TUTORIAL = "tutorial"
    GUIDE = "guide"
    REFERENCE = "reference"
    NEWS = "news"
    PROJECT = "project"


@dataclass
class FeedMetadata:
    feed_id: str
    feed_type: FeedType
    content_focus: ContentFocus
    quality_score: float
    update_frequency: int
    target_audience: str
    primary_topics: List[str]


class EducationalRSSManager:
    """Manages educational RSS feeds with quality scoring and categorization."""

    def __init__(self, supabase_service: SupabaseService):
        self.supabase = supabase_service
        self.feed_cache: Dict[str, FeedMetadata] = {}

    async def add_educational_feed(
        self,
        url: str,
        name: str,
        feed_type: FeedType,
        content_focus: ContentFocus,
        target_audience: str = "developers",
        primary_topics: List[str] = None,
    ) -> str:
        """Add a new educational RSS feed with categorization."""
        try:
            # Add feed to feeds table
            feed_data = {
                "name": name,
                "url": url,
                "category": f"{feed_type.value}_{content_focus.value}",
                "is_active": True,
            }

            result = self.supabase.client.table("feeds").insert(feed_data).execute()
            feed_id = result.data[0]["id"]

            # Add categorization metadata
            category_data = {
                "feed_id": feed_id,
                "feed_type": feed_type.value,
                "content_focus": content_focus.value,
                "quality_score": 0.8,  # Default for educational feeds
                "update_frequency_hours": 24,
                "target_audience": target_audience,
                "primary_topics": primary_topics or [],
                "metadata": {},
            }

            self.supabase.client.table("feed_categories").insert(category_data).execute()

            logger.info(f"Added educational feed: {name} ({feed_type.value})")
            return feed_id

        except Exception as e:
            logger.error(f"Failed to add educational feed {name}: {e}")
            raise

    async def get_feeds_by_type(self, feed_type: FeedType) -> List[FeedMetadata]:
        """Get all feeds of a specific type."""
        try:
            result = (
                self.supabase.client.table("feed_categories")
                .select("*, feeds(name, url)")
                .eq("feed_type", feed_type.value)
                .execute()
            )

            feeds = []
            for row in result.data:
                feeds.append(
                    FeedMetadata(
                        feed_id=row["feed_id"],
                        feed_type=FeedType(row["feed_type"]),
                        content_focus=ContentFocus(row["content_focus"]),
                        quality_score=row["quality_score"],
                        update_frequency=row["update_frequency_hours"],
                        target_audience=row["target_audience"],
                        primary_topics=row["primary_topics"],
                    )
                )

            return feeds

        except Exception as e:
            logger.error(f"Failed to get feeds by type {feed_type}: {e}")
            return []

    async def calculate_feed_quality_score(self, feed_id: str) -> float:
        """Calculate quality score based on user feedback and engagement."""
        try:
            # Get average rating from content feedback
            result = (
                self.supabase.client.table("content_feedback")
                .select("educational_value_rating")
                .eq("article_id", "ANY(SELECT id FROM articles WHERE feed_id = %s)", feed_id)
                .execute()
            )

            if not result.data:
                return 0.8  # Default score for new feeds

            ratings = [
                r["educational_value_rating"] for r in result.data if r["educational_value_rating"]
            ]
            if not ratings:
                return 0.8

            # Convert 1-5 rating to 0-1 score
            avg_rating = sum(ratings) / len(ratings)
            quality_score = (avg_rating - 1) / 4  # Normalize to 0-1

            # Update cached score
            self.supabase.client.table("feed_categories").update(
                {"quality_score": quality_score}
            ).eq("feed_id", feed_id).execute()

            return quality_score

        except Exception as e:
            logger.error(f"Failed to calculate quality score for feed {feed_id}: {e}")
            return 0.5

    async def get_educational_feeds(self) -> List[Dict]:
        """Get all educational feeds with metadata."""
        try:
            result = (
                self.supabase.client.table("feed_categories")
                .select("*, feeds(id, name, url, category, is_active)")
                .in_("feed_type", ["educational", "official"])
                .execute()
            )

            return result.data

        except Exception as e:
            logger.error(f"Failed to get educational feeds: {e}")
            return []


# Educational RSS feeds to add
EDUCATIONAL_FEEDS = [
    {
        "name": "freeCodeCamp",
        "url": "https://www.freecodecamp.org/news/rss/",
        "feed_type": FeedType.EDUCATIONAL,
        "content_focus": ContentFocus.TUTORIAL,
        "target_audience": "beginners",
        "primary_topics": ["web-development", "programming", "tutorials"],
    },
    {
        "name": "CSS-Tricks",
        "url": "https://css-tricks.com/feed/",
        "feed_type": FeedType.EDUCATIONAL,
        "content_focus": ContentFocus.TUTORIAL,
        "target_audience": "frontend-developers",
        "primary_topics": ["css", "frontend", "web-design"],
    },
    {
        "name": "MDN Web Docs Blog",
        "url": "https://developer.mozilla.org/en-US/blog/rss.xml",
        "feed_type": FeedType.OFFICIAL,
        "content_focus": ContentFocus.REFERENCE,
        "target_audience": "web-developers",
        "primary_topics": ["web-standards", "javascript", "html", "css"],
    },
    {
        "name": "Smashing Magazine",
        "url": "https://www.smashingmagazine.com/feed/",
        "feed_type": FeedType.EDUCATIONAL,
        "content_focus": ContentFocus.GUIDE,
        "target_audience": "designers-developers",
        "primary_topics": ["web-design", "ux", "frontend"],
    },
    {
        "name": "A List Apart",
        "url": "https://alistapart.com/main/feed/",
        "feed_type": FeedType.EDUCATIONAL,
        "content_focus": ContentFocus.GUIDE,
        "target_audience": "web-professionals",
        "primary_topics": ["web-standards", "design", "content-strategy"],
    },
    {
        "name": "Dev.to",
        "url": "https://dev.to/feed",
        "feed_type": FeedType.COMMUNITY,
        "content_focus": ContentFocus.TUTORIAL,
        "target_audience": "developers",
        "primary_topics": ["programming", "tutorials", "career"],
    },
    {
        "name": "Real Python",
        "url": "https://realpython.com/atom.xml",
        "feed_type": FeedType.EDUCATIONAL,
        "content_focus": ContentFocus.TUTORIAL,
        "target_audience": "python-developers",
        "primary_topics": ["python", "programming", "tutorials"],
    },
    {
        "name": "JavaScript Weekly",
        "url": "https://javascriptweekly.com/rss",
        "feed_type": FeedType.EDUCATIONAL,
        "content_focus": ContentFocus.NEWS,
        "target_audience": "javascript-developers",
        "primary_topics": ["javascript", "frontend", "nodejs"],
    },
    {
        "name": "React Blog",
        "url": "https://react.dev/rss.xml",
        "feed_type": FeedType.OFFICIAL,
        "content_focus": ContentFocus.REFERENCE,
        "target_audience": "react-developers",
        "primary_topics": ["react", "frontend", "javascript"],
    },
    {
        "name": "Vue.js News",
        "url": "https://news.vuejs.org/feed.rss",
        "feed_type": FeedType.OFFICIAL,
        "content_focus": ContentFocus.NEWS,
        "target_audience": "vue-developers",
        "primary_topics": ["vue", "frontend", "javascript"],
    },
    {
        "name": "Node.js Blog",
        "url": "https://nodejs.org/en/feed/blog.xml",
        "feed_type": FeedType.OFFICIAL,
        "content_focus": ContentFocus.REFERENCE,
        "target_audience": "nodejs-developers",
        "primary_topics": ["nodejs", "backend", "javascript"],
    },
    {
        "name": "GitHub Blog",
        "url": "https://github.blog/feed/",
        "feed_type": FeedType.OFFICIAL,
        "content_focus": ContentFocus.NEWS,
        "target_audience": "developers",
        "primary_topics": ["git", "development", "open-source"],
    },
    {
        "name": "Stack Overflow Blog",
        "url": "https://stackoverflow.blog/feed/",
        "feed_type": FeedType.COMMUNITY,
        "content_focus": ContentFocus.GUIDE,
        "target_audience": "developers",
        "primary_topics": ["programming", "career", "best-practices"],
    },
    {
        "name": "Google Developers Blog",
        "url": "https://developers.googleblog.com/feeds/posts/default",
        "feed_type": FeedType.OFFICIAL,
        "content_focus": ContentFocus.REFERENCE,
        "target_audience": "developers",
        "primary_topics": ["web-development", "mobile", "cloud"],
    },
    {
        "name": "Netlify Blog",
        "url": "https://www.netlify.com/blog/index.xml",
        "feed_type": FeedType.EDUCATIONAL,
        "content_focus": ContentFocus.TUTORIAL,
        "target_audience": "web-developers",
        "primary_topics": ["jamstack", "deployment", "web-development"],
    },
]
