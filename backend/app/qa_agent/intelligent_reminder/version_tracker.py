"""
Version Tracker for the Intelligent Reminder Agent.
Monitors technology framework versions and detects updates.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

import httpx

from ...services.supabase_service import SupabaseService
from .models import ReminderContext, TechnologyVersion, VersionType

logger = logging.getLogger(__name__)


class VersionTracker:
    """Tracks technology framework versions and updates"""

    def __init__(self, supabase_service: Optional[SupabaseService] = None):
        self.supabase_service = supabase_service or SupabaseService()
        self.version_sources = {
            "npm": self._check_npm_version,
            "github": self._check_github_releases,
            "pypi": self._check_pypi_version,
        }

    async def check_version_updates(self) -> List[TechnologyVersion]:
        """Check for version updates across all registered technologies"""
        try:
            # Get all registered technologies
            registered_techs = await self._get_registered_technologies()

            updates = []
            async with httpx.AsyncClient(timeout=30.0) as client:
                for tech in registered_techs:
                    try:
                        update = await self._check_single_technology(client, tech)
                        if update:
                            updates.append(update)
                    except Exception as e:
                        logger.error(f"Error checking {tech['technology_name']}: {e}")

            # Store updates in database
            if updates:
                await self._store_version_updates(updates)

            return updates

        except Exception as e:
            logger.error(f"Error checking version updates: {e}")
            return []

    async def register_technology(
        self, name: str, current_version: str, source_url: str
    ) -> TechnologyVersion:
        """Register a new technology for version tracking"""
        try:
            version_data = {
                "technology_name": name,
                "current_version": current_version,
                "version_type": self._classify_version_type(current_version, current_version),
                "source_url": source_url,
                "importance_level": 3,  # Default medium importance
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            }

            result = (
                await self.supabase_service.client.table("technology_registry")
                .upsert(version_data)
                .execute()
            )

            if result.data:
                return TechnologyVersion(**result.data[0])

        except Exception as e:
            logger.error(f"Error registering technology {name}: {e}")
            raise

    async def get_users_interested_in_technology(self, tech_name: str) -> List[UUID]:
        """Get users who have read articles about a specific technology"""
        try:
            # Query articles related to the technology
            query = """
            SELECT DISTINCT rl.user_id
            FROM reading_list rl
            JOIN articles a ON a.id = rl.article_id
            WHERE LOWER(a.title) LIKE LOWER($1)
               OR LOWER(a.content) LIKE LOWER($1)
               OR LOWER(a.ai_summary) LIKE LOWER($1)
            """

            search_term = f"%{tech_name}%"
            result = await self.supabase_service.client.rpc(
                "execute_sql", {"query": query, "params": [search_term]}
            ).execute()

            return [UUID(row["user_id"]) for row in (result.data or [])]

        except Exception as e:
            logger.error(f"Error getting interested users for {tech_name}: {e}")
            return []

    async def generate_version_update_context(
        self, tech_version: TechnologyVersion
    ) -> ReminderContext:
        """Generate context for a version update reminder"""
        try:
            # Determine update significance
            significance = self._get_update_significance(
                tech_version.version_type, tech_version.importance_level
            )

            title = f"{tech_version.technology_name} {tech_version.current_version} Released"

            if tech_version.version_type == VersionType.MAJOR:
                description = f"Major update available for {tech_version.technology_name}! "
                description += "This may include breaking changes and new features."
            elif tech_version.version_type == VersionType.MINOR:
                description = f"New features available in {tech_version.technology_name} "
                description += f"{tech_version.current_version}."
            else:
                description = f"Bug fixes and improvements in {tech_version.technology_name} "
                description += f"{tech_version.current_version}."

            if tech_version.release_notes:
                description += f"\n\nKey changes: {tech_version.release_notes[:200]}..."

            return ReminderContext(
                title=title,
                description=description,
                version_info={
                    "technology": tech_version.technology_name,
                    "new_version": tech_version.current_version,
                    "previous_version": tech_version.previous_version,
                    "version_type": tech_version.version_type.value,
                    "importance_level": tech_version.importance_level,
                    "release_date": tech_version.release_date.isoformat()
                    if tech_version.release_date
                    else None,
                },
                reading_time_estimate=5,  # Assume 5 minutes to review update
                priority_score=significance,
                action_url=tech_version.source_url,
            )

        except Exception as e:
            logger.error(f"Error generating version update context: {e}")
            return ReminderContext(
                title=f"{tech_version.technology_name} Update Available",
                description="A new version has been released.",
            )

    async def _get_registered_technologies(self) -> List[Dict[str, Any]]:
        """Get all registered technologies from database"""
        try:
            result = (
                await self.supabase_service.client.table("technology_registry")
                .select("*")
                .order("updated_at", desc=False)
                .execute()
            )
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Error getting registered technologies: {e}")
            return []

    async def _check_single_technology(
        self, client: httpx.AsyncClient, tech: Dict[str, Any]
    ) -> Optional[TechnologyVersion]:
        """Check for updates for a single technology"""
        source_url = tech.get("source_url", "")

        # Determine source type and check accordingly
        if "npmjs.com" in source_url or "npm" in source_url.lower():
            return await self._check_npm_version(client, tech)
        elif "github.com" in source_url:
            return await self._check_github_releases(client, tech)
        elif "pypi.org" in source_url:
            return await self._check_pypi_version(client, tech)
        else:
            logger.warning(f"Unknown source type for {tech['technology_name']}: {source_url}")
            return None

    async def _check_npm_version(
        self, client: httpx.AsyncClient, tech: Dict[str, Any]
    ) -> Optional[TechnologyVersion]:
        """Check NPM package version"""
        try:
            package_name = tech["technology_name"].lower()
            url = f"https://registry.npmjs.org/{package_name}/latest"

            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                latest_version = data.get("version")

                if latest_version and latest_version != tech["current_version"]:
                    return await self._create_version_update(tech, latest_version, data)

        except Exception as e:
            logger.error(f"Error checking NPM version for {tech['technology_name']}: {e}")

        return None

    async def _check_github_releases(
        self, client: httpx.AsyncClient, tech: Dict[str, Any]
    ) -> Optional[TechnologyVersion]:
        """Check GitHub releases"""
        try:
            # Extract owner/repo from URL
            url_parts = tech["source_url"].split("/")
            if len(url_parts) >= 5:
                owner = url_parts[-2]
                repo = url_parts[-1]

                api_url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"

                response = await client.get(api_url)
                if response.status_code == 200:
                    data = response.json()
                    latest_version = data.get("tag_name", "").lstrip("v")

                    if latest_version and latest_version != tech["current_version"]:
                        return await self._create_version_update(tech, latest_version, data)

        except Exception as e:
            logger.error(f"Error checking GitHub releases for {tech['technology_name']}: {e}")

        return None

    async def _check_pypi_version(
        self, client: httpx.AsyncClient, tech: Dict[str, Any]
    ) -> Optional[TechnologyVersion]:
        """Check PyPI package version"""
        try:
            package_name = tech["technology_name"].lower()
            url = f"https://pypi.org/pypi/{package_name}/json"

            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                latest_version = data.get("info", {}).get("version")

                if latest_version and latest_version != tech["current_version"]:
                    return await self._create_version_update(tech, latest_version, data)

        except Exception as e:
            logger.error(f"Error checking PyPI version for {tech['technology_name']}: {e}")

        return None

    async def _create_version_update(
        self, tech: Dict[str, Any], new_version: str, release_data: Dict[str, Any]
    ) -> TechnologyVersion:
        """Create a version update record"""
        version_type = self._classify_version_type(tech["current_version"], new_version)
        importance_level = self._calculate_importance_level(version_type, release_data)

        return TechnologyVersion(
            id=UUID(tech["id"]),
            technology_name=tech["technology_name"],
            current_version=new_version,
            previous_version=tech["current_version"],
            version_type=version_type,
            release_date=self._extract_release_date(release_data),
            release_notes=self._extract_release_notes(release_data),
            importance_level=importance_level,
            source_url=tech["source_url"],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    def _classify_version_type(self, old_version: str, new_version: str) -> VersionType:
        """Classify version update type (major/minor/patch)"""
        try:
            old_parts = [int(x) for x in old_version.split(".")]
            new_parts = [int(x) for x in new_version.split(".")]

            # Pad with zeros if needed
            max_len = max(len(old_parts), len(new_parts))
            old_parts.extend([0] * (max_len - len(old_parts)))
            new_parts.extend([0] * (max_len - len(new_parts)))

            if new_parts[0] > old_parts[0]:
                return VersionType.MAJOR
            elif new_parts[1] > old_parts[1]:
                return VersionType.MINOR
            else:
                return VersionType.PATCH

        except (ValueError, IndexError):
            # Fallback for non-semantic versions
            return VersionType.MINOR

    def _calculate_importance_level(
        self, version_type: VersionType, release_data: Dict[str, Any]
    ) -> int:
        """Calculate importance level (1-5) based on version type and release data"""
        base_importance = {VersionType.MAJOR: 5, VersionType.MINOR: 3, VersionType.PATCH: 2}

        importance = base_importance.get(version_type, 3)

        # Adjust based on release notes keywords
        release_notes = self._extract_release_notes(release_data).lower()

        if any(keyword in release_notes for keyword in ["security", "vulnerability", "critical"]):
            importance = min(5, importance + 2)
        elif any(keyword in release_notes for keyword in ["breaking", "deprecated"]):
            importance = min(5, importance + 1)

        return importance

    def _extract_release_date(self, release_data: Dict[str, Any]) -> Optional[datetime]:
        """Extract release date from release data"""
        try:
            # GitHub format
            if "published_at" in release_data:
                return datetime.fromisoformat(release_data["published_at"].replace("Z", "+00:00"))

            # NPM format
            if "time" in release_data:
                return datetime.fromisoformat(release_data["time"].replace("Z", "+00:00"))

        except (ValueError, KeyError):
            pass

        return datetime.now()

    def _extract_release_notes(self, release_data: Dict[str, Any]) -> str:
        """Extract release notes from release data"""
        # GitHub format
        if "body" in release_data:
            return release_data["body"][:1000]  # Limit length

        # NPM format
        if "description" in release_data:
            return release_data["description"][:1000]

        return ""

    def _get_update_significance(self, version_type: VersionType, importance_level: int) -> float:
        """Calculate update significance score (0-1)"""
        type_scores = {VersionType.MAJOR: 0.9, VersionType.MINOR: 0.6, VersionType.PATCH: 0.3}

        base_score = type_scores.get(version_type, 0.5)
        importance_multiplier = importance_level / 5.0

        return min(1.0, base_score * importance_multiplier)

    async def _store_version_updates(self, updates: List[TechnologyVersion]) -> None:
        """Store version updates in database"""
        try:
            data = []
            for update in updates:
                data.append(
                    {
                        "id": str(update.id),
                        "technology_name": update.technology_name,
                        "current_version": update.current_version,
                        "previous_version": update.previous_version,
                        "version_type": update.version_type.value,
                        "release_date": update.release_date.isoformat()
                        if update.release_date
                        else None,
                        "release_notes": update.release_notes,
                        "importance_level": update.importance_level,
                        "source_url": update.source_url,
                        "updated_at": datetime.now().isoformat(),
                    }
                )

            await self.supabase_service.client.table("technology_registry").upsert(data).execute()

        except Exception as e:
            logger.error(f"Error storing version updates: {e}")
