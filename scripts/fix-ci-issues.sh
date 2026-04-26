#!/bin/bash

# Fix CI Issues Script
# This script fixes common CI/CD issues in the tech-news-agent project

set -e

echo "🔧 Fixing CI Issues..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if we're in the project root
if [ ! -f "package.json" ] && [ ! -f "backend/requirements.txt" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

print_status "Starting CI fixes..."

# 1. Fix frontend permissions and dependencies
echo "🎨 Fixing frontend issues..."
cd frontend

# Clean and recreate .next directory with correct permissions
if [ -d ".next" ]; then
    rm -rf .next
fi
mkdir -p .next/cache
chmod -R 755 .next

# Fix node_modules permissions if they exist
if [ -d "node_modules" ]; then
    print_warning "Fixing node_modules permissions..."
    find node_modules -type d -exec chmod 755 {} \; 2>/dev/null || true
fi

# Install dependencies
print_status "Installing frontend dependencies..."
npm ci --prefer-offline --no-audit

# Fix formatting issues
print_status "Fixing code formatting..."
npm run format

cd ..

# 2. Fix backend issues
echo "🐍 Fixing backend issues..."
cd backend

# Check if virtual environment exists, create if not
if [ ! -d "venv" ]; then
    print_status "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip and install dependencies
print_status "Installing backend dependencies..."
pip install --upgrade pip
pip install black ruff mypy

# Install project dependencies
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
fi

if [ -f "requirements-dev.txt" ]; then
    pip install -r requirements-dev.txt
fi

# Fix code formatting
print_status "Fixing Python code formatting..."
python -m black app/ tests/ || print_warning "Some files couldn't be formatted"

# Fix linting issues where possible
print_status "Running Ruff auto-fixes..."
python -m ruff check --fix app/ tests/ || print_warning "Some linting issues remain"

cd ..

# 3. Create .gitignore entries for common CI issues
echo "📝 Updating .gitignore..."

# Frontend .gitignore additions
if [ ! -f "frontend/.gitignore" ]; then
    touch frontend/.gitignore
fi

cat >> frontend/.gitignore << 'EOF'

# CI/CD specific
.next/
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Testing
coverage/
.nyc_output/

# Environment
.env.local
.env.development.local
.env.test.local
.env.production.local
EOF

# Backend .gitignore additions
if [ ! -f "backend/.gitignore" ]; then
    touch backend/.gitignore
fi

cat >> backend/.gitignore << 'EOF'

# Virtual environment
venv/
env/
.venv/

# Python cache
__pycache__/
*.pyc
*.pyo
*.pyd
.Python

# Testing
.pytest_cache/
.coverage
htmlcov/

# IDE
.vscode/
.idea/
EOF

# 4. Create a pre-commit script
echo "🔄 Creating pre-commit script..."
cat > scripts/pre-commit.sh << 'EOF'
#!/bin/bash

# Pre-commit script to run before each commit
set -e

echo "🔍 Running pre-commit checks..."

# Frontend checks
echo "Checking frontend..."
cd frontend
npm run format:check || (echo "❌ Format issues found. Run 'npm run format'" && exit 1)
npm run lint || (echo "❌ Lint issues found. Run 'npm run lint:fix'" && exit 1)
cd ..

# Backend checks
echo "Checking backend..."
cd backend
if [ -d "venv" ]; then
    source venv/bin/activate
fi

python -m black --check app/ tests/ || (echo "❌ Format issues found. Run 'black app/ tests/'" && exit 1)
python -m ruff check app/ tests/ || (echo "❌ Lint issues found. Run 'ruff check --fix app/ tests/'" && exit 1)
cd ..

echo "✅ All pre-commit checks passed!"
EOF

chmod +x scripts/pre-commit.sh

# 5. Update package.json scripts for better CI
echo "📦 Updating package.json scripts..."
cd frontend

# Create a temporary package.json with updated scripts
node -e "
const pkg = require('./package.json');
pkg.scripts = {
  ...pkg.scripts,
  'ci:format': 'prettier --check \"**/*.{ts,tsx,js,jsx,json,css,md}\"',
  'ci:lint': 'next lint --max-warnings 0',
  'ci:build': 'NODE_OPTIONS=\"--max-old-space-size=4096\" next build',
  'ci:test': 'vitest run --reporter=verbose',
  'fix:all': 'npm run format && npm run lint:fix'
};
require('fs').writeFileSync('./package.json', JSON.stringify(pkg, null, 2) + '\n');
"

cd ..

print_status "CI fixes completed!"

echo ""
echo "📋 Summary of fixes applied:"
echo "  ✅ Fixed frontend permissions and dependencies"
echo "  ✅ Created Python virtual environment"
echo "  ✅ Fixed code formatting (Black, Prettier)"
echo "  ✅ Applied auto-fixes for linting issues"
echo "  ✅ Updated .gitignore files"
echo "  ✅ Created pre-commit script"
echo "  ✅ Updated package.json with CI-friendly scripts"
echo ""
echo "🚀 Next steps:"
echo "  1. Run 'git add .' to stage the changes"
echo "  2. Run 'git commit -m \"fix: resolve CI issues and improve build process\"'"
echo "  3. Push to trigger CI and verify fixes"
echo ""
echo "💡 To run pre-commit checks manually: ./scripts/pre-commit.sh"
