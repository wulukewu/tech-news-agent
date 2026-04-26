#!/bin/bash

# Code Quality Report Generator
# Generates a comprehensive report of code quality metrics

set -e

echo "📊 Generating Code Quality Report..."
echo "===================================="
echo ""

REPORT_FILE="docs/reports/code-quality-$(date +%Y-%m-%d).md"
mkdir -p docs/reports

cat > "$REPORT_FILE" << 'EOF'
# Code Quality Report
Generated: $(date)

## 📊 Metrics Summary

EOF

# Backend Metrics
echo "## Backend Metrics" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

cd backend

# Count lines of code
echo "### Lines of Code" >> "../$REPORT_FILE"
echo '```' >> "../$REPORT_FILE"
find app/ -name "*.py" | xargs wc -l | tail -1 >> "../$REPORT_FILE"
echo '```' >> "../$REPORT_FILE"
echo "" >> "../$REPORT_FILE"

# Largest files
echo "### Largest Files (Top 10)" >> "../$REPORT_FILE"
echo '```' >> "../$REPORT_FILE"
find app/ -name "*.py" -exec wc -l {} + | sort -rn | head -10 >> "../$REPORT_FILE"
echo '```' >> "../$REPORT_FILE"
echo "" >> "../$REPORT_FILE"

# Test coverage (if available)
if command -v pytest &> /dev/null; then
  echo "### Test Coverage" >> "../$REPORT_FILE"
  echo "Running tests with coverage..." >> "../$REPORT_FILE"
  echo '```' >> "../$REPORT_FILE"
  source venv/bin/activate 2>/dev/null || true
  pytest tests/ --cov=app --cov-report=term 2>&1 | tail -20 >> "../$REPORT_FILE" || echo "Tests not available" >> "../$REPORT_FILE"
  echo '```' >> "../$REPORT_FILE"
  echo "" >> "../$REPORT_FILE"
fi

cd ..

# Frontend Metrics
echo "## Frontend Metrics" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

cd frontend

# Count lines of code
echo "### Lines of Code" >> "../$REPORT_FILE"
echo '```' >> "../$REPORT_FILE"
find app/ components/ lib/ -name "*.ts" -o -name "*.tsx" | xargs wc -l | tail -1 >> "../$REPORT_FILE"
echo '```' >> "../$REPORT_FILE"
echo "" >> "../$REPORT_FILE"

# Largest files
echo "### Largest Files (Top 10)" >> "../$REPORT_FILE"
echo '```' >> "../$REPORT_FILE"
find app/ components/ lib/ -name "*.ts" -o -name "*.tsx" | xargs wc -l | sort -rn | head -10 >> "../$REPORT_FILE"
echo '```' >> "../$REPORT_FILE"
echo "" >> "../$REPORT_FILE"

# Count console statements
CONSOLE_COUNT=$(grep -r "console\." app/ components/ lib/ --include="*.ts" --include="*.tsx" 2>/dev/null | grep -v "console.error" | grep -v "examples/" | grep -v "__tests__/" | wc -l)
echo "### Code Quality Issues" >> "../$REPORT_FILE"
echo "- Console statements (non-error): $CONSOLE_COUNT" >> "../$REPORT_FILE"
echo "" >> "../$REPORT_FILE"

# TypeScript errors
echo "### TypeScript Check" >> "../$REPORT_FILE"
echo '```' >> "../$REPORT_FILE"
npm run type-check 2>&1 | tail -5 >> "../$REPORT_FILE" || echo "Type check failed" >> "../$REPORT_FILE"
echo '```' >> "../$REPORT_FILE"
echo "" >> "../$REPORT_FILE"

cd ..

# Git metrics
echo "## Git Metrics" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"
echo "### Recent Activity (Last 7 days)" >> "$REPORT_FILE"
echo '```' >> "$REPORT_FILE"
git log --since="7 days ago" --oneline | wc -l | xargs echo "Commits:" >> "$REPORT_FILE"
git log --since="7 days ago" --format='%an' | sort | uniq | wc -l | xargs echo "Contributors:" >> "$REPORT_FILE"
echo '```' >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

# Recommendations
cat >> "$REPORT_FILE" << 'RECOMMENDATIONS'
## 🎯 Recommendations

### High Priority
- [ ] Refactor files >500 lines
- [ ] Reduce console.log usage
- [ ] Improve test coverage to >70%

### Medium Priority
- [ ] Add missing type definitions
- [ ] Complete i18n translations
- [ ] Add E2E tests for critical flows

### Low Priority
- [ ] Improve documentation
- [ ] Optimize bundle size
- [ ] Add performance benchmarks

---
*Report generated automatically by code-quality-report.sh*
RECOMMENDATIONS

echo ""
echo "✅ Report generated: $REPORT_FILE"
echo ""
echo "📄 Summary:"
cat "$REPORT_FILE" | head -30
