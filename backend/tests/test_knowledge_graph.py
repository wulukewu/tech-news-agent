"""
E2E integration tests for Knowledge Graph Agent.
Tests: domain creation → graph build → progress tracking → recommendations.
Requirements: 1.1, 3.2, 4.2, 8.1
"""

import sys
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

# Stub heavy deps
_STUBS = [
    "asyncpg",
    "groq",
    "discord",
    "discord.ext",
    "discord.ext.commands",
    "discord.ui",
    "apscheduler",
    "apscheduler.schedulers",
    "apscheduler.schedulers.asyncio",
    "httpx",
    "supabase",
    "postgrest",
    "gotrue",
    "storage3",
    "realtime",
    "feedparser",
    "aiohttp",
    "aiofiles",
]
for _mod in _STUBS:
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()

from app.qa_agent.knowledge_graph.dependency_extractor import DependencyExtractor  # noqa: E402
from app.qa_agent.knowledge_graph.models import (  # noqa: E402
    DependencyType,
    KnowledgeNode,
    NodeStatus,
)
from app.qa_agent.knowledge_graph.progress_tracker import ProgressTracker  # noqa: E402
from app.qa_agent.knowledge_graph.recommendation_engine import RecommendationEngine  # noqa: E402

# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_node(name: str, difficulty: int = 2, domain_id=None) -> KnowledgeNode:
    return KnowledgeNode(
        id=uuid4(),
        domain_id=domain_id or uuid4(),
        name=name,
        display_name=name.replace("_", " ").title(),
        description=f"Learn {name}",
        difficulty=difficulty,
        estimated_hours=2.0,
    )


def _make_db_mock(nodes, progress_map=None, edges=None):
    """Build a GraphDatabase mock with preset return values."""
    db = MagicMock()
    db.get_nodes_by_domain = AsyncMock(return_value=nodes)
    db.get_user_progress = AsyncMock(return_value=progress_map or {})
    db.get_edges_by_domain = AsyncMock(return_value=edges or [])
    db.get_user_achievements = AsyncMock(return_value=[])
    db.update_node_status = AsyncMock()
    db.award_badge = AsyncMock()
    db.db = MagicMock()
    db.db.client = MagicMock()
    db.db.client.table.return_value.select.return_value.eq.return_value.execute.return_value = (
        MagicMock(data=[{"domain_id": str(uuid4())}])
    )
    return db


# ── DependencyExtractor ───────────────────────────────────────────────────────


class TestDependencyExtractor:
    def test_parse_valid_json(self):
        extractor = DependencyExtractor.__new__(DependencyExtractor)
        raw = """{
            "nodes": [
                {"name": "basics", "display_name": "Basics", "difficulty": 1, "estimated_hours": 2},
                {"name": "advanced", "display_name": "Advanced", "difficulty": 3, "estimated_hours": 4}
            ],
            "edges": [
                {"source": "basics", "target": "advanced", "type": "prerequisite", "confidence": 0.9}
            ]
        }"""
        nodes, edges = extractor._parse_response(raw)
        assert len(nodes) == 2
        assert len(edges) == 1
        assert edges[0]["source"] == "basics"
        assert edges[0]["target"] == "advanced"

    def test_strips_markdown_fences(self):
        extractor = DependencyExtractor.__new__(DependencyExtractor)
        raw = '```json\n{"nodes": [], "edges": []}\n```'
        nodes, edges = extractor._parse_response(raw)
        assert nodes == []
        assert edges == []

    def test_removes_self_loops(self):
        extractor = DependencyExtractor.__new__(DependencyExtractor)
        raw = """{
            "nodes": [{"name": "a", "difficulty": 1}],
            "edges": [{"source": "a", "target": "a", "type": "prerequisite"}]
        }"""
        nodes, edges = extractor._parse_response(raw)
        assert len(edges) == 0

    def test_removes_unknown_node_references(self):
        extractor = DependencyExtractor.__new__(DependencyExtractor)
        raw = """{
            "nodes": [{"name": "a", "difficulty": 1}],
            "edges": [{"source": "a", "target": "nonexistent", "type": "prerequisite"}]
        }"""
        nodes, edges = extractor._parse_response(raw)
        assert len(edges) == 0

    def test_cycle_detection_removes_cycle_edge(self):
        extractor = DependencyExtractor.__new__(DependencyExtractor)
        # a → b → c → a (cycle)
        edges = [
            {"source": "a", "target": "b", "type": "prerequisite"},
            {"source": "b", "target": "c", "type": "prerequisite"},
            {"source": "c", "target": "a", "type": "prerequisite"},
        ]
        result = extractor._remove_cycles(edges)
        # After cycle removal, no cycle should remain
        # Build adjacency and verify no cycle
        graph: dict = {}
        for e in result:
            graph.setdefault(e["source"], []).append(e["target"])

        def has_cycle(node, visited, stack):
            visited.add(node)
            stack.add(node)
            for n in graph.get(node, []):
                if n not in visited:
                    if has_cycle(n, visited, stack):
                        return True
                elif n in stack:
                    return True
            stack.discard(node)
            return False

        all_nodes = set(graph.keys()) | {t for ts in graph.values() for t in ts}
        visited: set = set()
        for node in all_nodes:
            if node not in visited:
                assert not has_cycle(node, visited, set()), "Cycle still present after removal"


# ── RecommendationEngine ──────────────────────────────────────────────────────


class TestRecommendationEngine:
    @pytest.mark.asyncio
    async def test_recommends_unlocked_nodes(self):
        domain_id = uuid4()
        n1 = _make_node("basics", difficulty=1, domain_id=domain_id)
        n2 = _make_node("intermediate", difficulty=2, domain_id=domain_id)
        n3 = _make_node("advanced", difficulty=3, domain_id=domain_id)

        from app.qa_agent.knowledge_graph.models import NodeDependency

        edges = [
            NodeDependency(n1.id, n2.id, DependencyType.PREREQUISITE),
            NodeDependency(n2.id, n3.id, DependencyType.PREREQUISITE),
        ]
        # n1 completed → n2 unlocked, n3 still locked
        progress = {str(n1.id): NodeStatus.COMPLETED}
        db = _make_db_mock([n1, n2, n3], progress, edges)

        engine = RecommendationEngine(db)
        recs = await engine.get_recommendations(uuid4(), domain_id, max_results=5)

        rec_ids = {r.node.id for r in recs}
        assert n2.id in rec_ids, "n2 should be recommended (n1 completed)"
        assert n3.id not in rec_ids, "n3 should NOT be recommended (n2 not completed)"
        assert n1.id not in rec_ids, "n1 should NOT be recommended (already completed)"

    @pytest.mark.asyncio
    async def test_in_progress_nodes_ranked_first(self):
        domain_id = uuid4()
        n1 = _make_node("a", difficulty=3, domain_id=domain_id)
        n2 = _make_node("b", difficulty=1, domain_id=domain_id)

        progress = {str(n1.id): NodeStatus.IN_PROGRESS}
        db = _make_db_mock([n1, n2], progress)

        engine = RecommendationEngine(db)
        recs = await engine.get_recommendations(uuid4(), domain_id, max_results=5)

        assert recs[0].node.id == n1.id, "In-progress node should rank first"

    @pytest.mark.asyncio
    async def test_respects_max_results(self):
        domain_id = uuid4()
        nodes = [_make_node(f"node_{i}", domain_id=domain_id) for i in range(10)]
        db = _make_db_mock(nodes)

        engine = RecommendationEngine(db)
        recs = await engine.get_recommendations(uuid4(), domain_id, max_results=3)
        assert len(recs) <= 3


# ── ProgressTracker ───────────────────────────────────────────────────────────


class TestProgressTracker:
    @pytest.mark.asyncio
    async def test_get_domain_progress_calculates_correctly(self):
        domain_id = uuid4()
        nodes = [_make_node(f"n{i}", domain_id=domain_id) for i in range(4)]
        progress = {
            str(nodes[0].id): NodeStatus.COMPLETED,
            str(nodes[1].id): NodeStatus.COMPLETED,
            str(nodes[2].id): NodeStatus.IN_PROGRESS,
        }
        db = _make_db_mock(nodes, progress)

        tracker = ProgressTracker(db)
        result = await tracker.get_domain_progress(uuid4(), domain_id, "Test Domain")

        assert result.total_nodes == 4
        assert result.completed_nodes == 2
        assert result.in_progress_nodes == 1
        assert result.progress_pct == 50.0

    @pytest.mark.asyncio
    async def test_mark_node_calls_update(self):
        db = _make_db_mock([])
        tracker = ProgressTracker(db)
        user_id = uuid4()
        node_id = uuid4()

        await tracker.mark_node(user_id, node_id, NodeStatus.COMPLETED)
        db.update_node_status.assert_called_once_with(user_id, node_id, NodeStatus.COMPLETED)
