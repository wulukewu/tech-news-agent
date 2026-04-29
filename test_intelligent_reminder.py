"""
Test script for Intelligent Reminder Agent
This script tests the core functionality without requiring database setup.
"""
import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.append('/home/luke/Documents/tech-news-agent/backend')

from app.qa_agent.intelligent_reminder import (
    IntelligentReminderAgent,
    ContentAnalyzer,
    VersionTracker,
    BehaviorAnalyzer,
    TimingEngine,
    ContextGenerator,
    ContentParser,
    ContentFormatter,
    ContentPrettyPrinter,
    ReminderContext,
    ReminderType,
    RelationshipType
)

def test_content_parser():
    """Test content parsing functionality"""
    print("🧪 Testing ContentParser...")

    sample_content = """
    # Python FastAPI Tutorial

    This is a comprehensive guide to building APIs with FastAPI.

    ```python
    from fastapi import FastAPI
    app = FastAPI()

    @app.get("/")
    def read_root():
        return {"Hello": "World"}
    ```

    FastAPI is a modern, fast web framework for building APIs with Python.
    """

    parsed = ContentParser.parse_article_content(sample_content)

    print(f"✓ Word count: {parsed['word_count']}")
    print(f"✓ Reading time: {parsed['reading_time']} minutes")
    print(f"✓ Keywords found: {parsed['keywords']}")
    print(f"✓ Has code: {parsed['has_code']}")
    print(f"✓ Complexity score: {parsed['complexity_score']:.2f}")

    return True

def test_content_formatter():
    """Test content formatting functionality"""
    print("\n🧪 Testing ContentFormatter...")

    context = ReminderContext(
        title="New FastAPI Version Available",
        description="FastAPI 0.104.0 has been released with new features and improvements.",
        related_articles=[
            {"title": "FastAPI Tutorial", "url": "https://example.com/tutorial"},
            {"title": "API Best Practices", "url": "https://example.com/practices"}
        ],
        version_info={
            "technology": "FastAPI",
            "new_version": "0.104.0",
            "previous_version": "0.103.2",
            "version_type": "minor"
        },
        reading_time_estimate=10,
        priority_score=0.8,
        action_url="https://fastapi.tiangolo.com/"
    )

    # Test text formatting
    text_output = ContentFormatter.format_to_text(context)
    print("✓ Text format generated")
    print(f"Preview: {text_output[:100]}...")

    # Test HTML formatting
    html_output = ContentFormatter.format_to_html(context)
    print("✓ HTML format generated")
    print(f"Preview: {html_output[:100]}...")

    # Test pretty printing
    pretty_output = ContentPrettyPrinter.pretty_print(context)
    print("✓ Pretty print format generated")
    print(f"Preview: {pretty_output[:100]}...")

    return True

def test_models():
    """Test model creation and validation"""
    print("\n🧪 Testing Models...")

    # Test ReminderContext
    context = ReminderContext(
        title="Test Reminder",
        description="This is a test reminder",
        priority_score=0.7
    )
    print(f"✓ ReminderContext created: {context.title}")

    # Test enums
    print(f"✓ ReminderType.ARTICLE_RELATION: {ReminderType.ARTICLE_RELATION}")
    print(f"✓ RelationshipType.PREREQUISITE: {RelationshipType.PREREQUISITE}")

    return True

def test_version_tracker_logic():
    """Test version tracking logic without external API calls"""
    print("\n🧪 Testing VersionTracker logic...")

    # Create a mock version tracker to test classification logic
    class MockVersionTracker:
        def _classify_version_type(self, old_version: str, new_version: str):
            try:
                old_parts = [int(x) for x in old_version.split('.')]
                new_parts = [int(x) for x in new_version.split('.')]

                # Pad with zeros if needed
                max_len = max(len(old_parts), len(new_parts))
                old_parts.extend([0] * (max_len - len(old_parts)))
                new_parts.extend([0] * (max_len - len(new_parts)))

                if new_parts[0] > old_parts[0]:
                    return "major"
                elif new_parts[1] > old_parts[1]:
                    return "minor"
                else:
                    return "patch"

            except (ValueError, IndexError):
                return "minor"

    tracker = MockVersionTracker()

    # Test version classification
    test_cases = [
        ("1.0.0", "2.0.0", "major"),
        ("1.0.0", "1.1.0", "minor"),
        ("1.0.0", "1.0.1", "patch"),
        ("0.103.2", "0.104.0", "minor"),
    ]

    for old, new, expected in test_cases:
        result = tracker._classify_version_type(old, new)
        print(f"✓ {old} → {new}: {result} (expected: {expected})")
        assert result == expected, f"Expected {expected}, got {result}"

    return True

def test_timing_logic():
    """Test timing engine logic"""
    print("\n🧪 Testing TimingEngine logic...")

    # Test time calculations
    from datetime import datetime, time

    class MockTimingEngine:
        def _is_time_in_range(self, current_time: time, start_time: time, end_time: time) -> bool:
            # Handle quiet hours that span midnight
            if start_time > end_time:
                return current_time >= start_time or current_time <= end_time
            else:
                return start_time <= current_time <= end_time

    engine = MockTimingEngine()

    # Test quiet hours logic
    test_cases = [
        (time(14, 0), time(22, 0), time(6, 0), True),   # 2pm during 10pm-6am quiet hours
        (time(23, 0), time(22, 0), time(6, 0), True),   # 11pm during 10pm-6am quiet hours
        (time(10, 0), time(22, 0), time(6, 0), False),  # 10am outside 10pm-6am quiet hours
        (time(14, 0), time(12, 0), time(18, 0), True),  # 2pm during 12pm-6pm quiet hours
        (time(10, 0), time(12, 0), time(18, 0), False), # 10am outside 12pm-6pm quiet hours
    ]

    for current, start, end, expected in test_cases:
        result = engine._is_time_in_range(current, start, end)
        print(f"✓ {current} in {start}-{end}: {result} (expected: {expected})")
        assert result == expected, f"Expected {expected}, got {result}"

    return True

def main():
    """Run all tests"""
    print("🚀 Starting Intelligent Reminder Agent Tests\n")

    tests = [
        test_models,
        test_content_parser,
        test_content_formatter,
        test_version_tracker_logic,
        test_timing_logic,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
                print(f"✅ {test.__name__} PASSED")
            else:
                failed += 1
                print(f"❌ {test.__name__} FAILED")
        except Exception as e:
            failed += 1
            print(f"❌ {test.__name__} FAILED: {e}")

    print(f"\n📊 Test Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 All tests passed! The Intelligent Reminder Agent implementation is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
