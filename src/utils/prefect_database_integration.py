"""
Prefect Database Integration Module
Manages database connections and integration between Prefect workflows and ML Trading System
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from contextlib import contextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

from ..data.storage.database import DatabaseManager, get_db_manager
from .logging_config import get_combined_logger, get_correlation_id

# Initialize logger
logger = get_combined_logger("mltrading.prefect.database")

class PrefectDatabaseManager:
    """
    Database manager for Prefect integration with schema separation
    Handles connections to both 'public' (application) and 'prefect' (workflow) schemas
    """
    
    def __init__(self, config_path: str = "config/prefect_config.yaml"):
        self.config_path = config_path
        self._app_db_manager = None
        self._prefect_engine = None
        self._prefect_session_factory = None
        self._connection_string = self._build_connection_string()
        
    def _build_connection_string(self) -> str:
        """Build PostgreSQL connection string from environment variables"""
        db_host = os.getenv('DB_HOST', 'localhost')
        db_port = os.getenv('DB_PORT', '5432')
        db_name = os.getenv('DB_NAME', 'mltrading')
        db_user = os.getenv('DB_USER', 'postgres')
        db_password = os.getenv('DB_PASSWORD', '')
        
        return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    @property
    def app_db_manager(self) -> DatabaseManager:
        """Get the main application database manager (public schema)"""
        if self._app_db_manager is None:
            self._app_db_manager = get_db_manager()
        return self._app_db_manager
    
    @property
    def prefect_engine(self):
        """Get SQLAlchemy engine for Prefect schema"""
        if self._prefect_engine is None:
            # Connection string with prefect schema as default
            prefect_connection = f"{self._connection_string}?options=-csearch_path%3Dprefect"
            
            self._prefect_engine = create_engine(
                prefect_connection,
                poolclass=QueuePool,
                pool_size=10,
                max_overflow=20,
                pool_timeout=30,
                pool_recycle=3600,
                echo=False
            )
            
            logger.info("Created Prefect database engine with schema separation")
            
        return self._prefect_engine
    
    @property
    def prefect_session_factory(self):
        """Get session factory for Prefect schema"""
        if self._prefect_session_factory is None:
            self._prefect_session_factory = sessionmaker(bind=self.prefect_engine)
        return self._prefect_session_factory
    
    @contextmanager
    def prefect_session(self):
        """Context manager for Prefect schema database sessions"""
        session = self.prefect_session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Prefect database session error: {e}")
            raise
        finally:
            session.close()
    
    def verify_schema_separation(self) -> Dict[str, Any]:
        """
        Verify that both schemas exist and are properly configured
        Returns status information about schema setup
        """
        results = {
            'public_schema': {'exists': False, 'tables': []},
            'prefect_schema': {'exists': False, 'tables': []},
            'connection_test': False,
            'search_path': None
        }
        
        try:
            # Test application database connection (public schema)
            conn = self.app_db_manager.get_connection()
            try:
                with conn.cursor() as cur:
                    # Check public schema tables
                    cur.execute("""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_type = 'BASE TABLE'
                        ORDER BY table_name;
                    """)
                    public_tables = [row[0] for row in cur.fetchall()]
                    
                    results['public_schema'] = {
                        'exists': len(public_tables) > 0,
                        'tables': public_tables
                    }
                    
                    # Check prefect schema
                    cur.execute("""
                        SELECT EXISTS (
                            SELECT 1 FROM information_schema.schemata 
                            WHERE schema_name = 'prefect'
                        );
                    """)
                    schema_exists = cur.fetchone()[0]
                    results['prefect_schema']['exists'] = schema_exists
                    
                    if schema_exists:
                        # Get prefect schema tables
                        cur.execute("""
                            SELECT table_name 
                            FROM information_schema.tables 
                            WHERE table_schema = 'prefect' 
                            AND table_type = 'BASE TABLE'
                            ORDER BY table_name;
                        """)
                        prefect_tables = [row[0] for row in cur.fetchall()]
                        results['prefect_schema']['tables'] = prefect_tables
                    
                    # Get current search path
                    cur.execute("SHOW search_path;")
                    search_path = cur.fetchone()[0]
                    results['search_path'] = search_path
                    
                    results['connection_test'] = True
            finally:
                self.app_db_manager.return_connection(conn)
                
            logger.info(f"Schema verification completed: {results}")
            
        except Exception as e:
            logger.error(f"Schema verification failed: {e}")
            results['error'] = str(e)
        
        return results
    
    def initialize_prefect_schema(self) -> bool:
        """
        Initialize the Prefect schema if it doesn't exist
        Returns True if successful, False otherwise
        """
        try:
            conn = self.app_db_manager.get_connection()
            try:
                with conn.cursor() as cur:
                    # Create schema if it doesn't exist
                    cur.execute("CREATE SCHEMA IF NOT EXISTS prefect;")
                    
                    # Grant permissions to current user
                    cur.execute("SELECT current_user;")
                    current_user = cur.fetchone()[0]
                    
                    permission_queries = [
                        f"GRANT USAGE ON SCHEMA prefect TO {current_user};",
                        f"GRANT CREATE ON SCHEMA prefect TO {current_user};",
                        f"GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA prefect TO {current_user};",
                        f"GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA prefect TO {current_user};",
                        f"ALTER DEFAULT PRIVILEGES IN SCHEMA prefect GRANT ALL ON TABLES TO {current_user};",
                        f"ALTER DEFAULT PRIVILEGES IN SCHEMA prefect GRANT ALL ON SEQUENCES TO {current_user};"
                    ]
                    
                    for query in permission_queries:
                        cur.execute(query)
                    
                    conn.commit()
            finally:
                self.app_db_manager.return_connection(conn)
                
            logger.info("Prefect schema initialized successfully")
            return True
                
        except Exception as e:
            logger.error(f"Failed to initialize Prefect schema: {e}")
            return False
    
    def log_workflow_event(self, event_type: str, workflow_name: str, 
                          status: str, metadata: Dict[str, Any] = None):
        """
        Log workflow events to the main application logging system
        Integrates Prefect workflow events with existing logging infrastructure
        """
        try:
            log_data = {
                'event_type': event_type,
                'workflow_name': workflow_name,
                'status': status,
                'correlation_id': get_correlation_id(),
                'metadata': metadata or {}
            }
            
            # Log to application database using existing logging system
            with self.app_db_manager.get_connection() as conn:
                insert_query = """
                INSERT INTO system_logs (level, component, message, metadata, created_at)
                VALUES (%(level)s, %(component)s, %(message)s, %(metadata)s, NOW())
                """
                
                level = 'INFO' if status == 'success' else 'ERROR' if status == 'failed' else 'WARNING'
                message = f"Prefect workflow: {workflow_name} - {event_type} - {status}"
                
                conn.execute(text(insert_query), {
                    'level': level,
                    'component': 'prefect_workflow',
                    'message': message,
                    'metadata': log_data
                })
                
                conn.commit()
                
            logger.info(f"Workflow event logged: {message}")
            
        except Exception as e:
            logger.error(f"Failed to log workflow event: {e}")
    
    def get_workflow_statistics(self) -> Dict[str, Any]:
        """
        Get workflow execution statistics from Prefect schema
        Returns aggregated statistics about workflow performance
        """
        stats = {
            'total_flows': 0,
            'successful_runs': 0,
            'failed_runs': 0,
            'average_duration': 0,
            'recent_activity': []
        }
        
        try:
            with self.prefect_session() as session:
                # Query Prefect tables for statistics
                # Note: Actual table names will be created by Prefect
                # This is a template - adjust based on actual Prefect 3.x schema
                
                # Flow runs summary (example query)
                flow_stats_query = """
                SELECT 
                    COUNT(*) as total_runs,
                    COUNT(CASE WHEN state_type = 'COMPLETED' THEN 1 END) as successful,
                    COUNT(CASE WHEN state_type = 'FAILED' THEN 1 END) as failed,
                    AVG(EXTRACT(EPOCH FROM (end_time - start_time))) as avg_duration
                FROM flow_run 
                WHERE start_time >= NOW() - INTERVAL '24 hours';
                """
                
                # Execute query when Prefect tables exist
                # result = session.execute(text(flow_stats_query)).fetchone()
                # if result:
                #     stats.update({
                #         'total_flows': result[0],
                #         'successful_runs': result[1],
                #         'failed_runs': result[2],
                #         'average_duration': result[3] or 0
                #     })
                
            logger.info("Retrieved workflow statistics")
            
        except Exception as e:
            logger.warning(f"Could not retrieve workflow statistics: {e}")
            # This is expected if Prefect hasn't created its tables yet
        
        return stats
    
    def cleanup_old_workflow_data(self, days_to_keep: int = 30) -> Dict[str, int]:
        """
        Clean up old workflow execution data from Prefect schema
        Returns counts of cleaned records
        """
        cleanup_results = {
            'flow_runs_deleted': 0,
            'task_runs_deleted': 0,
            'logs_deleted': 0
        }
        
        try:
            with self.prefect_session() as session:
                # Cleanup queries for Prefect tables
                # Note: Adjust based on actual Prefect 3.x schema
                
                cutoff_date = f"NOW() - INTERVAL '{days_to_keep} days'"
                
                cleanup_queries = [
                    # f"DELETE FROM task_run WHERE start_time < {cutoff_date}",
                    # f"DELETE FROM flow_run WHERE start_time < {cutoff_date}",
                    # f"DELETE FROM logs WHERE timestamp < {cutoff_date}"
                ]
                
                # Execute cleanup when Prefect tables exist
                # for query in cleanup_queries:
                #     result = session.execute(text(query))
                #     cleanup_results[f'{query.split()[2]}_deleted'] = result.rowcount
                
                session.commit()
                
            logger.info(f"Workflow data cleanup completed: {cleanup_results}")
            
        except Exception as e:
            logger.error(f"Workflow data cleanup failed: {e}")
        
        return cleanup_results
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on database connections and schema setup
        Returns health status information
        """
        health_status = {
            'overall_status': 'healthy',
            'checks': {},
            'timestamp': None
        }
        
        try:
            # Check application database connection
            conn = self.app_db_manager.get_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    health_status['checks']['app_database'] = 'healthy'
            finally:
                self.app_db_manager.return_connection(conn)
                
            # Check Prefect schema access (simpler approach)
            try:
                conn = self.app_db_manager.get_connection()
                try:
                    with conn.cursor() as cur:
                        cur.execute("SELECT 1 FROM information_schema.schemata WHERE schema_name = 'prefect' LIMIT 1")
                        health_status['checks']['prefect_schema'] = 'healthy'
                finally:
                    self.app_db_manager.return_connection(conn)
            except Exception:
                health_status['checks']['prefect_schema'] = 'unhealthy'
                
            # Verify schema separation
            schema_status = self.verify_schema_separation()
            if schema_status['connection_test']:
                health_status['checks']['schema_separation'] = 'healthy'
            else:
                health_status['checks']['schema_separation'] = 'unhealthy'
                health_status['overall_status'] = 'degraded'
                
        except Exception as e:
            health_status['overall_status'] = 'unhealthy'
            health_status['error'] = str(e)
            logger.error(f"Database health check failed: {e}")
        
        health_status['timestamp'] = str(datetime.now())
        
        return health_status


# Global instance
_prefect_db_manager = None

def get_prefect_db_manager() -> PrefectDatabaseManager:
    """
    Get or create the global Prefect database manager instance
    Singleton pattern for database connection management
    """
    global _prefect_db_manager
    if _prefect_db_manager is None:
        _prefect_db_manager = PrefectDatabaseManager()
    return _prefect_db_manager

def initialize_prefect_database() -> bool:
    """
    Initialize Prefect database schema and verify setup
    Returns True if successful, False otherwise
    """
    try:
        db_manager = get_prefect_db_manager()
        
        # Initialize schema
        if not db_manager.initialize_prefect_schema():
            return False
            
        # Verify setup
        verification = db_manager.verify_schema_separation()
        if not verification['prefect_schema']['exists']:
            logger.error("Prefect schema verification failed")
            return False
            
        logger.info("Prefect database initialization completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Prefect database initialization failed: {e}")
        return False