"""
Log Management Utilities
Provides convenient functions for managing logs across the application
"""

import os
import atexit
from pathlib import Path
from typing import Dict, Any, Optional

from .logging_config import (
    start_log_cleanup_scheduler,
    stop_log_cleanup_scheduler,
    consolidate_logs,
    cleanup_old_logs,
    get_log_statistics,
    get_combined_logger
)

class LogManager:
    """Centralized log management for the ML Trading application"""

    def __init__(self,
                 logs_dir: Optional[Path] = None,
                 auto_cleanup: bool = False,  # Disabled by default for Prefect scheduling
                 cleanup_interval_hours: int = 24,
                 consolidate_after_days: int = 7,
                 delete_after_days: int = 30,
                 delete_compressed_after_days: int = 90):
        """
        Initialize the log manager

        Args:
            logs_dir: Directory containing log files
            auto_cleanup: Whether to automatically start cleanup scheduler
            cleanup_interval_hours: Hours between cleanup runs
            consolidate_after_days: Days before consolidating logs
            delete_after_days: Days before deleting regular logs
            delete_compressed_after_days: Days before deleting compressed logs
        """
        self.logs_dir = logs_dir or Path("logs")
        self.logger = get_combined_logger("mltrading.log_manager")

        # Ensure logs directory exists
        self.logs_dir.mkdir(exist_ok=True)

        # Configuration
        self.cleanup_interval_hours = cleanup_interval_hours
        self.consolidate_after_days = consolidate_after_days
        self.delete_after_days = delete_after_days
        self.delete_compressed_after_days = delete_compressed_after_days

        # Start automatic cleanup if enabled
        if auto_cleanup:
            self.start_auto_cleanup()
            # Register cleanup on application exit
            atexit.register(self.stop_auto_cleanup)

    def start_auto_cleanup(self):
        """Start the automatic log cleanup scheduler"""
        try:
            start_log_cleanup_scheduler(
                cleanup_interval_hours=self.cleanup_interval_hours,
                consolidate_after_days=self.consolidate_after_days,
                delete_after_days=self.delete_after_days,
                delete_compressed_after_days=self.delete_compressed_after_days
            )
            self.logger.info("Automatic log cleanup scheduler started")
        except Exception as e:
            self.logger.error(f"Failed to start auto cleanup scheduler: {e}")

    def stop_auto_cleanup(self):
        """Stop the automatic log cleanup scheduler"""
        try:
            stop_log_cleanup_scheduler()
            self.logger.info("Automatic log cleanup scheduler stopped")
        except Exception as e:
            self.logger.error(f"Failed to stop auto cleanup scheduler: {e}")

    def manual_consolidation(self) -> Dict[str, Any]:
        """
        Manually trigger log consolidation

        Returns:
            Dictionary with consolidation results
        """
        self.logger.info("Starting manual log consolidation")
        results = consolidate_logs(self.logs_dir, self.consolidate_after_days)

        if results['status'] == 'success':
            self.logger.info(f"Manual consolidation completed: {results['message']}")
        else:
            self.logger.error(f"Manual consolidation failed: {results['message']}")

        return results

    def manual_cleanup(self) -> Dict[str, Any]:
        """
        Manually trigger log cleanup

        Returns:
            Dictionary with cleanup results
        """
        self.logger.info("Starting manual log cleanup")
        results = cleanup_old_logs(
            self.logs_dir,
            self.delete_after_days,
            self.delete_compressed_after_days
        )

        if results['status'] == 'success':
            self.logger.info(f"Manual cleanup completed: {results['message']}")
        else:
            self.logger.error(f"Manual cleanup failed: {results['message']}")

        return results

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get current log statistics

        Returns:
            Dictionary with log statistics
        """
        return get_log_statistics(self.logs_dir)

    def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the logging system

        Returns:
            Dictionary with health check results
        """
        health = {
            'status': 'healthy',
            'checks': {},
            'recommendations': []
        }

        try:
            # Check if logs directory exists and is writable
            if not self.logs_dir.exists():
                health['checks']['logs_directory'] = 'missing'
                health['status'] = 'unhealthy'
                health['recommendations'].append('Create logs directory')
            elif not os.access(self.logs_dir, os.W_OK):
                health['checks']['logs_directory'] = 'not_writable'
                health['status'] = 'unhealthy'
                health['recommendations'].append('Fix logs directory permissions')
            else:
                health['checks']['logs_directory'] = 'ok'

            # Get statistics
            stats = self.get_statistics()
            if stats['status'] == 'success':
                health['checks']['statistics'] = 'ok'
                health['stats'] = stats

                # Check for excessive log files
                if stats['total_log_files'] > 50:
                    health['recommendations'].append('Consider more frequent log cleanup')

                # Check for large log directory
                if stats['total_size'] > 1024 * 1024 * 1024:  # 1GB
                    health['recommendations'].append('Log directory is large, consider cleanup')
                    health['status'] = 'warning'

                # Check for very old files
                if stats['files_by_age']['older'] > 10:
                    health['recommendations'].append('Many old log files detected, consider cleanup')
            else:
                health['checks']['statistics'] = 'failed'
                health['status'] = 'warning'

        except Exception as e:
            health['status'] = 'unhealthy'
            health['checks']['health_check'] = f'failed: {e}'

        return health

    def emergency_cleanup(self) -> Dict[str, Any]:
        """
        Perform emergency cleanup when disk space is low

        Returns:
            Dictionary with emergency cleanup results
        """
        self.logger.warning("Performing emergency log cleanup")

        results = {
            'emergency_consolidation': {},
            'emergency_cleanup': {},
            'total_space_freed': 0
        }

        try:
            # Aggressive consolidation (consolidate files older than 1 day)
            consolidation_results = consolidate_logs(self.logs_dir, max_age_days=1)
            results['emergency_consolidation'] = consolidation_results

            # Aggressive cleanup (delete files older than 7 days)
            cleanup_results = cleanup_old_logs(
                self.logs_dir,
                max_age_days=7,
                max_compressed_age_days=14
            )
            results['emergency_cleanup'] = cleanup_results

            # Calculate total space freed
            results['total_space_freed'] = (
                consolidation_results.get('total_space_saved', 0) +
                cleanup_results.get('total_space_freed', 0)
            )

            self.logger.warning(f"Emergency cleanup completed, freed {results['total_space_freed']} bytes")

        except Exception as e:
            self.logger.error(f"Emergency cleanup failed: {e}")
            results['error'] = str(e)

        return results

# Global log manager instance
log_manager = None

def get_log_manager() -> LogManager:
    """
    Get the global log manager instance

    Returns:
        LogManager instance
    """
    global log_manager
    if log_manager is None:
        log_manager = LogManager()
    return log_manager

def initialize_log_management(auto_cleanup: bool = False, **kwargs) -> LogManager:
    """
    Initialize the log management system

    Args:
        auto_cleanup: Whether to enable automatic cleanup
        **kwargs: Additional arguments for LogManager

    Returns:
        Initialized LogManager instance
    """
    global log_manager
    log_manager = LogManager(auto_cleanup=auto_cleanup, **kwargs)
    return log_manager
