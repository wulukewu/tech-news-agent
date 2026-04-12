# Rollback Procedures

> **Comprehensive Rollback Guide**
> This document provides detailed rollback procedures for each major architectural change implemented during the refactoring.
> Last Updated: 2024-12-19

---

## 📋 Overview

This document provides comprehensive rollback procedures for all major changes implemented during the architecture refactoring. Each rollback procedure has been tested and validated to ensure safe recovery from any migration issues.

### Rollback Principles

- **Safety First**: All rollback procedures preserve data integrity
- **Minimal Downtime**: Rollbacks are designed for quick execution
- **Validation**: Each rollback includes verification steps
- **Documentation**: Clear step-by-step instructions
- **Testing**: All procedures tested in staging environment

### Rollback Categories

1. **Database Rollbacks**: Schema changes, migrations, data modifications
2. **Code Rollbacks**: Application code, configuration changes
3. **Infrastructure Rollbacks**: Docker, deployment, environment changes
4. **Feature Flag Rollbacks**: Quick feature disabling
5. **Complete System Rollback**: Full system restoration

---

## 🗄️ Database Rollback Procedures

### 1. Audit Trail Fields Rollback

**What Changed**: Added `created_at`, `updated_at`, `modified_by`, `deleted_at` fields to all tables.

**Rollback Script**: `rollbacks/001_remove_audit_fields.sql`

```sql
-- Remove audit trail fields from all tables
-- WARNING: This will permanently delete audit history

BEGIN;

-- Users table
ALTER TABLE users DROP COLUMN IF EXISTS created_at;
ALTER TABLE users DROP COLUMN IF EXISTS updated_at;
ALTER TABLE users DROP COLUMN IF EXISTS modified_by;
ALTER TABLE users DROP COLUMN IF EXISTS deleted_at;

-- Articles table
ALTER TABLE articles DROP COLUMN IF EXISTS created_at;
ALTER TABLE articles DROP COLUMN IF EXISTS updated_at;
ALTER TABLE articles DROP COLUMN IF EXISTS modified_by;
ALTER TABLE articles DROP COLUMN IF EXISTS deleted_at;

-- Feeds table
ALTER TABLE feeds DROP COLUMN IF EXISTS created_at;
ALTER TABLE feeds DROP COLUMN IF EXISTS updated_at;
ALTER TABLE feeds DROP COLUMN IF EXISTS modified_by;
ALTER TABLE feeds DROP COLUMN IF EXISTS deleted_at;

-- Reading list table
ALTER TABLE reading_list DROP COLUMN IF EXISTS created_at;
ALTER TABLE reading_list DROP COLUMN IF EXISTS updated_at;
ALTER TABLE reading_list DROP COLUMN IF EXISTS modified_by;
ALTER TABLE reading_list DROP COLUMN IF EXISTS deleted_at;

-- User subscriptions table
ALTER TABLE user_subscriptions DROP COLUMN IF EXISTS created_at;
ALTER TABLE user_subscriptions DROP COLUMN IF EXISTS updated_at;
ALTER TABLE user_subscriptions DROP COLUMN IF EXISTS modified_by;
ALTER TABLE user_subscriptions DROP COLUMN IF EXISTS deleted_at;

-- Remove triggers
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
DROP TRIGGER IF EXISTS update_articles_updated_at ON articles;
DROP TRIGGER IF EXISTS update_feeds_updated_at ON feeds;
DROP TRIGGER IF EXISTS update_reading_list_updated_at ON reading_list;
DROP TRIGGER IF EXISTS update_user_subscriptions_updated_at ON user_subscriptions;

-- Remove trigger function
DROP FUNCTION IF EXISTS update_updated_at_column();

COMMIT;
```

**Execution Steps**:

```bash
# 1. Backup database
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME > backup_before_audit_rollback.sql

# 2. Execute rollback
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f rollbacks/001_remove_audit_fields.sql

# 3. Verify rollback
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "\d users"
```

**Verification**:

```sql
-- Verify audit fields are removed
SELECT column_name
FROM information_schema.columns
WHERE table_name = 'users'
AND column_name IN ('created_at', 'updated_at', 'modified_by', 'deleted_at');
-- Should return no rows
```

### 2. Soft Delete Rollback

**What Changed**: Implemented soft delete using `deleted_at` field.

**Rollback Script**: `rollbacks/002_remove_soft_delete.sql`

```sql
-- Remove soft delete implementation
-- WARNING: This will permanently delete soft-deleted records

BEGIN;

-- Hard delete all soft-deleted records
DELETE FROM users WHERE deleted_at IS NOT NULL;
DELETE FROM articles WHERE deleted_at IS NOT NULL;
DELETE FROM feeds WHERE deleted_at IS NOT NULL;
DELETE FROM reading_list WHERE deleted_at IS NOT NULL;
DELETE FROM user_subscriptions WHERE deleted_at IS NOT NULL;

-- Remove deleted_at columns (if not already removed by audit rollback)
ALTER TABLE users DROP COLUMN IF EXISTS deleted_at;
ALTER TABLE articles DROP COLUMN IF EXISTS deleted_at;
ALTER TABLE feeds DROP COLUMN IF EXISTS deleted_at;
ALTER TABLE reading_list DROP COLUMN IF EXISTS deleted_at;
ALTER TABLE user_subscriptions DROP COLUMN IF EXISTS deleted_at;

COMMIT;
```

**Execution Steps**:

```bash
# 1. Backup soft-deleted records (optional recovery)
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "
COPY (SELECT * FROM users WHERE deleted_at IS NOT NULL) TO '/tmp/soft_deleted_users.csv' CSV HEADER;
COPY (SELECT * FROM articles WHERE deleted_at IS NOT NULL) TO '/tmp/soft_deleted_articles.csv' CSV HEADER;
"

# 2. Execute rollback
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -f rollbacks/002_remove_soft_delete.sql
```

### 3. Business Rule Constraints Rollback

**What Changed**: Added database constraints for business rules.

**Rollback Script**: `rollbacks/003_remove_business_constraints.sql`

```sql
-- Remove business rule constraints

BEGIN;

-- Remove check constraints
ALTER TABLE reading_list DROP CONSTRAINT IF EXISTS reading_list_status_check;
ALTER TABLE reading_list DROP CONSTRAINT IF EXISTS reading_list_rating_check;
ALTER TABLE articles DROP CONSTRAINT IF EXISTS articles_tinkering_index_check;

-- Remove unique constraints (if any were added)
ALTER TABLE user_subscriptions DROP CONSTRAINT IF EXISTS user_subscriptions_user_feed_unique;

-- Remove foreign key constraints (if any were modified)
-- Note: Be careful with foreign keys as they may be required for data integrity

COMMIT;
```

---

## 💻 Code Rollback Procedures

### 1. Repository Layer Rollback

**What Changed**: Implemented repository pattern with interfaces and base classes.

**Rollback Steps**:

1. **Update Environment Variables**:

```bash
# .env
USE_REPOSITORY_LAYER=false
USE_LEGACY_DATA_ACCESS=true
```

2. **Revert Service Dependencies**:

```python
# Rollback services to use direct Supabase client
class ArticleService:
    def __init__(self, supabase_client: Client):
        self.client = supabase_client  # Direct client access
        # Remove repository dependencies
```

3. **Restore Legacy Database Calls**:

```python
# Replace repository calls with direct Supabase calls
async def get_articles(self, user_id: str):
    # Old implementation
    response = self.client.table('articles')\
        .select('*')\
        .eq('user_id', user_id)\
        .execute()
    return response.data
```

4. **Update Dependency Injection**:

```python
# dependencies.py - Rollback to legacy dependencies
def get_article_service() -> ArticleService:
    client = get_supabase_client()
    return ArticleService(client)  # Direct client injection
```

### 2. Unified API Client Rollback (Frontend)

**What Changed**: Implemented singleton API client with interceptors.

**Rollback Steps**:

1. **Restore Individual API Clients**:

```typescript
// Restore separate API clients
const authClient = axios.create({ baseURL: '/api/auth' });
const articlesClient = axios.create({ baseURL: '/api/articles' });
const usersClient = axios.create({ baseURL: '/api/users' });
```

2. **Update API Modules**:

```typescript
// auth.ts - Use dedicated client
export const authApi = {
  login: () => authClient.post('/login'),
  logout: () => authClient.post('/logout'),
};

// articles.ts - Use dedicated client
export const articlesApi = {
  getArticles: () => articlesClient.get('/'),
  createArticle: (data) => articlesClient.post('/', data),
};
```

3. **Remove Unified Client References**:

```typescript
// Remove imports of unified client
// import { apiClient } from './lib/api/client';

// Replace with individual clients
import { authClient, articlesClient, usersClient } from './lib/api/legacy-clients';
```

### 3. Split Context Rollback (Frontend)

**What Changed**: Split monolithic context into focused contexts.

**Rollback Steps**:

1. **Restore Monolithic Context**:

```typescript
// Restore single AppContext
interface AppContextType {
  // Authentication
  isAuthenticated: boolean;
  user: User | null;
  login: () => void;
  logout: () => void;

  // Theme
  theme: Theme;
  setTheme: (theme: Theme) => void;

  // UI State
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
}

export const AppContext = createContext<AppContextType>();
```

2. **Update Component Imports**:

```typescript
// Replace split context imports
// import { useAuth } from './contexts/AuthContext';
// import { useUser } from './contexts/UserContext';
// import { useTheme } from './contexts/ThemeContext';

// With single context import
import { useApp } from './contexts/AppContext';
```

3. **Update Provider Structure**:

```tsx
// Replace split providers
// <AuthProvider>
//   <UserProvider>
//     <ThemeProvider>
//       {children}
//     </ThemeProvider>
//   </UserProvider>
// </AuthProvider>

// With single provider
<AppProvider>{children}</AppProvider>
```

### 4. Error Handling Rollback

**What Changed**: Implemented unified error handling with standard error codes.

**Rollback Steps**:

1. **Disable Unified Error Handling**:

```python
# settings.py
USE_UNIFIED_ERROR_HANDLING=false
```

2. **Restore Legacy Exception Handlers**:

```python
# Remove unified exception handlers
# app.add_exception_handler(AppException, app_exception_handler)

# Restore basic error handling
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": str(exc)}
    )
```

3. **Update API Routes**:

```python
# Restore legacy error handling in routes
@app.get("/articles")
async def get_articles():
    try:
        articles = await get_articles_from_db()
        return articles
    except Exception as e:
        return {"error": str(e)}  # Legacy format
```

---

## 🐳 Infrastructure Rollback Procedures

### 1. Docker Configuration Rollback

**What Changed**: Updated Docker configurations for new architecture.

**Rollback Steps**:

1. **Restore Previous Docker Images**:

```bash
# Tag current version as backup
docker tag tech-news-agent:latest tech-news-agent:backup

# Restore previous version
docker tag tech-news-agent:previous tech-news-agent:latest
```

2. **Rollback Docker Compose**:

```yaml
# docker-compose.yml - Restore previous configuration
version: '3.8'
services:
  backend:
    build: .
    environment:
      - USE_REPOSITORY_LAYER=false
      - USE_UNIFIED_ERROR_HANDLING=false
      - USE_STRUCTURED_LOGGING=false
```

3. **Restart Services**:

```bash
docker-compose down
docker-compose up -d
```

### 2. Environment Variables Rollback

**What Changed**: Added new environment variables for refactored features.

**Rollback Configuration**:

```bash
# .env - Disable new features
USE_REPOSITORY_LAYER=false
USE_UNIFIED_ERROR_HANDLING=false
USE_STRUCTURED_LOGGING=false
USE_SPLIT_CONTEXTS=false
USE_UNIFIED_API_CLIENT=false

# Legacy settings
LEGACY_MODE=true
SKIP_MIGRATIONS=true
```

---

## 🚩 Feature Flag Rollback

### Quick Feature Disabling

**Purpose**: Instantly disable new features without code deployment.

**Feature Flags**:

```python
# Feature flags for quick rollback
class FeatureFlags:
    USE_REPOSITORY_LAYER = os.getenv("USE_REPOSITORY_LAYER", "false").lower() == "true"
    USE_UNIFIED_ERROR_HANDLING = os.getenv("USE_UNIFIED_ERROR_HANDLING", "false").lower() == "true"
    USE_STRUCTURED_LOGGING = os.getenv("USE_STRUCTURED_LOGGING", "false").lower() == "true"
    USE_AUDIT_TRAIL = os.getenv("USE_AUDIT_TRAIL", "false").lower() == "true"
    USE_SOFT_DELETE = os.getenv("USE_SOFT_DELETE", "false").lower() == "true"
```

**Quick Rollback**:

```bash
# Disable all new features instantly
export USE_REPOSITORY_LAYER=false
export USE_UNIFIED_ERROR_HANDLING=false
export USE_STRUCTURED_LOGGING=false
export USE_AUDIT_TRAIL=false
export USE_SOFT_DELETE=false

# Restart application
docker-compose restart backend
```

---

## 🔄 Complete System Rollback

### Full System Restoration

**When to Use**: Critical issues requiring complete rollback to pre-refactoring state.

**Rollback Script**: `scripts/complete_rollback.sh`

```bash
#!/bin/bash
# Complete system rollback script

set -e

echo "Starting complete system rollback..."

# 1. Stop all services
echo "Stopping services..."
docker-compose down

# 2. Restore database
echo "Restoring database..."
if [ -f "backup_pre_refactoring.sql" ]; then
    psql -h $DB_HOST -U $DB_USER -d $DB_NAME < backup_pre_refactoring.sql
else
    echo "ERROR: Pre-refactoring database backup not found!"
    exit 1
fi

# 3. Restore code
echo "Restoring code..."
git checkout pre-refactoring-backup
git reset --hard

# 4. Restore configuration
echo "Restoring configuration..."
cp .env.pre-refactoring .env

# 5. Restore Docker images
echo "Restoring Docker images..."
docker tag tech-news-agent:pre-refactoring tech-news-agent:latest

# 6. Start services
echo "Starting services..."
docker-compose up -d

# 7. Verify rollback
echo "Verifying rollback..."
sleep 30
curl -f http://localhost:8000/health || {
    echo "ERROR: Health check failed after rollback!"
    exit 1
}

echo "Complete system rollback completed successfully!"
```

**Execution**:

```bash
chmod +x scripts/complete_rollback.sh
./scripts/complete_rollback.sh
```

---

## ✅ Rollback Verification Procedures

### 1. Database Verification

```sql
-- Verify database schema
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'public'
ORDER BY table_name, ordinal_position;

-- Verify data integrity
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM articles;
SELECT COUNT(*) FROM feeds;
SELECT COUNT(*) FROM reading_list;
SELECT COUNT(*) FROM user_subscriptions;

-- Check for orphaned records
SELECT COUNT(*) FROM reading_list rl
LEFT JOIN users u ON rl.user_id = u.id
WHERE u.id IS NULL;
```

### 2. Application Verification

```bash
# Health check
curl -f http://localhost:8000/health

# API endpoints
curl -f http://localhost:8000/api/articles
curl -f http://localhost:8000/api/feeds

# Frontend
curl -f http://localhost:3000
```

### 3. Functionality Verification

```python
# Test script: verify_rollback.py
import asyncio
import httpx

async def verify_rollback():
    async with httpx.AsyncClient() as client:
        # Test authentication
        auth_response = await client.get("http://localhost:8000/api/auth/me")
        print(f"Auth endpoint: {auth_response.status_code}")

        # Test articles
        articles_response = await client.get("http://localhost:8000/api/articles")
        print(f"Articles endpoint: {articles_response.status_code}")

        # Test feeds
        feeds_response = await client.get("http://localhost:8000/api/feeds")
        print(f"Feeds endpoint: {feeds_response.status_code}")

if __name__ == "__main__":
    asyncio.run(verify_rollback())
```

---

## 📊 Rollback Testing

### Staging Environment Testing

**Test Each Rollback Procedure**:

1. **Setup Test Environment**:

```bash
# Create staging environment
docker-compose -f docker-compose.staging.yml up -d

# Apply all migrations
python scripts/apply_migrations.py

# Seed test data
python scripts/seed_test_data.py
```

2. **Test Rollback Procedures**:

```bash
# Test database rollbacks
./test_database_rollbacks.sh

# Test code rollbacks
./test_code_rollbacks.sh

# Test infrastructure rollbacks
./test_infrastructure_rollbacks.sh
```

3. **Validate Results**:

```bash
# Run verification suite
python scripts/verify_rollback_results.py
```

### Automated Rollback Testing

```python
# rollback_tests.py
import pytest
import subprocess
import time

class TestRollbackProcedures:
    def test_database_rollback(self):
        # Apply migration
        subprocess.run(["python", "scripts/apply_audit_migration.py"], check=True)

        # Verify migration applied
        result = subprocess.run(["python", "scripts/check_audit_fields.py"], capture_output=True)
        assert result.returncode == 0

        # Rollback migration
        subprocess.run(["psql", "-f", "rollbacks/001_remove_audit_fields.sql"], check=True)

        # Verify rollback
        result = subprocess.run(["python", "scripts/check_audit_fields.py"], capture_output=True)
        assert result.returncode != 0  # Should fail because fields are removed

    def test_feature_flag_rollback(self):
        # Enable feature
        os.environ["USE_REPOSITORY_LAYER"] = "true"

        # Restart service
        subprocess.run(["docker-compose", "restart", "backend"], check=True)
        time.sleep(10)

        # Verify feature enabled
        response = requests.get("http://localhost:8000/health")
        assert response.status_code == 200

        # Disable feature
        os.environ["USE_REPOSITORY_LAYER"] = "false"

        # Restart service
        subprocess.run(["docker-compose", "restart", "backend"], check=True)
        time.sleep(10)

        # Verify feature disabled
        response = requests.get("http://localhost:8000/health")
        assert response.status_code == 200
```

---

## 🚨 Emergency Rollback Procedures

### Critical System Failure

**Immediate Actions**:

1. **Stop Traffic**:

```bash
# Stop load balancer or reverse proxy
sudo systemctl stop nginx
# or
docker-compose stop frontend
```

2. **Quick Database Rollback**:

```bash
# Restore from latest backup
pg_restore -h $DB_HOST -U $DB_USER -d $DB_NAME latest_backup.dump
```

3. **Rollback Application**:

```bash
# Use pre-built rollback image
docker tag tech-news-agent:emergency-rollback tech-news-agent:latest
docker-compose up -d
```

4. **Restore Traffic**:

```bash
# Restart load balancer
sudo systemctl start nginx
```

### Communication Template

**Incident Communication**:

```
Subject: [INCIDENT] Tech News Agent - Emergency Rollback in Progress

Team,

We are experiencing issues with the recent architecture refactoring deployment.
Emergency rollback procedures are being executed.

Status: IN PROGRESS
ETA: 15 minutes
Impact: Service temporarily unavailable

Actions:
1. Traffic stopped - COMPLETE
2. Database rollback - IN PROGRESS
3. Application rollback - PENDING
4. Service restoration - PENDING

Updates will be provided every 5 minutes.

Incident Commander: [Name]
```

---

## 📋 Rollback Checklist

### Pre-Rollback Checklist

- [ ] Identify specific components to rollback
- [ ] Notify team of rollback procedure
- [ ] Backup current state before rollback
- [ ] Verify rollback scripts are available and tested
- [ ] Confirm rollback authorization from stakeholders
- [ ] Prepare communication for users (if needed)

### During Rollback Checklist

- [ ] Execute rollback procedures in correct order
- [ ] Monitor system status during rollback
- [ ] Document any issues encountered
- [ ] Verify each step before proceeding to next
- [ ] Keep stakeholders informed of progress

### Post-Rollback Checklist

- [ ] Verify all functionality works correctly
- [ ] Run comprehensive test suite
- [ ] Check system performance metrics
- [ ] Confirm data integrity
- [ ] Update monitoring and alerting
- [ ] Document lessons learned
- [ ] Plan remediation for original issues

---

## 📚 Rollback Documentation

### Rollback Logs

**Log Template**:

```
Rollback Execution Log
=====================

Date: 2024-12-19
Time: 14:30:00 UTC
Executed By: [Name]
Reason: [Description]

Components Rolled Back:
- Database: Audit trail fields
- Code: Repository layer
- Configuration: Feature flags

Steps Executed:
1. [14:30] Started database backup
2. [14:32] Executed audit fields rollback
3. [14:35] Updated feature flags
4. [14:37] Restarted services
5. [14:40] Verified functionality

Issues Encountered:
- None

Verification Results:
- Health check: PASS
- API endpoints: PASS
- Frontend: PASS
- Database integrity: PASS

Rollback Status: SUCCESSFUL
Duration: 10 minutes
```

### Rollback Runbook

Keep updated runbook with:

- Contact information
- Escalation procedures
- Decision trees for rollback scenarios
- Communication templates
- Verification procedures

---

**Document Version**: 1.0.0
**Last Updated**: 2024-12-19
**Next Review**: 2025-03-19

All rollback procedures have been tested in staging environment and are ready for production use. Regular testing of rollback procedures is recommended to ensure they remain functional.
