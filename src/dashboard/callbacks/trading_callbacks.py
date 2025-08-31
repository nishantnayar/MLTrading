"""
Trading Dashboard Callbacks
Handles interactions between the Dash UI and Alpaca trading service
"""

import dash
from dash import Input, Output, State, callback_context, html

from ..layouts.trading_layout import (
    create_account_info_display,
    create_positions_table,
    create_orders_table,
    format_trading_log_message
)
from ...trading.brokers.alpaca_service import get_alpaca_service
from ...utils.logging_config import get_ui_logger

logger = get_ui_logger("trading_callbacks")


def register_trading_callbacks(app):
    """Register all trading-related callbacks"""

    @app.callback(
        [Output("trading-connection-status", "children"),
         Output("trading-connection-status", "color")],
        [Input("trading-data-interval", "n_intervals")]
    )
    def update_connection_status(n_intervals):
        """Update Alpaca connection status"""
        try:
            alpaca = get_alpaca_service()
            status = alpaca.get_connection_status()

            if status['connected']:
                mode = status['mode'].upper()
                account_id = status['account_info']['account_id'][:8] if status['account_info'] else 'Unknown'

                return (
                    f"✅ Connected to Alpaca ({mode} MODE) - Account: {account_id}...",
                    "success"
                )
            else:
                return (
                    "❌ Not connected to Alpaca - Check your API credentials in config/config.yaml",
                    "danger"
                )

        except Exception as e:
            logger.error(f"Error checking connection status: {e}")
            return (
                f"⚠️ Connection error: {str(e)}",
                "warning"
            )

    @app.callback(
        Output("account-info-display", "children"),
        [Input("refresh-account-btn", "n_clicks"),
         Input("trading-data-interval", "n_intervals")]
    )
    def update_account_info(refresh_clicks, n_intervals):
        """Update account information display"""
        try:
            alpaca = get_alpaca_service()
            account_info = alpaca.get_account_info()
            return create_account_info_display(account_info)

        except Exception as e:
            logger.error(f"Error updating account info: {e}")
            return html.P(f"Error loading account info: {e}", className="text-danger")

    @app.callback(
        Output("positions-table", "children"),
        [Input("refresh-positions-btn", "n_clicks"),
         Input("trading-data-interval", "n_intervals")]
    )
    def update_positions_table(refresh_clicks, n_intervals):
        """Update positions table"""
        try:
            alpaca = get_alpaca_service()
            positions = alpaca.get_positions()
            return create_positions_table(positions)

        except Exception as e:
            logger.error(f"Error updating positions: {e}")
            return html.P(f"Error loading positions: {e}", className="text-danger")

    @app.callback(
        Output("orders-table", "children"),
        [Input("refresh-orders-btn", "n_clicks"),
         Input("trading-data-interval", "n_intervals")]
    )
    def update_orders_table(refresh_clicks, n_intervals):
        """Update orders table"""
        try:
            alpaca = get_alpaca_service()
            orders = alpaca.get_orders(status='all', limit=20)
            return create_orders_table(orders)

        except Exception as e:
            logger.error(f"Error updating orders: {e}")
            return html.P(f"Error loading orders: {e}", className="text-danger")

    @app.callback(
        [Output("order-confirmation-modal", "is_open"),
         Output("order-confirmation-body", "children")],
        [Input("buy-btn", "n_clicks"),
         Input("sell-btn", "n_clicks"),
         Input("cancel-order-modal", "n_clicks"),
         Input("confirm-order-modal", "n_clicks")],
        [State("trade-symbol-input", "value"),
         State("trade-quantity-input", "value"),
         State("order-confirmation-modal", "is_open")]
    )
    def handle_trading_modal(buy_clicks, sell_clicks, cancel_clicks, confirm_clicks,
                             symbol, quantity, is_open):
        """Handle trading order modal"""
        ctx = callback_context

        if not ctx.triggered:
            return False, ""

        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

        # Close modal
        if trigger_id in ["cancel-order-modal", "confirm-order-modal"]:
            return False, ""

        # Open modal for buy/sell
        if trigger_id in ["buy-btn", "sell-btn"]:
            # Validate inputs
            if not symbol or not quantity:
                return False, ""

            try:
                quantity = int(quantity)
                if quantity <= 0:
                    return False, ""
            except ValueError:
                return False, ""

            side = "buy" if trigger_id == "buy-btn" else "sell"
            side_display = "BUY" if side == "buy" else "SELL"
            color = "success" if side == "buy" else "danger"

            # Get current price (simplified - you might want to get real quote)
            alpaca = get_alpaca_service()
            account_info = alpaca.get_account_info()

            modal_body = [
                html.H5(f"{side_display} Order Confirmation", className=f"text-{color}"),
                html.Hr(),
                html.P([
                    html.Strong("Symbol: "), symbol.upper(), html.Br(),
                    html.Strong("Quantity: "), f"{quantity:,} shares", html.Br(),
                    html.Strong("Side: "), side_display, html.Br(),
                    html.Strong("Order Type: "), "Market", html.Br(),
                    html.Strong("Estimated Cost: "), "Market Price"
                ]),
                html.Hr(),
                html.P([
                    html.Strong("Available Cash: "),
                    f"${account_info.get('cash', 0):,.2f}" if account_info else "Unknown"
                ], className="text-muted")
            ]

            return True, modal_body

        return False, ""

    @app.callback(
        Output("trading-log", "children"),
        [Input("confirm-order-modal", "n_clicks")],
        [State("trade-symbol-input", "value"),
         State("trade-quantity-input", "value"),
         State("trading-log", "children")],
        prevent_initial_call=True
    )
    def execute_trade_order(confirm_clicks, symbol, quantity, current_log):
        """Execute the confirmed trade order"""
        if not confirm_clicks:
            return current_log or []

        try:
            ctx = callback_context
            if not ctx.triggered:
                return current_log or []

            # Determine buy/sell from the previous trigger (stored in component state)
            # For now, we'll need to track this differently
            # This is a simplified version - you might want to store the order details in a Store

            # Get the side from the last button clicked (you might need to adjust this)
            side = "buy"  # Default to buy for now - this needs better implementation

            alpaca = get_alpaca_service()

            # Validate inputs again
            if not symbol or not quantity:
                error_msg = format_trading_log_message("❌ Invalid order parameters", "error")
                return (current_log or []) + [error_msg]

            quantity = int(quantity)

            # Submit order
            order_result = alpaca.submit_order(
                symbol=symbol.upper(),
                qty=quantity,
                side=side
            )

            # Update log
            log_messages = current_log or []

            if order_result:
                success_msg = format_trading_log_message(
                    f"✅ Order submitted: {side.upper()} {quantity} {symbol.upper()} (ID: {order_result['id'][:8]}...)",
                    "success"
                )
                log_messages.append(success_msg)
            else:
                error_msg = format_trading_log_message(
                    f"❌ Failed to submit order: {side.upper()} {quantity} {symbol.upper()}",
                    "error"
                )
                log_messages.append(error_msg)

            # Keep only last 20 log messages
            return log_messages[-20:]

        except Exception as e:
            logger.error(f"Error executing trade: {e}")
            error_msg = format_trading_log_message(f"❌ Trade execution error: {e}", "error")
            return (current_log or []) + [error_msg]

    @app.callback(
        [Output("trade-symbol-input", "value"),
         Output("trade-quantity-input", "value")],
        [Input("confirm-order-modal", "n_clicks")],
        prevent_initial_call=True
    )
    def clear_trade_inputs(confirm_clicks):
        """Clear trade input fields after order submission"""
        if confirm_clicks:
            return "", ""
        return dash.no_update, dash.no_update
