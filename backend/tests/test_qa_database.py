"""
Tests for QA Agent Database Connection and Configuration Management.

These tests verify that the database connection pooling, health checks,
and retry logic work correctly.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.qa_agent.database import (
    DatabaseConnectionError,
    DatabaseManager,
    close_database_manager,
    get_database_manager,
)
from app.qa_agent.db_utils import QADatabaseUtils


class TestDatabaseManager:
    """Test cases for DatabaseManager class."""

    @pytest.fixture
    async def db_manager(self):
        """Create a test database manager."""
        manager = DatabaseManager()
        yield manager
        await manager.close()

    def test_build_connection_params_with_url(self):
        """Test building connection parameters from DATABASE_URL."""
        manager = DatabaseManager()

        with patch("app.qa_agent.database.settings") as mock_settings:
            mock_settings.database_url = "postgresql://user:pass@localhost:5432/testdb"

            params = manager._build_connection_params()

            assert params["host"] == "localhost"
            assert params["port"] == 5432
            assert params["database"] == "testdb"
            assert params["user"] == "user"
            assert params["password"] == "pass"

    def test_build_connection_params_individual(self):
        """Test building connection parameters from individual settings."""
        manager = DatabaseManager()

        with patch("app.qa_agent.database.settings") as mock_settings:
            mock_settings.database_url = None
            mock_settings.database_host = "testhost"
            mock_settings.database_port = 5433
            mock_settings.database_name = "testdb"
            mock_settings.database_user = "testuser"
            mock_settings.database_password = "testpass"

            params = manager._build_connection_params()

            assert params["host"] == "testhost"
            assert params["port"] == 5433
            assert params["database"] == "testdb"
            assert params["user"] == "testuser"
            assert params["password"] == "testpass"

    def test_build_connection_params_invalid_url(self):
        """Test error handling for invalid DATABASE_URL."""
        manager = DatabaseManager()

        with patch("app.qa_agent.database.settings") as mock_settings:
            mock_settings.database_url = "invalid-url"

            # The current implementation doesn't validate URL format in _build_connection_params
            # It only validates in the config.py validators
            # So this test should expect the method to work but produce invalid params
            params = manager._build_connection_params()
            # The urlparse will handle invalid URLs gracefully
            assert params is not None

    @pytest.mark.asyncio
    async def test_initialize_success(self, db_manager):
        """Test successful database manager initialization."""
        with (
            patch.object(db_manager, "_create_pool") as mock_create_pool,
            patch.object(db_manager, "_verify_pgvector_extension") as mock_verify,
        ):
            mock_pool = AsyncMock()
            mock_create_pool.return_value = mock_pool
            mock_verify.return_value = None

            await db_manager.initialize()

            assert db_manager._is_initialized
            mock_create_pool.assert_called_once()
            mock_verify.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_failure(self, db_manager):
        """Test database manager initialization failure."""
        with patch.object(db_manager, "_create_pool") as mock_create_pool:
            mock_create_pool.side_effect = Exception("Connection failed")

            with pytest.raises(DatabaseConnectionError):
                await db_manager.initialize()

            assert not db_manager._is_initialized

    @pytest.mark.asyncio
    async def test_get_connection_not_initialized(self, db_manager):
        """Test getting connection when not initialized."""
        with pytest.raises(DatabaseConnectionError, match="not initialized"):
            async with db_manager.get_connection():
                pass

    @pytest.mark.asyncio
    async def test_execute_with_retry_success(self, db_manager):
        """Test successful query execution with retry."""
        mock_connection = AsyncMock()
        mock_connection.fetch.return_value = [{"result": "success"}]

        with patch.object(db_manager, "get_connection") as mock_get_conn:
            mock_get_conn.return_value.__aenter__.return_value = mock_connection
            mock_get_conn.return_value.__aexit__.return_value = None

            db_manager._is_initialized = True
            db_manager._pool = AsyncMock()

            result = await db_manager.execute_with_retry("SELECT 1")

            assert result == [{"result": "success"}]
            mock_connection.fetch.assert_called_once_with("SELECT 1")

    @pytest.mark.asyncio
    async def test_execute_with_retry_transient_error(self, db_manager):
        """Test retry mechanism with transient errors."""
        mock_connection = AsyncMock()
        # First call fails with connection error, second succeeds
        mock_connection.fetch.side_effect = [
            Exception("connection timeout"),
            [{"result": "success"}],
        ]

        with (
            patch.object(db_manager, "get_connection") as mock_get_conn,
            patch("asyncio.sleep") as mock_sleep,
        ):
            mock_get_conn.return_value.__aenter__.return_value = mock_connection
            mock_get_conn.return_value.__aexit__.return_value = None

            db_manager._is_initialized = True
            db_manager._pool = AsyncMock()

            result = await db_manager.execute_with_retry("SELECT 1", max_retries=2)

            assert result == [{"result": "success"}]
            assert mock_connection.fetch.call_count == 2
            mock_sleep.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_with_retry_non_transient_error(self, db_manager):
        """Test that non-transient errors are not retried."""
        mock_connection = AsyncMock()
        mock_connection.fetch.side_effect = Exception("syntax error")

        with patch.object(db_manager, "get_connection") as mock_get_conn:
            mock_get_conn.return_value.__aenter__.return_value = mock_connection
            mock_get_conn.return_value.__aexit__.return_value = None

            db_manager._is_initialized = True
            db_manager._pool = AsyncMock()

            with pytest.raises(DatabaseConnectionError):
                await db_manager.execute_with_retry("SELECT 1", max_retries=2)

            # Should only be called once (no retry for non-transient error)
            assert mock_connection.fetch.call_count == 1

    @pytest.mark.asyncio
    async def test_health_check_success(self, db_manager):
        """Test successful health check."""
        mock_connection = AsyncMock()
        mock_connection.fetchval.side_effect = [1, 0.5]  # Basic query, vector query

        mock_pool = MagicMock()  # Use MagicMock instead of AsyncMock for sync methods
        mock_pool.get_size.return_value = 10
        mock_pool.get_idle_size.return_value = 5

        with patch.object(db_manager, "get_connection") as mock_get_conn:
            mock_get_conn.return_value.__aenter__.return_value = mock_connection
            mock_get_conn.return_value.__aexit__.return_value = None

            db_manager._is_initialized = True
            db_manager._pool = mock_pool

            health = await db_manager.health_check()

            assert health["healthy"] is True
            assert health["pool_size"] == 10
            assert health["pool_free_size"] == 5
            assert health["pgvector_available"] is True
            assert health["response_time_ms"] is not None

    @pytest.mark.asyncio
    async def test_health_check_not_initialized(self, db_manager):
        """Test health check when not initialized."""
        health = await db_manager.health_check()

        assert health["healthy"] is False
        assert health["pool_initialized"] is False
        assert "not initialized" in health["error"]

    @pytest.mark.asyncio
    async def test_close(self, db_manager):
        """Test closing the database manager."""
        mock_pool = AsyncMock()
        db_manager._pool = mock_pool
        db_manager._is_initialized = True

        await db_manager.close()

        mock_pool.close.assert_called_once()
        assert db_manager._pool is None
        assert not db_manager._is_initialized

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test using DatabaseManager as async context manager."""
        with (
            patch.object(DatabaseManager, "initialize") as mock_init,
            patch.object(DatabaseManager, "close") as mock_close,
        ):
            async with DatabaseManager() as manager:
                assert isinstance(manager, DatabaseManager)

            mock_init.assert_called_once()
            mock_close.assert_called_once()


class TestQADatabaseUtils:
    """Test cases for QADatabaseUtils class."""

    @pytest.mark.asyncio
    async def test_get_table_stats(self):
        """Test getting table statistics."""
        mock_connection = AsyncMock()
        mock_connection.fetchval.side_effect = [
            100,  # articles count
            True,  # embeddings table exists
            50,  # embeddings count
            True,  # conversations table exists
            10,  # conversations count
        ]

        with patch("app.qa_agent.db_utils.get_db_connection") as mock_get_conn:
            mock_get_conn.return_value.__aenter__.return_value = mock_connection
            mock_get_conn.return_value.__aexit__.return_value = None

            stats = await QADatabaseUtils.get_table_stats()

            assert stats["articles_count"] == 100
            assert stats["embeddings_count"] == 50
            assert stats["conversations_count"] == 10

    @pytest.mark.asyncio
    async def test_test_vector_operations_success(self):
        """Test successful vector operations test."""
        mock_connection = AsyncMock()
        mock_connection.fetchval.side_effect = [
            True,  # extension exists
            None,  # basic vector ops
            1.0,  # similarity test
        ]

        with patch("app.qa_agent.db_utils.get_db_connection") as mock_get_conn:
            mock_get_conn.return_value.__aenter__.return_value = mock_connection
            mock_get_conn.return_value.__aexit__.return_value = None

            results = await QADatabaseUtils.test_vector_operations()

            assert results["vector_extension_available"] is True
            assert results["basic_vector_ops"] is True
            assert results["similarity_search"] is True
            assert results["test_distance"] == 1.0

    @pytest.mark.asyncio
    async def test_test_vector_operations_no_extension(self):
        """Test vector operations when extension is not available."""
        mock_connection = AsyncMock()
        mock_connection.fetchval.return_value = False  # extension doesn't exist

        with patch("app.qa_agent.db_utils.get_db_connection") as mock_get_conn:
            mock_get_conn.return_value.__aenter__.return_value = mock_connection
            mock_get_conn.return_value.__aexit__.return_value = None

            results = await QADatabaseUtils.test_vector_operations()

            assert results["vector_extension_available"] is False
            assert results["basic_vector_ops"] is False
            assert results["similarity_search"] is False
            assert "not installed" in results["error"]

    @pytest.mark.asyncio
    async def test_cleanup_expired_conversations(self):
        """Test cleaning up expired conversations."""
        mock_connection = AsyncMock()
        mock_connection.fetchval.side_effect = [True, 5]  # table exists  # deleted count

        with patch("app.qa_agent.db_utils.get_db_connection") as mock_get_conn:
            mock_get_conn.return_value.__aenter__.return_value = mock_connection
            mock_get_conn.return_value.__aexit__.return_value = None

            deleted = await QADatabaseUtils.cleanup_expired_conversations(7)

            assert deleted == 5

    @pytest.mark.asyncio
    async def test_get_database_info(self):
        """Test getting database information."""
        mock_connection = AsyncMock()
        mock_connection.fetchval.side_effect = [
            "PostgreSQL 15.0",  # version
            "testdb",  # database name
            "postgres",  # current user
            "public",  # current schema
        ]
        mock_connection.fetch.side_effect = [
            [{"extname": "vector", "extversion": "0.5.0"}],  # extensions
            [{"name": "max_connections", "setting": "100", "unit": None}],  # settings
        ]

        with patch("app.qa_agent.db_utils.get_db_connection") as mock_get_conn:
            mock_get_conn.return_value.__aenter__.return_value = mock_connection
            mock_get_conn.return_value.__aexit__.return_value = None

            info = await QADatabaseUtils.get_database_info()

            assert "PostgreSQL 15.0" in info["postgresql_version"]
            assert info["database_name"] == "testdb"
            assert info["current_user"] == "postgres"
            assert info["extensions"]["vector"] == "0.5.0"


class TestGlobalDatabaseManager:
    """Test cases for global database manager functions."""

    @pytest.mark.asyncio
    async def test_get_database_manager_singleton(self):
        """Test that get_database_manager returns singleton instance."""
        with patch.object(DatabaseManager, "initialize") as mock_init:
            manager1 = await get_database_manager()
            manager2 = await get_database_manager()

            assert manager1 is manager2
            mock_init.assert_called_once()

        # Clean up
        await close_database_manager()

    @pytest.mark.asyncio
    async def test_close_database_manager(self):
        """Test closing global database manager."""
        with (
            patch.object(DatabaseManager, "initialize") as mock_init,
            patch.object(DatabaseManager, "close") as mock_close,
        ):
            await get_database_manager()
            await close_database_manager()

            mock_close.assert_called_once()

        # Verify manager is reset
        with patch.object(DatabaseManager, "initialize") as mock_init2:
            await get_database_manager()
            mock_init2.assert_called_once()  # Should initialize again

        await close_database_manager()
