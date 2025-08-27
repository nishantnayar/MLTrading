"""
PostgreSQL database manager for ML Trading System.
Handles connections, table creation, and basic CRUD operations.
"""

import os
import warnings
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from contextlib import contextmanager
import psycopg2
from psycopg2.extras import RealDictCursor, execute_batch
from psycopg2.pool import SimpleConnectionPool
import pandas as pd

# Suppress pandas SQLAlchemy warning
warnings.filterwarnings('ignore', message='pandas only supports SQLAlchemy')

from ...utils.logging_config import get_combined_logger, log_operation
from ...utils.connection_config import ConnectionConfig, get_safe_db_config

logger = get_combined_logger("mltrading.data.database", enable_database_logging=True)


class DatabaseManager:
    """Manages PostgreSQL database connections and operations."""
    
    def __init__(self, host: str = None, port: int = None, 
                 database: str = None, user: str = None, 
                 password: str = None, min_conn: int = None, 
                 max_conn: int = None):
        """Initialize database manager with connection pool using safe defaults."""
        # Use safe configuration defaults
        safe_config = get_safe_db_config()
        
        self.host = host or safe_config['host']
        self.port = port or safe_config['port']
        self.database = database or safe_config['database']
        self.user = user or safe_config['user']
        self.password = password or safe_config['password']
        self.min_conn = min_conn or safe_config['min_conn']
        self.max_conn = max_conn or safe_config['max_conn']
        self.timeout = safe_config['timeout']
        self.pool = None
        self._init_pool()
        
    def _init_pool(self):
        """Initialize connection pool with safe limits."""
        try:
            self.pool = SimpleConnectionPool(
                self.min_conn, self.max_conn,
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                connect_timeout=self.timeout
            )
            logger.info(f"Database pool initialized with {self.min_conn}-{self.max_conn} connections (timeout: {self.timeout}s)")
            ConnectionConfig.log_configuration()
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            logger.warning("Falling back to direct connection mode")
            # Set pool to None to trigger fallback mode
            self.pool = None
            logger.warning("Database pool initialization failed, using fallback mode")
    
    def get_connection(self, timeout=60):
        """Get a connection from the pool with timeout and retry logic."""
        import time
        from psycopg2.pool import PoolError
        
        if self.pool is None:
            # Fallback: create a direct connection
            try:
                return psycopg2.connect(
                    host=self.host,
                    port=self.port,
                    database=self.database,
                    user=self.user,
                    password=self.password
                )
            except Exception as e:
                logger.error(f"Failed to create fallback connection: {e}")
                raise
        
        # Try to get connection with retry and exponential backoff
        max_retries = 5
        base_delay = 0.1
        
        for attempt in range(max_retries):
            try:
                return self.pool.getconn()
            except PoolError as e:
                if "pool exhausted" in str(e).lower() and attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"Connection pool exhausted, retry {attempt + 1}/{max_retries} in {delay:.2f}s")
                    time.sleep(delay)
                    continue
                else:
                    logger.error(f"Failed to get connection after {attempt + 1} attempts: {e}")
                    raise
            except Exception as e:
                logger.error(f"Unexpected error getting connection: {e}")
                raise
    
    def return_connection(self, conn):
        """Return a connection to the pool."""
        if conn is None:
            return
            
        try:
            if self.pool is None:
                # Close the fallback connection
                conn.close()
            else:
                self.pool.putconn(conn)
        except Exception as e:
            logger.error(f"Error returning connection to pool: {e}")
            # If we can't return to pool, close the connection
            try:
                conn.close()
            except:
                pass
    
    @contextmanager
    def get_connection_context(self):
        """Context manager for safe connection handling."""
        conn = None
        try:
            conn = self.get_connection()
            yield conn
        except Exception as e:
            logger.error(f"Error in connection context: {e}")
            raise
        finally:
            if conn is not None:
                self.return_connection(conn)
    
    def check_tables_exist(self) -> bool:
        """Check if all required tables exist in the database."""
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                # Check if market_data table exists
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'market_data'
                    )
                """)
                market_data_exists = cur.fetchone()[0]
                
                # Check if stock_info table exists
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'stock_info'
                    )
                """)
                stock_info_exists = cur.fetchone()[0]
                
                # Check if orders table exists
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'orders'
                    )
                """)
                orders_exists = cur.fetchone()[0]
                
                # Check if fills table exists
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'fills'
                    )
                """)
                fills_exists = cur.fetchone()[0]
                
                # Check if models table exists
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'models'
                    )
                """)
                models_exists = cur.fetchone()[0]
                
                # Check if predictions table exists
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'predictions'
                    )
                """)
                predictions_exists = cur.fetchone()[0]
                
                all_tables_exist = all([
                    market_data_exists, stock_info_exists, orders_exists, fills_exists, 
                    models_exists, predictions_exists
                ])
                
                if all_tables_exist:
                    logger.info("All database tables exist")
                else:
                    logger.warning("Some database tables are missing. Please run the create_tables.sql script")
                
                return all_tables_exist
                
        except Exception as e:
            logger.error(f"Failed to check tables: {e}")
            return False
        finally:
            self.return_connection(conn)
    
    def insert_market_data(self, data: List[Dict[str, Any]]):
        """Insert market data in batch."""
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                query = """
                    INSERT INTO market_data (symbol, timestamp, open, high, low, close, volume, source)
                    VALUES (%(symbol)s, %(timestamp)s, %(open)s, %(high)s, %(low)s, %(close)s, %(volume)s, %(source)s)
                    ON CONFLICT (symbol, timestamp, source) DO UPDATE SET
                        open = EXCLUDED.open,
                        high = EXCLUDED.high,
                        low = EXCLUDED.low,
                        close = EXCLUDED.close,
                        volume = EXCLUDED.volume
                """
                execute_batch(cur, query, data)
                conn.commit()
                logger.info(f"Inserted {len(data)} market data records")
                
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to insert market data: {e}")
            raise
        finally:
            self.return_connection(conn)
    
    def get_market_data(self, symbol: str, start_date: datetime, 
                       end_date: datetime, source: str = 'yahoo') -> pd.DataFrame:
        """Get market data for a symbol within date range."""
        conn = self.get_connection()
        try:
            # Debug: Log what we're searching for
            logger.info(f"Database query - Symbol: {symbol}, Start: {start_date}, End: {end_date}, Source: {source}")
            
            # First, check what data actually exists for this symbol
            debug_query = "SELECT MIN(timestamp), MAX(timestamp), COUNT(*) FROM market_data WHERE symbol = %s AND source = %s"
            with conn.cursor() as cur:
                cur.execute(debug_query, (symbol, source))
                debug_result = cur.fetchone()
                if debug_result:
                    min_ts, max_ts, count = debug_result
                    logger.info(f"Database contains for {symbol}: {count} records from {min_ts} to {max_ts}")
            
            query = """
                SELECT symbol, timestamp, open, high, low, close, volume, source
                FROM market_data 
                WHERE symbol = %s AND timestamp BETWEEN %s AND %s AND source = %s
                ORDER BY timestamp
            """
            # Use pandas with psycopg2 connection directly to avoid SQLAlchemy warning
            import pandas as pd
            df = pd.read_sql_query(query, conn, params=(symbol, start_date, end_date, source))
            
            # Debug: Log what we actually retrieved
            if not df.empty:
                retrieved_min = df['timestamp'].min()
                retrieved_max = df['timestamp'].max()
                logger.info(f"Retrieved from database: {len(df)} records from {retrieved_min} to {retrieved_max}")
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to get market data: {e}")
            # Return empty DataFrame instead of raising to prevent crashes
            return pd.DataFrame()
        finally:
            self.return_connection(conn)
    
    def get_latest_market_data(self, symbol: str, source: str = 'yahoo') -> Optional[Dict]:
        """Get latest market data for a symbol."""
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM market_data 
                    WHERE symbol = %s AND source = %s
                    ORDER BY timestamp DESC LIMIT 1
                """, (symbol, source))
                result = cur.fetchone()
                return dict(result) if result else None
                
        except Exception as e:
            logger.error(f"Failed to get latest market data: {e}")
            raise
        finally:
            self.return_connection(conn)
    
    def insert_order(self, order_data: Dict[str, Any]) -> int:
        """Insert a new order and return the order ID."""
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO orders (symbol, side, quantity, price, order_type, 
                                     status, alpaca_order_id, strategy_name)
                    VALUES (%(symbol)s, %(side)s, %(quantity)s, %(price)s, 
                           %(order_type)s, %(status)s, %(alpaca_order_id)s, %(strategy_name)s)
                    RETURNING id
                """, order_data)
                order_id = cur.fetchone()[0]
                conn.commit()
                logger.info(f"Inserted order {order_id} for {order_data['symbol']}")
                return order_id
                
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to insert order: {e}")
            raise
        finally:
            self.return_connection(conn)
    
    def update_order_status(self, order_id: int, status: str, filled_at: datetime = None):
        """Update order status."""
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                if filled_at:
                    cur.execute("""
                        UPDATE orders SET status = %s, filled_at = %s WHERE id = %s
                    """, (status, filled_at, order_id))
                else:
                    cur.execute("""
                        UPDATE orders SET status = %s WHERE id = %s
                    """, (status, order_id))
                conn.commit()
                logger.info(f"Updated order {order_id} status to {status}")
                
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to update order status: {e}")
            raise
        finally:
            self.return_connection(conn)
    
    def insert_prediction(self, prediction_data: Dict[str, Any]):
        """Insert a model prediction."""
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO predictions (symbol, model_id, timestamp, prediction, confidence, features)
                    VALUES (%(symbol)s, %(model_id)s, %(timestamp)s, %(prediction)s, %(confidence)s, %(features)s)
                """, prediction_data)
                conn.commit()
                logger.info(f"Inserted prediction for {prediction_data['symbol']}")
                
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to insert prediction: {e}")
            raise
        finally:
            self.return_connection(conn)
    
    def get_symbols_with_data(self, source: str = 'yahoo') -> List[str]:
        """Get list of symbols that have market data."""
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT DISTINCT symbol FROM market_data WHERE source = %s ORDER BY symbol
                """, (source,))
                return [row[0] for row in cur.fetchall()]
                
        except Exception as e:
            logger.error(f"Failed to get symbols: {e}")
            raise
        finally:
            self.return_connection(conn)
    
    def get_data_date_range(self, symbol: str, source: str = 'yahoo') -> tuple:
        """Get the date range of available data for a symbol."""
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT MIN(timestamp), MAX(timestamp) 
                    FROM market_data 
                    WHERE symbol = %s AND source = %s
                """, (symbol, source))
                result = cur.fetchone()
                return result if result else (None, None)
                
        except Exception as e:
            logger.error(f"Failed to get date range: {e}")
            raise
        finally:
            self.return_connection(conn)
    
    def insert_stock_info(self, stock_data: Dict[str, Any]):
        """Insert or update stock information."""
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO stock_info (symbol, company_name, sector, industry, 
                                          market_cap, country, currency, exchange, source)
                    VALUES (%(symbol)s, %(company_name)s, %(sector)s, %(industry)s,
                           %(market_cap)s, %(country)s, %(currency)s, %(exchange)s, %(source)s)
                    ON CONFLICT (symbol) DO UPDATE SET
                        company_name = EXCLUDED.company_name,
                        sector = EXCLUDED.sector,
                        industry = EXCLUDED.industry,
                        market_cap = EXCLUDED.market_cap,
                        country = EXCLUDED.country,
                        currency = EXCLUDED.currency,
                        exchange = EXCLUDED.exchange,
                        updated_at = NOW()
                """, stock_data)
                conn.commit()
                logger.info(f"Inserted/updated stock info for {stock_data['symbol']}")
                
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to insert stock info: {e}")
            raise
        finally:
            self.return_connection(conn)
    
    def get_stock_info(self, symbol: str) -> Optional[Dict]:
        """Get stock information for a symbol."""
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM stock_info WHERE symbol = %s
                """, (symbol,))
                result = cur.fetchone()
                return dict(result) if result else None
                
        except Exception as e:
            logger.error(f"Failed to get stock info: {e}")
            raise
        finally:
            self.return_connection(conn)
    
    def get_stocks_by_sector(self, sector: str) -> List[str]:
        """Get all symbols in a specific sector."""
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT symbol FROM stock_info WHERE sector = %s ORDER BY symbol
                """, (sector,))
                return [row[0] for row in cur.fetchall()]
                
        except Exception as e:
            logger.error(f"Failed to get stocks by sector: {e}")
            raise
        finally:
            self.return_connection(conn)
    
    def get_stocks_by_industry(self, industry: str) -> List[str]:
        """Get all symbols in a specific industry."""
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT symbol FROM stock_info WHERE industry = %s ORDER BY symbol
                """, (industry,))
                return [row[0] for row in cur.fetchall()]
                
        except Exception as e:
            logger.error(f"Failed to get stocks by industry: {e}")
            raise
        finally:
            self.return_connection(conn)
    
    def get_all_sectors(self) -> List[str]:
        """Get all unique sectors."""
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT DISTINCT sector FROM stock_info WHERE sector IS NOT NULL ORDER BY sector
                """)
                return [row[0] for row in cur.fetchall()]
                
        except Exception as e:
            logger.error(f"Failed to get sectors: {e}")
            raise
        finally:
            self.return_connection(conn)
    
    def get_all_industries(self) -> List[str]:
        """Get all unique industries."""
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT DISTINCT industry FROM stock_info WHERE industry IS NOT NULL ORDER BY industry
                """)
                return [row[0] for row in cur.fetchall()]
                
        except Exception as e:
            logger.error(f"Failed to get industries: {e}")
            raise
        finally:
            self.return_connection(conn)
    
    def get_industries_by_sector(self, sector: str) -> List[str]:
        """Get all unique industries within a specific sector."""
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT DISTINCT industry FROM stock_info 
                    WHERE sector = %s AND industry IS NOT NULL 
                    ORDER BY industry
                """, (sector,))
                return [row[0] for row in cur.fetchall()]
                
        except Exception as e:
            logger.error(f"Failed to get industries by sector: {e}")
            raise
        finally:
            self.return_connection(conn)
    
    def get_stocks_by_industry(self, industry: str, sector: str = None) -> List[str]:
        """Get all symbols in a specific industry, optionally filtered by sector."""
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                if sector:
                    cur.execute("""
                        SELECT symbol FROM stock_info 
                        WHERE industry = %s AND sector = %s 
                        ORDER BY symbol
                    """, (industry, sector))
                else:
                    cur.execute("""
                        SELECT symbol FROM stock_info 
                        WHERE industry = %s 
                        ORDER BY symbol
                    """, (industry,))
                return [row[0] for row in cur.fetchall()]
                
        except Exception as e:
            logger.error(f"Failed to get stocks by industry: {e}")
            raise
        finally:
            self.return_connection(conn)
    
    def get_earliest_data_date(self, source: str = 'yahoo') -> Optional[datetime]:
        """Get the earliest date in the market_data table."""
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT MIN(timestamp) FROM market_data WHERE source = %s
                """, (source,))
                result = cur.fetchone()
                return result[0] if result and result[0] else None
                
        except Exception as e:
            logger.error(f"Failed to get earliest data date: {e}")
            return None
        finally:
            self.return_connection(conn)
    
    def get_latest_data_date(self, source: str = 'yahoo') -> Optional[datetime]:
        """Get the latest date in the market_data table."""
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT MAX(timestamp) FROM market_data WHERE source = %s
                """, (source,))
                result = cur.fetchone()
                return result[0] if result and result[0] else None
                
        except Exception as e:
            logger.error(f"Failed to get latest data date: {e}")
            return None
        finally:
            self.return_connection(conn)
    
    def close(self):
        """Close the connection pool."""
        if self.pool:
            self.pool.closeall()
            logger.info("Database connection pool closed")


# Global database manager instance
db_manager = None

def get_db_manager() -> DatabaseManager:
    """Get the global database manager instance using environment variables."""
    global db_manager
    if db_manager is None:
        # Use environment variables for database configuration
        host = os.getenv('DB_HOST', 'localhost')
        port = int(os.getenv('DB_PORT', '5432'))
        database = os.getenv('DB_NAME', 'mltrading')
        user = os.getenv('DB_USER', 'postgres')
        password = os.getenv('DB_PASSWORD', 'nishant')  # fallback to hardcoded for backward compatibility
        
        db_manager = DatabaseManager(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )
    return db_manager 