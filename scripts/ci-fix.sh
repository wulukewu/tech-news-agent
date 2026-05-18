#!/bin/bash

# CI Fix Script
# Automatically fix common CI issues

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

# Get project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

resolve_backend_python() {
    if [ -x "$PROJECT_ROOT/backend/venv/bin/python" ]; then
        echo "$PROJECT_ROOT/backend/venv/bin/python"
    elif command_exists python3; then
        echo "python3"
    else
        echo ""
    fi
}

echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         CI Auto-Fix Script                 ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo ""

# ============================================
# Backend Fixes
# ============================================
echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo -e "${BLUE}🐍 BACKEND FIXES${NC}"
echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo ""

cd "$PROJECT_ROOT/backend"
BACKEND_PYTHON=$(resolve_backend_python)

if [ -z "$BACKEND_PYTHON" ]; then
    echo -e "${RED}❌ Python runtime not found (python3 or backend/venv/bin/python)${NC}"
    exit 1
fi

echo "1️⃣ Fixing Black formatting..."
if "$BACKEND_PYTHON" -m black app/ tests/; then
    echo -e "${GREEN}✅ Black formatting applied${NC}"
else
    echo -e "${RED}❌ Black formatting failed${NC}"
fi
echo ""

echo "2️⃣ Fixing Ruff issues..."
if "$BACKEND_PYTHON" -m ruff check --fix app/ tests/; then
    echo -e "${GREEN}✅ Ruff fixes applied${NC}"
else
    echo -e "${YELLOW}⚠️  Some Ruff issues may need manual fixing${NC}"
fi
echo ""

# ============================================
# Frontend Fixes
# ============================================
echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo -e "${BLUE}⚛️  FRONTEND FIXES${NC}"
echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo ""

cd "$PROJECT_ROOT/frontend"

echo "1️⃣ Fixing Prettier formatting..."
if npm run format; then
    echo -e "${GREEN}✅ Prettier formatting applied${NC}"
else
    echo -e "${RED}❌ Prettier formatting failed${NC}"
fi
echo ""

echo "2️⃣ Fixing ESLint issues..."
if npm run lint:fix; then
    echo -e "${GREEN}✅ ESLint fixes applied${NC}"
else
    echo -e "${YELLOW}⚠️  Some ESLint issues may need manual fixing${NC}"
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

echo -e "${GREEN}✅ Auto-fixes applied!${NC}"
echo ""
echo "Next steps:"
echo "  1. Review the changes: git diff"
echo "  2. Run local tests: ./scripts/ci-local-test.sh"
echo "  3. Commit and push if all tests pass"
echo ""
