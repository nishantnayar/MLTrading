"""Factory for creating common alert types."""

import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from .models import Alert, AlertSeverity, AlertCategory


class AlertFactory:
    """Factory class for creating standardized alerts."""
    
    @staticmethod
    def create_trading_error_alert(
        error_message: str,
        component: str,
        error_type: str = "Trading Error",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Alert:
        """Create a trading error alert."""
        return Alert(
            title=f"{error_type} in {component}",
            message=error_message,
            severity=AlertSeverity.HIGH,
            category=AlertCategory.TRADING_ERRORS,
            timestamp=datetime.now(timezone.utc),
            component=component,
            metadata=metadata or {}
        )
    
    @staticmethod
    def create_order_failure_alert(
        symbol: str,
        order_type: str,
        error_message: str,
        component: str = "TradingSystem",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Alert:
        """Create an order failure alert."""
        metadata = metadata or {}
        metadata.update({
            'symbol': symbol,
            'order_type': order_type
        })
        
        return Alert(
            title=f"Order Failure: {order_type} {symbol}",
            message=f"Failed to execute {order_type} order for {symbol}: {error_message}",
            severity=AlertSeverity.HIGH,
            category=AlertCategory.TRADING_ERRORS,
            timestamp=datetime.now(timezone.utc),
            component=component,
            metadata=metadata
        )
    
    @staticmethod
    def create_data_pipeline_error_alert(
        pipeline_name: str,
        error_message: str,
        component: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Alert:
        """Create a data pipeline error alert."""
        return Alert(
            title=f"Data Pipeline Error: {pipeline_name}",
            message=error_message,
            severity=AlertSeverity.MEDIUM,
            category=AlertCategory.DATA_PIPELINE,
            timestamp=datetime.now(timezone.utc),
            component=component,
            metadata=metadata or {}
        )
    
    @staticmethod
    def create_database_connection_alert(
        error_message: str,
        component: str = "Database",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Alert:
        """Create a database connection error alert."""
        return Alert(
            title="Database Connection Error",
            message=f"Database connection failed: {error_message}",
            severity=AlertSeverity.HIGH,
            category=AlertCategory.SYSTEM_HEALTH,
            timestamp=datetime.now(timezone.utc),
            component=component,
            metadata=metadata or {}
        )
    
    @staticmethod
    def create_api_error_alert(
        api_name: str,
        error_message: str,
        component: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Alert:
        """Create an API error alert."""
        return Alert(
            title=f"API Error: {api_name}",
            message=error_message,
            severity=AlertSeverity.MEDIUM,
            category=AlertCategory.SYSTEM_HEALTH,
            timestamp=datetime.now(timezone.utc),
            component=component,
            metadata=metadata or {}
        )
    
    @staticmethod
    def create_circuit_breaker_alert(
        service_name: str,
        component: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Alert:
        """Create a circuit breaker alert."""
        return Alert(
            title=f"Circuit Breaker Opened: {service_name}",
            message=f"Circuit breaker for {service_name} has been opened due to repeated failures",
            severity=AlertSeverity.HIGH,
            category=AlertCategory.SYSTEM_HEALTH,
            timestamp=datetime.now(timezone.utc),
            component=component,
            metadata=metadata or {}
        )
    
    @staticmethod
    def create_system_startup_alert(
        component: str,
        version: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Alert:
        """Create a system startup alert."""
        version_text = f" (v{version})" if version else ""
        return Alert(
            title=f"System Started: {component}{version_text}",
            message=f"{component} has started successfully and is ready to process requests",
            severity=AlertSeverity.INFO,
            category=AlertCategory.SYSTEM_HEALTH,
            timestamp=datetime.now(timezone.utc),
            component=component,
            metadata=metadata or {}
        )
    
    @staticmethod
    def create_system_shutdown_alert(
        component: str,
        reason: str = "Normal shutdown",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Alert:
        """Create a system shutdown alert."""
        return Alert(
            title=f"System Shutdown: {component}",
            message=f"{component} is shutting down: {reason}",
            severity=AlertSeverity.MEDIUM,
            category=AlertCategory.SYSTEM_HEALTH,
            timestamp=datetime.now(timezone.utc),
            component=component,
            metadata=metadata or {}
        )
    
    @staticmethod
    def create_performance_alert(
        metric_name: str,
        current_value: float,
        threshold: float,
        component: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Alert:
        """Create a performance threshold alert."""
        metadata = metadata or {}
        metadata.update({
            'metric': metric_name,
            'current_value': current_value,
            'threshold': threshold
        })
        
        return Alert(
            title=f"Performance Alert: {metric_name}",
            message=f"{metric_name} has exceeded threshold: {current_value} > {threshold}",
            severity=AlertSeverity.MEDIUM,
            category=AlertCategory.SYSTEM_HEALTH,
            timestamp=datetime.now(timezone.utc),
            component=component,
            metadata=metadata
        )
    
    @staticmethod
    def create_security_alert(
        title: str,
        message: str,
        component: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Alert:
        """Create a security alert."""
        return Alert(
            title=f"Security Alert: {title}",
            message=message,
            severity=AlertSeverity.CRITICAL,
            category=AlertCategory.SECURITY,
            timestamp=datetime.now(timezone.utc),
            component=component,
            metadata=metadata or {}
        )
    
    @staticmethod
    def create_feature_engineering_alert(
        pipeline_name: str,
        message: str,
        severity: AlertSeverity = AlertSeverity.MEDIUM,
        component: str = "FeatureEngineering",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Alert:
        """Create a feature engineering pipeline alert."""
        return Alert(
            title=f"Feature Engineering: {pipeline_name}",
            message=message,
            severity=severity,
            category=AlertCategory.DATA_PIPELINE,
            timestamp=datetime.now(timezone.utc),
            component=component,
            metadata=metadata or {}
        )
    
    @staticmethod
    def create_data_freshness_alert(
        data_source: str,
        last_update: datetime,
        threshold_hours: int,
        component: str = "DataMonitor",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Alert:
        """Create a data freshness alert."""
        hours_old = (datetime.now(timezone.utc) - last_update).total_seconds() / 3600
        
        metadata = metadata or {}
        metadata.update({
            'data_source': data_source,
            'last_update': last_update.isoformat(),
            'hours_old': round(hours_old, 1),
            'threshold_hours': threshold_hours
        })
        
        return Alert(
            title=f"Stale Data Alert: {data_source}",
            message=f"Data from {data_source} is {hours_old:.1f} hours old (threshold: {threshold_hours}h)",
            severity=AlertSeverity.MEDIUM,
            category=AlertCategory.DATA_PIPELINE,
            timestamp=datetime.now(timezone.utc),
            component=component,
            metadata=metadata
        )