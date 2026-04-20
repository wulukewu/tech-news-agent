#!/bin/bash

# Test Phase 1 Frontend Integration
# This script tests if the frontend can properly communicate with Phase 1 backend APIs

echo "🧪 Testing Phase 1 Frontend Integration"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Check if frontend is running
echo "1️⃣  Checking frontend status..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 | grep -q "200"; then
    echo -e "${GREEN}✓ Frontend is running${NC}"
else
    echo -e "${RED}✗ Frontend is not accessible${NC}"
    exit 1
fi
echo ""

# Test 2: Check if backend is running
echo "2️⃣  Checking backend status..."
if curl -s http://localhost:8000/health | grep -q "healthy"; then
    echo -e "${GREEN}✓ Backend is healthy${NC}"
else
    echo -e "${RED}✗ Backend is not healthy${NC}"
    exit 1
fi
echo ""

# Test 3: Check Phase 1 API endpoints
echo "3️⃣  Testing Phase 1 API endpoints..."

# Test tech depth levels (public endpoint)
echo "   Testing /api/notifications/tech-depth/levels..."
RESPONSE=$(curl -s -w "\n%{http_code}" http://localhost:8000/api/notifications/tech-depth/levels)
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
if [ "$HTTP_CODE" = "200" ]; then
    echo -e "   ${GREEN}✓ Tech depth levels endpoint working${NC}"
else
    echo -e "   ${RED}✗ Tech depth levels endpoint failed (HTTP $HTTP_CODE)${NC}"
fi

# Test quiet hours status (requires auth, should return 401)
echo "   Testing /api/notifications/quiet-hours/status..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/notifications/quiet-hours/status)
if [ "$HTTP_CODE" = "401" ]; then
    echo -e "   ${GREEN}✓ Quiet hours endpoint exists (requires auth)${NC}"
else
    echo -e "   ${YELLOW}⚠ Quiet hours endpoint returned HTTP $HTTP_CODE${NC}"
fi

# Test tech depth settings (requires auth, should return 401)
echo "   Testing /api/notifications/tech-depth..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/notifications/tech-depth)
if [ "$HTTP_CODE" = "401" ]; then
    echo -e "   ${GREEN}✓ Tech depth settings endpoint exists (requires auth)${NC}"
else
    echo -e "   ${YELLOW}⚠ Tech depth settings endpoint returned HTTP $HTTP_CODE${NC}"
fi

echo ""

# Test 4: Check if settings page is accessible
echo "4️⃣  Checking settings page..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/settings/notifications)
if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ Settings page is accessible${NC}"
else
    echo -e "${RED}✗ Settings page returned HTTP $HTTP_CODE${NC}"
fi
echo ""

# Summary
echo "========================================"
echo -e "${GREEN}✅ Phase 1 Frontend Integration Test Complete${NC}"
echo ""
echo "📝 Next Steps:"
echo "   1. Login to the frontend at http://localhost:3000"
echo "   2. Navigate to Settings > Notifications"
echo "   3. Test Quiet Hours and Technical Depth settings"
echo "   4. Verify settings are saved and loaded correctly"
echo ""
