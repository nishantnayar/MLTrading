"""
Help page layout for the dashboard.
Contains the help page UI components and documentation.
"""

import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logging_config import get_ui_logger

# Initialize logger
logger = get_ui_logger("dashboard")

def create_help_section(title, content, icon_class="fas fa-info-circle"):
    """Create a standardized help section."""
    return dbc.Card([
        dbc.CardHeader([
            html.I(className=f"{icon_class} me-2"),
            html.H5(title, className="mb-0")
        ], className="bg-light"),
        dbc.CardBody(content)
    ], className="mb-3")

def create_help_layout():
    """Create the help page layout"""
    return dbc.Container([
        # Help Page Header
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.H1("Help & Documentation", className="mb-0 text-primary fw-bold"),
                                html.P("Complete guide to using the ML Trading Dashboard", className="text-muted mb-0")
                            ], width=8),
                            dbc.Col([
                                html.Div([
                                    dbc.Button([
                                        html.I(className="fas fa-arrow-left me-2"),
                                        "Back to Dashboard"
                                    ], color="outline-primary", size="sm", href="/", id="back-to-dashboard")
                                ], className="text-end")
                            ], width=4)
                        ])
                    ], style={'padding': '15px 20px'})
                ], style={"border": "none", "box-shadow": "0 2px 4px rgba(0,0,0,0.1)", "margin-bottom": "20px"})
            ], width=12)
        ]),
        
        # Quick Start Guide
        dbc.Row([
            dbc.Col([
                create_help_section(
                    "Quick Start Guide",
                    [
                        html.P("Welcome to the ML Trading Dashboard! Here's how to get started:"),
                        html.Ol([
                            html.Li("Select a sector from the Sector Distribution chart to filter stocks"),
                            html.Li("Click on an industry in the Industry Distribution chart for more specific filtering"),
                            html.Li("Choose a stock symbol from the dropdown to view detailed analysis"),
                            html.Li("Monitor real-time price charts and volume data"),
                            html.Li("Review trading signals and market statistics")
                        ])
                    ],
                    "fas fa-rocket"
                )
            ], width=12)
        ]),
        
        # Chart Features
        dbc.Row([
            dbc.Col([
                create_help_section(
                    "Chart Features",
                    [
                        html.H6("Sector Distribution Chart:"),
                        html.Ul([
                            html.Li("Shows the number of stocks in each sector"),
                            html.Li("Click on any sector bar to filter stocks"),
                            html.Li("Bars are sorted with largest sector at the top")
                        ]),
                        html.H6("Industry Distribution Chart:"),
                        html.Ul([
                            html.Li("Displays industries within the selected sector"),
                            html.Li("Click on any industry bar to filter stocks"),
                            html.Li("Updates automatically when a sector is selected")
                        ]),
                        html.H6("OHLC Price Chart:"),
                        html.Ul([
                            html.Li("Candlestick chart showing open, high, low, and close prices"),
                            html.Li("Green candles indicate price increases"),
                            html.Li("Red candles indicate price decreases"),
                            html.Li("Displays all available historical data")
                        ]),
                        html.H6("Volume Chart:"),
                        html.Ul([
                            html.Li("Shows trading volume over time"),
                            html.Li("Helps identify trading activity patterns"),
                            html.Li("Correlates with price movements")
                        ])
                    ],
                    "fas fa-chart-bar"
                )
            ], width=12)
        ]),
        
        # Navigation Guide
        dbc.Row([
            dbc.Col([
                create_help_section(
                    "Navigation Guide",
                    [
                        html.H6("Top Navigation Bar:"),
                        html.Ul([
                            html.Li("Dashboard - Main trading interface with charts and data"),
                            html.Li("Logs - View system logs and performance metrics"),
                            html.Li("Settings - Configure trading parameters and system preferences"),
                            html.Li("Help - This documentation page")
                        ]),
                        html.H6("Dashboard Tabs:"),
                        html.Ul([
                            html.Li("Overview - Summary statistics and key metrics"),
                            html.Li("Charts - Interactive charts and data visualization"),
                            html.Li("Analysis - Technical analysis and trading signals"),
                            html.Li("Settings - Quick access to common settings")
                        ])
                    ],
                    "fas fa-compass"
                )
            ], width=6),
            
            # Data Sources
            dbc.Col([
                create_help_section(
                    "Data Sources",
                    [
                        html.H6("Market Data:"),
                        html.Ul([
                            html.Li("Real-time data from Yahoo Finance"),
                            html.Li("Historical OHLC data for technical analysis"),
                            html.Li("Volume and price information"),
                            html.Li("Sector and industry classifications")
                        ]),
                        html.H6("Database:"),
                        html.Ul([
                            html.Li("PostgreSQL database for data storage"),
                            html.Li("Automated data collection and updates"),
                            html.Li("Data retention and backup policies"),
                            html.Li("Performance optimization for large datasets")
                        ])
                    ],
                    "fas fa-database"
                )
            ], width=6)
        ]),
        
        # Trading Features
        dbc.Row([
            dbc.Col([
                create_help_section(
                    "Trading Features",
                    [
                        html.H6("Symbol Selection:"),
                        html.Ul([
                            html.Li("Dynamic dropdown based on sector/industry filters"),
                            html.Li("Company names displayed with symbols"),
                            html.Li("Real-time data availability checking"),
                            html.Li("Automatic symbol validation")
                        ]),
                        html.H6("Time Range Filtering:"),
                        html.Ul([
                            html.Li("1 Day, 1 Week, 1 Month, 3 Months, 1 Year"),
                            html.Li("All available data option"),
                            html.Li("Real-time chart updates"),
                            html.Li("Historical data analysis")
                        ])
                    ],
                    "fas fa-trading"
                )
            ], width=6),
            
            # System Information
            dbc.Col([
                create_help_section(
                    "System Information",
                    [
                        html.H6("Technology Stack:"),
                        html.Ul([
                            html.Li("Frontend: Dash with Bootstrap 5.3.0"),
                            html.Li("Backend: FastAPI with Python 3.9+"),
                            html.Li("Database: PostgreSQL with psycopg2"),
                            html.Li("Charts: Plotly for interactive visualizations")
                        ]),
                        html.H6("Performance:"),
                        html.Ul([
                            html.Li("Real-time data updates"),
                            html.Li("Optimized database queries"),
                            html.Li("Responsive design for all devices"),
                            html.Li("Efficient memory management")
                        ])
                    ],
                    "fas fa-cogs"
                )
            ], width=6)
        ]),
        
        # Troubleshooting
        dbc.Row([
            dbc.Col([
                create_help_section(
                    "Troubleshooting",
                    [
                        html.H6("Common Issues:"),
                        html.Ul([
                            html.Li("No data displayed - Check symbol selection and time range"),
                            html.Li("Charts not loading - Refresh the page or check internet connection"),
                            html.Li("Slow performance - Reduce time range or check system resources"),
                            html.Li("Database errors - Check connection settings in logs")
                        ]),
                        html.H6("Getting Help:"),
                        html.Ul([
                            html.Li("Check the Logs page for error messages"),
                            html.Li("Review system status in Settings"),
                            html.Li("Contact support with specific error details"),
                            html.Li("Check documentation for known issues")
                        ])
                    ],
                    "fas fa-tools"
                )
            ], width=12)
        ]),
        
        # Contact Information
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        html.I(className="fas fa-envelope me-2"),
                        html.H5("Contact & Support", className="mb-0")
                    ], className="bg-primary text-white"),
                    dbc.CardBody([
                        html.P("For technical support or feature requests:"),
                        html.Ul([
                            html.Li("Email: support@mltrading.com"),
                            html.Li("Documentation: docs.mltrading.com"),
                            html.Li("GitHub: github.com/ml-trading/dashboard"),
                            html.Li("Issues: github.com/ml-trading/dashboard/issues")
                        ])
                    ])
                ])
            ], width=12)
        ])
    ], fluid=True) 