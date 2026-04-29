"""
Intelligent Reminder Agent Module

This module provides intelligent, context-aware reminders for users based on:
- Article relationships and dependencies
- Technology version updates
- User behavior patterns and optimal timing
- Personalized content recommendations

Main Components:
- IntelligentReminderAgent: Main orchestrator
- ContentAnalyzer: Analyzes article relationships
- VersionTracker: Monitors technology updates
- BehaviorAnalyzer: Learns user patterns
- TimingEngine: Determines optimal send times
- ContextGenerator: Creates rich reminder content
"""

from .behavior_analyzer import BehaviorAnalyzer
from .content_analyzer import ContentAnalyzer
from .context_generator import (
    ContentFormatter,
    ContentParser,
    ContentPrettyPrinter,
    ContextGenerator,
)
from .intelligent_reminder_agent import IntelligentReminderAgent
from .models import (
    ArticleRelationship,
    PatternType,
    RelationshipType,
    ReminderChannel,
    ReminderContext,
    ReminderEffectivenessReport,
    ReminderFrequency,
    ReminderLog,
    ReminderSettings,
    ReminderStatus,
    ReminderType,
    TechnologyVersion,
    TimingDecision,
    UserBehaviorPattern,
    UserProfile,
    VersionType,
)
from .timing_engine import TimingEngine
from .version_tracker import VersionTracker

__all__ = [
    # Main classes
    "IntelligentReminderAgent",
    "ContentAnalyzer",
    "VersionTracker",
    "BehaviorAnalyzer",
    "TimingEngine",
    "ContextGenerator",
    "ContentParser",
    "ContentFormatter",
    "ContentPrettyPrinter",
    # Enums
    "ReminderType",
    "ReminderChannel",
    "ReminderStatus",
    "ReminderFrequency",
    "RelationshipType",
    "VersionType",
    "PatternType",
    # Models
    "ReminderContext",
    "ReminderSettings",
    "ReminderLog",
    "UserProfile",
    "TimingDecision",
    "ReminderEffectivenessReport",
    "ArticleRelationship",
    "TechnologyVersion",
    "UserBehaviorPattern",
]
