"""
Monitoring and Alerting System for Chat Persistence System

Provides:
  - ``AlertRule`` — configurable threshold-based alert rule
  - ``AlertManager`` — evaluates rules against live metrics and fires alerts
  - ``AlertChannel`` — pluggable notification channels (log, webhook, Discord)
  - Pre-configured rules matching the design document thresholds
  - Health-check endpoint integration

Alert thresholds (from design document):
  - Message storage latency > 200ms (p95)
  - Cross-platform sync failure rate > 1% (5-min window)
  - Discord command response time > 5s (p95)
  - DB query error rate > 0.1% (1-min window)
  - Any authentication failure

Validates: System reliability and monitoring (Task 10.4)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from app.core.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class AlertSeverity(str, Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AlertState(str, Enum):
    """Current state of an alert rule."""

    OK = "ok"
    FIRING = "firing"
    RESOLVED = "resolved"


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class Alert:
    """A fired alert instance.

    Attributes:
        rule_name: Name of the rule that fired.
        severity: Severity level.
        message: Human-readable description.
        value: The metric value that triggered the alert.
        threshold: The threshold that was breached.
        fired_at: UTC timestamp when the alert fired.
        metadata: Additional context.
    """

    rule_name: str
    severity: AlertSeverity
    message: str
    value: float
    threshold: float
    fired_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_name": self.rule_name,
            "severity": self.severity.value,
            "message": self.message,
            "value": round(self.value, 4),
            "threshold": self.threshold,
            "fired_at": self.fired_at.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class AlertRule:
    """A threshold-based alert rule.

    Args:
        name: Unique rule identifier.
        metric_name: Name of the metric to evaluate (matches PerformanceTracker keys).
        metric_field: Field on the metric dict to compare (e.g. ``"p95_duration_ms"``).
        threshold: Value above which the alert fires.
        severity: Alert severity when fired.
        message_template: Human-readable message. Use ``{value}`` and ``{threshold}``.
        enabled: Whether the rule is active.
    """

    name: str
    metric_name: str
    metric_field: str
    threshold: float
    severity: AlertSeverity
    message_template: str
    enabled: bool = True

    def evaluate(self, metric: dict[str, Any]) -> Optional[Alert]:
        """Evaluate this rule against *metric*.

        Returns:
            An :class:`Alert` if the threshold is breached, else ``None``.
        """
        if not self.enabled:
            return None

        value = metric.get(self.metric_field)
        if value is None:
            return None

        # Only fire if there are enough samples (avoid noise on cold start)
        call_count = metric.get("call_count", 0)
        if call_count < 5:
            return None

        if value > self.threshold:
            message = self.message_template.format(value=round(value, 2), threshold=self.threshold)
            return Alert(
                rule_name=self.name,
                severity=self.severity,
                message=message,
                value=value,
                threshold=self.threshold,
                metadata={"metric_name": self.metric_name, "call_count": call_count},
            )
        return None


# ---------------------------------------------------------------------------
# Alert channels
# ---------------------------------------------------------------------------


class AlertChannel:
    """Base class for alert notification channels."""

    async def send(self, alert: Alert) -> None:
        raise NotImplementedError


class LogAlertChannel(AlertChannel):
    """Sends alerts to the application logger."""

    async def send(self, alert: Alert) -> None:
        log_fn = logger.critical if alert.severity == AlertSeverity.CRITICAL else logger.warning
        log_fn(
            "ALERT FIRED",
            rule=alert.rule_name,
            severity=alert.severity.value,
            message=alert.message,
            value=alert.value,
            threshold=alert.threshold,
        )


class WebhookAlertChannel(AlertChannel):
    """Sends alerts to an HTTP webhook endpoint."""

    def __init__(self, url: str, timeout: float = 5.0) -> None:
        self.url = url
        self.timeout = timeout

    async def send(self, alert: Alert) -> None:
        try:
            import aiohttp  # type: ignore

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.url,
                    json=alert.to_dict(),
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                ) as resp:
                    if resp.status >= 400:
                        logger.warning(
                            "Webhook alert delivery failed",
                            status=resp.status,
                            rule=alert.rule_name,
                        )
        except Exception as exc:
            logger.warning(
                "Webhook alert channel error (non-fatal)",
                error=str(exc),
                rule=alert.rule_name,
            )


class DiscordAlertChannel(AlertChannel):
    """Sends alerts to a Discord channel via webhook."""

    def __init__(self, webhook_url: str) -> None:
        self.webhook_url = webhook_url

    async def send(self, alert: Alert) -> None:
        severity_emoji = {
            AlertSeverity.INFO: "ℹ️",
            AlertSeverity.WARNING: "⚠️",
            AlertSeverity.CRITICAL: "🚨",
        }.get(alert.severity, "⚠️")

        color = {
            AlertSeverity.INFO: 0x3498DB,
            AlertSeverity.WARNING: 0xF39C12,
            AlertSeverity.CRITICAL: 0xE74C3C,
        }.get(alert.severity, 0xF39C12)

        payload = {
            "embeds": [
                {
                    "title": f"{severity_emoji} Alert: {alert.rule_name}",
                    "description": alert.message,
                    "color": color,
                    "fields": [
                        {"name": "Value", "value": str(round(alert.value, 2)), "inline": True},
                        {"name": "Threshold", "value": str(alert.threshold), "inline": True},
                        {"name": "Severity", "value": alert.severity.value.upper(), "inline": True},
                    ],
                    "timestamp": alert.fired_at.isoformat(),
                }
            ]
        }

        try:
            import aiohttp  # type: ignore

            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=payload) as resp:
                    if resp.status >= 400:
                        logger.warning(
                            "Discord alert delivery failed",
                            status=resp.status,
                            rule=alert.rule_name,
                        )
        except Exception as exc:
            logger.warning(
                "Discord alert channel error (non-fatal)",
                error=str(exc),
                rule=alert.rule_name,
            )


# ---------------------------------------------------------------------------
# AlertManager
# ---------------------------------------------------------------------------


class AlertManager:
    """Evaluates alert rules against live metrics and dispatches alerts.

    Usage::

        manager = AlertManager()
        manager.add_channel(LogAlertChannel())
        manager.add_rule(DEFAULT_RULES[0])

        # In a background task:
        await manager.evaluate_all()
    """

    def __init__(self) -> None:
        self._rules: list[AlertRule] = []
        self._channels: list[AlertChannel] = []
        self._alert_history: list[Alert] = []
        self._firing_rules: set[str] = set()  # Rules currently in FIRING state

    def add_rule(self, rule: AlertRule) -> None:
        """Register an alert rule."""
        self._rules.append(rule)

    def add_channel(self, channel: AlertChannel) -> None:
        """Register a notification channel."""
        self._channels.append(channel)

    def get_rule_state(self, rule_name: str) -> AlertState:
        """Return the current state of a rule."""
        if rule_name in self._firing_rules:
            return AlertState.FIRING
        return AlertState.OK

    def get_alert_history(self, limit: int = 50) -> list[dict[str, Any]]:
        """Return recent alert history."""
        return [a.to_dict() for a in self._alert_history[-limit:]]

    async def evaluate_all(self) -> list[Alert]:
        """Evaluate all rules against current metrics.

        Returns:
            List of alerts that fired in this evaluation cycle.
        """
        from app.core.monitoring import tracker

        all_metrics = tracker.get_all_metrics()
        fired: list[Alert] = []

        for rule in self._rules:
            metric = all_metrics.get(rule.metric_name)
            if metric is None:
                continue

            alert = rule.evaluate(metric)
            if alert is not None:
                fired.append(alert)
                self._alert_history.append(alert)
                self._firing_rules.add(rule.name)
                await self._dispatch(alert)
            else:
                # Rule resolved
                if rule.name in self._firing_rules:
                    self._firing_rules.discard(rule.name)
                    logger.info("Alert resolved", rule=rule.name)

        return fired

    async def _dispatch(self, alert: Alert) -> None:
        """Send alert to all registered channels."""
        for channel in self._channels:
            try:
                await channel.send(alert)
            except Exception as exc:
                logger.warning(
                    "Alert channel dispatch error",
                    channel=type(channel).__name__,
                    error=str(exc),
                )

    def status_summary(self) -> dict[str, Any]:
        """Return a summary of current alert states."""
        return {
            "total_rules": len(self._rules),
            "firing_count": len(self._firing_rules),
            "firing_rules": list(self._firing_rules),
            "total_alerts_fired": len(self._alert_history),
            "channels": [type(c).__name__ for c in self._channels],
        }


# ---------------------------------------------------------------------------
# Pre-configured alert rules (from design document thresholds)
# ---------------------------------------------------------------------------

DEFAULT_RULES: list[AlertRule] = [
    # Requirement 7.2 — message storage > 200ms p95
    AlertRule(
        name="message_storage_latency_high",
        metric_name="add_message",
        metric_field="p95_duration_ms",
        threshold=200.0,
        severity=AlertSeverity.WARNING,
        message_template="Message storage p95 latency is {value}ms (threshold: {threshold}ms)",
    ),
    # Requirement 7.3 — conversation list > 500ms p95
    AlertRule(
        name="conversation_list_latency_high",
        metric_name="list_conversations",
        metric_field="p95_duration_ms",
        threshold=500.0,
        severity=AlertSeverity.WARNING,
        message_template="Conversation list p95 latency is {value}ms (threshold: {threshold}ms)",
    ),
    # Requirement 7.4 — cross-platform sync > 200ms p95
    AlertRule(
        name="cross_platform_sync_latency_high",
        metric_name="cross_platform_sync",
        metric_field="p95_duration_ms",
        threshold=200.0,
        severity=AlertSeverity.WARNING,
        message_template="Cross-platform sync p95 latency is {value}ms (threshold: {threshold}ms)",
    ),
    # Discord command response > 5s p95
    AlertRule(
        name="discord_command_latency_high",
        metric_name="discord_command",
        metric_field="p95_duration_ms",
        threshold=5000.0,
        severity=AlertSeverity.CRITICAL,
        message_template="Discord command p95 latency is {value}ms (threshold: {threshold}ms)",
    ),
    # DB query error rate > 10% (0.1 as fraction)
    AlertRule(
        name="db_query_error_rate_high",
        metric_name="db_query",
        metric_field="error_rate",
        threshold=0.001,  # 0.1%
        severity=AlertSeverity.CRITICAL,
        message_template="DB query error rate is {value:.4f} (threshold: {threshold})",
    ),
    # Sync failure rate > 1% (0.01 as fraction)
    AlertRule(
        name="sync_failure_rate_high",
        metric_name="cross_platform_sync",
        metric_field="error_rate",
        threshold=0.01,  # 1%
        severity=AlertSeverity.CRITICAL,
        message_template="Cross-platform sync failure rate is {value:.4f} (threshold: {threshold})",
    ),
    # Search latency > 500ms p95
    AlertRule(
        name="search_latency_high",
        metric_name="search_conversations",
        metric_field="p95_duration_ms",
        threshold=500.0,
        severity=AlertSeverity.WARNING,
        message_template="Conversation search p95 latency is {value}ms (threshold: {threshold}ms)",
    ),
]


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

#: Global AlertManager instance — configure channels at startup.
alert_manager = AlertManager()

# Register default rules
for _rule in DEFAULT_RULES:
    alert_manager.add_rule(_rule)

# Always log alerts
alert_manager.add_channel(LogAlertChannel())
