#!/bin/bash

# Show Intelligent Q&A Agent Database Migration Instructions
# This script provides instructions for manually applying the database schema migration

set -e  # Exit on any error

echo "🚀 Intelligent Q&A Agent Database Migration Setup"
echo "=================================================="

# Check if we're in the correct directory
if [ ! -f "backend/scripts/apply_intelligent_qa_migration.py" ]; then
    echo "❌ Error: Must run from project root directory"
    echo "Current directory: $(pwd)"
    exit 1
fi

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Warning: No virtual environment detected"
    echo "Consider activating your virtual environment first:"
    echo "  source venv/bin/activate"
    echo ""
fi

# Check required environment variables
if [ -z "$SUPABASE_URL" ] || [ -z "$SUPABASE_SERVICE_ROLE_KEY" ]; then
    echo "❌ Error: Missing required environment variables"
    echo "Please set the following variables:"
    echo "  - SUPABASE_URL"
    echo "  - SUPABASE_SERVICE_ROLE_KEY"
    echo ""
    echo "You can source them from your .env file:"
    echo "  source .env"
    exit 1
fi

echo "✓ Environment variables found"
echo "✓ Migration script found"
echo ""

# Show migration instructions
echo "📋 Showing migration instructions..."
python backend/scripts/apply_intelligent_qa_migration.py

migration_exit_code=$?

if [ $migration_exit_code -eq 0 ]; then
    echo ""
    echo "📝 Migration instructions displayed successfully!"
    echo "=================================================="
    echo ""
    echo "IMPORTANT: You must manually execute the SQL in Supabase Dashboard"
    echo ""
    echo "After executing the SQL, run the verification:"
    echo "  python backend/scripts/verify_intelligent_qa_schema.py"
    echo ""
else
    echo ""
    echo "❌ Failed to show migration instructions with exit code: $migration_exit_code"
    echo "=================================================="
    echo "Please check the error messages above and try again."
    echo ""
    exit $migration_exit_code
fi
