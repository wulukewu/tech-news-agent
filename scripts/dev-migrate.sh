#!/bin/bash

# Tech News Agent - Database Migration Script
# This script handles database migrations and seeding

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "\n${BLUE}=== $1 ===${NC}\n"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  init               Initialize database schema"
    echo "  seed               Seed database with default data"
    echo "  reset              Reset database (drop and recreate)"
    echo "  status             Check database connection and schema"
    echo "  backup             Create database backup"
    echo "  restore [FILE]     Restore database from backup"
    echo ""
    echo "Options:"
    echo "  -f, --force        Force operation without confirmation"
    echo "  -v, --verbose      Verbose output"
    echo "  -h, --help         Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 init            # Initialize database schema"
    echo "  $0 seed            # Seed with default feeds"
    echo "  $0 reset -f        # Reset database without confirmation"
    echo "  $0 status          # Check database status"
}

# Default options
FORCE=false
VERBOSE=false
COMMAND=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        init|seed|reset|status|backup|restore)
            COMMAND=$1
            shift
            ;;
        -f|--force)
            FORCE=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            if [ "$COMMAND" = "restore" ] && [ -z "$RESTORE_FILE" ]; then
                RESTORE_FILE=$1
                shift
            else
                print_error "Unknown option: $1"
                show_usage
                exit 1
            fi
            ;;
    esac
done

# Check if command is provided
if [ -z "$COMMAND" ]; then
    print_error "No command provided"
    show_usage
    exit 1
fi

# Load environment variables
load_env() {
    if [ -f .env ]; then
        export $(grep -v '^#' .env | xargs)
        print_status "Loaded environment variables from .env"
    else
        print_error ".env file not found"
        exit 1
    fi
}

# Check database connection
check_connection() {
    print_status "Checking database connection..."

    if [ -z "$SUPABASE_URL" ] || [ -z "$SUPABASE_KEY" ]; then
        print_error "SUPABASE_URL and SUPABASE_KEY must be set in .env"
        exit 1
    fi

    # Try to connect using Python script
    python3 -c "
import os
from supabase import create_client, Client

try:
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    supabase: Client = create_client(url, key)

    # Test connection with a simple query
    result = supabase.table('users').select('count').execute()
    print('✅ Database connection successful')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    exit(1)
" 2>/dev/null || {
        print_error "Failed to connect to database. Please check your SUPABASE_URL and SUPABASE_KEY"
        exit 1
    }

    print_success "Database connection verified"
}

# Initialize database schema
init_database() {
    print_header "Initializing Database Schema"

    if [ ! -f "backend/scripts/init_supabase.sql" ]; then
        print_error "Database initialization script not found: backend/scripts/init_supabase.sql"
        exit 1
    fi

    print_status "Database schema initialization requires manual execution in Supabase SQL Editor"
    print_status "Please follow these steps:"
    echo ""
    echo "1. Open Supabase Dashboard: $SUPABASE_URL"
    echo "2. Go to SQL Editor"
    echo "3. Copy and paste the contents of backend/scripts/init_supabase.sql"
    echo "4. Execute the SQL script"
    echo ""
    print_warning "This script cannot automatically execute SQL in Supabase"
    print_status "After running the SQL script, you can verify with: $0 status"
}

# Seed database with default data
seed_database() {
    print_header "Seeding Database"

    check_connection

    # Run seed scripts
    if [ -f "backend/scripts/seed_feeds.py" ]; then
        print_status "Seeding default feeds..."
        cd backend
        python3 scripts/seed_feeds.py
        cd ..
        print_success "Default feeds seeded"
    fi

    if [ -f "backend/scripts/seed_recommended_feeds.py" ]; then
        print_status "Seeding recommended feeds..."
        cd backend
        python3 scripts/seed_recommended_feeds.py
        cd ..
        print_success "Recommended feeds seeded"
    fi

    print_success "Database seeding completed"
}

# Reset database
reset_database() {
    print_header "Resetting Database"

    if [ "$FORCE" != true ]; then
        echo -e "${YELLOW}WARNING: This will delete all data in the database!${NC}"
        echo -n "Are you sure you want to continue? (y/N): "
        read -r response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            print_status "Database reset cancelled"
            exit 0
        fi
    fi

    print_status "Database reset requires manual execution in Supabase"
    print_warning "Please manually drop and recreate tables in Supabase SQL Editor"
    print_status "Then run: $0 init && $0 seed"
}

# Check database status
check_status() {
    print_header "Database Status"

    check_connection

    # Check if tables exist
    print_status "Checking database schema..."

    python3 -c "
import os
from supabase import create_client, Client

try:
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    supabase: Client = create_client(url, key)

    # Check for main tables
    tables = ['users', 'feeds', 'articles', 'user_subscriptions', 'reading_list']

    for table in tables:
        try:
            result = supabase.table(table).select('count').limit(1).execute()
            print(f'✅ Table {table} exists')
        except Exception as e:
            print(f'❌ Table {table} missing or inaccessible')

    # Get some basic stats
    try:
        users_count = len(supabase.table('users').select('id').execute().data)
        feeds_count = len(supabase.table('feeds').select('id').execute().data)
        articles_count = len(supabase.table('articles').select('id').execute().data)

        print(f'📊 Users: {users_count}')
        print(f'📊 Feeds: {feeds_count}')
        print(f'📊 Articles: {articles_count}')

    except Exception as e:
        print(f'⚠️  Could not fetch statistics: {e}')

except Exception as e:
    print(f'❌ Database status check failed: {e}')
    exit(1)
"

    print_success "Database status check completed"
}

# Create database backup
backup_database() {
    print_header "Creating Database Backup"

    print_warning "Database backup requires manual export from Supabase Dashboard"
    print_status "Please follow these steps:"
    echo ""
    echo "1. Open Supabase Dashboard: $SUPABASE_URL"
    echo "2. Go to Settings > Database"
    echo "3. Use the backup/export functionality"
    echo ""
    print_status "For automated backups, consider using Supabase CLI or pg_dump with connection string"
}

# Restore database from backup
restore_database() {
    print_header "Restoring Database"

    if [ -z "$RESTORE_FILE" ]; then
        print_error "Restore file not specified"
        show_usage
        exit 1
    fi

    if [ ! -f "$RESTORE_FILE" ]; then
        print_error "Restore file not found: $RESTORE_FILE"
        exit 1
    fi

    print_warning "Database restore requires manual import in Supabase Dashboard"
    print_status "Please follow these steps:"
    echo ""
    echo "1. Open Supabase Dashboard: $SUPABASE_URL"
    echo "2. Go to SQL Editor"
    echo "3. Import and execute: $RESTORE_FILE"
    echo ""
}

# Main execution
main() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║              Tech News Agent - Database Migration           ║"
    echo "║                   Database management tool                  ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    load_env

    case $COMMAND in
        init)
            init_database
            ;;
        seed)
            seed_database
            ;;
        reset)
            reset_database
            ;;
        status)
            check_status
            ;;
        backup)
            backup_database
            ;;
        restore)
            restore_database
            ;;
        *)
            print_error "Unknown command: $COMMAND"
            show_usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
