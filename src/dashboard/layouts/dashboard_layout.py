"""
Dashboard layout creation functions.
Contains the main dashboard content and tab structure.
"""

import dash_bootstrap_components as dbc
from dash import html, dcc

from ..config import (
    DEFAULT_CHART_HEIGHT, 
    DEFAULT_TIME_RANGE, 
    DEFAULT_SYMBOL,
    TIME_RANGE_OPTIONS,
    CARD_STYLE,
    CARD_STYLE_NONE
)


def create_chart_card(chart_id, height=DEFAULT_CHART_HEIGHT):
    """Create a card container for charts"""
    return dbc.Card([
        dbc.CardBody([
            dcc.Graph(id=chart_id, style={'height': height})
        ], className="p-0")
    ], style=CARD_STYLE_NONE)


def create_overview_tab():
    """Create the overview tab content"""
    return dbc.Tab(
        dbc.Card([
            dbc.CardBody([
                html.H1("About", className="mb-4"),
                
                # Current Time and Market Status
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H6("Current Time", className="text-muted mb-2"),
                                html.H4(id="current-time", className="text-primary mb-0")
                            ])
                        ], style=CARD_STYLE)
                    ], width=4),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H6("Next Market Open", className="text-muted mb-2"),
                                html.H4(id="next-market-open", className="text-success mb-0")
                            ])
                        ], style=CARD_STYLE)
                    ], width=4),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H6("Next Market Close", className="text-muted mb-2"),
                                html.H4(id="next-market-close", className="text-info mb-0")
                            ])
                        ], style=CARD_STYLE)
                    ], width=4)
                ], className="mb-4"),
                
                # Database Statistics
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H6("Total Symbols in Database", className="text-muted mb-2"),
                                html.H4(id="total-symbols-db", className="text-primary mb-0")
                            ])
                        ], style=CARD_STYLE)
                    ], width=6),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H6("Data Range", className="text-muted mb-2"),
                                html.H4(id="data-range", className="text-info mb-0")
                            ])
                        ], style=CARD_STYLE)
                    ], width=6)
                ], className="mb-4")
            ], className="p-4")
        ], style=CARD_STYLE_NONE),
        label="Overview",
        tab_id="overview-tab"
    )


def create_charts_tab():
    """Create the charts tab content with interactive charts"""
    return dbc.Tab(
        dbc.Card([
            dbc.CardBody([
                # Refresh Button Row
                dbc.Row([
                    dbc.Col([
                        dbc.Button(
                            "Refresh Statistics",
                            id="refresh-stats-btn",
                            color="primary",
                            className="w-100"
                        )
                    ], width=12)
                ], className="mb-3"),
                
                # Distribution Charts Row (at top to drive symbol selection)
                dbc.Row([
                    dbc.Col([
                        html.H5("Sector Distribution", className="text-center mb-2"),
                        create_chart_card("sector-chart", "300px")
                    ], width=6),
                    dbc.Col([
                        html.H5("Industry Distribution", className="text-center mb-2"),
                        create_chart_card("industry-chart", "300px")
                    ], width=6)
                ], className="mb-3"),
                
                # Filter Display Row
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.Div([
                                    html.H6("Current Selection", className="text-muted mb-2"),
                                    html.Div([
                                        html.Span("Sector: ", className="text-muted me-1"),
                                        html.Span("All Sectors", id="current-sector-filter", className="badge bg-primary me-3"),
                                        html.Span("Industry: ", className="text-muted me-1"),
                                        html.Span("All Industries", id="current-industry-filter", className="badge bg-info")
                                    ], className="d-flex align-items-center justify-content-center")
                                ], className="text-center")
                            ], className="py-2")
                        ], style=CARD_STYLE_NONE)
                    ], width=12)
                ], className="mb-4"),
                
                # Interactive Chart Controls Row
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H3("Interactive Chart Controls", className="text-center mb-3"),
                                dbc.Row([
                                    # Symbol Selection
                                    dbc.Col([
                                        html.Label("Select Symbol:", className="text-primary-emphasis mb-1"),
                                        dcc.Dropdown(
                                            id="symbol-dropdown",
                                            options=[],
                                            value=DEFAULT_SYMBOL,
                                            className="mb-2"
                                        )
                                    ], width=4),
                                    
                                    # Chart Type
                                    dbc.Col([
                                        html.Label("Chart Type:", className="text-primary-emphasis mb-1"),
                                        dcc.Dropdown(
                                            id="chart-type-dropdown",
                                            options=[
                                                {"label": "Candlestick", "value": "candlestick"},
                                                {"label": "OHLC", "value": "ohlc"},
                                                {"label": "Line", "value": "line"}
                                            ],
                                            value="candlestick",
                                            className="mb-2"
                                        )
                                    ], width=2),
                                    
                                    # Technical Indicators
                                    dbc.Col([
                                        html.Label("Indicators:", className="text-primary-emphasis mb-1"),
                                        dcc.Dropdown(
                                            id="indicators-dropdown",
                                            options=[
                                                {"label": "SMA (20)", "value": "sma"},
                                                {"label": "EMA (12,26)", "value": "ema"},
                                                {"label": "Bollinger Bands", "value": "bollinger"},
                                                {"label": "RSI", "value": "rsi"},
                                                {"label": "MACD", "value": "macd"},
                                                {"label": "Stochastic", "value": "stochastic"},
                                                {"label": "VWAP", "value": "vwap"},
                                                {"label": "ATR", "value": "atr"}
                                            ],
                                            value=["sma", "rsi"],
                                            multi=True,
                                            className="mb-2"
                                        )
                                    ], width=3),
                                    
                                    # Volume Toggle & Controls
                                    dbc.Col([
                                        html.Label("Volume Display:", className="text-primary-emphasis mb-1"),
                                        dcc.Dropdown(
                                            id="volume-display-dropdown",
                                            options=[
                                                {"label": "Hide Volume", "value": "none"},
                                                {"label": "Volume Bars", "value": "bars"},
                                                {"label": "Volume + MA", "value": "bars_ma"},
                                                {"label": "Volume Profile", "value": "profile"}
                                            ],
                                            value="bars_ma",
                                            className="mb-2"
                                        ),
                                        dbc.Checklist(
                                            options=[{"label": "Color by Price", "value": "color_price"}],
                                            value=["color_price"],
                                            id="volume-color-checkbox",
                                            inline=True,
                                            className="mb-1"
                                        )
                                    ], width=2),
                                    
                                    # Refresh Button
                                    dbc.Col([
                                        html.Label("", className="text-primary-emphasis mb-1"),  # Spacer
                                        dbc.Button("Refresh", id="refresh-chart-btn", color="primary", size="sm", className="w-100")
                                    ], width=1)
                                ], className="align-items-end")
                            ], className="p-3")
                        ], style=CARD_STYLE_NONE)
                    ], width=12)
                ], className="mb-3"),
                
                # Technical Analysis Summary Row (moved above chart for better space utilization)
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader([
                                html.H5("Technical Analysis Summary", className="mb-0"),
                                dbc.Button("View Detailed Analysis", id="analysis-modal-btn", color="outline-primary", size="sm")
                            ], className="d-flex justify-content-between align-items-center"),
                            dbc.CardBody([
                                html.Div(id="technical-analysis-summary", children=[
                                    html.P("Select a symbol to view technical analysis.", className="text-muted text-center")
                                ], className="py-2")  # Reduced padding for more compact layout
                            ])
                        ], style=CARD_STYLE_NONE)
                    ], width=12)
                ], className="mb-2"),  # Reduced margin for more chart space
                
                # Main Interactive Chart Row (now gets maximum available space)
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                dcc.Graph(
                                    id="interactive-price-chart",
                                    style={'height': '700px'},  # Increased height since we have more space
                                    config={
                                        'displayModeBar': True,
                                        'displaylogo': False,
                                        'modeBarButtonsToRemove': ['lasso2d', 'select2d'],
                                        'toImageButtonOptions': {
                                            'format': 'png',
                                            'filename': 'chart',
                                            'height': 700,  # Updated to match new height
                                            'width': 1200,
                                            'scale': 1
                                        }
                                    }
                                )
                            ], className="p-1")
                        ], style=CARD_STYLE_NONE)
                    ], width=12)
                ], className="mb-3")
            ], className="p-0")
        ], style=CARD_STYLE_NONE),
        label="Interactive Charts",
        tab_id="charts-tab"
    )


def create_analysis_tab():
    """Create the analysis tab content"""
    return dbc.Tab(
        dbc.Card([
            dbc.CardHeader("Analysis", className="text-center p-2"),
            dbc.CardBody([
                html.Div([
                    html.H5("Trading Analysis", className="text-center mb-3"),
                    html.P("Advanced trading analysis and insights will be displayed here.", className="text-center text-muted")
                ], className="p-4")
            ], className="p-0")
        ], style=CARD_STYLE_NONE),
        label="Analysis",
        tab_id="analysis-tab"
    )


def create_settings_tab():
    """Create the settings tab content"""
    return dbc.Tab(
        dbc.Card([
            dbc.CardHeader("Settings", className="text-center p-2"),
            dbc.CardBody([
                html.Div([
                    html.H5("Dashboard Settings", className="text-center mb-3"),
                    html.P("Configure your dashboard preferences and trading parameters.", className="text-center text-muted")
                ], className="p-4")
            ], className="p-0")
        ], style=CARD_STYLE_NONE),
        label="Settings",
        tab_id="settings-tab"
    )


def create_dashboard_content():
    """Create the main dashboard content with tabs"""
    return dbc.Tabs([
        create_overview_tab(),
        create_charts_tab(), 
        create_analysis_tab(),
        create_settings_tab()
    ], id="dashboard-tabs", active_tab="overview-tab")