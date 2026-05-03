# Deployment Guide

## 1. Prerequisites

### Accounts Required

- **Supabase** — [supabase.com](https://supabase.com) (database + pgvector)
- **Groq** — [console.groq.com](https://console.groq.com) (LLM API)
- **Discord** — [discord.com/developers](https://discord.com/developers/applications) (OAuth + bot)
- **Netlify** or **Vercel** — frontend hosting
- **Render** or **Railway** — backend hosting

### Software Required

- Docker + Docker Compose
- Node.js >= 18
- Python >= 3.11

---

## 2. Environment Configuration

Copy `.env.example` to `.env` and fill in the values:

```bash
cp .env.example .env
```

### Required Variables

```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key

# Groq AI
GROQ_API_KEY=your-groq-api-key

# JWT
JWT_SECRET_KEY=your-secret-key   # generate: openssl rand -hex 32
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Discord OAuth (web login)
DISCORD_CLIENT_ID=your-client-id
DISCORD_CLIENT_SECRET=your-client-secret
DISCORD_REDIRECT_URI=http://localhost:3000/auth/callback

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Optional Variables

```bash
# Discord Bot
DISCORD_TOKEN=your-bot-token
DISCORD_CHANNEL_ID=your-channel-id

# Scheduler
SCHEDULER_CRON=0 */6 * * *
SCHEDULER_TIMEZONE=Asia/Taipei
TIMEZONE=Asia/Taipei
```

---

## 3. Database Setup

The project uses Supabase (PostgreSQL + pgvector). There is no Alembic — all schema management is done via plain SQL files.

### Initial Setup

1. Open your Supabase project → **SQL Editor**
2. Run the full contents of `backend/scripts/init_supabase.sql`
3. Verify tables were created in the **Table Editor**

### Applying Migrations

For subsequent schema changes, run migration files in order:

**Option A — Supabase SQL Editor (manual):**

Open each file in `backend/scripts/migrations/` and run them in the SQL Editor in order.

**Option B — Migration script:**

```bash
python3 scripts/run_migrations.py
```

---

## 4. Development Deployment

### Docker Compose (Recommended)

```bash
# Start all services with hot reloading
make dev
# or
docker-compose up -d

# View logs
make logs-dev
# or
docker-compose logs -f

# Stop and clean up
make clean
```

Services started:
- Backend (FastAPI + Discord bot): `http://localhost:8000`
- Frontend (Next.js): `http://localhost:3000`
- API docs: `http://localhost:8000/docs`

### Local (Without Docker)

```bash
# Backend
cd backend
pip install -r requirements.txt
python -m app.main

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

---

## 5. Production Deployment

### Docker Compose (Self-Hosted)

```bash
# Start production stack
make prod
# or
docker-compose -f docker-compose.prod.yml up -d

# View logs
make logs-prod
# or
docker-compose -f docker-compose.prod.yml logs -f
```

Update `.env` with production values before starting:
- Set `DISCORD_REDIRECT_URI` to your production frontend URL
- Set `NEXT_PUBLIC_API_URL` to your production backend URL

### Frontend — Netlify

See [netlify-frontend.md](./netlify-frontend.md) for full setup.

Quick steps:
1. Connect your GitHub repo to Netlify
2. Set build command: `npm run build`
3. Set publish directory: `.next` (or `out` for static export)
4. Add all `NEXT_PUBLIC_*` environment variables in Netlify dashboard

### Backend — Render

See [render-deployment.md](./render-deployment.md) for full setup.

Quick steps:
1. Create a new **Web Service** on Render pointing to your repo
2. Set start command: `python -m app.main`
3. Add all required environment variables in Render dashboard
4. Set `DISCORD_REDIRECT_URI` and `NEXT_PUBLIC_API_URL` to production URLs

---

## 6. Health Checks

```bash
# Application health
GET /health

# Scheduler health
GET /health/scheduler
```

Example:

```bash
curl https://your-backend-url/health
curl https://your-backend-url/health/scheduler
```

Both endpoints return JSON with status information. Use these for uptime monitoring and deployment verification.

---

## 7. Troubleshooting

**Missing tables / database errors:**

```bash
cd backend
python3 scripts/verify_bot_health.py
python3 scripts/apply_missing_migration.py
```

**Discord bot not responding:**
- Verify `DISCORD_TOKEN` is set and valid
- Check bot has correct permissions and OAuth scopes in the Developer Portal

**Articles not fetching:**
- Check scheduler logs: `make logs-dev` or `docker-compose logs -f backend`
- Verify RSS feed URLs are reachable
- Confirm `GROQ_API_KEY` is valid and has available credits

**Frontend can't reach backend:**
- Confirm `NEXT_PUBLIC_API_URL` points to the correct backend URL
- Check CORS settings if frontend and backend are on different domains

**Auth callback errors:**
- Ensure `DISCORD_REDIRECT_URI` exactly matches the URI registered in the Discord Developer Portal
