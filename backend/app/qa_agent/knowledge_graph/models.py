"""Knowledge Graph Agent models."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID


class NodeStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class DependencyType(str, Enum):
    PREREQUISITE = "prerequisite"
    RELATED = "related"
    EXTENDS = "extends"


@dataclass
class KnowledgeNode:
    id: UUID
    domain_id: UUID
    name: str
    display_name: str
    description: str
    difficulty: int  # 1-5
    estimated_hours: float
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    # runtime fields (not in DB)
    status: NodeStatus = NodeStatus.NOT_STARTED
    is_unlocked: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "domain_id": str(self.domain_id),
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "difficulty": self.difficulty,
            "estimated_hours": self.estimated_hours,
            "tags": self.tags,
            "status": self.status.value,
            "is_unlocked": self.is_unlocked,
        }


@dataclass
class NodeDependency:
    source_node_id: UUID
    target_node_id: UUID
    dependency_type: DependencyType
    confidence_score: float = 1.0


@dataclass
class TechnicalDomain:
    id: UUID
    name: str
    display_name: str
    description: str
    icon: str
    is_builtin: bool
    node_count: int = 0
    user_progress_pct: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "icon": self.icon,
            "is_builtin": self.is_builtin,
            "node_count": self.node_count,
            "user_progress_pct": self.user_progress_pct,
        }


@dataclass
class GraphData:
    """Full graph data for a domain, ready for D3.js rendering."""

    domain: TechnicalDomain
    nodes: List[KnowledgeNode]
    edges: List[NodeDependency]
    user_progress_pct: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain": self.domain.to_dict(),
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [
                {
                    "source": str(e.source_node_id),
                    "target": str(e.target_node_id),
                    "type": e.dependency_type.value,
                    "confidence": e.confidence_score,
                }
                for e in self.edges
            ],
            "user_progress_pct": self.user_progress_pct,
        }


@dataclass
class LearningRecommendation:
    node: KnowledgeNode
    reason: str
    priority_score: float
    estimated_hours: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node": self.node.to_dict(),
            "reason": self.reason,
            "priority_score": self.priority_score,
            "estimated_hours": self.estimated_hours,
        }


@dataclass
class DomainProgress:
    domain_id: UUID
    domain_name: str
    total_nodes: int
    completed_nodes: int
    in_progress_nodes: int
    progress_pct: float
    badges: List[str] = field(default_factory=list)
    completed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain_id": str(self.domain_id),
            "domain_name": self.domain_name,
            "total_nodes": self.total_nodes,
            "completed_nodes": self.completed_nodes,
            "in_progress_nodes": self.in_progress_nodes,
            "progress_pct": self.progress_pct,
            "badges": self.badges,
        }
