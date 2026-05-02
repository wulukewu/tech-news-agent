"""
REST API endpoints for the Knowledge Graph Agent.
Requirements: 7.1-7.2, 6.1-6.6
"""
import logging
from typing import Any, Dict, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from ..api.auth import get_current_user
from ..qa_agent.knowledge_graph import (
    KnowledgeGraphBuilder,
    NodeStatus,
    ProgressTracker,
    RecommendationEngine,
)
from ..qa_agent.knowledge_graph.graph_database import GraphDatabase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/knowledge-graph", tags=["knowledge-graph"])


# ── Request / Response models ─────────────────────────────────────────────────


class CreateDomainRequest(BaseModel):
    name: str
    display_name: str
    description: str = ""
    icon: str = "📚"


class UpdateNodeStatusRequest(BaseModel):
    status: str  # not_started | in_progress | completed


# ── Helpers ───────────────────────────────────────────────────────────────────


async def _get_builder() -> KnowledgeGraphBuilder:
    return KnowledgeGraphBuilder()


async def _get_db() -> GraphDatabase:
    return GraphDatabase()


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.get("/domains")
async def list_domains(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: GraphDatabase = Depends(_get_db),
) -> List[Dict]:
    """List built-in domains + user's own custom domains."""
    user_id = current_user["user_id"]
    domains = await db.get_all_domains(user_id)

    result = []
    for domain in domains:
        progress_map = await db.get_user_progress(user_id, domain.id)
        nodes = await db.get_nodes_by_domain(domain.id)
        total = len(nodes)
        completed = sum(1 for n in nodes if progress_map.get(str(n.id)) == NodeStatus.COMPLETED)
        domain.node_count = total
        domain.user_progress_pct = (completed / total * 100) if total > 0 else 0.0
        result.append(domain.to_dict())

    return result


@router.post("/domains")
async def create_domain(
    body: CreateDomainRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    builder: KnowledgeGraphBuilder = Depends(_get_builder),
) -> Dict:
    """Create a new custom domain and build its graph via LLM."""
    user_id = current_user["user_id"]
    domain = await builder.get_or_build_domain(body.name, user_id)
    return domain.to_dict()


@router.get("/domains/{domain_name}")
async def get_domain_graph(
    domain_name: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    builder: KnowledgeGraphBuilder = Depends(_get_builder),
) -> Dict:
    """Get full graph data for a domain (builds it if it doesn't exist)."""
    user_id = current_user["user_id"]
    graph = await builder.get_graph_data(domain_name, user_id)
    return graph.to_dict()


@router.get("/domains/{domain_name}/progress")
async def get_domain_progress(
    domain_name: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: GraphDatabase = Depends(_get_db),
) -> Dict:
    """Get user's learning progress for a domain."""
    user_id = current_user["user_id"]
    domain = await db.get_domain_by_name(domain_name, user_id)
    if not domain:
        raise HTTPException(status_code=404, detail=f"Domain '{domain_name}' not found")

    tracker = ProgressTracker(db)
    progress = await tracker.get_domain_progress(user_id, domain.id, domain.display_name)
    return progress.to_dict()


@router.post("/nodes/{node_id}/complete")
async def complete_node(
    node_id: str,
    body: UpdateNodeStatusRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: GraphDatabase = Depends(_get_db),
) -> Dict:
    """Update a node's learning status."""
    try:
        status = NodeStatus(body.status)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status '{body.status}'. Must be: not_started, in_progress, completed",
        )

    user_id = current_user["user_id"]
    tracker = ProgressTracker(db)
    await tracker.mark_node(user_id, UUID(node_id), status)
    return {"success": True, "node_id": node_id, "status": status.value}


@router.get("/domains/{domain_name}/recommendations")
async def get_recommendations(
    domain_name: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    max_results: int = Query(default=5, ge=1, le=10),
    db: GraphDatabase = Depends(_get_db),
) -> List[Dict]:
    """Get personalized learning recommendations for a domain."""
    user_id = current_user["user_id"]
    domain = await db.get_domain_by_name(domain_name, user_id)
    if not domain:
        raise HTTPException(status_code=404, detail=f"Domain '{domain_name}' not found")

    engine = RecommendationEngine(db)
    recs = await engine.get_recommendations(user_id, domain.id, max_results)
    return [r.to_dict() for r in recs]


@router.get("/export/{domain_name}")
async def export_domain(
    domain_name: str,
    format: str = Query(default="json", regex="^(json|graphml)$"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    builder: KnowledgeGraphBuilder = Depends(_get_builder),
) -> Any:
    """Export domain graph as JSON or GraphML."""
    user_id = current_user["user_id"]
    graph = await builder.get_graph_data(domain_name, user_id)

    if format == "graphml":
        return _to_graphml(graph)

    return graph.to_dict()


@router.post("/domains/{domain_name}/rebuild")
async def rebuild_domain(
    domain_name: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    builder: KnowledgeGraphBuilder = Depends(_get_builder),
) -> Dict:
    """Force rebuild a domain's graph via LLM (incremental)."""
    user_id = current_user["user_id"]
    domain = await builder.rebuild_domain(domain_name, user_id)
    return domain.to_dict()


@router.get("/nodes/{node_id}/articles")
async def get_node_articles(
    node_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    limit: int = Query(default=5, ge=1, le=20),
    db: GraphDatabase = Depends(_get_db),
) -> List[Dict]:
    """
    Get articles related to a knowledge node.
    Uses semantic search (pgvector cosine similarity) when node embedding exists,
    falls back to keyword matching otherwise.
    See docs/improvements/knowledge-graph-article-linking.md
    """
    user_id = current_user["user_id"]

    # Get node info
    result = db.db.client.table("knowledge_nodes").select("*").eq("id", node_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Node not found")

    node = result.data[0]
    node_embedding = node.get("embedding")

    matched_articles: List[Dict] = []

    # ── Semantic search (preferred) ───────────────────────────────────────────
    if node_embedding:
        try:
            sem_result = db.db.client.rpc(
                "match_articles_by_embedding",
                {
                    "query_embedding": node_embedding,
                    "match_threshold": 0.6,
                    "match_count": limit,
                },
            ).execute()
            matched_articles = sem_result.data or []
        except Exception:
            pass  # Fall through to keyword search

    # ── Keyword fallback ──────────────────────────────────────────────────────
    if not matched_articles:
        terms = [node["display_name"], node["name"].replace("_", " ")]
        terms.extend((node.get("tags") or [])[:3])
        seen_ids: set = set()
        for term in terms:
            if len(matched_articles) >= limit:
                break
            res = (
                db.db.client.table("articles")
                .select("id, title, url, published_at")
                .ilike("title", f"%{term}%")
                .order("published_at", desc=True)
                .limit(limit)
                .execute()
            )
            for row in res.data or []:
                if row["id"] not in seen_ids:
                    seen_ids.add(row["id"])
                    matched_articles.append(row)

    # ── Attach reading status ─────────────────────────────────────────────────
    for article in matched_articles[:limit]:
        rl = (
            db.db.client.table("reading_list")
            .select("status")
            .eq("user_id", str(user_id))
            .eq("article_id", article["id"])
            .execute()
        )
        article["reading_status"] = rl.data[0]["status"] if rl.data else None

    return matched_articles[:limit]


# ── GraphML export helper ─────────────────────────────────────────────────────


def _to_graphml(graph) -> str:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<graphml xmlns="http://graphml.graphdrawing.org/graphml">',
        f'  <graph id="{graph.domain.name}" edgedefault="directed">',
    ]
    for node in graph.nodes:
        lines.append(
            f'    <node id="{node.id}"><data key="label">{node.display_name}</data>'
            f'<data key="status">{node.status.value}</data></node>'
        )
    for i, edge in enumerate(graph.edges):
        lines.append(
            f'    <edge id="e{i}" source="{edge.source_node_id}" '
            f'target="{edge.target_node_id}" type="{edge.dependency_type.value}"/>'
        )
    lines += ["  </graph>", "</graphml>"]
    return "\n".join(lines)
