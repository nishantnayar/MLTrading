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
from src.dashboard.layouts.logs_layout import create_logs_layout, register_logs_callbacks
from src.dashboard.layouts.author_layout import create_author_layout
from src.dashboard.callbacks import register_chart_callbacks, register_overview_callbacks
from src.dashboard.callbacks.interactive_chart_callbacks import register_interactive_chart_callbacks

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
            dbc.NavbarBrand("ML Trading", className="text-white"),
            dbc.Nav(nav_links, className="me-auto")
        ]),
        color="primary",
        dark=True,
        className="mb-4"
    )


def create_header():
    """Create the main header section"""
    return dbc.Row([
        dbc.Col([
            html.Div([
                html.H2("ML Trading Dashboard", className="text-center mb-2"),
                html.P("Welcome Nishant, Good Evening", className="text-center text-muted mb-0")
            ])
        ])
    ], className="mb-4")


def create_footer():
    """Create the footer section"""
    return dbc.Row([
        dbc.Col([
            html.Div([
                html.Span("Last Updated: ", className="text-muted"),
                html.Span("2nd Aug, 2025 5:54 PM", className="text-muted")
            ], className="text-center")
        ])
    ], className="mt-5")


# Main app layout
app.layout = dbc.Container([
    # Location component for navigation
    dcc.Location(id='url', refresh=False),
    
    # Interval to trigger initial callbacks (disabled by default, only runs once)
    dcc.Interval(
        id="initial-interval", 
        interval=DASHBOARD_CONFIG['refresh_interval'], 
        n_intervals=0, 
        disabled=True
    ),
    
    # Navigation Bar
    create_navigation(),
    
    # Header
    create_header(),
    
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
     Input("nav-help", "n_clicks"),
     Input("nav-settings", "n_clicks"),
     Input("nav-logs", "n_clicks"),
     Input("nav-author", "n_clicks")]
)
def display_page(pathname, nav_dashboard, nav_help, nav_settings, nav_logs, nav_author):
    """Display different pages based on navigation"""
    ctx = callback_context
    
    if not ctx.triggered:
        # Default to dashboard
        return create_dashboard_content()
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == "nav-help" or pathname == "/help":
        return create_help_layout()
    elif button_id == "nav-settings" or pathname == "/settings":
        return html.Div([
            html.H3("Settings", className="text-center"),
            html.P("Settings page coming soon...", className="text-center text-muted")
        ])
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
register_logs_callbacks(app)


if __name__ == '__main__':
    logger.info("Starting ML Trading Dashboard...")
    app.run(
        debug=DASHBOARD_CONFIG['debug'],
        host=DASHBOARD_CONFIG['host'], 
        port=DASHBOARD_CONFIG['port']
    )