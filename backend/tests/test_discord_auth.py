"""
Unit tests for DiscordAuthService

Tests cover:
- initiate_discord_link: code generation, code replacement, return value
- complete_discord_link: success, invalid code, expired code, conflict
- get_link_status: linked, not linked, pending code, expired pending code
- unlink_discord: success, no active link, pending code cleared
- get_linked_discord_accounts: returns discord links only, empty list

Validates: Requirements 5.1, 5.2, 5.5
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from app.services.discord_auth import DiscordAuthService, DiscordLinkStatus
from app.services.user_identity import (
    PLATFORM_DISCORD,
    PLATFORM_WEB,
    LinkResult,
    PlatformLink,
    UserIdentityManager,
    _VerificationEntry,
)

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


def _make_supabase_client(
    *,
    select_data: list[dict] | None = None,
    update_data: list[dict] | None = None,
    upsert_data: list[dict] | None = None,
    raise_on: str | None = None,
) -> MagicMock:
    """Build a minimal Supabase client mock."""
    client = MagicMock()

    def _make_query(data: list[dict] | None, should_raise: bool) -> MagicMock:
        response = MagicMock()
        response.data = data or []
        query = MagicMock()
        if should_raise:
            query.execute = MagicMock(side_effect=RuntimeError("db error"))
        else:
            query.execute = MagicMock(return_value=response)
        query.select = MagicMock(return_value=query)
        query.eq = MagicMock(return_value=query)
        query.limit = MagicMock(return_value=query)
        query.update = MagicMock(return_value=query)
        query.upsert = MagicMock(return_value=query)
        return query

    select_query = _make_query(select_data, raise_on == "select")
    update_query = _make_query(update_data, raise_on == "update")
    upsert_query = _make_query(upsert_data, raise_on == "upsert")

    def _table_side_effect(table_name: str) -> MagicMock:
        tbl = MagicMock()
        tbl.select = MagicMock(return_value=select_query)
        tbl.update = MagicMock(return_value=update_query)
        tbl.upsert = MagicMock(return_value=upsert_query)
        return tbl

    client.table = MagicMock(side_effect=_table_side_effect)
    return client


def _make_service(
    *,
    select_data: list[dict] | None = None,
    update_data: list[dict] | None = None,
    upsert_data: list[dict] | None = None,
    raise_on: str | None = None,
) -> DiscordAuthService:
    """Build a DiscordAuthService backed by a mock Supabase client."""
    client = _make_supabase_client(
        select_data=select_data,
        update_data=update_data,
        upsert_data=upsert_data,
        raise_on=raise_on,
    )
    identity_manager = UserIdentityManager(supabase_client=client)
    return DiscordAuthService(identity_manager=identity_manager)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# initiate_discord_link
# ---------------------------------------------------------------------------


class TestInitiateDiscordLink:
    def test_returns_six_digit_code(self):
        svc = _make_service()
        code = svc.initiate_discord_link("user-1")
        assert len(code) == 6
        assert code.isdigit()

    def test_code_stored_in_identity_manager(self):
        svc = _make_service()
        code = svc.initiate_discord_link("user-1")
        assert "user-1" in svc._identity_manager._verification_codes
        assert svc._identity_manager._verification_codes["user-1"].code == code

    def test_new_call_replaces_previous_code(self):
        svc = _make_service()
        code1 = svc.initiate_discord_link("user-1")
        code2 = svc.initiate_discord_link("user-1")
        # Only one entry per user
        assert len([k for k in svc._identity_manager._verification_codes if k == "user-1"]) == 1
        # The stored code is the latest one
        assert svc._identity_manager._verification_codes["user-1"].code == code2

    def test_different_users_get_independent_codes(self):
        svc = _make_service()
        svc.initiate_discord_link("user-1")
        svc.initiate_discord_link("user-2")
        assert "user-1" in svc._identity_manager._verification_codes
        assert "user-2" in svc._identity_manager._verification_codes

    def test_code_has_ten_minute_expiry(self):
        svc = _make_service()
        before = datetime.now(timezone.utc)
        svc.initiate_discord_link("user-1")
        after = datetime.now(timezone.utc)

        entry = svc._identity_manager._verification_codes["user-1"]
        assert entry.expires_at >= before + timedelta(minutes=10)
        assert entry.expires_at <= after + timedelta(minutes=10, seconds=1)


# ---------------------------------------------------------------------------
# complete_discord_link
# ---------------------------------------------------------------------------


class TestCompleteDiscordLink:
    @pytest.mark.asyncio
    async def test_successful_link(self):
        svc = _make_service(select_data=[], upsert_data=[{"user_id": "u1"}])
        code = svc.initiate_discord_link("u1")

        result = await svc.complete_discord_link(
            user_id="u1",
            discord_user_id="discord-123",
            code=code,
        )

        assert result.success is True
        assert result.user_id == "u1"
        assert result.platform == PLATFORM_DISCORD
        assert result.platform_user_id == "discord-123"
        assert result.error is None

    @pytest.mark.asyncio
    async def test_invalid_code_fails(self):
        svc = _make_service()
        # No code generated → validation fails
        result = await svc.complete_discord_link(
            user_id="u1",
            discord_user_id="discord-123",
            code="000000",
        )

        assert result.success is False
        assert result.error is not None
        assert "verification code" in result.error.lower()

    @pytest.mark.asyncio
    async def test_expired_code_fails(self):
        svc = _make_service()
        code = svc.initiate_discord_link("u1")
        # Manually expire the code
        svc._identity_manager._verification_codes["u1"] = _VerificationEntry(
            code=code,
            expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
        )

        result = await svc.complete_discord_link(
            user_id="u1",
            discord_user_id="discord-123",
            code=code,
        )

        assert result.success is False

    @pytest.mark.asyncio
    async def test_discord_id_already_linked_to_other_user_fails(self):
        svc = _make_service(select_data=[{"user_id": "other-user"}])
        code = svc.initiate_discord_link("u1")

        result = await svc.complete_discord_link(
            user_id="u1",
            discord_user_id="discord-123",
            code=code,
        )

        assert result.success is False
        assert "already linked" in result.error

    @pytest.mark.asyncio
    async def test_relinking_same_account_succeeds(self):
        """Linking the same discord_user_id back to the same user is allowed."""
        svc = _make_service(
            select_data=[{"user_id": "u1"}],
            upsert_data=[{"user_id": "u1"}],
        )
        code = svc.initiate_discord_link("u1")

        result = await svc.complete_discord_link(
            user_id="u1",
            discord_user_id="discord-123",
            code=code,
        )

        assert result.success is True

    @pytest.mark.asyncio
    async def test_returns_link_result_type(self):
        svc = _make_service(select_data=[], upsert_data=[{"user_id": "u1"}])
        code = svc.initiate_discord_link("u1")

        result = await svc.complete_discord_link("u1", "discord-123", code)

        assert isinstance(result, LinkResult)


# ---------------------------------------------------------------------------
# get_link_status
# ---------------------------------------------------------------------------


class TestGetLinkStatus:
    @pytest.mark.asyncio
    async def test_returns_linked_status_when_discord_link_exists(self):
        svc = _make_service(
            select_data=[
                {
                    "user_id": "u1",
                    "platform": PLATFORM_DISCORD,
                    "platform_user_id": "discord-123",
                    "platform_username": "TestUser#0001",
                    "linked_at": _now_iso(),
                    "is_active": True,
                }
            ]
        )

        status = await svc.get_link_status("u1")

        assert isinstance(status, DiscordLinkStatus)
        assert status.is_linked is True
        assert status.discord_user_id == "discord-123"
        assert status.discord_username == "TestUser#0001"
        assert status.linked_at is not None

    @pytest.mark.asyncio
    async def test_returns_not_linked_when_no_discord_link(self):
        svc = _make_service(select_data=[])

        status = await svc.get_link_status("u1")

        assert status.is_linked is False
        assert status.discord_user_id is None
        assert status.discord_username is None
        assert status.linked_at is None

    @pytest.mark.asyncio
    async def test_pending_code_included_when_active(self):
        svc = _make_service(select_data=[])
        code = svc.initiate_discord_link("u1")

        status = await svc.get_link_status("u1")

        assert status.pending_code == code

    @pytest.mark.asyncio
    async def test_pending_code_is_none_when_no_code_generated(self):
        svc = _make_service(select_data=[])

        status = await svc.get_link_status("u1")

        assert status.pending_code is None

    @pytest.mark.asyncio
    async def test_pending_code_is_none_when_code_expired(self):
        svc = _make_service(select_data=[])
        code = svc.initiate_discord_link("u1")
        # Expire the code
        svc._identity_manager._verification_codes["u1"] = _VerificationEntry(
            code=code,
            expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
        )

        status = await svc.get_link_status("u1")

        assert status.pending_code is None

    @pytest.mark.asyncio
    async def test_non_discord_links_are_ignored(self):
        """Only Discord links should affect is_linked."""
        svc = _make_service(
            select_data=[
                {
                    "user_id": "u1",
                    "platform": PLATFORM_WEB,
                    "platform_user_id": "web-user-1",
                    "platform_username": None,
                    "linked_at": _now_iso(),
                    "is_active": True,
                }
            ]
        )

        status = await svc.get_link_status("u1")

        assert status.is_linked is False

    @pytest.mark.asyncio
    async def test_linked_status_with_pending_code(self):
        """A user can be linked AND have a pending code (e.g. re-linking)."""
        svc = _make_service(
            select_data=[
                {
                    "user_id": "u1",
                    "platform": PLATFORM_DISCORD,
                    "platform_user_id": "discord-123",
                    "platform_username": None,
                    "linked_at": _now_iso(),
                    "is_active": True,
                }
            ]
        )
        code = svc.initiate_discord_link("u1")

        status = await svc.get_link_status("u1")

        assert status.is_linked is True
        assert status.pending_code == code


# ---------------------------------------------------------------------------
# unlink_discord
# ---------------------------------------------------------------------------


class TestUnlinkDiscord:
    @pytest.mark.asyncio
    async def test_successful_unlink_returns_true(self):
        svc = _make_service(update_data=[{"user_id": "u1", "is_active": False}])
        result = await svc.unlink_discord("u1")
        assert result is True

    @pytest.mark.asyncio
    async def test_no_active_link_returns_false(self):
        svc = _make_service(update_data=[])
        result = await svc.unlink_discord("u1")
        assert result is False

    @pytest.mark.asyncio
    async def test_pending_code_cleared_on_unlink(self):
        svc = _make_service(update_data=[{"user_id": "u1", "is_active": False}])
        svc.initiate_discord_link("u1")
        assert "u1" in svc._identity_manager._verification_codes

        await svc.unlink_discord("u1")

        assert "u1" not in svc._identity_manager._verification_codes

    @pytest.mark.asyncio
    async def test_pending_code_cleared_even_when_no_active_link(self):
        """Pending code should be cleared regardless of whether a link existed."""
        svc = _make_service(update_data=[])
        svc.initiate_discord_link("u1")
        assert "u1" in svc._identity_manager._verification_codes

        await svc.unlink_discord("u1")

        assert "u1" not in svc._identity_manager._verification_codes

    @pytest.mark.asyncio
    async def test_unlink_does_not_affect_other_users(self):
        svc = _make_service(update_data=[{"user_id": "u1", "is_active": False}])
        svc.initiate_discord_link("u2")

        await svc.unlink_discord("u1")

        # u2's code should still be present
        assert "u2" in svc._identity_manager._verification_codes


# ---------------------------------------------------------------------------
# get_linked_discord_accounts
# ---------------------------------------------------------------------------


class TestGetLinkedDiscordAccounts:
    @pytest.mark.asyncio
    async def test_returns_discord_links_only(self):
        svc = _make_service(
            select_data=[
                {
                    "user_id": "u1",
                    "platform": PLATFORM_DISCORD,
                    "platform_user_id": "discord-123",
                    "platform_username": "TestUser",
                    "linked_at": _now_iso(),
                    "is_active": True,
                },
                {
                    "user_id": "u1",
                    "platform": PLATFORM_WEB,
                    "platform_user_id": "web-user-1",
                    "platform_username": None,
                    "linked_at": _now_iso(),
                    "is_active": True,
                },
            ]
        )

        links = await svc.get_linked_discord_accounts("u1")

        assert len(links) == 1
        assert links[0].platform == PLATFORM_DISCORD
        assert links[0].platform_user_id == "discord-123"

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_discord_links(self):
        svc = _make_service(select_data=[])

        links = await svc.get_linked_discord_accounts("u1")

        assert links == []

    @pytest.mark.asyncio
    async def test_returns_platform_link_objects(self):
        svc = _make_service(
            select_data=[
                {
                    "user_id": "u1",
                    "platform": PLATFORM_DISCORD,
                    "platform_user_id": "discord-123",
                    "platform_username": "TestUser",
                    "linked_at": _now_iso(),
                    "is_active": True,
                }
            ]
        )

        links = await svc.get_linked_discord_accounts("u1")

        assert len(links) == 1
        assert isinstance(links[0], PlatformLink)

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_only_web_links(self):
        svc = _make_service(
            select_data=[
                {
                    "user_id": "u1",
                    "platform": PLATFORM_WEB,
                    "platform_user_id": "web-user-1",
                    "platform_username": None,
                    "linked_at": _now_iso(),
                    "is_active": True,
                }
            ]
        )

        links = await svc.get_linked_discord_accounts("u1")

        assert links == []


# ---------------------------------------------------------------------------
# Integration-style: full initiate → complete → status → unlink flow
# ---------------------------------------------------------------------------


class TestFullDiscordAuthFlow:
    @pytest.mark.asyncio
    async def test_initiate_complete_status_unlink(self):
        """Full happy-path: initiate → complete → check status → unlink."""
        # Step 1: initiate — generates a code
        svc = _make_service(select_data=[], upsert_data=[{"user_id": "u1"}])
        code = svc.initiate_discord_link("u1")
        assert len(code) == 6

        # Step 2: complete — link the account
        result = await svc.complete_discord_link("u1", "discord-abc", code)
        assert result.success is True

        # Step 3: check status — now linked (need fresh mock with link data)
        svc2 = _make_service(
            select_data=[
                {
                    "user_id": "u1",
                    "platform": PLATFORM_DISCORD,
                    "platform_user_id": "discord-abc",
                    "platform_username": None,
                    "linked_at": _now_iso(),
                    "is_active": True,
                }
            ]
        )
        status = await svc2.get_link_status("u1")
        assert status.is_linked is True
        assert status.discord_user_id == "discord-abc"

        # Step 4: unlink
        svc3 = _make_service(update_data=[{"user_id": "u1", "is_active": False}])
        unlinked = await svc3.unlink_discord("u1")
        assert unlinked is True

    @pytest.mark.asyncio
    async def test_code_consumed_after_complete(self):
        """After completing the link, the verification code must be consumed."""
        svc = _make_service(select_data=[], upsert_data=[{"user_id": "u1"}])
        code = svc.initiate_discord_link("u1")

        await svc.complete_discord_link("u1", "discord-abc", code)

        # Code should be consumed — second attempt must fail
        result2 = await svc.complete_discord_link("u1", "discord-abc", code)
        assert result2.success is False

    @pytest.mark.asyncio
    async def test_status_shows_pending_code_before_completion(self):
        svc = _make_service(select_data=[])
        code = svc.initiate_discord_link("u1")

        status = await svc.get_link_status("u1")

        assert status.is_linked is False
        assert status.pending_code == code

    @pytest.mark.asyncio
    async def test_get_linked_accounts_after_link(self):
        svc = _make_service(
            select_data=[
                {
                    "user_id": "u1",
                    "platform": PLATFORM_DISCORD,
                    "platform_user_id": "discord-abc",
                    "platform_username": None,
                    "linked_at": _now_iso(),
                    "is_active": True,
                }
            ]
        )

        links = await svc.get_linked_discord_accounts("u1")

        assert len(links) == 1
        assert links[0].platform_user_id == "discord-abc"
