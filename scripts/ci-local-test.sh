#!/bin/bash

# Local CI Test Script
# Run this before pushing to verify all CI checks will pass
# This script mirrors the exact checks that run in GitHub Actions

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Track results
BACKEND_PASSED=true
FRONTEND_PASSED=true

# Get project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║       Local CI Test - Pre-Push Check      ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo ""
echo "📁 Project: $PROJECT_ROOT"
echo ""

# ============================================
# Backend Tests
# ============================================
echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo -e "${BLUE}🐍 BACKEND CHECKS${NC}"
echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo ""

cd "$PROJECT_ROOT/backend"

# Set dummy env vars (same as CI)
export SUPABASE_URL="https://dummy.supabase.co"
export SUPABASE_KEY="dummy_supabase_key"
export DISCORD_TOKEN="dummy_discord_token"
export DISCORD_CHANNEL_ID="123456789012345678"
export GROQ_API_KEY="dummy_groq_api_key"
export TIMEZONE="Asia/Taipei"
export JWT_SECRET_KEY="dummy_jwt_secret_key_for_testing_only_32_chars"
export JWT_ALGORITHM="HS256"
export JWT_ACCESS_TOKEN_EXPIRE_MINUTES="30"

echo "1️⃣ Black formatting check..."
if black --check app/ tests/; then
    echo -e "${GREEN}✅ Black formatting passed${NC}"
else
    echo -e "${RED}❌ Black formatting failed${NC}"
    echo -e "${YELLOW}💡 Fix with: cd backend && black app/ tests/${NC}"
    BACKEND_PASSED=false
fi
echo ""

echo "2️⃣ Ruff linting..."
if ruff check app/ tests/; then
    echo -e "${GREEN}✅ Ruff linting passed${NC}"
else
    echo -e "${RED}❌ Ruff linting failed${NC}"
    echo -e "${YELLOW}💡 Fix with: cd backend && ruff check --fix app/ tests/${NC}"
    BACKEND_PASSED=false
fi
echo ""

echo "3️⃣ Type checking with mypy..."
if mypy app/ --ignore-missing-imports --no-strict-optional --python-version=3.11; then
    echo -e "${GREEN}✅ Type checking passed${NC}"
else
    echo -e "${RED}❌ Type checking failed${NC}"
    BACKEND_PASSED=false
fi
echo ""

echo "4️⃣ Running tests with coverage..."
if pytest -v --tb=short \
    --cov=app \
    --cov-report=term-missing \
    --cov-report=json:coverage.json \
    -n auto; then

    # Check coverage threshold
    COVERAGE=$(python3 -c "import json; print(json.load(open('coverage.json'))['totals']['percent_covered'])")
    THRESHOLD=70

    echo ""
    echo -e "📊 Coverage: ${COVERAGE}% (threshold: ${THRESHOLD}%)"

    if (( $(echo "$COVERAGE >= $THRESHOLD" | bc -l) )); then
        echo -e "${GREEN}✅ Tests and coverage passed${NC}"
    else
        echo -e "${RED}❌ Coverage below threshold${NC}"
        BACKEND_PASSED=false
    fi
else
    echo -e "${RED}❌ Tests failed${NC}"
    BACKEND_PASSED=false
fi
echo ""

# ============================================
# Frontend Tests
# ============================================
echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo -e "${BLUE}⚛️  FRONTEND CHECKS${NC}"
echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo ""

cd "$PROJECT_ROOT/frontend"

echo "1️⃣ Prettier formatting check..."
if npm run format:check; then
    echo -e "${GREEN}✅ Prettier formatting passed${NC}"
else
    echo -e "${RED}❌ Prettier formatting failed${NC}"
    echo -e "${YELLOW}💡 Fix with: cd frontend && npm run format${NC}"
    FRONTEND_PASSED=false
fi
echo ""

echo "2️⃣ ESLint..."
if npm run lint; then
    echo -e "${GREEN}✅ ESLint passed${NC}"
else
    echo -e "${RED}❌ ESLint failed${NC}"
    echo -e "${YELLOW}💡 Fix with: cd frontend && npm run lint:fix${NC}"
    FRONTEND_PASSED=false
fi
echo ""

echo "3️⃣ TypeScript type check..."
if npm run type-check; then
    echo -e "${GREEN}✅ Type checking passed${NC}"
else
    echo -e "${RED}❌ Type checking failed${NC}"
    FRONTEND_PASSED=false
fi
echo ""

echo "4️⃣ Running tests with coverage..."
if npm run test:coverage -- --passWithNoTests; then

    # Check coverage threshold if file exists
    if [ -f "coverage/coverage-summary.json" ]; then
        COVERAGE=$(node -e "const c = require('./coverage/coverage-summary.json'); console.log(c.total.lines.pct);")
        THRESHOLD=70

        echo ""
        echo -e "📊 Coverage: ${COVERAGE}% (threshold: ${THRESHOLD}%)"

        if (( $(echo "$COVERAGE >= $THRESHOLD" | bc -l) )); then
            echo -e "${GREEN}✅ Tests and coverage passed${NC}"
        else
            echo -e "${RED}❌ Coverage below threshold${NC}"
            FRONTEND_PASSED=false
        fi
    else
        echo -e "${GREEN}✅ Tests passed (no coverage data)${NC}"
    fi
else
    echo -e "${RED}❌ Tests failed${NC}"
    FRONTEND_PASSED=false
fi
echo ""

echo "5️⃣ Build verification..."
if npm run build; then
    echo -e "${GREEN}✅ Build passed${NC}"
else
    echo -e "${RED}❌ Build failed${NC}"
    FRONTEND_PASSED=false
fi
echo ""

# ============================================
# Summary
# ============================================
cd "$PROJECT_ROOT"

echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo -e "${BLUE}📊 SUMMARY${NC}"
echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo ""

if $BACKEND_PASSED && $FRONTEND_PASSED; then
    echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  ✅ All checks passed! Ready to push.     ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
    exit 0
else
    echo -e "${RED}╔════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║  ❌ Some checks failed. Please fix them.  ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════╝${NC}"
    echo ""
    echo "Results:"
    if $BACKEND_PASSED; then
        echo -e "  Backend:  ${GREEN}✅ Passed${NC}"
    else
        echo -e "  Backend:  ${RED}❌ Failed${NC}"
    fi
    if $FRONTEND_PASSED; then
        echo -e "  Frontend: ${GREEN}✅ Passed${NC}"
    else
        echo -e "  Frontend: ${RED}❌ Failed${NC}"
    fi
    echo ""
    exit 1
fi
