# Pre-Commit Hooks - Quick Reference

## 🚀 Quick Start

```bash
# Install hooks (one-time setup)
make pre-commit-install
# or
bash scripts/setup-pre-commit.sh
```

## 📋 Common Commands

| Command                      | Description                     |
| ---------------------------- | ------------------------------- |
| `make pre-commit-run`        | Run all hooks on all files      |
| `make pre-commit-update`     | Update hooks to latest versions |
| `make pre-commit-clean`      | Clean cache and reinstall       |
| `pre-commit run --all-files` | Run all hooks manually          |
| `pre-commit run <hook-id>`   | Run specific hook               |

## 🔍 Available Hooks

### General

- `trailing-whitespace` - Remove trailing whitespace
- `end-of-file-fixer` - Ensure files end with newline
- `check-yaml` - Validate YAML syntax
- `check-json` - Validate JSON syntax
- `check-merge-conflict` - Detect merge conflicts
- `check-added-large-files` - Prevent large files

### Backend (Python)

- `black` - Format Python code
- `ruff` - Lint Python code (includes complexity checks)
- `mypy` - Type check Python code

### Frontend (TypeScript/JavaScript)

- `prettier` - Format JS/TS code
- `eslint` - Lint JS/TS code (includes complexity checks)
- `tsc` - Type check TypeScript code

## 🎯 Complexity Limits

### Backend (Python)

- Max branches: **12**
- Max statements: **50**
- Max arguments: **6**
- Max returns: **6**

### Frontend (TypeScript)

- Cyclomatic complexity: **10**
- Max function lines: **50**
- Max nesting depth: **4**
- Max parameters: **4**

## 🔧 Troubleshooting

### Hooks are slow on first run

✅ Normal - environments are being cached. Subsequent runs will be fast.

### Hook fails with import errors

```bash
# Backend
cd backend && pip install -r requirements.txt

# Frontend
cd frontend && npm install
```

### Clear cache and reinstall

```bash
make pre-commit-clean
# or
pre-commit clean && pre-commit install
```

### Bypass hooks (emergency only)

```bash
git commit --no-verify -m "message"
```

⚠️ **Warning**: Only use in exceptional circumstances!

## 📚 Full Documentation

See `docs/PRE_COMMIT_HOOKS.md` for complete documentation.

## ✅ Requirements

- **Requirement 12.3**: Pre-commit hooks run quality checks on commit ✅
- **Requirement 12.4**: Maximum function complexity limits enforced ✅
