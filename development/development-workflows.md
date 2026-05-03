# Development Workflows

This document outlines common development workflows for the Tech News Agent project, including setup, testing, debugging, and deployment procedures.

## Table of Contents

- [Initial Setup](#initial-setup)
- [Daily Development Workflow](#daily-development-workflow)
- [Testing Workflows](#testing-workflows)
- [Database Management](#database-management)
- [Code Quality Workflows](#code-quality-workflows)
- [Debugging Workflows](#debugging-workflows)
- [Deployment Workflows](#deployment-workflows)
- [Troubleshooting](#troubleshooting)

## Initial Setup

### First-Time Setup

1. **Clone and Setup Environment**

   ```bash
   git clone <repository-url>
   cd tech-news-agent
   ./scripts/dev-setup.sh
   ```

2. **Configure Environment Variables**

   ```bash
   # Edit .env file with your credentials
   nano .env

   # Required variables:
   # - SUPABASE_URL and SUPABASE_KEY
   # - GROQ_API_KEY
   # - JWT_SECRET_KEY (generate with: openssl rand -hex 32)
   ```

3. **Initialize Database**

   ```bash
   # Run the SQL script in Supabase SQL Editor
   # File: backend/scripts/init_supabase.sql

   # Then seed with default data
   ./scripts/dev-migrate.sh seed
   ```

4. **Start Development Environment**
   ```bash
   make dev
   ```

### Verification

- Web Interface: http://localhost:3000
- API Documentation: http://localhost:8000/docs
- API Health Check: http://localhost:8000/health

## Daily Development Workflow

### Starting Development

```bash
# Start all services
make dev

# View logs
make logs-dev

# Check service status
docker-compose ps
```

### Making Changes

1. **Frontend Changes**
   - Edit files in `frontend/` directory
   - Hot Module Replacement (HMR) automatically reloads changes
   - Check browser console for errors

2. **Backend Changes**
   - Edit files in `backend/app/` directory
   - FastAPI auto-reload detects changes and restarts server
   - Check Docker logs: `make logs-dev`

3. **Database Changes**
   - Create migration scripts in `backend/scripts/migrations/`
   - Test migrations: `./scripts/dev-migrate.sh status`
   - Apply migrations manually in Supabase SQL Editor

### Code Quality Checks

```bash
# Run all quality checks
make check

# Individual checks
make lint           # Lint all code
make format         # Format all code
make format-check   # Check formatting without changes
```

### Testing Changes

```bash
# Run all tests
./scripts/dev-test.sh

# Run specific test suites
./scripts/dev-test.sh --frontend --unit
./scripts/dev-test.sh --backend --property
./scripts/dev-test.sh --coverage
```

### Committing Changes

```bash
# Pre-commit hooks run automatically
git add .
git commit -m "feat: add new feature"

# If pre-commit hooks fail, fix issues and retry
make format
git add .
git commit -m "feat: add new feature"
```

## Testing Workflows

### Unit Testing

```bash
# Frontend unit tests
cd frontend
npm run test:unit

# Backend unit tests
cd backend
pytest tests/unit/ -v
```

### Integration Testing

```bash
# Frontend integration tests
cd frontend
npm run test:integration

# Backend integration tests
cd backend
pytest tests/integration/ -v
```

### Property-Based Testing

```bash
# Run property tests (backend)
cd backend
pytest tests/test_database_properties.py -v

# Run with different profiles
HYPOTHESIS_PROFILE=dev pytest tests/test_database_properties.py -v    # Fast (10 examples)
HYPOTHESIS_PROFILE=ci pytest tests/test_database_properties.py -v     # CI (100 examples)
```

### End-to-End Testing

```bash
# Frontend E2E tests
cd frontend
npm run test:e2e        # Headless
npm run test:e2e:ui     # Interactive UI
```

### Test Coverage

```bash
# Frontend coverage
cd frontend
npm run test:coverage

# Backend coverage
cd backend
pytest --cov=app --cov-report=html --cov-report=term
```

## Database Management

### Database Status

```bash
# Check database connection and schema
./scripts/dev-migrate.sh status
```

### Seeding Data

```bash
# Seed default feeds
./scripts/dev-migrate.sh seed

# Seed specific data
cd backend
python3 scripts/seed_recommended_feeds.py
```

### Database Reset

```bash
# Reset database (with confirmation)
./scripts/dev-migrate.sh reset

# Force reset (no confirmation)
./scripts/dev-migrate.sh reset --force
```

### Manual Database Operations

```bash
# Connect to database using Python
cd backend
python3 -c "
from app.core.config import get_settings
from supabase import create_client
settings = get_settings()
supabase = create_client(settings.supabase_url, settings.supabase_key)
# Your database operations here
"
```

## Code Quality Workflows

### Linting

```bash
# Lint all code
make lint

# Lint specific parts
make lint-frontend
make lint-backend

# Auto-fix linting issues
cd frontend && npm run lint:fix
cd backend && ruff check --fix .
```

### Formatting

```bash
# Format all code
make format

# Format specific parts
make format-frontend
make format-backend

# Check formatting without changes
make format-check
```

### Pre-commit Hooks

```bash
# Install pre-commit hooks
make pre-commit-install

# Run pre-commit on all files
make pre-commit-run

# Update pre-commit hooks
make pre-commit-update
```

### Type Checking

```bash
# Frontend type checking
cd frontend
npm run type-check

# Backend type checking (via mypy if configured)
cd backend
mypy app/
```

## Debugging Workflows

### Frontend Debugging

1. **Browser DevTools**
   - Open Chrome/Firefox DevTools (F12)
   - Check Console tab for JavaScript errors
   - Use Network tab to inspect API calls
   - Use React DevTools extension

2. **Source Maps**
   - Source maps are enabled in development
   - Set breakpoints directly in TypeScript source
   - Use debugger statements in code

3. **API Client Debugging**
   ```typescript
   // Enable API logging
   import { apiClient } from '@/lib/api/client';
   apiClient.setLogging(true);
   ```

### Backend Debugging

1. **Docker Logs**

   ```bash
   # View all logs
   make logs-dev

   # View specific service logs
   docker-compose logs -f backend
   ```

2. **Structured Logging**

   ```python
   from app.core.logger import get_logger
   logger = get_logger(__name__)

   logger.info("Debug message", extra_data={"key": "value"})
   logger.error("Error occurred", exc_info=True)
   ```

3. **Interactive Debugging**

   ```bash
   # Add breakpoint in code
   import pdb; pdb.set_trace()

   # Or use ipdb for better experience
   import ipdb; ipdb.set_trace()
   ```

### Database Debugging

1. **Query Logging**
   - Enable query logging in Supabase Dashboard
   - Check logs for slow or failed queries

2. **Direct Database Access**
   ```bash
   # Use Supabase SQL Editor for direct queries
   # Or connect via psql if you have connection string
   ```

### Performance Debugging

1. **Frontend Performance**

   ```bash
   # Build and analyze bundle
   cd frontend
   npm run build
   npm run analyze  # If configured
   ```

2. **API Performance**
   - Check API response times in browser DevTools
   - Use FastAPI's built-in profiling
   - Monitor with application performance monitoring (APM) tools

## Deployment Workflows

### Development Deployment

```bash
# Build and start development environment
make up-dev

# Rebuild images
make build-dev
```

### Production Deployment

```bash
# Build production images
make build-prod

# Start production environment
make prod

# View production logs
make logs-prod
```

### Environment-Specific Configuration

1. **Development (.env)**

   ```bash
   NODE_ENV=development
   LOG_LEVEL=DEBUG
   ```

2. **Production (.env.prod)**
   ```bash
   NODE_ENV=production
   LOG_LEVEL=INFO
   ```

## Troubleshooting

### Common Issues

1. **Docker Issues**

   ```bash
   # Clean up Docker resources
   make clean

   # Rebuild everything
   docker-compose down -v
   docker-compose up -d --build
   ```

2. **Port Conflicts**

   ```bash
   # Check what's using ports 3000 and 8000
   lsof -i :3000
   lsof -i :8000

   # Kill processes if needed
   kill -9 <PID>
   ```

3. **Environment Variable Issues**

   ```bash
   # Verify environment variables are loaded
   docker-compose exec backend env | grep SUPABASE
   docker-compose exec frontend env | grep NEXT_PUBLIC
   ```

4. **Database Connection Issues**

   ```bash
   # Test database connection
   ./scripts/dev-migrate.sh status

   # Check Supabase service status
   curl -I https://your-project.supabase.co
   ```

5. **Node Modules Issues**

   ```bash
   # Clear and reinstall frontend dependencies
   cd frontend
   rm -rf node_modules package-lock.json
   npm install
   ```

6. **Python Dependencies Issues**
   ```bash
   # Rebuild backend container
   docker-compose build backend --no-cache
   ```

### Getting Help

1. **Check Logs**

   ```bash
   make logs-dev
   ```

2. **Verify Configuration**

   ```bash
   # Check environment variables
   cat .env

   # Check Docker services
   docker-compose ps
   ```

3. **Run Health Checks**

   ```bash
   # API health check
   curl http://localhost:8000/health

   # Database status
   ./scripts/dev-migrate.sh status
   ```

4. **Documentation**
   - [README.md](../README.md) - Project overview
   - [QUICKSTART.md](QUICKSTART.md) - Quick setup guide
   - [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) - Detailed development guide

### Performance Optimization

1. **Frontend Optimization**
   - Use React.memo for expensive components
   - Implement proper loading states
   - Optimize bundle size with code splitting

2. **Backend Optimization**
   - Use database indexes for frequent queries
   - Implement caching for expensive operations
   - Monitor API response times

3. **Database Optimization**
   - Analyze slow queries in Supabase Dashboard
   - Add appropriate indexes
   - Use connection pooling

## Best Practices

### Code Organization

- Follow the established project structure
- Use TypeScript for type safety
- Write comprehensive tests
- Document complex logic

### Git Workflow

- Use conventional commit messages
- Create feature branches for new work
- Run tests before pushing
- Use pull requests for code review

### Security

- Never commit secrets to version control
- Use environment variables for configuration
- Validate all user inputs
- Follow security best practices for authentication

### Performance

- Monitor application performance
- Optimize database queries
- Use caching where appropriate
- Minimize bundle sizes

This workflow guide should help you navigate the development process efficiently. For specific technical details, refer to the other documentation files in the `docs/` directory.
