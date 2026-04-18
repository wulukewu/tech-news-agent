#!/bin/bash

# CI Verification Script
# Run this before pushing to verify all CI checks will pass

set -e  # Exit on error

echo "🔍 Starting CI verification..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track failures
FAILURES=0

# Function to run a check
run_check() {
    local name=$1
    local command=$2
    local dir=$3

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🔧 Running: $name"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    if [ -n "$dir" ]; then
        cd "$dir"
    fi

    if eval "$command"; then
        echo -e "${GREEN}✅ $name passed${NC}"
    else
        echo -e "${RED}❌ $name failed${NC}"
        FAILURES=$((FAILURES + 1))
    fi

    if [ -n "$dir" ]; then
        cd - > /dev/null
    fi

    echo ""
}

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

cd "$PROJECT_ROOT"

echo "📁 Project root: $PROJECT_ROOT"
echo ""

# Backend checks
echo "═══════════════════════════════════════════"
echo "🐍 BACKEND CHECKS"
echo "═══════════════════════════════════════════"
echo ""

run_check "Backend: Black formatting" "black --check app/ tests/" "backend"
run_check "Backend: Ruff linting" "ruff check app/ tests/" "backend"
run_check "Backend: Type checking (mypy)" "mypy app/ --ignore-missing-imports --no-strict-optional --python-version=3.11" "backend"
run_check "Backend: Fast tests" "pytest tests/test_health_endpoint.py tests/test_config.py -v --tb=short" "backend"

# Frontend checks
echo "═══════════════════════════════════════════"
echo "⚛️  FRONTEND CHECKS"
echo "═══════════════════════════════════════════"
echo ""

run_check "Frontend: Prettier formatting" "npm run format:check" "frontend"
run_check "Frontend: ESLint" "npm run lint" "frontend"
run_check "Frontend: TypeScript type check" "npm run type-check" "frontend"
run_check "Frontend: Build" "npm run build" "frontend"

# Summary
echo "═══════════════════════════════════════════"
echo "📊 SUMMARY"
echo "═══════════════════════════════════════════"
echo ""

if [ $FAILURES -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed! Ready to push.${NC}"
    exit 0
else
    echo -e "${RED}❌ $FAILURES check(s) failed. Please fix before pushing.${NC}"
    exit 1
fi
