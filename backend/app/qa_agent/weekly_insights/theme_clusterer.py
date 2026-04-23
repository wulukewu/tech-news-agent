"""
Theme Clusterer

Groups articles with similar themes into Topic Clusters.
Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
"""

import logging
from collections import Counter, defaultdict
from typing import Any

logger = logging.getLogger(__name__)


class ThemeClusterer:
    """Clusters articles by shared themes and technologies."""

    def cluster(self, articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Group articles into topic clusters based on shared themes/technologies.

        Returns a list of clusters sorted by article count (descending), each with:
          - name: cluster label
          - articles: list of article dicts in this cluster
          - article_count: number of articles
          - strength: normalized relevance score (0-1)
          - top_keywords: most common keywords across articles
        """
        # Build a frequency map: theme/tech -> list of articles
        theme_to_articles: dict[str, list[dict[str, Any]]] = defaultdict(list)

        for article in articles:
            tags = set(article.get("themes", [])) | set(article.get("technologies", []))
            for tag in tags:
                theme_to_articles[tag.lower()].append(article)

        if not theme_to_articles:
            return []

        # Keep only themes that appear in ≥2 articles
        clusters_raw = {theme: arts for theme, arts in theme_to_articles.items() if len(arts) >= 2}

        if not clusters_raw:
            # Fall back: one cluster per domain
            return self._cluster_by_domain(articles)

        # Sort by frequency
        sorted_themes = sorted(clusters_raw.items(), key=lambda x: len(x[1]), reverse=True)

        # Deduplicate: each article appears in at most its top cluster
        seen_ids: set[str] = set()
        clusters: list[dict[str, Any]] = []

        max_count = sorted_themes[0][1].__len__() if sorted_themes else 1

        for theme, arts in sorted_themes[:20]:  # cap at 20 clusters
            unique_arts = [a for a in arts if a.get("id") not in seen_ids]
            if not unique_arts:
                continue
            for a in unique_arts:
                seen_ids.add(a.get("id"))

            # Collect top keywords
            kw_counter: Counter = Counter()
            for a in unique_arts:
                kw_counter.update(a.get("keywords", []))
            top_kw = [kw for kw, _ in kw_counter.most_common(5)]

            clusters.append(
                {
                    "name": theme.title(),
                    "articles": unique_arts,
                    "article_count": len(unique_arts),
                    "strength": round(len(unique_arts) / max_count, 2),
                    "top_keywords": top_kw,
                }
            )

        return clusters

    def _cluster_by_domain(self, articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Fallback: cluster by domain when no shared themes found."""
        domain_map: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for a in articles:
            domain_map[a.get("domain", "other")].append(a)

        clusters = []
        max_count = max((len(v) for v in domain_map.values()), default=1)
        for domain, arts in sorted(domain_map.items(), key=lambda x: len(x[1]), reverse=True):
            clusters.append(
                {
                    "name": domain.replace("_", "/").title(),
                    "articles": arts,
                    "article_count": len(arts),
                    "strength": round(len(arts) / max_count, 2),
                    "top_keywords": [],
                }
            )
        return clusters
