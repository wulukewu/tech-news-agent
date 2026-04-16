#!/bin/bash

# TypeScript Error Checker
# Helps identify and categorize TypeScript errors for systematic fixing

set -e

echo "🔍 Checking TypeScript errors..."
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Change to frontend directory
cd frontend

# Function to count errors in a file
count_errors() {
    local file=$1
    npx tsc --noEmit "$file" 2>&1 | grep -c "error TS" || echo "0"
}

# Function to show errors for a file
show_errors() {
    local file=$1
    echo -e "${BLUE}Checking: $file${NC}"
    npx tsc --noEmit "$file" 2>&1 | grep "error TS" || echo -e "${GREEN}  ✓ No errors${NC}"
    echo ""
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Phase 1: Component Type Fixes (P0-P1)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Task 1.1: ErrorMessage Component
echo "📋 Task 1.1: ErrorMessage Component Usage"
show_errors "app/(dashboard)/settings/notifications/page.tsx"
show_errors "features/notifications/components/NotificationHistoryPanel.tsx"

# Task 1.3: Missing Type Exports
echo "📋 Task 1.3: Missing Type Exports"
show_errors "components/ui/drag-drop-list.tsx"
show_errors "features/articles/components/InteractiveArticleBrowser.example.tsx"

# Task 1.4: Button Size Types
echo "📋 Task 1.4: Button Size Types"
show_errors "features/ai-analysis/components/AnalysisTrigger.tsx"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Phase 2: API & Utility Type Fixes (P1-P2)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Task 2.1: Window.gtag Types
echo "📋 Task 2.1: Window.gtag Types"
show_errors "features/ai-analysis/hooks/index.ts"

# Task 2.2: ServiceWorkerRegistration.sync Types
echo "📋 Task 2.2: ServiceWorkerRegistration.sync Types"
show_errors "hooks/useBackgroundSync.ts"

# Task 2.3: VirtualizedList Generic Types
echo "📋 Task 2.3: VirtualizedList Generic Types"
show_errors "components/ui/VirtualizedList.tsx"

# Task 2.4: API Return Types
echo "📋 Task 2.4: API Return Types"
show_errors "lib/api/auth.ts"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Phase 3: Example & Demo File Fixes (P3)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Task 3.1: Lazy Component Imports
echo "📋 Task 3.1: Lazy Component Imports"
show_errors "components/lazy-components.tsx"

# Task 3.2: Error Recovery Examples
echo "📋 Task 3.2: Error Recovery Examples"
show_errors "lib/api/examples/enhanced-features-example.ts"
show_errors "lib/api/examples/error-handling-example.ts"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Run full type check
echo "Running full type check..."
if npx tsc --noEmit 2>&1 | grep -q "error TS"; then
    ERROR_COUNT=$(npx tsc --noEmit 2>&1 | grep -c "error TS" || echo "0")
    echo -e "${RED}✗ Found $ERROR_COUNT TypeScript errors${NC}"
    echo ""
    echo "Run 'npm run type-check' for full details"
else
    echo -e "${GREEN}✓ No TypeScript errors found!${NC}"
fi

echo ""
echo "📚 See docs/tasks/typescript-errors-fix-plan.md for detailed fix instructions"
echo ""
