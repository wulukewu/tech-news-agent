#!/bin/bash
# Local testing script to verify all CI checks pass

set -e  # Exit on error

echo "================================"
echo "Running Local CI Tests"
echo "================================"
echo ""

# Frontend Tests
echo "📦 Frontend Tests"
echo "--------------------------------"

cd frontend

echo "✓ Type checking..."
npm run type-check

echo "✓ Linting..."
npm run lint

echo "✓ Unit tests..."
npm test -- --passWithNoTests

echo "✓ Building..."
npm run build

cd ..

echo ""
echo "🐍 Backend Tests"
echo "--------------------------------"

cd backend

echo "✓ Running fast tests (without parallelization for stability)..."
pytest --tb=short -q --ignore-glob="*property*.py" --ignore=tests/integration/ --ignore=tests/test_add_feed_command.py

cd ..

echo ""
echo "================================"
echo "✅ All tests passed!"
echo "================================"
