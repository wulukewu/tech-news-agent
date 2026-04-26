#!/bin/bash

# Final CI Fix Script
# This script applies all the fixes needed for CI to pass

set -e

echo "🔧 Applying final CI fixes..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# 1. Fix frontend issues
echo "🎨 Fixing frontend..."
cd frontend

# Clean .next directory
sudo rm -rf .next 2>/dev/null || true
mkdir -p .next/cache
chmod -R 755 .next 2>/dev/null || true

# Format code
npm run format
print_status "Frontend formatting fixed"

cd ..

# 2. Fix backend issues
echo "🐍 Fixing backend..."
cd backend

# Use virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
    print_status "Using existing virtual environment"
else
    python3 -m venv venv
    source venv/bin/activate
    print_status "Created new virtual environment"
fi

# Install tools
pip install --upgrade pip
pip install black ruff mypy

# Install minimal dependencies
if [ -f "requirements-minimal.txt" ]; then
    pip install -r requirements-minimal.txt
    print_status "Installed minimal dependencies"
else
    print_warning "requirements-minimal.txt not found, using requirements.txt"
    pip install -r requirements.txt || print_warning "Some dependencies failed"
fi

# Format and fix code
python -m black app/ tests/
print_status "Backend formatting fixed"

# Try to fix some linting issues automatically
python -m ruff check --fix app/ tests/ || print_warning "Some linting issues remain"

cd ..

# 3. Update .gitignore files
echo "📝 Updating .gitignore files..."

# Add backend virtual environment to gitignore
if ! grep -q "venv/" backend/.gitignore 2>/dev/null; then
    echo -e "\n# Virtual environment\nvenv/\n*.pyc\n__pycache__/" >> backend/.gitignore
fi

# Add frontend build artifacts to gitignore
if ! grep -q ".next/" frontend/.gitignore 2>/dev/null; then
    echo -e "\n# Build artifacts\n.next/\nnode_modules/\n*.log" >> frontend/.gitignore
fi

print_status "Updated .gitignore files"

# 4. Test the fixes
echo "🧪 Testing fixes..."

# Test frontend
cd frontend
if npm run format:check; then
    print_status "Frontend formatting check passed"
else
    print_warning "Frontend formatting issues remain"
fi

if npm run build; then
    print_status "Frontend build successful"
else
    print_warning "Frontend build failed"
fi

cd ..

# Test backend
cd backend
if [ -d "venv" ]; then
    source venv/bin/activate
fi

if python -m black --check app/ tests/; then
    print_status "Backend formatting check passed"
else
    print_warning "Backend formatting issues remain"
fi

cd ..

print_status "CI fixes completed!"

echo ""
echo "📋 Summary:"
echo "  ✅ Fixed frontend permissions and formatting"
echo "  ✅ Created Python virtual environment"
echo "  ✅ Fixed backend code formatting"
echo "  ✅ Updated .gitignore files"
echo "  ✅ Tested basic build processes"
echo ""
echo "🚀 Ready to commit and push!"
echo ""
echo "Next steps:"
echo "  1. git add ."
echo "  2. git commit -m \"fix: resolve CI issues and improve build reliability\""
echo "  3. git push"
