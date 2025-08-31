"""
Help page layout for the dashboard.
Contains comprehensive documentation for the updated ML Trading Dashboard.
"""

from dash import html
import dash_bootstrap_components as dbc
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logging_config import get_ui_logger

# Initialize logger
logger = get_ui_logger("dashboard")


def create_help_section(title, content, icon_class="fas fa-info-circle", card_color="light"):
    """Create a standardized help section with enhanced styling."""
    return dbc.Card([
        dbc.CardHeader([
            html.I(className=f"{icon_class} me-2"),
            html.H5(title, className="mb-0")
        ], className=f"bg-{card_color}" + (" text-white" if card_color in ["primary", "success", "danger", "warning", "info"] else "")),
        dbc.CardBody(content)
    ], className="mb-4 shadow-sm")


def create_feature_card(title, description, icon, color="primary"):
    """Create a feature highlight card."""
    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.I(className=f"{icon} fa-2x text-{color} mb-3"),
                html.H5(title, className="mb-2"),
                html.P(description, className="text-muted mb-0")
            ], className="text-center")
        ])
    ], className="h-100 shadow-sm border-0")


def create_step_card(step_num, title, description, icon):
    """Create a numbered step card for workflows."""
    return dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.Span(step_num, className="badge bg-primary fs-6 me-2"),
                        html.I(className=f"{icon} me-2"),
                        html.Strong(title)
                    ]),
                    html.P(description, className="mt-2 mb-0 text-muted")
                ], width=12)
            ])
        ])
    ], className="mb-3 border-start border-primary border-3")


def create_help_layout():
    """Create the enhanced help page layout with latest features."""
    return dbc.Container([
        # Enhanced Header with Quick Links
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.H1([
                                    html.I(className="fas fa-book-open me-3 text-primary"),
                                    "ML Trading Dashboard"
                                ], className="mb-2 fw-bold"),
                                                                 html.P("Complete guide to the simplified trading dashboard with advanced volume analysis and technical indicators",
                                       className="text-muted mb-3"),
                                 dbc.Alert([
                                     html.I(className="fas fa-info-circle me-2"),
                                     html.Strong("Simplified Dashboard:"), " The settings page has been removed to focus on core trading functionality and eliminate debugging complexity."
                                 ], color="info", className="mb-3"),
                                dbc.ButtonGroup([
                                    dbc.Button([html.I(className="fas fa-rocket me-1"), "Quick Start"],
                                              color="primary", size="sm", href="#quick-start"),
                                    dbc.Button([html.I(className="fas fa-chart-line me-1"), "Charts Guide"],
                                              color="outline-primary", size="sm", href="#charts"),
                                    dbc.Button([html.I(className="fas fa-volume-up me-1"), "Volume Features"],
                                              color="outline-success", size="sm", href="#volume"),
                                    dbc.Button([html.I(className="fas fa-cogs me-1"), "Technical Analysis"],
                                              color="outline-info", size="sm", href="#technical")
                                ])
                            ], width=12)
                        ])
                    ], className="py-4")
                ], className="border-0 shadow-lg bg-gradient")
            ], width=12)
        ], className="mb-4"),


        # Quick Start Guide
        dbc.Row([
            dbc.Col([
                create_help_section(
                    "🚀 Quick Start Guide",
                    [
                        html.P("Get up and running with the ML Trading Dashboard in minutes:", className="lead"),
                        dbc.Row([
                            dbc.Col([
                                create_step_card(
                                    "1",
                                    "Navigate to Interactive Charts",
                                    "Click on the 'Interactive Charts' tab to access the main trading interface",
                                    "fas fa-mouse-pointer"
                                )
                            ], width=6),
                            dbc.Col([
                                create_step_card(
                                    "2",
                                    "Select Your Symbol",
                                    "Choose a stock symbol from the dropdown. Use sector/industry filters to narrow down options",
                                    "fas fa-search"
                                )
                            ], width=6)
                        ]),
                        dbc.Row([
                            dbc.Col([
                                create_step_card(
                                    "3",
                                    "Configure Chart Display",
                                    "Choose chart type (Candlestick/OHLC/Line), select technical indicators, and set volume display options",
                                    "fas fa-sliders-h"
                                )
                            ], width=6),
                            dbc.Col([
                                create_step_card(
                                    "4",
                                    "Analyze the Data",
                                    "Review the Technical Analysis Summary, then dive into the interactive charts below",
                                    "fas fa-chart-line"
                                )
                            ], width=6)
                        ])
                    ],
                    "fas fa-rocket",
                    "primary"
                )
            ], width=12)
        ], id="quick-start"),

        # Enhanced Charts Section
        dbc.Row([
            dbc.Col([
                create_help_section(
                    "📊 Interactive Charts Guide",
                    [
                        dbc.Tabs([
                            dbc.Tab([
                                html.Div([
                                    html.H5("Chart Types & Controls", className="mt-3 mb-3"),
                                    dbc.Alert([
                                        html.H6("🎛️ New Button-Based Controls", className="alert-heading mb-2"),
                                        html.P("Chart type selection now uses intuitive button controls instead of dropdowns for better accessibility and mobile support!", className="mb-0")
                                    ], color="success", className="mb-3"),

                                    html.H6("Chart Type Buttons:"),
                                    dbc.ButtonGroup([
                                        dbc.Button("📈 Candlestick", color="primary", size="sm", disabled=True),
                                        dbc.Button("📊 OHLC", color="outline-primary", size="sm", disabled=True),
                                        dbc.Button("📉 Line", color="outline-primary", size="sm", disabled=True),
                                        dbc.Button("📋 Bar", color="outline-primary", size="sm", disabled=True)
                                    ], className="mb-4 w-100"),

                                    dbc.Row([
                                        dbc.Col([
                                            dbc.Card([
                                                dbc.CardBody([
                                                    html.H6("📈 Candlestick Charts"),
                                                    html.P("Default chart type showing OHLC data with colored candles:"),
                                                    html.Ul([
                                                        html.Li("Green candles: Close > Open (bullish)"),
                                                        html.Li("Red candles: Close < Open (bearish)"),
                                                        html.Li("Wicks show high/low prices"),
                                                        html.Li("Best for trend and pattern analysis")
                                                    ])
                                                ])
                                            ])
                                        ], width=6),
                                        dbc.Col([
                                            dbc.Card([
                                                dbc.CardBody([
                                                    html.H6("📊 OHLC Charts"),
                                                    html.P("Traditional bar charts for precise price analysis:"),
                                                    html.Ul([
                                                        html.Li("Vertical line shows high-low range"),
                                                        html.Li("Left tick marks the opening price"),
                                                        html.Li("Right tick marks the closing price"),
                                                        html.Li("Ideal for technical analysis")
                                                    ])
                                                ])
                                            ])
                                        ], width=6)
                                    ], className="mb-3"),
                                    dbc.Row([
                                        dbc.Col([
                                            dbc.Card([
                                                dbc.CardBody([
                                                    html.H6("📉 Line Charts"),
                                                    html.P("Simple line connecting closing prices:"),
                                                    html.Ul([
                                                        html.Li("Clean view of price trends"),
                                                        html.Li("Less visual noise"),
                                                        html.Li("Great for long-term analysis"),
                                                        html.Li("Easy to spot support/resistance")
                                                    ])
                                                ])
                                            ])
                                        ], width=6),
                                        dbc.Col([
                                            dbc.Card([
                                                dbc.CardBody([
                                                    html.H6("📋 Bar Charts"),
                                                    html.P("Colored bars based on price direction:"),
                                                    html.Ul([
                                                        html.Li("Height shows closing price"),
                                                        html.Li("Green bars: price closed higher"),
                                                        html.Li("Red bars: price closed lower"),
                                                        html.Li("Good for volume comparison")
                                                    ])
                                                ])
                                            ])
                                        ], width=6)
                                    ])
                                ])
                            ], label="Chart Types", tab_id="chart-types"),

                            dbc.Tab([
                                html.Div([
                                    html.H5("Technical Indicators", className="mt-3 mb-3"),
                                    dbc.Accordion([
                                        dbc.AccordionItem([
                                            html.H6("Moving Averages"),
                                            html.Ul([
                                                html.Li("SMA (20): Simple Moving Average over 20 periods"),
                                                html.Li("EMA (12,26): Exponential Moving Averages for MACD calculation"),
                                                html.Li("Helps identify trend direction and momentum")
                                            ]),
                                            dbc.Alert("💡 Use moving averages to identify trend changes and potential entry/exit points", color="info")
                                        ], title="📈 Moving Averages"),

                                        dbc.AccordionItem([
                                            html.H6("Momentum Oscillators"),
                                            html.Ul([
                                                html.Li("RSI (14): Relative Strength Index - measures overbought/oversold conditions"),
                                                html.Li("MACD: Moving Average Convergence Divergence - trend and momentum"),
                                                html.Li("Stochastic: Compares closing price to price range over time")
                                            ]),
                                            dbc.Alert("⚠️ RSI > 70 suggests overbought, RSI < 30 suggests oversold conditions", color="warning")
                                        ], title="⚡ Momentum Indicators"),

                                        dbc.AccordionItem([
                                            html.H6("Volatility & Volume"),
                                            html.Ul([
                                                html.Li("Bollinger Bands: Volatility bands around moving average"),
                                                html.Li("ATR: Average True Range - measures volatility"),
                                                html.Li("VWAP: Volume Weighted Average Price - institutional benchmark")
                                            ]),
                                            dbc.Alert("📊 VWAP is often used by institutions as a benchmark for trade execution", color="success")
                                        ], title="📊 Volatility & Volume")
                                    ])
                                ])
                            ], label="Technical Indicators", tab_id="indicators")
                        ])
                    ],
                    "fas fa-chart-line",
                    "info"
                )
            ], width=12)
        ], id="charts"),

        # Volume Features Section
        dbc.Row([
            dbc.Col([
                create_help_section(
                    "🔊 Enhanced Volume Analysis",
                    [
                        dbc.Alert([
                            html.H5("Volume is King! 👑", className="alert-heading"),
                            html.P("Volume confirms price movements and reveals market sentiment. Our enhanced volume tools give you deep insights into trading activity.")
                        ], color="success", className="mb-4"),

                        dbc.Row([
                            dbc.Col([
                                html.H5("Volume Display Options"),
                                dbc.ListGroup([
                                    dbc.ListGroupItem([
                                        html.Strong("Hide Volume"), " - Clean price-only view"
                                    ]),
                                    dbc.ListGroupItem([
                                        html.Strong("Volume Bars"), " - Standard volume bars"
                                    ]),
                                    dbc.ListGroupItem([
                                        html.Strong("Volume + MA"), " - Bars with 20-day moving average (recommended)",
                                        dbc.Badge("Default", color="primary", className="ms-2")
                                    ]),
                                    dbc.ListGroupItem([
                                        html.Strong("Volume Profile"), " - Advanced volume analysis (future enhancement)"
                                    ])
                                ])
                            ], width=6),
                            dbc.Col([
                                html.H5("Color Coding Options"),
                                dbc.Card([
                                    dbc.CardBody([
                                        dbc.Switch(
                                            id="help-color-demo",
                                            label="Color by Price Direction",
                                            value=True,
                                            disabled=True
                                        ),
                                        html.Hr(),
                                        html.Div([
                                            dbc.Badge("🟢 Green", color="success", className="me-2"), "Volume when price closes higher",
                                            html.Br(),
                                            dbc.Badge("🔴 Red", color="danger", className="me-2"), "Volume when price closes lower",
                                            html.Br(),
                                            dbc.Badge("🔵 Bright", color="info", className="me-2"), "High volume (>1.5x average)",
                                            html.Br(),
                                            dbc.Badge("⚪ Dim", color="secondary", className="me-2"), "Normal volume"
                                        ])
                                    ])
                                ])
                            ], width=6)
                        ]),

                        html.Hr(),

                        dbc.Row([
                            dbc.Col([
                                html.H5("Technical Analysis Summary Cards"),
                                html.P("The volume card in the Technical Analysis Summary shows:"),
                                dbc.Row([
                                    dbc.Col([
                                        dbc.Card([
                                            dbc.CardBody([
                                                html.H6("Current Volume", className="text-muted mb-1"),
                                                html.H4("2.5M", className="text-success mb-0"),
                                                html.Small("1.2x avg", className="text-muted")
                                            ], className="text-center")
                                        ], className="border-success")
                                    ], width=4),
                                    dbc.Col([
                                        html.Ul([
                                            html.Li("📊 Formatted volume (K/M/B)"),
                                            html.Li("📈 Ratio vs 20-day average"),
                                            html.Li("🎨 Color-coded status"),
                                            html.Li("⚡ Real-time updates")
                                        ])
                                    ], width=8)
                                ])
                            ], width=12)
                        ])
                    ],
                    "fas fa-volume-up",
                    "success"
                )
            ], width=12)
        ], id="volume"),

        # Technical Analysis Section
        dbc.Row([
            dbc.Col([
                create_help_section(
                    "🔬 Technical Analysis Summary",
                    [
                        html.P("The Technical Analysis Summary provides instant insights into key metrics:", className="lead"),

                        dbc.Row([
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardHeader("Sample Analysis Summary"),
                                    dbc.CardBody([
                                        dbc.Row([
                                            dbc.Col([
                                                html.H6("Current Price", className="text-muted mb-1"),
                                                html.H5("$150.25", className="text-primary mb-0")
                                            ], width=2, className="text-center"),
                                            dbc.Col([
                                                html.H6("30D Change", className="text-muted mb-1"),
                                                html.H5("+5.2%", className="text-success mb-0")
                                            ], width=2, className="text-center"),
                                            dbc.Col([
                                                html.H6("RSI(14)", className="text-muted mb-1"),
                                                html.H5("65.4", className="text-warning mb-0")
                                            ], width=2, className="text-center"),
                                            dbc.Col([
                                                html.H6("Volume", className="text-muted mb-1"),
                                                html.H5("2.5M", className="text-success mb-0"),
                                                html.Small("1.2x avg", className="text-muted")
                                            ], width=2, className="text-center"),
                                            dbc.Col([
                                                html.H6("Trend", className="text-muted mb-1"),
                                                html.H5("Bullish", className="text-success mb-0")
                                            ], width=2, className="text-center"),
                                            dbc.Col([
                                                dbc.Button("View Detailed Analysis", color="outline-primary", size="sm")
                                            ], width=2, className="d-flex align-items-center justify-content-center")
                                        ])
                                    ])
                                ])
                            ], width=12)
                        ], className="mb-3"),

                        dbc.Row([
                            dbc.Col([
                                html.H6("Understanding the Metrics:"),
                                dbc.ListGroup([
                                    dbc.ListGroupItem([
                                        html.Strong("Current Price: "), "Real-time or latest available price"
                                    ]),
                                    dbc.ListGroupItem([
                                        html.Strong("30D Change: "), "Percentage change over 30 days (green=positive, red=negative)"
                                    ]),
                                    dbc.ListGroupItem([
                                        html.Strong("RSI(14): "), "Relative Strength Index - overbought (>70), oversold (<30), neutral (30-70)"
                                    ]),
                                    dbc.ListGroupItem([
                                        html.Strong("Volume: "), "Current volume vs 20-day average with color coding"
                                    ]),
                                    dbc.ListGroupItem([
                                        html.Strong("Trend: "), "Bullish (price > SMA20) or Bearish (price < SMA20)"
                                    ])
                                ])
                            ], width=12)
                        ])
                    ],
                    "fas fa-microscope",
                    "warning"
                )
            ], width=12)
        ], id="technical"),

        # Dashboard Navigation
        dbc.Row([
            dbc.Col([
                create_help_section(
                    "🧭 Dashboard Navigation",
                    [
                        dbc.Row([
                            dbc.Col([
                                html.H6("Main Tabs:"),
                                dbc.ListGroup([
                                    dbc.ListGroupItem([
                                        html.I(className="fas fa-tachometer-alt me-2"),
                                        html.Strong("Overview"), " - Market statistics and sector/industry analysis"
                                    ]),
                                    dbc.ListGroupItem([
                                        html.I(className="fas fa-chart-line me-2"),
                                        html.Strong("Interactive Charts"), " - Advanced charting with technical analysis"
                                    ]),
                                    dbc.ListGroupItem([
                                        html.I(className="fas fa-brain me-2"),
                                        html.Strong("Analysis"), " - Advanced trading insights and analytics"
                                    ]),

                                ])
                            ], width=6),
                            dbc.Col([
                                html.H6("Top Navigation:"),
                                dbc.ListGroup([
                                    dbc.ListGroupItem([
                                        html.I(className="fas fa-home me-2"),
                                        html.Strong("Dashboard"), " - Main application interface"
                                    ]),
                                    dbc.ListGroupItem([
                                        html.I(className="fas fa-file-alt me-2"),
                                        html.Strong("Logs"), " - System logs and performance monitoring"
                                    ]),
                                    dbc.ListGroupItem([
                                        html.I(className="fas fa-question-circle me-2"),
                                        html.Strong("Help"), " - This documentation page"
                                    ]),
                                    dbc.ListGroupItem([
                                        html.I(className="fas fa-user me-2"),
                                        html.Strong("Author"), " - About the developer"
                                    ])
                                ])
                            ], width=6)
                        ])
                    ],
                    "fas fa-compass"
                )
            ], width=12)
        ]),

        # Keyboard Shortcuts
        dbc.Row([
            dbc.Col([
                create_help_section(
                    "⌨️ Keyboard Shortcuts & Tips",
                    [
                        dbc.Row([
                            dbc.Col([
                                html.H6("Chart Interactions:"),
                                dbc.Table([
                                    html.Tbody([
                                        html.Tr([html.Td("Zoom"), html.Td("Mouse wheel or drag")]),
                                        html.Tr([html.Td("Pan"), html.Td("Click and drag")]),
                                        html.Tr([html.Td("Reset Zoom"), html.Td("Double-click")]),
                                        html.Tr([html.Td("Toggle Legend"), html.Td("Click legend items")]),
                                        html.Tr([html.Td("Crosshair"), html.Td("Hover over chart")])
                                    ])
                                ], striped=True, size="sm")
                            ], width=6),
                            dbc.Col([
                                html.H6("Pro Tips:"),
                                dbc.Alert([
                                    html.Ul([
                                        html.Li("Use the volume display dropdown to customize your view"),
                                        html.Li("Check Technical Analysis Summary before diving into charts"),
                                        html.Li("Multiple indicators can be selected simultaneously"),
                                        html.Li("Volume color coding helps identify accumulation/distribution"),
                                        html.Li("Right-click charts for additional options")
                                    ], className="mb-0")
                                ], color="info")
                            ], width=6)
                        ])
                    ],
                    "fas fa-keyboard"
                )
            ], width=12)
        ]),

        # Recent Improvements Section
        dbc.Row([
            dbc.Col([
                create_help_section(
                    "🚀 Recent System Improvements",
                    [
                        dbc.Alert([
                            html.H5("Latest Updates - August 2025", className="alert-heading"),
                            html.P("The ML Trading Dashboard has received significant improvements for better usability and reliability.")
                        ], color="primary", className="mb-4"),

                        dbc.Row([
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardHeader([
                                        html.I(className="fas fa-mouse-pointer me-2"),
                                        html.H6("Button-Based Chart Controls", className="mb-0")
                                    ]),
                                    dbc.CardBody([
                                        html.Ul([
                                            html.Li("Replaced problematic dropdown menus with accessible button controls"),
                                            html.Li("Improved mobile and touch device compatibility"),
                                            html.Li("Better visual feedback for selected chart types"),
                                            html.Li("Enhanced keyboard navigation support")
                                        ])
                                    ])
                                ])
                            ], width=6),
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardHeader([
                                        html.I(className="fas fa-robot me-2"),
                                        html.H6("Automated Testing Suite", className="mb-0")
                                    ]),
                                    dbc.CardBody([
                                        html.Ul([
                                            html.Li("Fully automated regression testing for CI/CD"),
                                            html.Li("Comprehensive dashboard functionality validation"),
                                            html.Li("Graceful handling of optional features (Alpaca integration)"),
                                            html.Li("No manual intervention required for test execution")
                                        ])
                                    ])
                                ])
                            ], width=6)
                        ], className="mb-3"),

                        dbc.Row([
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardHeader([
                                        html.I(className="fas fa-chart-bar me-2"),
                                        html.H6("Enhanced Volume Analysis", className="mb-0")
                                    ]),
                                    dbc.CardBody([
                                        html.Ul([
                                            html.Li("Improved volume display options and color coding"),
                                            html.Li("Better volume ratio calculations vs historical averages"),
                                            html.Li("More intuitive volume chart integration"),
                                            html.Li("Enhanced volume-based technical indicators")
                                        ])
                                    ])
                                ])
                            ], width=6),
                            dbc.Col([
                                dbc.Card([
                                    dbc.CardHeader([
                                        html.I(className="fas fa-cogs me-2"),
                                        html.H6("System Reliability", className="mb-0")
                                    ]),
                                    dbc.CardBody([
                                        html.Ul([
                                            html.Li("Fixed syntax errors and code quality issues"),
                                            html.Li("Improved error handling and graceful degradation"),
                                            html.Li("Better logging and debugging capabilities"),
                                            html.Li("Consolidated documentation for easier maintenance")
                                        ])
                                    ])
                                ])
                            ], width=6)
                        ])
                    ],
                    "fas fa-star",
                    "primary"
                )
            ], width=12)
        ]),

        # Troubleshooting
        dbc.Row([
            dbc.Col([
                create_help_section(
                    "🔧 Troubleshooting",
                    [
                        dbc.Accordion([
                            dbc.AccordionItem([
                                html.H6("Common Solutions:"),
                                html.Ul([
                                    html.Li("Refresh the page (Ctrl+F5)"),
                                    html.Li("Check your internet connection"),
                                    html.Li("Try selecting a different symbol"),
                                    html.Li("Clear browser cache and cookies")
                                ]),
                                dbc.Alert("If problems persist, check the Logs page for detailed error messages.", color="warning")
                            ], title="Charts Not Loading"),

                            dbc.AccordionItem([
                                html.H6("Possible Causes:"),
                                html.Ul([
                                    html.Li("Symbol may not have recent data"),
                                    html.Li("Market may be closed"),
                                    html.Li("Data provider temporary issue"),
                                    html.Li("Time range too narrow")
                                ]),
                                dbc.Alert("Try expanding the time range or selecting a more active symbol.", color="info")
                            ], title="No Data Displayed"),

                            dbc.AccordionItem([
                                html.H6("Performance Tips:"),
                                html.Ul([
                                    html.Li("Reduce the number of indicators displayed"),
                                    html.Li("Use shorter time ranges for real-time analysis"),
                                    html.Li("Close other browser tabs"),
                                    html.Li("Disable browser extensions that might interfere")
                                ]),
                                dbc.Alert("For best performance, use Chrome or Firefox browsers.", color="success")
                            ], title="Slow Performance")
                        ])
                    ],
                    "fas fa-tools",
                    "danger"
                )
            ], width=12)
        ]),

        # Footer with Contact Info
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.H5([html.I(className="fas fa-rocket me-2"), "Ready to Trade?"]),
                                html.P("You're now equipped with all the knowledge to use the ML Trading Dashboard effectively. Start with the Overview tab, then explore Interactive Charts for detailed analysis.")
                            ], width=8),
                            dbc.Col([
                                dbc.Button([
                                    html.I(className="fas fa-arrow-right me-2"),
                                    "Go to Dashboard"
                                ], color="primary", size="lg", href="/", className="w-100")
                            ], width=4, className="d-flex align-items-center")
                        ])
                    ])
                ], className="border-primary border-2")
            ], width=12)
        ], className="mt-4 mb-5")

    ], fluid=True, className="py-4")

