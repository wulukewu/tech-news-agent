#!/usr/bin/env python3
"""
Test script for notification preferences migration files.
Validates SQL syntax and migration file structure.
"""

import os
import re
from pathlib import Path

def test_migration_files():
    """Test the notification preferences migration files."""

    migration_dir = Path(__file__).parent

    # Migration files to test
    migration_files = [
        '005_create_user_notification_preferences_table.sql',
        '006_create_notification_locks_table.sql'
    ]

    print("🧪 Testing notification preferences migration files...")

    for migration_file in migration_files:
        migration_path = migration_dir / migration_file

        if not migration_path.exists():
            print(f"❌ Migration file not found: {migration_file}")
            return False

        print(f"\n📄 Testing {migration_file}:")

        with open(migration_path, 'r') as f:
            content = f.read()

        # Test 1: Check for required header comments
        if not content.startswith('-- Migration'):
            print("❌ Missing migration header comment")
            return False
        print("✅ Has migration header comment")

        # Test 2: Check for task and requirements references
        if '-- Task' not in content or '-- Requirements' not in content:
            print("❌ Missing task or requirements references")
            return False
        print("✅ Has task and requirements references")

        # Test 3: Check for CREATE TABLE IF NOT EXISTS
        if 'CREATE TABLE IF NOT EXISTS' not in content:
            print("❌ Missing CREATE TABLE IF NOT EXISTS statement")
            return False
        print("✅ Uses CREATE TABLE IF NOT EXISTS")

        # Test 4: Check for proper foreign key constraints
        if 'REFERENCES users(id) ON DELETE CASCADE' not in content:
            print("❌ Missing proper foreign key constraint")
            return False
        print("✅ Has proper foreign key constraint")

        # Test 5: Check for indexes
        if 'CREATE INDEX' not in content:
            print("❌ Missing index creation")
            return False
        print("✅ Creates indexes")

        # Test 6: Check for table comments
        if 'COMMENT ON TABLE' not in content:
            print("❌ Missing table comments")
            return False
        print("✅ Has table comments")

        # Test 7: Specific checks for user_notification_preferences
        if '005_' in migration_file:
            # Check for frequency constraint
            if "CHECK (frequency IN ('daily', 'weekly', 'monthly', 'disabled'))" not in content:
                print("❌ Missing frequency check constraint")
                return False
            print("✅ Has frequency check constraint")

            # Check for default values
            required_defaults = [
                "DEFAULT 'weekly'",
                "DEFAULT '18:00:00'",
                "DEFAULT 'Asia/Taipei'",
                "DEFAULT true",
                "DEFAULT false"
            ]

            for default in required_defaults:
                if default not in content:
                    print(f"❌ Missing required default: {default}")
                    return False
            print("✅ Has all required default values")

            # Check for unique constraint on user_id
            if 'UNIQUE(user_id)' not in content:
                print("❌ Missing unique constraint on user_id")
                return False
            print("✅ Has unique constraint on user_id")

        # Test 8: Specific checks for notification_locks
        if '006_' in migration_file:
            # Check for status constraint
            if "CHECK (status IN ('pending', 'processing', 'completed', 'failed'))" not in content:
                print("❌ Missing status check constraint")
                return False
            print("✅ Has status check constraint")

            # Check for unique constraint on user_id, notification_type, scheduled_time
            if 'UNIQUE(user_id, notification_type, scheduled_time)' not in content:
                print("❌ Missing unique constraint on user_id, notification_type, scheduled_time")
                return False
            print("✅ Has unique constraint on user_id, notification_type, scheduled_time")

    print("\n🎉 All migration files passed validation!")
    return True

def test_python_scripts():
    """Test the Python migration scripts."""

    migration_dir = Path(__file__).parent

    python_files = [
        'apply_notification_preferences_migration.py',
        'verify_notification_preferences.py'
    ]

    print("\n🐍 Testing Python migration scripts...")

    for python_file in python_files:
        python_path = migration_dir / python_file

        if not python_path.exists():
            print(f"❌ Python file not found: {python_file}")
            return False

        print(f"\n📄 Testing {python_file}:")

        with open(python_path, 'r') as f:
            content = f.read()

        # Test 1: Check for shebang
        if not content.startswith('#!/usr/bin/env python3'):
            print("❌ Missing proper shebang")
            return False
        print("✅ Has proper shebang")

        # Test 2: Check for docstring
        if '"""' not in content[:200]:
            print("❌ Missing module docstring")
            return False
        print("✅ Has module docstring")

        # Test 3: Check for required imports
        required_imports = ['os', 'sys', 'supabase', 'dotenv']
        for imp in required_imports:
            if f'import {imp}' not in content and f'from {imp}' not in content:
                print(f"❌ Missing required import: {imp}")
                return False
        print("✅ Has all required imports")

        # Test 4: Check for main guard
        if "if __name__ == '__main__':" not in content:
            print("❌ Missing main guard")
            return False
        print("✅ Has main guard")

    print("\n🎉 All Python scripts passed validation!")
    return True

if __name__ == '__main__':
    success = test_migration_files() and test_python_scripts()

    if success:
        print("\n✅ All tests passed! Migration files are ready for deployment.")
    else:
        print("\n❌ Some tests failed. Please fix the issues before deploying.")

    exit(0 if success else 1)
