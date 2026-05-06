# Troubleshooting Guide

This guide helps you diagnose and fix common issues in the Tech News Agent.

## Table of Contents

- [Quick Diagnostics](#quick-diagnostics)
- [Common Issues](#common-issues)
- [Database Issues](#database-issues)
- [Discord Bot Issues](#discord-bot-issues)
- [Frontend Issues](#frontend-issues)
- [Backend Issues](#backend-issues)
- [Docker Issues](#docker-issues)
- [Error Reference](#error-reference)
- [Getting Help](#getting-help)

---

## Quick Diagnostics

```bash
# Check all service status
make ps

# Check backend health
curl http://localhost:8000/health
curl http://localhost:8000/health/scheduler

# Check logs
make logs-dev       # development
make logs-prod      # production

# Check ports
lsof -i :3000
lsof -i :8000
```

---

## Common Issues

### 1. Missing Database Tables

**Symptoms:** `relation "X" does not exist`, 500 errors on API calls

**Solutions:**

Option A — Run the init SQL in Supabase SQL Editor:
```
Supabase Dashboard → SQL Editor → paste backend/scripts/init_supabase.sql → Run
```

Option B — Run the migration script:
```bash
python3 backend/scripts/apply_missing_migration.py
```

To verify the database state:
```bash
python3 backend/scripts/verify_bot_health.py
```

---

### 2. Discord Bot Not Responding

**Symptoms:** Bot is online but ignores commands, slash commands not registered

**Checklist:**
- `DISCORD_TOKEN` is set correctly in `.env`
- Bot has the required permissions in the Discord server (Send Messages, Use Slash Commands, Send Messages in Threads)
- OAuth scopes include `bot` and `applications.commands`
- Bot has been invited to the server with the correct permission integer

```bash
# Check token is loaded
docker-compose exec backend env | grep DISCORD_TOKEN

# Check bot logs
docker-compose logs backend | grep -i discord
```

---

### 3. Articles Not Fetching

**Symptoms:** No new articles appear, scheduler seems idle

**Checklist:**
1. Check scheduler health: `curl http://localhost:8000/health/scheduler`
2. Check backend logs for scheduler errors: `make logs-dev`
3. Verify RSS feed URLs are valid and reachable
4. Confirm `GROQ_API_KEY` is set and has remaining credits

```bash
# Manually trigger a fetch
curl -X POST http://localhost:8000/api/scheduler/trigger
# or via Discord: /trigger_fetch
```

---

### 4. Frontend Can't Connect to Backend

**Symptoms:** API calls fail, "Network Error", blank pages after login

**Solutions:**

```bash
# Verify the env var is set
grep NEXT_PUBLIC_API_URL .env

# Test backend is reachable
curl http://localhost:8000/health
```

- Ensure `NEXT_PUBLIC_API_URL=http://localhost:8000` in `.env`
- Check CORS config in the backend allows the frontend origin
- If running in Docker, use the service name: `http://backend:8000`

---

### 5. Authentication Failures

**Symptoms:** Login redirects fail, "Invalid token", 401 errors

**Checklist:**
- `DISCORD_CLIENT_ID` and `DISCORD_CLIENT_SECRET` match the Discord Developer Portal
- `DISCORD_REDIRECT_URI` matches exactly what is registered in the portal (e.g. `http://localhost:3000/auth/callback`)
- `JWT_SECRET_KEY` is set (generate with `openssl rand -hex 32`)

---

### 6. Port Conflicts

**Symptoms:** `address already in use`, services fail to start

```bash
# Find what's using the ports
lsof -i :3000
lsof -i :8000

# Kill the conflicting process
kill -9 $(lsof -t -i:3000)
kill -9 $(lsof -t -i:8000)
```

---

## Database Issues

The project uses **Supabase (cloud PostgreSQL)**. There is no local database and no Alembic. All migrations are SQL files.

### Running Migrations

```bash
# Option 1: Supabase SQL Editor (recommended)
# Paste backend/scripts/init_supabase.sql and run

# Option 2: Migration script
python3 backend/scripts/apply_missing_migration.py
```

### Connection Timeout / Auth Failure

```bash
# Verify credentials are set
grep SUPABASE .env

# Test connection manually
python3 -c "
from supabase import create_client
import os
c = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
print('Connected:', c.table('users').select('count').execute())
"

# Check Supabase project status
# Supabase Dashboard → Settings → General
```

- Use the **service role key** (not the anon key) for `SUPABASE_KEY`
- Check that RLS policies allow service role access

---

## Discord Bot Issues

### Bot Token Invalid

```bash
grep DISCORD_TOKEN .env
# Regenerate token at: Discord Developer Portal → Bot → Reset Token
```

### Slash Commands Not Appearing

Slash commands can take up to 1 hour to propagate globally. For instant registration, use guild-specific commands during development.

```bash
docker-compose logs backend | grep -i "command\|sync\|slash"
```

---

## Frontend Issues

### Build Failures

```bash
cd frontend
rm -rf node_modules .next
npm install
npm run build
```

### TypeScript Errors

```bash
cd frontend
npm run type-check
```

### Hydration Errors

Use `useEffect` for any browser-only code (e.g. `localStorage`, `Date`):

```typescript
const [mounted, setMounted] = useState(false);
useEffect(() => setMounted(true), []);
if (!mounted) return null;
```

---

## Backend Issues

### Import / Dependency Errors

```bash
docker-compose exec backend pip list
docker-compose build backend --no-cache
```

### Scheduler Not Running

```bash
curl http://localhost:8000/health/scheduler
make logs-dev | grep -i scheduler
```

Set `LOG_LEVEL=DEBUG` in `.env` for verbose output.

---

## Docker Issues

### Services Won't Start

```bash
# Check logs for the failing service
docker-compose logs backend
docker-compose logs frontend

# Clean up and rebuild
make clean
make dev
```

### Out of Disk Space

```bash
docker system df
docker system prune -a -f
docker volume prune -f
```

### Makefile Reference

| Command | Description |
|---------|-------------|
| `make dev` | Start development environment |
| `make prod` | Start production environment |
| `make logs-dev` | Tail development logs |
| `make logs-prod` | Tail production logs |
| `make clean` | Stop and remove containers/volumes |
| `make ps` | Show running services |

---

## Error Reference

| Error | Likely Cause | Fix |
|-------|-------------|-----|
| `relation "X" does not exist` | Missing DB table | Run `init_supabase.sql` or `apply_missing_migration.py` |
| `401 Unauthorized` | Bad/expired JWT or Discord token | Re-login or check `JWT_SECRET_KEY` |
| `403 Forbidden` | Missing permissions or RLS policy | Check Supabase RLS, bot permissions |
| `404 Not Found` | Wrong endpoint or missing resource | Check URL, verify data exists |
| `500 Internal Server Error` | Unhandled exception | Check `make logs-dev` |
| `Port already in use` | Port conflict | `kill -9 $(lsof -t -i:PORT)` |
| `GROQ API error` | No credits or invalid key | Check [console.groq.com](https://console.groq.com) |

---

## Getting Help

### Collect Debug Info

```bash
# Service status
make ps

# Recent logs (sanitize before sharing)
docker-compose logs --tail=100

# Config check (hides values)
cat .env | sed 's/=.*/=***/'

# System info
docker --version && docker-compose --version
```

### Useful Scripts

```bash
python3 backend/scripts/verify_bot_health.py      # Check bot + DB health
python3 backend/scripts/apply_missing_migration.py # Apply missing DB migrations
```

### Emergency Reset

```bash
make clean
docker system prune -f
cp .env.example .env   # re-fill credentials
make dev
```

### Documentation

- [Quick Start Guide](../guides/quick-start.md)
- [Environment Setup](../setup/env-setup-guide.md)
- [Developer Guide](../development/developer-guide.md)
- [Architecture Overview](../architecture/architecture-overview.md)
