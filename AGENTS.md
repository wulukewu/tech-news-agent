# AGENTS.md

Guidelines for AI agents working on this codebase.

## Database Schema

`backend/scripts/init_complete.sql` is the **single source of truth** for the database schema.

**Any schema change MUST also update `init_complete.sql`:**
- Add/drop table → add/remove the `CREATE TABLE IF NOT EXISTS` block
- Add/drop/alter column → update the column definition in place
- Add/remove index → add/remove `CREATE INDEX IF NOT EXISTS`
- Add/update function or trigger → update the relevant block

Do **not** append `ALTER TABLE` statements to `init_complete.sql`. Keep it as a clean schema definition, not a migration log.

After updating, verify: a fresh Supabase project running only `init_complete.sql` should produce the same schema as production.

---

## Documentation

All `.md` files must go under `docs/` in the appropriate subfolder. Do not create markdown files in the project root or scattered in source directories.

**Root directory exceptions** (only these are allowed at root):
`README.md`, `README_zh.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `LICENSE`, `CODE_OF_CONDUCT.md`, `.gitignore`, config files (e.g. `package.json`, `requirements.txt`, `Dockerfile`)

**File naming:** use kebab-case English names, e.g. `api-authentication.md`.

When updating `README.md`, also update `README_zh.md` to keep them in sync.

---

## Code Standards

- **Python:** follow PEP 8, use type hints, format with `ruff`, type-check with `mypy`, test with `pytest`
- **TypeScript:** use ESLint + Prettier, strict mode, functional React components with hooks

---

## Project Structure

```
backend/app/
├── api/          # REST endpoints
├── bot/          # Discord bot
├── services/     # Service layer (mixin pattern)
├── qa_agent/     # QA subsystem
├── repositories/ # Data access
├── schemas/      # Pydantic models
└── tasks/        # APScheduler jobs

frontend/
├── app/          # Next.js app router
├── features/     # Feature-sliced components
├── components/   # Shared UI
└── lib/          # API client, hooks, utils
```

---

## Running Checks

```bash
./scripts/ci-fix.sh          # auto-fix formatting/linting
./scripts/ci-local-test.sh   # full CI check
```
