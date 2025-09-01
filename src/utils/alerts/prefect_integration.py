"""
Prefect integration utilities for the MLTrading Alert System.

This module provides seamless integration between the alert system and Prefect workflows,
including context-aware alert managers, flow/task decorators, and error handling.
"""

import functools
import logging
from typing import Optional, Callable, Any, Dict
from datetime import datetime, timezone

try:
    from prefect import get_run_context, get_run_logger
    from prefect.context import FlowRunContext, TaskRunContext

    PREFECT_AVAILABLE = True
except ImportError:
    PREFECT_AVAILABLE = False

from .alert_manager import AlertManager
from .models import AlertSeverity, AlertCategory
from .alert_factory import AlertFactory


class PrefectAlertManager:
    """Alert manager with Prefect context awareness."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize Prefect-aware alert manager."""
        self.alert_manager = AlertManager(config)
        self.logger = logging.getLogger(__name__)
        self._prefect_available = PREFECT_AVAILABLE

    def _get_prefect_context(self) -> Dict[str, Any]:
        """Get current Prefect context information."""
        if not self._prefect_available:
            return {}

        try:
            context = get_run_context()
            metadata = {}

            if isinstance(context, FlowRunContext):
                metadata.update({
                    'prefect_type': 'flow',
                    'flow_name': context.flow.name,
                    'flow_run_id': str(context.flow_run.id),
                    'flow_run_name': context.flow_run.name,
                })
            elif isinstance(context, TaskRunContext):
                metadata.update({
                    'prefect_type': 'task',
                    'task_name': context.task.name,
                    'task_run_id': str(context.task_run.id),
                    'task_run_name': context.task_run.name,
                    'flow_run_id': str(context.task_run.flow_run_id),
                })

            return metadata

        except Exception as e:
            self.logger.debug(f"Could not get Prefect context: {e}")
            return {}

    def send_alert(
            self,
            title: str,
            message: str,
            severity: AlertSeverity,
            category: AlertCategory = AlertCategory.GENERAL,
            component: Optional[str] = None,
            metadata: Optional[Dict[str, Any]] = None
    ):
        """Send alert with Prefect context information."""
        # Merge Prefect context with provided metadata
        prefect_context = self._get_prefect_context()
        combined_metadata = {**(metadata or {}), **prefect_context}

        # Use Prefect component name if not specified
        if not component and prefect_context:
            if prefect_context.get('prefect_type') == 'flow':
                component = f"Flow: {prefect_context.get('flow_name')}"
            elif prefect_context.get('prefect_type') == 'task':
                component = f"Task: {prefect_context.get('task_name')}"

        return self.alert_manager.send_alert(
            title=title,
            message=message,
            severity=severity,
            category=category,
            component=component,
            metadata=combined_metadata
        )

    def send_flow_start_alert(self, flow_name: str, metadata: Optional[Dict[str, Any]] = None):
        """Send flow start notification."""
        return self.send_alert(
            title=f"Flow Started: {flow_name}",
            message=f"Prefect flow '{flow_name}' has started execution",
            severity=AlertSeverity.INFO,
            category=AlertCategory.DATA_PIPELINE,
            metadata=metadata
        )

    def send_flow_success_alert(self, flow_name: str, duration: Optional[float] = None,
                                metadata: Optional[Dict[str, Any]] = None):
        """Send flow success notification."""
        duration_text = f" in {duration:.1f}s" if duration else ""
        return self.send_alert(
            title=f"Flow Completed: {flow_name}",
            message=f"Prefect flow '{flow_name}' completed successfully{duration_text}",
            severity=AlertSeverity.INFO,
            category=AlertCategory.DATA_PIPELINE,
            metadata=metadata
        )

    def send_flow_failure_alert(self, flow_name: str, error: Exception, metadata: Optional[Dict[str, Any]] = None):
        """Send flow failure notification."""
        error_metadata = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            **(metadata or {})
        }

        return self.send_alert(
            title=f"Flow Failed: {flow_name}",
            message=f"Prefect flow '{flow_name}' failed with error: {str(error)}",
            severity=AlertSeverity.HIGH,
            category=AlertCategory.DATA_PIPELINE,
            metadata=error_metadata
        )

    def send_task_failure_alert(self, task_name: str, error: Exception, metadata: Optional[Dict[str, Any]] = None):
        """Send task failure notification."""
        error_metadata = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            **(metadata or {})
        }

        return self.send_alert(
            title=f"Task Failed: {task_name}",
            message=f"Prefect task '{task_name}' failed with error: {str(error)}",
            severity=AlertSeverity.MEDIUM,
            category=AlertCategory.DATA_PIPELINE,
            metadata=error_metadata
        )

    # Delegate other methods to the underlying alert manager

    def __getattr__(self, name):
        """Delegate unknown methods to the underlying AlertManager."""
        return getattr(self.alert_manager, name)


# Global alert manager instance
_alert_manager: Optional[PrefectAlertManager] = None


def initialize_alert_manager(config: Dict[str, Any]) -> PrefectAlertManager:
    """Initialize the global alert manager instance."""
    global _alert_manager
    _alert_manager = PrefectAlertManager(config)
    return _alert_manager


def get_alert_manager() -> Optional[PrefectAlertManager]:
    """Get the global alert manager instance."""
    return _alert_manager


def alert_on_failure(
        severity: AlertSeverity = AlertSeverity.MEDIUM,
        category: AlertCategory = AlertCategory.DATA_PIPELINE,
        send_success_alert: bool = False
):
    """
    Decorator to automatically send alerts on function failure.

    Args:
        severity: Alert severity for failures
        category: Alert category
        send_success_alert: Whether to send success notifications
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            alert_manager = get_alert_manager()
            if not alert_manager:
                # No alert manager available, just run the function
                return func(*args, **kwargs)

            func_name = func.__name__
            start_time = datetime.now(timezone.utc)

            try:
                result = func(*args, **kwargs)

                if send_success_alert:
                    duration = (datetime.now(timezone.utc) - start_time).total_seconds()

                    if PREFECT_AVAILABLE:
                        try:
                            context = get_run_context()
                            if isinstance(context, FlowRunContext):
                                alert_manager.send_flow_success_alert(
                                    flow_name=func_name,
                                    duration=duration
                                )
                            elif isinstance(context, TaskRunContext):
                                alert_manager.send_alert(
                                    title=f"Task Completed: {func_name}",
                                    message=f"Task '{func_name}' completed successfully in {duration:.1f}s",
                                    severity=AlertSeverity.INFO,
                                    category=category
                                )
                        except Exception:
                            # Fallback to basic alert
                            alert_manager.send_alert(
                                title=f"Function Completed: {func_name}",
                                message=f"Function '{func_name}' completed successfully",
                                severity=AlertSeverity.INFO,
                                category=category
                            )

                return result

            except Exception as e:
                if PREFECT_AVAILABLE:
                    try:
                        context = get_run_context()
                        if isinstance(context, FlowRunContext):
                            alert_manager.send_flow_failure_alert(
                                flow_name=func_name,
                                error=e
                            )
                        elif isinstance(context, TaskRunContext):
                            alert_manager.send_task_failure_alert(
                                task_name=func_name,
                                error=e
                            )
                    except Exception:
                        # Fallback to basic alert
                        alert_manager.send_alert(
                            title=f"Function Failed: {func_name}",
                            message=f"Function '{func_name}' failed: {str(e)}",
                            severity=severity,
                            category=category,
                            metadata={'error_type': type(e).__name__}
                        )
                else:
                    # No Prefect context, send basic alert
                    alert_manager.send_alert(
                        title=f"Function Failed: {func_name}",
                        message=f"Function '{func_name}' failed: {str(e)}",
                        severity=severity,
                        category=category,
                        metadata={'error_type': type(e).__name__}
                    )

                # Re-raise the exception
                raise

        return wrapper

    return decorator


def alert_on_long_runtime(
        threshold_seconds: float = 300,  # 5 minutes
        severity: AlertSeverity = AlertSeverity.MEDIUM,
        category: AlertCategory = AlertCategory.SYSTEM_HEALTH
):
    """
    Decorator to send alerts when functions take longer than expected.

    Args:
        threshold_seconds: Runtime threshold in seconds
        severity: Alert severity
        category: Alert category
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            alert_manager = get_alert_manager()
            func_name = func.__name__
            start_time = datetime.now(timezone.utc)

            try:
                result = func(*args, **kwargs)

                # Check runtime
                duration = (datetime.now(timezone.utc) - start_time).total_seconds()
                if alert_manager and duration > threshold_seconds:
                    alert_manager.send_alert(
                        title=f"Long Runtime: {func_name}",
                        message=f"Function '{func_name}' took {duration:.1f}s (threshold: {threshold_seconds}s)",
                        severity=severity,
                        category=category,
                        metadata={
                            'duration': duration,
                            'threshold': threshold_seconds,
                            'function_name': func_name
                        }
                    )

                return result

            except Exception as e:
                # Still check runtime even on failure
                duration = (datetime.now(timezone.utc) - start_time).total_seconds()
                if alert_manager and duration > threshold_seconds:
                    alert_manager.send_alert(
                        title=f"Long Runtime (Failed): {func_name}",
                        message=f"Function '{func_name}' failed after {duration:.1f}s (threshold: {threshold_seconds}s)",
                        severity=severity,
                        category=category,
                        metadata={
                            'duration': duration,
                            'threshold': threshold_seconds,
                            'function_name': func_name,
                            'error_type': type(e).__name__,
                            'error_message': str(e)
                        }
                    )
                raise

        return wrapper

    return decorator


# Convenience functions for common Prefect scenarios


def create_data_pipeline_alerts(config: Dict[str, Any]) -> PrefectAlertManager:
    """Create alert manager optimized for data pipeline workflows."""
    alert_manager = PrefectAlertManager(config)

    # You could customize settings here for data pipelines
    # For example, adjust rate limits, severity thresholds, etc.

    return alert_manager


def create_trading_alerts(config: Dict[str, Any]) -> PrefectAlertManager:
    """Create alert manager optimized for trading workflows."""
    alert_manager = PrefectAlertManager(config)

    # You could customize settings here for trading workflows
    # For example, higher sensitivity for trading errors

    return alert_manager
