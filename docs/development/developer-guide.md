# Developer Guide

## Table of Contents

1. [Prerequisites & Setup](#1-prerequisites--setup)
2. [Project Structure](#2-project-structure)
3. [Development Workflow](#3-development-workflow)
4. [Code Quality](#4-code-quality)
5. [Testing](#5-testing)
6. [Adding New Features](#6-adding-new-features)
7. [Key Conventions](#7-key-conventions)

---

## 1. Prerequisites & Setup

### Requirements

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose (recommended)
- A Supabase project with pgvector enabled
- Groq API key
- Discord application (bot token + OAuth credentials)

### Initial Setup

```bash
# Clone and enter the repo
git clone https://github.com/yourusername/tech-news-agent.git
cd tech-news-agent

# Copy and fill in environment variables
cp .env.example .env
# Edit .env — see Environment Variables section below

# Initialize the database
# Run backend/scripts/init_supabase.sql in the Supabase SQL Editor
```

### Environment Variables

| Variable | Required | Description |
|---|---|---|
| `SUPABASE_URL` | ✅ | Supabase project URL |
| `SUPABASE_KEY` | ✅ | Supabase service role key |
| `GROQ_API_KEY` | ✅ | Groq API key |
| `JWT_SECRET_KEY` | ✅ | JWT signing secret (`openssl rand -hex 32`) |
| `JWT_ALGORITHM` | ✅ | `HS256` |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | ✅ | e.g. `30` |
| `DISCORD_CLIENT_ID` | ✅ | Discord OAuth client ID |
| `DISCORD_CLIENT_SECRET` | ✅ | Discord OAuth client secret |
| `DISCORD_REDIRECT_URI` | ✅ | e.g. `http://localhost:3000/auth/callback` |
| `NEXT_PUBLIC_API_URL` | ✅ | e.g. `http://localhost:8000` |
| `DISCORD_TOKEN` | optional | Bot token (required for Discord bot) |
| `DISCORD_CHANNEL_ID` | optional | Default channel for bot announcements |
| `SCHEDULER_CRON` | optional | Default: `0 */6 * * *` |
| `SCHEDULER_TIMEZONE` | optional | Default: `Asia/Taipei` |
| `TIMEZONE` | optional | Default: `Asia/Taipei` |
| `RSS_FETCH_DAYS` | optional | Days of history to fetch (default: `7`) |
| `LOG_LEVEL` | optional | Default: `INFO` |

---

## 2. Project Structure

```
tech-news-agent/
├── backend/
│   ├── app/
│   │   ├── api/               # REST API endpoints (FastAPI routers)
│   │   │   ├── auth.py
│   │   │   ├── articles.py
│   │   │   ├── feeds.py
│   │   │   ├── reading_list.py
│   │   │   ├── qa.py
│   │   │   ├── conversations/
│   │   │   ├── notifications/
│   │   │   ├── learning_path/
│   │   │   └── ...
│   │   ├── bot/
│   │   │   ├── cogs/          # 13 Discord bot command cogs
│   │   │   └── client.py
│   │   ├── services/          # ~50 service files (mixin pattern)
│   │   │   └── _mixins/       # article, feed, reading_list, notification, user
│   │   ├── qa_agent/          # QA subsystem (vector search, conversation, learning)
│   │   ├── core/              # config, exceptions, logger, validators
│   │   ├── repositories/      # data access layer (Supabase queries)
│   │   ├── schemas/           # Pydantic models
│   │   └── tasks/             # APScheduler background jobs
│   ├── scripts/               # DB init, migrations, utilities
│   ├── tests/                 # pytest test suite
│   └── requirements.txt
│
├── frontend/
│   ├── app/                   # Next.js 14 App Router pages
│   │   ├── (public)/          # Unauthenticated routes
│   │   └── app/               # Authenticated routes
│   ├── features/              # Feature-sliced components
│   ├── components/            # Shared UI (shadcn/ui)
│   ├── lib/                   # API client, hooks, utils
│   ├── locales/               # i18n strings (EN/ZH)
│   └── package.json
│
├── docs/                      # All documentation
├── scripts/                   # Dev, CI, migration scripts
├── docker-compose.yml         # Development
├── docker-compose.prod.yml    # Production
└── Makefile
```

### Backend Layer Responsibilities

| Layer | Path | Responsibility |
|---|---|---|
| API | `app/api/` | HTTP request handling, auth, response shaping |
| Bot | `app/bot/cogs/` | Discord slash commands and interactions |
| Services | `app/services/` | Business logic, orchestration |
| Repositories | `app/repositories/` | All Supabase/DB queries |
| Schemas | `app/schemas/` | Pydantic request/response models |
| Tasks | `app/tasks/` | Scheduled background jobs |
| Core | `app/core/` | Config, logging, shared exceptions |

---

## 3. Development Workflow

### Option A: Docker Compose (Recommended)

```bash
# Development (hot reload)
make dev
# or
docker-compose up -d

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend

# Stop
docker-compose down
```

Access:
- Web: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Option B: Local Development

**Backend:**

```bash
cd backend
pip install -r requirements.txt
python -m app.main
```

**Frontend** (separate terminal):

```bash
cd frontend
npm install
npm run dev
```

### Pre-commit Hooks

Install once after cloning:

```bash
pip install pre-commit
pre-commit install
```

Hooks run automatically on `git commit`:
- `black` — Python formatting
- `ruff` — Python linting
- `prettier` — TypeScript/CSS formatting
- `eslint` — TypeScript linting
- Translation validation — ensures EN/ZH locale keys are in sync

---

## 4. Code Quality

### Backend Tools

| Tool | Purpose | Command |
|---|---|---|
| `ruff` | Linting + import sorting | `ruff check app/` |
| `black` | Formatting | `black app/` |
| `mypy` | Static type checking | `mypy app/` |

### Frontend Tools

| Tool | Purpose | Command |
|---|---|---|
| `eslint` | Linting | `npm run lint` |
| `prettier` | Formatting | `npm run format` |
| TypeScript | Type checking | `npm run type-check` |

### CI Scripts

```bash
# Auto-fix formatting and linting issues
./scripts/ci-fix.sh

# Full CI check (mirrors GitHub Actions — run before pushing)
./scripts/ci-local-test.sh
```

Always run `./scripts/ci-local-test.sh` before opening a PR.

### Python Code Standards

- Use type hints on all function signatures
- Write Google-style docstrings on public functions
- Follow PEP 8 (enforced by ruff/black)
- Handle exceptions explicitly — never silently swallow errors

```python
async def get_user_articles(user_id: str, limit: int = 20) -> list[ArticleSchema]:
    """Fetch articles for a user's subscribed feeds.

    Args:
        user_id: The user's UUID string.
        limit: Maximum number of articles to return.

    Returns:
        List of article schemas ordered by published_at desc.

    Raises:
        RepositoryError: If the database query fails.
    """
    return await self.article_repo.get_for_user(user_id, limit=limit)
```

---

## 5. Testing

### Backend

```bash
cd backend

# Run all tests
pytest -v

# With coverage report
pytest --cov=app --cov-report=html

# Property-based tests (Hypothesis profiles)
HYPOTHESIS_PROFILE=dev pytest tests/test_database_properties.py -v   # 10 examples (fast)
HYPOTHESIS_PROFILE=ci  pytest tests/test_database_properties.py -v   # 100 examples
```

Test structure:

```
backend/tests/
├── conftest.py
├── test_config.py
├── test_database_properties.py   # Hypothesis property tests
├── bot/
│   ├── utils/test_validators.py
│   └── test_performance.py
└── integration/
    └── test_multi_tenant_workflow.py
```

Test types:
- **Unit**: individual functions and validators
- **Property-based**: Hypothesis for invariants (e.g., rating always 1–5)
- **Integration**: full user journey across service + repository layers
- **Performance**: response time assertions for critical paths

### Frontend

```bash
cd frontend

# Unit tests (vitest)
npm test

# With coverage
npm run test:coverage

# E2E tests (Playwright)
npm run test:e2e
```

---

## 6. Adding New Features

### A. New API Endpoint

1. Create a router file in `backend/app/api/` (or add to an existing one):

```python
# backend/app/api/my_feature.py
from fastapi import APIRouter, Depends
from app.core.auth import get_current_user
from app.schemas.my_feature import MyFeatureResponse
from app.services.my_feature_service import MyFeatureService

router = APIRouter(prefix="/api/my-feature", tags=["my-feature"])

@router.get("/", response_model=MyFeatureResponse)
async def get_my_feature(current_user=Depends(get_current_user)):
    service = MyFeatureService()
    return await service.get(current_user["id"])
```

2. Register the router in `backend/app/main.py`:

```python
from app.api.my_feature import router as my_feature_router
app.include_router(my_feature_router)
```

3. Add Pydantic schemas in `backend/app/schemas/my_feature.py`.
4. Add repository methods in `backend/app/repositories/`.
5. Add service logic in `backend/app/services/`.
6. Write tests in `backend/tests/`.

### B. New Discord Bot Command

1. Create or add to a cog in `backend/app/bot/cogs/`:

```python
# backend/app/bot/cogs/my_commands.py
import discord
from discord.ext import commands
from discord import app_commands

class MyCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="my_command", description="Does something useful")
    async def my_command(self, interaction: discord.Interaction):
        await interaction.response.defer()
        # business logic here
        await interaction.followup.send("Done!")

async def setup(bot: commands.Bot):
    await bot.add_cog(MyCommands(bot))
```

2. Register the cog in `backend/app/bot/client.py` under the cog loading section.

3. Use `await interaction.response.defer()` for any operation that may take more than 3 seconds.

### C. New Frontend Page

1. Create the page directory under `frontend/app/app/my-page/`:

```
frontend/app/app/my-page/
├── page.tsx        # Page component
└── loading.tsx     # Optional loading UI
```

2. Add feature components in `frontend/features/my-feature/`:

```typescript
// frontend/features/my-feature/components/MyFeatureCard.tsx
interface MyFeatureCardProps {
  data: MyFeatureData;
}

export function MyFeatureCard({ data }: MyFeatureCardProps) {
  return <div>{data.title}</div>;
}
```

3. Add API calls in `frontend/lib/api/` and React Query hooks in `frontend/lib/hooks/`.

4. Add i18n strings to both `frontend/locales/en.json` and `frontend/locales/zh.json` (the pre-commit hook validates they stay in sync).

---

## 7. Key Conventions

### Git Commits

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Examples:
```
feat(api): add weekly insights endpoint
fix(bot): handle missing user profile gracefully
docs(dev): update developer guide
test(qa): add property tests for query processor
```

### Multi-Tenancy

Data isolation is enforced at the **repository layer**. Every query that touches user-owned data (reading list, subscriptions, notifications, conversations) must be scoped by `user_id`. Never fetch all rows and filter in Python.

```python
# ✅ Correct — scoped at query level
async def get_reading_list(self, user_id: str) -> list[ReadingListItem]:
    return await self.db.table("reading_list").select("*").eq("user_id", user_id).execute()

# ❌ Wrong — fetches all rows
async def get_reading_list(self) -> list[ReadingListItem]:
    all_items = await self.db.table("reading_list").select("*").execute()
    return [i for i in all_items if i["user_id"] == user_id]
```

### Service Mixin Pattern

Large services are split into mixins under `backend/app/services/_mixins/`. Each mixin handles one domain (articles, feeds, reading list, notifications, user). The main `SupabaseService` composes them via multiple inheritance.

When adding new service methods, place them in the appropriate mixin file rather than the main service class.

### Error Handling

Define domain-specific exceptions in `backend/app/core/exceptions.py`. Catch specific exceptions at the API/bot layer and return user-friendly messages.

```python
# In a cog or API handler
try:
    result = await service.do_something(user_id)
except RepositoryError as e:
    logger.error("DB error for user %s: %s", user_id, e, exc_info=True)
    await interaction.followup.send("Operation failed, please try again.", ephemeral=True)
```

### Database

- No local database, no Alembic migrations — all schema changes go through the Supabase SQL Editor.
- Migration scripts live in `backend/scripts/`.
- Use pgvector (`embedding VECTOR(1536)`) for semantic search on articles and conversations.

### Frontend Data Fetching

Use React Query for all server state. Define query keys centrally in `frontend/lib/queryKeys.ts` to avoid cache collisions.

```typescript
// ✅ Use React Query
const { data, isLoading } = useQuery({
  queryKey: queryKeys.readingList(userId),
  queryFn: () => api.readingList.getAll(),
});
```

### i18n

All user-facing strings must be in both `frontend/locales/en.json` and `frontend/locales/zh.json`. Use the `useTranslations` hook from `next-intl`. The pre-commit hook will reject commits where the two locale files have mismatched keys.

---

## References

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [discord.py Docs](https://discordpy.readthedocs.io/)
- [Supabase Docs](https://supabase.com/docs)
- [Groq API Docs](https://console.groq.com/docs)
- [Next.js 14 Docs](https://nextjs.org/docs)
- [shadcn/ui](https://ui.shadcn.com)
- [Hypothesis Docs](https://hypothesis.readthedocs.io/)
