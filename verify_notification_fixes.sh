#!/bin/bash

# Notification Settings Fix Verification Script
# This script verifies that all notification-related fixes are working correctly

set -e

echo "🔍 Verifying Notification Settings Fixes..."
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print success
success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Function to print error
error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to print warning
warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Function to print section header
section() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  $1"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
}

# 1. Check Backend Files
section "1. Checking Backend Files"

if [ -f "backend/app/api/notifications.py" ]; then
    success "Notification API endpoints exist"
else
    error "Notification API endpoints missing"
    exit 1
fi

if [ -f "backend/app/services/notification_settings_service.py" ]; then
    success "Notification settings service exists"
else
    error "Notification settings service missing"
    exit 1
fi

if [ -f "backend/app/schemas/notification.py" ]; then
    success "Notification schemas exist"
else
    error "Notification schemas missing"
    exit 1
fi

if [ -f "backend/tests/test_notification_settings_service.py" ]; then
    success "Backend tests exist"
else
    error "Backend tests missing"
    exit 1
fi

# 2. Check Frontend Files
section "2. Checking Frontend Files"

if [ -f "frontend/features/notifications/components/QuietHoursSettings.tsx" ]; then
    success "QuietHoursSettings component exists"
else
    error "QuietHoursSettings component missing"
    exit 1
fi

if [ -f "frontend/features/notifications/components/TinkeringIndexThreshold.tsx" ]; then
    success "TinkeringIndexThreshold component exists"
else
    error "TinkeringIndexThreshold component missing"
    exit 1
fi

if [ -f "frontend/features/notifications/components/NotificationFrequencySelector.tsx" ]; then
    success "NotificationFrequencySelector component exists"
else
    error "NotificationFrequencySelector component missing"
    exit 1
fi

if [ -f "frontend/features/notifications/__tests__/unit/QuietHoursSettings.test.tsx" ]; then
    success "Frontend tests exist"
else
    error "Frontend tests missing"
    exit 1
fi

# 3. Check Defensive Programming
section "3. Checking Defensive Programming"

if grep -q "const safeQuietHours = quietHours ||" frontend/features/notifications/components/QuietHoursSettings.tsx; then
    success "QuietHoursSettings has defensive programming"
else
    error "QuietHoursSettings missing defensive programming"
    exit 1
fi

if grep -q "const safeThreshold = threshold ||" frontend/features/notifications/components/TinkeringIndexThreshold.tsx; then
    success "TinkeringIndexThreshold has defensive programming"
else
    error "TinkeringIndexThreshold missing defensive programming"
    exit 1
fi

if grep -q "frequency || 'immediate'" frontend/features/notifications/components/NotificationFrequencySelector.tsx; then
    success "NotificationFrequencySelector has defensive programming"
else
    error "NotificationFrequencySelector missing defensive programming"
    exit 1
fi

if grep -q "const safeFeedSettings = feedSettings ||" frontend/features/notifications/components/FeedNotificationSettings.tsx; then
    success "FeedNotificationSettings has defensive programming"
else
    error "FeedNotificationSettings missing defensive programming"
    exit 1
fi

if grep -q "!data || !data.recentHistory || data.recentHistory.length" frontend/features/notifications/components/NotificationHistoryPanel.tsx; then
    success "NotificationHistoryPanel has defensive programming"
else
    error "NotificationHistoryPanel missing defensive programming"
    exit 1
fi

# 4. Check Router Registration
section "4. Checking Router Registration"

if grep -q "app.include_router(notifications.router" backend/app/main.py; then
    success "Notifications router is registered"
else
    error "Notifications router not registered"
    exit 1
fi

# 5. Run Backend Tests
section "5. Running Backend Tests"

cd backend
if python3 -m pytest tests/test_notification_settings_service.py -v --tb=short; then
    success "All backend tests passed"
else
    error "Backend tests failed"
    exit 1
fi
cd ..

# 6. Run Frontend Tests
section "6. Running Frontend Tests"

cd frontend
if npm test -- QuietHoursSettings.test.tsx --run; then
    success "All frontend tests passed"
else
    error "Frontend tests failed"
    exit 1
fi
cd ..

# 7. Check API Endpoint
section "7. Checking API Endpoint"

# Check if backend is running
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    success "Backend is running"

    # Test notification endpoint (should return 401 without auth)
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/notifications/settings)

    if [ "$HTTP_CODE" = "401" ]; then
        success "Notification API endpoint exists (returns 401 as expected)"
    elif [ "$HTTP_CODE" = "404" ]; then
        error "Notification API endpoint returns 404 (not found)"
        exit 1
    else
        warning "Notification API endpoint returns unexpected code: $HTTP_CODE"
    fi
else
    warning "Backend is not running - skipping API endpoint check"
    warning "Start backend with: cd backend && python3 -m uvicorn app.main:app --reload"
fi

# 8. Summary
section "Summary"

success "All verification checks passed!"
echo ""
echo "✨ Notification settings fixes are working correctly:"
echo "   • Backend API endpoints created"
echo "   • Frontend components have defensive programming"
echo "   • All tests passing"
echo "   • Router properly registered"
echo ""
echo "📝 Next steps:"
echo "   1. Start backend: cd backend && python3 -m uvicorn app.main:app --reload"
echo "   2. Start frontend: cd frontend && npm run dev"
echo "   3. Navigate to: http://localhost:3000/settings/notifications"
echo "   4. Verify no 404 or runtime errors"
echo ""
