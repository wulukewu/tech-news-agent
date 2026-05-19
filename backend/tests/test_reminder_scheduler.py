"""測試智能提醒排程任務"""

import pytest

pytestmark = pytest.mark.skip(reason="intelligent_reminder_job removed from scheduler")


@pytest.mark.asyncio
async def test_scheduler_job():
    pass
