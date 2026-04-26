#!/bin/bash

# Script to replace console.log with logger utility
# Usage: ./scripts/replace-console-logs.sh

set -e

echo "🔄 Replacing console.log with logger utility..."
echo ""

cd frontend

# Files to process (excluding test files and examples)
FILES=$(find app/ components/ lib/ -type f \( -name "*.ts" -o -name "*.tsx" \) \
  ! -path "*/node_modules/*" \
  ! -path "*/__tests__/*" \
  ! -path "*/examples/*" \
  ! -name "*.test.ts" \
  ! -name "*.test.tsx" \
  ! -name "logger.ts")

TOTAL=0
MODIFIED=0

for file in $FILES; do
  # Check if file contains console statements
  if grep -q "console\." "$file" 2>/dev/null; then
    TOTAL=$((TOTAL + 1))

    # Check if logger is already imported
    if ! grep -q "from.*logger" "$file" 2>/dev/null; then
      # Add logger import at the top (after other imports)
      if grep -q "^import" "$file"; then
        # Find the last import line
        LAST_IMPORT=$(grep -n "^import" "$file" | tail -1 | cut -d: -f1)
        # Insert logger import after last import
        sed -i "${LAST_IMPORT}a import { logger } from '@/lib/utils/logger';" "$file"
        echo "  ✓ Added logger import to $file"
      fi
    fi

    # Replace console.log with logger.debug
    if grep -q "console\.log" "$file"; then
      sed -i 's/console\.log/logger.debug/g' "$file"
      MODIFIED=$((MODIFIED + 1))
      echo "  ✓ Replaced console.log in $file"
    fi

    # Replace console.info with logger.info
    if grep -q "console\.info" "$file"; then
      sed -i 's/console\.info/logger.info/g' "$file"
      echo "  ✓ Replaced console.info in $file"
    fi

    # Replace console.warn with logger.warn
    if grep -q "console\.warn" "$file"; then
      sed -i 's/console\.warn/logger.warn/g' "$file"
      echo "  ✓ Replaced console.warn in $file"
    fi

    # Keep console.error as is (errors should always be logged)
  fi
done

echo ""
echo "📊 Summary:"
echo "  Total files with console statements: $TOTAL"
echo "  Files modified: $MODIFIED"
echo ""
echo "✅ Done! Run 'npm run lint:fix' to fix any formatting issues."
