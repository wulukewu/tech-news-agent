# Pre-Commit Hooks Setup

This document describes the pre-commit hooks configuration for the Tech News Agent project.

## Overview

Pre-commit hooks automatically run quality checks before each commit, ensuring code quality standards are enforced across the codebase. This helps catch issues early and maintains consistency.

## Installation

Pre-commit hooks are automatically installed when you run the project setup. To manually install or reinstall:

```bash
# Install pre-commit (if not already installed)
pip install pre-commit

# Install the git hooks
pre-commit install
```

## Configured Hooks

### General File Checks

- **trailing-whitespace**: Removes trailing whitespace from all files
- **end-of-file-fixer**: Ensures files end with a newline
- **check-yaml**: Validates YAML file syntax
- **check-json**: Validates JSON file syntax
- **check-added-large-files**: Prevents committing large files
- **check-merge-conflict**: Detects merge conflict markers

### Backend (Python)

#### 1. Black - Code Formatting

- **Purpose**: Enforces consistent Python code formatting
- **Configuration**: `backend/pyproject.toml`
- **Line length**: 100 characters
- **Target**: Python 3.11

#### 2. Ruff - Linting & Complexity Checks

- **Purpose**: Fast Python linter with complexity checks
- **Configuration**: `backend/pyproject.toml`
- **Includes**:
  - Pycodestyle errors (E) and warnings (W)
  - Pyflakes (F)
  - Import sorting (I)
  - PEP8 naming (N)
  - Pyupgrade (UP)
  - Bugbear (B)
  - Comprehensions (C4)
  - Simplify (SIM)
  - **Pylint rules (PL)** - includes complexity checks
  - Ruff-specific rules (RUF)

**Complexity Limits** (enforced via Pylint rules):

- Max arguments: 6
- Max branches: 12
- Max returns: 6
- Max statements: 50

#### 3. Mypy - Type Checking

- **Purpose**: Static type checking for Python
- **Configuration**: Inline in `.pre-commit-config.yaml`
- **Settings**:
  - Ignores missing imports
  - Python version: 3.11
  - Includes type stubs for: pydantic, fastapi, requests

### Frontend (TypeScript/JavaScript)

#### 1. Prettier - Code Formatting

- **Purpose**: Enforces consistent code formatting
- **Configuration**: `frontend/.prettierrc`
- **Settings**:
  - Single quotes
  - Semicolons
  - Line length: 100 characters
  - Tab width: 2 spaces

#### 2. ESLint - Linting & Complexity Checks

- **Purpose**: JavaScript/TypeScript linting with complexity checks
- **Configuration**: `frontend/.eslintrc.json`
- **Includes**:
  - Next.js core web vitals
  - TypeScript recommended rules
  - Prettier compatibility

**Complexity Limits**:

- **Cyclomatic complexity**: Max 10 (enforced via `complexity` rule)
- Max function lines: 50 (excluding blanks and comments)
- Max nesting depth: 4
- Max parameters: 4

#### 3. TypeScript - Type Checking

- **Purpose**: Static type checking for TypeScript
- **Configuration**: `frontend/tsconfig.json`
- **Command**: `npm run type-check`
- **Runs**: Only when TypeScript files change

## Running Hooks Manually

### Run all hooks on all files

```bash
pre-commit run --all-files
```

### Run specific hook

```bash
pre-commit run <hook-id> --all-files
```

Examples:

```bash
pre-commit run black --all-files
pre-commit run ruff --all-files
pre-commit run eslint --all-files
pre-commit run prettier --all-files
```

### Run hooks on specific files

```bash
pre-commit run --files backend/app/main.py
pre-commit run --files frontend/app/page.tsx
```

## Bypassing Hooks (Not Recommended)

In rare cases where you need to bypass pre-commit hooks:

```bash
git commit --no-verify -m "commit message"
```

**Warning**: Only use this in exceptional circumstances. Bypassing hooks can introduce code quality issues.

## Updating Hooks

To update all hooks to their latest versions:

```bash
pre-commit autoupdate
```

## Troubleshooting

### Hooks are slow

Pre-commit caches environments. First run is slow, subsequent runs are fast.

### Hook fails with import errors

For Python hooks, ensure your virtual environment has all dependencies:

```bash
cd backend
pip install -r requirements.txt
```

For frontend hooks, ensure node modules are installed:

```bash
cd frontend
npm install
```

### Clearing pre-commit cache

If hooks behave unexpectedly:

```bash
pre-commit clean
pre-commit install
```

### TypeScript hook fails

Ensure the frontend builds successfully:

```bash
cd frontend
npm run type-check
```

## CI Integration

Pre-commit hooks are also run in the CI pipeline (GitHub Actions) to ensure all commits meet quality standards, even if hooks were bypassed locally.

## Requirements Validation

This pre-commit setup validates:

- **Requirement 12.3**: Pre-commit hooks run quality checks on commit
- **Requirement 12.4**: Maximum function complexity limits are enforced
  - Backend: Max 12 branches, 50 statements (Ruff/Pylint)
  - Frontend: Max cyclomatic complexity 10 (ESLint)

## Additional Resources

- [Pre-commit documentation](https://pre-commit.com/)
- [Black documentation](https://black.readthedocs.io/)
- [Ruff documentation](https://docs.astral.sh/ruff/)
- [ESLint complexity rule](https://eslint.org/docs/latest/rules/complexity)
- [Mypy documentation](https://mypy.readthedocs.io/)
