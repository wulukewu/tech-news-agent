#!/bin/bash
# DM Conversation Memory System - Quick Verification
# Checks if all components are in place

echo "============================================================"
echo "DM Conversation Memory System - Quick Verification"
echo "============================================================"
echo ""

PASS=0
FAIL=0

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $2"
        ((PASS++))
    else
        echo -e "${RED}✗${NC} $2 (missing: $1)"
        ((FAIL++))
    fi
}

check_content() {
    if grep -q "$2" "$1" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} $3"
        ((PASS++))
    else
        echo -e "${RED}✗${NC} $3"
        ((FAIL++))
    fi
}

echo -e "${BLUE}1. Database Migration${NC}"
echo "------------------------------------------------------------"
check_file "scripts/migrations/017_dm_conversation_memory.sql" "Migration file exists"
check_content "scripts/migrations/017_dm_conversation_memory.sql" "dm_conversations" "dm_conversations table defined"
check_content "scripts/migrations/017_dm_conversation_memory.sql" "preference_summary" "preference_summary column defined"
echo ""

echo -e "${BLUE}2. Backend Services${NC}"
echo "------------------------------------------------------------"
check_file "app/bot/cogs/dm_conversation_listener.py" "DM Conversation Listener"
check_file "app/services/preference_summary_service.py" "Preference Summary Service"
check_file "app/services/auto_preference_summary.py" "Auto Preference Summary"
check_content "app/tasks/scheduler.py" "preference_summary_job" "Scheduler job registered"
echo ""

echo -e "${BLUE}3. Recommendation Integration${NC}"
echo "------------------------------------------------------------"
check_file "app/services/recommendation_reason.py" "Recommendation Reason Service"
check_content "app/services/recommendation_reason.py" "preference_summary" "Uses preference_summary parameter"
check_content "app/tasks/proactive_recommendation.py" "preference_summary" "Proactive recommendation fetches summary"
echo ""

echo -e "${BLUE}4. Discord Commands${NC}"
echo "------------------------------------------------------------"
check_content "app/bot/cogs/news_commands.py" "my_profile" "/my_profile command"
check_content "app/bot/cogs/news_commands.py" "update_profile" "/update_profile command"
echo ""

echo -e "${BLUE}5. API Endpoints${NC}"
echo "------------------------------------------------------------"
check_content "app/api/proactive_learning.py" "UpdateSummaryRequest" "UpdateSummaryRequest schema"
check_content "app/api/proactive_learning.py" "@router.patch.*summary" "PATCH /summary endpoint"
check_content "app/api/proactive_learning.py" "@router.get.*summary" "GET /summary endpoint"
echo ""

echo -e "${BLUE}6. Frontend Integration${NC}"
echo "------------------------------------------------------------"
check_file "frontend/app/app/preferences/page.tsx" "Preferences page"
check_file "frontend/app/app/settings/preferences/page.tsx" "Settings preferences page"
check_content "frontend/lib/api/proactive-learning.ts" "getPreferenceSummary" "Frontend API: getPreferenceSummary"
check_content "frontend/lib/api/proactive-learning.ts" "updatePreferenceSummary" "Frontend API: updatePreferenceSummary"
echo ""

echo "============================================================"
echo -e "${BLUE}Summary${NC}"
echo "============================================================"
TOTAL=$((PASS + FAIL))
PERCENTAGE=$((PASS * 100 / TOTAL))

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed! ($PASS/$TOTAL)${NC}"
    echo ""
    echo -e "${GREEN}🎉 DM Conversation Memory System is fully implemented!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Ensure migration 017 is applied to your database"
    echo "  2. Test by sending a DM to the bot"
    echo "  3. Run /update_profile to generate summary"
    echo "  4. Run /my_profile to view your preferences"
    echo ""
    exit 0
elif [ $PERCENTAGE -ge 80 ]; then
    echo -e "${YELLOW}⚠ Most checks passed ($PASS/$TOTAL - $PERCENTAGE%)${NC}"
    echo ""
    echo -e "${YELLOW}System is mostly complete, $FAIL minor issues to fix.${NC}"
    echo ""
    exit 1
else
    echo -e "${RED}✗ Many checks failed ($PASS/$TOTAL - $PERCENTAGE%)${NC}"
    echo ""
    echo -e "${RED}System needs significant work.${NC}"
    echo ""
    exit 2
fi
