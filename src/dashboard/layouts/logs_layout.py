"""
Logs page layout for the dashboard.
Contains the logs page UI components and log viewing functionality.
"""

import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import sys
from pathlib import Path
import pandas as pd
import logging

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logging_config import get_ui_logger
from src.dashboard.utils.log_viewer import (
    create_log_viewer, load_and_filter_logs, format_log_display,
    get_log_stats, generate_log_analytics
)

# Initialize logger
logger = get_ui_logger("dashboard")


def create_logs_layout():
    """Create the logs page layout"""
    return dbc.Container([
        # Logs Page Header
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.H1("System Logs", className="mb-0 text-primary fw-bold"),
                                html.P("View and filter system logs from all components with enhanced analytics",
                                       className="text-muted mb-0")
                            ], width=12)
                        ])
                    ], style={'padding': '15px 20px'})
                ], style={"border": "none", "box-shadow": "0 2px 4px rgba(0,0,0,0.1)", "margin-bottom": "20px"})
            ], width=12)
        ]),

        # Log Viewer Component
        dbc.Row([
            dbc.Col([
                create_log_viewer()
            ], width=12)
        ])
    ], fluid=True)


def register_logs_callbacks(app):
    """Register callbacks for the logs page"""

    @app.callback(
        [Output("log-content", "children"),
         Output("log-stats", "children")],
        [Input("log-component-filter", "value"),
         Input("log-level-filter", "value"),
         Input("log-time-filter", "value"),
         Input("log-event-type-filter", "value"),
         Input("log-symbol-filter", "value"),
         Input("refresh-logs-btn", "n_clicks")]
    )
    def update_logs(component_filter, level_filter, time_filter,
                    event_type_filter, symbol_filter, refresh_clicks):
        """Update log display based on filters"""
        try:
            # Set default values if None
            component_filter = component_filter or "all"
            level_filter = level_filter or "all"
            time_filter = time_filter or "24h"
            event_type_filter = event_type_filter or "all"
            symbol_filter = symbol_filter or "all"

            # Load and filter logs
            logs = load_and_filter_logs(
                component_filter, level_filter, time_filter,
                event_type_filter, symbol_filter
            )

            # Format for display
            log_display = format_log_display(logs)
            log_stats = get_log_stats(logs)

            return log_display, log_stats
        except Exception as e:
            error_msg = f"Error loading logs: {str(e)}"
            return html.Div(error_msg, className="text-danger"), html.Div("Error occurred", className="text-danger")

    @app.callback(
        Output("analytics-section", "children"),
        [Input("analytics-btn", "n_clicks")],
        [State("log-component-filter", "value"),
         State("log-level-filter", "value"),
         State("log-time-filter", "value"),
         State("log-event-type-filter", "value"),
         State("log-symbol-filter", "value")]
    )
    def toggle_analytics(n_clicks, component_filter, level_filter, time_filter,
                         event_type_filter, symbol_filter):
        """Toggle analytics section"""
        if not n_clicks:
            return dash.no_update

        try:
            # Set default values if None
            component_filter = component_filter or "all"
            level_filter = level_filter or "all"
            time_filter = time_filter or "24h"
            event_type_filter = event_type_filter or "all"
            symbol_filter = symbol_filter or "all"

            # Load logs for analytics
            logs = load_and_filter_logs(
                component_filter, level_filter, time_filter,
                event_type_filter, symbol_filter
            )

            # Generate analytics
            analytics = generate_log_analytics(logs)

            return analytics
        except Exception as e:
            return html.Div(f"Error generating analytics: {str(e)}", className="text-danger")

    @app.callback(
        Output("analytics-section", "style"),
        [Input("analytics-btn", "n_clicks")]
    )
    def toggle_analytics_visibility(n_clicks):
        """Toggle analytics section visibility"""
        if not n_clicks:
            return {"display": "none"}

        # Toggle visibility based on click count
        if n_clicks % 2 == 1:  # Odd clicks = show
            return {"display": "block"}
        else:  # Even clicks = hide
            return {"display": "none"}

    @app.callback(
        Output("download-logs", "data"),
        [Input("download-logs-btn", "n_clicks")],
        [State("log-component-filter", "value"),
         State("log-level-filter", "value"),
         State("log-time-filter", "value"),
         State("log-event-type-filter", "value"),
         State("log-symbol-filter", "value")]
    )
    def download_logs(n_clicks, component_filter, level_filter, time_filter,
                      event_type_filter, symbol_filter):
        """Download filtered logs as CSV"""
        if not n_clicks:
            return None

        try:
            # Set default values if None
            component_filter = component_filter or "all"
            level_filter = level_filter or "all"
            time_filter = time_filter or "24h"
            event_type_filter = event_type_filter or "all"
            symbol_filter = symbol_filter or "all"

            logs = load_and_filter_logs(
                component_filter, level_filter, time_filter,
                event_type_filter, symbol_filter
            )

            if not logs:
                return None

            # Convert to DataFrame and create CSV
            df = pd.DataFrame(logs)

            # Flatten metadata for CSV export
            if 'metadata' in df.columns:
                # Extract common metadata fields
                df['event_type'] = df['metadata'].apply(lambda x: x.get('event_type', '') if x else '')
                df['symbol'] = df['metadata'].apply(lambda x: x.get('symbol', '') if x else '')
                df['operation'] = df['metadata'].apply(lambda x: x.get('operation', '') if x else '')
                df['duration_ms'] = df['metadata'].apply(lambda x: x.get('duration_ms', '') if x else '')

                # Remove the metadata column for cleaner CSV
                df = df.drop('metadata', axis=1)

            # Create filename with filters
            filename = f"mltrading_logs_{component_filter}_{level_filter}_{time_filter}.csv"

            return dcc.send_data_frame(df.to_csv, filename, index=False)
        except Exception as e:
            logging.error(f"Error downloading logs: {e}")
            return None

    @app.callback(
        Output("log-content", "children", allow_duplicate=True),
        [Input("clear-logs-btn", "n_clicks")],
        prevent_initial_call=True
    )
    def clear_logs(n_clicks):
        """Clear the combined log file"""
        if not n_clicks:
            return dash.no_update

        try:
            combined_log_path = Path("logs/mltrading_combined.log")
            if combined_log_path.exists():
                # Clear the file by opening in write mode
                with open(combined_log_path, 'w') as f:
                    f.write("")

                return html.Div("Logs cleared successfully.", className="text-success")
            else:
                return html.Div("No log file found to clear.", className="text-warning")
        except Exception as e:
            return html.Div(f"Error clearing logs: {str(e)}", className="text-danger")

    @app.callback(
        Output("log-symbol-filter", "options"),
        [Input("log-event-type-filter", "value")]
    )
    def update_symbol_options(event_type):
        """Update symbol dropdown options based on available trading logs"""
        try:
            if event_type != "trading":
                return [{"label": "All Symbols", "value": "all"}]

            # Load logs to find available symbols
            logs = load_and_filter_logs(event_type_filter="trading")

            # Extract unique symbols from trading logs
            symbols = set()
            for log in logs:
                symbol = log.get('metadata', {}).get('symbol', '')
                if symbol:
                    symbols.add(symbol)

            # Create options
            options = [{"label": "All Symbols", "value": "all"}]
            for symbol in sorted(symbols):
                options.append({"label": symbol, "value": symbol})

            return options
        except Exception as e:
            logging.error(f"Error updating symbol options: {e}")
            return [{"label": "All Symbols", "value": "all"}]
