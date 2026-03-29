"""
Property-based tests and unit tests for build_week_string.
Tests Published_Week format requirements.
"""
import re
import pytest
from datetime import datetime, timezone, timedelta
from hypothesis import given, settings as h_settings
from hypothesis import strategies as st

from app.services.notion_service import build_week_string


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------

# Generate valid datetime objects
# ISO week dates can be complex, so we'll generate dates from 1900 to 2100
# Note: datetimes() requires naive datetime bounds, we'll add timezone later
datetime_strategy = st.datetimes(
    min_value=datetime(1900, 1, 1),
    max_value=datetime(2100, 12, 31),
).map(lambda dt: dt.replace(tzinfo=timezone.utc))


# ---------------------------------------------------------------------------
# Property 13: Published_Week 格式符合 ^\d{4}-\d{2}$ 且週次 1-53
# ---------------------------------------------------------------------------

# Feature: notion-article-pages-refactor, Property 13: Published_Week 格式符合 ^\d{4}-\d{2}$ 且週次 1-53
@given(dt=datetime_strategy)
@h_settings(max_examples=100)
def test_build_week_string_format_and_range(dt):
    r"""Validates: Requirements 2.2

    For any datetime object, build_week_string returns a string that:
    1. Matches the format ^\d{4}-\d{2}$ (YYYY-WW)
    2. Week number is between 1 and 53 (inclusive)
    """
    week_string = build_week_string(dt)
    
    # Check format matches ^\d{4}-\d{2}$
    pattern = r'^\d{4}-\d{2}$'
    assert re.match(pattern, week_string), (
        f"Week string '{week_string}' does not match format YYYY-WW (pattern: {pattern})"
    )
    
    # Extract year and week number
    parts = week_string.split('-')
    assert len(parts) == 2, f"Week string '{week_string}' should have exactly 2 parts separated by '-'"
    
    year_str, week_str = parts
    assert len(year_str) == 4, f"Year part '{year_str}' should be 4 digits"
    assert len(week_str) == 2, f"Week part '{week_str}' should be 2 digits"
    
    year = int(year_str)
    week = int(week_str)
    
    # Check week number is in valid range (1-53)
    assert 1 <= week <= 53, (
        f"Week number {week} is out of valid range [1, 53] for date {dt.isoformat()}"
    )
    
    # Verify consistency with isocalendar()
    iso_year, iso_week, _ = dt.isocalendar()
    expected = f"{iso_year:04d}-{iso_week:02d}"
    assert week_string == expected, (
        f"Week string '{week_string}' does not match expected '{expected}' "
        f"from isocalendar() for date {dt.isoformat()}"
    )


# ---------------------------------------------------------------------------
# Unit tests for build_week_string
# ---------------------------------------------------------------------------

def test_build_week_string_first_week_of_year():
    """Test first week of 2024."""
    dt = datetime(2024, 1, 1, tzinfo=timezone.utc)
    week_string = build_week_string(dt)
    assert week_string == "2024-01"


def test_build_week_string_last_week_of_year():
    """Test last week of 2024 (week 52)."""
    dt = datetime(2024, 12, 30, tzinfo=timezone.utc)
    week_string = build_week_string(dt)
    # December 30, 2024 is in week 1 of 2025 according to ISO 8601
    # Let's verify with isocalendar
    iso_year, iso_week, _ = dt.isocalendar()
    expected = f"{iso_year:04d}-{iso_week:02d}"
    assert week_string == expected


def test_build_week_string_mid_year():
    """Test mid-year date."""
    dt = datetime(2024, 6, 15, tzinfo=timezone.utc)
    week_string = build_week_string(dt)
    iso_year, iso_week, _ = dt.isocalendar()
    expected = f"{iso_year:04d}-{iso_week:02d}"
    assert week_string == expected


def test_build_week_string_week_53():
    """Test a year with 53 weeks (e.g., 2020)."""
    # December 31, 2020 is in week 53 of 2020
    dt = datetime(2020, 12, 31, tzinfo=timezone.utc)
    week_string = build_week_string(dt)
    assert week_string == "2020-53"


def test_build_week_string_format():
    """Test that format is always YYYY-WW with zero-padding."""
    dt = datetime(2024, 1, 5, tzinfo=timezone.utc)
    week_string = build_week_string(dt)
    
    # Check format
    assert re.match(r'^\d{4}-\d{2}$', week_string)
    
    # Check zero-padding
    parts = week_string.split('-')
    assert len(parts[0]) == 4  # Year is 4 digits
    assert len(parts[1]) == 2  # Week is 2 digits (zero-padded)


def test_build_week_string_with_timezone():
    """Test with different timezone (UTC+8)."""
    utc_plus_8 = timezone(timedelta(hours=8))
    dt = datetime(2024, 3, 15, 10, 30, tzinfo=utc_plus_8)
    week_string = build_week_string(dt)
    
    iso_year, iso_week, _ = dt.isocalendar()
    expected = f"{iso_year:04d}-{iso_week:02d}"
    assert week_string == expected
