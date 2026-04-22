"""
Database Connection and Configuration Management for Intelligent Q&A Agent

This module provides high-performance database connection pooling using asyncpg
for the intelligent Q&A agent system. It includes connection health checks,
retry logic, and proper resource management.

Validates: Requirements 6.4, 9.4
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, Optional
from urllib.parse import urlparse

import asyncpg
from asyncpg import Connection, Pool

from app.core.config import settings
from app.core.exceptions import ConfigurationError

logger = logging.getLogger(__name__)


class DatabaseConnectionError(Exception):
    """Raised when database connection operations fail."""

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error


class DatabaseManager:
    """
    High-performance database connection manager for the intelligent Q&A agent.

    Provides connection pooling, health checks, and retry logic for PostgreSQL
    with pgvector support.
    """

    def __init__(self):
        self._pool: Optional[Pool] = None
        self._connection_params: Dict[str, Any] = {}
        self._is_initialized = False
        self._health_check_interval = 30.0  # seconds
        self._max_retries = 3
        self._retry_delay = 1.0  # seconds

    async def initialize(self) -> None:
        """
        Initialize the database connection pool.

        Raises:
            DatabaseConnectionError: If initialization fails
            ConfigurationError: If configuration is invalid
        """
        if self._is_initialized:
            logger.warning("Database manager already initialized")
            return

        logger.info("Initializing database connection manager")

        try:
            self._connection_params = self._build_connection_params()
            self._pool = await self._create_pool()

            # Verify pgvector extension is available
            await self._verify_pgvector_extension()

            self._is_initialized = True
            logger.info("Database connection manager initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize database manager: {e}", exc_info=True)
            await self.close()
            raise DatabaseConnectionError(f"Database initialization failed: {e}", original_error=e)

    def _build_connection_params(self) -> Dict[str, Any]:
        """
        Build connection parameters from configuration.

        Returns:
            Dictionary of connection parameters for asyncpg

        Raises:
            ConfigurationError: If configuration is invalid
        """
        if settings.database_url:
            # Parse DATABASE_URL if provided
            try:
                parsed = urlparse(settings.database_url)
                return {
                    "host": parsed.hostname,
                    "port": parsed.port or 5432,
                    "database": parsed.path.lstrip("/") if parsed.path else "postgres",
                    "user": parsed.username,
                    "password": parsed.password,
                }
            except Exception as e:
                raise ConfigurationError(f"Invalid DATABASE_URL format: {e}") from e
        else:
            # Use individual configuration parameters
            return {
                "host": settings.database_host,
                "port": settings.database_port,
                "database": settings.database_name,
                "user": settings.database_user,
                "password": settings.database_password,
            }

    async def _create_pool(self) -> Pool:
        """
        Create asyncpg connection pool with optimized settings.

        Returns:
            Configured asyncpg Pool instance

        Raises:
            DatabaseConnectionError: If pool creation fails
        """
        try:
            logger.info(
                f"Creating connection pool: "
                f"host={self._connection_params['host']}, "
                f"port={self._connection_params['port']}, "
                f"database={self._connection_params['database']}, "
                f"min_size={settings.database_pool_min_size}, "
                f"max_size={settings.database_pool_max_size}"
            )

            pool = await asyncpg.create_pool(
                **self._connection_params,
                min_size=settings.database_pool_min_size,
                max_size=settings.database_pool_max_size,
                max_queries=settings.database_pool_max_queries,
                max_inactive_connection_lifetime=settings.database_pool_max_inactive_connection_lifetime,
                timeout=settings.database_connection_timeout,
                command_timeout=settings.database_command_timeout,
                # Connection initialization callback
                init=self._init_connection,
            )

            logger.info("Database connection pool created successfully")
            return pool

        except Exception as e:
            logger.error(f"Failed to create connection pool: {e}", exc_info=True)
            raise DatabaseConnectionError(f"Pool creation failed: {e}", original_error=e)

    async def _init_connection(self, connection: Connection) -> None:
        """
        Initialize a new database connection.

        This callback is called for each new connection in the pool.

        Args:
            connection: The new asyncpg connection
        """
        try:
            # Set connection-level parameters for optimal performance
            await connection.execute("SET search_path TO public")
            await connection.execute("SET timezone TO 'UTC'")

            # Enable pgvector extension if not already enabled
            await connection.execute("CREATE EXTENSION IF NOT EXISTS vector")

            logger.debug("Connection initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize connection: {e}", exc_info=True)
            raise

    async def _verify_pgvector_extension(self) -> None:
        """
        Verify that pgvector extension is available and working.

        Raises:
            DatabaseConnectionError: If pgvector is not available
        """
        try:
            async with self.get_connection() as conn:
                # Check if vector extension is installed
                result = await conn.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'vector')"
                )

                if not result:
                    raise DatabaseConnectionError(
                        "pgvector extension is not installed. "
                        "Please install it with: CREATE EXTENSION vector;"
                    )

                # Test basic vector operations
                await conn.execute("SELECT '[1,2,3]'::vector")

                logger.info("pgvector extension verified successfully")

        except DatabaseConnectionError:
            raise
        except Exception as e:
            logger.error(f"pgvector verification failed: {e}", exc_info=True)
            raise DatabaseConnectionError(f"pgvector verification failed: {e}", original_error=e)

    @asynccontextmanager
    async def get_connection(self) -> AsyncGenerator[Connection, None]:
        """
        Get a database connection from the pool.

        Yields:
            asyncpg Connection instance

        Raises:
            DatabaseConnectionError: If connection cannot be acquired
        """
        if not self._is_initialized or not self._pool:
            raise DatabaseConnectionError("Database manager not initialized")

        connection = None
        try:
            connection = await self._pool.acquire()
            yield connection
        except Exception as e:
            logger.error(f"Database connection error: {e}", exc_info=True)
            raise DatabaseConnectionError(f"Connection operation failed: {e}", original_error=e)
        finally:
            if connection:
                try:
                    await self._pool.release(connection)
                except Exception as e:
                    logger.error(f"Failed to release connection: {e}", exc_info=True)

    async def execute_with_retry(
        self,
        query: str,
        *args,
        max_retries: Optional[int] = None,
        retry_delay: Optional[float] = None,
    ) -> Any:
        """
        Execute a query with automatic retry on transient failures.

        Args:
            query: SQL query to execute
            *args: Query parameters
            max_retries: Maximum number of retries (defaults to instance setting)
            retry_delay: Delay between retries in seconds (defaults to instance setting)

        Returns:
            Query result

        Raises:
            DatabaseConnectionError: If all retries fail
        """
        max_retries = max_retries or self._max_retries
        retry_delay = retry_delay or self._retry_delay

        last_error = None

        for attempt in range(max_retries + 1):
            try:
                async with self.get_connection() as conn:
                    return await conn.fetch(query, *args)

            except Exception as e:
                last_error = e
                error_str = str(e).lower()

                # Check if this is a transient error worth retrying
                is_transient = any(
                    keyword in error_str
                    for keyword in [
                        "connection",
                        "timeout",
                        "temporary",
                        "unavailable",
                        "network",
                        "broken",
                        "reset",
                        "closed",
                    ]
                )

                if not is_transient or attempt == max_retries:
                    break

                logger.warning(
                    f"Transient database error on attempt {attempt + 1}/{max_retries + 1}, "
                    f"retrying in {retry_delay}s: {e}"
                )
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff

        logger.error(f"Database operation failed after {max_retries + 1} attempts: {last_error}")
        raise DatabaseConnectionError(
            f"Query failed after {max_retries + 1} attempts: {last_error}",
            original_error=last_error,
        )

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a comprehensive health check of the database connection.

        Returns:
            Dictionary containing health check results
        """
        health_status = {
            "healthy": False,
            "pool_initialized": self._is_initialized,
            "pool_size": 0,
            "pool_free_size": 0,
            "pgvector_available": False,
            "response_time_ms": None,
            "error": None,
        }

        if not self._is_initialized or not self._pool:
            health_status["error"] = "Database manager not initialized"
            return health_status

        try:
            import time

            start_time = time.time()

            # Get pool statistics
            health_status["pool_size"] = self._pool.get_size()
            health_status["pool_free_size"] = self._pool.get_idle_size()

            # Test basic connectivity and pgvector
            async with self.get_connection() as conn:
                # Basic connectivity test
                await conn.fetchval("SELECT 1")

                # Test pgvector functionality
                await conn.fetchval("SELECT '[1,2,3]'::vector <-> '[1,2,4]'::vector")
                health_status["pgvector_available"] = True

            end_time = time.time()
            health_status["response_time_ms"] = round((end_time - start_time) * 1000, 2)
            health_status["healthy"] = True

        except Exception as e:
            health_status["error"] = str(e)
            logger.error(f"Database health check failed: {e}", exc_info=True)

        return health_status

    async def close(self) -> None:
        """
        Close the database connection pool and clean up resources.
        """
        if self._pool:
            logger.info("Closing database connection pool")
            try:
                await self._pool.close()
                logger.info("Database connection pool closed successfully")
            except Exception as e:
                logger.error(f"Error closing database pool: {e}", exc_info=True)
            finally:
                self._pool = None
                self._is_initialized = False

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


async def get_database_manager() -> DatabaseManager:
    """
    Get the global database manager instance.

    Returns:
        Initialized DatabaseManager instance

    Raises:
        DatabaseConnectionError: If initialization fails
    """
    global _db_manager

    if _db_manager is None:
        _db_manager = DatabaseManager()
        await _db_manager.initialize()

    return _db_manager


async def close_database_manager() -> None:
    """
    Close the global database manager instance.
    """
    global _db_manager

    if _db_manager:
        await _db_manager.close()
        _db_manager = None


@asynccontextmanager
async def get_db_connection() -> AsyncGenerator[Connection, None]:
    """
    Convenience function to get a database connection.

    Yields:
        asyncpg Connection instance
    """
    db_manager = await get_database_manager()
    async with db_manager.get_connection() as conn:
        yield conn
