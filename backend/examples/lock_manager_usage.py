"""
LockManager Usage Example

This example demonstrates how to use the LockManager for atomic notification locking
to prevent duplicate notifications in multi-instance environments.

Requirements: 10.1, 10.2, 10.3, 10.4, 10.5
"""

import asyncio
from datetime import datetime
from uuid import uuid4

from app.services.lock_manager import LockManager
from app.services.supabase_service import SupabaseService


async def example_notification_with_locking():
    """
    Example of how to use LockManager to prevent duplicate notifications.

    This example shows the typical workflow:
    1. Attempt to acquire a lock before sending notification
    2. Send notification if lock is acquired
    3. Release lock after completion
    4. Handle cases where lock already exists (duplicate prevention)
    """
    # Initialize services
    supabase_service = SupabaseService()
    lock_manager = LockManager(supabase_service.client)

    # Example notification parameters
    user_id = uuid4()
    notification_type = "weekly_digest"
    scheduled_time = datetime.utcnow()

    print(f"Attempting to send {notification_type} notification to user {user_id}")

    try:
        # Step 1: Attempt to acquire notification lock
        lock = await lock_manager.acquire_notification_lock(
            user_id=user_id,
            notification_type=notification_type,
            scheduled_time=scheduled_time,
            ttl_minutes=30,  # Lock expires in 30 minutes
        )

        if lock is None:
            print(
                "❌ Lock already exists - notification already being processed by another instance"
            )
            return False

        print(f"✅ Lock acquired: {lock.id}")

        try:
            # Step 2: Send the actual notification
            print("📧 Sending notification...")

            # Simulate notification sending
            await asyncio.sleep(1)  # Simulate API call delay

            # In real implementation, this would be:
            # success = await notification_service.send_notification(user_id, notification_type)
            success = True  # Simulate successful sending

            if success:
                print("✅ Notification sent successfully")

                # Step 3: Release lock as completed
                await lock_manager.release_lock(lock.id, "completed")
                print("🔓 Lock released as completed")

                return True
            else:
                print("❌ Notification failed to send")

                # Release lock as failed
                await lock_manager.release_lock(lock.id, "failed")
                print("🔓 Lock released as failed")

                return False

        except Exception as e:
            print(f"❌ Error during notification sending: {e}")

            # Release lock as failed
            await lock_manager.release_lock(lock.id, "failed")
            print("🔓 Lock released as failed due to exception")

            return False

    except Exception as e:
        print(f"❌ Error acquiring lock: {e}")
        return False


async def example_concurrent_notifications():
    """
    Example demonstrating how LockManager prevents duplicate notifications
    when multiple instances try to send the same notification concurrently.
    """
    print("\n" + "=" * 60)
    print("CONCURRENT NOTIFICATION EXAMPLE")
    print("=" * 60)

    # Initialize services
    supabase_service = SupabaseService()
    lock_manager1 = LockManager(supabase_service.client)
    lock_manager2 = LockManager(supabase_service.client)

    # Override instance IDs to simulate different instances
    lock_manager1.instance_id = "instance_1"
    lock_manager2.instance_id = "instance_2"

    # Same notification parameters for both instances
    user_id = uuid4()
    notification_type = "weekly_digest"
    scheduled_time = datetime.utcnow()

    async def send_notification_instance(instance_name, lock_manager):
        """Simulate notification sending from a specific instance."""
        print(f"[{instance_name}] Attempting to acquire lock...")

        lock = await lock_manager.acquire_notification_lock(
            user_id=user_id,
            notification_type=notification_type,
            scheduled_time=scheduled_time,
        )

        if lock is None:
            print(f"[{instance_name}] ❌ Lock already exists - skipping duplicate notification")
            return False

        print(f"[{instance_name}] ✅ Lock acquired: {lock.id}")

        # Simulate notification sending
        await asyncio.sleep(0.5)
        print(f"[{instance_name}] 📧 Notification sent")

        # Release lock
        await lock_manager.release_lock(lock.id, "completed")
        print(f"[{instance_name}] 🔓 Lock released")

        return True

    # Run both instances concurrently
    results = await asyncio.gather(
        send_notification_instance("Instance 1", lock_manager1),
        send_notification_instance("Instance 2", lock_manager2),
        return_exceptions=True,
    )

    successful_sends = sum(1 for result in results if result is True)
    print(f"\n📊 Result: {successful_sends} out of 2 instances successfully sent notification")
    print(
        "✅ Duplicate prevention working correctly!"
        if successful_sends == 1
        else "❌ Something went wrong"
    )


async def example_lock_cleanup():
    """
    Example demonstrating lock cleanup functionality.
    """
    print("\n" + "=" * 60)
    print("LOCK CLEANUP EXAMPLE")
    print("=" * 60)

    # Initialize services
    supabase_service = SupabaseService()
    lock_manager = LockManager(supabase_service.client)

    # Create a lock with very short TTL
    user_id = uuid4()
    notification_type = "test_cleanup"
    scheduled_time = datetime.utcnow()

    print("Creating lock with 0 minute TTL (expires immediately)...")
    lock = await lock_manager.acquire_notification_lock(
        user_id=user_id,
        notification_type=notification_type,
        scheduled_time=scheduled_time,
        ttl_minutes=0,  # Expires immediately
    )

    if lock:
        print(f"✅ Lock created: {lock.id}")

        # Wait a moment to ensure expiration
        await asyncio.sleep(0.1)

        # Run cleanup
        print("Running cleanup of expired locks...")
        cleaned_count = await lock_manager.cleanup_expired_locks()
        print(f"🧹 Cleaned up {cleaned_count} expired locks")

        # Verify lock was cleaned up
        lock_status = await lock_manager.get_lock_status(
            user_id=user_id,
            notification_type=notification_type,
            scheduled_time=scheduled_time,
        )

        if lock_status is None:
            print("✅ Lock successfully cleaned up")
        else:
            print("❌ Lock still exists after cleanup")
    else:
        print("❌ Failed to create lock")


async def example_lock_statistics():
    """
    Example demonstrating lock statistics functionality.
    """
    print("\n" + "=" * 60)
    print("LOCK STATISTICS EXAMPLE")
    print("=" * 60)

    # Initialize services
    supabase_service = SupabaseService()
    lock_manager = LockManager(supabase_service.client)

    # Get current statistics
    stats = await lock_manager.get_lock_statistics()

    print("📊 Current Lock Statistics:")
    print(f"   Total locks: {stats['total_locks']}")
    print(f"   Active locks: {stats['active_locks']}")
    print(f"   Expired locks: {stats['expired_locks']}")
    print(f"   Instance ID: {stats['instance_id']}")

    if stats["by_status"]:
        print("   By status:")
        for status, count in stats["by_status"].items():
            print(f"     {status}: {count}")
    else:
        print("   No locks found")


async def main():
    """
    Main function demonstrating various LockManager usage patterns.
    """
    print("🔒 LockManager Usage Examples")
    print("=" * 60)

    try:
        # Example 1: Basic notification with locking
        print("1. BASIC NOTIFICATION WITH LOCKING")
        print("-" * 40)
        success = await example_notification_with_locking()
        print(f"Result: {'Success' if success else 'Failed'}")

        # Example 2: Concurrent notifications (duplicate prevention)
        await example_concurrent_notifications()

        # Example 3: Lock cleanup
        await example_lock_cleanup()

        # Example 4: Lock statistics
        await example_lock_statistics()

        print("\n" + "=" * 60)
        print("✅ All examples completed successfully!")

    except Exception as e:
        print(f"❌ Error running examples: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    # Note: This example requires the notification_locks table to exist
    # Apply migration 006_create_notification_locks_table.sql first

    print("⚠️  Note: This example requires the notification_locks table to exist.")
    print("   Apply migration 006_create_notification_locks_table.sql first.\n")

    asyncio.run(main())
