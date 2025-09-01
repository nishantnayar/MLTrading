"""Alert models and enums for the MLTrading system."""

from enum import Enum
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from dataclasses import dataclass


class AlertSeverity(Enum):
    """Alert severity levels."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"

    @property
    def priority(self) -> int:
        """Return numeric priority for comparison."""
        return {
            AlertSeverity.CRITICAL: 5,
            AlertSeverity.HIGH: 4,
            AlertSeverity.MEDIUM: 3,
            AlertSeverity.LOW: 2,
            AlertSeverity.INFO: 1
        }[self]

    def __ge__(self, other) -> bool:
        if not isinstance(other, AlertSeverity):
            return NotImplemented
        return self.priority >= other.priority

    def __gt__(self, other) -> bool:
        if not isinstance(other, AlertSeverity):
            return NotImplemented
        return self.priority > other.priority


class AlertCategory(Enum):
    """Alert categories for different system components."""
    TRADING_ERRORS = "trading_errors"
    SYSTEM_HEALTH = "system_health"
    DATA_PIPELINE = "data_pipeline"
    SECURITY = "security"
    GENERAL = "general"


@dataclass
class Alert:
    """Alert data structure."""
    title: str
    message: str
    severity: AlertSeverity
    category: AlertCategory
    timestamp: datetime
    component: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Validate alert data after initialization."""
        if not self.title or not self.title.strip():
            raise ValueError("Alert title cannot be empty")
        if not self.message or not self.message.strip():
            raise ValueError("Alert message cannot be empty")
        if self.metadata is None:
            self.metadata = {}

    def to_email_subject(self) -> str:
        """Generate email subject line for this alert."""
        return f"[{self.severity.value}] MLTrading Alert: {self.title}"

    def to_email_body(self) -> str:
        """Generate email body for this alert."""
        body_lines = [
            "Alert Details:",
            "================",
            f"Title: {self.title}",
            f"Severity: {self.severity.value}",
            f"Category: {self.category.value}",
            f"Timestamp: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}",
        ]

        if self.component:
            body_lines.append(f"Component: {self.component}")

        body_lines.extend([
            "",
            "Message:",
            "--------",
            f"{self.message}",
        ])

        if self.metadata:
            body_lines.extend([
                "",
                "Additional Information:",
                "----------------------"
            ])
            for key, value in self.metadata.items():
                body_lines.append(f"{key}: {value}")

        body_lines.extend([
            "",
            "--",
            "MLTrading Alert System",
            f"Generated at {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"
        ])

        return "\n".join(body_lines)


class AlertStatus(Enum):
    """Alert processing status."""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    RATE_LIMITED = "rate_limited"
    FILTERED = "filtered"
