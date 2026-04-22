# Pre-commit Configuration

This document explains the pre-commit hooks configuration and recent adjustments.

## Overview

Pre-commit hooks run automatically before each commit to ensure code quality. The configuration is in `.pre-commit-config.yaml`.

## Hooks Enabled

### General File Checks

- Trailing whitespace removal
- End-of-file fixer
- YAML validation
- Large file detection
- Merge conflict detection
- JSON validation

### Backend (Python)

#### Black (Formatting)

- **Purpose**: Automatic code formatting
- **Files**: `backend/**/*.py`
- **Action**: Auto-fixes formatting issues

#### Ruff (Linting)

- **Purpose**: Fast Python linter (replaces flake8, isort, etc.)
- **Files**: `backend/**/*.py`
- **Action**: Auto-fixes common issues
- **Config**: `backend/pyproject.toml`

#### Mypy (Type Checking)

- **Purpose**: Static type checking
- **Files**: `backend/**/*.py`
- **Action**: Validates type annotations
- **Config**: Inline args in `.pre-commit-config.yaml`

### Frontend (TypeScript/React)

#### Prettier (Formatting)

- **Purpose**: Automatic code formatting
- **Files**: `frontend/**/*.{js,jsx,ts,tsx,json,css,md}`
- **Action**: Auto-fixes formatting issues

#### ESLint (Linting)

- **Purpose**: Code quality and style checking
- **Files**: `frontend/**/*.{js,jsx,ts,tsx}`
- **Action**: Auto-fixes common issues
- **Config**: `frontend/.eslintrc.json`

#### TypeScript (Type Checking)

- **Status**: ⚠️ Currently disabled
- **Reason**: Type migration in progress
- **Files**: `frontend/**/*.{ts,tsx}`
- **Action**: Will validate types when re-enabled

## Recent Changes (April 2026)

### ESLint Rule Adjustments

To allow the project to commit during refactoring, we've relaxed some rules:

**Changed from Error to Warning:**

- `@typescript-eslint/no-unused-vars`: error → warn
- `complexity`: error (max 10) → warn (max 15)
- `max-depth`: error → warn

**Increased Limits:**

- `max-lines-per-function`: 50 → 100 lines
- `max-params`: 4 → 5 parameters
- `complexity`: 10 → 15 cyclomatic complexity

**Added Rules:**

- `no-prototype-builtins`: warn
- `@typescript-eslint/no-var-requires`: warn
- `react-hooks/exhaustive-deps`: warn
- `react-hooks/rules-of-hooks`: error
- `react/no-unescaped-entities`: warn
- `react/display-name`: warn

### TypeScript Type Checking

**Temporarily disabled** to allow commits during type migration. Will be re-enabled once:

1. All type errors are fixed
2. API response types are standardized
3. Test mocks are updated

## Usage

### Install Pre-commit

```bash
# Install pre-commit tool
pip install pre-commit

# Or with homebrew
brew install pre-commit
```

### Setup Hooks

```bash
# Install git hooks
pre-commit install

# Run on all files (optional)
pre-commit run --all-files
```

### Skip Hooks (Emergency Only)

```bash
# Skip all hooks for one commit
git commit --no-verify -m "Emergency fix"

# Skip specific hook
SKIP=eslint git commit -m "Skip ESLint"
```

## Fixing Common Issues

### ESLint Warnings

**Too many lines in function:**

```typescript
// Before: 150 lines
function hugeFunction() {
  // ... lots of code
}

// After: Extract smaller functions
function hugeFunction() {
  const result1 = helperFunction1();
  const result2 = helperFunction2();
  return combineResults(result1, result2);
}
```

**High complexity:**

```typescript
// Before: Complexity 20
function complex(x) {
  if (x > 0) {
    if (x < 10) {
      if (x % 2 === 0) {
        // ... many nested conditions
      }
    }
  }
}

// After: Extract conditions
function complex(x) {
  if (!isValidRange(x)) return;
  if (!isEven(x)) return;
  // ... simpler logic
}
```

**Unused variables:**

```typescript
// Before
function example(req, res, ctx) {
  return res(ctx.json({ ok: true }));
}

// After: Prefix with underscore
function example(_req, res, ctx) {
  return res(ctx.json({ ok: true }));
}
```

### TypeScript Errors

**Type mismatches:**

```typescript
// Before
const items: Item[] = response.data.map((item) => ({
  id: item.id,
  // missing required fields
}));

// After: Include all required fields
const items: Item[] = response.data.map((item) => ({
  id: item.id,
  name: item.name,
  createdAt: item.created_at,
}));
```

**Missing properties:**

```typescript
// Before
interface User {
  id: string;
  name: string;
}

const user = { id: '1' }; // Error: missing 'name'

// After
const user: User = { id: '1', name: 'John' };
```

## Configuration Files

### `.pre-commit-config.yaml`

Main configuration file defining all hooks and their settings.

### `frontend/.eslintrc.json`

ESLint rules for frontend code quality.

### `frontend/.prettierrc`

Prettier formatting rules for frontend.

### `backend/pyproject.toml`

Ruff and other Python tool configurations.

## Best Practices

1. **Run hooks before pushing**: `pre-commit run --all-files`
2. **Fix warnings gradually**: Don't ignore them forever
3. **Update dependencies**: Keep hook versions current
4. **Test locally**: Don't rely only on CI
5. **Document exceptions**: If you skip hooks, explain why

## Troubleshooting

### Hooks not running

```bash
# Reinstall hooks
pre-commit uninstall
pre-commit install
```

### Hook fails with "command not found"

```bash
# Update hook environments
pre-commit clean
pre-commit install --install-hooks
```

### ESLint fails with module errors

```bash
# Reinstall frontend dependencies
cd frontend
npm install
```

### Mypy fails with import errors

```bash
# Install backend dependencies
cd backend
pip install -r requirements-dev.txt
```

## Future Improvements

1. **Re-enable TypeScript checking** once type migration is complete
2. **Gradually tighten ESLint rules** as code quality improves
3. **Add commit message linting** (commitlint)
4. **Add security scanning** (bandit for Python, npm audit for Node)
5. **Add test coverage checks** (pytest-cov, jest coverage)

## Related Documentation

- [Code Quality Guide](./CODE_QUALITY.md)
- [Development Workflows](./DEVELOPMENT_WORKFLOWS.md)
- [Testing Guide](./TESTING.md)

---

**Last Updated**: April 12, 2026
**Status**: Active with relaxed rules during refactoring
