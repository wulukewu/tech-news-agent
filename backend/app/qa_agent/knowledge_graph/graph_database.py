"""
GraphDatabase - CRUD layer for knowledge graph tables.
Handles nodes, edges, domains, and user progress.
"""
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.services.supabase_service import SupabaseService

from .models import (
    DependencyType,
    KnowledgeNode,
    NodeDependency,
    NodeStatus,
    TechnicalDomain,
)

logger = logging.getLogger(__name__)


class GraphDatabase:
    def __init__(self, supabase: Optional[SupabaseService] = None):
        self.db = supabase or SupabaseService()

    # ── Domains ──────────────────────────────────────────────────────────────

    async def get_all_domains(self, user_id: Optional[UUID] = None) -> List[TechnicalDomain]:
        """Return built-in domains + user's own custom domains."""
        # Built-ins
        result = (
            self.db.client.table("technical_domains")
            .select("*")
            .is_("created_by", "null")
            .execute()
        )
        domains = [self._row_to_domain(r) for r in (result.data or [])]
        # User's custom domains
        if user_id:
            custom = (
                self.db.client.table("technical_domains")
                .select("*")
                .eq("created_by", str(user_id))
                .execute()
            )
            domains += [self._row_to_domain(r) for r in (custom.data or [])]
        return domains

    async def get_domain_by_name(
        self, name: str, user_id: Optional[UUID] = None
    ) -> Optional[TechnicalDomain]:
        """Find domain by name. Built-ins are global; custom domains are user-scoped."""
        # Try built-in first (created_by IS NULL)
        result = (
            self.db.client.table("technical_domains")
            .select("*")
            .eq("name", name)
            .is_("created_by", "null")
            .execute()
        )
        if result.data:
            return self._row_to_domain(result.data[0])
        # Try user-owned custom domain
        if user_id:
            result = (
                self.db.client.table("technical_domains")
                .select("*")
                .eq("name", name)
                .eq("created_by", str(user_id))
                .execute()
            )
            if result.data:
                return self._row_to_domain(result.data[0])
        return None

    async def create_domain(
        self,
        name: str,
        display_name: str,
        description: str,
        icon: str = "📚",
        created_by: Optional[UUID] = None,
    ) -> TechnicalDomain:
        data = {
            "name": name,
            "display_name": display_name,
            "description": description,
            "icon": icon,
            "is_builtin": False,
            "created_by": str(created_by) if created_by else None,
        }
        result = self.db.client.table("technical_domains").insert(data).execute()
        return self._row_to_domain(result.data[0])

    # ── Nodes ─────────────────────────────────────────────────────────────────

    async def get_nodes_by_domain(self, domain_id: UUID) -> List[KnowledgeNode]:
        result = (
            self.db.client.table("knowledge_nodes")
            .select("*")
            .eq("domain_id", str(domain_id))
            .execute()
        )
        return [self._row_to_node(r) for r in (result.data or [])]

    async def upsert_node(
        self, domain_id: UUID, node_data: Dict[str, Any], skip_embedding: bool = False
    ) -> KnowledgeNode:
        # Generate embedding for semantic search (best-effort, non-blocking)
        # Skip when caller will do batch embedding instead
        embedding = None
        if not skip_embedding:
            try:
                from app.services.voyage_embedding import embed_text

                text = f"{node_data.get('display_name', node_data['name'])} {node_data.get('description', '')} {' '.join(node_data.get('tags', []))}"
                embedding = await embed_text(text.strip())
            except Exception:
                pass

        data: Dict[str, Any] = {
            "domain_id": str(domain_id),
            "name": node_data["name"],
            "display_name": node_data.get("display_name", node_data["name"]),
            "description": node_data.get("description", ""),
            "difficulty": node_data.get("difficulty", 3),
            "estimated_hours": node_data.get("estimated_hours", 1.0),
            "tags": node_data.get("tags", []),
            "metadata": node_data.get("metadata", {}),
        }
        if embedding:
            data["embedding"] = embedding

        result = (
            self.db.client.table("knowledge_nodes")
            .upsert(data, on_conflict="domain_id,name")
            .execute()
        )
        return self._row_to_node(result.data[0])

    # ── Edges ─────────────────────────────────────────────────────────────────

    async def get_edges_by_domain(self, domain_id: UUID) -> List[NodeDependency]:
        nodes = await self.get_nodes_by_domain(domain_id)
        node_ids = [str(n.id) for n in nodes]
        if not node_ids:
            return []
        result = (
            self.db.client.table("node_dependencies")
            .select("*")
            .in_("source_node_id", node_ids)
            .execute()
        )
        return [self._row_to_edge(r) for r in (result.data or [])]

    async def upsert_edge(
        self,
        source_id: UUID,
        target_id: UUID,
        dep_type: DependencyType = DependencyType.PREREQUISITE,
        confidence: float = 1.0,
    ) -> None:
        data = {
            "source_node_id": str(source_id),
            "target_node_id": str(target_id),
            "dependency_type": dep_type.value,
            "confidence_score": confidence,
        }
        self.db.client.table("node_dependencies").upsert(
            data, on_conflict="source_node_id,target_node_id,dependency_type"
        ).execute()

    # ── User Progress ─────────────────────────────────────────────────────────

    async def get_user_progress(self, user_id: UUID, domain_id: UUID) -> Dict[str, NodeStatus]:
        """Returns {node_id: status} for all nodes in domain."""
        nodes = await self.get_nodes_by_domain(domain_id)
        node_ids = [str(n.id) for n in nodes]
        if not node_ids:
            return {}
        result = (
            self.db.client.table("user_node_progress")
            .select("node_id,status")
            .eq("user_id", str(user_id))
            .in_("node_id", node_ids)
            .execute()
        )
        return {r["node_id"]: NodeStatus(r["status"]) for r in (result.data or [])}

    async def update_node_status(self, user_id: UUID, node_id: UUID, status: NodeStatus) -> None:
        from datetime import datetime, timezone

        data: Dict[str, Any] = {
            "user_id": str(user_id),
            "node_id": str(node_id),
            "status": status.value,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        if status == NodeStatus.COMPLETED:
            data["completed_at"] = datetime.now(timezone.utc).isoformat()

        self.db.client.table("user_node_progress").upsert(
            data, on_conflict="user_id,node_id"
        ).execute()

    async def get_user_achievements(self, user_id: UUID, domain_id: UUID) -> List[str]:
        result = (
            self.db.client.table("user_achievements")
            .select("badge_type")
            .eq("user_id", str(user_id))
            .eq("domain_id", str(domain_id))
            .execute()
        )
        return [r["badge_type"] for r in (result.data or [])]

    async def award_badge(
        self, user_id: UUID, domain_id: UUID, badge_type: str, badge_name: str
    ) -> None:
        self.db.client.table("user_achievements").upsert(
            {
                "user_id": str(user_id),
                "domain_id": str(domain_id),
                "badge_type": badge_type,
                "badge_name": badge_name,
            },
            on_conflict="user_id,domain_id,badge_type",
        ).execute()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _row_to_domain(self, row: Dict) -> TechnicalDomain:
        return TechnicalDomain(
            id=UUID(row["id"]),
            name=row["name"],
            display_name=row["display_name"],
            description=row.get("description") or "",
            icon=row.get("icon") or "📚",
            is_builtin=row.get("is_builtin", False),
        )

    def _row_to_node(self, row: Dict) -> KnowledgeNode:
        return KnowledgeNode(
            id=UUID(row["id"]),
            domain_id=UUID(row["domain_id"]),
            name=row["name"],
            display_name=row["display_name"],
            description=row.get("description") or "",
            difficulty=row.get("difficulty", 3),
            estimated_hours=row.get("estimated_hours", 1.0),
            tags=row.get("tags") or [],
            metadata=row.get("metadata") or {},
        )

    def _row_to_edge(self, row: Dict) -> NodeDependency:
        return NodeDependency(
            source_node_id=UUID(row["source_node_id"]),
            target_node_id=UUID(row["target_node_id"]),
            dependency_type=DependencyType(row.get("dependency_type", "prerequisite")),
            confidence_score=row.get("confidence_score", 1.0),
        )
