#!/bin/bash

# Migration 009: Add notification day fields
# This script provides instructions for applying the migration

echo "📋 Migration 009: Add notification day fields"
echo "=============================================="
echo ""
echo "This migration adds two new fields to user_notification_preferences:"
echo "  - notification_day_of_week (0-6, default: 5 = Friday)"
echo "  - notification_day_of_month (1-31, default: 1)"
echo ""
echo "📝 To apply this migration:"
echo ""
echo "Option 1: Using Supabase Dashboard (Recommended)"
echo "  1. Go to https://supabase.com/dashboard"
echo "  2. Select your project"
echo "  3. Go to SQL Editor"
echo "  4. Copy and paste the contents of:"
echo "     scripts/migrations/009_add_notification_day_fields.sql"
echo "  5. Click 'Run'"
echo ""
echo "Option 2: Using psql command line"
echo "  psql \"\$DATABASE_URL\" -f scripts/migrations/009_add_notification_day_fields.sql"
echo ""
echo "✅ After applying, run: python3 scripts/verify_migration_009.py"
echo ""
