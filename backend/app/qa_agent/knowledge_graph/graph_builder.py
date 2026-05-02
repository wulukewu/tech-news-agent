"""
KnowledgeGraphBuilder - Builds and manages domain skill trees.
Orchestrates DependencyExtractor + GraphDatabase.
Requirements: 3.1-3.2, 1.1-1.4, 8.5-8.6
"""
import logging
from typing import Optional
from uuid import UUID

from app.services.supabase_service import SupabaseService

from .dependency_extractor import DependencyExtractor
from .graph_database import GraphDatabase
from .models import DependencyType, GraphData, NodeStatus, TechnicalDomain

logger = logging.getLogger(__name__)


class KnowledgeGraphBuilder:
    def __init__(
        self,
        supabase: Optional[SupabaseService] = None,
        extractor: Optional[DependencyExtractor] = None,
    ):
        self.db = GraphDatabase(supabase)
        self.extractor = extractor or DependencyExtractor()

    async def get_or_build_domain(
        self, domain_name: str, user_id: Optional[UUID] = None
    ) -> TechnicalDomain:
        """Return existing domain or build it from scratch via LLM."""
        domain = await self.db.get_domain_by_name(domain_name)
        if domain:
            return domain

        # Create domain record first
        display_name = domain_name.replace("-", " ").title()
        domain = await self.db.create_domain(
            name=domain_name,
            display_name=display_name,
            description=f"Knowledge graph for {display_name}",
            created_by=user_id,
        )

        # Extract nodes/edges via LLM
        logger.info(f"Building knowledge graph for domain '{domain_name}' via LLM")
        nodes_data, edges_data = await self.extractor.extract_domain_graph(display_name)

        # Persist nodes
        node_name_to_id = {}
        for node_data in nodes_data:
            node = await self.db.upsert_node(domain.id, node_data)
            node_name_to_id[node_data["name"]] = node.id

        # Persist edges
        for edge_data in edges_data:
            src_id = node_name_to_id.get(edge_data["source"])
            tgt_id = node_name_to_id.get(edge_data["target"])
            if src_id and tgt_id:
                dep_type = DependencyType(edge_data.get("type", "prerequisite"))
                await self.db.upsert_edge(
                    src_id, tgt_id, dep_type, edge_data.get("confidence", 0.9)
                )

        logger.info(
            f"Built domain '{domain_name}': {len(nodes_data)} nodes, {len(edges_data)} edges"
        )
        return domain

    async def get_graph_data(self, domain_name: str, user_id: Optional[UUID] = None) -> GraphData:
        """Return full graph data with user progress applied."""
        domain = await self.get_or_build_domain(domain_name, user_id)
        nodes = await self.db.get_nodes_by_domain(domain.id)
        edges = await self.db.get_edges_by_domain(domain.id)

        # Apply user progress
        progress_map = {}
        if user_id:
            progress_map = await self.db.get_user_progress(user_id, domain.id)

        # Determine which nodes are unlocked (all prerequisites completed)
        prereq_map: dict = {str(n.id): [] for n in nodes}
        for edge in edges:
            if edge.dependency_type == DependencyType.PREREQUISITE:
                prereq_map.setdefault(str(edge.target_node_id), []).append(str(edge.source_node_id))

        completed_ids = {
            nid for nid, status in progress_map.items() if status == NodeStatus.COMPLETED
        }

        for node in nodes:
            nid = str(node.id)
            node.status = progress_map.get(nid, NodeStatus.NOT_STARTED)
            prereqs = prereq_map.get(nid, [])
            node.is_unlocked = all(p in completed_ids for p in prereqs)

        total = len(nodes)
        completed = sum(1 for n in nodes if n.status == NodeStatus.COMPLETED)
        progress_pct = (completed / total * 100) if total > 0 else 0.0

        domain.node_count = total
        domain.user_progress_pct = progress_pct

        return GraphData(
            domain=domain,
            nodes=nodes,
            edges=edges,
            user_progress_pct=progress_pct,
        )

    async def rebuild_domain(self, domain_name: str) -> TechnicalDomain:
        """Force rebuild a domain's graph via LLM (incremental: only adds new nodes)."""
        domain = await self.db.get_domain_by_name(domain_name)
        if not domain:
            return await self.get_or_build_domain(domain_name)

        display_name = domain.display_name
        nodes_data, edges_data = await self.extractor.extract_domain_graph(display_name)

        node_name_to_id = {}
        for node_data in nodes_data:
            node = await self.db.upsert_node(domain.id, node_data)
            node_name_to_id[node_data["name"]] = node.id

        for edge_data in edges_data:
            src_id = node_name_to_id.get(edge_data["source"])
            tgt_id = node_name_to_id.get(edge_data["target"])
            if src_id and tgt_id:
                dep_type = DependencyType(edge_data.get("type", "prerequisite"))
                await self.db.upsert_edge(
                    src_id, tgt_id, dep_type, edge_data.get("confidence", 0.9)
                )

        return domain
