"""
Symbol service for managing stock symbols and company information.
Handles symbol metadata, sector/industry data, and symbol filtering.
"""

from typing import List, Dict, Any, Optional
from .base_service import BaseDashboardService
from .cache_service import cached


class SymbolService(BaseDashboardService):
    """Service to handle symbol and company information operations."""
    
    @cached(ttl=300, key_func=lambda self, source='yahoo': f"symbols_{source}")
    def get_available_symbols(self, source: str = 'yahoo') -> List[Dict[str, str]]:
        """Get list of available symbols with market data and company names using batch query."""
        try:
            # Use batch query to get symbols with company names in single DB call
            query = """
                SELECT DISTINCT s.symbol, COALESCE(si.company_name, s.symbol) as company_name
                FROM (
                    SELECT DISTINCT symbol FROM market_data WHERE source = %s
                ) s
                LEFT JOIN stock_info si ON s.symbol = si.symbol
                ORDER BY s.symbol
            """
            
            results = self.execute_query(query, (source,))
            
            if not results:
                self.logger.warning("No symbols found with market data")
                return self.get_fallback_data('symbols')
            
            symbol_data = [
                {
                    'symbol': row[0],
                    'company_name': row[1]
                }
                for row in results
            ]
            
            self.logger.info(f"Retrieved {len(symbol_data)} symbols with company names in single batch query")
            return symbol_data
            
        except Exception as e:
            self.logger.error(f"Error getting available symbols: {e}")
            return self.get_fallback_data('symbols')
    
    def get_symbols_by_sector(self, sector: str, source: str = 'yahoo') -> List[Dict[str, str]]:
        """Get symbols filtered by sector."""
        try:
            if not sector or sector == "All Sectors":
                return self.get_available_symbols(source)
            
            query = """
                SELECT DISTINCT s.symbol, s.company_name 
                FROM stock_info s
                INNER JOIN market_data md ON s.symbol = md.symbol
                WHERE s.sector = %s AND md.source = %s
                ORDER BY s.symbol
            """
            
            results = self.execute_query(query, (sector, source))
            
            if not results:
                self.logger.warning(f"No symbols found for sector: {sector}")
                return []
            
            symbol_data = [
                {
                    'symbol': row[0],
                    'company_name': row[1] or row[0]  # Fallback to symbol if no name
                }
                for row in results
            ]
            
            self.logger.info(f"Retrieved {len(symbol_data)} symbols for sector: {sector}")
            return symbol_data
            
        except Exception as e:
            self.logger.error(f"Error getting symbols by sector {sector}: {e}")
            return self.get_fallback_data('symbols')
    
    def get_symbols_by_industry(self, industry: str, source: str = 'yahoo') -> List[Dict[str, str]]:
        """Get symbols filtered by industry."""
        try:
            if not industry or industry == "All Industries":
                return self.get_available_symbols(source)
            
            query = """
                SELECT DISTINCT s.symbol, s.company_name 
                FROM stock_info s
                INNER JOIN market_data md ON s.symbol = md.symbol
                WHERE s.industry = %s AND md.source = %s
                ORDER BY s.symbol
            """
            
            results = self.execute_query(query, (industry, source))
            
            if not results:
                self.logger.warning(f"No symbols found for industry: {industry}")
                return []
            
            symbol_data = [
                {
                    'symbol': row[0],
                    'company_name': row[1] or row[0]  # Fallback to symbol if no name
                }
                for row in results
            ]
            
            self.logger.info(f"Retrieved {len(symbol_data)} symbols for industry: {industry}")
            return symbol_data
            
        except Exception as e:
            self.logger.error(f"Error getting symbols by industry {industry}: {e}")
            return self.get_fallback_data('symbols')
    
    @cached(ttl=600, key_func=lambda self, source='yahoo': f"sectors_{source}")
    def get_sector_distribution(self, source: str = 'yahoo') -> Dict[str, Any]:
        """Get distribution of symbols by sector."""
        try:
            query = """
                SELECT DISTINCT s.sector, COUNT(DISTINCT s.symbol) as count
                FROM stock_info s
                INNER JOIN market_data md ON s.symbol = md.symbol
                WHERE md.source = %s AND s.sector IS NOT NULL AND s.sector != ''
                GROUP BY s.sector
                ORDER BY count DESC, s.sector ASC
            """
            
            results = self.execute_query(query, (source,))
            
            if not results:
                self.logger.warning("No sector distribution data found")
                return {'sectors': [], 'counts': []}
            
            sectors = [row[0] for row in results]
            counts = [row[1] for row in results]
            
            self.logger.info(f"Retrieved sector distribution: {len(sectors)} sectors")
            
            return {
                'sectors': sectors,
                'counts': counts
            }
            
        except Exception as e:
            self.logger.error(f"Error getting sector distribution: {e}")
            return self.get_fallback_data('sectors')
    
    @cached(ttl=600, key_func=lambda self, sector, source='yahoo': f"industries_{sector}_{source}")
    def get_industry_distribution(self, sector: str, source: str = 'yahoo') -> Dict[str, Any]:
        """Get distribution of symbols by industry within a sector."""
        try:
            if not sector or sector == "All Sectors":
                self.logger.warning("No specific sector provided for industry distribution")
                return {'industries': [], 'counts': []}
            
            query = """
                SELECT DISTINCT s.industry, COUNT(DISTINCT s.symbol) as count
                FROM stock_info s
                INNER JOIN market_data md ON s.symbol = md.symbol
                WHERE md.source = %s AND s.sector = %s 
                AND s.industry IS NOT NULL AND s.industry != ''
                GROUP BY s.industry
                ORDER BY count DESC, s.industry ASC
            """
            
            results = self.execute_query(query, (source, sector))
            
            if not results:
                self.logger.warning(f"No industry distribution data found for sector: {sector}")
                return {'industries': [], 'counts': []}
            
            industries = [row[0] for row in results]
            counts = [row[1] for row in results]
            
            self.logger.info(f"Retrieved industry distribution for {sector}: {len(industries)} industries")
            
            return {
                'industries': industries,
                'counts': counts
            }
            
        except Exception as e:
            self.logger.error(f"Error getting industry distribution for sector {sector}: {e}")
            return self.get_fallback_data('industries')
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get detailed information for a specific symbol."""
        try:
            if not self.validate_symbol(symbol):
                self.logger.warning(f"Invalid symbol format: {symbol}")
                return None
            
            stock_info = self.db_manager.get_stock_info(symbol.upper())
            
            if not stock_info:
                self.logger.warning(f"No information found for symbol: {symbol}")
                return None
            
            self.logger.info(f"Retrieved info for symbol: {symbol}")
            return stock_info
            
        except Exception as e:
            self.logger.error(f"Error getting symbol info for {symbol}: {e}")
            return None
    
    def search_symbols(self, query: str, limit: int = 10) -> List[Dict[str, str]]:
        """Search symbols by symbol or company name."""
        try:
            if not query or len(query) < 2:
                return []
            
            search_query = """
                SELECT DISTINCT s.symbol, s.company_name
                FROM stock_info s
                INNER JOIN market_data md ON s.symbol = md.symbol
                WHERE (
                    s.symbol ILIKE %s OR 
                    s.company_name ILIKE %s
                )
                ORDER BY 
                    CASE WHEN s.symbol ILIKE %s THEN 1 ELSE 2 END,
                    s.symbol
                LIMIT %s
            """
            
            search_pattern = f"%{query}%"
            exact_pattern = f"{query}%"
            
            results = self.execute_query(
                search_query, 
                (search_pattern, search_pattern, exact_pattern, limit)
            )
            
            if not results:
                return []
            
            symbol_data = [
                {
                    'symbol': row[0],
                    'company_name': row[1] or row[0]
                }
                for row in results
            ]
            
            self.logger.info(f"Found {len(symbol_data)} symbols for search: '{query}'")
            return symbol_data
            
        except Exception as e:
            self.logger.error(f"Error searching symbols with query '{query}': {e}")
            return []