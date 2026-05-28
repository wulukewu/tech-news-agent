from unittest.mock import MagicMock, patch

import pytest

from app.services.llm_service import LLMService


@pytest.mark.asyncio
async def test_generate_takeaway_cache_hit():
    """Verify that if actionable_takeaway exists in the database, it returns it instantly."""
    article_id = "test-article-123"
    cached_takeaway = "這是一句快取的技術精華。"

    # Mock Supabase response
    mock_supabase_client = MagicMock()
    mock_table = MagicMock()
    mock_eq = MagicMock()
    mock_execute = MagicMock()

    mock_execute.return_value = MagicMock(
        data=[
            {
                "title": "測試文章",
                "category": "技術",
                "actionable_takeaway": cached_takeaway,
                "ai_summary": "文章摘要",
            }
        ]
    )

    mock_supabase_client.table.return_value = mock_table
    mock_table.select.return_value = mock_table
    mock_table.eq.return_value = mock_eq
    mock_eq.execute = mock_execute

    with patch("app.services.supabase_service.SupabaseService") as mock_supabase_class:
        mock_supabase_instance = MagicMock()
        mock_supabase_instance.client = mock_supabase_client
        mock_supabase_class.return_value = mock_supabase_instance

        llm_service = LLMService.__new__(LLMService)
        llm_service.client = MagicMock()
        takeaway = await llm_service.generate_takeaway(article_id)

        assert takeaway == cached_takeaway
        # Ensure Groq API is not called
        assert (
            not hasattr(llm_service.client.chat.completions, "create_async")
            or not llm_service.client.chat.completions.create.called
        )


@pytest.mark.asyncio
async def test_generate_takeaway_cache_miss():
    """Verify that if actionable_takeaway is missing, it calls Groq, caches it in DB, and returns it."""
    article_id = "test-article-456"
    generated_takeaway = "這是動態生成的技術精華核心要點。"

    # Mock Supabase response for select (cache miss)
    mock_supabase_client = MagicMock()

    # Setup select chain
    mock_select_table = MagicMock()
    mock_select_eq = MagicMock()
    mock_select_execute = MagicMock()
    mock_select_execute.return_value = MagicMock(
        data=[
            {"title": "測試文章", "category": "技術", "actionable_takeaway": None, "ai_summary": "文章摘要"}
        ]
    )
    mock_select_table.select.return_value = mock_select_table
    mock_select_table.eq.return_value = mock_select_eq
    mock_select_eq.execute = mock_select_execute

    # Setup update chain
    mock_update_table = MagicMock()
    mock_update_eq = MagicMock()
    mock_update_execute = MagicMock()
    mock_update_table.update.return_value = mock_update_table
    mock_update_table.eq.return_value = mock_update_eq
    mock_update_eq.execute = mock_update_execute

    def get_table(table_name):
        return mock_supabase_client

    mock_supabase_client.table = get_table
    mock_supabase_client.select = mock_select_table.select
    mock_supabase_client.update = mock_update_table.update

    # Mock Groq client chat completion
    mock_groq_response = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    mock_message.content = generated_takeaway
    mock_choice.message = mock_message
    mock_groq_response.choices = [mock_choice]

    with patch(
        "app.services.supabase_service.SupabaseService"
    ) as mock_supabase_class, patch.object(LLMService, "_call_groq") as mock_call_groq:
        mock_supabase_instance = MagicMock()
        mock_supabase_instance.client = mock_supabase_client
        mock_supabase_class.return_value = mock_supabase_instance

        mock_call_groq.return_value = mock_groq_response

        llm_service = LLMService.__new__(LLMService)
        llm_service.client = MagicMock()
        takeaway = await llm_service.generate_takeaway(article_id)

        assert takeaway == generated_takeaway
        # Verify Supabase update was called to cache back the takeaway
        mock_update_table.update.assert_called_once_with(
            {"actionable_takeaway": generated_takeaway}
        )
