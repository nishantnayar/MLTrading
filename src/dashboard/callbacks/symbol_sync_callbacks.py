"""
Symbol Synchronization Callbacks
Handles synchronization of selected symbols across all dashboard tabs
"""

from dash import Input, Output, State, callback_context, dash
import dash.dependencies
import json


def register_symbol_sync_callbacks(app):
    """Register symbol synchronization callbacks with the app"""

    @app.callback(
        [Output("selected-symbol-store", "data"),
         Output("symbol-search", "value"),
         Output("detailed-analysis-symbol", "value"),
         Output("comparison-symbol-1", "value"),
         Output("main-tabs", "active_tab")],
        [Input("symbol-search", "value"),
         Input("detailed-analysis-symbol", "value"),
         Input("comparison-symbol-1", "value"),
         Input({"type": "analyze-symbol-btn", "index": dash.dependencies.ALL}, "n_clicks"),
         Input({"type": "compare-symbol-btn", "index": dash.dependencies.ALL}, "n_clicks")],
        [State("selected-symbol-store", "data"),
         State("main-tabs", "active_tab")]
    )
    def sync_selected_symbol(overview_symbol, detailed_symbol, comparison_symbol, analyze_clicks, compare_clicks,
                             stored_symbol, current_tab):
        """
        Synchronize symbol selection across all tabs and handle overview button clicks.

        Handles both symbol dropdown changes and analyze/compare button clicks from overview.
        """

        # Handle initial load
        if not callback_context.triggered:
            return _handle_initial_load(stored_symbol, current_tab)

        # Get trigger information
        triggered_id = callback_context.triggered[0]["prop_id"].split(".")[0]
        trigger_value = callback_context.triggered[0]["value"]

        # Handle button clicks from overview
        button_result = _handle_button_clicks(triggered_id, trigger_value)
        if button_result:
            return button_result

        # Handle dropdown changes
        dropdown_result = _handle_dropdown_changes(
            triggered_id, overview_symbol, detailed_symbol, comparison_symbol, stored_symbol, current_tab
        )
        if dropdown_result:
            return dropdown_result

        # Maintain current values
        return _maintain_current_values(overview_symbol, detailed_symbol, comparison_symbol, stored_symbol, current_tab)

    @app.callback(
        Output("comparison-symbol-2", "value"),
        [Input("selected-symbol-store", "data")],
        prevent_initial_call=True
    )
    def sync_comparison_symbol_2(selected_symbol):
        """Set comparison symbol 2 to a different default when main symbol changes."""
        if selected_symbol == "AAPL":
            return "MSFT"
        elif selected_symbol == "MSFT":
            return "GOOGL"
        else:
            return "AAPL"

    @app.callback(
        Output("comparison-symbol-3", "value"),
        [Input("selected-symbol-store", "data")],
        prevent_initial_call=True
    )
    def sync_comparison_symbol_3(selected_symbol):
        """Set comparison symbol 3 to a different default when main symbol changes."""
        if selected_symbol == "AAPL":
            return "TSLA"
        elif selected_symbol == "MSFT":
            return "NVDA"
        else:
            return "MSFT"


def _handle_initial_load(stored_symbol, current_tab):
    """Handle initial callback load"""
    default_symbol = stored_symbol or "AAPL"
    return default_symbol, default_symbol, default_symbol, default_symbol, current_tab or "overview-tab"


def _handle_button_clicks(triggered_id, trigger_value):
    """Handle analyze/compare button clicks from overview"""
    try:
        btn_info = json.loads(triggered_id)
        if 'type' in btn_info and 'index' in btn_info:
            button_type = btn_info['type']
            symbol = btn_info['index']

            # Only proceed if this is actually a button click with n_clicks > 0
            if trigger_value is not None and trigger_value > 0:
                if button_type == "analyze-symbol-btn":
                    # Set symbol and navigate to charts tab
                    return symbol, symbol, symbol, symbol, "charts-tab"
                elif button_type == "compare-symbol-btn":
                    # Set symbol and navigate to comparison tab
                    return symbol, symbol, symbol, symbol, "comparison-tab"
    except (json.JSONDecodeError, KeyError, TypeError):
        # Not a button click, continue with dropdown logic
        pass
    return None


def _handle_dropdown_changes(triggered_id, overview_symbol, detailed_symbol, comparison_symbol, stored_symbol, current_tab):
    """Handle symbol dropdown changes"""
    new_symbol = None
    if triggered_id == "symbol-search" and overview_symbol:
        new_symbol = overview_symbol
    elif triggered_id == "detailed-analysis-symbol" and detailed_symbol:
        new_symbol = detailed_symbol
    elif triggered_id == "comparison-symbol-1" and comparison_symbol:
        new_symbol = comparison_symbol

    # If we have a new symbol, sync it across all dropdowns
    if new_symbol and new_symbol != stored_symbol:
        return new_symbol, new_symbol, new_symbol, new_symbol, current_tab or "overview-tab"
    return None


def _maintain_current_values(overview_symbol, detailed_symbol, comparison_symbol, stored_symbol, current_tab):
    """Maintain current symbol values when no changes needed"""
    current_overview = overview_symbol or stored_symbol or "AAPL"
    current_detailed = detailed_symbol or stored_symbol or "AAPL"
    current_comparison = comparison_symbol or stored_symbol or "AAPL"
    current_stored = stored_symbol or "AAPL"

    return current_stored, current_overview, current_detailed, current_comparison, current_tab or "overview-tab"
