#!/bin/bash

# Script to apply database migrations
# Usage: ./scripts/migrations/apply_migration.sh [migration_file]

set -e

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check if SUPABASE_URL is set
if [ -z "$SUPABASE_URL" ]; then
    echo "Error: SUPABASE_URL not set in .env file"
    exit 1
fi

# Extract database connection details from SUPABASE_URL
# Format: https://[project-ref].supabase.co
PROJECT_REF=$(echo $SUPABASE_URL | sed -E 's|https://([^.]+)\.supabase\.co|\1|')

# Construct PostgreSQL connection string
# Note: You'll need to get the database password from Supabase dashboard
# Settings > Database > Connection string > URI
if [ -z "$DATABASE_URL" ]; then
    echo "Error: DATABASE_URL not set in .env file"
    echo "Please add DATABASE_URL to your .env file"
    echo "Get it from: Supabase Dashboard > Settings > Database > Connection string"
    exit 1
fi

# Determine which migration to apply
if [ -z "$1" ]; then
    echo "Applying all migrations in order..."
    for migration in scripts/migrations/*.sql; do
        if [ -f "$migration" ]; then
            echo "Applying: $migration"
            psql "$DATABASE_URL" -f "$migration"
            echo "✓ Applied: $migration"
        fi
    done
else
    MIGRATION_FILE="$1"
    if [ ! -f "$MIGRATION_FILE" ]; then
        echo "Error: Migration file not found: $MIGRATION_FILE"
        exit 1
    fi
    echo "Applying: $MIGRATION_FILE"
    psql "$DATABASE_URL" -f "$MIGRATION_FILE"
    echo "✓ Applied: $MIGRATION_FILE"
fi

echo ""
echo "✓ Migration(s) applied successfully!"
