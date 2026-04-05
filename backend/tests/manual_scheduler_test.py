"""
Manual test script to verify scheduler configuration.

This script demonstrates the configurable scheduler functionality.
Run this script to see the scheduler configuration in action.

Usage:
    python tests/manual_scheduler_test.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.tasks.scheduler import setup_scheduler, scheduler
from app.core.config import settings


def test_default_configuration():
    """Test scheduler with default configuration."""
    print("\n" + "="*60)
    print("Testing Default Configuration")
    print("="*60)
    
    print(f"SCHEDULER_CRON: {settings.scheduler_cron}")
    print(f"SCHEDULER_TIMEZONE: {settings.scheduler_timezone}")
    print(f"TIMEZONE (fallback): {settings.timezone}")
    
    try:
        scheduler.remove_all_jobs()
        setup_scheduler()
        
        jobs = scheduler.get_jobs()
        print(f"\n✓ Scheduler initialized successfully")
        print(f"  Jobs registered: {len(jobs)}")
        
        for job in jobs:
            print(f"  - Job ID: {job.id}")
            print(f"    Name: {job.name}")
            print(f"    Trigger: {job.trigger}")
        
        return True
    except Exception as e:
        print(f"\n✗ Scheduler initialization failed: {e}")
        return False


def test_custom_configuration():
    """Test scheduler with custom CRON expression."""
    print("\n" + "="*60)
    print("Testing Custom Configuration")
    print("="*60)
    
    # Temporarily override settings
    original_cron = settings.scheduler_cron
    original_tz = settings.scheduler_timezone
    
    try:
        # Set custom values
        settings.scheduler_cron = "0 0 * * *"  # Daily at midnight
        settings.scheduler_timezone = "UTC"
        
        print(f"SCHEDULER_CRON: {settings.scheduler_cron}")
        print(f"SCHEDULER_TIMEZONE: {settings.scheduler_timezone}")
        
        scheduler.remove_all_jobs()
        setup_scheduler()
        
        jobs = scheduler.get_jobs()
        print(f"\n✓ Scheduler initialized with custom config")
        print(f"  Jobs registered: {len(jobs)}")
        
        for job in jobs:
            print(f"  - Job ID: {job.id}")
            print(f"    Name: {job.name}")
            print(f"    Trigger: {job.trigger}")
        
        return True
    except Exception as e:
        print(f"\n✗ Scheduler initialization failed: {e}")
        return False
    finally:
        # Restore original values
        settings.scheduler_cron = original_cron
        settings.scheduler_timezone = original_tz


def test_invalid_configuration():
    """Test scheduler with invalid CRON expression."""
    print("\n" + "="*60)
    print("Testing Invalid Configuration (Expected to Fail)")
    print("="*60)
    
    original_cron = settings.scheduler_cron
    
    try:
        # Set invalid CRON
        settings.scheduler_cron = "invalid_cron_expression"
        
        print(f"SCHEDULER_CRON: {settings.scheduler_cron}")
        
        scheduler.remove_all_jobs()
        setup_scheduler()
        
        print(f"\n✗ Scheduler should have raised ValueError but didn't!")
        return False
    except ValueError as e:
        print(f"\n✓ Scheduler correctly rejected invalid CRON")
        print(f"  Error: {e}")
        return True
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        return False
    finally:
        # Restore original value
        settings.scheduler_cron = original_cron


def main():
    """Run all manual tests."""
    print("\n" + "="*60)
    print("Scheduler Configuration Manual Tests")
    print("="*60)
    
    results = []
    
    # Test 1: Default configuration
    results.append(("Default Configuration", test_default_configuration()))
    
    # Test 2: Custom configuration
    results.append(("Custom Configuration", test_custom_configuration()))
    
    # Test 3: Invalid configuration
    results.append(("Invalid Configuration", test_invalid_configuration()))
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status}: {test_name}")
    
    all_passed = all(passed for _, passed in results)
    
    print("\n" + "="*60)
    if all_passed:
        print("All tests passed! ✓")
    else:
        print("Some tests failed! ✗")
    print("="*60 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
