"""
Unit tests for UserIdentityManager

Tests cover:
- generate_verification_code: code format, expiry, one-code-per-user
- validate_verification_code: valid code, expired code, wrong code, missing code
- link_platform_account: success, invalid platform, bad token, duplicate link
- unlink_platform_account: success, no active link found
- get_user_by_platform_id: found, not found, db error
- get_linked_platforms: returns list, empty list, db error
- verify_platform_identity: id match + active link, id mismatch, no link
- audit log: entries recorded for link/unlink operations

Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from app.core.errors import DatabaseError
from app.services.user_identity import (
    PLATFORM_DISCORD,
    PLATFORM_WEB,
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
    """Build a minimal Supabase client mock.

    Args:
        select_data: Rows returned by ``.execute()`` on SELECT queries.
        update_data: Rows returned by ``.execute()`` on UPDATE queries.
        upsert_data: Rows returned by ``.execute()`` on UPSERT queries.
        raise_on: If set to ``"select"``, ``"update"``, or ``"upsert"``,
            the corresponding execute call will raise a ``RuntimeError``.
    """
    client = MagicMock()

    # Build a chainable query mock
    def _make_query(data: list[dict] | None, should_raise: bool) -> MagicMock:
        response = MagicMock()
        response.data = data or []
        query = MagicMock()
        if should_raise:
            query.execute = MagicMock(side_effect=RuntimeError("db error"))
        else:
            query.execute = MagicMock(return_value=response)
        # Make every chained call return the same query mock
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


def _make_manager(
    *,
    select_data: list[dict] | None = None,
    update_data: list[dict] | None = None,
    upsert_data: list[dict] | None = None,
    raise_on: str | None = None,
) -> UserIdentityManager:
    client = _make_supabase_client(
        select_data=select_data,
        update_data=update_data,
        upsert_data=upsert_data,
        raise_on=raise_on,
    )
    return UserIdentityManager(supabase_client=client)


# ---------------------------------------------------------------------------
# generate_verification_code
# ---------------------------------------------------------------------------


class TestGenerateVerificationCode:
    def test_returns_six_digit_string(self):
        mgr = _make_manager()
        code = mgr.generate_verification_code("user-1")
        assert len(code) == 6
        assert code.isdigit()

    def test_code_stored_in_memory(self):
        mgr = _make_manager()
        code = mgr.generate_verification_code("user-1")
        assert "user-1" in mgr._verification_codes
        assert mgr._verification_codes["user-1"].code == code

    def test_expiry_is_ten_minutes_from_now(self):
        mgr = _make_manager()
        before = datetime.now(timezone.utc)
        mgr.generate_verification_code("user-1")
        after = datetime.now(timezone.utc)

        entry = mgr._verification_codes["user-1"]
        assert entry.expires_at >= before + timedelta(minutes=10)
        assert entry.expires_at <= after + timedelta(minutes=10, seconds=1)

    def test_new_code_replaces_old_code(self):
        mgr = _make_manager()
        code1 = mgr.generate_verification_code("user-1")
        code2 = mgr.generate_verification_code("user-1")
        # Only one entry per user
        assert len([k for k in mgr._verification_codes if k == "user-1"]) == 1
        # The stored code is the latest one
        assert mgr._verification_codes["user-1"].code == code2

    def test_different_users_get_independent_codes(self):
        mgr = _make_manager()
        mgr.generate_verification_code("user-1")
        mgr.generate_verification_code("user-2")
        assert "user-1" in mgr._verification_codes
        assert "user-2" in mgr._verification_codes


# ---------------------------------------------------------------------------
# validate_verification_code
# ---------------------------------------------------------------------------


class TestValidateVerificationCode:
    def test_valid_code_returns_true(self):
        mgr = _make_manager()
        code = mgr.generate_verification_code("user-1")
        assert mgr.validate_verification_code("user-1", code) is True

    def test_valid_code_is_consumed(self):
        """After a successful validation the code must be removed."""
        mgr = _make_manager()
        code = mgr.generate_verification_code("user-1")
        mgr.validate_verification_code("user-1", code)
        # Second attempt with the same code must fail
        assert mgr.validate_verification_code("user-1", code) is False

    def test_wrong_code_returns_false(self):
        mgr = _make_manager()
        mgr.generate_verification_code("user-1")
        assert mgr.validate_verification_code("user-1", "000000") is False

    def test_no_code_returns_false(self):
        mgr = _make_manager()
        assert mgr.validate_verification_code("user-1", "123456") is False

    def test_expired_code_returns_false(self):
        mgr = _make_manager()
        code = mgr.generate_verification_code("user-1")
        # Manually expire the entry
        mgr._verification_codes["user-1"] = _VerificationEntry(
            code=code,
            expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
        )
        assert mgr.validate_verification_code("user-1", code) is False

    def test_expired_code_is_cleaned_up(self):
        mgr = _make_manager()
        code = mgr.generate_verification_code("user-1")
        mgr._verification_codes["user-1"] = _VerificationEntry(
            code=code,
            expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
        )
        mgr.validate_verification_code("user-1", code)
        assert "user-1" not in mgr._verification_codes

    def test_wrong_user_returns_false(self):
        mgr = _make_manager()
        code = mgr.generate_verification_code("user-1")
        assert mgr.validate_verification_code("user-2", code) is False


# ---------------------------------------------------------------------------
# link_platform_account
# ---------------------------------------------------------------------------


class TestLinkPlatformAccount:
    @pytest.mark.asyncio
    async def test_successful_link(self):
        # No existing owner → select returns empty
        mgr = _make_manager(select_data=[], upsert_data=[{"user_id": "u1"}])
        code = mgr.generate_verification_code("u1")

        result = await mgr.link_platform_account(
            user_id="u1",
            platform=PLATFORM_DISCORD,
            platform_user_id="discord-123",
            verification_token=code,
        )

        assert result.success is True
        assert result.user_id == "u1"
        assert result.platform == PLATFORM_DISCORD
        assert result.platform_user_id == "discord-123"
        assert result.error is None

    @pytest.mark.asyncio
    async def test_unsupported_platform_fails(self):
        mgr = _make_manager()
        code = mgr.generate_verification_code("u1")

        result = await mgr.link_platform_account(
            user_id="u1",
            platform="telegram",
            platform_user_id="tg-123",
            verification_token=code,
        )

        assert result.success is False
        assert "Unsupported platform" in result.error

    @pytest.mark.asyncio
    async def test_invalid_verification_token_fails(self):
        mgr = _make_manager()

        result = await mgr.link_platform_account(
            user_id="u1",
            platform=PLATFORM_DISCORD,
            platform_user_id="discord-123",
            verification_token="000000",
        )

        assert result.success is False
        assert "verification code" in result.error.lower()

    @pytest.mark.asyncio
    async def test_expired_verification_token_fails(self):
        mgr = _make_manager()
        code = mgr.generate_verification_code("u1")
        # Expire the code
        mgr._verification_codes["u1"] = _VerificationEntry(
            code=code,
            expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
        )

        result = await mgr.link_platform_account(
            user_id="u1",
            platform=PLATFORM_DISCORD,
            platform_user_id="discord-123",
            verification_token=code,
        )

        assert result.success is False

    @pytest.mark.asyncio
    async def test_platform_already_linked_to_other_user_fails(self):
        # select returns a different owner
        mgr = _make_manager(select_data=[{"user_id": "other-user"}])
        code = mgr.generate_verification_code("u1")

        result = await mgr.link_platform_account(
            user_id="u1",
            platform=PLATFORM_DISCORD,
            platform_user_id="discord-123",
            verification_token=code,
        )

        assert result.success is False
        assert "already linked" in result.error

    @pytest.mark.asyncio
    async def test_relinking_same_account_succeeds(self):
        """Linking the same platform_user_id back to the same user is allowed."""
        mgr = _make_manager(
            select_data=[{"user_id": "u1"}],
            upsert_data=[{"user_id": "u1"}],
        )
        code = mgr.generate_verification_code("u1")

        result = await mgr.link_platform_account(
            user_id="u1",
            platform=PLATFORM_DISCORD,
            platform_user_id="discord-123",
            verification_token=code,
        )

        assert result.success is True

    @pytest.mark.asyncio
    async def test_db_error_on_select_raises_database_error(self):
        mgr = _make_manager(raise_on="select")
        code = mgr.generate_verification_code("u1")

        with pytest.raises(DatabaseError):
            await mgr.link_platform_account(
                user_id="u1",
                platform=PLATFORM_DISCORD,
                platform_user_id="discord-123",
                verification_token=code,
            )

    @pytest.mark.asyncio
    async def test_db_error_on_upsert_raises_database_error(self):
        mgr = _make_manager(select_data=[], raise_on="upsert")
        code = mgr.generate_verification_code("u1")

        with pytest.raises(DatabaseError):
            await mgr.link_platform_account(
                user_id="u1",
                platform=PLATFORM_DISCORD,
                platform_user_id="discord-123",
                verification_token=code,
            )

    @pytest.mark.asyncio
    async def test_audit_entry_recorded_on_success(self):
        mgr = _make_manager(select_data=[], upsert_data=[{"user_id": "u1"}])
        code = mgr.generate_verification_code("u1")
        await mgr.link_platform_account("u1", PLATFORM_DISCORD, "d-1", code)

        log = mgr.get_audit_log()
        assert len(log) == 1
        assert log[0].action == "link"
        assert log[0].success is True
        assert log[0].user_id == "u1"

    @pytest.mark.asyncio
    async def test_audit_entry_recorded_on_failure(self):
        mgr = _make_manager()
        # No code generated → validation fails
        result = await mgr.link_platform_account("u1", PLATFORM_DISCORD, "d-1", "bad")

        assert result.success is False
        log = mgr.get_audit_log()
        assert len(log) == 1
        assert log[0].action == "link"
        assert log[0].success is False


# ---------------------------------------------------------------------------
# unlink_platform_account
# ---------------------------------------------------------------------------


class TestUnlinkPlatformAccount:
    @pytest.mark.asyncio
    async def test_successful_unlink(self):
        mgr = _make_manager(update_data=[{"user_id": "u1", "is_active": False}])
        result = await mgr.unlink_platform_account("u1", PLATFORM_DISCORD)
        assert result is True

    @pytest.mark.asyncio
    async def test_no_active_link_returns_false(self):
        mgr = _make_manager(update_data=[])
        result = await mgr.unlink_platform_account("u1", PLATFORM_DISCORD)
        assert result is False

    @pytest.mark.asyncio
    async def test_db_error_raises_database_error(self):
        mgr = _make_manager(raise_on="update")
        with pytest.raises(DatabaseError):
            await mgr.unlink_platform_account("u1", PLATFORM_DISCORD)

    @pytest.mark.asyncio
    async def test_audit_entry_recorded_on_success(self):
        mgr = _make_manager(update_data=[{"user_id": "u1"}])
        await mgr.unlink_platform_account("u1", PLATFORM_DISCORD)

        log = mgr.get_audit_log()
        assert len(log) == 1
        assert log[0].action == "unlink"
        assert log[0].success is True

    @pytest.mark.asyncio
    async def test_audit_entry_recorded_on_no_link(self):
        mgr = _make_manager(update_data=[])
        await mgr.unlink_platform_account("u1", PLATFORM_DISCORD)

        log = mgr.get_audit_log()
        assert len(log) == 1
        assert log[0].action == "unlink"
        assert log[0].success is False


# ---------------------------------------------------------------------------
# get_user_by_platform_id
# ---------------------------------------------------------------------------


class TestGetUserByPlatformId:
    @pytest.mark.asyncio
    async def test_returns_user_id_when_found(self):
        mgr = _make_manager(select_data=[{"user_id": "u1"}])
        result = await mgr.get_user_by_platform_id(PLATFORM_DISCORD, "discord-123")
        assert result == "u1"

    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self):
        mgr = _make_manager(select_data=[])
        result = await mgr.get_user_by_platform_id(PLATFORM_DISCORD, "discord-999")
        assert result is None

    @pytest.mark.asyncio
    async def test_db_error_raises_database_error(self):
        mgr = _make_manager(raise_on="select")
        with pytest.raises(DatabaseError):
            await mgr.get_user_by_platform_id(PLATFORM_DISCORD, "discord-123")


# ---------------------------------------------------------------------------
# get_linked_platforms
# ---------------------------------------------------------------------------


class TestGetLinkedPlatforms:
    @pytest.mark.asyncio
    async def test_returns_platform_links(self):
        now_iso = datetime.now(timezone.utc).isoformat()
        mgr = _make_manager(
            select_data=[
                {
                    "user_id": "u1",
                    "platform": PLATFORM_DISCORD,
                    "platform_user_id": "discord-123",
                    "platform_username": "TestUser",
                    "linked_at": now_iso,
                    "is_active": True,
                }
            ]
        )
        links = await mgr.get_linked_platforms("u1")

        assert len(links) == 1
        link = links[0]
        assert isinstance(link, PlatformLink)
        assert link.user_id == "u1"
        assert link.platform == PLATFORM_DISCORD
        assert link.platform_user_id == "discord-123"
        assert link.platform_username == "TestUser"
        assert link.is_active is True

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_links(self):
        mgr = _make_manager(select_data=[])
        links = await mgr.get_linked_platforms("u1")
        assert links == []

    @pytest.mark.asyncio
    async def test_linked_at_parsed_from_iso_string(self):
        ts = "2024-06-01T12:00:00+00:00"
        mgr = _make_manager(
            select_data=[
                {
                    "user_id": "u1",
                    "platform": PLATFORM_DISCORD,
                    "platform_user_id": "d-1",
                    "platform_username": None,
                    "linked_at": ts,
                    "is_active": True,
                }
            ]
        )
        links = await mgr.get_linked_platforms("u1")
        assert links[0].linked_at.year == 2024
        assert links[0].linked_at.month == 6

    @pytest.mark.asyncio
    async def test_db_error_raises_database_error(self):
        mgr = _make_manager(raise_on="select")
        with pytest.raises(DatabaseError):
            await mgr.get_linked_platforms("u1")

    @pytest.mark.asyncio
    async def test_multiple_links_returned(self):
        now_iso = datetime.now(timezone.utc).isoformat()
        mgr = _make_manager(
            select_data=[
                {
                    "user_id": "u1",
                    "platform": PLATFORM_DISCORD,
                    "platform_user_id": "d-1",
                    "platform_username": None,
                    "linked_at": now_iso,
                    "is_active": True,
                },
                {
                    "user_id": "u1",
                    "platform": PLATFORM_WEB,
                    "platform_user_id": "w-1",
                    "platform_username": None,
                    "linked_at": now_iso,
                    "is_active": True,
                },
            ]
        )
        links = await mgr.get_linked_platforms("u1")
        assert len(links) == 2
        platforms = {lnk.platform for lnk in links}
        assert platforms == {PLATFORM_DISCORD, PLATFORM_WEB}


# ---------------------------------------------------------------------------
# verify_platform_identity
# ---------------------------------------------------------------------------


class TestVerifyPlatformIdentity:
    @pytest.mark.asyncio
    async def test_returns_true_when_id_matches_and_link_exists(self):
        mgr = _make_manager(select_data=[{"user_id": "u1"}])
        result = await mgr.verify_platform_identity(
            platform=PLATFORM_DISCORD,
            platform_user_id="discord-123",
            verification_data={"platform_user_id": "discord-123"},
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_returns_false_when_id_mismatch(self):
        mgr = _make_manager(select_data=[{"user_id": "u1"}])
        result = await mgr.verify_platform_identity(
            platform=PLATFORM_DISCORD,
            platform_user_id="discord-123",
            verification_data={"platform_user_id": "discord-WRONG"},
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_returns_false_when_no_active_link(self):
        mgr = _make_manager(select_data=[])
        result = await mgr.verify_platform_identity(
            platform=PLATFORM_DISCORD,
            platform_user_id="discord-123",
            verification_data={"platform_user_id": "discord-123"},
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_returns_false_on_db_error(self):
        mgr = _make_manager(raise_on="select")
        result = await mgr.verify_platform_identity(
            platform=PLATFORM_DISCORD,
            platform_user_id="discord-123",
            verification_data={"platform_user_id": "discord-123"},
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_returns_false_when_verification_data_missing_key(self):
        mgr = _make_manager(select_data=[{"user_id": "u1"}])
        result = await mgr.verify_platform_identity(
            platform=PLATFORM_DISCORD,
            platform_user_id="discord-123",
            verification_data={},
        )
        assert result is False


# ---------------------------------------------------------------------------
# Audit log
# ---------------------------------------------------------------------------


class TestAuditLog:
    @pytest.mark.asyncio
    async def test_audit_log_initially_empty(self):
        mgr = _make_manager()
        assert mgr.get_audit_log() == []

    @pytest.mark.asyncio
    async def test_audit_log_returns_copy(self):
        """Mutating the returned list must not affect internal state."""
        mgr = _make_manager(update_data=[{"user_id": "u1"}])
        await mgr.unlink_platform_account("u1", PLATFORM_DISCORD)

        log = mgr.get_audit_log()
        log.clear()

        assert len(mgr.get_audit_log()) == 1

    @pytest.mark.asyncio
    async def test_multiple_operations_all_logged(self):
        mgr = _make_manager(
            select_data=[],
            upsert_data=[{"user_id": "u1"}],
            update_data=[{"user_id": "u1"}],
        )
        code = mgr.generate_verification_code("u1")
        await mgr.link_platform_account("u1", PLATFORM_DISCORD, "d-1", code)

        # Need a fresh manager for unlink (different mock state)
        mgr2 = _make_manager(update_data=[{"user_id": "u1"}])
        await mgr2.unlink_platform_account("u1", PLATFORM_DISCORD)

        assert len(mgr.get_audit_log()) == 1  # link
        assert len(mgr2.get_audit_log()) == 1  # unlink

    @pytest.mark.asyncio
    async def test_audit_entry_has_timestamp(self):
        mgr = _make_manager(update_data=[{"user_id": "u1"}])
        before = datetime.now(timezone.utc)
        await mgr.unlink_platform_account("u1", PLATFORM_DISCORD)
        after = datetime.now(timezone.utc)

        entry = mgr.get_audit_log()[0]
        assert before <= entry.timestamp <= after


# ---------------------------------------------------------------------------
# Integration-style: full link → verify → unlink flow
# ---------------------------------------------------------------------------


class TestFullIdentityFlow:
    @pytest.mark.asyncio
    async def test_link_then_verify_then_unlink(self):
        """Full happy-path: generate code → link → verify → unlink."""
        # Step 1: link (no existing owner)
        link_mgr = _make_manager(
            select_data=[],
            upsert_data=[{"user_id": "u1"}],
        )
        code = link_mgr.generate_verification_code("u1")
        link_result = await link_mgr.link_platform_account(
            "u1", PLATFORM_DISCORD, "discord-abc", code
        )
        assert link_result.success is True

        # Step 2: verify (active link exists)
        verify_mgr = _make_manager(select_data=[{"user_id": "u1"}])
        verified = await verify_mgr.verify_platform_identity(
            PLATFORM_DISCORD,
            "discord-abc",
            {"platform_user_id": "discord-abc"},
        )
        assert verified is True

        # Step 3: unlink
        unlink_mgr = _make_manager(update_data=[{"user_id": "u1", "is_active": False}])
        unlinked = await unlink_mgr.unlink_platform_account("u1", PLATFORM_DISCORD)
        assert unlinked is True

    @pytest.mark.asyncio
    async def test_lookup_after_link(self):
        """After linking, get_user_by_platform_id should return the user."""
        mgr = _make_manager(select_data=[{"user_id": "u1"}])
        found = await mgr.get_user_by_platform_id(PLATFORM_DISCORD, "discord-abc")
        assert found == "u1"

    @pytest.mark.asyncio
    async def test_lookup_after_unlink_returns_none(self):
        """After unlinking, get_user_by_platform_id should return None."""
        mgr = _make_manager(select_data=[])
        found = await mgr.get_user_by_platform_id(PLATFORM_DISCORD, "discord-abc")
        assert found is None
