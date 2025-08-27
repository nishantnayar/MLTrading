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
    MAX_POOL_SIZE = min(3, CONNECTIONS_PER_PROCESS)  # Conservative: 3 connections max per process
    
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
        """Get database connection parameters"""
        return {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', '5432')),
            'database': os.getenv('DB_NAME', 'mltrading'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'nishant'),
            'connect_timeout': cls.CONNECTION_TIMEOUT
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