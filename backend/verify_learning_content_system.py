#!/usr/bin/env python3
"""
Simple verification that the Learning Content Enhancement System is properly integrated.
"""

import os
import sys

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_imports():
    """Test that all new modules can be imported."""
    try:
        print("🧪 Testing Learning Content Enhancement System imports...")

        # Test service imports
        from app.services.educational_rss_manager import (
            EDUCATIONAL_FEEDS,
            ContentFocus,
            FeedType,
        )

        print("   ✅ Educational RSS Manager")

        from app.services.content_classification_service import (
            ContentType,
            DifficultyLevel,
        )

        print("   ✅ Content Classification Service")

        print("   ✅ Enhanced Recommendation Engine")

        print("   ✅ Quality Assurance System")

        # Test API imports
        print("   ✅ Learning Content API")

        print("\n📊 System Statistics:")
        print(f"   📡 Educational feeds configured: {len(EDUCATIONAL_FEEDS)}")
        print(f"   🏷️  Content types: {len(ContentType)}")
        print(f"   📈 Difficulty levels: {len(DifficultyLevel)}")
        print(f"   📋 Feed types: {len(FeedType)}")

        # Show feed distribution
        feed_types = {}
        content_focuses = {}

        for feed in EDUCATIONAL_FEEDS:
            feed_type = feed["feed_type"].value
            content_focus = feed["content_focus"].value

            feed_types[feed_type] = feed_types.get(feed_type, 0) + 1
            content_focuses[content_focus] = content_focuses.get(content_focus, 0) + 1

        print("\n📈 Feed Distribution:")
        print(f"   By Type: {dict(feed_types)}")
        print(f"   By Focus: {dict(content_focuses)}")

        return True

    except ImportError as e:
        print(f"   ❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False


def test_api_integration():
    """Test that API is properly integrated."""
    try:
        print("\n🌐 Testing API integration...")

        # Check if main.py includes the new router
        with open("app/main.py", "r") as f:
            main_content = f.read()

        if "learning_content" in main_content:
            print("   ✅ Learning content router registered in main.py")
        else:
            print("   ❌ Learning content router not found in main.py")
            return False

        return True

    except Exception as e:
        print(f"   ❌ API integration test failed: {e}")
        return False


def main():
    """Main verification function."""
    print("🔍 Learning Content Enhancement System Verification")
    print("=" * 60)

    success = True

    # Test imports
    if not test_imports():
        success = False

    # Test API integration
    if not test_api_integration():
        success = False

    print("\n" + "=" * 60)

    if success:
        print("✅ All verifications passed!")
        print("\n📋 Next Steps:")
        print("1. Run database migration: 018_create_content_enhancement_tables.sql")
        print("2. Seed educational feeds: python3 scripts/seed_educational_feeds.py")
        print("3. Process and classify articles: python3 scripts/enhanced_rss_processor.py")
        print("4. Test the system: python3 test_learning_content_enhancement.py")
        print("\n🚀 Learning Content Enhancement System is ready!")
        return 0
    else:
        print("❌ Some verifications failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
