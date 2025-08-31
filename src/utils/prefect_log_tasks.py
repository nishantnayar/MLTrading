"""
Prefect Tasks for Log Management
Ready-to-use Prefect tasks for scheduling log cleanup operations
"""

from pathlib import Path
from typing import Dict, Any, Optional

from .log_manager import LogManager
from .logging_config import (
    consolidate_logs,
    cleanup_old_logs,
    get_log_statistics,
    get_combined_logger
)

# Initialize logger
logger = get_combined_logger("mltrading.prefect.log_tasks")


def log_consolidation_task(
    logs_dir: Optional[str] = None,
    max_age_days: int = 7
) -> Dict[str, Any]:
    """
    Prefect task for log consolidation

    Args:
        logs_dir: Directory containing log files
        max_age_days: Maximum age in days before compression

    Returns:
        Dictionary with consolidation results
    """
    logger.info(f"Starting log consolidation task (max_age_days={max_age_days})")

    try:
        logs_path = Path(logs_dir) if logs_dir else None
        results = consolidate_logs(logs_path, max_age_days)

        if results['status'] == 'success':
            logger.info(f"Log consolidation completed: {results['message']}")
        else:
            logger.error(f"Log consolidation failed: {results['message']}")

        return results

    except Exception as e:
        error_msg = f"Log consolidation task failed: {e}"
        logger.error(error_msg)
        return {
            'status': 'error',
            'message': error_msg,
            'compressed_files': [],
            'failed_files': [],
            'total_space_saved': 0,
            'errors': [str(e)]
        }


def log_cleanup_task(
    logs_dir: Optional[str] = None,
    max_age_days: int = 30,
    max_compressed_age_days: int = 90
) -> Dict[str, Any]:
    """
    Prefect task for log cleanup

    Args:
        logs_dir: Directory containing log files
        max_age_days: Maximum age for regular log files before deletion
        max_compressed_age_days: Maximum age for compressed files before deletion

    Returns:
        Dictionary with cleanup results
    """
    logger.info(f"Starting log cleanup task (max_age_days={max_age_days}, max_compressed_age_days={max_compressed_age_days})")

    try:
        logs_path = Path(logs_dir) if logs_dir else None
        results = cleanup_old_logs(logs_path, max_age_days, max_compressed_age_days)

        if results['status'] == 'success':
            logger.info(f"Log cleanup completed: {results['message']}")
        else:
            logger.error(f"Log cleanup failed: {results['message']}")

        return results

    except Exception as e:
        error_msg = f"Log cleanup task failed: {e}"
        logger.error(error_msg)
        return {
            'status': 'error',
            'message': error_msg,
            'deleted_files': [],
            'deleted_compressed': [],
            'total_space_freed': 0,
            'errors': [str(e)]
        }


def log_statistics_task(
    logs_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Prefect task for getting log statistics

    Args:
        logs_dir: Directory containing log files

    Returns:
        Dictionary with log statistics
    """
    logger.info("Starting log statistics task")

    try:
        logs_path = Path(logs_dir) if logs_dir else None
        stats = get_log_statistics(logs_path)

        if stats['status'] == 'success':
            logger.info(f"Log statistics gathered successfully: {stats['total_log_files']} log files, {stats['total_compressed_files']} compressed files")
        else:
            logger.error(f"Failed to get log statistics: {stats.get('message', 'Unknown error')}")

        return stats

    except Exception as e:
        error_msg = f"Log statistics task failed: {e}"
        logger.error(error_msg)
        return {
            'status': 'error',
            'message': error_msg,
            'total_log_files': 0,
            'total_compressed_files': 0,
            'total_size': 0,
            'oldest_file': None,
            'newest_file': None,
            'files_by_age': {'1d': 0, '7d': 0, '30d': 0, 'older': 0}
        }


def log_health_check_task(
    logs_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Prefect task for log health check

    Args:
        logs_dir: Directory containing log files

    Returns:
        Dictionary with health check results
    """
    logger.info("Starting log health check task")

    try:
        log_manager = LogManager(
            logs_dir=Path(logs_dir) if logs_dir else None,
            auto_cleanup=False
        )

        health = log_manager.health_check()

        if health['status'] == 'healthy':
            logger.info("Log health check passed")
        elif health['status'] == 'warning':
            logger.warning(f"Log health check warnings: {health['recommendations']}")
        else:
            logger.error(f"Log health check failed: {health['checks']}")

        return health

    except Exception as e:
        error_msg = f"Log health check task failed: {e}"
        logger.error(error_msg)
        return {
            'status': 'unhealthy',
            'checks': {'health_check_task': f'failed: {e}'},
            'recommendations': ['Fix log health check task errors']
        }


def emergency_log_cleanup_task(
    logs_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Prefect task for emergency log cleanup (when disk space is critical)

    Args:
        logs_dir: Directory containing log files

    Returns:
        Dictionary with emergency cleanup results
    """
    logger.warning("Starting emergency log cleanup task")

    try:
        log_manager = LogManager(
            logs_dir=Path(logs_dir) if logs_dir else None,
            auto_cleanup=False
        )

        results = log_manager.emergency_cleanup()

        logger.warning(f"Emergency cleanup completed, freed {results.get('total_space_freed', 0)} bytes")

        return results

    except Exception as e:
        error_msg = f"Emergency log cleanup task failed: {e}"
        logger.error(error_msg)
        return {
            'error': error_msg,
            'emergency_consolidation': {'status': 'error'},
            'emergency_cleanup': {'status': 'error'},
            'total_space_freed': 0
        }


def full_log_maintenance_task(
    logs_dir: Optional[str] = None,
    consolidate_after_days: int = 7,
    delete_after_days: int = 30,
    delete_compressed_after_days: int = 90
) -> Dict[str, Any]:
    """
    Prefect task that performs complete log maintenance

    Args:
        logs_dir: Directory containing log files
        consolidate_after_days: Days before consolidating logs
        delete_after_days: Days before deleting regular logs
        delete_compressed_after_days: Days before deleting compressed logs

    Returns:
        Dictionary with complete maintenance results
    """
    logger.info("Starting full log maintenance task")

    results = {
        'statistics_before': {},
        'consolidation': {},
        'cleanup': {},
        'statistics_after': {},
        'total_space_freed': 0
    }

    try:
        # Get initial statistics
        results['statistics_before'] = log_statistics_task(logs_dir)

        # Perform consolidation
        results['consolidation'] = log_consolidation_task(logs_dir, consolidate_after_days)

        # Perform cleanup
        results['cleanup'] = log_cleanup_task(logs_dir, delete_after_days, delete_compressed_after_days)

        # Get final statistics
        results['statistics_after'] = log_statistics_task(logs_dir)

        # Calculate total space freed
        consolidation_saved = results['consolidation'].get('total_space_saved', 0)
        cleanup_freed = results['cleanup'].get('total_space_freed', 0)
        results['total_space_freed'] = consolidation_saved + cleanup_freed

        logger.info(f"Full log maintenance completed, total space freed: {results['total_space_freed']} bytes")

        return results

    except Exception as e:
        error_msg = f"Full log maintenance task failed: {e}"
        logger.error(error_msg)
        results['error'] = error_msg
        return results

# Example Prefect flow configuration (commented out since Prefect may not be installed)
"""
# Example usage with Prefect 2.x:

from prefect import flow, task
from prefect.schedules import IntervalSchedule
from datetime import timedelta

@task


def consolidate_logs_prefect_task():
    return log_consolidation_task()

@task


def cleanup_logs_prefect_task():
    return log_cleanup_task()

@task


def health_check_prefect_task():
    return log_health_check_task()

@flow(name="daily-log-maintenance")


def daily_log_maintenance_flow():
    # Run health check first
    health_results = health_check_prefect_task()

    # Run consolidation
    consolidation_results = consolidate_logs_prefect_task()

    # Run cleanup
    cleanup_results = cleanup_logs_prefect_task()

    return {
        'health': health_results,
        'consolidation': consolidation_results,
        'cleanup': cleanup_results
    }

# Schedule the flow to run daily at 2 AM
if __name__ == "__main__":
    # Create deployment
    from prefect.deployments import Deployment
    from prefect.schedules import CronSchedule

    deployment = Deployment.build_from_flow(
        flow=daily_log_maintenance_flow,
        name="daily-log-maintenance",
        schedule=CronSchedule(cron="0 2 * * *"),  # Daily at 2 AM
        work_queue_name="default"
    )

    deployment.apply()
"""

