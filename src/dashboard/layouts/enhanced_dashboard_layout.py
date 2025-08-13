"""
Enhanced dashboard layout with interactive chart features.
Integrates advanced charting, technical indicators, and interactive controls.
"""

import dash_bootstrap_components as dbc
from dash import html, dcc
import plotly.graph_objs as go

from .interactive_chart import create_chart_controls, create_indicator_info_panel
from ..config import CHART_COLORS, CARD_STYLE
from ...utils.logging_config import get_ui_logger

logger = get_ui_logger("enhanced_dashboard")


def create_enhanced_dashboard_content() -> html.Div:
    """Create enhanced dashboard with interactive charts and technical analysis."""
    
    return html.Div([
        # Chart Controls Section
        dbc.Row([
            dbc.Col([
                create_chart_controls()
            ], width=12)
        ], className="mb-4"),
        
        # Main Chart and Analysis Section
        dbc.Row([
            # Advanced Chart
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        dbc.Row([
                            dbc.Col([
                                html.H5("Advanced Technical Chart", className="mb-0")
                            ], width=8),
                            dbc.Col([
                                dbc.ButtonGroup([
                                    dbc.Button(
                                        "📊 Analysis", 
                                        id="analysis-btn", 
                                        size="sm", 
                                        color="primary",
                                        outline=True
                                    ),
                                    dbc.Button(
                                        "ℹ️ Indicators", 
                                        id="indicator-info-btn", 
                                        size="sm", 
                                        color="info",
                                        outline=True
                                    ),
                                    dbc.Button(
                                        "🎯 Levels", 
                                        id="calculate-levels-btn", 
                                        size="sm", 
                                        color="warning",
                                        outline=True
                                    )
                                ])
                            ], width=4, className="text-end")
                        ])
                    ]),
                    dbc.CardBody([
                        dcc.Loading([
                            dcc.Graph(
                                id="advanced-price-chart",
                                config={
                                    'displayModeBar': True,
                                    'displaylogo': False,
                                    'modeBarButtonsToAdd': [
                                        'drawline',
                                        'drawopenpath',
                                        'drawclosedpath',
                                        'drawcircle',
                                        'drawrect',
                                        'eraseshape'
                                    ],
                                    'modeBarButtonsToRemove': [
                                        'lasso2d',
                                        'select2d'
                                    ]
                                },
                                style={'height': '600px'}
                            )
                        ], type="default")
                    ])
                ], style=CARD_STYLE)
            ], width=9),
            
            # Chart Statistics and Quick Info
            dbc.Col([
                # Quick Statistics
                dbc.Card([
                    dbc.CardHeader([
                        html.H6("Quick Stats", className="mb-0")
                    ]),
                    dbc.CardBody([
                        html.Div(id="chart-statistics")
                    ])
                ], className="mb-3", style=CARD_STYLE),
                
                # Market Overview Cards
                create_market_overview_cards(),
                
                # Support/Resistance Levels
                dbc.Card([
                    dbc.CardHeader([
                        html.H6("Key Levels", className="mb-0")
                    ]),
                    dbc.CardBody([
                        html.Div(id="support-resistance-display")
                    ])
                ], className="mb-3", style=CARD_STYLE),
                
                # Trading Signals
                create_trading_signals_card()
                
            ], width=3)
        ], className="mb-4"),
        
        # Secondary Charts Row
        dbc.Row([
            # Volume Analysis
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H6("Volume Analysis", className="mb-0")
                    ]),
                    dbc.CardBody([
                        dcc.Loading([
                            dcc.Graph(
                                id="volume-analysis-chart",
                                style={'height': '300px'}
                            )
                        ], type="default")
                    ])
                ], style=CARD_STYLE)
            ], width=6),
            
            # Price Distribution
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.H6("Price Distribution", className="mb-0")
                    ]),
                    dbc.CardBody([
                        dcc.Loading([
                            dcc.Graph(
                                id="price-distribution-chart",
                                style={'height': '300px'}
                            )
                        ], type="default")
                    ])
                ], style=CARD_STYLE)
            ], width=6)
        ], className="mb-4"),
        
        # Indicator Information Panel (Collapsible)
        dbc.Row([
            dbc.Col([
                create_indicator_info_panel()
            ], width=12)
        ], className="mb-4"),
        
        # Hidden data stores
        dcc.Store(id="support-levels-store"),
        dcc.Store(id="resistance-levels-store"),
        dcc.Store(id="chart-annotations-store"),
        
        # Analysis Modal
        create_analysis_modal(),
        
        # Drawing Tools Modal
        create_drawing_tools_modal()
        
    ])


def create_market_overview_cards() -> html.Div:
    """Create market overview cards."""
    return html.Div([
        dbc.Card([
            dbc.CardBody([
                html.H6("📈 Trend", className="text-success"),
                html.P("Bullish", className="mb-0", id="trend-indicator")
            ])
        ], className="mb-2 text-center", style=CARD_STYLE),
        
        dbc.Card([
            dbc.CardBody([
                html.H6("🎯 Signal", className="text-primary"),
                html.P("Buy", className="mb-0", id="signal-indicator")
            ])
        ], className="mb-2 text-center", style=CARD_STYLE),
        
        dbc.Card([
            dbc.CardBody([
                html.H6("📊 Strength", className="text-warning"),
                html.P("Strong", className="mb-0", id="strength-indicator")
            ])
        ], className="mb-2 text-center", style=CARD_STYLE)
    ])


def create_trading_signals_card() -> dbc.Card:
    """Create trading signals card."""
    return dbc.Card([
        dbc.CardHeader([
            html.H6("Trading Signals", className="mb-0")
        ]),
        dbc.CardBody([
            html.Div(id="trading-signals-list", children=[
                dbc.Alert([
                    html.Strong("RSI Oversold"),
                    html.Br(),
                    html.Small("RSI below 30 - potential buy signal", className="text-muted")
                ], color="success", className="mb-2"),
                
                dbc.Alert([
                    html.Strong("MACD Bullish Cross"),
                    html.Br(),
                    html.Small("MACD line crossed above signal", className="text-muted")
                ], color="info", className="mb-2"),
                
                dbc.Alert([
                    html.Strong("Volume Surge"),
                    html.Br(),
                    html.Small("Volume 150% above average", className="text-muted")
                ], color="warning", className="mb-0")
            ])
        ])
    ], style=CARD_STYLE)


def create_analysis_modal() -> dbc.Modal:
    """Create comprehensive analysis modal."""
    return dbc.Modal([
        dbc.ModalHeader([
            dbc.ModalTitle("📊 Comprehensive Technical Analysis")
        ]),
        dbc.ModalBody([
            dcc.Loading([
                html.Div(id="chart-analysis-content")
            ], type="default")
        ]),
        dbc.ModalFooter([
            dbc.Button(
                "Close", 
                id="close-analysis-modal", 
                className="ms-auto",
                color="secondary"
            )
        ])
    ], id="chart-analysis-modal", size="lg")


def create_drawing_tools_modal() -> dbc.Modal:
    """Create drawing tools configuration modal."""
    return dbc.Modal([
        dbc.ModalHeader([
            dbc.ModalTitle("🎨 Drawing Tools")
        ]),
        dbc.ModalBody([
            dbc.Row([
                dbc.Col([
                    html.H6("Line Tools"),
                    dbc.ButtonGroup([
                        dbc.Button("Trend Line", size="sm", outline=True),
                        dbc.Button("Horizontal Line", size="sm", outline=True),
                        dbc.Button("Vertical Line", size="sm", outline=True)
                    ], vertical=True, className="mb-3")
                ], width=6),
                
                dbc.Col([
                    html.H6("Shape Tools"),
                    dbc.ButtonGroup([
                        dbc.Button("Rectangle", size="sm", outline=True),
                        dbc.Button("Circle", size="sm", outline=True),
                        dbc.Button("Triangle", size="sm", outline=True)
                    ], vertical=True, className="mb-3")
                ], width=6)
            ]),
            
            dbc.Row([
                dbc.Col([
                    html.H6("Fibonacci Tools"),
                    dbc.ButtonGroup([
                        dbc.Button("Fib Retracement", size="sm", outline=True),
                        dbc.Button("Fib Extension", size="sm", outline=True),
                        dbc.Button("Fib Fan", size="sm", outline=True)
                    ], vertical=True)
                ], width=6),
                
                dbc.Col([
                    html.H6("Annotation Tools"),
                    dbc.ButtonGroup([
                        dbc.Button("Text Box", size="sm", outline=True),
                        dbc.Button("Arrow", size="sm", outline=True),
                        dbc.Button("Price Alert", size="sm", outline=True)
                    ], vertical=True)
                ], width=6)
            ])
        ]),
        dbc.ModalFooter([
            dbc.Button("Clear All", color="danger", outline=True, className="me-2"),
            dbc.Button("Apply", color="primary", className="me-2"),
            dbc.Button("Close", id="close-drawing-modal", color="secondary")
        ])
    ], id="drawing-tools-modal")


def create_zoom_controls() -> html.Div:
    """Create advanced zoom and pan controls."""
    return html.Div([
        dbc.ButtonGroup([
            dbc.Button("🔍 Zoom In", id="zoom-in-btn", size="sm", outline=True),
            dbc.Button("🔍 Zoom Out", id="zoom-out-btn", size="sm", outline=True),
            dbc.Button("↔️ Pan", id="pan-btn", size="sm", outline=True),
            dbc.Button("🎯 Auto Scale", id="auto-scale-btn", size="sm", outline=True),
            dbc.Button("🔄 Reset", id="reset-zoom-btn", size="sm", outline=True)
        ]),
        
        html.Hr(),
        
        # Time Range Quick Selectors
        html.H6("Quick Time Ranges:", className="mt-3 mb-2"),
        dbc.ButtonGroup([
            dbc.Button("1D", id="range-1d-btn", size="sm", outline=True),
            dbc.Button("1W", id="range-1w-btn", size="sm", outline=True),
            dbc.Button("1M", id="range-1m-btn", size="sm", outline=True),
            dbc.Button("3M", id="range-3m-btn", size="sm", outline=True),
            dbc.Button("1Y", id="range-1y-btn", size="sm", outline=True),
            dbc.Button("ALL", id="range-all-btn", size="sm", outline=True)
        ], className="mb-3"),
        
        # Chart Type Selector
        html.H6("Chart Type:", className="mb-2"),
        dcc.RadioItems(
            id="chart-type-radio",
            options=[
                {'label': '📊 Candlestick', 'value': 'candlestick'},
                {'label': '📈 OHLC', 'value': 'ohlc'},
                {'label': '📉 Line', 'value': 'line'}
            ],
            value='candlestick',
            className="mb-3"
        )
    ])


def create_real_time_data_panel() -> dbc.Card:
    """Create real-time data update panel."""
    return dbc.Card([
        dbc.CardHeader([
            dbc.Row([
                dbc.Col([
                    html.H6("Real-Time Data", className="mb-0")
                ], width=8),
                dbc.Col([
                    dbc.Switch(
                        id="real-time-toggle",
                        label="Live",
                        value=False,
                        className="text-end"
                    )
                ], width=4)
            ])
        ]),
        dbc.CardBody([
            html.Div([
                dbc.Row([
                    dbc.Col([
                        html.Small("Last Update:", className="text-muted"),
                        html.Div("--:--:--", id="last-update-time")
                    ], width=6),
                    dbc.Col([
                        html.Small("Data Source:", className="text-muted"),
                        html.Div("Yahoo Finance", id="data-source")
                    ], width=6)
                ]),
                dbc.Row([
                    dbc.Col([
                        html.Small("Refresh Rate:", className="text-muted"),
                        dcc.Dropdown(
                            id="refresh-rate-dropdown",
                            options=[
                                {'label': '5 seconds', 'value': 5},
                                {'label': '15 seconds', 'value': 15},
                                {'label': '30 seconds', 'value': 30},
                                {'label': '1 minute', 'value': 60}
                            ],
                            value=30,
                            clearable=False,
                            style={'fontSize': '12px'}
                        )
                    ], width=12)
                ], className="mt-2")
            ])
        ])
    ], style=CARD_STYLE)


# Interval component for real-time updates
def create_real_time_interval() -> dcc.Interval:
    """Create interval component for real-time chart updates."""
    return dcc.Interval(
        id="real-time-interval",
        interval=30*1000,  # 30 seconds
        n_intervals=0,
        disabled=True  # Disabled by default
    )