"""
Base service class with common database connection logic.
Provides shared functionality for all dashboard services.
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data.storage.database import get_db_manager
from src.utils.logging_config import get_ui_logger


class BaseDashboardService:
    """Base service class with common database connection and error handling."""
    
    def __init__(self):
        """Initialize the base service with database connection."""
        self.db_manager = get_db_manager()
        self.logger = get_ui_logger("dashboard_service")
        self.logger.info(f"{self.__class__.__name__} initialized")
    
    def handle_db_error(self, operation: str, error: Exception) -> Dict[str, Any]:
        """Handle database errors with consistent logging and fallback."""
        self.logger.error(f"Database error in {operation}: {error}")
        return {
            'error': True,
            'message': f"Database error in {operation}",
            'details': str(error)
        }
    
    def validate_symbol(self, symbol: str) -> bool:
        """Validate stock symbol format."""
        if not symbol or not isinstance(symbol, str):
            return False
        
        symbol = symbol.upper().strip()
        
        # Basic validation: 1-5 uppercase letters, optionally with dots or hyphens
        import re
        return bool(re.match(r'^[A-Z]{1,5}([.-][A-Z]{1,2})?$', symbol))
    
    def get_fallback_data(self, data_type: str) -> Dict[str, Any]:
        """Provide fallback data when database operations fail."""
        fallback_data = {
            'symbols': [],
            'sectors': [],
            'industries': [],
            'market_data': [],
            'statistics': {
                'total_symbols': 0,
                'active_trades': 0,
                'portfolio_value': 0,
                'daily_pnl': 0
            }
        }
        
        return fallback_data.get(data_type, [])
    
    def format_error_response(self, error_type: str, message: str, details: str = "") -> Dict[str, Any]:
        """Format consistent error responses."""
        return {
            'success': False,
            'error_type': error_type,
            'message': message,
            'details': details,
            'data': None
        }
    
    def format_success_response(self, data: Any, message: str = "Operation successful") -> Dict[str, Any]:
        """Format consistent success responses."""
        return {
            'success': True,
            'error_type': None,
            'message': message,
            'details': "",
            'data': data
        }
    
    def execute_query(self, query: str, params: tuple = None) -> List[tuple]:
        """Execute a SELECT query and return results."""
        try:
            conn = self.db_manager.get_connection()
            try:
                with conn.cursor() as cur:
                    if params:
                        cur.execute(query, params)
                    else:
                        cur.execute(query)
                    return cur.fetchall()
            finally:
                self.db_manager.return_connection(conn)
        except Exception as e:
            self.logger.error(f"Error executing query: {e}")
            return []