# Quick CI Guide

## 🚀 Before You Push

Run this command to verify all CI checks will pass:

```bash
./scripts/ci-local-test.sh
```

This runs the same major checks used in GitHub Actions, so you can catch issues before pushing.

## 🔧 Quick Fixes

### Fix TypeScript Errors

```bash
cd frontend
npm run type-check
```

### Fix Linting Issues

```bash
# Frontend
cd frontend
npm run lint:fix

# Backend
cd backend
ruff check --fix app/ tests/
```

### Fix Formatting

```bash
# Frontend
cd frontend
npm run format

# Backend
cd backend
black app/ tests/
```

### Run Tests

```bash
# Frontend
cd frontend
npm run test:gate           # blocking (unit)
npm run test:extended       # non-blocking (integration + property)

# Backend
cd backend
make test
```

## 📊 CI Workflow

The CI runs these checks in order:

1. **Backend Quality** → Black, Ruff, mypy
2. **Backend Tests (blocking)** → pytest
3. **Frontend Quality** → Prettier, ESLint, TypeScript
4. **Frontend Tests (blocking)** → `npm run test:gate` (unit)
5. **Frontend Extended Tests (non-blocking)** → `npm run test:extended` (integration + property)
6. **Quality Gate** → Blocking checks must pass

## ❌ Common Errors

### "Property 'X' does not exist on type 'Y'"

**Fix**: Add the missing property to the type definition in `frontend/types/`

### "Coverage is below X% threshold"

**Fix**: Add tests or adjust threshold in `.github/workflows/ci.yml`

### "Black would reformat"

**Fix**: Run `black app/ tests/` in backend directory

### "ESLint errors"

**Fix**: Run `npm run lint:fix` in frontend directory

## 📝 CI Configuration

- **File**: `.github/workflows/ci.yml`
- **Blocking frontend test command**: `npm run test:gate`
- **Non-blocking frontend test command**: `npm run test:extended`
- **Backend local quality command**: `make -C backend lint`

## 🔍 View CI Results

After pushing, check CI status at:

- GitHub Actions tab in your repository
- Or click the status badge in the PR

## 💡 Tips

1. Run `./scripts/ci-local-test.sh` before every push
2. Fix linting/formatting issues first (they're easiest)
3. Then fix TypeScript errors
4. Then fix blocking tests (`test:gate`)
5. Treat `test:extended` failures as technical debt and track them

## 🆘 Need Help?

- Check `docs/ci-fixes.md` for detailed troubleshooting
- Review test files in `backend/tests/` and `frontend/__tests__/`
- Ask the team if you're stuck!
