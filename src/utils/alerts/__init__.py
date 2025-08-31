"""Alert system for MLTrading."""

from .models import Alert, AlertSeverity, AlertCategory, AlertStatus
from .email_service import EmailService
from .alert_manager import AlertManager
from .alert_factory import AlertFactory
from .prefect_integration import (
    PrefectAlertManager,
    initialize_alert_manager,
    get_alert_manager,
    alert_on_failure,
    alert_on_long_runtime,
    create_data_pipeline_alerts,
    create_trading_alerts
)

__all__ = [
    'Alert',
    'AlertSeverity', 
    'AlertCategory',
    'AlertStatus',
    'EmailService',
    'AlertManager',
    'AlertFactory',
    'PrefectAlertManager',
    'initialize_alert_manager',
    'get_alert_manager',
    'alert_on_failure',
    'alert_on_long_runtime',
    'create_data_pipeline_alerts',
    'create_trading_alerts'
]