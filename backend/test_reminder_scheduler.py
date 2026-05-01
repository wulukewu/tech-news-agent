"""測試智能提醒排程任務"""
import asyncio
import sys

sys.path.insert(0, "/app")

from app.tasks.scheduler import intelligent_reminder_job


async def test_scheduler_job():
    print("🧪 測試智能提醒排程任務\n")
    print("執行 intelligent_reminder_job()...\n")

    await intelligent_reminder_job()

    print("\n✅ 排程任務執行完成")


if __name__ == "__main__":
    asyncio.run(test_scheduler_job())
