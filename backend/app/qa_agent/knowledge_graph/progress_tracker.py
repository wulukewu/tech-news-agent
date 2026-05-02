"""
ProgressTracker - Tracks user learning progress in knowledge graphs.
Requirements: 3.1-3.6, 4.1
"""
import logging
from typing import Optional
from uuid import UUID

from .graph_database import GraphDatabase
from .models import DomainProgress, NodeStatus

logger = logging.getLogger(__name__)

_BADGE_THRESHOLDS = [
    (25, "starter", "🌱 Getting Started"),
    (50, "halfway", "⚡ Halfway There"),
    (75, "advanced", "🔥 Advanced Learner"),
    (100, "master", "🏆 Domain Master"),
]


class ProgressTracker:
    def __init__(self, db: Optional[GraphDatabase] = None):
        self.db = db or GraphDatabase()

    async def mark_node(self, user_id: UUID, node_id: UUID, status: NodeStatus) -> None:
        """Update a node's status and award badges if milestones are reached."""
        await self.db.update_node_status(user_id, node_id, status)

        # Check for badge awards after completion
        if status == NodeStatus.COMPLETED:
            await self._check_badges(user_id, node_id)

    async def get_domain_progress(
        self, user_id: UUID, domain_id: UUID, domain_name: str
    ) -> DomainProgress:
        nodes = await self.db.get_nodes_by_domain(domain_id)
        progress_map = await self.db.get_user_progress(user_id, domain_id)
        badges = await self.db.get_user_achievements(user_id, domain_id)

        total = len(nodes)
        completed = sum(1 for n in nodes if progress_map.get(str(n.id)) == NodeStatus.COMPLETED)
        in_progress = sum(1 for n in nodes if progress_map.get(str(n.id)) == NodeStatus.IN_PROGRESS)
        pct = (completed / total * 100) if total > 0 else 0.0

        return DomainProgress(
            domain_id=domain_id,
            domain_name=domain_name,
            total_nodes=total,
            completed_nodes=completed,
            in_progress_nodes=in_progress,
            progress_pct=round(pct, 1),
            badges=badges,
        )

    async def _check_badges(self, user_id: UUID, node_id: UUID) -> None:
        """Award badges based on completion percentage milestones."""
        try:
            # Get the domain for this node
            result = (
                self.db.db.client.table("knowledge_nodes")
                .select("domain_id")
                .eq("id", str(node_id))
                .execute()
            )
            if not result.data:
                return
            domain_id = UUID(result.data[0]["domain_id"])

            nodes = await self.db.get_nodes_by_domain(domain_id)
            progress_map = await self.db.get_user_progress(user_id, domain_id)
            total = len(nodes)
            if total == 0:
                return
            completed = sum(1 for n in nodes if progress_map.get(str(n.id)) == NodeStatus.COMPLETED)
            pct = completed / total * 100

            for threshold, badge_type, badge_name in _BADGE_THRESHOLDS:
                if pct >= threshold:
                    await self.db.award_badge(user_id, domain_id, badge_type, badge_name)
        except Exception as e:
            logger.error(f"Badge check failed: {e}")
