# Intelligent Q&A Agent Database Connection

This module provides high-performance database connection pooling and management for the intelligent Q&A agent system using asyncpg and PostgreSQL with pgvector support.

## Features

- **Connection Pooling**: Efficient asyncpg connection pooling with configurable parameters
- **Health Monitoring**: Comprehensive health checks and monitoring capabilities
- **Retry Logic**: Automatic retry mechanism for transient database errors
- **pgvector Support**: Built-in support for vector operations and similarity search
- **Configuration Management**: Flexible configuration via environment variables or DATABASE_URL
- **Error Handling**: Robust error handling with detailed logging and graceful degradation

## Configuration

### Environment Variables

You can configure the database connection using either a `DATABASE_URL` or individual parameters:

#### Option 1: DATABASE_URL (Recommended)

```bash
DATABASE_URL=postgresql://username:password@localhost:5432/database_name
```

#### Option 2: Individual Parameters

```bash
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=postgres
DATABASE_USER=postgres
DATABASE_PASSWORD=your_password
```

#### Connection Pool Configuration (Optional)

```bash
DATABASE_POOL_MIN_SIZE=5                              # Minimum connections in pool
DATABASE_POOL_MAX_SIZE=20                             # Maximum connections in pool
DATABASE_POOL_MAX_QUERIES=50000                       # Max queries per connection
DATABASE_POOL_MAX_INACTIVE_CONNECTION_LIFETIME=300.0  # Connection lifetime (seconds)
DATABASE_CONNECTION_TIMEOUT=10.0                      # Connection timeout (seconds)
DATABASE_COMMAND_TIMEOUT=60.0                         # Command timeout (seconds)
```

## Usage

### Basic Usage

```python
from app.qa_agent.database import get_database_manager, get_db_connection

# Get the global database manager
db_manager = await get_database_manager()

# Check database health
health = await db_manager.health_check()
print(f"Database healthy: {health['healthy']}")

# Use connection context manager
async with get_db_connection() as conn:
    result = await conn.fetchval("SELECT version()")
    print(f"PostgreSQL version: {result}")
```

### Vector Operations

```python
async with get_db_connection() as conn:
    # Test vector similarity
    distance = await conn.fetchval(
        "SELECT '[1,2,3]'::vector <-> '[1,2,4]'::vector"
    )

    # Similarity search
    results = await conn.fetch("""
        SELECT content, embedding <-> $1 as distance
        FROM article_embeddings
        WHERE embedding <-> $1 < 0.5
        ORDER BY distance
        LIMIT 10
    """, query_embedding)
```

### Retry Mechanism

```python
# Execute with automatic retry on transient errors
result = await db_manager.execute_with_retry(
    "SELECT * FROM articles WHERE id = $1",
    article_id,
    max_retries=3
)
```

### Utility Functions

```python
from app.qa_agent.db_utils import QADatabaseUtils

# Get table statistics
stats = await QADatabaseUtils.get_table_stats()

# Test vector operations
vector_test = await QADatabaseUtils.test_vector_operations()

# Get database information
db_info = await QADatabaseUtils.get_database_info()

# Cleanup expired conversations
deleted_count = await QADatabaseUtils.cleanup_expired_conversations(days=7)
```

## Architecture

### DatabaseManager Class

The `DatabaseManager` class provides the core functionality:

- **Connection Pool Management**: Creates and manages asyncpg connection pools
- **Health Monitoring**: Provides comprehensive health checks
- **Error Handling**: Implements retry logic and error recovery
- **Resource Management**: Proper cleanup and resource management

### Key Methods

- `initialize()`: Initialize the database connection pool
- `get_connection()`: Get a connection from the pool (context manager)
- `execute_with_retry()`: Execute queries with automatic retry
- `health_check()`: Perform comprehensive health check
- `close()`: Close the connection pool and cleanup resources

### Global Manager

The module provides a global database manager instance that can be accessed via:

```python
# Get singleton instance
db_manager = await get_database_manager()

# Close global instance
await close_database_manager()
```

## Error Handling

The system implements comprehensive error handling:

### DatabaseConnectionError

Raised for database connection and operation failures:

```python
try:
    async with get_db_connection() as conn:
        result = await conn.fetchval("SELECT 1")
except DatabaseConnectionError as e:
    logger.error(f"Database error: {e}")
    # Handle error appropriately
```

### Retry Logic

Automatic retry for transient errors:

- Connection timeouts
- Network errors
- Temporary unavailability
- Broken connections

Non-transient errors (syntax errors, constraint violations) are not retried.

## Health Monitoring

The health check provides comprehensive status information:

```python
health = await db_manager.health_check()
# Returns:
{
    "healthy": True,
    "pool_initialized": True,
    "pool_size": 10,
    "pool_free_size": 5,
    "pgvector_available": True,
    "response_time_ms": 15.2,
    "error": None
}
```

## Performance Considerations

### Connection Pool Sizing

- **Min Size**: Keep minimum connections for immediate availability
- **Max Size**: Limit maximum connections to prevent resource exhaustion
- **Query Limit**: Recycle connections after specified query count
- **Lifetime**: Recycle idle connections to maintain freshness

### Recommended Settings

For production environments:

```bash
DATABASE_POOL_MIN_SIZE=10
DATABASE_POOL_MAX_SIZE=50
DATABASE_POOL_MAX_QUERIES=50000
DATABASE_POOL_MAX_INACTIVE_CONNECTION_LIFETIME=300.0
DATABASE_CONNECTION_TIMEOUT=10.0
DATABASE_COMMAND_TIMEOUT=60.0
```

## Testing

Run the test suite to verify functionality:

```bash
cd backend
python -m pytest tests/test_qa_database.py -v
```

Run the example usage script:

```bash
cd backend
python -m app.qa_agent.example_usage
```

Run the database test script:

```bash
cd backend
python -m app.qa_agent.test_database
```

## Requirements

- Python 3.11+
- asyncpg >= 0.29.0
- PostgreSQL with pgvector extension
- Proper database credentials and network access

## Integration with QA Agent

This database connection manager is designed specifically for the intelligent Q&A agent system and provides:

1. **High Performance**: Optimized for concurrent vector similarity searches
2. **Scalability**: Supports 50+ concurrent users with proper connection pooling
3. **Reliability**: Comprehensive error handling and retry mechanisms
4. **Monitoring**: Built-in health checks and performance monitoring
5. **pgvector Support**: Native support for vector operations and similarity search

The connection manager integrates seamlessly with other QA agent components:

- **Vector Store**: Provides connections for embedding storage and retrieval
- **Query Processor**: Supports high-performance query execution
- **Conversation Manager**: Handles conversation state persistence
- **Response Generator**: Enables efficient article retrieval and processing

## Troubleshooting

### Common Issues

1. **Connection Refused**: Check database host, port, and network connectivity
2. **Authentication Failed**: Verify username and password
3. **pgvector Not Available**: Install pgvector extension in PostgreSQL
4. **Pool Exhaustion**: Increase max pool size or check for connection leaks
5. **Timeout Errors**: Increase connection or command timeout values

### Debugging

Enable debug logging to troubleshoot issues:

```python
import logging
logging.getLogger('app.qa_agent.database').setLevel(logging.DEBUG)
```

Check health status:

```python
health = await db_manager.health_check()
if not health['healthy']:
    print(f"Database issue: {health['error']}")
```

---

## Completed Tasks

### ✅ Task 1.1: Database Schema Setup

- PostgreSQL with pgvector extension
- Tables: articles, article_embeddings, conversations, user_profiles, query_logs
- Vector similarity indexes

### ✅ Task 1.2: Database Connection Management

- Async connection pooling with asyncpg
- Environment configuration
- Health checks and retry logic

### ✅ Task 8.1: Conversation Context Management

- ConversationManager class with persistent storage
- Conversation history maintenance (10 turns limit)
- Context retrieval and conversation state management
- Data retention policies and automatic cleanup

### ✅ Task 2.1: Core Data Models

- ParsedQuery, ArticleMatch, StructuredResponse, ConversationContext
- Validation methods and enum types
- Comprehensive type safety with Pydantic

### ✅ Task 2.2: User Profile and Article Models

- UserProfile with reading history and preferences
- Article and ArticleSummary models
- Serialization/deserialization support

### ✅ Task 3.1: VectorStore Implementation

- Store, update, delete embeddings
- Vector similarity search with pgvector
- Metadata filtering and user isolation

### ✅ Task 3.2: Embedding Generation and Preprocessing

- HTML cleaning and text formatting
- Chunking strategy for long articles
- Embedding generation with OpenAI-compatible API
- Separate vectorization for title, content, metadata

## Module Components

### Core Files

- `models.py` - Core data models (ParsedQuery, ArticleMatch, StructuredResponse, etc.)
- `article_models.py` - Enhanced article models with metadata support
- `vector_store.py` - pgvector integration for semantic search
- `embedding_service.py` - Article preprocessing and embedding generation
- `conversation_manager.py` - Conversation context management and persistence
- `database.py` - Database connection and utilities (this file)
- `constants.py` - System constants and configuration
- `validators.py` - Data validation utilities

### Examples

- `examples/embedding_service_usage.py` - Embedding service usage examples
- `example_usage.py` - Database usage examples
- `example_models_usage.py` - Data models usage examples

## Quick Start Guide

### 1. Article Preprocessing

```python
from app.qa_agent.embedding_service import ArticlePreprocessor

preprocessor = ArticlePreprocessor()
result = preprocessor.preprocess_article(html_content, title)
```

### 2. Text Chunking

```python
from app.qa_agent.embedding_service import TextChunker

chunker = TextChunker(chunk_size=1000, chunk_overlap=200)
chunks = chunker.chunk_text(text, language="en")
```

### 3. Complete Embedding Pipeline

```python
from app.qa_agent.embedding_service import get_embedding_service

service = get_embedding_service()
result = await service.process_and_embed_article(
    article_id, title, content, metadata
)
```

### 5. Conversation Management

```python
from app.qa_agent.conversation_manager import get_conversation_manager

manager = get_conversation_manager()
conversation_id = await manager.create_conversation(user_id)
await manager.add_turn(conversation_id, query, parsed_query, response)
context = await manager.get_context(conversation_id)
```

### 6. Vector Search

```python
from app.qa_agent.vector_store import get_vector_store

vector_store = get_vector_store()
matches = await vector_store.search_similar(
    query_vector, user_id, limit=10
)
```

## Task Documentation

- [Task 8.1 Summary](./TASK_8.1_COMPLETION_SUMMARY.md) - Conversation context management

- [Task 1.1 Summary](./TASK_1.1_COMPLETION_SUMMARY.md) - Database schema setup
- [Task 2.1 Summary](./TASK_2.1_COMPLETION_SUMMARY.md) - Core data models
- [Task 2.2 Summary](./TASK_2.2_COMPLETION_SUMMARY.md) - User profile and article models
- [Task 3.1 Summary](./TASK_3.1_COMPLETION_SUMMARY.md) - VectorStore implementation
- [Task 3.2 Summary](./TASK_3.2_COMPLETION_SUMMARY.md) - Embedding generation and preprocessing

## Next Steps

Upcoming tasks:

- [ ] Task 3.3: Property tests for vector operations
- [ ] Task 4.1: Query processor implementation
- [ ] Task 4.2: Complex query handling
- [ ] Task 5.1: Semantic search functionality
- [ ] Task 5.2: Search result optimization

## Additional Resources

For more information, refer to:

- Design document: `.kiro/specs/intelligent-qa-agent/design.md`
- Requirements: `.kiro/specs/intelligent-qa-agent/requirements.md`
- Tasks: `.kiro/specs/intelligent-qa-agent/tasks.md`
