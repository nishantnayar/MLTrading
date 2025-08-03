"""
Settings page layout for the dashboard.
Contains the settings page UI components.
"""

import dash
from dash import html, dcc, callback_context, Input, Output
import dash_bootstrap_components as dbc
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logging_config import get_ui_logger

# Initialize logger
logger = get_ui_logger("dashboard")

def create_settings_layout():
    """Create the settings page layout"""
    return dbc.Container([
        # Settings Page Header
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.H1("System Settings", className="mb-0 text-primary fw-bold"),
                                html.P("Configure trading parameters and system preferences", className="text-muted mb-0")
                            ], width=8),
                            dbc.Col([
                                html.Div([
                                    dbc.Button([
                                        html.I(className="fas fa-arrow-left me-2"),
                                        "Back to Dashboard"
                                    ], color="outline-primary", size="sm", href="/", id="back-to-dashboard-settings")
                                ], className="text-end")
                            ], width=4)
                        ])
                    ], style={'padding': '15px 20px'})
                ], style={"border": "none", "box-shadow": "0 2px 4px rgba(0,0,0,0.1)", "margin-bottom": "20px"})
            ], width=12)
        ]),
        
        # Settings Cards
        dbc.Row([
            # Trading Settings
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Trading Configuration"),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Label("Default Risk Level:"),
                                dcc.Slider(
                                    id='default-risk-slider',
                                    min=1,
                                    max=10,
                                    step=1,
                                    value=5,
                                    marks={i: str(i) for i in range(1, 11)}
                                )
                            ], width=6),
                            dbc.Col([
                                html.Label("Max Position Size (%):"),
                                dcc.Input(
                                    id='max-position-size',
                                    type='number',
                                    value=10,
                                    min=1,
                                    max=100,
                                    className="form-control"
                                )
                            ], width=6)
                        ], className="mb-3"),
                        dbc.Row([
                            dbc.Col([
                                html.Label("Stop Loss (%):"),
                                dcc.Input(
                                    id='stop-loss',
                                    type='number',
                                    value=5,
                                    min=1,
                                    max=50,
                                    step=0.5,
                                    className="form-control"
                                )
                            ], width=6),
                            dbc.Col([
                                html.Label("Take Profit (%):"),
                                dcc.Input(
                                    id='take-profit',
                                    type='number',
                                    value=10,
                                    min=1,
                                    max=100,
                                    step=0.5,
                                    className="form-control"
                                )
                            ], width=6)
                        ])
                    ])
                ], className="settings-card")
            ], width=6),
            
            # System Settings
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("System Configuration"),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Label("Data Refresh Interval (seconds):"),
                                dcc.Input(
                                    id='refresh-interval',
                                    type='number',
                                    value=30,
                                    min=5,
                                    max=300,
                                    className="form-control"
                                )
                            ], width=6),
                            dbc.Col([
                                html.Label("Log Level:"),
                                dcc.Dropdown(
                                    id='log-level-dropdown',
                                    options=[
                                        {'label': 'DEBUG', 'value': 'DEBUG'},
                                        {'label': 'INFO', 'value': 'INFO'},
                                        {'label': 'WARNING', 'value': 'WARNING'},
                                        {'label': 'ERROR', 'value': 'ERROR'}
                                    ],
                                    value='INFO',
                                    className="form-control"
                                )
                            ], width=6)
                        ], className="mb-3"),
                        dbc.Row([
                            dbc.Col([
                                html.Label("Database Connection:"),
                                html.Div([
                                    html.Span("Connected", className="badge bg-success me-2"),
                                    html.Small("PostgreSQL - market_data", className="text-muted")
                                ])
                            ], width=6),
                            dbc.Col([
                                html.Label("API Status:"),
                                html.Div([
                                    html.Span("Online", className="badge bg-success me-2"),
                                    html.Small("FastAPI - Running", className="text-muted")
                                ])
                            ], width=6)
                        ])
                    ])
                ], className="settings-card")
            ], width=6)
        ], className="mb-4"),
        
        # Additional Settings
        dbc.Row([
            # Notification Settings
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Notification Settings"),
                    dbc.CardBody([
                        dbc.Checklist(
                            id='notification-settings',
                            options=[
                                {'label': 'Email Alerts', 'value': 'email'},
                                {'label': 'SMS Notifications', 'value': 'sms'},
                                {'label': 'Desktop Notifications', 'value': 'desktop'},
                                {'label': 'Trading Signals', 'value': 'signals'},
                                {'label': 'System Warnings', 'value': 'warnings'}
                            ],
                            value=['desktop', 'signals'],
                            inline=True
                        )
                    ])
                ])
            ], width=6),
            
            # Data Settings
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Data Management"),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Label("Data Retention (days):"),
                                dcc.Input(
                                    id='data-retention',
                                    type='number',
                                    value=365,
                                    min=30,
                                    max=1095,
                                    className="form-control"
                                )
                            ], width=6),
                            dbc.Col([
                                html.Label("Auto Backup:"),
                                dcc.Dropdown(
                                    id='auto-backup',
                                    options=[
                                        {'label': 'Daily', 'value': 'daily'},
                                        {'label': 'Weekly', 'value': 'weekly'},
                                        {'label': 'Monthly', 'value': 'monthly'},
                                        {'label': 'Disabled', 'value': 'disabled'}
                                    ],
                                    value='weekly',
                                    className="form-control"
                                )
                            ], width=6)
                        ])
                    ])
                ])
            ], width=6)
        ], className="mb-4"),
        
        # Action Buttons
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                dbc.Button([
                                    html.I(className="fas fa-save me-2"),
                                    "Save Settings"
                                ], color="primary", id="save-settings-btn", className="me-2"),
                                dbc.Button([
                                    html.I(className="fas fa-undo me-2"),
                                    "Reset to Defaults"
                                ], color="outline-secondary", id="reset-settings-btn", className="me-2"),
                                dbc.Button([
                                    html.I(className="fas fa-download me-2"),
                                    "Export Settings"
                                ], color="outline-info", id="export-settings-btn")
                            ], className="text-center")
                        ])
                    ])
                ])
            ], width=12)
        ])
    ], fluid=True)

def register_settings_callbacks(app):
    """Register callbacks for the settings page"""
    
    @app.callback(
        Output("save-settings-btn", "children"),
        [Input("save-settings-btn", "n_clicks")],
        prevent_initial_call=True
    )
    def save_settings(n_clicks):
        if n_clicks:
            logger.info("Settings saved")
            return [html.I(className="fas fa-check me-2"), "Settings Saved"]
        return [html.I(className="fas fa-save me-2"), "Save Settings"]
    
    @app.callback(
        Output("reset-settings-btn", "children"),
        [Input("reset-settings-btn", "n_clicks")],
        prevent_initial_call=True
    )
    def reset_settings(n_clicks):
        if n_clicks:
            logger.info("Settings reset to defaults")
            return [html.I(className="fas fa-check me-2"), "Settings Reset"]
        return [html.I(className="fas fa-undo me-2"), "Reset to Defaults"]
    
    @app.callback(
        Output("export-settings-btn", "children"),
        [Input("export-settings-btn", "n_clicks")],
        prevent_initial_call=True
    )
    def export_settings(n_clicks):
        if n_clicks:
            logger.info("Settings exported")
            return [html.I(className="fas fa-check me-2"), "Settings Exported"]
        return [html.I(className="fas fa-download me-2"), "Export Settings"] 