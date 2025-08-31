"""
Database connection configuration for MLTrading system.
Manages connection limits across concurrent processes.
"""

import os
from typing import Dict, Any


class ConnectionConfig:
    """Configuration class for database connection management"""

    # Global connection limits
    POSTGRES_MAX_CONNECTIONS = 100  # PostgreSQL default
    SYSTEM_RESERVED_CONNECTIONS = 20  # Reserve for other applications

    # MLTrading system limits
    AVAILABLE_CONNECTIONS = POSTGRES_MAX_CONNECTIONS - SYSTEM_RESERVED_CONNECTIONS  # 80

    # Per-process limits (conservative to handle concurrent processes)
    MAX_PROCESSES_EXPECTED = 10  # Expect up to 10 concurrent processes
    CONNECTIONS_PER_PROCESS = AVAILABLE_CONNECTIONS // MAX_PROCESSES_EXPECTED  # 8

    # Connection pool settings for each DatabaseManager instance
    MIN_POOL_SIZE = 1
    MAX_POOL_SIZE = 1  # Single connection per process - most conservative

    # Alternative configurations based on workload
    SEQUENTIAL_POOL_SIZE = 1    # For sequential processing
    BATCH_POOL_SIZE = 2         # For small batch processing
    CONCURRENT_POOL_SIZE = 3    # Only for non-connection intensive tasks

    # Connection timeout and retry settings
    CONNECTION_TIMEOUT = 30  # seconds
    POOL_RETRY_ATTEMPTS = 3
    POOL_RETRY_DELAY = 0.5  # seconds

    @classmethod
    def get_pool_config(cls) -> Dict[str, Any]:
        """Get connection pool configuration"""
        return {
            'min_conn': cls.MIN_POOL_SIZE,
            'max_conn': cls.MAX_POOL_SIZE,
            'timeout': cls.CONNECTION_TIMEOUT
        }

    @classmethod
    def get_connection_params(cls) -> Dict[str, Any]:
        """Get database connection parameters from unified settings"""
        try:
            from ..config.settings import get_settings
            settings = get_settings()
            return {
                'host': settings.database.host,
                'port': settings.database.port,
                'database': settings.database.name,
                'user': settings.database.user,
                'password': settings.database.password,
                'min_conn': settings.database.min_connections,
                'max_conn': settings.database.max_connections,
                'timeout': settings.database.timeout
            }
        except ImportError:
            # Fallback to environment variables for backward compatibility
            return cls._get_legacy_connection_params()

    @classmethod
    def _get_legacy_connection_params(cls) -> Dict[str, Any]:
        """Legacy connection parameters from environment variables"""
        return {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', '5432')),
            'database': os.getenv('DB_NAME', 'mltrading'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'nishant'),
            'min_conn': cls.MIN_POOL_SIZE,
            'max_conn': cls.MAX_POOL_SIZE,
            'timeout': cls.CONNECTION_TIMEOUT
        }

    @classmethod
    def log_configuration(cls):
        """Log current connection configuration"""
        import logging
        logger = logging.getLogger('mltrading.connection_config')

        logger.info(f"Database Connection Configuration:")
        logger.info(f"  PostgreSQL max_connections: {cls.POSTGRES_MAX_CONNECTIONS}")
        logger.info(f"  System reserved: {cls.SYSTEM_RESERVED_CONNECTIONS}")
        logger.info(f"  Available for MLTrading: {cls.AVAILABLE_CONNECTIONS}")
        logger.info(f"  Expected concurrent processes: {cls.MAX_PROCESSES_EXPECTED}")
        logger.info(f"  Connections per process: {cls.CONNECTIONS_PER_PROCESS}")
        logger.info(f"  Pool size per DatabaseManager: {cls.MIN_POOL_SIZE}-{cls.MAX_POOL_SIZE}")


# Production-safe connection limits
PRODUCTION_CONNECTION_CONFIG = {
    'min_conn': ConnectionConfig.MIN_POOL_SIZE,
    'max_conn': ConnectionConfig.MAX_POOL_SIZE,
    'timeout': ConnectionConfig.CONNECTION_TIMEOUT
}


def get_safe_db_config():
    """Get production-safe database configuration"""
    return {
        **ConnectionConfig.get_connection_params(),
        **ConnectionConfig.get_pool_config()
    }
