"""Email service for sending alerts."""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from .models import Alert
from ..circuit_breaker import CircuitBreaker, CircuitBreakerConfig, CircuitState


class EmailService:
    """Service for sending email alerts."""


    def __init__(self, config: Dict[str, Any]):
        """Initialize email service with configuration."""
        self.config = config
        self.enabled = config.get('enabled', False)
        self.smtp_server = config.get('smtp_server', 'smtp.mail.yahoo.com')
        self.smtp_port = config.get('smtp_port', 587)
        self.use_tls = config.get('use_tls', True)
        self.timeout = config.get('timeout', 30)

        # Get credentials from environment variables
        self.sender_email = os.getenv('EMAIL_SENDER', config.get('sender_email', ''))
        self.sender_password = os.getenv('EMAIL_PASSWORD', config.get('sender_password', ''))
        self.recipient_email = os.getenv('ALERT_RECIPIENT_EMAIL', config.get('recipient_email', ''))

        self.logger = logging.getLogger(__name__)

        # Circuit breaker for email service reliability
        cb_config = CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=300.0,  # 5 minutes
            timeout=self.timeout
        )
        self.circuit_breaker = CircuitBreaker(name="email_service", config=cb_config)

        self._validate_config()


    def _validate_config(self) -> None:
        """Validate email configuration."""
        if not self.enabled:
            self.logger.info("Email alerts are disabled in configuration")
            return

        missing_configs = []
        if not self.sender_email:
            missing_configs.append("EMAIL_SENDER environment variable")
        if not self.sender_password:
            missing_configs.append("EMAIL_PASSWORD environment variable")
        if not self.recipient_email:
            missing_configs.append("ALERT_RECIPIENT_EMAIL environment variable")

        if missing_configs:
            self.logger.warning(
                f"Email service partially configured. Missing: {', '.join(missing_configs)}. "
                "Email alerts will be disabled until these are set."
            )
            self.enabled = False


    def is_available(self) -> bool:
        """Check if email service is available and properly configured."""
        return (
            self.enabled and
            bool(self.sender_email) and
            bool(self.sender_password) and
            bool(self.recipient_email) and
            self.circuit_breaker.state != CircuitState.OPEN
        )


    def send_alert(self, alert: Alert) -> bool:
        """
        Send an alert via email.

        Args:
            alert: Alert object to send

        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        if not self.is_available():
            self.logger.debug(
                f"Email service not available. Enabled: {self.enabled}, "
                f"Circuit breaker state: {self.circuit_breaker.state.value}"
            )
            return False

        try:
            return self.circuit_breaker.call(self._send_email, alert)
        except Exception as e:
            self.logger.error(f"Failed to send email alert: {e}")
            return False


    def _send_email(self, alert: Alert) -> bool:
        """
        Internal method to send email (used by circuit breaker).

        Args:
            alert: Alert object to send

        Returns:
            bool: True if email was sent successfully

        Raises:
            Exception: If email sending fails
        """
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = self.recipient_email
            msg['Subject'] = alert.to_email_subject()

            # Add body
            body = alert.to_email_body()
            msg.attach(MIMEText(body, 'plain'))

            # Connect to server and send
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=self.timeout) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)

            self.logger.info(
                f"Email alert sent successfully: {alert.severity.value} - {alert.title}"
            )
            return True

        except smtplib.SMTPAuthenticationError as e:
            self.logger.error(f"SMTP authentication failed: {e}")
            raise
        except smtplib.SMTPConnectError as e:
            self.logger.error(f"SMTP connection failed: {e}")
            raise
        except smtplib.SMTPException as e:
            self.logger.error(f"SMTP error occurred: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error sending email: {e}")
            raise


    def test_connection(self) -> bool:
        """
        Test email service connection and authentication.

        Returns:
            bool: True if connection test successful, False otherwise
        """
        if not self.is_available():
            self.logger.info("Email service not configured for testing")
            return False

        try:
            # Import here to avoid circular imports
            from .models import AlertSeverity, AlertCategory

            # Create test alert
            test_alert = Alert(
                title="Email Service Test",
                message="This is a test email from the MLTrading alert system.",
                severity=AlertSeverity.INFO,
                category=AlertCategory.SYSTEM_HEALTH,
                timestamp=datetime.now(timezone.utc),
                component="EmailService",
                metadata={"test": True}
            )

            return self.send_alert(test_alert)

        except Exception as e:
            self.logger.error(f"Email service test failed: {e}")
            return False


    def get_status(self) -> Dict[str, Any]:
        """
        Get current status of email service.

        Returns:
            Dict containing service status information
        """
        return {
            'enabled': self.enabled,
            'available': self.is_available(),
            'circuit_breaker_state': self.circuit_breaker.state.value,
            'circuit_breaker_failures': self.circuit_breaker.stats.failure_count,
            'sender_configured': bool(self.sender_email),
            'recipient_configured': bool(self.recipient_email),
            'smtp_server': self.smtp_server,
            'smtp_port': self.smtp_port
        }

