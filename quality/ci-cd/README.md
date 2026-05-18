# CI/CD Documentation

Documentation for the project's CI/CD pipeline.

## Guides

- [CI Guide](ci-guide.md) — Full CI/CD pipeline explanation, all checks, troubleshooting
- [Quick CI Guide](quick-ci-guide.md) — Pre-push checklist and common fixes
- [CI Analysis & Recommendations](ci-analysis-and-recommendations.md) — CI design analysis
- [Quality Gate Stabilization Plan](quality-gate-stabilization-plan.md) — Remediation plan for lint/test reliability

## Quick Commands

```bash
# Auto-fix formatting issues
./scripts/ci-fix.sh

# Run full CI check locally
./scripts/ci-local-test.sh
```

## CI Architecture

```
GitHub Actions CI
├── Backend Job (parallel)
│   ├── Black formatting
│   ├── Ruff linting
│   ├── mypy type checking
│   └── pytest + coverage
│
├── Frontend Job (parallel)
│   ├── Prettier formatting
│   ├── ESLint linting
│   ├── TypeScript type checking
│   ├── Vitest + coverage
│   └── Next.js build
│
└── Quality Gate
    └── All checks must pass
```

## Related

- [GitHub Actions config](../../.github/workflows/ci.yml)
- [Local test script](../../scripts/ci-local-test.sh)
- [Auto-fix script](../../scripts/ci-fix.sh)
