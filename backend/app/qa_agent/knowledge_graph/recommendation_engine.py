"""
RecommendationEngine - Suggests next nodes to learn based on user progress.
Requirements: 4.1-4.6
"""

import logging
from typing import List, Optional
from uuid import UUID

from .graph_database import GraphDatabase
from .models import DependencyType, KnowledgeNode, LearningRecommendation, NodeStatus

logger = logging.getLogger(__name__)


class RecommendationEngine:
    def __init__(self, db: Optional[GraphDatabase] = None):
        self.db = db or GraphDatabase()

    async def get_recommendations(
        self,
        user_id: UUID,
        domain_id: UUID,
        max_results: int = 5,
    ) -> List[LearningRecommendation]:
        """Return 3-5 prioritized learning recommendations."""
        nodes = await self.db.get_nodes_by_domain(domain_id)
        edges = await self.db.get_edges_by_domain(domain_id)
        progress_map = await self.db.get_user_progress(user_id, domain_id)

        completed_ids = {nid for nid, s in progress_map.items() if s == NodeStatus.COMPLETED}
        in_progress_ids = {nid for nid, s in progress_map.items() if s == NodeStatus.IN_PROGRESS}

        # Build prerequisite map: node_id -> [prerequisite_ids]
        prereq_map: dict = {str(n.id): [] for n in nodes}
        for edge in edges:
            if edge.dependency_type == DependencyType.PREREQUISITE:
                prereq_map.setdefault(str(edge.target_node_id), []).append(str(edge.source_node_id))

        candidates: List[KnowledgeNode] = []
        for node in nodes:
            nid = str(node.id)
            if nid in completed_ids:
                continue
            prereqs = prereq_map.get(nid, [])
            if all(p in completed_ids for p in prereqs):
                candidates.append(node)

        # Score candidates: in-progress first, then by difficulty (easier first)
        def score(n: KnowledgeNode) -> float:
            nid = str(n.id)
            base = 10.0 if nid in in_progress_ids else 0.0
            # Prefer lower difficulty when starting out
            difficulty_bonus = (6 - n.difficulty) * 1.0
            return base + difficulty_bonus

        candidates.sort(key=score, reverse=True)
        candidates = candidates[:max_results]

        recommendations = []
        for node in candidates:
            nid = str(node.id)
            if nid in in_progress_ids:
                reason = "Already in progress — finish to unlock next steps."
            elif not prereq_map.get(nid):
                reason = f"No prerequisites — good entry point for {node.display_name}."
            else:
                n_prereqs = len(prereq_map.get(nid, []))
                reason = f"All {n_prereqs} prerequisite{'s' if n_prereqs > 1 else ''} done. You're ready for this."

            recommendations.append(
                LearningRecommendation(
                    node=node,
                    reason=reason,
                    priority_score=score(node),
                    estimated_hours=node.estimated_hours,
                )
            )

        return recommendations
