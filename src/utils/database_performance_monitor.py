"""
Database Performance Monitor for feature_engineered_data table optimization.
Monitors query performance, index usage, and provides optimization recommendations.
"""

import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from contextlib import contextmanager
from dataclasses import dataclass

try:
    from ..data.storage.database import DatabaseManager
    from .logging_config import get_ui_logger
except ImportError:
    # Handle direct script execution
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from data.storage.database import DatabaseManager
    from utils.logging_config import get_ui_logger


@dataclass
class QueryMetrics:
    """Query performance metrics"""
    query_hash: str
    sql: str
    execution_time: float
    rows_returned: int
    timestamp: datetime
    parameters: Optional[tuple] = None


@dataclass
class IndexUsageStats:
    """Index usage statistics"""
    index_name: str
    table_name: str
    index_scans: int
    tuples_read: int
    tuples_fetched: int
    usage_ratio: float


class DatabasePerformanceMonitor:
    """
    Monitors database performance with focus on feature_engineered_data optimization.

    Features:
    - Query execution timing
    - Index usage analysis
    - Slow query detection
    - Performance recommendations
    - Automated optimization suggestions
    """

    def __init__(self):
        self.logger = get_ui_logger("db_performance_monitor")
        self.db_manager = DatabaseManager()
        self.query_metrics: List[QueryMetrics] = []
        self.slow_query_threshold = 1.0  # seconds

    @contextmanager
    def monitor_query(self, sql: str, parameters: Optional[tuple] = None):
        """
        Context manager to monitor query execution time and performance.

        Usage:
        with monitor.monitor_query("SELECT * FROM feature_engineered_data WHERE symbol = %s", ("AAPL",)):
            result = execute_query(...)
        """
        start_time = time.time()
        query_hash = str(hash(sql.strip()[:100]))

        try:
            yield

        finally:
            execution_time = time.time() - start_time

            # Log slow queries immediately
            if execution_time > self.slow_query_threshold:
                self.logger.warning(f"Slow query detected: {execution_time:.3f}s - {sql[:100]}...")

            # Store metrics for analysis
            metrics = QueryMetrics(
                query_hash=query_hash,
                sql=sql[:500],  # Truncate long queries
                execution_time=execution_time,
                rows_returned=0,  # Would need to be set by caller
                timestamp=datetime.now(),
                parameters=parameters
            )

            self.query_metrics.append(metrics)

            # Keep only recent metrics (last 1000 queries)
            if len(self.query_metrics) > 1000:
                self.query_metrics = self.query_metrics[-1000:]

    def get_slow_queries(self, limit: int = 10) -> List[QueryMetrics]:
        """Get the slowest queries from recent history"""
        sorted_queries = sorted(self.query_metrics, key=lambda x: x.execution_time, reverse=True)
        return sorted_queries[:limit]

    def get_feature_table_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics for feature_engineered_data table.
        """
        try:
            with self.db_manager.get_connection_context() as conn:
                with conn.cursor() as cur:
                    stats = {}

                    # Basic table statistics
                    cur.execute("""
                        SELECT
                            schemaname,
                            tablename,
                            attname,
                            n_distinct,
                            correlation
                        FROM pg_stats
                        WHERE tablename = 'feature_engineered_data'
                        AND attname IN ('symbol', 'timestamp', 'feature_version')
                    """)

                    column_stats = cur.fetchall()
                    stats['column_statistics'] = [
                        {
                            'column': row[2],
                            'distinct_values': row[3],
                            'correlation': row[4]
                        }
                        for row in column_stats
                    ]

                    # Table size information
                    cur.execute("""
                        SELECT
                            pg_size_pretty(pg_total_relation_size('feature_engineered_data')) as total_size,
                            pg_size_pretty(pg_relation_size('feature_engineered_data')) as table_size,
                            pg_size_pretty(pg_total_relation_size('feature_engineered_data') - pg_relation_size('feature_engineered_data')) as index_size
                    """)

                    size_info = cur.fetchone()
                    stats['table_size'] = {
                        'total_size': size_info[0],
                        'table_size': size_info[1],
                        'index_size': size_info[2]
                    }

                    # Row count and data distribution
                    cur.execute("""
                        SELECT
                            COUNT(*) as total_rows,
                            COUNT(DISTINCT symbol) as unique_symbols,
                            MIN(timestamp) as earliest_timestamp,
                            MAX(timestamp) as latest_timestamp,
                            COUNT(CASE WHEN rsi_1d IS NOT NULL THEN 1 END) as rsi_coverage,
                            COUNT(CASE WHEN price_ma_short IS NOT NULL THEN 1 END) as ma_coverage
                        FROM feature_engineered_data
                    """)

                    row_info = cur.fetchone()
                    stats['data_distribution'] = {
                        'total_rows': row_info[0],
                        'unique_symbols': row_info[1],
                        'date_range': f"{row_info[2]} to {row_info[3]}",
                        'rsi_coverage_pct': (row_info[4] / row_info[0] * 100) if row_info[0] > 0 else 0,
                        'ma_coverage_pct': (row_info[5] / row_info[0] * 100) if row_info[0] > 0 else 0
                    }

                    return stats

        except Exception as e:
            self.logger.error(f"Error getting feature table stats: {e}")
            return {}

    def get_index_usage_stats(self) -> List[IndexUsageStats]:
        """
        Get index usage statistics for feature_engineered_data table.
        """
        try:
            with self.db_manager.get_connection_context() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT
                            schemaname,
                            tablename,
                            indexrelname,
                            idx_scan,
                            idx_tup_read,
                            idx_tup_fetch
                        FROM pg_stat_user_indexes
                        WHERE tablename = 'feature_engineered_data'
                        ORDER BY idx_scan DESC
                    """)

                    results = cur.fetchall()

                    index_stats = []
                    for row in results:
                        usage_ratio = (row[5] / max(row[4], 1)) if row[4] > 0 else 0

                        stats = IndexUsageStats(
                            index_name=row[2],
                            table_name=row[1],
                            index_scans=row[3],
                            tuples_read=row[4],
                            tuples_fetched=row[5],
                            usage_ratio=usage_ratio
                        )
                        index_stats.append(stats)

                    return index_stats

        except Exception as e:
            self.logger.error(f"Error getting index usage stats: {e}")
            return []

    def analyze_query_patterns(self) -> Dict[str, Any]:
        """
        Analyze common query patterns and performance.
        """
        if not self.query_metrics:
            return {"message": "No query metrics available"}

        analysis = {
            'total_queries': len(self.query_metrics),
            'average_execution_time': sum(q.execution_time for q in self.query_metrics) / len(self.query_metrics),
            'slow_queries_count': len([q for q in self.query_metrics if q.execution_time > self.slow_query_threshold]),
            'query_patterns': {}
        }

        # Group queries by pattern (first 50 chars)
        pattern_groups = {}
        for query in self.query_metrics:
            pattern = query.sql[:50].strip()
            if pattern not in pattern_groups:
                pattern_groups[pattern] = []
            pattern_groups[pattern].append(query)

        # Analyze each pattern
        for pattern, queries in pattern_groups.items():
            avg_time = sum(q.execution_time for q in queries) / len(queries)
            max_time = max(q.execution_time for q in queries)

            analysis['query_patterns'][pattern] = {
                'count': len(queries),
                'average_time': avg_time,
                'max_time': max_time,
                'slow_queries': len([q for q in queries if q.execution_time > self.slow_query_threshold])
            }

        return analysis

    def get_optimization_recommendations(self) -> List[Dict[str, str]]:
        """
        Generate optimization recommendations based on performance analysis.
        """
        recommendations = []

        try:
            # Get current stats
            table_stats = self.get_feature_table_stats()
            index_stats = self.get_index_usage_stats()
            query_analysis = self.analyze_query_patterns()

            # Check for missing indexes based on query patterns
            common_patterns = query_analysis.get('query_patterns', {})
            for pattern, stats in common_patterns.items():
                if stats['average_time'] > 0.5 and 'WHERE symbol' in pattern:
                    recommendations.append({
                        'type': 'Index Optimization',
                        'priority': 'High',
                        'description': 'Consider composite index on (symbol, feature_version, timestamp)',
                        'sql': 'CREATE INDEX idx_features_symbol_version_time ON feature_engineered_data(symbol, feature_version, timestamp DESC);'
                    })

            # Check for unused indexes
            for idx_stat in index_stats:
                if idx_stat.index_scans < 10:  # Adjust threshold as needed
                    recommendations.append({
                        'type': 'Index Cleanup',
                        'priority': 'Medium',
                        'description': f'Index {idx_stat.index_name} has low usage ({idx_stat.index_scans} scans)',
                        'sql': f'-- Consider dropping: DROP INDEX {idx_stat.index_name};'
                    })

            # Check for SELECT * queries
            select_all_queries = [p for p in common_patterns.keys() if 'SELECT *' in p.upper()]
            if select_all_queries:
                recommendations.append({
                    'type': 'Query Optimization',
                    'priority': 'High',
                    'description': 'Avoid SELECT * queries on feature_engineered_data (100+ columns)',
                    'sql': 'SELECT specific columns instead of SELECT *'
                })

            # Check table size vs performance
            if table_stats.get('data_distribution', {}).get('total_rows', 0) > 1000000:
                recommendations.append({
                    'type': 'Data Management',
                    'priority': 'Medium',
                    'description': 'Large table detected. Consider partitioning by timestamp or symbol',
                    'sql': '-- Consider table partitioning or archiving old data'
                })

            return recommendations

        except Exception as e:
            self.logger.error(f"Error generating recommendations: {e}")
            return []

    def generate_performance_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive performance report.
        """
        return {
            'timestamp': datetime.now().isoformat(),
            'table_statistics': self.get_feature_table_stats(),
            'index_usage': [
                {
                    'name': idx.index_name,
                    'scans': idx.index_scans,
                    'usage_ratio': idx.usage_ratio
                }
                for idx in self.get_index_usage_stats()
            ],
            'query_analysis': self.analyze_query_patterns(),
            'slow_queries': [
                {
                    'sql': q.sql,
                    'execution_time': q.execution_time,
                    'timestamp': q.timestamp.isoformat()
                }
                for q in self.get_slow_queries(5)
            ],
            'recommendations': self.get_optimization_recommendations()
        }

    def benchmark_common_queries(self) -> Dict[str, float]:
        """
        Benchmark common query patterns against feature_engineered_data.
        """
        benchmarks = {}

        try:
            with self.db_manager.get_connection_context() as conn:
                with conn.cursor() as cur:
                    # Test queries representing common access patterns
                    test_queries = {
                        'count_total': "SELECT COUNT(*) FROM feature_engineered_data",
                        'count_by_symbol': "SELECT COUNT(*) FROM feature_engineered_data WHERE symbol = 'AAPL'",
                        'recent_data': """
                            SELECT symbol, timestamp, close, rsi_1d, price_ma_short
                            FROM feature_engineered_data
                            WHERE timestamp >= NOW() - INTERVAL '7 days'
                            LIMIT 100
                        """,
                        'symbol_range': """
                            SELECT timestamp, close, rsi_1d
                            FROM feature_engineered_data
                            WHERE symbol = 'AAPL'
                            AND timestamp >= NOW() - INTERVAL '30 days'
                            ORDER BY timestamp
                        """
                    }

                    for test_name, sql in test_queries.items():
                        start_time = time.time()
                        try:
                            cur.execute(sql)
                            cur.fetchall()  # Ensure all data is fetched
                            execution_time = time.time() - start_time
                            benchmarks[test_name] = execution_time
                        except Exception as e:
                            self.logger.warning(f"Benchmark query '{test_name}' failed: {e}")
                            benchmarks[test_name] = -1  # Indicate failure

            return benchmarks

        except Exception as e:
            self.logger.error(f"Error running benchmarks: {e}")
            return {}


# Global performance monitor instance
performance_monitor = DatabasePerformanceMonitor()


def get_performance_monitor() -> DatabasePerformanceMonitor:
    """Get global performance monitor instance"""
    return performance_monitor


# Decorator for automatic query monitoring
def monitor_db_performance(func):
    """
    Decorator to automatically monitor database query performance.

    Usage:
    @monitor_db_performance
    def some_db_query():
        return execute_query("SELECT ...")
    """
    def wrapper(*args, **kwargs):
        # Extract SQL from function or arguments if available
        sql = kwargs.get('sql', 'Unknown query')

        with performance_monitor.monitor_query(sql):
            return func(*args, **kwargs)

    return wrapper
