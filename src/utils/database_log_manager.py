"""
Database Log Management Utilities
Provides functions for managing, querying, and cleaning up database logs
"""

import json
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

from ..data.storage.database import DatabaseManager
from .logging_config import get_combined_logger

logger = get_combined_logger("mltrading.database_log_manager", enable_database_logging=False)


class DatabaseLogManager:
    """Manager for database-stored logs"""


    def __init__(self, db_manager: DatabaseManager = None):
        self.db_manager = db_manager or DatabaseManager()


    def get_log_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about database logs

        Returns:
            Dictionary with log statistics
        """
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    stats = {}

                    # System logs statistics
                    cursor.execute("""
                        SELECT
                            COUNT(*) as total_logs,
                            COUNT(DISTINCT correlation_id) as unique_correlations,
                            MIN(timestamp) as oldest_log,
                            MAX(timestamp) as newest_log,
                            COUNT(CASE WHEN level = 'ERROR' THEN 1 END) as error_count,
                            COUNT(CASE WHEN level = 'WARNING' THEN 1 END) as warning_count,
                            COUNT(CASE WHEN level = 'INFO' THEN 1 END) as info_count,
                            COUNT(CASE WHEN level = 'DEBUG' THEN 1 END) as debug_count
                        FROM system_logs
                    """)
                    result = cursor.fetchone()
                    stats['system_logs'] = dict(zip([desc[0] for desc in cursor.description], result))

                    # Trading events statistics
                    cursor.execute("""
                        SELECT
                            COUNT(*) as total_events,
                            COUNT(DISTINCT symbol) as unique_symbols,
                            COUNT(DISTINCT event_type) as unique_event_types,
                            MIN(timestamp) as oldest_event,
                            MAX(timestamp) as newest_event
                        FROM trading_events
                    """)
                    result = cursor.fetchone()
                    stats['trading_events'] = dict(zip([desc[0] for desc in cursor.description], result))

                    # Performance logs statistics
                    cursor.execute("""
                        SELECT
                            COUNT(*) as total_metrics,
                            AVG(duration_ms) as avg_duration_ms,
                            MAX(duration_ms) as max_duration_ms,
                            COUNT(CASE WHEN status = 'error' THEN 1 END) as error_count,
                            COUNT(DISTINCT operation_name) as unique_operations
                        FROM performance_logs
                    """)
                    result = cursor.fetchone()
                    stats['performance_logs'] = dict(zip([desc[0] for desc in cursor.description], result))

                    # Error logs statistics
                    cursor.execute("""
                        SELECT
                            COUNT(*) as total_errors,
                            COUNT(DISTINCT error_type) as unique_error_types,
                            COUNT(DISTINCT component) as affected_components,
                            MIN(timestamp) as oldest_error,
                            MAX(timestamp) as newest_error
                        FROM error_logs
                    """)
                    result = cursor.fetchone()
                    stats['error_logs'] = dict(zip([desc[0] for desc in cursor.description], result))

                    # Calculate total database size
                    cursor.execute("""
                        SELECT
                            pg_total_relation_size('system_logs') +
                            pg_total_relation_size('trading_events') +
                            pg_total_relation_size('performance_logs') +
                            pg_total_relation_size('error_logs') +
                            pg_total_relation_size('user_action_logs') as total_size_bytes
                    """)
                    result = cursor.fetchone()
                    stats['total_size_bytes'] = result[0] if result[0] else 0
                    stats['total_size_mb'] = stats['total_size_bytes'] / 1024 / 1024

                    stats['status'] = 'success'
                    return stats

        except Exception as e:
            logger.error(f"Failed to get database log statistics: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'system_logs': {},
                'trading_events': {},
                'performance_logs': {},
                'error_logs': {},
                'total_size_bytes': 0,
                'total_size_mb': 0
            }


    def query_logs(self,
                   table: str = 'system_logs',
                   start_time: datetime = None,
                   end_time: datetime = None,
                   level: str = None,
                   component: str = None,
                   correlation_id: str = None,
                   limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Query logs from database with filters

        Args:
            table: Table to query ('system_logs', 'trading_events', etc.)
            start_time: Start time filter
            end_time: End time filter
            level: Log level filter
            component: Component filter
            correlation_id: Correlation ID filter
            limit: Maximum number of results

        Returns:
            List of log entries
        """
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Build query dynamically
                    base_query = f"SELECT * FROM {table}"
                    conditions = []
                    params = {}

                    if start_time:
                        conditions.append("timestamp >= %(start_time)s")
                        params['start_time'] = start_time

                    if end_time:
                        conditions.append("timestamp <= %(end_time)s")
                        params['end_time'] = end_time

                    if level and table == 'system_logs':
                        conditions.append("level = %(level)s")
                        params['level'] = level

                    if component:
                        if table == 'system_logs':
                            conditions.append("logger_name LIKE %(component)s")
                            params['component'] = f"%{component}%"
                        elif table in ['performance_logs', 'error_logs']:
                            conditions.append("component = %(component)s")
                            params['component'] = component

                    if correlation_id:
                        conditions.append("correlation_id = %(correlation_id)s")
                        params['correlation_id'] = correlation_id

                    if conditions:
                        base_query += " WHERE " + " AND ".join(conditions)

                    base_query += " ORDER BY timestamp DESC"

                    if limit:
                        base_query += f" LIMIT {limit}"

                    cursor.execute(base_query, params)
                    columns = [desc[0] for desc in cursor.description]
                    results = []

                    for row in cursor.fetchall():
                        entry = dict(zip(columns, row))
                        # Convert datetime objects to ISO strings for JSON serialization
                        for key, value in entry.items():
                            if isinstance(value, datetime):
                                entry[key] = value.isoformat()
                        results.append(entry)

                    return results

        except Exception as e:
            logger.error(f"Failed to query logs from {table}: {e}")
            return []


    def cleanup_old_logs(self,
                        older_than_days: int = 30,
                        table: str = None) -> Dict[str, Any]:
        """
        Clean up old logs from database

        Args:
            older_than_days: Delete logs older than this many days
            table: Specific table to clean (None for all tables)

        Returns:
            Dictionary with cleanup results
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=older_than_days)
        tables_to_clean = [table] if table else [
            'system_logs', 'trading_events', 'performance_logs',
            'error_logs', 'user_action_logs'
        ]

        results = {
            'status': 'success',
            'cutoff_date': cutoff_date.isoformat(),
            'tables_cleaned': {},
            'total_deleted': 0,
            'errors': []
        }

        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    for table_name in tables_to_clean:
                        try:
                            # Check if table exists
                            cursor.execute("""
                                SELECT EXISTS (
                                    SELECT FROM information_schema.tables
                                    WHERE table_name = %s
                                )
                            """, (table_name,))

                            if not cursor.fetchone()[0]:
                                continue

                            # Count records to be deleted
                            cursor.execute("""
                                SELECT COUNT(*) FROM {table_name}
                                WHERE timestamp < %s
                            """, (cutoff_date,))
                            count_to_delete = cursor.fetchone()[0]

                            if count_to_delete > 0:
                                # Delete old records
                                cursor.execute("""
                                    DELETE FROM {table_name}
                                    WHERE timestamp < %s
                                """, (cutoff_date,))

                                results['tables_cleaned'][table_name] = count_to_delete
                                results['total_deleted'] += count_to_delete
                            else:
                                results['tables_cleaned'][table_name] = 0

                        except Exception as e:
                            error_msg = f"Failed to clean table {table_name}: {e}"
                            results['errors'].append(error_msg)
                            logger.error(error_msg)

                    conn.commit()

        except Exception as e:
            results['status'] = 'error'
            results['message'] = str(e)
            logger.error(f"Database log cleanup failed: {e}")

        return results


    def vacuum_analyze(self) -> Dict[str, Any]:
        """
        Vacuum and analyze log tables for better performance

        Returns:
            Dictionary with vacuum results
        """
        tables = ['system_logs', 'trading_events', 'performance_logs',
                 'error_logs', 'user_action_logs']

        results = {
            'status': 'success',
            'tables_processed': [],
            'errors': []
        }

        try:
            with self.db_manager.get_connection() as conn:
                # Set autocommit for VACUUM operations
                conn.autocommit = True

                with conn.cursor() as cursor:
                    for table in tables:
                        try:
                            # Check if table exists
                            cursor.execute("""
                                SELECT EXISTS (
                                    SELECT FROM information_schema.tables
                                    WHERE table_name = %s
                                )
                            """, (table,))

                            if cursor.fetchone()[0]:
                                cursor.execute(f"VACUUM ANALYZE {table}")
                                results['tables_processed'].append(table)

                        except Exception as e:
                            error_msg = f"Failed to vacuum table {table}: {e}"
                            results['errors'].append(error_msg)
                            logger.error(error_msg)

                # Reset autocommit
                conn.autocommit = False

        except Exception as e:
            results['status'] = 'error'
            results['message'] = str(e)
            logger.error(f"Database vacuum failed: {e}")

        return results


    def get_recent_errors(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get recent error logs

        Args:
            hours: Number of hours to look back

        Returns:
            List of recent errors
        """
        # start_time = datetime.now(timezone.utc) - timedelta(hours=hours)  # Currently unused

        return self.query_logs(
            table='system_logs',
            # start_time=start_time,  # Currently unused
            level='ERROR',
            limit=100
        )


    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get performance summary for recent operations

        Args:
            hours: Number of hours to analyze

        Returns:
            Performance summary
        """
        start_time = datetime.now(timezone.utc) - timedelta(hours=hours)

        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT
                            operation_name,
                            COUNT(*) as call_count,
                            AVG(duration_ms) as avg_duration_ms,
                            MIN(duration_ms) as min_duration_ms,
                            MAX(duration_ms) as max_duration_ms,
                            COUNT(CASE WHEN status = 'error' THEN 1 END) as error_count,
                            COUNT(CASE WHEN status = 'success' THEN 1 END) as success_count
                        FROM performance_logs
                        WHERE timestamp >= %s
                        GROUP BY operation_name
                        ORDER BY avg_duration_ms DESC
                    """, (start_time,))

                    columns = [desc[0] for desc in cursor.description]
                    results = []

                    for row in cursor.fetchall():
                        entry = dict(zip(columns, row))
                        # Calculate success rate
                        total_calls = entry['call_count']
                        if total_calls > 0:
                            entry['success_rate'] = entry['success_count'] / total_calls * 100
                        else:
                            entry['success_rate'] = 0
                        results.append(entry)

                    return {
                        'status': 'success',
                        'time_range_hours': hours,
                        'operations': results
                    }

        except Exception as e:
            logger.error(f"Failed to get performance summary: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'operations': []
            }


    def export_logs_to_csv(self,
                          table: str,
                          output_path: Path,
                          start_time: datetime = None,
                          end_time: datetime = None,
                          limit: int = None) -> Dict[str, Any]:
        """
        Export logs to CSV file

        Args:
            table: Table to export
            output_path: Path for CSV file
            start_time: Start time filter
            end_time: End time filter
            limit: Maximum number of records

        Returns:
            Export results
        """
        try:
            import pandas as pd

            logs = self.query_logs(
                table=table,
                # start_time=start_time,  # Currently unused
                end_time=end_time,
                limit=limit
            )

            if not logs:
                return {
                    'status': 'warning',
                    'message': 'No logs found to export',
                    'records_exported': 0
                }

            df = pd.DataFrame(logs)
            df.to_csv(output_path, index=False)

            return {
                'status': 'success',
                'message': f'Exported {len(logs)} records to {output_path}',
                'records_exported': len(logs),
                'output_path': str(output_path)
            }

        except Exception as e:
            logger.error(f"Failed to export logs: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'records_exported': 0
            }

# Global instance
_db_log_manager = None


def get_database_log_manager() -> DatabaseLogManager:
    """Get global database log manager instance"""
    global _db_log_manager
    if _db_log_manager is None:
        _db_log_manager = DatabaseLogManager()
    return _db_log_manager

