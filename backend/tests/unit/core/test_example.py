"""
Example unit test demonstrating the new test organization structure.

This test can be removed after migration is complete.
"""

import pytest


@pytest.mark.unit
def test_example_unit_test(mock_supabase_client):
    """Example unit test using shared fixture."""
    # Arrange
    assert mock_supabase_client is not None

    # Act
    result = mock_supabase_client.table("test")

    # Assert
    assert result is not None


@pytest.mark.unit
def test_example_without_fixtures():
    """Example unit test without fixtures."""
    # Arrange
    test_value = "hello"

    # Act
    result = test_value.upper()

    # Assert
    assert result == "HELLO"
