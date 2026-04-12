#!/bin/bash

# Setup Pre-Commit Hooks
# This script installs and configures pre-commit hooks for the Tech News Agent project

set -e

echo "🔧 Setting up pre-commit hooks..."

# Check if pre-commit is installed
if ! command -v pre-commit &> /dev/null; then
    echo "❌ pre-commit is not installed"
    echo "📦 Installing pre-commit..."

    # Try to install with pip
    if command -v pip3 &> /dev/null; then
        pip3 install pre-commit
    elif command -v pip &> /dev/null; then
        pip install pre-commit
    else
        echo "❌ pip is not available. Please install Python and pip first."
        exit 1
    fi
fi

echo "✅ pre-commit is installed (version: $(pre-commit --version))"

# Install the git hooks
echo "📝 Installing git hooks..."
pre-commit install

echo "✅ Git hooks installed successfully"

# Install hook environments (optional but recommended)
echo "🔄 Installing hook environments (this may take a few minutes)..."
pre-commit install-hooks

echo ""
echo "✅ Pre-commit hooks setup complete!"
echo ""
echo "📚 Documentation: docs/PRE_COMMIT_HOOKS.md"
echo ""
echo "🚀 Quick commands:"
echo "  - Run all hooks:     pre-commit run --all-files"
echo "  - Run specific hook: pre-commit run <hook-id> --all-files"
echo "  - Update hooks:      pre-commit autoupdate"
echo ""
echo "💡 Hooks will now run automatically before each commit"
