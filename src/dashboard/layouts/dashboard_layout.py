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
from ..components.shared_components import (
    create_chart_card,
    create_metric_card,
    create_section_header,
    create_control_group,
    create_button_group
)




def create_overview_tab():
    """Create the overview tab content"""
    return dbc.Tab(
        dbc.Card([
            dbc.CardBody([
                # Hero Section with Professional Background
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.Div([
                                    # Background image using CSS
                                    html.Div([
                                        html.Div([
                                            html.H1([
                                                html.I(className="fas fa-chart-line me-3"),
                                                "ML Trading Dashboard"
                                            ], className="display-4 text-white fw-bold mb-3"),
                                            html.P("Advanced market analysis and stock filtering platform powered by machine learning",
                                                   className="lead text-white-50 mb-4"),
                                            html.Div([
                                                dbc.Badge("Live Data", color="success", className="me-2"),
                                                dbc.Badge("Real-time Analysis", color="info", className="me-2"),
                                                dbc.Badge("Smart Filtering", color="primary")
                                            ])
                                        ], className="hero-content p-4")
                                    ], className="hero-section", style={
                                        "background": "linear-gradient(135deg, #1e3c72 0%, #2a5298 100%)",
                                        "background-image": "url('data:image/svg+xml,<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 1000 200\"><polygon fill=\"%23ffffff08\" points=\"0,100 50,120 100,80 150,110 200,90 250,130 300,100 350,140 400,120 450,90 500,110 550,80 600,120 650,100 700,130 750,110 800,90 850,120 900,100 950,130 1000,110 1000,200 0,200\"/></svg>')",
                                        "background-size": "cover",
                                        "background-position": "center",
                                        "border-radius": "12px",
                                        "min-height": "200px",
                                        "display": "flex",
                                        "align-items": "center"
                                    })
                                ])
                            ], className="p-0")
                        ], style={**CARD_STYLE, "overflow": "hidden"})
                    ], width=12)
                ], className="mb-4"),
                
                # Market Status Cards
                dbc.Row([
                    dbc.Col([
                        create_metric_card(
                            title="Current Time",
                            value="",
                            value_id="current-time",
                            card_style=CARD_STYLE,
                            enhanced=True
                        )
                    ], width=3),
                    dbc.Col([
                        create_metric_card(
                            title="Next Market Open",
                            value="",
                            value_id="next-market-open",
                            color_class="text-success",
                            card_style=CARD_STYLE,
                            enhanced=True
                        )
                    ], width=3),
                    dbc.Col([
                        create_metric_card(
                            title="Next Market Close",
                            value="",
                            value_id="next-market-close",
                            color_class="text-info",
                            card_style=CARD_STYLE,
                            enhanced=True
                        )
                    ], width=3),
                    dbc.Col([
                        create_metric_card(
                            title="Total Symbols",
                            value="",
                            value_id="total-symbols-db",
                            card_style=CARD_STYLE,
                            enhanced=True
                        )
                    ], width=3)
                ], className="mb-4"),
                
                # Advanced Filtering Controls
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader([
                                html.H5([
                                    html.I(className="fas fa-sliders-h me-2"),
                                    "Advanced Filters"
                                ], className="mb-0")
                            ]),
                            dbc.CardBody([
                                dbc.Row([
                                    dbc.Col([
                                        html.Label("Time Period:", className="form-label small"),
                                        dcc.Dropdown(
                                            id="time-period-filter",
                                            options=[
                                                {"label": "Last 7 Days", "value": 7},
                                                {"label": "Last 30 Days", "value": 30},
                                                {"label": "Last 90 Days", "value": 90}
                                            ],
                                            value=7,
                                            clearable=False,
                                            className="mb-2"
                                        )
                                    ], width=3),
                                    dbc.Col([
                                        html.Label("Volume Range:", className="form-label small"),
                                        dcc.RangeSlider(
                                            id="volume-range-filter",
                                            min=0,
                                            max=100,
                                            value=[10, 90],
                                            marks={0: "Low", 50: "Medium", 100: "High"},
                                            tooltip={"placement": "bottom", "always_visible": False}
                                        )
                                    ], width=3),
                                    dbc.Col([
                                        html.Label("Market Cap:", className="form-label small"),
                                        dcc.Dropdown(
                                            id="market-cap-filter",
                                            options=[
                                                {"label": "All Caps", "value": "all"},
                                                {"label": "Large Cap (>$10B)", "value": "large"},
                                                {"label": "Mid Cap ($2B-$10B)", "value": "mid"},
                                                {"label": "Small Cap (<$2B)", "value": "small"}
                                            ],
                                            value="all",
                                            clearable=False,
                                            className="mb-2"
                                        )
                                    ], width=3),
                                    dbc.Col([
                                        html.Label("Actions:", className="form-label small"),
                                        html.Div([
                                            dbc.Button("Apply Filters", id="apply-filters-btn", color="primary", size="sm", className="me-2"),
                                            dbc.Button("Reset", id="reset-filters-btn", color="outline-secondary", size="sm")
                                        ])
                                    ], width=3)
                                ])
                            ])
                        ], style=CARD_STYLE)
                    ], width=12)
                ], className="mb-4"),
                
                # Stock Filtering Charts Section
                dbc.Row([
                    dbc.Col([
                        create_section_header(
                            "Market Analytics Dashboard", 
                            subtitle="Interactive charts for discovering and filtering stocks",
                            icon_class="fas fa-chart-bar"
                        )
                    ], width=12)
                ], className="mb-3"),
                
                # First Row: Sector and Industry Charts
                dbc.Row([
                    # Sector Distribution Chart
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader([
                                html.H5([
                                    html.I(className="fas fa-industry me-2"),
                                    "Sector Distribution"
                                ], className="mb-0")
                            ]),
                            dbc.CardBody([
                                dcc.Graph(
                                    id="sector-distribution-chart", 
                                    style={'height': '400px'},
                                    config={
                                        'displayModeBar': False, 
                                        'staticPlot': False,
                                        'doubleClick': False,
                                        'showTips': False,
                                        'displaylogo': False,
                                        'modeBarButtonsToRemove': ['select2d', 'lasso2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d']
                                    }
                                )
                            ], className="p-0")
                        ], style=CARD_STYLE)
                    ], width=6),
                    
                    # Industry Distribution Chart (driven by sector)
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader([
                                html.H5([
                                    html.I(className="fas fa-building me-2"),
                                    html.Span("Industries", id="industry-title-base"),
                                    dbc.Badge(
                                        id="selected-sector-badge",
                                        children="",
                                        color="primary",
                                        pill=True,
                                        className="ms-2",
                                        style={"display": "none", "font-size": "0.7em"}
                                    )
                                ], className="mb-0")
                            ]),
                            dbc.CardBody([
                                dcc.Graph(
                                    id="industry-distribution-chart", 
                                    style={'height': '400px'},
                                    config={'displayModeBar': False, 'staticPlot': False}
                                )
                            ], className="p-0")
                        ], style=CARD_STYLE)
                    ], width=6)
                ], className="mb-4"),
                
                # Second Row: Volume, Performance, and Activity Charts
                dbc.Row([
                    # Top Symbols by Volume Chart  
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader([
                                html.H5([
                                    html.I(className="fas fa-chart-bar me-2"),
                                    "Top Symbols by Volume"
                                ], className="mb-0")
                            ]),
                            dbc.CardBody([
                                dcc.Graph(
                                    id="top-volume-chart", 
                                    style={'height': '400px'},
                                    config={'displayModeBar': False, 'staticPlot': False}
                                )
                            ], className="p-0")
                        ], style=CARD_STYLE)
                    ], width=4),
                    
                    # Price Performance Chart
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader([
                                html.H5([
                                    html.I(className="fas fa-trending-up me-2"),
                                    "Price Performance (7-Day)"
                                ], className="mb-0")
                            ]),
                            dbc.CardBody([
                                dcc.Graph(
                                    id="price-performance-chart", 
                                    style={'height': '400px'},
                                    config={'displayModeBar': False, 'staticPlot': False}
                                )
                            ], className="p-0")
                        ], style=CARD_STYLE)
                    ], width=4),
                    
                    # Market Activity Chart
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader([
                                html.H5([
                                    html.I(className="fas fa-chart-line me-2"),
                                    "Market Activity Summary"
                                ], className="mb-0")
                            ]),
                            dbc.CardBody([
                                dcc.Graph(
                                    id="market-activity-chart", 
                                    style={'height': '400px'},
                                    config={'displayModeBar': False, 'staticPlot': False}
                                )
                            ], className="p-0")
                        ], style=CARD_STYLE)
                    ], width=4)
                ], className="mb-4"),
                
                # Enhanced Filtered Symbols Section
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader([
                                html.Div([
                                    html.H5([
                                        html.I(className="fas fa-stars me-2"),
                                        "Discovered Symbols",
                                        dbc.Badge("", id="filter-status-badge", color="success", pill=True, className="ms-2", style={"display": "none"})
                                    ], className="mb-0"),
                                    html.Div([
                                        dbc.Button([
                                            html.I(className="fas fa-download me-1"),
                                            "Export List"
                                        ], id="export-symbols-btn", color="outline-primary", size="sm", className="me-2"),
                                        dbc.Button([
                                            html.I(className="fas fa-heart me-1"),
                                            "Save Watchlist"
                                        ], id="save-watchlist-btn", color="outline-success", size="sm")
                                    ])
                                ], className="d-flex justify-content-between align-items-center")
                            ]),
                            dbc.CardBody([
                                html.Div(id="filtered-symbols-display", children=[
                                    html.Div([
                                        html.I(className="fas fa-mouse-pointer fa-2x text-muted mb-3"),
                                        html.H6("Interactive Stock Discovery", className="text-muted"),
                                        html.P("Click on any bar in the charts above to discover stocks by sector, industry, volume, or performance.", 
                                               className="text-muted"),
                                        html.Small("💡 Tip: Start by clicking on a sector to see related industries", className="text-info")
                                    ], className="text-center py-4")
                                ])
                            ])
                        ], style=CARD_STYLE)
                    ], width=12)
                ], className="mb-4"),
                
                # Quick Stats Footer
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                dbc.Row([
                                    dbc.Col([
                                        html.Div([
                                            html.I(className="fas fa-database text-primary me-2"),
                                            html.Strong("Data Range: "),
                                            html.Span(id="data-range", children="Loading...")
                                        ])
                                    ], width=6),
                                    dbc.Col([
                                        html.Div([
                                            html.I(className="fas fa-clock text-info me-2"),
                                            html.Strong("Last Updated: "),
                                            html.Span(id="last-updated", children="Just now")
                                        ])
                                    ], width=6)
                                ])
                            ], className="py-2")
                        ], style=CARD_STYLE, className="border-0 bg-light")
                    ], width=12)
                ], className="mb-3"),
                
                # Refresh Button for Charts
                dbc.Row([
                    dbc.Col([
                        dbc.Button(
                            [html.I(className="fas fa-sync-alt me-2"), "Refresh Overview Charts"],
                            id="refresh-overview-btn",
                            color="primary",
                            size="sm",
                            className="hover-lift"
                        )
                    ], width="auto", className="ms-auto")
                ], className="mb-3")
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
                            [html.I(className="fas fa-sync-alt me-2"), "Refresh Statistics"],
                            id="refresh-stats-btn",
                            color="primary",
                            size="sm",
                            className="hover-lift"
                        )
                    ], width="auto", className="ms-auto")
                ], className="mb-3 justify-content-end"),
                
                # Technical Analysis Header
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.Div([
                                    html.H3([
                                        html.I(className="fas fa-chart-line me-2 text-primary"),
                                        "Technical Analysis Dashboard"
                                    ], className="text-center mb-2"),
                                    html.P("Complete market data and technical indicators for any symbol", 
                                           className="text-center text-muted mb-0")
                                ], className="text-center")
                            ], className="py-3")
                        ], style=CARD_STYLE)
                    ], width=12)
                ], className="mb-4"),
                
                # Interactive Chart Controls Row
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                create_section_header(
                                    "Chart Controls", 
                                    subtitle="Customize your technical analysis view",
                                    icon_class="fas fa-sliders-h"
                                ),
                                # Simplified Controls with Symbol Type-ahead
                                dbc.Row([
                                    # Symbol Type-ahead
                                    dbc.Col([
                                        html.Label("Search Symbol:", className="text-primary-emphasis mb-1"),
                                        dcc.Dropdown(
                                            id="symbol-search",
                                            options=[],
                                            value="ADBE",
                                            placeholder="Type to search symbols (e.g., ADBE, AAPL, TSLA)",
                                            searchable=True,
                                            clearable=False,
                                            className="mb-2"
                                        )
                                    ], width=3),
                                    
                                    # Chart Type  
                                    dbc.Col([
                                        html.Label("Chart Type:", className="text-primary-emphasis mb-1"),
                                        dcc.Dropdown(
                                            id="chart-type-dropdown",
                                            options=[
                                                {"label": "Candlestick", "value": "candlestick"},
                                                {"label": "OHLC", "value": "ohlc"},
                                                {"label": "Line", "value": "line"},
                                                {"label": "Bar", "value": "bar"}
                                            ],
                                            value="candlestick",
                                            className="mb-2"
                                        )
                                    ], width=2),
                                    
                                    # Technical Indicators
                                    dbc.Col([
                                        html.Label("Technical Indicators:", className="text-primary-emphasis mb-1"),
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
                                    
                                    # Volume Controls
                                    dbc.Col([
                                        html.Label("Volume:", className="text-primary-emphasis mb-1"),
                                        dcc.Dropdown(
                                            id="volume-display-dropdown",
                                            options=[
                                                {"label": "Hide", "value": "none"},
                                                {"label": "Bars", "value": "bars"},
                                                {"label": "Bars + MA", "value": "bars_ma"},
                                                {"label": "Profile", "value": "profile"}
                                            ],
                                            value="bars_ma",
                                            className="mb-2"
                                        )
                                    ], width=2),
                                    
                                    # Data Status & Refresh
                                    dbc.Col([
                                        html.Div([
                                            dbc.Button([
                                                html.I(className="fas fa-sync-alt me-1"),
                                                "Refresh"
                                            ], id="refresh-chart-btn", color="outline-primary", size="sm")
                                        ], className="d-flex align-items-end justify-content-end")
                                    ], width=2)
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
                                create_section_header(
                                    "Technical Analysis Summary",
                                    icon_class="fas fa-chart-line"
                                ),
                                dbc.Button(
                                    [html.I(className="fas fa-external-link-alt me-2"), "View Detailed Analysis"], 
                                    id="analysis-modal-btn", 
                                    color="outline-primary", 
                                    size="sm",
                                    className="hover-lift"
                                )
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


def create_comparison_tab():
    """Create the symbol comparison tab content"""
    return dbc.Tab(
        dbc.Card([
            dbc.CardBody([
                # Comparison Header
                dbc.Row([
                    dbc.Col([
                        html.H3([
                            html.I(className="fas fa-balance-scale me-3"),
                            "Symbol Comparison"
                        ], className="mb-3"),
                        html.P("Compare multiple symbols side-by-side with detailed metrics and charts", 
                               className="text-muted mb-4")
                    ], width=12)
                ]),
                
                # Symbol Selection Panel
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardHeader([
                                html.H5([
                                    html.I(className="fas fa-plus-circle me-2"),
                                    "Select Symbols to Compare"
                                ], className="mb-0")
                            ]),
                            dbc.CardBody([
                                dbc.Row([
                                    dbc.Col([
                                        html.Label("Symbol 1:", className="form-label"),
                                        dcc.Dropdown(
                                            id="comparison-symbol-1",
                                            placeholder="Select first symbol...",
                                            className="mb-3"
                                        )
                                    ], width=3),
                                    dbc.Col([
                                        html.Label("Symbol 2:", className="form-label"),
                                        dcc.Dropdown(
                                            id="comparison-symbol-2",
                                            placeholder="Select second symbol...",
                                            className="mb-3"
                                        )
                                    ], width=3),
                                    dbc.Col([
                                        html.Label("Symbol 3 (Optional):", className="form-label"),
                                        dcc.Dropdown(
                                            id="comparison-symbol-3",
                                            placeholder="Select third symbol...",
                                            className="mb-3"
                                        )
                                    ], width=3),
                                    dbc.Col([
                                        html.Label("Actions:", className="form-label"),
                                        html.Div([
                                            dbc.Button("Compare", id="compare-symbols-btn", color="primary", className="me-2"),
                                            dbc.Button("Clear", id="clear-comparison-btn", color="outline-secondary")
                                        ])
                                    ], width=3)
                                ])
                            ])
                        ], style=CARD_STYLE)
                    ], width=12)
                ], className="mb-4"),
                
                # Comparison Results
                html.Div(id="comparison-results", children=[
                    html.Div([
                        html.I(className="fas fa-chart-bar fa-3x text-muted mb-3"),
                        html.H5("Ready to Compare", className="text-muted"),
                        html.P("Select 2-3 symbols above and click 'Compare' to see detailed side-by-side analysis", 
                               className="text-muted")
                    ], className="text-center py-5")
                ])
            ])
        ], style=CARD_STYLE_NONE),
        label="Compare",
        tab_id="comparison-tab"
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




def create_dashboard_content():
    """Create the main dashboard content with tabs"""
    return html.Div([
        # Data storage for filtered symbols
        dcc.Store(id="filtered-symbols-store", data=[]),
        dcc.Store(id="selected-symbol-store", data=""),
        dcc.Store(id="selected-sector-store", data=""),
        
        # Main tabs
        dbc.Tabs([
            create_overview_tab(),
            create_charts_tab(), 
            create_comparison_tab(),
            create_analysis_tab()
        ], id="main-tabs", active_tab="overview-tab")
    ])