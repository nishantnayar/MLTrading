"""
Interactive chart callbacks for advanced chart features.
Handles technical indicators, zoom controls, and chart interactions.
"""

from dash import Input, Output, State, callback_context, html
import dash_bootstrap_components as dbc

from ..layouts.interactive_chart import InteractiveChartBuilder
from ..services.market_data_service import MarketDataService
from ..services.technical_indicators import TechnicalIndicatorService
from ...utils.logging_config import get_ui_logger
from ..utils.date_formatters import format_date_range

logger = get_ui_logger("interactive_chart_callbacks")


def register_interactive_chart_callbacks(app):
    """Register all interactive chart callbacks with the app."""

    chart_builder = InteractiveChartBuilder()
    market_service = MarketDataService()
    indicator_service = TechnicalIndicatorService()

    # NEW: Toggle advanced controls
    @app.callback(
        Output("advanced-chart-controls", "is_open"),
        [Input("chart-controls-toggle", "n_clicks")],
        [State("advanced-chart-controls", "is_open")],
        prevent_initial_call=True
    )


    def toggle_advanced_controls(n_clicks, is_open):
        """Toggle the advanced chart controls collapse."""
        if n_clicks:
            return not is_open
        return is_open

    # NEW: Chart type button handlers
    @app.callback(
        [Output("chart-type-store", "data"),
         Output("chart-type-candlestick", "outline"),
         Output("chart-type-ohlc", "outline"),
         Output("chart-type-line", "outline"),
         Output("chart-type-bar", "outline")],
        [Input("chart-type-candlestick", "n_clicks"),
         Input("chart-type-ohlc", "n_clicks"),
         Input("chart-type-line", "n_clicks"),
         Input("chart-type-bar", "n_clicks")],
        prevent_initial_call=True
    )


    def update_chart_type(*clicks):
        """Handle chart type button clicks."""
        ctx = callback_context
        if not ctx.triggered:
            return 'candlestick', False, True, True, True

        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
        chart_types = {
            'chart-type-candlestick': ('candlestick', False, True, True, True),
            'chart-type-ohlc': ('ohlc', True, False, True, True),
            'chart-type-line': ('line', True, True, False, True),
            'chart-type-bar': ('bar', True, True, True, False)
        }

        return chart_types.get(trigger_id, ('candlestick', False, True, True, True))

    # NEW: Quick indicator toggles
    @app.callback(
        [Output("overlay-indicators-store", "data"),
         Output("indicator-sma-btn", "outline"),
         Output("indicator-ema-btn", "outline"),
         Output("indicator-bollinger-btn", "outline")],
        [Input("indicator-sma-btn", "n_clicks"),
         Input("indicator-ema-btn", "n_clicks"),
         Input("indicator-bollinger-btn", "n_clicks")],
        [State("overlay-indicators-store", "data")],
        prevent_initial_call=True
    )


    def toggle_overlay_indicators(sma_clicks, ema_clicks, bb_clicks, current_indicators):
        """Toggle overlay indicators on/off."""
        ctx = callback_context
        if not ctx.triggered:
            return current_indicators or ['sma', 'ema'], False, False, True

        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
        indicators = set(current_indicators or ['sma', 'ema'])

        indicator_map = {
            'indicator-sma-btn': 'sma',
            'indicator-ema-btn': 'ema',
            'indicator-bollinger-btn': 'bollinger'
        }

        if trigger_id in indicator_map:
            indicator = indicator_map[trigger_id]
            if indicator in indicators:
                indicators.discard(indicator)
            else:
                indicators.add(indicator)

        indicators_list = list(indicators)
        return (indicators_list,
                'sma' not in indicators,
                'ema' not in indicators,
                'bollinger' not in indicators)

    # NEW: RSI toggle
    @app.callback(
        [Output("oscillator-indicators-store", "data"),
         Output("indicator-rsi-btn", "outline")],
        [Input("indicator-rsi-btn", "n_clicks")],
        [State("oscillator-indicators-store", "data")],
        prevent_initial_call=True
    )


    def toggle_rsi_indicator(rsi_clicks, current_oscillators):
        """Toggle RSI indicator on/off."""
        if not rsi_clicks:
            return current_oscillators or ['rsi'], False

        oscillators = set(current_oscillators or ['rsi'])
        if 'rsi' in oscillators:
            oscillators.discard('rsi')
        else:
            oscillators.add('rsi')

        oscillators_list = list(oscillators)
        return oscillators_list, 'rsi' not in oscillators

    # NEW: Volume display controls
    @app.callback(
        [Output("volume-display-store", "data"),
         Output("volume-hide-btn", "outline"),
         Output("volume-bars-btn", "outline"),
         Output("volume-bars-ma-btn", "outline"),
         Output("volume-toggle-btn", "outline")],
        [Input("volume-hide-btn", "n_clicks"),
         Input("volume-bars-btn", "n_clicks"),
         Input("volume-bars-ma-btn", "n_clicks"),
         Input("volume-toggle-btn", "n_clicks")],
        [State("volume-display-store", "data")],
        prevent_initial_call=True
    )


    def update_volume_display(*clicks):
        """Handle volume display button clicks."""
        ctx = callback_context
        if not ctx.triggered:
            return 'bars_ma', True, True, False, False

        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

        if trigger_id == 'volume-toggle-btn':
            # Quick toggle between hide and bars_ma
            current = clicks[-1] or 'bars_ma'
            new_mode = 'hide' if current != 'hide' else 'bars_ma'
        else:
            volume_modes = {
                'volume-hide-btn': 'hide',
                'volume-bars-btn': 'bars',
                'volume-bars-ma-btn': 'bars_ma'
            }
            new_mode = volume_modes.get(trigger_id, 'bars_ma')

        return (new_mode,
                new_mode != 'hide',      # hide outline
                new_mode != 'bars',      # bars outline
                new_mode != 'bars_ma',   # bars_ma outline
                new_mode == 'hide')      # toggle outline

    # NEW: Dynamic advanced indicator callbacks
    # This creates callbacks for all available indicators dynamically
    indicator_service_temp = TechnicalIndicatorService()
    chart_config = indicator_service_temp.get_indicator_config()

    # Get overlay indicators
    overlay_indicators = [key for key, config in chart_config.items() if config.get('type') == 'overlay']
    oscillator_indicators = [key for key, config in chart_config.items() if config.get('type') == 'oscillator']

    # Create a callback for overlay indicator buttons in advanced section
    if overlay_indicators:
        overlay_inputs = [Input(f"overlay-{ind}-btn", "n_clicks") for ind in overlay_indicators]
        overlay_outputs = [Output(f"overlay-{ind}-btn", "outline") for ind in overlay_indicators]

        @app.callback(
            [Output("overlay-indicators-store", "data", allow_duplicate=True)] + overlay_outputs,
            overlay_inputs,
            [State("overlay-indicators-store", "data")],
            prevent_initial_call=True
        )


        def toggle_advanced_overlay_indicators(*args):
            """Handle advanced overlay indicator toggles."""
            ctx = callback_context
            if not ctx.triggered:
                # Default state - SMA and EMA active
                default_indicators = ['sma', 'ema']
                outlines = [ind not in default_indicators for ind in overlay_indicators]
                return [default_indicators] + outlines

            # Get current state (last argument is the state)
            current_indicators = set(args[-1] or ['sma', 'ema'])

            # Find which button was clicked
            trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

            # Extract indicator name from button ID
            if trigger_id.startswith('overlay-') and trigger_id.endswith('-btn'):
                indicator = trigger_id[8:-4]  # Remove 'overlay-' and '-btn'

                if indicator in current_indicators:
                    current_indicators.discard(indicator)
                else:
                    current_indicators.add(indicator)

            indicators_list = list(current_indicators)
            outlines = [ind not in current_indicators for ind in overlay_indicators]

            return [indicators_list] + outlines

    # Create a callback for oscillator indicator buttons in advanced section
    if oscillator_indicators:
        oscillator_inputs = [Input(f"oscillator-{ind}-btn", "n_clicks") for ind in oscillator_indicators]
        oscillator_outputs = [Output(f"oscillator-{ind}-btn", "outline") for ind in oscillator_indicators]

        @app.callback(
            [Output("oscillator-indicators-store", "data", allow_duplicate=True)] + oscillator_outputs,
            oscillator_inputs,
            [State("oscillator-indicators-store", "data")],
            prevent_initial_call=True
        )


        def toggle_advanced_oscillator_indicators(*args):
            """Handle advanced oscillator indicator toggles."""
            ctx = callback_context
            if not ctx.triggered:
                # Default state - RSI active
                default_indicators = ['rsi']
                outlines = [ind not in default_indicators for ind in oscillator_indicators]
                return [default_indicators] + outlines

            # Get current state (last argument is the state)
            current_indicators = set(args[-1] or ['rsi'])

            # Find which button was clicked
            trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

            # Extract indicator name from button ID
            if trigger_id.startswith('oscillator-') and trigger_id.endswith('-btn'):
                indicator = trigger_id[11:-4]  # Remove 'oscillator-' and '-btn'

                if indicator in current_indicators:
                    current_indicators.discard(indicator)
                else:
                    current_indicators.add(indicator)

            indicators_list = list(current_indicators)
            outlines = [ind not in current_indicators for ind in oscillator_indicators]

            return [indicators_list] + outlines

    # Initial symbol options callback
    @app.callback(
        Output("symbol-search", "options"),
        [Input("symbol-search", "search_value"),
         Input("filtered-symbols-store", "data")],
        prevent_initial_call=False
    )


    def update_symbol_options(search_value, filtered_symbols):
        """Update symbol dropdown options based on search query and filtered symbols."""
        try:
            # Prioritize filtered symbols if available
            if filtered_symbols and len(filtered_symbols) > 0:
                # Get detailed info for filtered symbols
                all_symbols = market_service.get_available_symbols()
                symbols = [s for s in all_symbols if s['symbol'] in filtered_symbols][:20]

                # If user is searching, filter the already filtered symbols
                if search_value and len(search_value) >= 1:
                    symbols = [s for s in symbols
                             if search_value.upper() in s['symbol'].upper() or
                                search_value.upper() in s.get('company_name', '').upper()]

            elif not search_value or len(search_value) < 1:
                # Return top 10 symbols by default
                symbols = market_service.get_available_symbols()[:10]
            else:
                # Search for symbols matching the query
                symbols = market_service.search_symbols(search_value, limit=20)

            if not symbols:
                return [{"label": "No symbols found", "value": "", "disabled": True}]

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

            return options

        except Exception as e:
            logger.error(f"Error updating symbol options: {e}")
            return [{"label": "Error loading symbols", "value": "", "disabled": True}]

    @app.callback(
        Output("interactive-price-chart", "figure"),
        [
            Input("symbol-search", "value"),
            Input("chart-type-store", "data"),
            Input("overlay-indicators-store", "data"),
            Input("oscillator-indicators-store", "data"),
            Input("volume-display-store", "data"),
            Input("refresh-chart-btn", "n_clicks")
        ],
        prevent_initial_call=False
    )


    def update_interactive_chart(symbol, chart_type, overlay_indicators, oscillator_indicators, volume_display, refresh_clicks):
        """Update interactive chart with technical indicators."""
        try:
            # Use selected symbol or default to ADBE
            if not symbol:
                symbol = "ADBE"

            # Combine overlay and oscillator indicators
            # indicators = (overlay_indicators or []) + (oscillator_indicators or [])  # Currently unused

            # Get ALL available market data (no artificial date limit)
            # Let users see the complete data range they have
            df = market_service.get_all_available_data(symbol)

            if df is None or df.empty:
                return chart_builder._create_empty_chart(f"No data available for {symbol}")

            # Log actual data range for debugging
            if not df.empty and 'timestamp' in df.columns:
                actual_start = df['timestamp'].min()
                actual_end = df['timestamp'].max()

                # Debug: Log raw dates before formatting
                logger.info(f"Raw date range for {symbol}: {actual_start} to {actual_end}")

                data_range_str = format_date_range(actual_start, actual_end, "compact")
                logger.info(f"Chart data for {symbol}: {len(df)} records from {data_range_str}")

            # Determine volume display settings
            show_volume = volume_display and volume_display != "hide"
            color_by_price = True  # Always color by price for better visuals

            # Use indicators or default
            indicators = (overlay_indicators or []) + (oscillator_indicators or [])
            chart_indicators = indicators or []

            # Create advanced chart
            fig = chart_builder.create_advanced_price_chart(
                df=df,
                symbol=symbol,
                # indicators=chart_indicators,  # Currently unused
                show_volume=show_volume,
                chart_type=chart_type or 'candlestick',
                volume_display=volume_display or 'bars_ma',
                color_by_price=color_by_price
            )


            logger.info(f"Updated interactive chart for {symbol} with {len(chart_indicators)} indicators")
            return fig

        except Exception as e:
            logger.error(f"Error updating interactive chart: {e}")
            return chart_builder._create_empty_chart(f"Error loading chart: {str(e)}")

    @app.callback(
        Output("technical-analysis-summary", "children"),
        [
            Input("symbol-search", "value"),
            Input("overlay-indicators-store", "data"),
            Input("oscillator-indicators-store", "data")
        ],
        prevent_initial_call=True
    )


    def update_technical_analysis_summary(symbol, overlay_indicators, oscillator_indicators):
        """Update technical analysis summary."""
        try:
            if not symbol:
                symbol = "ADBE"

            # Combine indicators for analysis
            # indicators = (overlay_indicators or []) + (oscillator_indicators or [])  # Currently unused

            # Get recent market data for analysis
            df = market_service.get_market_data(symbol, days=30)

            if df is None or df.empty:
                return html.P(f"No data available for {symbol}", className="text-muted text-center")

            # Calculate basic technical indicators
            analysis_indicators = indicator_service.calculate_all_indicators(df)

            # Create summary cards
            current_price = df['close'].iloc[-1]
            price_change = ((current_price - df['close'].iloc[0]) / df['close'].iloc[0]) * 100

            summary_items = [
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("Current Price", className="text-muted mb-1"),
                            html.H5(f"${current_price:.2f}", className="text-primary mb-0")
                        ])
                    ])
                ], width=2),  # Reduced from 3 to 2 to make room for volume
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H6("30D Change", className="text-muted mb-1"),
                            html.H5(f"{price_change:+.2f}%",
                                   className="text-success" if price_change >= 0 else "text-danger")
                        ])
                    ])
                ], width=2),  # Reduced from 3 to 2 to make room for volume
            ]

            # Add RSI if available
            if 'rsi' in analysis_indicators:
                rsi_value = analysis_indicators['rsi'].iloc[-1]
                rsi_color = "text-danger" if rsi_value > 70 else "text-success" if rsi_value < 30 else "text-warning"
                summary_items.append(
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H6("RSI(14)", className="text-muted mb-1"),
                                html.H5(f"{rsi_value:.1f}", className=f"{rsi_color} mb-0")
                            ])
                        ])
                    ], width=2)  # Changed from 3 to 2 for consistency
                )

            # Add volume analysis
            if 'volume' in df.columns:
                current_volume = df['volume'].iloc[-1]
                avg_volume = df['volume'].rolling(window=20).mean().iloc[-1]
                volume_ratio = (current_volume / avg_volume) if avg_volume > 0 else 0

                # Format volume in millions/billions


                def format_volume(vol):
                    if vol >= 1e9:
                        return f"{vol/1e9:.1f}B"
                    elif vol >= 1e6:
                        return f"{vol/1e6:.1f}M"
                    elif vol >= 1e3:
                        return f"{vol/1e3:.1f}K"
                    else:
                        return f"{vol:.0f}"

                volume_color = "text-success" if volume_ratio > 1.5 else "text-warning" if volume_ratio > 0.8 else "text-muted"

                summary_items.append(
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H6("Volume", className="text-muted mb-1"),
                                html.H5(format_volume(current_volume), className=f"{volume_color} mb-0"),
                                html.Small(f"{volume_ratio:.1f}x avg", className="text-muted")
                            ])
                        ])
                    ], width=2)
                )

            # Add trend analysis
            if 'sma_20' in analysis_indicators:
                sma_20 = analysis_indicators['sma_20'].iloc[-1]
                trend = "Bullish" if current_price > sma_20 else "Bearish"
                trend_color = "text-success" if trend == "Bullish" else "text-danger"
                summary_items.append(
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H6("Trend", className="text-muted mb-1"),
                                html.H5(trend, className=f"{trend_color} mb-0")
                            ])
                        ])
                    ], width=2)
                )

            return dbc.Row(summary_items)

        except Exception as e:
            logger.error(f"Error updating technical analysis summary: {e}")
            return html.P(f"Error loading analysis: {str(e)}", className="text-danger text-center")

