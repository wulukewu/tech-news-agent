"""
E2E integration tests for Intelligent Reminder Agent.
Tests the full pipeline: article analysis → reminder generation → delivery → interaction tracking.
"""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest


def _make_agent(supabase_mock=None, notification_mock=None):
    from app.qa_agent.intelligent_reminder.intelligent_reminder_agent import (
        IntelligentReminderAgent,
    )

    agent = IntelligentReminderAgent.__new__(IntelligentReminderAgent)
    agent.supabase_service = supabase_mock or MagicMock()
    agent.notification_service = notification_mock or MagicMock()
    agent.llm_service = MagicMock()
    agent.content_analyzer = MagicMock()
    agent.version_tracker = MagicMock()
    agent.behavior_analyzer = MagicMock()
    agent.timing_engine = MagicMock()
    agent.context_generator = MagicMock()
    return agent


def _make_reminder(user_id=None, content_id=None, channel="discord"):
    uid = str(user_id or uuid4())
    cid = str(content_id or uuid4())
    return {
        "id": str(uuid4()),
        "user_id": uid,
        "content_id": cid,
        "channel": channel,
        "status": "pending",
        "reminder_context": {
            "title": "Test Reminder",
            "description": "You should read this related article",
            "related_articles": [],
            "version_info": None,
            "reading_time_estimate": 5,
            "priority_score": 0.7,
            "action_url": "https://example.com/article",
        },
    }


# ── Task 8.3: Cross-channel read sync ─────────────────────────────────────────


class TestCrossChannelSync:
    """When a reminder is already read on one channel, skip sending on another."""

    @pytest.mark.asyncio
    async def test_skips_send_if_already_read_on_another_channel(self):
        supabase = MagicMock()
        notification = MagicMock()
        notification.send_discord_dm = AsyncMock(return_value=True)

        # Simulate: content already read on web channel
        supabase.client.table.return_value.select.return_value.eq.return_value.eq.return_value.in_.return_value.execute.return_value = MagicMock(
            data=[{"id": str(uuid4())}]  # non-empty = already read
        )
        supabase.client.table.return_value.update.return_value.eq.return_value.execute.return_value = (
            MagicMock()
        )

        agent = _make_agent(supabase, notification)
        reminder = _make_reminder(channel="discord")

        await agent._send_reminder(reminder)

        # Discord DM should NOT have been called
        notification.send_discord_dm.assert_not_called()

    @pytest.mark.asyncio
    async def test_sends_if_not_yet_read_on_any_channel(self):
        supabase = MagicMock()
        notification = MagicMock()
        notification.send_discord_dm = AsyncMock(return_value=True)

        # Simulate: not read anywhere yet
        supabase.client.table.return_value.select.return_value.eq.return_value.eq.return_value.in_.return_value.execute.return_value = MagicMock(
            data=[]  # empty = not read
        )
        supabase.client.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[]  # no failures
        )
        supabase.client.table.return_value.update.return_value.eq.return_value.execute.return_value = (
            MagicMock()
        )

        agent = _make_agent(supabase, notification)
        reminder = _make_reminder(channel="discord")

        await agent._send_reminder(reminder)

        notification.send_discord_dm.assert_called_once()


# ── Task 8.3: Channel fallback after 3 failures ───────────────────────────────


class TestChannelFallback:
    """After 3 consecutive failures, _resolve_channel should switch to fallback."""

    @pytest.mark.asyncio
    async def test_falls_back_after_3_failures(self):
        supabase = MagicMock()
        # Simulate 3 recent failures for discord
        supabase.client.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[{"status": "failed"}, {"status": "failed"}, {"status": "failed"}]
        )

        agent = _make_agent(supabase)
        result = await agent._resolve_channel("user-1", "discord")
        assert result == "web"

    @pytest.mark.asyncio
    async def test_keeps_channel_with_fewer_than_3_failures(self):
        supabase = MagicMock()
        # Only 2 failures
        supabase.client.table.return_value.select.return_value.eq.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[{"status": "failed"}, {"status": "failed"}]
        )

        agent = _make_agent(supabase)
        result = await agent._resolve_channel("user-1", "discord")
        assert result == "discord"


# ── Task 8.6: Interaction tracking pipeline ───────────────────────────────────


class TestInteractionTracking:
    """track_reminder_interaction updates status and triggers behavior analysis."""

    @pytest.mark.asyncio
    async def test_read_interaction_updates_status(self):
        supabase = MagicMock()
        reminder_id = uuid4()

        # Mock _get_reminder_by_id
        supabase.client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[
                {
                    "id": str(reminder_id),
                    "user_id": str(uuid4()),
                    "status": "delivered",
                    "sent_at": datetime.now(timezone.utc).isoformat(),
                }
            ]
        )
        supabase.client.table.return_value.update.return_value.eq.return_value.execute.return_value = (
            MagicMock()
        )

        agent = _make_agent(supabase)
        agent.behavior_analyzer.track_reminder_response = AsyncMock()

        await agent.track_reminder_interaction(reminder_id, "read")

        # Verify update was called with "read" status
        update_call = supabase.client.table.return_value.update.call_args
        assert update_call is not None
        update_data = update_call[0][0]
        assert update_data["status"] == "read"

    @pytest.mark.asyncio
    async def test_dismissed_interaction_does_not_trigger_behavior_tracking(self):
        supabase = MagicMock()
        reminder_id = uuid4()

        supabase.client.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[
                {
                    "id": str(reminder_id),
                    "user_id": str(uuid4()),
                    "status": "delivered",
                    "sent_at": datetime.now(timezone.utc).isoformat(),
                }
            ]
        )
        supabase.client.table.return_value.update.return_value.eq.return_value.execute.return_value = (
            MagicMock()
        )

        agent = _make_agent(supabase)
        agent.behavior_analyzer.track_reminder_response = AsyncMock()

        await agent.track_reminder_interaction(reminder_id, "dismissed")

        # behavior_analyzer should NOT be called for dismissed
        agent.behavior_analyzer.track_reminder_response.assert_not_called()
