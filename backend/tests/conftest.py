"""
Test configuration and fixtures for backend tests.

This module provides:
- Global pytest configuration
- Hypothesis settings for property-based testing
- Database fixtures (test_supabase_client, test_user, test_feed, etc.)
- Shared fixtures from fixtures/ directory

The hierarchical test organization separates tests by type:
- unit/: Fast, isolated tests with mocked dependencies
- integration/: Tests with real database/service interactions
- e2e/: Complete workflow tests
- property/: Property-based tests with Hypothesis

Shared fixtures are organized in fixtures/ directory:
- fixtures/database.py: Database and test data fixtures
- fixtures/auth.py: Authentication fixtures
- fixtures/api.py: API testing fixtures
- fixtures/bot.py: Discord bot fixtures
"""

# CRITICAL: Set environment variables BEFORE any imports
# This ensures settings can be loaded when app modules are imported
import os

# Only set defaults if not already set (allows tests to override)
if "APP_ENV" not in os.environ:
    os.environ["APP_ENV"] = "test"
os.environ.setdefault("SUPABASE_URL", "https://dummy.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "dummy-key")
os.environ.setdefault("GROQ_API_KEY", "dummy-key")
os.environ.setdefault("JWT_SECRET", "dummy-secret-for-testing-at-least-32-chars-long")
os.environ.setdefault("DISCORD_CLIENT_ID", "dummy-client-id")
os.environ.setdefault("DISCORD_CLIENT_SECRET", "dummy-client-secret")
os.environ.setdefault("DISCORD_REDIRECT_URI", "http://localhost:3000/auth/callback")
os.environ.setdefault(
    "DISCORD_TOKEN", "dummy-discord-token-at-least-50-characters-long-for-validation"
)

import sys

import pytest
from dotenv import load_dotenv
from hypothesis import Verbosity, settings
from supabase import Client, create_client

# Load environment variables from .env if it exists (after setting defaults)
load_dotenv()


def pytest_configure(config):
    """Configure pytest before test collection."""
    pass


# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Import shared fixtures to make them available to all tests
pytest_plugins = [
    "tests.fixtures.database",
    "tests.fixtures.auth",
    "tests.fixtures.api",
    "tests.fixtures.bot",
]


# Configure Hypothesis settings
# 配置 Hypothesis 設定（減少迭代次數以加快測試速度）
settings.register_profile("default", max_examples=10, verbosity=Verbosity.normal)
settings.register_profile("ci", max_examples=10, verbosity=Verbosity.verbose)
settings.register_profile("dev", max_examples=10, verbosity=Verbosity.normal)
settings.register_profile("debug", max_examples=5, verbosity=Verbosity.verbose)

# Load profile from environment or use default
settings.load_profile(os.getenv("HYPOTHESIS_PROFILE", "default"))


@pytest.fixture(scope="session")
def supabase_url() -> str:
    """Get Supabase URL from environment."""
    url = os.getenv("SUPABASE_URL")
    if not url:
        pytest.skip("SUPABASE_URL not set - skipping integration tests")
    # Skip if using dummy URL (CI environment without real database)
    if "dummy" in url.lower():
        pytest.skip("Using dummy SUPABASE_URL - skipping integration tests")
    return url


@pytest.fixture(scope="session")
def supabase_key() -> str:
    """Get Supabase key from environment."""
    key = os.getenv("SUPABASE_KEY")
    if not key:
        pytest.skip("SUPABASE_KEY not set - skipping integration tests")
    # Skip if using dummy key (CI environment without real database)
    if "dummy" in key.lower():
        pytest.skip("Using dummy SUPABASE_KEY - skipping integration tests")
    return key


@pytest.fixture(scope="function")
def test_supabase_client(supabase_url: str, supabase_key: str) -> Client:
    """
    Create a Supabase client for testing.

    This fixture provides a fresh Supabase client for each test function.
    It connects to the test database using credentials from environment variables.

    Usage:
        def test_something(test_supabase_client):
            result = test_supabase_client.table('users').select('*').execute()
    """
    client = create_client(supabase_url, supabase_key)
    return client


@pytest.fixture(scope="function")
def test_user(test_supabase_client: Client):
    """
    Create a test user and clean up after the test.

    This fixture provides a reusable test user with a unique discord_id.
    The user is automatically deleted after the test completes.

    Returns:
        dict: User record with keys: id, discord_id, created_at

    Usage:
        def test_something(test_user):
            user_id = test_user['id']
            discord_id = test_user['discord_id']
    """
    # Generate unique discord_id
    test_discord_id = f"test_user_{os.urandom(8).hex()}"

    # Create user
    result = test_supabase_client.table("users").insert({"discord_id": test_discord_id}).execute()

    user = result.data[0]

    yield user

    # Cleanup: Delete user (cascades to subscriptions and reading_list)
    try:
        test_supabase_client.table("users").delete().eq("id", user["id"]).execute()
    except Exception:
        # Ignore cleanup errors (user might already be deleted by test)
        pass


@pytest.fixture(scope="function")
def test_feed(test_supabase_client: Client):
    """
    Create a test feed and clean up after the test.

    This fixture provides a reusable test feed with a unique URL.
    The feed is automatically deleted after the test completes.

    IMPORTANT: Test feeds are created as INACTIVE to prevent the scheduler
    from attempting to fetch them.

    Returns:
        dict: Feed record with keys: id, name, url, category, is_active, created_at

    Usage:
        def test_something(test_feed):
            feed_id = test_feed['id']
            feed_url = test_feed['url']
    """
    # Generate unique feed URL
    test_feed_url = f"https://test-feed-{os.urandom(8).hex()}.com/rss.xml"

    # Create feed as INACTIVE to prevent scheduler from fetching it
    result = (
        test_supabase_client.table("feeds")
        .insert(
            {
                "name": "Test Feed",
                "url": test_feed_url,
                "category": "Test Category",
                "is_active": False,  # Changed from True to False
            }
        )
        .execute()
    )

    feed = result.data[0]

    yield feed

    # Cleanup: Delete feed (cascades to articles)
    try:
        test_supabase_client.table("feeds").delete().eq("id", feed["id"]).execute()
    except Exception:
        # Ignore cleanup errors (feed might already be deleted by test)
        pass


@pytest.fixture(scope="function")
def test_article(test_supabase_client: Client, test_feed):
    """
    Create a test article and clean up after the test.

    This fixture provides a reusable test article linked to a test feed.
    The article is automatically deleted after the test completes.
    Depends on test_feed fixture.

    Returns:
        dict: Article record with keys: id, feed_id, title, url, published_at,
              tinkering_index, ai_summary, embedding, created_at

    Usage:
        def test_something(test_article):
            article_id = test_article['id']
            article_url = test_article['url']
    """
    # Generate unique article URL
    test_article_url = f"https://test-article-{os.urandom(8).hex()}.com"

    # Create article
    result = (
        test_supabase_client.table("articles")
        .insert({"feed_id": test_feed["id"], "title": "Test Article", "url": test_article_url})
        .execute()
    )

    article = result.data[0]

    yield article

    # Cleanup: Delete article (cascades to reading_list)
    try:
        test_supabase_client.table("articles").delete().eq("id", article["id"]).execute()
    except Exception:
        # Ignore cleanup errors (article might already be deleted by test)
        pass


@pytest.fixture(scope="function")
def test_subscription(test_supabase_client: Client, test_user, test_feed):
    """
    Create a test subscription and clean up after the test.

    This fixture provides a reusable test subscription linking a user to a feed.
    The subscription is automatically deleted after the test completes.
    Depends on test_user and test_feed fixtures.

    Returns:
        dict: Subscription record with keys: id, user_id, feed_id, subscribed_at

    Usage:
        def test_something(test_subscription):
            subscription_id = test_subscription['id']
    """
    # Create subscription
    result = (
        test_supabase_client.table("user_subscriptions")
        .insert({"user_id": test_user["id"], "feed_id": test_feed["id"]})
        .execute()
    )

    subscription = result.data[0]

    yield subscription

    # Cleanup: Delete subscription
    try:
        test_supabase_client.table("user_subscriptions").delete().eq(
            "id", subscription["id"]
        ).execute()
    except Exception:
        # Ignore cleanup errors (subscription might already be deleted by test)
        pass


@pytest.fixture(scope="function")
def test_reading_list_entry(test_supabase_client: Client, test_user, test_article):
    """
    Create a test reading list entry and clean up after the test.

    This fixture provides a reusable test reading list entry linking a user to an article.
    The entry is automatically deleted after the test completes.
    Depends on test_user and test_article fixtures.

    Returns:
        dict: Reading list entry with keys: id, user_id, article_id, status,
              rating, added_at, updated_at

    Usage:
        def test_something(test_reading_list_entry):
            entry_id = test_reading_list_entry['id']
            status = test_reading_list_entry['status']
    """
    # Create reading list entry
    result = (
        test_supabase_client.table("reading_list")
        .insert({"user_id": test_user["id"], "article_id": test_article["id"], "status": "Unread"})
        .execute()
    )

    entry = result.data[0]

    yield entry

    # Cleanup: Delete reading list entry
    try:
        test_supabase_client.table("reading_list").delete().eq("id", entry["id"]).execute()
    except Exception:
        # Ignore cleanup errors (entry might already be deleted by test)
        pass


@pytest.fixture(scope="function")
def cleanup_test_data(test_supabase_client: Client):
    """
    Comprehensive test database cleanup mechanism.
    Task 7.2: 建立測試資料庫清理機制

    This fixture provides a cleanup mechanism that ensures test independence by:
    - Tracking all created test data IDs during test execution
    - Cleaning up all test data after each test completes
    - Handling cascading deletes in the correct order

    The fixture yields a dictionary with tracking lists for each table.
    Tests can append IDs to these lists, and cleanup will be automatic.

    Usage:
        def test_something(test_supabase_client, cleanup_test_data):
            # Create test data
            user = test_supabase_client.table('users').insert({
                'discord_id': 'test_123'
            }).execute().data[0]

            # Track for cleanup
            cleanup_test_data['users'].append(user['id'])

            # Test logic here...
            # Cleanup happens automatically after test

    Returns:
        dict: Dictionary with lists for tracking IDs:
            - 'users': List of user IDs to clean up
            - 'feeds': List of feed IDs to clean up
            - 'articles': List of article IDs to clean up
            - 'subscriptions': List of subscription IDs to clean up
            - 'reading_list': List of reading list entry IDs to clean up
    """
    # Initialize tracking dictionary
    cleanup_tracker = {
        "users": [],
        "feeds": [],
        "articles": [],
        "subscriptions": [],
        "reading_list": [],
    }

    yield cleanup_tracker

    # Cleanup in reverse dependency order to respect foreign key constraints
    # Note: Due to CASCADE DELETE, cleaning up parent records will automatically
    # clean up child records, but we clean up explicitly for clarity

    # 1. Clean up reading_list entries (no dependencies)
    for entry_id in cleanup_tracker["reading_list"]:
        try:
            test_supabase_client.table("reading_list").delete().eq("id", entry_id).execute()
        except Exception:
            # Ignore errors (might be already deleted by cascade)
            pass

    # 2. Clean up subscriptions (no dependencies)
    for subscription_id in cleanup_tracker["subscriptions"]:
        try:
            test_supabase_client.table("user_subscriptions").delete().eq(
                "id", subscription_id
            ).execute()
        except Exception:
            # Ignore errors (might be already deleted by cascade)
            pass

    # 3. Clean up articles (will cascade to reading_list)
    for article_id in cleanup_tracker["articles"]:
        try:
            test_supabase_client.table("articles").delete().eq("id", article_id).execute()
        except Exception:
            # Ignore errors (might be already deleted by cascade)
            pass

    # 4. Clean up feeds (will cascade to articles and subscriptions)
    for feed_id in cleanup_tracker["feeds"]:
        try:
            test_supabase_client.table("feeds").delete().eq("id", feed_id).execute()
        except Exception:
            # Ignore errors (might be already deleted by cascade)
            pass

    # 5. Clean up users (will cascade to subscriptions and reading_list)
    for user_id in cleanup_tracker["users"]:
        try:
            test_supabase_client.table("users").delete().eq("id", user_id).execute()
        except Exception:
            # Ignore errors (might be already deleted by cascade)
            pass
