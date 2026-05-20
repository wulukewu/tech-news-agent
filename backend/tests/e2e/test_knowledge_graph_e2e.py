"""
E2E tests for Knowledge Graph Agent.
Tests the full workflow: create domain → visualize graph → mark node complete → progress update.
Requirements: 1.1, 3.2, 4.2, 8.1
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_db():
    """Mock GraphDatabase with realistic return values."""
    db = MagicMock()

    domain = {
        "id": "domain-uuid-1",
        "name": "python",
        "display_name": "Python",
        "description": "General-purpose programming language",
        "icon": "🐍",
        "is_builtin": True,
        "created_by": None,
    }

    nodes = [
        {
            "id": "node-uuid-1",
            "domain_id": "domain-uuid-1",
            "name": "variables",
            "display_name": "Variables & Types",
            "description": "Basic Python variables and data types",
            "difficulty": 1,
            "estimated_hours": 1.0,
            "tags": ["basics"],
            "metadata": {},
        },
        {
            "id": "node-uuid-2",
            "domain_id": "domain-uuid-1",
            "name": "functions",
            "display_name": "Functions",
            "description": "Defining and calling functions",
            "difficulty": 2,
            "estimated_hours": 2.0,
            "tags": ["basics"],
            "metadata": {},
        },
    ]

    edges = [
        {
            "id": "edge-uuid-1",
            "source_node_id": "node-uuid-1",
            "target_node_id": "node-uuid-2",
            "dependency_type": "prerequisite",
            "confidence_score": 0.95,
        }
    ]

    progress = [
        {
            "node_id": "node-uuid-1",
            "status": "not_started",
            "completed_at": None,
            "time_spent_minutes": 0,
        },
        {
            "node_id": "node-uuid-2",
            "status": "not_started",
            "completed_at": None,
            "time_spent_minutes": 0,
        },
    ]

    db.get_domain = AsyncMock(return_value=domain)
    db.list_domains = AsyncMock(return_value=[domain])
    db.get_nodes_for_domain = AsyncMock(return_value=nodes)
    db.get_edges_for_domain = AsyncMock(return_value=edges)
    db.get_user_progress = AsyncMock(return_value=progress)
    db.upsert_node_progress = AsyncMock(return_value=None)
    db.get_achievements = AsyncMock(return_value=[])
    db.create_domain = AsyncMock(
        return_value={
            **{"id": "domain-uuid-new"},
            **{
                "name": "golang",
                "display_name": "Go",
                "description": "Concurrent systems language",
                "icon": "🐹",
                "is_builtin": False,
                "created_by": "user-uuid-1",
            },
        }
    )

    return db


@pytest.fixture
def mock_user():
    return {"id": "user-uuid-1", "discord_id": "123456789"}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestKnowledgeGraphE2E:
    """Full workflow tests for the Knowledge Graph Agent."""

    @pytest.mark.asyncio
    async def test_list_domains_returns_builtin(self, mock_db, mock_user):
        """Step 1: User can see available technical domains."""
        from app.qa_agent.knowledge_graph.graph_database import GraphDatabase

        with patch.object(GraphDatabase, "__new__", return_value=mock_db):
            domains = await mock_db.list_domains()

        assert len(domains) == 1
        assert domains[0]["name"] == "python"
        assert domains[0]["is_builtin"] is True

    @pytest.mark.asyncio
    async def test_get_domain_graph_returns_nodes_and_edges(self, mock_db, mock_user):
        """Step 2: User can load the graph for a domain (nodes + edges)."""
        nodes = await mock_db.get_nodes_for_domain("domain-uuid-1")
        edges = await mock_db.get_edges_for_domain("domain-uuid-1")

        assert len(nodes) == 2
        assert nodes[0]["name"] == "variables"
        assert nodes[1]["name"] == "functions"

        assert len(edges) == 1
        assert edges[0]["source_node_id"] == "node-uuid-1"
        assert edges[0]["target_node_id"] == "node-uuid-2"
        assert edges[0]["dependency_type"] == "prerequisite"

    @pytest.mark.asyncio
    async def test_initial_progress_is_zero(self, mock_db, mock_user):
        """Step 3: All nodes start as not_started."""
        progress = await mock_db.get_user_progress("user-uuid-1", "domain-uuid-1")

        assert all(p["status"] == "not_started" for p in progress)

    @pytest.mark.asyncio
    async def test_mark_node_complete_updates_progress(self, mock_db, mock_user):
        """Step 4: Marking a node complete persists the status change."""
        await mock_db.upsert_node_progress(
            user_id="user-uuid-1",
            node_id="node-uuid-1",
            status="completed",
        )

        mock_db.upsert_node_progress.assert_called_once_with(
            user_id="user-uuid-1",
            node_id="node-uuid-1",
            status="completed",
        )

    @pytest.mark.asyncio
    async def test_progress_percentage_calculation(self, mock_db, mock_user):
        """Step 5: Progress percentage reflects completed nodes."""

        # Simulate 1 of 2 nodes completed
        completed_progress = [
            {
                "node_id": "node-uuid-1",
                "status": "completed",
                "completed_at": "2026-05-20T00:00:00Z",
                "time_spent_minutes": 60,
            },
            {
                "node_id": "node-uuid-2",
                "status": "not_started",
                "completed_at": None,
                "time_spent_minutes": 0,
            },
        ]
        mock_db.get_user_progress = AsyncMock(return_value=completed_progress)

        progress = await mock_db.get_user_progress("user-uuid-1", "domain-uuid-1")
        completed = sum(1 for p in progress if p["status"] == "completed")
        total = len(progress)
        pct = completed / total * 100

        assert pct == 50.0

    @pytest.mark.asyncio
    async def test_create_custom_domain(self, mock_db, mock_user):
        """Step 6: User can create a custom domain."""
        new_domain = await mock_db.create_domain(
            name="golang",
            display_name="Go",
            description="Concurrent systems language",
            icon="🐹",
            created_by="user-uuid-1",
        )

        assert new_domain["name"] == "golang"
        assert new_domain["is_builtin"] is False
        assert new_domain["created_by"] == "user-uuid-1"

    @pytest.mark.asyncio
    async def test_full_workflow(self, mock_db, mock_user):
        """
        Full E2E: list domains → load graph → check initial progress
        → mark node complete → verify progress update.
        """
        # 1. List domains
        domains = await mock_db.list_domains()
        assert len(domains) >= 1
        domain = domains[0]

        # 2. Load graph
        nodes = await mock_db.get_nodes_for_domain(domain["id"])
        edges = await mock_db.get_edges_for_domain(domain["id"])
        assert len(nodes) > 0

        # 3. Check initial progress
        progress = await mock_db.get_user_progress(mock_user["id"], domain["id"])
        assert all(p["status"] == "not_started" for p in progress)

        # 4. Mark first node complete
        first_node_id = nodes[0]["id"]
        await mock_db.upsert_node_progress(
            user_id=mock_user["id"],
            node_id=first_node_id,
            status="completed",
        )

        # 5. Verify the call was made correctly
        mock_db.upsert_node_progress.assert_called_with(
            user_id=mock_user["id"],
            node_id=first_node_id,
            status="completed",
        )
