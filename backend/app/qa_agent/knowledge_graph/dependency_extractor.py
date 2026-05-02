"""
DependencyExtractor - Uses LLM to extract knowledge node dependencies from a domain name.
Returns a list of nodes and edges that form the domain's skill tree.
Requirements: 9.1-9.6, 1.1-1.5
"""
import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)

_EXTRACTION_PROMPT = """\
You are a technical curriculum designer. Given a technology domain, generate a structured knowledge graph.

Domain: {domain}

Return a JSON object with this exact structure:
{{
  "nodes": [
    {{
      "name": "snake_case_unique_id",
      "display_name": "Human Readable Name",
      "description": "1-2 sentence description",
      "difficulty": 1-5,
      "estimated_hours": float,
      "tags": ["tag1", "tag2"]
    }}
  ],
  "edges": [
    {{
      "source": "prerequisite_node_name",
      "target": "dependent_node_name",
      "type": "prerequisite|related|extends",
      "confidence": 0.0-1.0
    }}
  ]
}}

Rules:
- Generate 15-25 nodes covering the full learning path from beginner to advanced
- difficulty: 1=beginner, 5=expert
- edges: source must be learned BEFORE target (prerequisite), or is related/extends
- No circular dependencies in prerequisite edges
- Use English for node names and display_names
- Return ONLY valid JSON, no markdown
"""


class DependencyExtractor:
    def __init__(self, llm_service: Optional[LLMService] = None):
        self.llm = llm_service or LLMService()

    async def extract_domain_graph(
        self, domain_name: str
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Returns (nodes, edges) for the given domain.
        Falls back to empty lists on failure.
        """
        try:
            prompt = _EXTRACTION_PROMPT.format(domain=domain_name)
            response = await self.llm.generate_response(
                prompt=prompt,
                model="llama-3.3-70b-versatile",
                max_tokens=4096,
                temperature=0.3,
            )
            return self._parse_response(response)
        except Exception as e:
            logger.error(f"DependencyExtractor failed for domain '{domain_name}': {e}")
            return [], []

    def _parse_response(self, response: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Parse LLM JSON response, handling common formatting issues."""
        text = response.strip()
        # Strip markdown code fences if present
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            # Try to extract JSON object from surrounding text
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                data = json.loads(text[start:end])
            else:
                logger.error("Could not parse LLM response as JSON")
                return [], []

        nodes = data.get("nodes", [])
        edges = data.get("edges", [])

        # Validate and sanitize
        valid_nodes = []
        node_names = set()
        for n in nodes:
            if not isinstance(n, dict) or "name" not in n:
                continue
            n.setdefault("display_name", n["name"].replace("_", " ").title())
            n.setdefault("description", "")
            n.setdefault("difficulty", 3)
            n.setdefault("estimated_hours", 2.0)
            n.setdefault("tags", [])
            n["difficulty"] = max(1, min(5, int(n["difficulty"])))
            valid_nodes.append(n)
            node_names.add(n["name"])

        valid_edges = []
        seen_edges = set()
        for e in edges:
            if not isinstance(e, dict):
                continue
            src, tgt = e.get("source"), e.get("target")
            if not src or not tgt or src not in node_names or tgt not in node_names:
                continue
            if src == tgt:
                continue
            key = (src, tgt, e.get("type", "prerequisite"))
            if key in seen_edges:
                continue
            seen_edges.add(key)
            e.setdefault("type", "prerequisite")
            e.setdefault("confidence", 0.9)
            valid_edges.append(e)

        # Detect and remove cycles in prerequisite edges
        valid_edges = self._remove_cycles(valid_edges)

        logger.info(f"Extracted {len(valid_nodes)} nodes and {len(valid_edges)} edges")
        return valid_nodes, valid_edges

    def _remove_cycles(self, edges: List[Dict]) -> List[Dict]:
        """Remove edges that create cycles using DFS cycle detection."""
        prereq_edges = [e for e in edges if e.get("type") == "prerequisite"]
        other_edges = [e for e in edges if e.get("type") != "prerequisite"]

        # Build adjacency for cycle detection
        graph: Dict[str, List[str]] = {}
        for e in prereq_edges:
            graph.setdefault(e["source"], []).append(e["target"])

        def has_cycle(node: str, visited: set, rec_stack: set) -> bool:
            visited.add(node)
            rec_stack.add(node)
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor, visited, rec_stack):
                        return True
                elif neighbor in rec_stack:
                    return True
            rec_stack.discard(node)
            return False

        all_nodes = set(graph.keys()) | {t for targets in graph.values() for t in targets}
        visited: set = set()
        for node in all_nodes:
            if node not in visited:
                if has_cycle(node, visited, set()):
                    # Remove the last added edge that caused the cycle
                    logger.warning(f"Cycle detected involving node '{node}', removing last edge")
                    if prereq_edges:
                        removed = prereq_edges.pop()
                        graph.get(removed["source"], []).remove(removed["target"])

        return prereq_edges + other_edges
