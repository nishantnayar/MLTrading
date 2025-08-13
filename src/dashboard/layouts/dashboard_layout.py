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
                ], className="mb-4"),
                
                # Refresh Button
                dbc.Row([
                    dbc.Col([
                        dbc.Button(
                            "Refresh Statistics",
                            id="refresh-stats-btn",
                            color="primary",
                            className="w-100"
                        )
                    ], width=12)
                ], className="mb-3")
            ], className="p-4")
        ], style=CARD_STYLE_NONE),
        label="Overview",
        tab_id="overview-tab"
    )


def create_charts_tab():
    """Create the charts tab content"""
    return dbc.Tab(
        dbc.Card([
            dbc.CardBody([
                # Distribution Charts Row
                dbc.Row([
                    dbc.Col([
                        create_chart_card("sector-chart", "450px")
                    ], width=6),
                    dbc.Col([
                        create_chart_card("industry-chart", "450px")
                    ], width=6)
                ], className="mb-3"),
                
                # Filter Display Row
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.Span("Current Filters: ", className="text-muted"),
                            html.Span("Sector: ", className="text-muted"),
                            html.Span("All Sectors", id="current-sector-filter", className="badge bg-primary me-2"),
                            html.Span("Industry: ", className="text-muted"),
                            html.Span("All Industries", id="current-industry-filter", className="badge bg-info")
                        ], className="text-center")
                    ], width=12)
                ], className="mb-3"),
                
                # Chart Controls Row
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H3("Chart Controls", className="text-center mb-3"),
                                dbc.Row([
                                    dbc.Col([
                                        dbc.Row([
                                            dbc.Col([
                                                html.P("Select Symbol:", className="text-primary-emphasis mb-0")
                                            ], width=3),
                                            dbc.Col([
                                                dcc.Dropdown(
                                                    id="symbol-dropdown",
                                                    options=[],
                                                    value=DEFAULT_SYMBOL,
                                                    className="mb-0"
                                                )
                                            ], width=9)
                                        ], className="align-items-center")
                                    ], width=5),
                                    dbc.Col([
                                        dbc.Row([
                                            dbc.Col([
                                                html.P("Time Range:", className="text-primary-emphasis mb-0")
                                            ], width=5),
                                            dbc.Col([
                                                dcc.Dropdown(
                                                    id="time-range-dropdown",
                                                    options=TIME_RANGE_OPTIONS,
                                                    value=DEFAULT_TIME_RANGE,
                                                    className="mb-0"
                                                )
                                            ], width=7)
                                        ], className="align-items-center")
                                    ], width=3),
                                    dbc.Col([
                                        dbc.Button("Refresh Data", id="refresh-data-btn", color="primary", size="sm", className="w-75")
                                    ], width=4, className="d-flex align-items-end justify-content-center")
                                ], className="align-items-end")
                            ], className="p-3")
                        ], style=CARD_STYLE_NONE)
                    ], width=12)
                ], className="mb-3"),
                
                # Price Chart Row
                dbc.Row([
                    dbc.Col([
                        create_chart_card("price-chart", DEFAULT_CHART_HEIGHT)
                    ], width=12)
                ], className="mb-3")
            ], className="p-0")
        ], style=CARD_STYLE_NONE),
        label="Charts",
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