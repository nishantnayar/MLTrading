"""
Analytics service for dashboard statistics and performance metrics.
Handles portfolio analytics, trading statistics, and performance calculations.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from .base_service import BaseDashboardService


class AnalyticsService(BaseDashboardService):
    """Service to handle analytics and statistics operations."""
    
    def get_summary_statistics(self) -> Dict[str, Any]:
        """Get summary statistics for the dashboard."""
        try:
            # Get total symbols with data
            total_symbols_query = "SELECT COUNT(DISTINCT symbol) FROM market_data WHERE source = 'yahoo'"
            total_symbols_result = self.execute_query(total_symbols_query)
            total_symbols = total_symbols_result[0][0] if total_symbols_result else 0
            
            # For now, return mock data for trading-related metrics
            # These will be replaced with real data when trading engine is implemented
            stats = {
                'total_symbols': total_symbols,
                'active_trades': 0,  # Will be calculated from orders table
                'portfolio_value': 0,  # Will be calculated from positions
                'daily_pnl': 0  # Will be calculated from fills table
            }
            
            self.logger.info("Retrieved summary statistics")
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting summary statistics: {e}")
            return self.get_fallback_data('statistics')
    
    def get_market_overview(self, days: int = 30) -> Dict[str, Any]:
        """Get market overview data for the specified period."""
        try:
            # For now, create a simple market overview based on average closing prices
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            query = """
                SELECT DATE(timestamp) as date, AVG(close) as avg_close
                FROM market_data
                WHERE source = 'yahoo' 
                AND timestamp >= %s 
                AND timestamp <= %s
                AND close IS NOT NULL
                GROUP BY DATE(timestamp)
                ORDER BY date
            """
            
            results = self.execute_query(query, (start_date, end_date))
            
            if not results:
                self.logger.warning("No market overview data found")
                return {'dates': [], 'values': []}
            
            dates = [result[0].strftime('%Y-%m-%d') for result in results]
            values = [float(result[1]) for result in results]
            
            self.logger.info(f"Retrieved market overview data for {len(dates)} days")
            
            return {
                'dates': dates,
                'values': values
            }
            
        except Exception as e:
            self.logger.error(f"Error getting market overview: {e}")
            return {'dates': [], 'values': []}
    
    def get_top_performers(self, days: int = 1, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top performing stocks over the specified period."""
        try:
            # Calculate performance over the specified period
            query = """
                WITH price_changes AS (
                    SELECT 
                        m1.symbol,
                        s.company_name,
                        m1.close as current_close,
                        m2.close as previous_close,
                        ((m1.close - m2.close) / m2.close * 100) as change_percent
                    FROM market_data m1
                    JOIN market_data m2 ON m1.symbol = m2.symbol
                    LEFT JOIN stock_info s ON m1.symbol = s.symbol
                    WHERE m1.source = 'yahoo' 
                    AND m2.source = 'yahoo'
                    AND m1.timestamp >= (CURRENT_DATE - INTERVAL '%s days')
                    AND m2.timestamp >= (CURRENT_DATE - INTERVAL '%s days')
                    AND m1.timestamp = (
                        SELECT MAX(timestamp) 
                        FROM market_data 
                        WHERE symbol = m1.symbol AND source = 'yahoo'
                        AND timestamp >= (CURRENT_DATE - INTERVAL '%s days')
                    )
                    AND m2.timestamp = (
                        SELECT MIN(timestamp) 
                        FROM market_data 
                        WHERE symbol = m2.symbol AND source = 'yahoo'
                        AND timestamp >= (CURRENT_DATE - INTERVAL '%s days')
                    )
                )
                SELECT 
                    symbol,
                    company_name,
                    current_close,
                    previous_close,
                    ROUND(change_percent, 2) as change
                FROM price_changes
                WHERE change_percent IS NOT NULL
                ORDER BY change_percent DESC
                LIMIT %s
            """
            
            results = self.execute_query(query, (days, days, days, days, limit))
            
            if not results:
                self.logger.warning("No top performers data found")
                return []
            
            performers = []
            for result in results:
                performers.append({
                    'symbol': result[0],
                    'company_name': result[1] or result[0],
                    'current_price': float(result[2]),
                    'previous_price': float(result[3]),
                    'change': float(result[4])
                })
            
            self.logger.info(f"Retrieved {len(performers)} top performers")
            return performers
            
        except Exception as e:
            self.logger.error(f"Error getting top performers: {e}")
            return []
    
    def get_recent_activity(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent trading activity."""
        try:
            # For now, return mock data since trading engine isn't implemented yet
            # This will be replaced with real order/fill data when available
            
            activity = [
                {
                    'time': '10:30 AM',
                    'action': 'BUY',
                    'symbol': 'AAPL',
                    'price': 150.25
                },
                {
                    'time': '10:15 AM', 
                    'action': 'SELL',
                    'symbol': 'MSFT',
                    'price': 280.50
                },
                {
                    'time': '09:45 AM',
                    'action': 'BUY',
                    'symbol': 'GOOGL',
                    'price': 2800.75
                }
            ]
            
            self.logger.info("Retrieved mock recent activity data")
            return activity[:limit]
            
        except Exception as e:
            self.logger.error(f"Error getting recent activity: {e}")
            return []
    
    def get_portfolio_performance(self, days: int = 30) -> Dict[str, Any]:
        """Get portfolio performance metrics."""
        try:
            # Mock portfolio performance data
            # Will be replaced with real calculations when portfolio tracking is implemented
            
            performance = {
                'total_value': 50000.00,
                'daily_change': 1250.75,
                'daily_change_percent': 2.56,
                'total_return': 5000.00,
                'total_return_percent': 11.11,
                'sharpe_ratio': 1.25,
                'max_drawdown': -8.5,
                'win_rate': 65.2
            }
            
            self.logger.info("Retrieved mock portfolio performance data")
            return performance
            
        except Exception as e:
            self.logger.error(f"Error getting portfolio performance: {e}")
            return {}
    
    def get_symbol_correlation(self, symbols: List[str], days: int = 90) -> Dict[str, Any]:
        """Calculate correlation matrix for given symbols."""
        try:
            if not symbols or len(symbols) < 2:
                return {}
            
            # Get price data for all symbols
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            price_data = {}
            for symbol in symbols[:10]:  # Limit to 10 symbols to avoid performance issues
                query = """
                    SELECT DATE(timestamp) as date, close
                    FROM market_data
                    WHERE symbol = %s AND source = 'yahoo'
                    AND timestamp >= %s AND timestamp <= %s
                    AND close IS NOT NULL
                    ORDER BY date
                """
                
                results = self.execute_query(query, (symbol.upper(), start_date, end_date))
                
                if results:
                    price_data[symbol] = {result[0]: float(result[1]) for result in results}
            
            if len(price_data) < 2:
                return {}
            
            # Calculate simple correlation (basic implementation)
            # In a production system, would use pandas or numpy for more sophisticated calculations
            correlations = {}
            symbol_list = list(price_data.keys())
            
            for i, symbol1 in enumerate(symbol_list):
                correlations[symbol1] = {}
                for j, symbol2 in enumerate(symbol_list):
                    if i == j:
                        correlations[symbol1][symbol2] = 1.0
                    elif j < i:
                        # Use previously calculated correlation (symmetric)
                        correlations[symbol1][symbol2] = correlations[symbol2][symbol1]
                    else:
                        # Calculate correlation (simplified)
                        common_dates = set(price_data[symbol1].keys()) & set(price_data[symbol2].keys())
                        if len(common_dates) > 10:
                            # Mock correlation for now (would use proper statistical calculation)
                            correlations[symbol1][symbol2] = 0.5  # Placeholder
                        else:
                            correlations[symbol1][symbol2] = 0.0
            
            self.logger.info(f"Calculated correlation matrix for {len(symbol_list)} symbols")
            
            return {
                'symbols': symbol_list,
                'correlations': correlations,
                'period_days': days
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating symbol correlation: {e}")
            return {}
    
    def get_volatility_metrics(self, symbol: str, days: int = 30) -> Dict[str, Any]:
        """Calculate volatility metrics for a symbol."""
        try:
            if not self.validate_symbol(symbol):
                return {}
            
            # Get daily returns for volatility calculation
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days + 1)  # Extra day for return calculation
            
            query = """
                SELECT DATE(timestamp) as date, close
                FROM market_data
                WHERE symbol = %s AND source = 'yahoo'
                AND timestamp >= %s AND timestamp <= %s
                AND close IS NOT NULL
                GROUP BY DATE(timestamp)
                ORDER BY date
            """
            
            results = self.execute_query(query, (symbol.upper(), start_date, end_date))
            
            if not results or len(results) < 2:
                return {}
            
            # Calculate daily returns
            prices = [float(result[1]) for result in results]
            returns = []
            
            for i in range(1, len(prices)):
                daily_return = (prices[i] - prices[i-1]) / prices[i-1]
                returns.append(daily_return)
            
            if not returns:
                return {}
            
            # Calculate volatility metrics
            import statistics
            
            mean_return = statistics.mean(returns)
            std_dev = statistics.stdev(returns) if len(returns) > 1 else 0
            
            # Annualized volatility (assuming 252 trading days per year)
            annualized_volatility = std_dev * (252 ** 0.5) * 100
            
            volatility_metrics = {
                'symbol': symbol.upper(),
                'period_days': days,
                'daily_volatility': std_dev * 100,
                'annualized_volatility': annualized_volatility,
                'mean_daily_return': mean_return * 100,
                'min_daily_return': min(returns) * 100,
                'max_daily_return': max(returns) * 100,
                'return_count': len(returns)
            }
            
            self.logger.info(f"Calculated volatility metrics for {symbol}")
            return volatility_metrics
            
        except Exception as e:
            self.logger.error(f"Error calculating volatility metrics for {symbol}: {e}")
            return {}