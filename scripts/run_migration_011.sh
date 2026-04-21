#!/bin/bash

# Script to display migration 011 SQL for manual execution in Supabase
# This migration creates the dm_sent_articles table to track sent notifications

echo "=========================================="
echo "Migration 011: Create dm_sent_articles table"
echo "=========================================="
echo ""
echo "Please copy and paste the following SQL into your Supabase SQL Editor:"
echo ""
echo "----------------------------------------"
cat scripts/migrations/011_create_dm_sent_articles_table.sql
echo "----------------------------------------"
echo ""
echo "After running the SQL in Supabase, restart your backend service:"
echo "  docker-compose restart backend"
echo ""
echo "Then test the notification to verify:"
echo "  1. No duplicate articles"
echo "  2. Improved format with summaries"
echo "  3. Publish time displayed"
echo ""
