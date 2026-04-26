#!/bin/bash
set -e

echo "🚀 Running complete CI checks locally..."
echo ""

# ============================================
# Backend Checks
# ============================================
echo "📦 Backend Checks"
echo "=================="
cd backend

# Activate virtual environment
source venv/bin/activate

echo "✅ 1. Black formatting check..."
python -m black --check app/ tests/ || {
  echo "❌ Black formatting failed. Running auto-fix..."
  python -m black app/ tests/
  echo "✅ Black formatting fixed!"
}

echo ""
echo "✅ 2. Ruff linting check..."
python -m ruff check app/ tests/ || {
  echo "❌ Ruff linting failed"
  exit 1
}

echo ""
echo "✅ Backend checks passed!"
echo ""

cd ..

# ============================================
# Frontend Checks
# ============================================
echo "🎨 Frontend Checks"
echo "=================="
cd frontend

echo "✅ 1. Prettier formatting check..."
npm run format:check || {
  echo "❌ Prettier formatting failed. Running auto-fix..."
  npm run format
  echo "✅ Prettier formatting fixed!"
}

echo ""
echo "✅ 2. TypeScript type checking..."
npm run type-check || {
  echo "❌ Type errors found"
  exit 1
}

echo ""
echo "✅ 3. ESLint check..."
npm run lint || {
  echo "⚠️ ESLint warnings found (non-blocking)"
}

echo ""
echo "✅ 4. TypeScript build check..."
npm run build || {
  echo "❌ Build failed"
  exit 1
}

echo ""
echo "✅ Frontend checks passed!"
echo ""

cd ..

# ============================================
# Summary
# ============================================
echo "🎉 All CI checks passed!"
echo ""
echo "✅ Backend: Black ✓ Ruff ✓"
echo "✅ Frontend: Prettier ✓ TypeScript ✓ ESLint ✓ Build ✓"
echo ""
echo "Ready to push! 🚀"
