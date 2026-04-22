# Quick Start: Code Quality Tools

## TL;DR

```bash
# Check everything
make check

# Fix what can be auto-fixed
make format
cd frontend && npm run lint:fix
cd backend && make lint-fix
```

## Frontend (TypeScript/React)

### Check

```bash
cd frontend
npm run lint              # ESLint
npm run format:check      # Prettier
```

### Fix

```bash
cd frontend
npm run lint:fix          # Auto-fix ESLint issues
npm run format            # Auto-format with Prettier
```

## Backend (Python)

### Check

```bash
cd backend
make lint                 # Ruff
make format-check         # Black + Ruff
```

### Fix

```bash
cd backend
make lint-fix             # Auto-fix Ruff issues
make format               # Auto-format with Black
```

## Root Commands (Both Frontend + Backend)

### Check

```bash
make lint                 # Lint both
make format-check         # Check formatting both
make check                # All checks
```

### Fix

```bash
make format               # Format both
```

## Key Rules

### Frontend

- Max function complexity: 10
- Max function lines: 50
- Max nesting depth: 4
- Max parameters: 4
- No `console.log` in production
- No `any` types (warn)

### Backend

- Max arguments: 6
- Max branches: 12
- Max returns: 6
- Max statements: 50
- Use modern Python syntax
- Imports must be sorted

## Common Issues

### "Function too complex"

→ Break into smaller functions

### "Function too long"

→ Extract logic into helper functions

### "Too many parameters"

→ Use objects/dataclasses

### "Unexpected console statement"

→ Use proper logging instead

### "Import block unsorted"

→ Run `make format` in backend

## Pre-commit Setup

```bash
pip install pre-commit
pre-commit install
```

Now quality checks run automatically before each commit!

## IDE Setup

### VS Code

Install extensions:

- ESLint
- Prettier
- Ruff

Enable format on save in settings.

### PyCharm/WebStorm

Enable ESLint, Prettier, Ruff, and Black in settings.

## More Details

See [CODE_QUALITY.md](./CODE_QUALITY.md) for comprehensive documentation.
