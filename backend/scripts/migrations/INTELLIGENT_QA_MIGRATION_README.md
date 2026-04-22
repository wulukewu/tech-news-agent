# Intelligent Q&A Agent Database Migration

This directory contains the database migration for the Intelligent Q&A Agent feature, which adds semantic search and conversational AI capabilities to the Tech News Agent.

## Overview

The migration creates four new tables that work alongside the existing schema:

- **article_embeddings**: Vector embeddings for semantic search
- **conversations**: Multi-turn conversation context
- **user_profiles**: User preferences and reading history
- **query_logs**: Encrypted query logs for analytics

## Migration Files

- `007_create_intelligent_qa_schema.sql` - Main migration SQL
- `../apply_intelligent_qa_migration.py` - Migration instruction script
- `../verify_intelligent_qa_schema.py` - Schema verification script
- `../run_intelligent_qa_migration.sh` - Shell wrapper script

## Prerequisites

1. **PostgreSQL with pgvector**: Your database must support the pgvector extension
2. **Existing Schema**: Base tables (users, articles, feeds) must exist
3. **Permissions**: Database admin access to create tables and extensions
4. **Environment**: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY variables set

## Migration Process

### Step 1: Prepare Environment

```bash
# Activate virtual environment
source venv/bin/activate

# Load environment variables
source .env

# Verify prerequisites
python backend/scripts/apply_intelligent_qa_migration.py
```

### Step 2: Execute Migration SQL

The migration must be executed manually in Supabase Dashboard due to security restrictions:

1. Open [Supabase Dashboard](https://supabase.com/dashboard)
2. Navigate to your project
3. Go to **SQL Editor**
4. Copy the SQL from `007_create_intelligent_qa_schema.sql`
5. Paste and execute in the SQL Editor

### Step 3: Verify Migration

```bash
# Run verification script
python backend/scripts/verify_intelligent_qa_schema.py
```

## What the Migration Creates

### Tables

1. **article_embeddings**
   - Stores vector embeddings (1536 dimensions for OpenAI)
   - Supports chunked articles for long content
   - Includes metadata and audit trail fields

2. **conversations**
   - Multi-turn conversation context storage
   - Auto-expires after 7 days
   - Tracks conversation topics and turn counts

3. **user_profiles**
   - User reading history and preferences
   - Language preferences and interaction patterns
   - Satisfaction score tracking

4. **query_logs**
   - Encrypted query storage for analytics
   - Response time and satisfaction tracking
   - Privacy-compliant data retention

### Indexes

- **Vector Similarity**: ivfflat indexes for cosine similarity search
- **Performance**: Standard B-tree indexes for common queries
- **Soft Delete**: Partial indexes for active records only

### Constraints

- **Data Validation**: Check constraints for valid ranges and formats
- **Referential Integrity**: Foreign key constraints to existing tables
- **Business Rules**: Constraints enforcing application logic

### Triggers

- **Audit Trail**: Auto-update timestamps on record changes
- **Data Consistency**: Maintain data integrity across operations

## Performance Considerations

### Vector Index Tuning

The migration creates ivfflat indexes with `lists = 100`, suitable for:

- Up to 100,000 vectors: `lists = 100` (default)
- Up to 1,000,000 vectors: `lists = 1000`
- Up to 10,000,000 vectors: `lists = 10000`

Adjust the `lists` parameter based on your expected data volume.

### Query Optimization

- Use `LIMIT` clauses in vector similarity searches
- Filter by `deleted_at IS NULL` for active records
- Consider partitioning `query_logs` by date for large volumes

## Security Features

### Data Protection

- Query text encrypted at application level
- User data isolation through foreign keys
- Soft delete preserves audit trail

### Privacy Compliance

- Automatic conversation expiration
- Complete user data deletion support
- Anonymized analytics capabilities

## Troubleshooting

### Common Issues

1. **pgvector Extension Missing**

   ```sql
   -- Enable pgvector extension
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

2. **Permission Denied**
   - Ensure you have database admin privileges
   - Use service role key, not anon key

3. **Foreign Key Violations**
   - Verify base schema exists (users, articles tables)
   - Check existing data integrity

4. **Index Creation Fails**
   - Ensure sufficient memory for index creation
   - Consider creating indexes after data insertion

### Verification Failures

If verification fails:

1. Check Supabase Dashboard for error messages
2. Verify all SQL statements executed successfully
3. Ensure pgvector extension is enabled
4. Check table permissions and access

### Rollback Procedure

If you need to rollback the migration:

```sql
-- Drop tables in reverse dependency order
DROP TABLE IF EXISTS query_logs CASCADE;
DROP TABLE IF EXISTS user_profiles CASCADE;
DROP TABLE IF EXISTS conversations CASCADE;
DROP TABLE IF EXISTS article_embeddings CASCADE;

-- Note: This will lose all Q&A agent data
-- Consider backing up data before rollback
```

## Next Steps

After successful migration:

1. **Implement Vector Store Service**: Create service layer for embedding operations
2. **Build Embedding Pipeline**: Set up automatic article vectorization
3. **Create Query Processor**: Implement natural language query parsing
4. **Develop Response Generator**: Build structured response generation
5. **Add Conversation Manager**: Implement multi-turn conversation logic

## Support

For issues with the migration:

1. Check the verification script output for specific errors
2. Review Supabase Dashboard logs for detailed error messages
3. Ensure all prerequisites are met
4. Verify environment variables are correctly set

The migration is designed to be safe and reversible, with comprehensive error checking and validation at each step.
