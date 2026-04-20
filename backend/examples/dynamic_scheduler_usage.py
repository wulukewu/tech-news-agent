"""
Dynamic Scheduler Usage Example

This example demonstrates how to use the DynamicScheduler class to manage
individual user notification jobs based on their preferences.

Requirements: 5.1, 5.2, 5.4, 5.5
"""

import asyncio
from datetime import time
from uuid import uuid4

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.repositories.user_notification_preferences import UserNotificationPreferences
from app.services.dynamic_scheduler import DynamicScheduler


async def main():
    """Example usage of DynamicScheduler."""
    print("Dynamic Scheduler Usage Example")
    print("=" * 40)

    # Initialize scheduler
    scheduler = AsyncIOScheduler()
    scheduler.start()

    # Initialize dynamic scheduler
    dynamic_scheduler = DynamicScheduler(scheduler)

    # Create sample user preferences
    user_id = uuid4()
    preferences = UserNotificationPreferences(
        id=uuid4(),
        user_id=user_id,
        frequency="weekly",
        notification_time=time(18, 0),  # 6 PM
        timezone="Asia/Taipei",
        dm_enabled=True,
        email_enabled=False,
    )

    print(f"User ID: {user_id}")
    print(
        f"Preferences: {preferences.frequency} at {preferences.notification_time} ({preferences.timezone})"
    )
    print()

    # Example 1: Schedule a notification
    print("1. Scheduling user notification...")
    await dynamic_scheduler.schedule_user_notification(user_id, preferences)

    # Check job info
    job_info = await dynamic_scheduler.get_user_job_info(user_id)
    if job_info:
        print(f"   Job scheduled: {job_info['name']}")
        print(f"   Next run time: {job_info['next_run_time']}")
    else:
        print("   No job found (notifications may be disabled)")
    print()

    # Example 2: Get scheduler stats
    print("2. Scheduler statistics:")
    stats = await dynamic_scheduler.get_scheduler_stats()
    print(f"   Total jobs: {stats['total_jobs']}")
    print(f"   User notification jobs: {stats['user_notification_jobs']}")
    print(f"   Scheduler running: {stats['scheduler_running']}")
    print()

    # Example 3: Update preferences (reschedule)
    print("3. Updating preferences (daily notifications at 9 AM)...")
    preferences.frequency = "daily"
    preferences.notification_time = time(9, 0)

    await dynamic_scheduler.reschedule_user_notification(user_id, preferences)

    # Check updated job info
    job_info = await dynamic_scheduler.get_user_job_info(user_id)
    if job_info:
        print(f"   Job rescheduled: {job_info['name']}")
        print(f"   Next run time: {job_info['next_run_time']}")
    print()

    # Example 4: Cancel notification
    print("4. Canceling user notification...")
    await dynamic_scheduler.cancel_user_notification(user_id)

    # Verify cancellation
    job_info = await dynamic_scheduler.get_user_job_info(user_id)
    if job_info:
        print(f"   Job still exists: {job_info['name']}")
    else:
        print("   Job successfully canceled")
    print()

    # Example 5: Cleanup expired jobs
    print("5. Cleaning up expired jobs...")
    cleaned_count = await dynamic_scheduler.cleanup_expired_jobs()
    print(f"   Cleaned up {cleaned_count} expired jobs")
    print()

    # Final stats
    print("Final scheduler statistics:")
    stats = await dynamic_scheduler.get_scheduler_stats()
    print(f"   Total jobs: {stats['total_jobs']}")
    print(f"   User notification jobs: {stats['user_notification_jobs']}")

    # Shutdown scheduler
    scheduler.shutdown()
    print("\nScheduler shutdown complete.")


if __name__ == "__main__":
    asyncio.run(main())
