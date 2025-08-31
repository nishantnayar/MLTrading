"""
Symbol comparison callback functions for the dashboard.
Handles side-by-side symbol analysis and comparison charts.
"""

import plotly.graph_objs as go
import dash
from dash import Input, Output, html, State, callback_context, dcc
import dash_bootstrap_components as dbc

from ..config import CHART_COLORS
from ..layouts.chart_components import create_empty_chart
from ..services.market_data_service import MarketDataService
from ...utils.logging_config import get_ui_logger

logger = get_ui_logger("comparison_callbacks")
data_service = MarketDataService()


def register_comparison_callbacks(app):
    """Register all comparison-related callbacks with the app"""

    # Populate comparison symbol dropdowns
    @app.callback(
        [Output("comparison-symbol-1", "options"),
         Output("comparison-symbol-2", "options"),
         Output("comparison-symbol-3", "options")],
        [Input("filtered-symbols-store", "data")],
        prevent_initial_call=False
    )
    def update_comparison_symbol_options(filtered_symbols):
        """Update comparison symbol dropdown options"""
        try:
            # Use filtered symbols if available, otherwise get all symbols
            if filtered_symbols and len(filtered_symbols) > 0:
                # Get detailed info for filtered symbols
                all_symbols = data_service.get_available_symbols()
                symbols = [s for s in all_symbols if s['symbol'] in filtered_symbols][:50]
            else:
                # Get top 50 symbols by default
                symbols = data_service.get_available_symbols()[:50]

            if not symbols:
                options = [{"label": "No symbols available", "value": "", "disabled": True}]
                return options, options, options

            # Format options for dropdown
            options = []
            for symbol_data in symbols:
                symbol = symbol_data.get('symbol', '')
                company_name = symbol_data.get('company_name', '')

                if company_name and company_name != symbol:
                    label = f"{symbol} - {company_name}"
                else:
                    label = symbol

                options.append({"label": label, "value": symbol})

            return options, options, options

        except Exception as e:
            logger.error(f"Error updating comparison symbol options: {e}")
            error_options = [{"label": "Error loading symbols", "value": "", "disabled": True}]
            return error_options, error_options, error_options

    @app.callback(
        Output("comparison-results", "children"),
        [Input("compare-symbols-btn", "n_clicks"),
         Input("clear-comparison-btn", "n_clicks")],
        [State("comparison-symbol-1", "value"),
         State("comparison-symbol-2", "value"),
         State("comparison-symbol-3", "value")],
        prevent_initial_call=True
    )
    def update_comparison_results(compare_clicks, clear_clicks, symbol1, symbol2, symbol3):
        """Update comparison results based on selected symbols"""
        try:
            ctx = callback_context
            if not ctx.triggered:
                return dash.no_update

            trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

            # Handle clear button
            if trigger_id == "clear-comparison-btn":
                return html.Div([
                    html.I(className="fas fa-chart-bar fa-3x text-muted mb-3"),
                    html.H5("Ready to Compare", className="text-muted"),
                    html.P("Select 2-3 symbols above and click 'Compare' to see detailed side-by-side analysis",
                           className="text-muted")
                ], className="text-center py-5")

            # Handle compare button
            if trigger_id == "compare-symbols-btn":
                if not symbol1 or not symbol2:
                    return dbc.Alert(
                        "Please select at least 2 symbols to compare.",
                        color="warning",
                        className="text-center"
                    )

                # Collect selected symbols
                symbols = [symbol1, symbol2]
                if symbol3:
                    symbols.append(symbol3)

                # Generate comparison results
                return create_symbol_comparison_layout(symbols)

            return dash.no_update

        except Exception as e:
            logger.error(f"Error updating comparison results: {e}")
            return dbc.Alert(
                "Error generating comparison. Please try again.",
                color="danger",
                className="text-center"
            )


def create_symbol_comparison_layout(symbols):
    """Create the comparison layout for selected symbols"""
    try:
        comparison_components = []

        # Header with symbol list
        comparison_components.append(
            dbc.Row([
                dbc.Col([
                    html.H4([
                        html.I(className="fas fa-chart-line me-2"),
                        f"Comparing: {' vs '.join(symbols)}"
                    ], className="text-primary mb-4")
                ], width=12)
            ])
        )

        # Price comparison chart
        price_chart = create_price_comparison_chart(symbols)
        comparison_components.append(
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.H5([
                                html.I(className="fas fa-chart-line me-2"),
                                "Price Performance Comparison (30 Days)"
                            ], className="mb-0")
                        ]),
                        dbc.CardBody([
                            dcc.Graph(figure=price_chart, style={'height': '400px'})
                        ], className="p-0")
                    ])
                ], width=12)
            ], className="mb-4")
        )

        # Metrics comparison table
        metrics_table = create_metrics_comparison_table(symbols)
        comparison_components.append(
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.H5([
                                html.I(className="fas fa-table me-2"),
                                "Key Metrics Comparison"
                            ], className="mb-0")
                        ]),
                        dbc.CardBody([
                            metrics_table
                        ])
                    ])
                ], width=12)
            ], className="mb-4")
        )

        # Volume comparison chart
        volume_chart = create_volume_comparison_chart(symbols)
        comparison_components.append(
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader([
                            html.H5([
                                html.I(className="fas fa-chart-bar me-2"),
                                "Volume Comparison (7 Days)"
                            ], className="mb-0")
                        ]),
                        dbc.CardBody([
                            dcc.Graph(figure=volume_chart, style={'height': '300px'})
                        ], className="p-0")
                    ])
                ], width=12)
            ])
        )

        return comparison_components

    except Exception as e:
        logger.error(f"Error creating comparison layout: {e}")
        return dbc.Alert(
            f"Error creating comparison layout: {str(e)}",
            color="danger"
        )


def create_price_comparison_chart(symbols):
    """Create price comparison chart for multiple symbols"""
    try:
        fig = go.Figure()

        colors = [CHART_COLORS['primary'], CHART_COLORS['success'], CHART_COLORS['warning']]

        for i, symbol in enumerate(symbols):
            # Get 30 days of data for each symbol
            market_data = data_service.get_market_data(symbol, days=30)

            if not market_data.empty:
                # Normalize prices to percentage change from first day
                first_price = market_data['close'].iloc[0]
                normalized_prices = ((market_data['close'] / first_price) - 1) * 100

                fig.add_trace(go.Scatter(
                    x=market_data['timestamp'],
                    y=normalized_prices,
                    mode='lines',
                    name=symbol,
                    line=dict(color=colors[i % len(colors)], width=2),
                    hovertemplate=f'<b>{symbol}</b><br>Date: %{{x}}<br>Change: %{{y:.2f}}%<extra></extra>'
                ))

        fig.update_layout(
            title="Normalized Price Performance (%)",
            xaxis_title="Date",
            yaxis_title="Price Change (%)",
            template='plotly_white',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            hovermode='x unified'
        )

        return fig

    except Exception as e:
        logger.error(f"Error creating price comparison chart: {e}")
        return create_empty_chart("Error Loading Price Comparison")


def create_volume_comparison_chart(symbols):
    """Create volume comparison chart"""
    try:
        fig = go.Figure()

        colors = [CHART_COLORS['info'], CHART_COLORS['warning'], CHART_COLORS['danger']]

        for i, symbol in enumerate(symbols):
            market_data = data_service.get_market_data(symbol, days=7)

            if not market_data.empty:
                fig.add_trace(go.Bar(
                    x=market_data['timestamp'],
                    y=market_data['volume'],
                    name=symbol,
                    marker_color=colors[i % len(colors)],
                    hovertemplate=f'<b>{symbol}</b><br>Date: %{{x}}<br>Volume: %{{y:,.0f}}<extra></extra>'
                ))

        fig.update_layout(
            title="Volume Comparison",
            xaxis_title="Date",
            yaxis_title="Volume",
            template='plotly_white',
            barmode='group',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        return fig

    except Exception as e:
        logger.error(f"Error creating volume comparison chart: {e}")
        return create_empty_chart("Error Loading Volume Comparison")


def create_metrics_comparison_table(symbols):
    """Create metrics comparison table"""
    try:
        # Calculate metrics for each symbol
        metrics_data = []

        for symbol in symbols:
            try:
                # Get latest price and change
                price_change = data_service.get_price_change(symbol, days=1)
                quality_metrics = data_service.get_data_quality_metrics(symbol)
                market_data = data_service.get_market_data(symbol, days=7)

                if price_change:
                    current_price = price_change.get('close', 0)
                    change_percent = price_change.get('change_percent', 0)
                    change = price_change.get('change', 0)
                else:
                    current_price = 0
                    change_percent = 0
                    change = 0

                avg_volume = market_data['volume'].mean() if not market_data.empty else 0

                metrics_data.append({
                    'Symbol': symbol,
                    'Current Price': f"${current_price:.2f}" if current_price else "N/A",
                    'Change ($)': f"${change:.2f}" if change else "N/A",
                    'Change (%)': f"{change_percent:.2f}%" if change_percent else "N/A",
                    'Avg Volume (7d)': f"{avg_volume:,.0f}" if avg_volume else "N/A",
                    'Data Points': quality_metrics.get('total_records', 0)
                })

            except Exception:
                metrics_data.append({
                    'Symbol': symbol,
                    'Current Price': "Error",
                    'Change ($)': "Error",
                    'Change (%)': "Error",
                    'Avg Volume (7d)': "Error",
                    'Data Points': "Error"
                })

        # Create table
        table_header = [
            html.Thead([
                html.Tr([
                    html.Th("Symbol"),
                    html.Th("Current Price"),
                    html.Th("Change ($)"),
                    html.Th("Change (%)"),
                    html.Th("Avg Volume (7d)"),
                    html.Th("Data Points")
                ])
            ])
        ]

        table_body = [
            html.Tbody([
                html.Tr([
                    html.Td(row['Symbol'], className="fw-bold"),
                    html.Td(row['Current Price']),
                    html.Td(row['Change ($)'], className="text-success" if "$" in str(row['Change ($)']) and float(
                        row['Change ($)'].replace('$', '')) > 0 else "text-danger" if "$" in str(
                        row['Change ($)']) else ""),
                    html.Td(row['Change (%)'], className="text-success" if "%" in str(row['Change (%)']) and float(
                        row['Change (%)'].replace('%', '')) > 0 else "text-danger" if "%" in str(
                        row['Change (%)']) else ""),
                    html.Td(row['Avg Volume (7d)']),
                    html.Td(row['Data Points'])
                ]) for row in metrics_data
            ])
        ]

        return dbc.Table(table_header + table_body, bordered=True, hover=True, responsive=True, striped=True)

    except Exception as e:
        logger.error(f"Error creating metrics table: {e}")
        return html.P("Error loading metrics comparison", className="text-danger")
