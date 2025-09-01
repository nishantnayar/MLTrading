"""
Trading Dashboard Layout
Integrates Alpaca trading functionality with the existing Dash UI
"""

import dash_bootstrap_components as dbc
from dash import html, dcc, dash_table
from datetime import datetime

from ..config import CARD_STYLE
from ...utils.logging_config import get_ui_logger

logger = get_ui_logger("trading_layout")


def create_trading_dashboard() -> html.Div:
    """Create the main trading dashboard"""

    return html.Div(id="trading-dashboard", children=[
        # Connection Status Header
        dbc.Alert(
            id="trading-connection-status",
            children="🔌 Checking Alpaca connection...",
            color="info",
            className="mb-4"
        ),

        # Trading Controls Row
        dbc.Row([
            # Account Info Card
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("📊 Account Information"),
                    dbc.CardBody([
                        html.Div(id="account-info-display"),
                        dbc.Button(
                            "Refresh Account",
                            id="refresh-account-btn",
                            color="primary",
                            size="sm",
                            className="mt-2"
                        )
                    ])
                ], style=CARD_STYLE)
            ], width=6),

            # Quick Trade Card
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("⚡ Quick Trade"),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Symbol"),
                                dbc.Input(
                                    id="trade-symbol-input",
                                    placeholder="e.g., AAPL",
                                    type="text"
                                )
                            ], width=6),
                            dbc.Col([
                                dbc.Label("Quantity"),
                                dbc.Input(
                                    id="trade-quantity-input",
                                    placeholder="100",
                                    type="number",
                                    min=1
                                )
                            ], width=6)
                        ], className="mb-3"),

                        dbc.Row([
                            dbc.Col([
                                dbc.Button(
                                    "🟢 BUY",
                                    id="buy-btn",
                                    color="success",
                                    className="w-100"
                                )
                            ], width=6),
                            dbc.Col([
                                dbc.Button(
                                    "🔴 SELL",
                                    id="sell-btn",
                                    color="danger",
                                    className="w-100"
                                )
                            ], width=6)
                        ])
                    ])
                ], style=CARD_STYLE)
            ], width=6)
        ], className="mb-4"),

        # Positions and Orders Row
        dbc.Row([
            # Current Positions
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        "📈 Current Positions",
                        dbc.Button(
                            "🔄",
                            id="refresh-positions-btn",
                            color="outline-primary",
                            size="sm",
                            className="float-end"
                        )
                    ]),
                    dbc.CardBody([
                        html.Div(id="positions-table")
                    ])
                ], style=CARD_STYLE)
            ], width=12)
        ], className="mb-4"),

        # Recent Orders
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader([
                        "📋 Recent Orders",
                        dbc.Button(
                            "🔄",
                            id="refresh-orders-btn",
                            color="outline-primary",
                            size="sm",
                            className="float-end"
                        )
                    ]),
                    dbc.CardBody([
                        html.Div(id="orders-table")
                    ])
                ], style=CARD_STYLE)
            ], width=12)
        ], className="mb-4"),

        # Trading Activity Log
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("📝 Trading Activity Log"),
                    dbc.CardBody([
                        html.Div(
                            id="trading-log",
                            style={
                                "height": "300px",
                                "overflow-y": "auto",
                                "background-color": "#f8f9fa",
                                "padding": "10px",
                                "border-radius": "5px"
                            }
                        )
                    ])
                ], style=CARD_STYLE)
            ], width=12)
        ]),

        # Hidden components for data storage
        dcc.Store(id="trading-data-store"),
        dcc.Interval(
            id="trading-data-interval",
            interval=5000,  # Update every 5 seconds
            n_intervals=0
        ),

        # Modal for order confirmation
        dbc.Modal([
            dbc.ModalHeader("Confirm Order"),
            dbc.ModalBody(id="order-confirmation-body"),
            dbc.ModalFooter([
                dbc.Button("Cancel", id="cancel-order-modal", color="secondary"),
                dbc.Button("Confirm Order", id="confirm-order-modal", color="primary")
            ])
        ], id="order-confirmation-modal", is_open=False)

    ])


def create_account_info_display(account_info: dict) -> html.Div:
    """Create account information display"""
    if not account_info:
        return html.P("Unable to load account information", className="text-muted")

    return html.Div([
        dbc.Row([
            dbc.Col([
                html.H6("Portfolio Value", className="text-muted mb-1"),
                html.H4(f"${account_info.get('portfolio_value', 0):,.2f}", className="text-primary")
            ], width=6),
            dbc.Col([
                html.H6("Buying Power", className="text-muted mb-1"),
                html.H4(f"${account_info.get('buying_power', 0):,.2f}", className="text-success")
            ], width=6)
        ], className="mb-3"),

        dbc.Row([
            dbc.Col([
                html.H6("Cash", className="text-muted mb-1"),
                html.H5(f"${account_info.get('cash', 0):,.2f}")
            ], width=6),
            dbc.Col([
                html.H6("Day Trades", className="text-muted mb-1"),
                html.H5(f"{account_info.get('day_trade_count', 0)}")
            ], width=6)
        ]),

        # Account status badges
        html.Div([
            dbc.Badge(
                "Pattern Day Trader" if account_info.get('pattern_day_trader', False) else "Regular Account",
                color="warning" if account_info.get('pattern_day_trader', False) else "info",
                className="me-2"
            ),
            dbc.Badge(
                "Account Blocked" if account_info.get('account_blocked', False) else "Active",
                color="danger" if account_info.get('account_blocked', False) else "success"
            )
        ], className="mt-2")
    ])


def create_positions_table(positions: list) -> html.Div:
    """Create positions table"""
    if not positions:
        return html.P("No current positions", className="text-muted text-center")

    # Prepare data for dash_table
    columns = [
        {"name": "Symbol", "id": "symbol"},
        {"name": "Qty", "id": "qty", "type": "numeric"},
        {"name": "Avg Price", "id": "avg_entry_price", "type": "numeric", "format": {"specifier": "$.2f"}},
        {"name": "Market Value", "id": "market_value", "type": "numeric", "format": {"specifier": "$.2f"}},
        {"name": "P&L", "id": "unrealized_pl", "type": "numeric", "format": {"specifier": "$.2f"}},
        {"name": "P&L %", "id": "unrealized_plpc", "type": "numeric", "format": {"specifier": ".2%"}}
    ]

    return dash_table.DataTable(
        data=positions,
        columns=columns,
        style_cell={'textAlign': 'center'},
        style_data_conditional=[
            {
                'if': {'filter_query': '{unrealized_pl} > 0'},
                'backgroundColor': '#d4edda',
                'color': 'black',
            },
            {
                'if': {'filter_query': '{unrealized_pl} < 0'},
                'backgroundColor': '#f8d7da',
                'color': 'black',
            }
        ],
        style_header={
            'backgroundColor': '#e9ece',
            'fontWeight': 'bold'
        }
    )


def create_orders_table(orders: list) -> html.Div:
    """Create orders table"""
    if not orders:
        return html.P("No recent orders", className="text-muted text-center")

    # Prepare data for dash_table
    columns = [
        {"name": "Symbol", "id": "symbol"},
        {"name": "Side", "id": "side"},
        {"name": "Qty", "id": "qty", "type": "numeric"},
        {"name": "Status", "id": "status"},
        {"name": "Type", "id": "order_type"},
        {"name": "Filled Price", "id": "filled_avg_price", "type": "numeric", "format": {"specifier": "$.2f"}},
        {"name": "Submitted", "id": "submitted_at"}
    ]

    # Format datetime for display
    for order in orders:
        if order.get('submitted_at'):
            try:
                dt = datetime.fromisoformat(order['submitted_at'].replace('Z', '+00:00'))
                order['submitted_at'] = dt.strftime('%m/%d %H:%M')
            except Exception:
                pass

    return dash_table.DataTable(
        data=orders[:10],  # Show last 10 orders
        columns=columns,
        style_cell={'textAlign': 'center'},
        style_data_conditional=[
            {
                'if': {'filter_query': '{status} = filled'},
                'backgroundColor': '#d4edda',
                'color': 'black',
            },
            {
                'if': {'filter_query': '{status} = canceled'},
                'backgroundColor': '#f8d7da',
                'color': 'black',
            }
        ],
        style_header={
            'backgroundColor': '#e9ece',
            'fontWeight': 'bold'
        }
    )


def format_trading_log_message(message: str, level: str = "info") -> html.Div:
    """Format a trading log message"""

    color_map = {
        "info": "text-info",
        "success": "text-success",
        "warning": "text-warning",
        "error": "text-danger"
    }

    timestamp = datetime.now().strftime("%H:%M:%S")

    return html.Div([
        html.Span(f"[{timestamp}] ", className="text-muted"),
        html.Span(message, className=color_map.get(level, "text-dark"))
    ], className="mb-1")
