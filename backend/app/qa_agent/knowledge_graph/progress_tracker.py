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

    async def sync_from_reading_list(self, user_id: UUID, article_id: str) -> None:
        """
        Auto-update node progress when a user reads an article.
        Finds nodes whose display_name appears in the article title,
        marks them as in_progress if currently not_started.
        TODO: upgrade to embedding similarity once node embeddings are populated.
        """
        import logging as _logging

        _log = _logging.getLogger(__name__)
        try:
            result = (
                self.db.db.client.table("articles").select("title").eq("id", article_id).execute()
            )
            if not result.data:
                return
            title = result.data[0].get("title", "").lower()
            if not title:
                return

            nodes_result = (
                self.db.db.client.table("knowledge_nodes").select("id, display_name").execute()
            )
            for node in nodes_result.data or []:
                node_name = (node.get("display_name") or "").lower()
                if not node_name or node_name not in title:
                    continue
                node_id = UUID(node["id"])
                cur = (
                    self.db.db.client.table("user_node_progress")
                    .select("status")
                    .eq("user_id", str(user_id))
                    .eq("node_id", str(node_id))
                    .execute()
                )
                current = NodeStatus(cur.data[0]["status"]) if cur.data else NodeStatus.NOT_STARTED
                if current == NodeStatus.NOT_STARTED:
                    await self.mark_node(user_id, node_id, NodeStatus.IN_PROGRESS)
                    _log.info(f"Auto-marked node {node_id} as in_progress for user {user_id}")
        except Exception as e:
            _log.warning(f"sync_from_reading_list failed: {e}")

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
        """Award badges based on completion percentage milestones, send Discord DM for new ones."""
        try:
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

            existing_badges = set(await self.db.get_user_achievements(user_id, domain_id))

            # Get domain name for notification
            domain_result = (
                self.db.db.client.table("technical_domains")
                .select("display_name")
                .eq("id", str(domain_id))
                .execute()
            )
            domain_name = domain_result.data[0]["display_name"] if domain_result.data else "Unknown"

            for threshold, badge_type, badge_name in _BADGE_THRESHOLDS:
                if pct >= threshold:
                    await self.db.award_badge(user_id, domain_id, badge_type, badge_name)
                    # Send Discord DM only for newly earned badges
                    if badge_name not in existing_badges:
                        await self._send_badge_notification(
                            user_id, domain_name, badge_name, pct, nodes, progress_map
                        )
        except Exception as e:
            logger.error(f"Badge check failed: {e}")

    async def _send_badge_notification(
        self,
        user_id: UUID,
        domain_name: str,
        badge_name: str,
        pct: float,
        nodes: list,
        progress_map: dict,
    ) -> None:
        """Send Discord DM when user earns a new badge."""
        try:
            from app.qa_agent.knowledge_graph.recommendation_engine import RecommendationEngine
            from app.services.notification_service import NotificationService

            # Get next recommendation
            domain_result = (
                self.db.db.client.table("technical_domains")
                .select("id")
                .eq("display_name", domain_name)
                .execute()
            )
            next_step = ""
            if domain_result.data:
                domain_id = UUID(domain_result.data[0]["id"])
                engine = RecommendationEngine(self.db)
                recs = await engine.get_recommendations(user_id, domain_id, max_results=1)
                if recs:
                    next_step = (
                        f"\n\n**Next recommended:** {recs[0].node.display_name}\n_{recs[0].reason}_"
                    )

            message = (
                f"**{badge_name}** — {domain_name}\n"
                f"You've completed **{pct:.0f}%** of the {domain_name} knowledge graph!"
                f"{next_step}"
            )

            svc = NotificationService()
            await svc.send_discord_dm(user_id=user_id, message=message)
            logger.info(f"Sent badge notification to user {user_id}: {badge_name}")
        except Exception as e:
            logger.warning(f"Badge notification failed (non-critical): {e}")
