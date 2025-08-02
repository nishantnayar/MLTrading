import dash
from dash import html, dcc, callback_context
import dash_bootstrap_components as dbc
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logging_config import get_ui_logger

# Initialize logger
logger = get_ui_logger("dashboard")

# Define the settings page layout
layout = dbc.Container([
    # Page Header
    dbc.Row([
        dbc.Col([
            html.H2("System Settings", className="text-center mb-4"),
            html.P("Configure trading parameters and system preferences", className="text-center text-muted")
        ])
    ], className="mb-4"),
    
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
                            html.Label("Log Level:"),
                            dcc.Dropdown(
                                id='log-level',
                                options=[
                                    {'label': 'DEBUG', 'value': 'DEBUG'},
                                    {'label': 'INFO', 'value': 'INFO'},
                                    {'label': 'WARNING', 'value': 'WARNING'},
                                    {'label': 'ERROR', 'value': 'ERROR'}
                                ],
                                value='INFO',
                                className="form-control"
                            )
                        ], width=6),
                        dbc.Col([
                            html.Label("Auto Refresh (seconds):"),
                            dcc.Input(
                                id='auto-refresh',
                                type='number',
                                value=30,
                                min=5,
                                max=300,
                                className="form-control"
                            )
                        ], width=6)
                    ], className="mb-3"),
                    dbc.Row([
                        dbc.Col([
                            html.Label("Theme:"),
                            dcc.Dropdown(
                                id='theme-selector',
                                options=[
                                    {'label': 'Light', 'value': 'light'},
                                    {'label': 'Dark', 'value': 'dark'},
                                    {'label': 'Auto', 'value': 'auto'}
                                ],
                                value='light',
                                className="form-control"
                            )
                        ], width=6),
                        dbc.Col([
                            html.Label("Notifications:"),
                            dbc.Checklist(
                                id='notifications',
                                options=[
                                    {'label': 'Enable Email Alerts', 'value': 'email'},
                                    {'label': 'Enable SMS Alerts', 'value': 'sms'},
                                    {'label': 'Enable Push Notifications', 'value': 'push'}
                                ],
                                value=['email'],
                                inline=True
                            )
                        ], width=6)
                    ])
                ])
            ], className="settings-card")
        ], width=6)
    ]),
    
    # Data Source Settings
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Data Source Configuration"),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Label("Primary Data Source:"),
                            dcc.Dropdown(
                                id='data-source',
                                options=[
                                    {'label': 'Yahoo Finance', 'value': 'yahoo'},
                                    {'label': 'Alpha Vantage', 'value': 'alphavantage'},
                                    {'label': 'IEX Cloud', 'value': 'iex'},
                                    {'label': 'Custom API', 'value': 'custom'}
                                ],
                                value='yahoo',
                                className="form-control"
                            )
                        ], width=6),
                        dbc.Col([
                            html.Label("API Key:"),
                            dcc.Input(
                                id='api-key',
                                type='password',
                                placeholder='Enter your API key',
                                className="form-control"
                            )
                        ], width=6)
                    ], className="mb-3"),
                    dbc.Row([
                        dbc.Col([
                            html.Label("Update Frequency (minutes):"),
                            dcc.Input(
                                id='update-frequency',
                                type='number',
                                value=5,
                                min=1,
                                max=60,
                                className="form-control"
                            )
                        ], width=6),
                        dbc.Col([
                            html.Label("Historical Data Days:"),
                            dcc.Input(
                                id='historical-days',
                                type='number',
                                value=365,
                                min=30,
                                max=3650,
                                className="form-control"
                            )
                        ], width=6)
                    ])
                ])
            ], className="settings-card")
        ], width=12)
    ]),
    
    # Action Buttons
    dbc.Row([
        dbc.Col([
            dbc.Button("Save Settings", color="success", className="me-2"),
            dbc.Button("Reset to Defaults", color="warning", className="me-2"),
            dbc.Button("Export Configuration", color="info", className="me-2"),
            dbc.Button("Import Configuration", color="secondary")
        ], className="text-center")
    ], className="mt-4")
], fluid=True) 