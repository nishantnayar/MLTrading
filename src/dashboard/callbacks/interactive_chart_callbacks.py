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
from ..utils.date_formatters import format_date_range, format_timestamp

logger = get_ui_logger("interactive_chart_callbacks")


def register_interactive_chart_callbacks(app):
    """Register all interactive chart callbacks with the app."""
    
    chart_builder = InteractiveChartBuilder()
    market_service = MarketDataService()
    indicator_service = TechnicalIndicatorService()
    
    # Initial symbol options callback
    @app.callback(
        Output("symbol-search", "options"),
        [Input("symbol-search", "search_value"),
         Input("filtered-symbols-store", "data")],
        prevent_initial_call=False
    )
    def update_symbol_options(search_value, filtered_symbols):
        """Update symbol dropdown options based on search query and filtered symbols."""
        try:
            # Prioritize filtered symbols if available
            if filtered_symbols and len(filtered_symbols) > 0:
                # Get detailed info for filtered symbols
                all_symbols = market_service.get_available_symbols()
                symbols = [s for s in all_symbols if s['symbol'] in filtered_symbols][:20]
                
                # If user is searching, filter the already filtered symbols
                if search_value and len(search_value) >= 1:
                    symbols = [s for s in symbols 
                             if search_value.upper() in s['symbol'].upper() or 
                                search_value.upper() in s.get('company_name', '').upper()]
            
            elif not search_value or len(search_value) < 1:
                # Return top 10 symbols by default
                symbols = market_service.get_available_symbols()[:10]
            else:
                # Search for symbols matching the query
                symbols = market_service.search_symbols(search_value, limit=20)
            
            if not symbols:
                return [{"label": "No symbols found", "value": "", "disabled": True}]
            
            # Format options for dropdown
            options = []
            for symbol_data in symbols:
                symbol = symbol_data.get('symbol', '')
                company_name = symbol_data.get('company_name', '')
                
                if company_name and company_name != symbol:
                    label = f"{symbol} - {company_name}"
                else:
                    label = symbol
                
                options.append({"label": label, "value": symbol})
            
            return options
            
        except Exception as e:
            logger.error(f"Error updating symbol options: {e}")
            return [{"label": "Error loading symbols", "value": "", "disabled": True}]
    
    @app.callback(
        Output("interactive-price-chart", "figure"),
        [
            Input("symbol-search", "value"),
            Input("chart-type-dropdown", "value"),
            Input("indicators-dropdown", "value"),
            Input("volume-display-dropdown", "value"),
            Input("refresh-chart-btn", "n_clicks")
        ],
        prevent_initial_call=False
    )
    def update_interactive_chart(symbol, chart_type, indicators, volume_display, refresh_clicks):
        """Update interactive chart with technical indicators."""
        try:
            # Use selected symbol or default to ADBE
            if not symbol:
                symbol = "ADBE"
            
            # Get ALL available market data (no artificial date limit)
            # Let users see the complete data range they have
            df = market_service.get_all_available_data(symbol)
            
            if df is None or df.empty:
                return chart_builder._create_empty_chart(f"No data available for {symbol}")
            
            # Log actual data range for debugging
            if not df.empty and 'timestamp' in df.columns:
                actual_start = df['timestamp'].min()
                actual_end = df['timestamp'].max()
                
                # Debug: Log raw dates before formatting
                logger.info(f"Raw date range for {symbol}: {actual_start} to {actual_end}")
                
                data_range_str = format_date_range(actual_start, actual_end, "compact")
                logger.info(f"Chart data for {symbol}: {len(df)} records from {data_range_str}")
                
                # Check if data is recent (within last 30 days)
                from datetime import datetime, timedelta
                is_recent = actual_end >= (datetime.now() - timedelta(days=30))
                
                # Add data range info to chart title with status indicator
                status_icon = "🟢" if is_recent else "🟡"
                status_text = "Live Data" if is_recent else "Historical Data"
                chart_subtitle = f"{status_icon} {status_text}: {data_range_str} ({len(df)} records)"
            else:
                chart_subtitle = None
            
            # Determine volume display settings
            show_volume = volume_display and volume_display != "none"
            color_by_price = True  # Always color by price for better visuals
            
            # Use indicators or default
            chart_indicators = indicators or []
            
            # Create advanced chart
            fig = chart_builder.create_advanced_price_chart(
                df=df,
                symbol=symbol,
                indicators=chart_indicators,
                show_volume=show_volume,
                chart_type=chart_type or 'candlestick',
                volume_display=volume_display or 'bars_ma',
                color_by_price=color_by_price
            )
            
            # Update chart title to include data range info
            if chart_subtitle:
                current_title = fig.layout.title.text if fig.layout.title else f"{symbol} Price Chart"
                fig.update_layout(
                    title={
                        'text': f"{current_title}<br><span style='font-size:12px;color:gray'>{chart_subtitle}</span>",
                        'x': 0.5,
                        'xanchor': 'center'
                    }
                )
            
            logger.info(f"Updated interactive chart for {symbol} with {len(chart_indicators)} indicators")
            return fig
            
        except Exception as e:
            logger.error(f"Error updating interactive chart: {e}")
            return chart_builder._create_empty_chart(f"Error loading chart: {str(e)}")
    
    @app.callback(
        Output("technical-analysis-summary", "children"),
        [
            Input("symbol-search", "value"),
            Input("indicators-dropdown", "value")
        ],
        prevent_initial_call=True
    )
    def update_technical_analysis_summary(symbol, indicators):
        """Update technical analysis summary."""
        try:
            if not symbol:
                symbol = "ADBE"
            
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
                ], width=2),  # Reduced from 3 to 2 to make room for volume
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("30D Change", className="text-muted mb-1"),
                            html.H5(f"{price_change:+.2f}%", 
                                   className="text-success" if price_change >= 0 else "text-danger")
                        ])
                    ])
                ], width=2),  # Reduced from 3 to 2 to make room for volume
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
                    ], width=2)  # Changed from 3 to 2 for consistency
                )
            
            # Add volume analysis
            if 'volume' in df.columns:
                current_volume = df['volume'].iloc[-1]
                avg_volume = df['volume'].rolling(window=20).mean().iloc[-1]
                volume_ratio = (current_volume / avg_volume) if avg_volume > 0 else 0
                
                # Format volume in millions/billions
                def format_volume(vol):
                    if vol >= 1e9:
                        return f"{vol/1e9:.1f}B"
                    elif vol >= 1e6:
                        return f"{vol/1e6:.1f}M"
                    elif vol >= 1e3:
                        return f"{vol/1e3:.1f}K"
                    else:
                        return f"{vol:.0f}"
                
                volume_color = "text-success" if volume_ratio > 1.5 else "text-warning" if volume_ratio > 0.8 else "text-muted"
                
                summary_items.append(
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H6("Volume", className="text-muted mb-1"),
                                html.H5(format_volume(current_volume), className=f"{volume_color} mb-0"),
                                html.Small(f"{volume_ratio:.1f}x avg", className="text-muted")
                            ])
                        ])
                    ], width=2)
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
                    ], width=2)
                )
            
            return dbc.Row(summary_items)
            
        except Exception as e:
            logger.error(f"Error updating technical analysis summary: {e}")
            return html.P(f"Error loading analysis: {str(e)}", className="text-danger text-center")
