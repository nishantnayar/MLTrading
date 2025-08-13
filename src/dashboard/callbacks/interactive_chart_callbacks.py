"""
Interactive chart callbacks for advanced chart features.
Handles technical indicators, zoom controls, and chart interactions.
"""

import plotly.graph_objs as go
from dash import Input, Output, State, callback_context, html
import dash_bootstrap_components as dbc
import pandas as pd
from typing import List, Dict, Any, Optional

from ..layouts.interactive_chart import InteractiveChartBuilder
from ..services.market_data_service import MarketDataService
from ..services.technical_indicators import TechnicalIndicatorService
from ..utils.validators import InputValidator
from ...utils.logging_config import get_ui_logger

logger = get_ui_logger("interactive_chart_callbacks")


class InteractiveChartCallbacks:
    """Handles all interactive chart callbacks."""
    
    def __init__(self):
        self.chart_builder = InteractiveChartBuilder()
        self.market_service = MarketDataService()
        self.indicator_service = TechnicalIndicatorService()
    
    def register_callbacks(self, app):
        """Register all interactive chart callbacks."""
        
        @app.callback(
            Output("advanced-price-chart", "figure"),
            [
                Input("symbol-dropdown", "value"),
                Input("time-range-dropdown", "value"),
                Input("chart-type-dropdown", "value"),
                Input("overlay-indicators-dropdown", "value"),
                Input("oscillator-indicators-dropdown", "value"),
                Input("volume-toggle", "value"),
                Input("refresh-data-btn", "n_clicks")
            ],
            prevent_initial_call=False
        )
        def update_advanced_chart(symbol, time_range, chart_type, overlay_indicators, 
                                oscillator_indicators, show_volume, refresh_clicks):
            """Update advanced chart with technical indicators."""
            try:
                # Validate inputs
                if not symbol:
                    return self.chart_builder._create_empty_chart("Please select a symbol")
                
                is_valid, error = InputValidator.validate_symbol(symbol)
                if not is_valid:
                    return self.chart_builder._create_empty_chart(f"Invalid symbol: {error}")
                
                # Get time range
                time_range_map = {
                    '1D': 1, '1W': 7, '1M': 30, '3M': 90, 
                    '6M': 180, '1Y': 365, 'ALL': 1000
                }
                days = time_range_map.get(time_range, 30)
                
                # Get market data
                df = self.market_service.get_market_data(symbol, days=days)
                
                if df is None or df.empty:
                    return self.chart_builder._create_empty_chart(f"No data available for {symbol}")
                
                # Combine indicators
                all_indicators = []
                if overlay_indicators:
                    all_indicators.extend(overlay_indicators)
                if oscillator_indicators:
                    all_indicators.extend(oscillator_indicators)
                
                # Create advanced chart
                fig = self.chart_builder.create_advanced_price_chart(
                    df=df,
                    symbol=symbol,
                    indicators=all_indicators,
                    show_volume=show_volume,
                    chart_type=chart_type or 'candlestick'
                )
                
                logger.info(f"Updated advanced chart for {symbol} with {len(all_indicators)} indicators")
                return fig
                
            except Exception as e:
                logger.error(f"Error updating advanced chart: {e}")
                return self.chart_builder._create_empty_chart(f"Error loading chart: {str(e)}")
        
        @app.callback(
            Output("indicator-info-collapse", "is_open"),
            [Input("indicator-info-btn", "n_clicks")],
            [State("indicator-info-collapse", "is_open")]
        )
        def toggle_indicator_info(n_clicks, is_open):
            """Toggle indicator information panel."""
            if n_clicks:
                return not is_open
            return is_open
        
        @app.callback(
            Output("chart-analysis-modal", "is_open"),
            [Input("analysis-btn", "n_clicks"), Input("close-analysis-modal", "n_clicks")],
            [State("chart-analysis-modal", "is_open")]
        )
        def toggle_analysis_modal(analysis_clicks, close_clicks, is_open):
            """Toggle chart analysis modal."""
            if analysis_clicks or close_clicks:
                return not is_open
            return is_open
        
        @app.callback(
            Output("chart-analysis-content", "children"),
            [Input("analysis-btn", "n_clicks")],
            [State("symbol-dropdown", "value")]
        )
        def generate_chart_analysis(n_clicks, symbol):
            """Generate comprehensive chart analysis."""
            if not n_clicks or not symbol:
                return html.Div("Select a symbol and click Analysis to view insights.")
            
            try:
                # Get market data
                df = self.market_service.get_market_data(symbol, days=90)
                
                if df is None or df.empty:
                    return dbc.Alert("No data available for analysis.", color="warning")
                
                # Calculate all indicators
                indicators = self.indicator_service.calculate_all_indicators(df)
                
                # Generate analysis
                analysis = self._generate_technical_analysis(df, indicators, symbol)
                
                return analysis
                
            except Exception as e:
                logger.error(f"Error generating analysis: {e}")
                return dbc.Alert(f"Error generating analysis: {str(e)}", color="danger")
        
        @app.callback(
            [Output("support-levels-store", "data"),
             Output("resistance-levels-store", "data")],
            [Input("symbol-dropdown", "value"),
             Input("calculate-levels-btn", "n_clicks")]
        )
        def calculate_support_resistance(symbol, n_clicks):
            """Calculate and store support/resistance levels."""
            if not symbol or not n_clicks:
                return [], []
            
            try:
                df = self.market_service.get_market_data(symbol, days=180)
                if df is None or df.empty:
                    return [], []
                
                levels = self.indicator_service.calculate_support_resistance(df, window=20)
                
                return levels.get('support', []), levels.get('resistance', [])\n                
            except Exception as e:\n                logger.error(f"Error calculating support/resistance: {e}")
                return [], []
        
        @app.callback(
            Output("chart-statistics", "children"),
            [Input("symbol-dropdown", "value"),
             Input("time-range-dropdown", "value")]
        )
        def update_chart_statistics(symbol, time_range):
            """Update chart statistics panel."""
            if not symbol:
                return html.Div("Select a symbol to view statistics.")
            
            try:
                # Get time range
                time_range_map = {
                    '1D': 1, '1W': 7, '1M': 30, '3M': 90, 
                    '6M': 180, '1Y': 365, 'ALL': 1000
                }
                days = time_range_map.get(time_range, 30)
                
                # Get market data
                df = self.market_service.get_market_data(symbol, days=days)
                
                if df is None or df.empty:
                    return dbc.Alert("No data available for statistics.", color="warning")
                
                # Calculate statistics
                stats = self._calculate_chart_statistics(df, symbol, days)
                
                return self._create_statistics_cards(stats)
                
            except Exception as e:
                logger.error(f"Error updating statistics: {e}")
                return dbc.Alert(f"Error loading statistics: {str(e)}", color="danger")
    
    def _generate_technical_analysis(self, df: pd.DataFrame, indicators: Dict[str, Any], symbol: str) -> html.Div:
        """Generate comprehensive technical analysis."""
        analysis_items = []
        
        # Price Analysis
        current_price = df['close'].iloc[-1]
        price_change = ((current_price - df['close'].iloc[0]) / df['close'].iloc[0]) * 100
        
        analysis_items.append(
            dbc.Card([
                dbc.CardHeader("Price Analysis"),
                dbc.CardBody([
                    html.P(f"Current Price: ${current_price:.2f}"),
                    html.P(f"Period Change: {price_change:+.2f}%"),
                    html.P(self._get_price_trend_analysis(df))
                ])
            ], className="mb-3")
        )
        
        # Moving Average Analysis
        if 'sma_20' in indicators and 'sma_50' in indicators:
            sma_20 = indicators['sma_20'].iloc[-1]
            sma_50 = indicators['sma_50'].iloc[-1]
            
            ma_signal = "Bullish" if sma_20 > sma_50 else "Bearish"
            ma_analysis = f"SMA(20): ${sma_20:.2f}, SMA(50): ${sma_50:.2f} - {ma_signal} signal"
            
            analysis_items.append(
                dbc.Card([
                    dbc.CardHeader("Moving Average Analysis"),
                    dbc.CardBody([
                        html.P(ma_analysis),
                        html.P(self._get_ma_position_analysis(current_price, sma_20, sma_50))
                    ])
                ], className="mb-3")
            )
        
        # RSI Analysis
        if 'rsi' in indicators:
            rsi_value = indicators['rsi'].iloc[-1]
            rsi_analysis = self._get_rsi_analysis(rsi_value)
            
            analysis_items.append(
                dbc.Card([
                    dbc.CardHeader("RSI Analysis"),
                    dbc.CardBody([
                        html.P(f"RSI(14): {rsi_value:.2f}"),
                        html.P(rsi_analysis)
                    ])
                ], className="mb-3")
            )
        
        # MACD Analysis
        if 'macd' in indicators:
            macd_data = indicators['macd']
            macd_value = macd_data['macd'].iloc[-1]
            signal_value = macd_data['signal'].iloc[-1]
            histogram_value = macd_data['histogram'].iloc[-1]
            
            macd_analysis = self._get_macd_analysis(macd_value, signal_value, histogram_value)
            
            analysis_items.append(
                dbc.Card([
                    dbc.CardHeader("MACD Analysis"),
                    dbc.CardBody([
                        html.P(f"MACD: {macd_value:.4f}"),
                        html.P(f"Signal: {signal_value:.4f}"),
                        html.P(f"Histogram: {histogram_value:.4f}"),
                        html.P(macd_analysis)
                    ])
                ], className="mb-3")
            )
        
        # Overall Assessment
        overall_sentiment = self._get_overall_sentiment(indicators, df)
        
        analysis_items.append(
            dbc.Card([
                dbc.CardHeader("Overall Assessment"),
                dbc.CardBody([
                    html.H5(f"Market Sentiment: {overall_sentiment['sentiment']}", 
                           className=f"text-{overall_sentiment['color']}"),
                    html.P(overall_sentiment['reasoning'])
                ])
            ], color=overall_sentiment['color'], outline=True)
        )
        
        return html.Div(analysis_items)
    
    def _calculate_chart_statistics(self, df: pd.DataFrame, symbol: str, days: int) -> Dict[str, Any]:
        """Calculate comprehensive chart statistics."""
        stats = {}
        
        # Basic price statistics
        stats['high'] = df['high'].max()
        stats['low'] = df['low'].min()
        stats['current'] = df['close'].iloc[-1]
        stats['volume_avg'] = df['volume'].mean()
        stats['volume_total'] = df['volume'].sum()
        
        # Price changes
        stats['change_abs'] = stats['current'] - df['close'].iloc[0]
        stats['change_pct'] = (stats['change_abs'] / df['close'].iloc[0]) * 100
        
        # Volatility
        returns = df['close'].pct_change().dropna()
        stats['volatility_daily'] = returns.std() * 100
        stats['volatility_annual'] = stats['volatility_daily'] * (252 ** 0.5)
        
        # Technical levels
        stats['resistance'] = df['high'].rolling(window=20).max().iloc[-1]
        stats['support'] = df['low'].rolling(window=20).min().iloc[-1]
        
        return stats
    
    def _create_statistics_cards(self, stats: Dict[str, Any]) -> html.Div:
        """Create statistics display cards."""
        cards = [
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(f"${stats['current']:.2f}", className="text-primary"),
                        html.P("Current Price", className="text-muted mb-0")
                    ])
                ], className="text-center")
            ], width=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(f"{stats['change_pct']:+.2f}%", 
                               className="text-success" if stats['change_pct'] >= 0 else "text-danger"),
                        html.P("Period Change", className="text-muted mb-0")
                    ])
                ], className="text-center")
            ], width=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(f"{stats['volatility_daily']:.2f}%", className="text-warning"),
                        html.P("Daily Volatility", className="text-muted mb-0")
                    ])
                ], className="text-center")
            ], width=3),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H4(f"{stats['volume_avg']:,.0f}", className="text-info"),
                        html.P("Avg Volume", className="text-muted mb-0")
                    ])
                ], className="text-center")
            ], width=3)
        ]
        
        return dbc.Row(cards, className="mb-3")
    
    def _get_price_trend_analysis(self, df: pd.DataFrame) -> str:
        """Analyze price trend."""
        if len(df) < 10:
            return "Insufficient data for trend analysis."
        
        recent_prices = df['close'].tail(10)
        if recent_prices.iloc[-1] > recent_prices.iloc[0]:
            return "Short-term uptrend detected."
        elif recent_prices.iloc[-1] < recent_prices.iloc[0]:
            return "Short-term downtrend detected."
        else:
            return "Price consolidating in range."
    
    def _get_ma_position_analysis(self, price: float, sma_20: float, sma_50: float) -> str:
        """Analyze moving average positions."""
        if price > sma_20 > sma_50:
            return "Price above both MAs - strong bullish signal."
        elif price > sma_20 and sma_20 < sma_50:
            return "Price above short MA but below long MA - mixed signal."
        elif price < sma_20 < sma_50:
            return "Price below both MAs - strong bearish signal."
        else:
            return "Mixed moving average signals."
    
    def _get_rsi_analysis(self, rsi: float) -> str:
        """Analyze RSI value."""
        if rsi > 70:
            return "RSI indicates overbought conditions - potential reversal."
        elif rsi < 30:
            return "RSI indicates oversold conditions - potential bounce."
        elif 40 <= rsi <= 60:
            return "RSI in neutral zone - no clear signal."
        else:
            return "RSI trending but not at extreme levels."
    
    def _get_macd_analysis(self, macd: float, signal: float, histogram: float) -> str:
        """Analyze MACD indicators."""
        if macd > signal and histogram > 0:
            return "MACD above signal line with positive histogram - bullish momentum."
        elif macd < signal and histogram < 0:
            return "MACD below signal line with negative histogram - bearish momentum."
        elif macd > 0 and signal > 0:
            return "Both MACD and signal positive - overall bullish trend."
        elif macd < 0 and signal < 0:
            return "Both MACD and signal negative - overall bearish trend."
        else:
            return "MACD showing mixed signals - trend unclear."
    
    def _get_overall_sentiment(self, indicators: Dict[str, Any], df: pd.DataFrame) -> Dict[str, str]:
        """Calculate overall market sentiment."""
        bullish_signals = 0
        bearish_signals = 0
        total_signals = 0
        
        # RSI analysis
        if 'rsi' in indicators:
            rsi = indicators['rsi'].iloc[-1]
            total_signals += 1
            if rsi < 30:
                bullish_signals += 1
            elif rsi > 70:
                bearish_signals += 1
        
        # MACD analysis
        if 'macd' in indicators:
            macd_data = indicators['macd']
            macd_value = macd_data['macd'].iloc[-1]
            signal_value = macd_data['signal'].iloc[-1]
            total_signals += 1
            if macd_value > signal_value:
                bullish_signals += 1
            else:
                bearish_signals += 1
        
        # Moving average analysis
        if 'sma_20' in indicators and 'sma_50' in indicators:
            sma_20 = indicators['sma_20'].iloc[-1]
            sma_50 = indicators['sma_50'].iloc[-1]
            total_signals += 1
            if sma_20 > sma_50:
                bullish_signals += 1
            else:
                bearish_signals += 1
        
        # Calculate sentiment
        if total_signals == 0:
            return {
                'sentiment': 'Neutral',
                'color': 'secondary',
                'reasoning': 'Insufficient indicator data for sentiment analysis.'
            }
        
        bullish_ratio = bullish_signals / total_signals
        
        if bullish_ratio >= 0.7:
            return {
                'sentiment': 'Bullish',
                'color': 'success',
                'reasoning': f'{bullish_signals}/{total_signals} indicators showing bullish signals.'
            }
        elif bullish_ratio <= 0.3:
            return {
                'sentiment': 'Bearish',
                'color': 'danger',
                'reasoning': f'{bearish_signals}/{total_signals} indicators showing bearish signals.'
            }
        else:
            return {
                'sentiment': 'Neutral',
                'color': 'warning',
                'reasoning': f'Mixed signals: {bullish_signals} bullish, {bearish_signals} bearish out of {total_signals} indicators.'
            }