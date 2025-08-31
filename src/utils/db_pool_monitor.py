"""
Database Connection Pool Monitor
Provides utilities to monitor and manage database connection pool health
"""

import time
import threading
from typing import Dict, Any
from ..data.storage.database import DatabaseManager


class ConnectionPoolMonitor:
    """Monitor database connection pool usage and health"""


    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.stats = {
            'active_connections': 0,
            'pool_size': 0,
            'connection_errors': 0,
            'last_check': None
        }


    def get_pool_status(self) -> Dict[str, Any]:
        """Get current connection pool status"""
        try:
            if self.db_manager.pool:
                # Get basic pool information
                pool = self.db_manager.pool
                self.stats.update({
                    'min_connections': pool.minconn,
                    'max_connections': pool.maxconn,
                    'pool_size': len(pool._pool) + len(pool._used),
                    'available_connections': len(pool._pool),
                    'used_connections': len(pool._used),
                    'last_check': time.time()
                })
            else:
                self.stats.update({
                    'pool_status': 'fallback_mode',
                    'last_check': time.time()
                })
        except Exception as e:
            self.stats['connection_errors'] += 1
            self.stats['last_error'] = str(e)

        return self.stats.copy()


    def test_connection(self) -> bool:
        """Test if we can get a connection from the pool"""
        try:
            conn = self.db_manager.get_connection()
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            self.db_manager.return_connection(conn)
            return True
        except Exception as e:
            self.stats['connection_errors'] += 1
            self.stats['last_error'] = str(e)
            return False


    def close_idle_connections(self):
        """Close idle connections if possible"""
        try:
            if self.db_manager.pool:
                pool = self.db_manager.pool
                # Close connections that exceed minimum
                while len(pool._pool) > pool.minconn:
                    try:
                        conn = pool._pool.pop()
                        conn.close()
                    except Exception:
                        break
        except Exception as e:
            self.stats['last_error'] = str(e)


def create_optimized_db_manager() -> DatabaseManager:
    """Create a database manager optimized for high-throughput logging"""
    return DatabaseManager(
        min_conn=3,
        max_conn=30  # Increased pool size for logging workload
    )


def monitor_pool_health(db_manager: DatabaseManager, interval: int = 30):
    """Background thread to monitor pool health"""
    monitor = ConnectionPoolMonitor(db_manager)


    def monitor_loop():
        while True:
            try:
                status = monitor.get_pool_status()

                # Log warning if pool is heavily used
                if status.get('used_connections', 0) > status.get('max_connections', 0) * 0.8:
                    print(f"WARNING: Database pool heavily used: {status['used_connections']}/{status['max_connections']}")

                # Test connection health
                if not monitor.test_connection():
                    print("WARNING: Database connection test failed")

            except Exception as e:
                print(f"Error in pool monitor: {e}")

            time.sleep(interval)

    monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
    monitor_thread.start()
    return monitor

