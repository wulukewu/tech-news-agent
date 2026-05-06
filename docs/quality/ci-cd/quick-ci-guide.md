# Quick CI Guide

## 🚀 Before You Push

Run this command to verify all CI checks will pass:

```bash
./scripts/verify-ci.sh
```

This will run all the same checks that GitHub Actions runs, so you can catch issues before pushing.

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
npm run test:coverage -- --run

# Backend
cd backend
pytest
```

## 📊 CI Workflow

The CI runs these checks in order:

1. **Backend Quality** → Black, Ruff, mypy, complexity
2. **Backend Tests** → pytest with coverage (≥70%)
3. **Frontend Quality** → Prettier, ESLint, TypeScript, complexity
4. **Frontend Tests** → Vitest with coverage (≥70%)
5. **Quality Gate** → All checks must pass

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
- **Coverage Thresholds**: 70% for both backend and frontend
- **Test Timeout**: 300s for fast tests, 600s for full tests

## 🔍 View CI Results

After pushing, check CI status at:

- GitHub Actions tab in your repository
- Or click the status badge in the PR

## 💡 Tips

1. Run `./scripts/verify-ci.sh` before every push
2. Fix linting/formatting issues first (they're easiest)
3. Then fix TypeScript errors
4. Finally, ensure tests pass
5. Check coverage if tests pass but coverage is low

## 🆘 Need Help?

- Check `docs/ci-fixes.md` for detailed troubleshooting
- Review test files in `backend/tests/` and `frontend/__tests__/`
- Ask the team if you're stuck!
