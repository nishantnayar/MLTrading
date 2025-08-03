"""
PostgreSQL database manager for ML Trading System.
Handles connections, table creation, and basic CRUD operations.
"""

import os
import logging
import warnings
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor, execute_batch
from psycopg2.pool import SimpleConnectionPool
import pandas as pd

# Suppress pandas SQLAlchemy warning
warnings.filterwarnings('ignore', message='pandas only supports SQLAlchemy')

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages PostgreSQL database connections and operations."""
    
    def __init__(self, host: str = 'localhost', port: int = 5432, 
                 database: str = 'mltrading', user: str = 'postgres', 
                 password: str = 'nishant', min_conn: int = 1, 
                 max_conn: int = 10):
        """Initialize database manager with connection pool."""
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.min_conn = min_conn
        self.max_conn = max_conn
        self.pool = None
        self._init_pool()
        
    def _init_pool(self):
        """Initialize connection pool."""
        try:
            self.pool = SimpleConnectionPool(
                self.min_conn, self.max_conn,
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
            logger.info(f"Database pool initialized with {self.min_conn}-{self.max_conn} connections")
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            # Create a fallback connection for testing
            self.pool = None
            logger.warning("Database pool initialization failed, using fallback mode")
    
    def get_connection(self):
        """Get a connection from the pool."""
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
        return self.pool.getconn()
    
    def return_connection(self, conn):
        """Return a connection to the pool."""
        if self.pool is None:
            # Close the fallback connection
            try:
                conn.close()
            except Exception as e:
                logger.error(f"Error closing fallback connection: {e}")
        else:
            self.pool.putconn(conn)
    
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
            query = """
                SELECT symbol, timestamp, open, high, low, close, volume, source
                FROM market_data 
                WHERE symbol = %s AND timestamp BETWEEN %s AND %s AND source = %s
                ORDER BY timestamp
            """
            # Use pandas with psycopg2 connection directly to avoid SQLAlchemy warning
            import pandas as pd
            df = pd.read_sql_query(query, conn, params=(symbol, start_date, end_date, source))
            return df
            
        except Exception as e:
            logger.error(f"Failed to get market data: {e}")
            raise
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
    
    def close(self):
        """Close the connection pool."""
        if self.pool:
            self.pool.closeall()
            logger.info("Database connection pool closed")


# Global database manager instance
db_manager = None

def get_db_manager() -> DatabaseManager:
    """Get the global database manager instance."""
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager()
    return db_manager 