"""Alert manager for the MLTrading system."""

import logging
import threading
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List
from collections import defaultdict, deque

from .models import Alert, AlertSeverity, AlertCategory, AlertStatus
from .email_service import EmailService


class RateLimiter:
    """Rate limiter for alerts to prevent spam."""

    def __init__(self, max_per_hour: int = 10, max_per_day: int = 50):
        """Initialize rate limiter."""
        self.max_per_hour = max_per_hour
        self.max_per_day = max_per_day
        self.hourly_counts = defaultdict(lambda: deque())
        self.daily_counts = defaultdict(lambda: deque())
        self.lock = threading.Lock()

    def can_send_alert(self, category: AlertCategory) -> bool:
        """
        Check if an alert can be sent based on rate limits.

        Args:
            category: Alert category to check

        Returns:
            bool: True if alert can be sent, False if rate limited
        """
        with self.lock:
            now = datetime.now(timezone.utc)
            hour_ago = now - timedelta(hours=1)
            day_ago = now - timedelta(days=1)

            # Clean old entries
            hourly_queue = self.hourly_counts[category]
            while hourly_queue and hourly_queue[0] < hour_ago:
                hourly_queue.popleft()

            daily_queue = self.daily_counts[category]
            while daily_queue and daily_queue[0] < day_ago:
                daily_queue.popleft()

            # Check limits
            if len(hourly_queue) >= self.max_per_hour:
                return False
            if len(daily_queue) >= self.max_per_day:
                return False

            return True

    def record_alert_sent(self, category: AlertCategory) -> None:
        """Record that an alert was sent."""
        with self.lock:
            now = datetime.now(timezone.utc)
            self.hourly_counts[category].append(now)
            self.daily_counts[category].append(now)

    def get_stats(self) -> Dict[str, Dict[str, int]]:
        """Get current rate limiting statistics."""
        with self.lock:
            stats = {}
            for category in AlertCategory:
                stats[category.value] = {
                    'sent_last_hour': len(self.hourly_counts[category]),
                    'sent_last_day': len(self.daily_counts[category]),
                    'hourly_limit': self.max_per_hour,
                    'daily_limit': self.max_per_day
                }
            return stats


class AlertManager:
    """Central alert management system."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize alert manager with configuration."""
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Parse configuration
        alert_config = config.get('alerts', {})
        email_config = config.get('email_alerts', {})

        self.enabled = alert_config.get('enabled', True)
        self.min_severity = AlertSeverity(alert_config.get('min_severity', 'MEDIUM'))

        # Initialize rate limiter
        rate_config = alert_config.get('rate_limiting', {})
        if rate_config.get('enabled', True):
            self.rate_limiter = RateLimiter(
                max_per_hour=rate_config.get('max_alerts_per_hour', 10),
                max_per_day=rate_config.get('max_alerts_per_day', 50)
            )
        else:
            self.rate_limiter = None

        # Category configurations
        self.category_configs = alert_config.get('alert_categories', {})

        # Initialize email service
        self.email_service = EmailService(email_config)

        # Alert statistics
        self.stats = {
            'total_alerts': 0,
            'sent_alerts': 0,
            'failed_alerts': 0,
            'rate_limited_alerts': 0,
            'filtered_alerts': 0,
            'alerts_by_severity': defaultdict(int),
            'alerts_by_category': defaultdict(int)
        }
        self.stats_lock = threading.Lock()

        self.logger.info(f"Alert manager initialized. Enabled: {self.enabled}")

    def send_alert(
        self,
        title: str,
        message: str,
        severity: AlertSeverity,
        category: AlertCategory = AlertCategory.GENERAL,
        component: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AlertStatus:
        """
        Send an alert through the system.

        Args:
            title: Alert title
            message: Alert message
            severity: Alert severity level
            category: Alert category
            component: Component that generated the alert
            metadata: Additional metadata

        Returns:
            AlertStatus: Status of the alert processing
        """
        # Create alert object
        alert = Alert(
            title=title,
            message=message,
            severity=severity,
            category=category,
            timestamp=datetime.now(timezone.utc),
            component=component,
            metadata=metadata or {}
        )

        return self.process_alert(alert)

    def process_alert(self, alert: Alert) -> AlertStatus:
        """
        Process an alert through all filters and send if appropriate.

        Args:
            alert: Alert to process

        Returns:
            AlertStatus: Processing result
        """
        with self.stats_lock:
            self.stats['total_alerts'] += 1
            self.stats['alerts_by_severity'][alert.severity.value] += 1
            self.stats['alerts_by_category'][alert.category.value] += 1

        self.logger.debug(
            f"Processing alert: {alert.severity.value} - {alert.title}"
        )

        if not self.enabled:
            self.logger.debug("Alert system disabled, skipping alert")
            return AlertStatus.FILTERED

        # Check severity filter
        if not self._should_send_by_severity(alert):
            self.logger.debug(f"Alert filtered by severity: {alert.severity.value}")
            with self.stats_lock:
                self.stats['filtered_alerts'] += 1
            return AlertStatus.FILTERED

        # Check category configuration
        if not self._should_send_by_category(alert):
            self.logger.debug(f"Alert filtered by category: {alert.category.value}")
            with self.stats_lock:
                self.stats['filtered_alerts'] += 1
            return AlertStatus.FILTERED

        # Check rate limits
        if not self._should_send_by_rate_limit(alert):
            self.logger.info(
                f"Alert rate limited: {alert.category.value} - {alert.title}"
            )
            with self.stats_lock:
                self.stats['rate_limited_alerts'] += 1
            return AlertStatus.RATE_LIMITED

        # Send the alert
        success = self.email_service.send_alert(alert)

        if success:
            self.logger.info(f"Alert sent successfully: {alert.severity.value} - {alert.title}")
            if self.rate_limiter:
                self.rate_limiter.record_alert_sent(alert.category)
            with self.stats_lock:
                self.stats['sent_alerts'] += 1
            return AlertStatus.SENT
        else:
            self.logger.error(f"Failed to send alert: {alert.severity.value} - {alert.title}")
            with self.stats_lock:
                self.stats['failed_alerts'] += 1
            return AlertStatus.FAILED

    def _should_send_by_severity(self, alert: Alert) -> bool:
        """Check if alert meets minimum severity threshold."""
        return alert.severity >= self.min_severity

    def _should_send_by_category(self, alert: Alert) -> bool:
        """Check if alert category is enabled."""
        category_config = self.category_configs.get(alert.category.value, {})
        return category_config.get('enabled', True)

    def _should_send_by_rate_limit(self, alert: Alert) -> bool:
        """Check if alert passes rate limiting."""
        if not self.rate_limiter:
            return True
        return self.rate_limiter.can_send_alert(alert.category)

    def send_critical_alert(
        self,
        title: str,
        message: str,
        category: AlertCategory = AlertCategory.GENERAL,
        component: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AlertStatus:
        """Send a critical alert (bypasses some filters)."""
        return self.send_alert(
            title=title,
            message=message,
            severity=AlertSeverity.CRITICAL,
            category=category,
            component=component,
            metadata=metadata
        )

    def send_trading_error_alert(
        self,
        error_message: str,
        component: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AlertStatus:
        """Send a trading error alert."""
        return self.send_alert(
            title="Trading System Error",
            message=error_message,
            severity=AlertSeverity.HIGH,
            category=AlertCategory.TRADING_ERRORS,
            component=component,
            metadata=metadata
        )

    def send_system_health_alert(
        self,
        title: str,
        message: str,
        severity: AlertSeverity = AlertSeverity.MEDIUM,
        component: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AlertStatus:
        """Send a system health alert."""
        return self.send_alert(
            title=title,
            message=message,
            severity=severity,
            category=AlertCategory.SYSTEM_HEALTH,
            component=component,
            metadata=metadata
        )

    def send_data_pipeline_alert(
        self,
        title: str,
        message: str,
        severity: AlertSeverity = AlertSeverity.MEDIUM,
        component: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AlertStatus:
        """Send a data pipeline alert."""
        return self.send_alert(
            title=title,
            message=message,
            severity=severity,
            category=AlertCategory.DATA_PIPELINE,
            component=component,
            metadata=metadata
        )

    def send_security_alert(
        self,
        title: str,
        message: str,
        component: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AlertStatus:
        """Send a security alert (always critical)."""
        return self.send_alert(
            title=title,
            message=message,
            severity=AlertSeverity.CRITICAL,
            category=AlertCategory.SECURITY,
            component=component,
            metadata=metadata
        )

    def test_alert_system(self) -> bool:
        """Test the alert system by sending a test alert."""
        self.logger.info("Testing alert system...")

        status = self.send_alert(
            title="Alert System Test",
            message="This is a test alert to verify the alert system is working correctly.",
            severity=AlertSeverity.INFO,
            category=AlertCategory.SYSTEM_HEALTH,
            component="AlertManager",
            metadata={"test": True, "timestamp": datetime.now(timezone.utc).isoformat()}
        )

        success = status == AlertStatus.SENT
        self.logger.info(f"Alert system test {'passed' if success else 'failed'}: {status.value}")
        return success

    def get_stats(self) -> Dict[str, Any]:
        """Get alert system statistics."""
        with self.stats_lock:
            stats = dict(self.stats)
            stats['alerts_by_severity'] = dict(stats['alerts_by_severity'])
            stats['alerts_by_category'] = dict(stats['alerts_by_category'])

        # Add rate limiter stats if available
        if self.rate_limiter:
            stats['rate_limiter'] = self.rate_limiter.get_stats()

        # Add email service stats
        stats['email_service'] = self.email_service.get_status()

        return stats

    def get_status(self) -> Dict[str, Any]:
        """Get current status of the alert system."""
        return {
            'enabled': self.enabled,
            'min_severity': self.min_severity.value,
            'email_service_available': self.email_service.is_available(),
            'rate_limiting_enabled': self.rate_limiter is not None,
            'categories_enabled': {
                cat: self.category_configs.get(cat, {}).get('enabled', True)
                for cat in [c.value for c in AlertCategory]
            }
        }
