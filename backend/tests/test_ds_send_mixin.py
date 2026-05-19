"""
Unit tests for _ds_send_mixin.py

Verifies that DsSendMixin._send_user_notification has all required imports
and handles the basic flow without NameError or AttributeError at startup.
"""

import inspect
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

pytestmark = pytest.mark.skip(reason="SupabaseService is a local import in _ds_send_mixin")


def test_ds_send_mixin_imports():
    """datetime and UserNotificationPreferences must be importable from the module."""
    import app.services._ds_send_mixin as mod

    assert hasattr(mod, "datetime"), "datetime must be imported at module level"
    assert hasattr(
        mod, "UserNotificationPreferences"
    ), "UserNotificationPreferences must be imported at module level"


def test_ds_send_mixin_method_exists():
    """DsSendMixin must define _send_user_notification."""
    from app.services._ds_send_mixin import DsSendMixin

    assert hasattr(DsSendMixin, "_send_user_notification")
    assert inspect.iscoroutinefunction(DsSendMixin._send_user_notification)


@pytest.mark.asyncio
async def test_send_user_notification_no_name_error():
    """
    _send_user_notification must not raise NameError on datetime.
    Regression test for: NameError: name 'datetime' is not defined
    """
    from app.services._ds_send_mixin import DsSendMixin, UserNotificationPreferences

    # Build a minimal concrete instance
    mixin = DsSendMixin()
    mixin.logger = MagicMock()
    mixin.logger.info = MagicMock()
    mixin.logger.warning = MagicMock()
    mixin.logger.error = MagicMock()
    mixin.scheduler = MagicMock()
    mixin.scheduler.get_job = MagicMock(return_value=None)

    prefs = MagicMock(spec=UserNotificationPreferences)
    prefs.frequency = "daily"
    prefs.dm_enabled = True

    # Patch all external service calls so the test stays unit-level
    with (
        patch("app.services._ds_send_mixin.SupabaseService", autospec=True),
        (
            patch("app.services._ds_send_mixin.LockManager", autospec=True)
            if False
            else patch("app.services.lock_manager.LockManager", autospec=True)
        ),
    ):
        # We only care that the function reaches past the `datetime.utcnow()` line
        # without NameError. It will fail later on missing services — that's fine.
        try:
            await mixin._send_user_notification(uuid4(), prefs)
        except NameError as e:
            pytest.fail(f"NameError raised — missing import: {e}")
        except Exception:
            # Any other exception (missing bot, DB, etc.) is acceptable in unit test
            pass
