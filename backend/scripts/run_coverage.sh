#!/bin/bash

# Backend Test Coverage Script
# This script runs tests with coverage reporting and generates reports

set -e

echo "🧪 Running Backend Tests with Coverage..."
echo "=========================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Run tests with coverage
python3 -m pytest tests/ \
  --cov=app \
  --cov-report=term-missing \
  --cov-report=html:htmlcov \
  --cov-report=json:coverage.json \
  -m "not property_test" \
  --tb=short \
  -v

# Check if coverage report was generated
if [ -f "coverage.json" ]; then
  echo ""
  echo "✅ Coverage reports generated:"
  echo "  - Terminal: See above"
  echo "  - HTML: htmlcov/index.html"
  echo "  - JSON: coverage.json"
  echo ""

  # Extract overall coverage percentage
  COVERAGE=$(python3 -c "import json; data=json.load(open('coverage.json')); print(f\"{data['totals']['percent_covered']:.1f}\")")

  echo "📊 Overall Coverage: ${COVERAGE}%"

  if (( $(echo "$COVERAGE >= 80" | bc -l) )); then
    echo -e "${GREEN}✅ Coverage meets 80% target!${NC}"
  elif (( $(echo "$COVERAGE >= 70" | bc -l) )); then
    echo -e "${YELLOW}⚠️  Coverage is above 70% but below 80% target${NC}"
  else
    echo -e "${RED}❌ Coverage is below 70% - needs improvement${NC}"
  fi

  echo ""
  echo "📖 View detailed HTML report:"
  echo "   open htmlcov/index.html"
else
  echo -e "${RED}❌ Coverage report not generated${NC}"
  exit 1
fi
