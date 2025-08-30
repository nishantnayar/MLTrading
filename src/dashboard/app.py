"""
Streamlined ML Trading Dashboard Application.
Main entry point for the Dash web application.
"""

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, callback_context, Input, Output
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import configuration and components
from src.utils.logging_config import get_ui_logger
from src.dashboard.config import (
    DASHBOARD_CONFIG, 
    EXTERNAL_STYLESHEETS, 
    NAV_ITEMS,
    CARD_STYLE
)
from src.dashboard.layouts.dashboard_layout import create_dashboard_content
from src.dashboard.layouts.help_layout import create_help_layout
from src.dashboard.layouts.tests_layout import create_tests_layout
from src.dashboard.layouts.trading_layout import create_trading_dashboard
from src.dashboard.layouts.logs_layout import create_logs_layout, register_logs_callbacks
from src.dashboard.layouts.author_layout import create_author_layout
from src.dashboard.callbacks import register_chart_callbacks, register_overview_callbacks, register_comparison_callbacks, register_pipeline_callbacks
from src.dashboard.callbacks.interactive_chart_callbacks import register_interactive_chart_callbacks
from src.dashboard.callbacks.trading_callbacks import register_trading_callbacks
from src.dashboard.callbacks.detailed_analysis_callbacks import register_detailed_analysis_callbacks
from src.dashboard.callbacks.symbol_sync_callbacks import register_symbol_sync_callbacks
from src.dashboard.utils.date_formatters import get_current_timestamp

# Initialize logger
logger = get_ui_logger("dashboard")

# Initialize Dash app with Bootstrap Cerulean theme
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.CERULEAN,
        *EXTERNAL_STYLESHEETS
    ],
    suppress_callback_exceptions=True
)


def create_navigation():
    """Create the navigation bar"""
    nav_links = []
    for item in NAV_ITEMS:
        nav_links.append(
            dbc.NavItem(
                dbc.NavLink(
                    item["label"], 
                    href="#", 
                    id=item["id"], 
                    className="text-white"
                )
            )
        )
    
    return dbc.Navbar(
        dbc.Container([
            dbc.NavbarBrand([
                html.I(className="fas fa-chart-line me-2"),
                "ML Trading"
            ], className="text-white fw-bold", style={"font-size": "1.25rem"}),
            dbc.Nav(nav_links, className="me-auto")
        ]),
        color="primary",
        dark=True,
        className="mb-4 shadow-sm",
        style={"border-radius": "0 0 12px 12px"}
    )


def create_header():
    """Create the main header section"""
    return dbc.Row([
        dbc.Col([
            html.Div([
                html.H1("ML Trading Dashboard", className="text-center mb-2 text-gradient", 
                        style={"font-weight": "700", "letter-spacing": "-0.025em"}),
                html.Div([
                    html.I(className="fas fa-user-circle me-2 text-primary"),
                    html.Span("Welcome Nishant, Good Evening", className="fs-5")
                ], className="text-center text-muted mb-0 d-flex align-items-center justify-content-center")
            ], className="fade-in")
        ])
    ], className="mb-4 section-spacing")


def create_footer():
    """Create the footer section"""
    current_time = get_current_timestamp("default", "US/Central")
    return dbc.Row([
        dbc.Col([
            html.Div([
                html.I(className="fas fa-clock me-2 text-primary"),
                html.Span("Last Updated: ", className="text-muted"),
                html.Span(current_time, id="footer-timestamp", className="text-primary fw-medium")
            ], className="text-center d-flex align-items-center justify-content-center")
        ])
    ], className="mt-5 section-spacing")


# Main app layout
app.layout = dbc.Container([
    # Location component for navigation
    dcc.Location(id='url', refresh=False),
    
    # Interval to trigger initial callbacks and periodic updates
    dcc.Interval(
        id="initial-interval", 
        interval=60000,  # 1 minute for timestamp updates
        n_intervals=0, 
        disabled=False
    ),
    
    # Pipeline status interval for real-time updates
    dcc.Interval(
        id="pipeline-status-interval",
        interval=30000,  # 30 seconds for pipeline status
        n_intervals=0,
        disabled=False
    ),
    
    # Navigation Bar
    create_navigation(),
    
    # Header
    create_header(),
    
    # Notification areas for pipeline status
    html.Div(id="trigger-pipeline-notification"),
    html.Div(id="pipeline-status-alert"),
    
    # Main Content Area
    dbc.Row([
        dbc.Col([
            html.Div(id="page-content")
        ])
    ], className="mb-3"),
    
    # Footer
    create_footer()
    
], fluid=True)


# Navigation callback
@app.callback(
    Output("page-content", "children"),
    [Input("url", "pathname"),
     Input("nav-dashboard", "n_clicks"),
     Input("nav-trading", "n_clicks"),
     Input("nav-tests", "n_clicks"),
     Input("nav-help", "n_clicks"),
     Input("nav-logs", "n_clicks"),
     Input("nav-author", "n_clicks")]
)
def display_page(pathname, nav_dashboard, nav_trading, nav_tests, nav_help, nav_logs, nav_author):
    """Display different pages based on navigation"""
    ctx = callback_context
    
    if not ctx.triggered:
        # Default to dashboard
        return create_dashboard_content()
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == "nav-trading" or pathname == "/trading":
        return create_trading_dashboard()
    elif button_id == "nav-tests" or pathname == "/tests":
        return create_tests_layout()
    elif button_id == "nav-help" or pathname == "/help":
        return create_help_layout()
    elif button_id == "nav-logs" or pathname == "/logs":
        return create_logs_layout()
    elif button_id == "nav-author" or pathname == "/author":
        return create_author_layout()
    else:
        # Default to dashboard
        return create_dashboard_content()


# Callback to handle initial load and disable interval
@app.callback(
    Output("initial-interval", "disabled"),
    [Input("initial-interval", "n_intervals")],
    prevent_initial_call=False
)
def handle_initial_load(n_intervals):
    """Enable interval for initial load, then disable it"""
    if n_intervals and n_intervals > 0:
        return True  # Disable interval after first run
    return False  # Keep enabled for initial load


# Register all callback modules
register_chart_callbacks(app)
register_overview_callbacks(app)
register_interactive_chart_callbacks(app)
register_comparison_callbacks(app)
register_logs_callbacks(app)

# Callback to update footer timestamp every minute
@app.callback(
    Output("footer-timestamp", "children"),
    [Input("initial-interval", "n_intervals")],
    prevent_initial_call=False
)
def update_footer_timestamp(n_intervals):
    """Update footer timestamp every minute"""
    return get_current_timestamp("default", "US/Central")


# Additional trading callbacks registration (logs callbacks already registered above)
register_trading_callbacks(app)  # Register trading callbacks
register_pipeline_callbacks(app)  # Register pipeline status callbacks
register_detailed_analysis_callbacks(app)  # Register detailed analysis callbacks
register_symbol_sync_callbacks(app)  # Register symbol synchronization callbacks

if __name__ == '__main__':
    logger.info("Starting ML Trading Dashboard...")
    app.run(
        debug=DASHBOARD_CONFIG['debug'],
        host=DASHBOARD_CONFIG['host'], 
        port=DASHBOARD_CONFIG['port']
    )