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

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

resolve_backend_python() {
    if [ -x "$PROJECT_ROOT/backend/venv/bin/python" ]; then
        echo "$PROJECT_ROOT/backend/venv/bin/python"
    elif command_exists python3; then
        echo "python3"
    else
        echo ""
    fi
}

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
export APP_ENV="test"
export HYPOTHESIS_PROFILE="ci"
export SUPABASE_URL="https://dummy.supabase.co"
export SUPABASE_KEY="dummy_supabase_key_that_is_long_enough"
export DISCORD_TOKEN="dummy_discord_token_that_is_long_enough_to_pass_validation_check"
export DISCORD_CHANNEL_ID="123456789012345678"
export DISCORD_CLIENT_ID="123456789012345678"
export DISCORD_CLIENT_SECRET="dummy_discord_client_secret_long_enough"
export DISCORD_REDIRECT_URI="http://localhost:8000/api/auth/discord/callback"
export GROQ_API_KEY="gsk_dummy_groq_api_key_for_ci_testing_only"
export TIMEZONE="Asia/Taipei"
export JWT_SECRET="abcdef1234567890abcdef1234567890ab"
export JWT_ALGORITHM="HS256"
export JWT_EXPIRATION_DAYS="7"
export CORS_ORIGINS="http://localhost:3000"
export FRONTEND_URL="http://localhost:3000"

BACKEND_PYTHON=$(resolve_backend_python)
if [ -z "$BACKEND_PYTHON" ]; then
    echo -e "${RED}❌ Python runtime not found (python3 or backend/venv/bin/python)${NC}"
    exit 1
fi

echo "1️⃣ Black formatting check..."
if "$BACKEND_PYTHON" -m black --check --diff app/ tests/; then
    echo -e "${GREEN}✅ Black formatting passed${NC}"
else
    echo -e "${RED}❌ Black formatting failed${NC}"
    echo -e "${YELLOW}💡 Fix with: cd backend && $BACKEND_PYTHON -m black app/ tests/${NC}"
    BACKEND_PASSED=false
fi
echo ""

echo "2️⃣ Ruff linting..."
if "$BACKEND_PYTHON" -m ruff check app/ tests/; then
    echo -e "${GREEN}✅ Ruff linting passed${NC}"
else
    echo -e "${RED}❌ Ruff linting failed${NC}"
    echo -e "${YELLOW}💡 Fix with: cd backend && $BACKEND_PYTHON -m ruff check --fix app/ tests/${NC}"
    BACKEND_PASSED=false
fi
echo ""

echo "3️⃣ Type checking with mypy..."
if MYPYPATH=. "$BACKEND_PYTHON" -m mypy app/ --ignore-missing-imports --no-strict-optional --python-version=3.11 --explicit-package-bases; then
    echo -e "${GREEN}✅ Type checking passed${NC}"
else
    echo -e "${YELLOW}⚠️ Type checking failed (non-blocking)${NC}"
fi
echo ""

echo "4️⃣ Running backend tests with coverage..."
if "$BACKEND_PYTHON" -m pytest tests/ --tb=short \
    --cov=app \
    --cov-report=term \
    --timeout=30 \
    -n 4 \
    --dist=loadfile \
    -q; then
    echo -e "${GREEN}✅ Backend tests passed${NC}"
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

if ! command_exists npm; then
    echo -e "${RED}❌ npm not found${NC}"
    exit 1
fi

echo "0️⃣ Generate i18n types..."
if npm run generate:i18n-types; then
    echo -e "${GREEN}✅ i18n types generated${NC}"
else
    echo -e "${RED}❌ i18n type generation failed${NC}"
    FRONTEND_PASSED=false
fi
echo ""

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
if npx eslint . --ext .ts,.tsx --max-warnings 9999; then
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

echo "4️⃣ Running gate tests (blocking)..."
if npm run test:gate; then
    echo -e "${GREEN}✅ Gate tests passed${NC}"
else
    echo -e "${RED}❌ Gate tests failed${NC}"
    FRONTEND_PASSED=false
fi
echo ""

echo "5️⃣ Running extended tests (non-blocking)..."
if npm run test:extended; then
    echo -e "${GREEN}✅ Extended tests passed${NC}"
else
    echo -e "${YELLOW}⚠️ Extended tests failed (non-blocking)${NC}"
fi
echo ""

echo "6️⃣ Build verification..."
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
