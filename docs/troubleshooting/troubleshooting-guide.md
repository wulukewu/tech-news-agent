# Troubleshooting Guide

This guide helps you diagnose and fix common issues in the Tech News Agent development environment.

## Table of Contents

- [Quick Diagnostics](#quick-diagnostics)
- [Common Issues](#common-issues)
- [Development Environment Issues](#development-environment-issues)
- [Frontend Issues](#frontend-issues)
- [Backend Issues](#backend-issues)
- [Database Issues](#database-issues)
- [Docker Issues](#docker-issues)
- [Performance Issues](#performance-issues)
- [Error Messages and Solutions](#error-messages-and-solutions)
- [Getting Help](#getting-help)

## Quick Diagnostics

### Health Check Commands

```bash
# Check all services status
make ps

# Check database connection
./scripts/dev-migrate.sh status

# Test API health
curl http://localhost:8000/health

# Test frontend
curl http://localhost:3000

# Check logs
make logs-dev
```

### System Requirements Check

```bash
# Check Docker
docker --version
docker-compose --version

# Check available resources
docker system df
docker stats --no-stream

# Check ports
lsof -i :3000
lsof -i :8000
```

## Common Issues

### 1. Services Won't Start

**Symptoms:**

- `make dev` fails
- Containers exit immediately
- Port binding errors

**Solutions:**

```bash
# Check if ports are in use
lsof -i :3000 :8000

# Kill processes using the ports
kill -9 $(lsof -t -i:3000)
kill -9 $(lsof -t -i:8000)

# Clean up Docker resources
make clean
docker system prune -f

# Rebuild and start
make up-dev
```

### 2. Environment Variables Not Loading

**Symptoms:**

- "Configuration missing" errors
- API calls fail with authentication errors
- Services can't connect to database

**Solutions:**

```bash
# Verify .env file exists
ls -la .env

# Check environment variables in containers
docker-compose exec backend env | grep SUPABASE
docker-compose exec frontend env | grep NEXT_PUBLIC

# Recreate .env from template
cp .env.example .env
# Edit .env with your values

# Restart services to reload environment
make restart-dev
```

### 3. Hot Module Replacement Not Working

**Symptoms:**

- Changes not reflected in browser
- Need to manually refresh
- Slow reload times

**Solutions:**

```bash
# Test HMR performance
./scripts/test-hmr.sh

# Check file permissions (especially on Windows/WSL)
ls -la frontend/
ls -la backend/app/

# Restart with clean build
make down-dev
make build-dev
make dev

# For WSL2 users, try local development
cd frontend && npm run dev
cd backend && uvicorn app.main:app --reload
```

### 4. Database Connection Issues

**Symptoms:**

- "Database connection failed" errors
- Timeout errors
- Authentication failures

**Solutions:**

```bash
# Test database connection
./scripts/dev-migrate.sh status

# Check Supabase service status
curl -I https://your-project.supabase.co

# Verify credentials in .env
grep SUPABASE .env

# Test connection manually
python3 -c "
from supabase import create_client
import os
client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
print('Connection successful')
"
```

## Development Environment Issues

### Docker Issues

#### Container Exits Immediately

```bash
# Check container logs
docker-compose logs backend
docker-compose logs frontend

# Check for syntax errors in Dockerfile
docker-compose build --no-cache

# Verify base images are available
docker pull node:20-alpine
docker pull python:3.11-slim
```

#### Out of Disk Space

```bash
# Check Docker disk usage
docker system df

# Clean up unused resources
docker system prune -a -f
docker volume prune -f

# Remove unused images
docker image prune -a -f
```

#### Memory Issues

```bash
# Check Docker memory usage
docker stats

# Increase Docker memory limit (Docker Desktop)
# Settings > Resources > Memory > Increase limit

# Reduce memory usage
docker-compose down
docker system prune -f
make dev
```

### Network Issues

#### Port Conflicts

```bash
# Find what's using the ports
lsof -i :3000
lsof -i :8000

# Change ports in docker-compose.yml if needed
# Or kill conflicting processes
sudo kill -9 $(lsof -t -i:3000)
```

#### DNS Resolution Issues

```bash
# Test DNS resolution
nslookup your-project.supabase.co

# Try using IP address instead of hostname
# Check /etc/hosts file for conflicts

# Restart Docker daemon
sudo systemctl restart docker  # Linux
# Or restart Docker Desktop
```

## Frontend Issues

### Build Failures

#### TypeScript Errors

```bash
# Check TypeScript configuration
cd frontend
npm run type-check

# Fix common issues
npm install --save-dev @types/node @types/react @types/react-dom

# Clear TypeScript cache
rm -rf .next
npm run build
```

#### Dependency Issues

```bash
# Clear node_modules and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install

# Check for peer dependency warnings
npm ls

# Update dependencies
npm update
```

### Runtime Errors

#### Hydration Errors

**Error:** "Hydration failed because the initial UI does not match what was rendered on the server"

**Solutions:**

- Ensure server and client render the same content
- Check for browser-only code running on server
- Use `useEffect` for client-only code
- Check for date/time formatting differences

```typescript
// Fix hydration issues
import { useEffect, useState } from 'react';

function MyComponent() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  // Client-only code here
  return <div>{new Date().toLocaleString()}</div>;
}
```

#### API Call Failures

```bash
# Check API client configuration
grep NEXT_PUBLIC_API_URL .env

# Test API endpoints directly
curl http://localhost:8000/health
curl http://localhost:8000/api/articles

# Check browser network tab for failed requests
# Enable API debugging in browser console
```

## Backend Issues

### FastAPI Issues

#### Import Errors

```bash
# Check Python path
docker-compose exec backend python -c "import sys; print(sys.path)"

# Verify all dependencies are installed
docker-compose exec backend pip list

# Rebuild container with fresh dependencies
docker-compose build backend --no-cache
```

#### Database Migration Issues

```bash
# Check database schema
./scripts/dev-migrate.sh status

# Re-run initialization
./scripts/dev-migrate.sh init

# Check for SQL syntax errors in migration files
cat backend/scripts/init_supabase.sql
```

### Discord Bot Issues

#### Bot Not Responding

```bash
# Check bot token
grep DISCORD_TOKEN .env

# Verify bot permissions in Discord Developer Portal
# Check bot logs
docker-compose logs backend | grep -i discord

# Test bot connection
docker-compose exec backend python -c "
import discord
import os
client = discord.Client()
print('Bot token configured:', bool(os.getenv('DISCORD_TOKEN')))
"
```

#### Command Registration Issues

```bash
# Check command registration logs
docker-compose logs backend | grep -i command

# Manually sync commands (if needed)
# Check Discord Developer Portal > Applications > Your Bot > General Information
```

## Database Issues

### Connection Problems

#### Supabase Connection Timeout

```bash
# Test connection with curl
curl -H "apikey: YOUR_SUPABASE_KEY" \
     -H "Authorization: Bearer YOUR_SUPABASE_KEY" \
     "https://your-project.supabase.co/rest/v1/users?select=count"

# Check Supabase project status
# Visit Supabase Dashboard > Settings > General
```

#### Authentication Failures

```bash
# Verify service role key (not anon key)
# Check key permissions in Supabase Dashboard
# Ensure RLS policies allow service role access
```

### Data Issues

#### Missing Tables

```bash
# Check if tables exist
./scripts/dev-migrate.sh status

# Re-run database initialization
# Copy backend/scripts/init_supabase.sql to Supabase SQL Editor
# Execute the SQL script
```

#### Data Inconsistency

```bash
# Check data integrity
./scripts/dev-migrate.sh status

# Reset database if needed
./scripts/dev-migrate.sh reset --force
./scripts/dev-migrate.sh init
./scripts/dev-migrate.sh seed
```

## Performance Issues

### Slow API Responses

```bash
# Check API response times
curl -w "@curl-format.txt" http://localhost:8000/api/articles

# Monitor database query performance
# Check Supabase Dashboard > Logs > Slow Queries

# Enable FastAPI debug logging
# Set LOG_LEVEL=DEBUG in .env
```

### High Memory Usage

```bash
# Monitor container memory usage
docker stats

# Check for memory leaks
# Profile Python code with memory_profiler
# Check for large objects in memory
```

### Slow Frontend Loading

```bash
# Analyze bundle size
cd frontend
npm run build
npm run analyze  # If configured

# Check for large dependencies
npx webpack-bundle-analyzer .next/static/chunks/*.js

# Optimize images and assets
# Use Next.js Image component
# Enable compression
```

## Error Messages and Solutions

### Common Error Patterns

#### "Cannot read property 'X' of undefined"

**Cause:** Accessing property of undefined/null object

**Solutions:**

```typescript
// Use optional chaining
const value = obj?.property?.subProperty;

// Use conditional rendering
{data && <Component data={data} />}

// Provide default values
const { property = 'default' } = obj || {};
```

#### "Module not found"

**Cause:** Missing dependency or incorrect import path

**Solutions:**

```bash
# Install missing dependency
npm install missing-package

# Check import paths
# Use absolute imports with @ alias
import { Component } from '@/components/Component';

# Clear module cache
rm -rf node_modules/.cache
```

#### "Port already in use"

**Cause:** Another process is using the port

**Solutions:**

```bash
# Find and kill process
lsof -ti:3000 | xargs kill -9

# Use different port
# Modify docker-compose.yml ports section
```

#### "Database connection failed"

**Cause:** Invalid credentials or network issues

**Solutions:**

```bash
# Verify credentials
./scripts/dev-migrate.sh status

# Check network connectivity
ping your-project.supabase.co

# Update connection string
# Check .env file for typos
```

### HTTP Error Codes

#### 401 Unauthorized

- Check authentication token
- Verify token hasn't expired
- Clear localStorage and re-login

#### 403 Forbidden

- Check user permissions
- Verify API key has correct permissions
- Check Supabase RLS policies

#### 404 Not Found

- Verify API endpoint exists
- Check URL for typos
- Ensure resource exists in database

#### 500 Internal Server Error

- Check backend logs: `make logs-dev`
- Verify database connection
- Check for unhandled exceptions

## Getting Help

### Debugging Steps

1. **Check Logs**

   ```bash
   make logs-dev
   docker-compose logs backend
   docker-compose logs frontend
   ```

2. **Verify Configuration**

   ```bash
   cat .env
   ./scripts/dev-migrate.sh status
   ```

3. **Test Components Individually**

   ```bash
   curl http://localhost:8000/health
   curl http://localhost:3000
   ```

4. **Check System Resources**
   ```bash
   docker stats
   df -h
   free -h
   ```

### Collecting Debug Information

When reporting issues, include:

```bash
# System information
uname -a
docker --version
docker-compose --version

# Service status
make ps
docker-compose logs --tail=50

# Configuration (remove sensitive data)
cat .env | sed 's/=.*/=***/'

# Resource usage
docker stats --no-stream
```

### Documentation Resources

- [README.md](../README.md) - Project overview
- [QUICKSTART.md](QUICKSTART.md) - Setup guide
- [DEVELOPMENT_WORKFLOWS.md](DEVELOPMENT_WORKFLOWS.md) - Development workflows
- [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) - Technical details

### Support Channels

1. **Check existing documentation**
2. **Search GitHub issues**
3. **Create detailed bug report with:**
   - Steps to reproduce
   - Expected vs actual behavior
   - System information
   - Relevant logs
   - Configuration (sanitized)

### Emergency Recovery

If everything is broken:

```bash
# Nuclear option - reset everything
make clean
docker system prune -a -f
rm -rf frontend/node_modules frontend/.next
rm -rf backend/__pycache__ backend/.pytest_cache

# Start fresh
./scripts/dev-setup.sh
make dev
```

This should resolve most issues. If problems persist, check the documentation or create an issue with detailed information about your environment and the specific error messages you're seeing.
