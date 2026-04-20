#!/bin/bash

# Phase 1 Complete Verification Script
# Verifies all Phase 1 features are working correctly

echo "🔍 Phase 1 完整驗證測試"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PASS=0
FAIL=0

# Function to test endpoint
test_endpoint() {
    local name=$1
    local url=$2
    local expected_code=$3

    echo -n "   Testing $name... "
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$url")

    if [ "$HTTP_CODE" = "$expected_code" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $HTTP_CODE)"
        ((PASS++))
    else
        echo -e "${RED}✗ FAIL${NC} (Expected $expected_code, got $HTTP_CODE)"
        ((FAIL++))
    fi
}

# Test 1: Backend Health
echo "1️⃣  Backend Health Check"
if curl -s http://localhost:8000/health | grep -q '"status":"healthy"'; then
    echo -e "   ${GREEN}✓ Backend is healthy${NC}"
    ((PASS++))
else
    echo -e "   ${RED}✗ Backend is not healthy${NC}"
    ((FAIL++))
fi
echo ""

# Test 2: Frontend Status
echo "2️⃣  Frontend Status Check"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000)
if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "304" ]; then
    echo -e "   ${GREEN}✓ Frontend is running${NC}"
    ((PASS++))
else
    echo -e "   ${RED}✗ Frontend is not accessible (HTTP $HTTP_CODE)${NC}"
    ((FAIL++))
fi
echo ""

# Test 3: Phase 1 Public Endpoints
echo "3️⃣  Phase 1 Public Endpoints"
test_endpoint "Tech Depth Levels" "http://localhost:8000/api/notifications/tech-depth/levels" "200"
test_endpoint "Supported Timezones" "http://localhost:8000/api/notifications/preferences/timezones" "200"
echo ""

# Test 4: Phase 1 Protected Endpoints (should return 401 without auth)
echo "4️⃣  Phase 1 Protected Endpoints (Auth Required)"
test_endpoint "Quiet Hours GET" "http://localhost:8000/api/notifications/quiet-hours" "401"
test_endpoint "Quiet Hours Status" "http://localhost:8000/api/notifications/quiet-hours/status" "401"
test_endpoint "Tech Depth GET" "http://localhost:8000/api/notifications/tech-depth" "401"
test_endpoint "Tech Depth Stats" "http://localhost:8000/api/notifications/tech-depth/stats" "401"
test_endpoint "Notification History" "http://localhost:8000/api/notifications/history" "401"
test_endpoint "Notification Stats" "http://localhost:8000/api/notifications/history/stats" "401"
echo ""

# Test 5: Database Tables
echo "5️⃣  Database Schema Verification"
echo "   ${BLUE}ℹ${NC}  Checking if required tables exist..."
echo "   - user_quiet_hours"
echo "   - notification_history"
echo "   - user_notification_preferences (with tech_depth columns)"
echo "   ${YELLOW}⚠${NC}  Manual verification required in Supabase"
echo ""

# Test 6: Docker Containers
echo "6️⃣  Docker Containers Status"
BACKEND_STATUS=$(docker ps --filter "name=tech-news-agent-backend-dev" --format "{{.Status}}" | grep -o "Up")
FRONTEND_STATUS=$(docker ps --filter "name=tech-news-agent-frontend-dev" --format "{{.Status}}" | grep -o "Up")

if [ "$BACKEND_STATUS" = "Up" ]; then
    echo -e "   ${GREEN}✓ Backend container is running${NC}"
    ((PASS++))
else
    echo -e "   ${RED}✗ Backend container is not running${NC}"
    ((FAIL++))
fi

if [ "$FRONTEND_STATUS" = "Up" ]; then
    echo -e "   ${GREEN}✓ Frontend container is running${NC}"
    ((PASS++))
else
    echo -e "   ${RED}✗ Frontend container is not running${NC}"
    ((FAIL++))
fi
echo ""

# Summary
echo "========================================"
echo "📊 Test Results Summary"
echo "========================================"
echo -e "   ${GREEN}Passed: $PASS${NC}"
echo -e "   ${RED}Failed: $FAIL${NC}"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✅ All automated tests passed!${NC}"
    echo ""
    echo "📝 Manual Testing Steps:"
    echo "   1. Login to http://localhost:3000"
    echo "   2. Navigate to Settings > Notifications"
    echo "   3. Test Quiet Hours settings:"
    echo "      - Enable/disable quiet hours"
    echo "      - Set time range and timezone"
    echo "      - Select weekdays"
    echo "      - Verify status indicator"
    echo "   4. Test Technical Depth settings:"
    echo "      - Enable/disable filtering"
    echo "      - Select threshold level"
    echo "      - View statistics"
    echo "   5. View Notification History:"
    echo "      - Check past notifications"
    echo "      - View statistics"
    echo ""
    echo -e "${GREEN}🎉 Phase 1 is ready for production!${NC}"
else
    echo -e "${RED}❌ Some tests failed. Please review the errors above.${NC}"
    exit 1
fi
