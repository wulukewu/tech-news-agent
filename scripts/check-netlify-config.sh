#!/bin/bash

# Netlify Configuration Checker
# Verifies that Next.js is properly configured for Netlify deployment

set -e

echo "🔍 Checking Netlify deployment configuration..."
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0
WARNINGS=0

# Check 1: netlify.toml exists
echo "1️⃣  Checking netlify.toml..."
if [ -f "netlify.toml" ]; then
    echo -e "${GREEN}✓${NC} netlify.toml found"

    # Check for Next.js plugin
    if grep -q "@netlify/plugin-nextjs" netlify.toml; then
        echo -e "${GREEN}✓${NC} Next.js plugin configured"
    else
        echo -e "${RED}✗${NC} Next.js plugin not found in netlify.toml"
        ERRORS=$((ERRORS + 1))
    fi

    # Check for correct base directory
    if grep -q 'base = "frontend/"' netlify.toml; then
        echo -e "${GREEN}✓${NC} Base directory set to frontend/"
    else
        echo -e "${YELLOW}⚠${NC} Base directory might not be set correctly"
        WARNINGS=$((WARNINGS + 1))
    fi

    # Check for incorrect redirects
    if grep -q 'to = "/index.html"' netlify.toml; then
        echo -e "${RED}✗${NC} Found SPA-style redirect (should not be used with Next.js)"
        ERRORS=$((ERRORS + 1))
    else
        echo -e "${GREEN}✓${NC} No problematic redirects found"
    fi
else
    echo -e "${RED}✗${NC} netlify.toml not found"
    ERRORS=$((ERRORS + 1))
fi

echo ""

# Check 2: next.config.js
echo "2️⃣  Checking next.config.js..."
if [ -f "frontend/next.config.js" ]; then
    echo -e "${GREEN}✓${NC} next.config.js found"

    # Check for standalone output (should be commented out for Netlify)
    if grep -q "output: 'standalone'" frontend/next.config.js && ! grep -q "// output: 'standalone'" frontend/next.config.js; then
        echo -e "${RED}✗${NC} output: 'standalone' is active (should be commented out for Netlify)"
        echo -e "   ${YELLOW}This is the most common cause of 404 errors!${NC}"
        ERRORS=$((ERRORS + 1))
    else
        echo -e "${GREEN}✓${NC} output: 'standalone' is not active"
    fi
else
    echo -e "${RED}✗${NC} next.config.js not found"
    ERRORS=$((ERRORS + 1))
fi

echo ""

# Check 3: package.json
echo "3️⃣  Checking package.json..."
if [ -f "frontend/package.json" ]; then
    echo -e "${GREEN}✓${NC} package.json found"

    # Check for build script
    if grep -q '"build"' frontend/package.json; then
        echo -e "${GREEN}✓${NC} Build script found"
    else
        echo -e "${RED}✗${NC} Build script not found"
        ERRORS=$((ERRORS + 1))
    fi

    # Check for Next.js dependency
    if grep -q '"next"' frontend/package.json; then
        echo -e "${GREEN}✓${NC} Next.js dependency found"
    else
        echo -e "${RED}✗${NC} Next.js dependency not found"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo -e "${RED}✗${NC} package.json not found"
    ERRORS=$((ERRORS + 1))
fi

echo ""

# Check 4: Environment variables
echo "4️⃣  Checking environment variables..."
if [ -f "frontend/.env.local" ] || [ -f "frontend/.env" ]; then
    echo -e "${GREEN}✓${NC} Environment file found"
    echo -e "${YELLOW}⚠${NC} Remember to set these in Netlify UI:"
    echo "   - NEXT_PUBLIC_API_BASE_URL"
    echo "   - NEXT_PUBLIC_APP_NAME"
else
    echo -e "${YELLOW}⚠${NC} No .env file found (might be intentional)"
    WARNINGS=$((WARNINGS + 1))
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Summary
if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC} Your configuration looks good for Netlify deployment."
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠ $WARNINGS warning(s) found${NC} - Review the warnings above"
else
    echo -e "${RED}✗ $ERRORS error(s) found${NC} - Fix these before deploying"
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}⚠ $WARNINGS warning(s) found${NC} - Review the warnings above"
    fi
fi

echo ""
echo "📚 For more help, see: docs/deployment/netlify-deployment.md"
echo ""

exit $ERRORS
