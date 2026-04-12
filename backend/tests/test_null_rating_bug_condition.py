"""
Bug Condition Exploration Test: Null Rating Rejection (Bug 3)
==============================================================

This test is designed to run on UNFIXED code to confirm that Bug 3 exists.

Bug Condition 3: Backend Rejects Null Rating Values
- Rating value is null
- Request endpoint is /api/reading-list/{article_id}/rating
- Request method is PATCH
- UpdateRatingRequest schema rejects null

Expected Behavior (what the test encodes):
- For any rating update request where rating is null, the system SHALL accept
  the null value and update the database to set rating to NULL

CRITICAL: This test MUST FAIL on unfixed code - failure confirms the bug exists.
DO NOT attempt to fix the test or the code when it fails.

Expected outcome on UNFIXED code: FAIL (this is correct - it proves the bug exists)
Expected outcome on FIXED code: PASS (confirms the fix works)

The test will document counterexamples found:
- Backend returns 422 validation error: "Rating must be between 1 and 5"
- Pydantic validation rejects null before reaching business logic
- UpdateRatingRequest schema: rating: int = Field(..., ge=1, le=5) doesn't allow None

Validates: Requirements 1.5, 1.6, 2.5, 2.6
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from hypothesis import Phase, given, settings
from hypothesis import strategies as st

from app.main import app
from app.schemas.reading_list import UpdateRatingRequest


class TestBug3NullRatingRejection:
    """
    Bug Condition Exploration: Backend rejects null rating values.

    **Validates: Requirements 1.5, 1.6, 2.5, 2.6**

    This test encodes the EXPECTED behavior: the backend should accept null
    ratings and update the database to NULL, allowing users to clear ratings.

    On UNFIXED code, this test will FAIL because:
    - UpdateRatingRequest schema only accepts integers 1-5
    - Pydantic validation rejects null before reaching business logic
    - Backend returns 422 validation error

    On FIXED code, this test will PASS because:
    - UpdateRatingRequest schema accepts Optional[int]
    - Null values pass validation
    - Database is updated to NULL
    """

    @pytest.mark.asyncio
    async def test_bug3_schema_rejects_null_rating(self):
        """
        Property 1: Bug Condition - Backend Rejects Null Rating Values

        This test verifies that the UpdateRatingRequest schema accepts null ratings.

        EXPECTED OUTCOME ON UNFIXED CODE: FAIL
        - Schema validation raises ValueError or ValidationError
        - Error message: "Rating must be between 1 and 5" or similar

        EXPECTED OUTCOME ON FIXED CODE: PASS
        - Schema accepts null rating
        - No validation error is raised

        **Validates: Requirements 1.5, 1.6, 2.5, 2.6**
        """
        from pydantic import ValidationError

        # Attempt to create UpdateRatingRequest with null rating
        # On UNFIXED code: This will raise ValidationError
        # On FIXED code: This will succeed
        try:
            request = UpdateRatingRequest(rating=None)
            # If we reach here, the schema accepts null (FIXED code)
            assert request.rating is None, "Schema accepted null but stored different value"
            # Test PASSES on fixed code
        except ValidationError as e:
            # If we reach here, the schema rejects null (UNFIXED code)
            pytest.fail(
                f"Bug 3 confirmed: UpdateRatingRequest schema rejects null rating. "
                f"ValidationError: {e}\n"
                f"This is EXPECTED on unfixed code. The test encodes the correct behavior "
                f"(accepting null) and will pass after the fix is implemented."
            )

    @pytest.mark.asyncio
    async def test_bug3_api_endpoint_rejects_null_rating(self):
        """
        Property 1: Bug Condition - Backend API Rejects Null Rating Values

        This test verifies that the PATCH /api/reading-list/{article_id}/rating
        endpoint accepts null ratings and updates the database.

        EXPECTED OUTCOME ON UNFIXED CODE: FAIL
        - API returns 422 Unprocessable Entity
        - Response body contains validation error

        EXPECTED OUTCOME ON FIXED CODE: PASS
        - API returns 200 OK
        - Database is updated to NULL
        - Response confirms rating was cleared

        **Validates: Requirements 1.5, 1.6, 2.5, 2.6**
        """
        client = TestClient(app)

        # Mock authentication
        mock_user = {"discord_id": "test_user_123", "username": "TestUser"}

        # Mock SupabaseService
        mock_supabase = MagicMock()
        mock_supabase.get_or_create_user = AsyncMock(return_value=uuid4())

        # Mock database response for successful update
        mock_response = MagicMock()
        mock_response.data = [{"article_id": str(uuid4()), "rating": None}]
        mock_supabase.client.table.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value = (
            mock_response
        )

        article_id = uuid4()

        async def mock_get_current_user():
            return mock_user

        with (
            patch("app.api.reading_list.get_current_user", new=mock_get_current_user),
            patch("app.api.reading_list.SupabaseService", return_value=mock_supabase),
        ):
            # Attempt to send null rating
            # On UNFIXED code: This will return 422 validation error
            # On FIXED code: This will return 200 success
            response = client.patch(f"/api/reading-list/{article_id}/rating", json={"rating": None})

            # Check if the API accepted null rating
            if response.status_code == 422:
                # UNFIXED code: Schema validation rejected null
                error_detail = response.json().get("detail", "")
                pytest.fail(
                    f"Bug 3 confirmed: API endpoint rejects null rating with 422 error.\n"
                    f"Response: {response.json()}\n"
                    f"Error detail: {error_detail}\n"
                    f"This is EXPECTED on unfixed code. The test encodes the correct behavior "
                    f"(accepting null) and will pass after the fix is implemented."
                )

            # FIXED code: API accepted null rating
            assert response.status_code == 200, (
                f"Expected 200 OK after fix, got {response.status_code}. "
                f"Response: {response.json()}"
            )

            response_data = response.json()
            assert (
                response_data["rating"] is None
            ), f"Expected rating to be null in response, got {response_data.get('rating')}"

    @given(
        article_id=st.uuids(),
    )
    @settings(max_examples=10, phases=[Phase.generate, Phase.target], deadline=None)
    @pytest.mark.asyncio
    async def test_bug3_property_null_rating_accepted(self, article_id):
        """
        Property 1: Bug Condition - Backend Accepts Null Rating (Property-Based Test)

        For ANY article_id, when rating is null, the system SHALL accept the null
        value and update the database to set rating to NULL.

        This property-based test generates multiple article_ids and verifies that
        null ratings are consistently accepted across all inputs.

        EXPECTED OUTCOME ON UNFIXED CODE: FAIL
        - Schema validation rejects null for all generated inputs

        EXPECTED OUTCOME ON FIXED CODE: PASS
        - Schema accepts null for all generated inputs
        - Database updates succeed for all inputs

        **Validates: Requirements 1.5, 1.6, 2.5, 2.6**
        """
        client = TestClient(app)

        # Mock authentication
        mock_user = {"discord_id": "test_user_123", "username": "TestUser"}

        # Mock SupabaseService
        mock_supabase = MagicMock()
        mock_supabase.get_or_create_user = AsyncMock(return_value=uuid4())

        # Mock database response for successful update
        mock_response = MagicMock()
        mock_response.data = [{"article_id": str(article_id), "rating": None}]
        mock_supabase.client.table.return_value.update.return_value.eq.return_value.eq.return_value.execute.return_value = (
            mock_response
        )

        async def mock_get_current_user():
            return mock_user

        with (
            patch("app.api.reading_list.get_current_user", new=mock_get_current_user),
            patch("app.api.reading_list.SupabaseService", return_value=mock_supabase),
        ):
            # Attempt to send null rating for this article_id
            response = client.patch(f"/api/reading-list/{article_id}/rating", json={"rating": None})

            # On UNFIXED code: This will return 422 for all inputs
            # On FIXED code: This will return 200 for all inputs
            if response.status_code == 422:
                pytest.fail(
                    f"Bug 3 confirmed: API rejects null rating for article_id={article_id}.\n"
                    f"Response: {response.json()}\n"
                    f"This is EXPECTED on unfixed code. The property holds after the fix."
                )

            # FIXED code: Verify the property holds
            assert response.status_code == 200, (
                f"Property violated: Expected 200 OK for article_id={article_id}, "
                f"got {response.status_code}"
            )

            response_data = response.json()
            assert response_data["rating"] is None, (
                f"Property violated: Expected rating=null for article_id={article_id}, "
                f"got {response_data.get('rating')}"
            )

    @pytest.mark.asyncio
    async def test_bug3_counterexample_documentation(self):
        """
        Counterexample Documentation Test

        This test documents the specific counterexamples that demonstrate the bug:
        1. UpdateRatingRequest schema: rating: int = Field(..., ge=1, le=5) doesn't allow None
        2. Pydantic validation rejects null before reaching business logic
        3. Backend returns 422 validation error: "Rating must be between 1 and 5"

        EXPECTED OUTCOME ON UNFIXED CODE: FAIL (documents counterexamples)
        EXPECTED OUTCOME ON FIXED CODE: PASS (counterexamples no longer occur)

        **Validates: Requirements 1.5, 1.6, 2.5, 2.6**
        """
        from pydantic import ValidationError

        counterexamples = []

        # Counterexample 1: Schema validation rejects null
        try:
            UpdateRatingRequest(rating=None)
        except ValidationError as e:
            counterexamples.append(
                {
                    "type": "Schema Validation Error",
                    "error": str(e),
                    "description": "UpdateRatingRequest schema rejects null rating",
                }
            )

        # Counterexample 2: API endpoint returns 422
        client = TestClient(app)
        mock_user = {"discord_id": "test_user_123", "username": "TestUser"}

        async def mock_get_current_user():
            return mock_user

        with patch("app.api.reading_list.get_current_user", new=mock_get_current_user):
            response = client.patch(f"/api/reading-list/{uuid4()}/rating", json={"rating": None})

            if response.status_code == 422:
                counterexamples.append(
                    {
                        "type": "API Validation Error",
                        "status_code": response.status_code,
                        "response": response.json(),
                        "description": "API endpoint rejects null rating with 422 error",
                    }
                )

        # If counterexamples were found, the bug exists (UNFIXED code)
        if counterexamples:
            counterexample_report = "\n".join(
                [
                    f"\nCounterexample {i+1}: {ce['type']}\n"
                    f"  Description: {ce['description']}\n"
                    f"  Details: {ce.get('error') or ce.get('response')}"
                    for i, ce in enumerate(counterexamples)
                ]
            )

            pytest.fail(
                f"Bug 3 confirmed: Found {len(counterexamples)} counterexample(s) "
                f"demonstrating that null ratings are rejected.\n"
                f"{counterexample_report}\n\n"
                f"This is EXPECTED on unfixed code. These counterexamples prove the bug exists.\n"
                f"After the fix is implemented, this test will pass (no counterexamples found)."
            )

        # If no counterexamples were found, the bug is fixed (FIXED code)
        # Test passes silently
