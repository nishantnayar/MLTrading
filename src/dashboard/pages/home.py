import dash
from dash import html, dcc, callback_context, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logging_config import get_ui_logger, log_dashboard_event
from src.dashboard.services.data_service import get_data_service

# Initialize logger
logger = get_ui_logger("dashboard")

# Initialize data service
data_service = get_data_service()

# Get real market data
def get_market_stats(symbol='AAPL'):
    """Get real market statistics."""
    try:
        stats = data_service.get_dashboard_stats(symbol)
        return stats
    except Exception as e:
        logger.error(f"Failed to get market stats: {e}")
        return {
            'current_price': 0,
            'daily_change': 0,
            'daily_change_percent': 0,
            'total_volume': 0,
            'last_signal': 'N/A',
            'has_data': False
        }

def create_price_chart(symbol='AAPL'):
    """Create price chart with real data."""
    try:
        chart_data = data_service.get_chart_data(symbol, days=30)
        
        if not chart_data['has_data']:
            # Return empty chart if no data
            fig = go.Figure()
            fig.update_layout(
                title=f'No data available for {symbol}',
                xaxis_title='Date',
                yaxis_title='Price ($)',
                height=400
            )
            return fig
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=chart_data['dates'],
            y=chart_data['prices'],
            mode='lines',
            name=f'{symbol} Price',
            line=dict(color='#007bff')
        ))
        fig.update_layout(
            title=f'{symbol} Stock Price (30 Days)',
            xaxis_title='Date',
            yaxis_title='Price ($)',
            height=400,
            template='plotly_white'
        )
        return fig
    except Exception as e:
        logger.error(f"Failed to create price chart: {e}")
        fig = go.Figure()
        fig.update_layout(
            title='Error loading price data',
            xaxis_title='Date',
            yaxis_title='Price ($)',
            height=400
        )
        return fig

def create_volume_chart(symbol='AAPL'):
    """Create volume chart with real data."""
    try:
        chart_data = data_service.get_chart_data(symbol, days=30)
        
        if not chart_data['has_data']:
            # Return empty chart if no data
            fig = go.Figure()
            fig.update_layout(
                title=f'No data available for {symbol}',
                xaxis_title='Date',
                yaxis_title='Volume',
                height=300
            )
            return fig
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=chart_data['dates'],
            y=chart_data['volumes'],
            name=f'{symbol} Volume',
            marker_color='#17a2b8'
        ))
        fig.update_layout(
            title=f'{symbol} Trading Volume (30 Days)',
            xaxis_title='Date',
            yaxis_title='Volume',
            height=300,
            template='plotly_white'
        )
        return fig
    except Exception as e:
        logger.error(f"Failed to create volume chart: {e}")
        fig = go.Figure()
        fig.update_layout(
            title='Error loading volume data',
            xaxis_title='Date',
            yaxis_title='Volume',
            height=300
        )
        return fig

def get_recent_signals(symbol='AAPL'):
    """Get recent trading signals."""
    try:
        signals = data_service.get_recent_signals(symbol, days=7)
        return signals
    except Exception as e:
        logger.error(f"Failed to get recent signals: {e}")
        return []

def get_available_symbols():
    """Get list of available symbols from database."""
    try:
        symbols = data_service.get_available_symbols()
        return symbols
    except Exception as e:
        logger.error(f"Failed to get available symbols: {e}")
        return ['AAPL']  # Fallback to default

# Define the home page layout
layout = dbc.Container([
    # Symbol Selector
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Select Symbol", className="card-title"),
                    dcc.Dropdown(
                        id='symbol-dropdown',
                        options=[],
                        value='AAPL',
                        className="mb-3",
                        placeholder="Select a symbol..."
                    ),
                    dbc.Button("Refresh Data", id="refresh-data-btn", color="primary", size="sm")
                ])
            ], className="mb-3")
        ], width=12)
    ]),
    
    # Stats Cards
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Current Price", className="card-title"),
                    html.H2(id="current-price", className="text-primary")
                ])
            ], className="stats-card price-card")
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Daily Change", className="card-title"),
                    html.H2(id="daily-change", className="text-success")
                ])
            ], className="stats-card change-card")
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Total Volume", className="card-title"),
                    html.H2(id="total-volume", className="text-info")
                ])
            ], className="stats-card volume-card")
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Last Signal", className="card-title"),
                    html.H2(id="last-signal", className="text-warning")
                ])
            ], className="stats-card signal-card")
        ], width=3)
    ], className="mb-4 fade-in", id="stats-cards"),

    # Charts
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5("Price Chart", className="mb-0")),
                dbc.CardBody([
                    dcc.Graph(
                        id='price-chart'
                    )
                ])
            ], className="chart-card")
        ], width=8),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5("Volume Chart", className="mb-0")),
                dbc.CardBody([
                    dcc.Graph(
                        id='volume-chart'
                    )
                ])
            ], className="chart-card")
        ], width=4)
    ], className="mb-4 slide-in"),

    # Control Panel
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Trading Controls"),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Button("Start Trading", color="success", className="me-2"),
                            dbc.Button("Stop Trading", color="danger", className="me-2"),
                            dbc.Button("Refresh Data", color="info")
                        ])
                    ]),
                    html.Hr(),
                    dbc.Row([
                        dbc.Col([
                            html.Label("Risk Level:"),
                            dcc.Slider(
                                id='risk-slider',
                                min=1,
                                max=10,
                                step=1,
                                value=5,
                                marks={i: str(i) for i in range(1, 11)}
                            )
                        ])
                    ])
                ])
            ], className="control-panel")
        ], width=6),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Recent Signals"),
                dbc.CardBody([
                    html.Div(id="recent-signals")
                ])
            ], className="signals-card")
        ], width=6)
    ], className="fade-in")
], fluid=True)

# Callbacks for real-time data updates
def register_callbacks(app):
    """Register callbacks for the home page."""
    
    # Initial callback to populate symbol dropdown on page load
    @app.callback(
        [Output("symbol-dropdown", "options"),
         Output("symbol-dropdown", "value")],
        [Input("refresh-data-btn", "n_clicks")]
    )
    def update_symbol_options(refresh_clicks):
        """Update symbol dropdown options from database."""
        try:
            symbols = get_available_symbols()
            options = [{'label': symbol, 'value': symbol} for symbol in symbols]
            
            # Set default value to first available symbol
            default_value = symbols[0] if symbols else 'AAPL'
            
            logger.info(f"Updated symbol dropdown with {len(symbols)} symbols")
            return options, default_value
            
        except Exception as e:
            logger.error(f"Failed to update symbol options: {e}")
            # Return fallback options
            fallback_options = [{'label': 'AAPL', 'value': 'AAPL'}]
            return fallback_options, 'AAPL'
    
    # Combined callback for all dashboard updates (handles both initial load and updates)
    @app.callback(
        [Output("current-price", "children"),
         Output("daily-change", "children"),
         Output("total-volume", "children"),
         Output("last-signal", "children"),
         Output("daily-change", "className"),
         Output("price-chart", "figure"),
         Output("volume-chart", "figure"),
         Output("recent-signals", "children")],
        [Input("symbol-dropdown", "value"),
         Input("refresh-data-btn", "n_clicks")]
    )
    def update_dashboard(symbol, refresh_clicks):
        """Update all dashboard components."""
        try:
            # Get symbol (default to AAPL if None)
            current_symbol = symbol or 'AAPL'
            
            # Check if this is an initial load or an update
            ctx = callback_context
            if not ctx.triggered:
                logger.info(f"Initializing dashboard for symbol: {current_symbol}")
            else:
                logger.info(f"Updating dashboard for symbol: {current_symbol}")
            
            # Get market stats
            stats = get_market_stats(current_symbol)
            
            # Format stats
            if not stats['has_data']:
                current_price = "$0.00"
                daily_change = "$0.00"
                total_volume = "0"
                last_signal = "N/A"
                change_class = "text-muted"
            else:
                current_price = f"${stats['current_price']:.2f}"
                daily_change = f"{stats['daily_change']:+.2f}"
                change_class = "text-success" if stats['daily_change'] >= 0 else "text-danger"
                total_volume = f"{stats['total_volume']:,}"
                last_signal = stats['last_signal']
            
            # Create charts
            price_chart = create_price_chart(current_symbol)
            volume_chart = create_volume_chart(current_symbol)
            
            # Get recent signals
            signals = get_recent_signals(current_symbol)
            if not signals:
                recent_signals = html.Div("No recent signals available", className="text-muted")
            else:
                signal_items = []
                for signal in signals:
                    signal_class = "text-success" if signal['signal'] == 'BUY' else "text-danger" if signal['signal'] == 'SELL' else "text-warning"
                    signal_items.append(
                        html.Div([
                            html.Span(f"{signal['date']}: {signal['signal']} (${signal['price']:.2f})", 
                                     className=f"signal-item {signal_class}")
                        ], className="signal-item")
                    )
                recent_signals = signal_items
            
            logger.info(f"Successfully updated dashboard for {current_symbol}")
            return [current_price, daily_change, total_volume, last_signal, change_class, 
                   price_chart, volume_chart, recent_signals]
            
        except Exception as e:
            logger.error(f"Failed to update dashboard: {e}")
            # Return safe defaults
            error_chart = go.Figure()
            error_chart.update_layout(
                title='Error loading data',
                xaxis_title='Date',
                yaxis_title='Value',
                height=400
            )
            
            return ["$0.00", "$0.00", "0", "N/A", "text-muted", 
                   error_chart, error_chart, 
                   html.Div("Error loading data", className="text-danger")] 