"""
Interactive chart callbacks for advanced chart features.
Handles technical indicators, zoom controls, and chart interactions.
"""

import plotly.graph_objs as go
from dash import Input, Output, State, callback_context, html
import dash_bootstrap_components as dbc
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from ..layouts.interactive_chart import InteractiveChartBuilder
from ..services.market_data_service import MarketDataService
from ..services.technical_indicators import TechnicalIndicatorService
from ...utils.logging_config import get_ui_logger

logger = get_ui_logger("interactive_chart_callbacks")


def register_interactive_chart_callbacks(app):
    """Register all interactive chart callbacks with the app."""
    
    chart_builder = InteractiveChartBuilder()
    market_service = MarketDataService()
    indicator_service = TechnicalIndicatorService()
    
    @app.callback(
        Output("interactive-price-chart", "figure"),
        [
            Input("symbol-dropdown", "value"),
            Input("chart-type-dropdown", "value"),
            Input("indicators-dropdown", "value"),
            Input("volume-checkbox", "value"),
            Input("refresh-chart-btn", "n_clicks")
        ],
        prevent_initial_call=False
    )
    def update_interactive_chart(symbol, chart_type, indicators, volume_checkbox, refresh_clicks):
        """Update interactive chart with technical indicators."""
        try:
            # Validate inputs
            if not symbol:
                return chart_builder._create_empty_chart("Please select a symbol")
            
            # Use default time range (chart buttons will handle range selection)
            days = 180  # Default to 6 months for good chart range
            
            # Get market data
            df = market_service.get_market_data(symbol, days=days)
            
            if df is None or df.empty:
                return chart_builder._create_empty_chart(f"No data available for {symbol}")
            
            # Check volume checkbox
            show_volume = 'volume' in (volume_checkbox or [])
            
            # Use indicators or default
            chart_indicators = indicators or []
            
            # Create advanced chart
            fig = chart_builder.create_advanced_price_chart(
                df=df,
                symbol=symbol,
                indicators=chart_indicators,
                show_volume=show_volume,
                chart_type=chart_type or 'candlestick'
            )
            
            logger.info(f"Updated interactive chart for {symbol} with {len(chart_indicators)} indicators")
            return fig
            
        except Exception as e:
            logger.error(f"Error updating interactive chart: {e}")
            return chart_builder._create_empty_chart(f"Error loading chart: {str(e)}")
    
    @app.callback(
        Output("technical-analysis-summary", "children"),
        [
            Input("symbol-dropdown", "value"),
            Input("indicators-dropdown", "value")
        ],
        prevent_initial_call=True
    )
    def update_technical_analysis_summary(symbol, indicators):
        """Update technical analysis summary."""
        try:
            if not symbol:
                return html.P("Select a symbol to view technical analysis.", className="text-muted text-center")
            
            # Get recent market data for analysis
            df = market_service.get_market_data(symbol, days=30)
            
            if df is None or df.empty:
                return html.P(f"No data available for {symbol}", className="text-muted text-center")
            
            # Calculate basic technical indicators
            analysis_indicators = indicator_service.calculate_all_indicators(df)
            
            # Create summary cards
            current_price = df['close'].iloc[-1]
            price_change = ((current_price - df['close'].iloc[0]) / df['close'].iloc[0]) * 100
            
            summary_items = [
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("Current Price", className="text-muted mb-1"),
                            html.H5(f"${current_price:.2f}", className="text-primary mb-0")
                        ])
                    ])
                ], width=3),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("30D Change", className="text-muted mb-1"),
                            html.H5(f"{price_change:+.2f}%", 
                                   className="text-success" if price_change >= 0 else "text-danger")
                        ])
                    ])
                ], width=3),
            ]
            
            # Add RSI if available
            if 'rsi' in analysis_indicators:
                rsi_value = analysis_indicators['rsi'].iloc[-1]
                rsi_color = "text-danger" if rsi_value > 70 else "text-success" if rsi_value < 30 else "text-warning"
                summary_items.append(
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H6("RSI(14)", className="text-muted mb-1"),
                                html.H5(f"{rsi_value:.1f}", className=f"{rsi_color} mb-0")
                            ])
                        ])
                    ], width=3)
                )
            
            # Add trend analysis
            if 'sma_20' in analysis_indicators:
                sma_20 = analysis_indicators['sma_20'].iloc[-1]
                trend = "Bullish" if current_price > sma_20 else "Bearish"
                trend_color = "text-success" if trend == "Bullish" else "text-danger"
                summary_items.append(
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H6("Trend", className="text-muted mb-1"),
                                html.H5(trend, className=f"{trend_color} mb-0")
                            ])
                        ])
                    ], width=3)
                )
            
            return dbc.Row(summary_items)
            
        except Exception as e:
            logger.error(f"Error updating technical analysis summary: {e}")
            return html.P(f"Error loading analysis: {str(e)}", className="text-danger text-center")
