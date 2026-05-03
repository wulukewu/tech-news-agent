#!/bin/bash
# Apply migration 018: Add source tracking to reading_list

echo "📦 Applying migration 018: Add source tracking to reading_list"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found"
    exit 1
fi

# Load environment variables
source .env

# Check if SUPABASE_URL and SUPABASE_KEY are set
if [ -z "$SUPABASE_URL" ] || [ -z "$SUPABASE_KEY" ]; then
    echo "❌ Error: SUPABASE_URL or SUPABASE_KEY not set in .env"
    exit 1
fi

echo "🔗 Connecting to Supabase..."
echo "   URL: $SUPABASE_URL"
echo ""

# Read migration file
MIGRATION_FILE="backend/scripts/migrations/018_add_reading_list_source.sql"

if [ ! -f "$MIGRATION_FILE" ]; then
    echo "❌ Error: Migration file not found: $MIGRATION_FILE"
    exit 1
fi

echo "📄 Reading migration file: $MIGRATION_FILE"
echo ""

# Execute migration using psql (requires psql to be installed)
# Extract database connection details from SUPABASE_URL
# Format: postgresql://postgres:[PASSWORD]@[HOST]:[PORT]/postgres

# Alternative: Use Supabase REST API
echo "⚠️  Please run this SQL in your Supabase SQL Editor:"
echo ""
cat "$MIGRATION_FILE"
echo ""
echo "📝 Or copy the file content from: $MIGRATION_FILE"
echo ""
echo "✅ After running the SQL, restart the backend:"
echo "   docker-compose restart backend"
