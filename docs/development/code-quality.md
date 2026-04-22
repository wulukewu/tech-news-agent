# Code Quality Standards

This document describes the code quality tools and standards enforced in the Tech News Agent project.

## Overview

The project enforces code quality through:

- **Frontend**: ESLint + Prettier for TypeScript/React
- **Backend**: Ruff + Black for Python
- **Pre-commit hooks**: Automated quality checks before commits
- **CI/CD**: Quality gates in GitHub Actions

## Frontend (TypeScript/React)

### ESLint Configuration

Location: `.eslintrc.json`

**Key Rules:**

- `complexity: 10` - Maximum cyclomatic complexity per function
- `max-lines-per-function: 50` - Maximum lines per function (excluding comments/blanks)
- `max-depth: 4` - Maximum nesting depth
- `max-params: 4` - Maximum function parameters
- `no-console: warn` - Warn on console statements
- `@typescript-eslint/no-unused-vars: error` - Error on unused variables
- `@typescript-eslint/no-explicit-any: warn` - Warn on explicit `any` types

**Running ESLint:**

```bash
# From frontend directory
npm run lint              # Check for issues
npm run lint:fix          # Auto-fix issues

# From project root
make lint-frontend        # Check frontend
make lint                 # Check both frontend and backend
```

### Prettier Configuration

Location: `.prettierrc`

**Settings:**

- Line width: 100 characters
- Tab width: 2 spaces
- Single quotes for strings
- Semicolons required
- Trailing commas (ES5)
- LF line endings

**Running Prettier:**

```bash
# From frontend directory
npm run format            # Format all files
npm run format:check      # Check formatting without changes

# From project root
make format-frontend      # Format frontend
make format               # Format both frontend and backend
```

### Ignored Files

Location: `.eslintignore`, `.prettierignore`

Ignored directories:

- `node_modules/`
- `.next/`, `out/`, `dist/`, `build/`
- `coverage/`
- Generated files (`*.d.ts`)
- Config files (`*.config.js`, `*.config.ts`)

## Backend (Python)

### Ruff Configuration

Location: `backend/pyproject.toml`

**Enabled Rule Sets:**

- `E` - pycodestyle errors
- `F` - pyflakes
- `I` - isort (import sorting)
- `N` - pep8-naming
- `W` - pycodestyle warnings
- `UP` - pyupgrade (modern Python syntax)
- `B` - flake8-bugbear (common bugs)
- `C4` - flake8-comprehensions
- `SIM` - flake8-simplify
- `PL` - pylint
- `RUF` - ruff-specific rules

**Complexity Limits:**

- Max arguments: 6
- Max branches: 12
- Max returns: 6
- Max statements: 50

**Running Ruff:**

```bash
# From backend directory
make lint                 # Check for issues
make lint-fix             # Auto-fix issues

# From project root
make lint-backend         # Check backend
make lint                 # Check both frontend and backend
```

### Black Configuration

Location: `backend/pyproject.toml`

**Settings:**

- Line length: 100 characters
- Target version: Python 3.11

**Running Black:**

```bash
# From backend directory
make format               # Format all files
make format-check         # Check formatting without changes

# From project root
make format-backend       # Format backend
make format               # Format both frontend and backend
```

## Root-Level Commands

The project root `Makefile` provides convenient commands for both frontend and backend:

```bash
# Linting
make lint                 # Lint both frontend and backend
make lint-frontend        # Lint frontend only
make lint-backend         # Lint backend only

# Formatting
make format               # Format both frontend and backend
make format-frontend      # Format frontend only
make format-backend       # Format backend only

# Combined checks
make format-check         # Check formatting for both
make check                # Run all quality checks (lint + format-check)
```

## Pre-commit Hooks

### Setup

Install pre-commit hooks to automatically check code quality before commits:

```bash
# Install pre-commit (if not already installed)
pip install pre-commit

# Install hooks
pre-commit install
```

### What Gets Checked

Pre-commit hooks will run:

1. **Frontend**: ESLint + Prettier
2. **Backend**: Ruff + Black
3. **General**: Trailing whitespace, file endings, YAML syntax

If any check fails, the commit will be blocked until issues are fixed.

## CI/CD Integration

### GitHub Actions

The CI pipeline (`.github/workflows/ci.yml`) runs:

1. **Linting**: ESLint (frontend) + Ruff (backend)
2. **Formatting**: Prettier (frontend) + Black (backend)
3. **Type checking**: TypeScript compiler
4. **Tests**: Jest (frontend) + pytest (backend)

All checks must pass before merging to main branch.

## IDE Integration

### VS Code

Recommended extensions (`.vscode/extensions.json`):

- ESLint (`dbaeumer.vscode-eslint`)
- Prettier (`esbenp.prettier-vscode`)
- Ruff (`charliermarsh.ruff`)

Recommended settings (`.vscode/settings.json`):

```json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.codeActionsOnSave": {
      "source.organizeImports": true,
      "source.fixAll": true
    }
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[typescriptreact]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```

### PyCharm / WebStorm

1. Enable ESLint: Settings → Languages & Frameworks → JavaScript → Code Quality Tools → ESLint
2. Enable Prettier: Settings → Languages & Frameworks → JavaScript → Prettier
3. Enable Ruff: Settings → Tools → External Tools (add Ruff)
4. Enable Black: Settings → Tools → Black

## Troubleshooting

### ESLint Issues

**Problem**: ESLint not finding configuration

```bash
# Solution: Ensure you're in the frontend directory or project root
cd frontend && npm run lint
```

**Problem**: ESLint cache issues

```bash
# Solution: Clear ESLint cache
rm -rf frontend/.eslintcache
```

### Prettier Issues

**Problem**: Prettier conflicts with ESLint

```bash
# Solution: Ensure eslint-config-prettier is installed
cd frontend && npm install --save-dev eslint-config-prettier
```

### Ruff Issues

**Problem**: Ruff not found

```bash
# Solution: Install Ruff
pip install ruff
```

**Problem**: Ruff configuration not loaded

```bash
# Solution: Ensure you're in the backend directory
cd backend && make lint
```

### Black Issues

**Problem**: Black not found

```bash
# Solution: Install Black
pip install black
```

## Best Practices

### Writing Compliant Code

1. **Keep functions small**: Max 50 lines, complexity ≤ 10
2. **Limit nesting**: Max depth of 4
3. **Limit parameters**: Max 4 parameters (use objects for more)
4. **Use TypeScript types**: Avoid `any`, use proper interfaces
5. **Handle errors properly**: Don't use bare `console.log` in production
6. **Write self-documenting code**: Clear names, minimal comments
7. **Follow import order**: Automatic with isort/ESLint

### Before Committing

```bash
# Run all checks
make check

# Or run individually
make lint
make format-check
```

### Fixing Issues

```bash
# Auto-fix what can be fixed
make format           # Format code
cd frontend && npm run lint:fix  # Fix ESLint issues
cd backend && make lint-fix      # Fix Ruff issues

# Then check again
make check
```

## References

- [ESLint Rules](https://eslint.org/docs/rules/)
- [TypeScript ESLint Rules](https://typescript-eslint.io/rules/)
- [Prettier Options](https://prettier.io/docs/en/options.html)
- [Ruff Rules](https://docs.astral.sh/ruff/rules/)
- [Black Documentation](https://black.readthedocs.io/)
