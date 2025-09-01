"""
Interactive chart callbacks - Refactored version
Breaking down the large register_interactive_chart_callbacks into smaller functions
"""

from dash import Input, Output, State, callback_context
from ..services.unified_data_service import MarketDataService
from ..services.technical_indicators import TechnicalIndicatorService
from ..layouts.interactive_chart import InteractiveChartBuilder
from ...utils.logging_config import get_ui_logger

logger = get_ui_logger("interactive_chart_callbacks")


def register_interactive_chart_callbacks(app):
    """Register all interactive chart callbacks with the app."""

    chart_builder = InteractiveChartBuilder()
    market_service = MarketDataService()
    indicator_service = TechnicalIndicatorService()

    # Register individual callback groups
    _register_chart_control_callbacks(app)
    _register_chart_type_callbacks(app)
    _register_indicator_callbacks(app, indicator_service)
    _register_volume_callbacks(app)
    _register_symbol_callbacks(app, market_service)
    _register_chart_update_callbacks(app, chart_builder, market_service)
    _register_technical_analysis_callbacks(app, market_service)


def _register_chart_control_callbacks(app):
    """Register chart control toggle callbacks"""
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


def _register_chart_type_callbacks(app):
    """Register chart type selection callbacks"""
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


def _register_indicator_callbacks(app, indicator_service):
    """Register indicator selection callbacks"""
    # Basic indicator toggles
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

    # RSI toggle
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

    # Dynamic advanced indicator callbacks
    _register_advanced_indicator_callbacks(app, indicator_service)


def _register_advanced_indicator_callbacks(app, indicator_service):
    """Register advanced indicator callbacks dynamically"""
    chart_config = indicator_service.get_indicator_config()

    # Get overlay indicators
    overlay_indicators = [key for key, config in chart_config.items() if config.get('type') == 'overlay']
    
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
                default_indicators = ['sma', 'ema']
                outlines = [ind not in default_indicators for ind in overlay_indicators]
                return [default_indicators] + outlines

            trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
            current_indicators = args[-1] or ['sma', 'ema']
            indicators = set(current_indicators)

            for ind in overlay_indicators:
                if trigger_id == f"overlay-{ind}-btn":
                    if ind in indicators:
                        indicators.discard(ind)
                    else:
                        indicators.add(ind)
                    break

            indicators_list = list(indicators)
            outlines = [ind not in indicators for ind in overlay_indicators]
            return [indicators_list] + outlines

    # Get oscillator indicators
    oscillator_indicators = [key for key, config in chart_config.items() if config.get('type') == 'oscillator']
    
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
                default_indicators = ['rsi']
                outlines = [ind not in default_indicators for ind in oscillator_indicators]
                return [default_indicators] + outlines

            trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
            current_oscillators = args[-1] or ['rsi']
            oscillators = set(current_oscillators)

            for ind in oscillator_indicators:
                if trigger_id == f"oscillator-{ind}-btn":
                    if ind in oscillators:
                        oscillators.discard(ind)
                    else:
                        oscillators.add(ind)
                    break

            oscillators_list = list(oscillators)
            outlines = [ind not in oscillators for ind in oscillator_indicators]
            return [oscillators_list] + outlines


def _register_volume_callbacks(app):
    """Register volume display callbacks"""
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
            current_mode = clicks[-1] if len(clicks) > 0 else 'bars_ma'
            new_mode = 'hide' if current_mode != 'hide' else 'bars_ma'
        else:
            volume_modes = {
                'volume-hide-btn': 'hide',
                'volume-bars-btn': 'bars',
                'volume-bars-ma-btn': 'bars_ma'
            }
            new_mode = volume_modes.get(trigger_id, 'bars_ma')

        return (new_mode,
                new_mode != 'hide',
                new_mode != 'bars',
                new_mode != 'bars_ma',
                new_mode == 'hide')


def _register_symbol_callbacks(app, market_service):
    """Register symbol search callbacks"""
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
                all_symbols = market_service.get_available_symbols()
                symbols = [s for s in all_symbols if s['symbol'] in filtered_symbols][:20]

                if search_value and len(search_value) >= 1:
                    symbols = [s for s in symbols
                               if search_value.upper() in s['symbol'].upper() or
                               search_value.upper() in s.get('company_name', '').upper()]

            elif not search_value or len(search_value) < 1:
                symbols = market_service.get_available_symbols()[:10]
            else:
                symbols = market_service.search_symbols(search_value, limit=20)

            options = []
            for symbol_data in symbols:
                symbol = symbol_data['symbol']
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


def _register_chart_update_callbacks(app, chart_builder, market_service):
    """Register chart update callbacks"""
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
    def update_interactive_chart(symbol, chart_type, overlay_indicators, oscillator_indicators, volume_display,
                                 refresh_clicks):
        """Update interactive chart with technical indicators."""
        try:
            # Use selected symbol or default to ADBE
            if not symbol:
                symbol = "ADBE"

            # Get ALL available market data
            df = market_service.get_all_available_data(symbol)

            if df is None or df.empty:
                return chart_builder._create_empty_chart(f"No data available for {symbol}")

            # Log actual data range for debugging
            if not df.empty and 'timestamp' in df.columns:
                actual_start = df['timestamp'].min()
                actual_end = df['timestamp'].max()

                logger.info(f"Raw date range for {symbol}: {actual_start} to {actual_end}")

            # Determine volume display settings
            show_volume = volume_display and volume_display != "hide"
            color_by_price = True

            # Use indicators or default
            indicators = (overlay_indicators or []) + (oscillator_indicators or [])
            chart_indicators = indicators or []

            # Create advanced chart
            fig = chart_builder.create_advanced_price_chart(
                df=df,
                symbol=symbol,
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


def _register_technical_analysis_callbacks(app, market_service):
    """Register technical analysis summary callbacks"""
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

            # Get market data for analysis
            df = market_service.get_all_available_data(symbol)

            if df is None or df.empty:
                return "No data available for technical analysis"

            # Get current price and calculate basic metrics
            current_price = df['close'].iloc[-1]
            price_change = ((current_price - df['close'].iloc[-30]) / df['close'].iloc[-30] * 100) if len(df) >= 30 else 0

            # Get technical indicators
            analysis_indicators = market_service.get_technical_indicators(symbol)

            summary_items = [
                # Current Price
                {
                    "title": "Current Price",
                    "value": f"${current_price:.2f}",
                    "change": f"{price_change:+.2f}%",
                    "color": "success" if price_change >= 0 else "danger"
                }
            ]

            # Add RSI if available
            if 'rsi' in analysis_indicators:
                rsi_value = analysis_indicators['rsi'].iloc[-1]
                rsi_status = "Overbought" if rsi_value > 70 else "Oversold" if rsi_value < 30 else "Neutral"
                rsi_color = "danger" if rsi_value > 70 else "warning" if rsi_value < 30 else "success"

                summary_items.append({
                    "title": "RSI (14)",
                    "value": f"{rsi_value:.1f}",
                    "status": rsi_status,
                    "color": rsi_color
                })

            # Add volume analysis if available
            if 'volume' in df.columns:
                current_volume = df['volume'].iloc[-1]
                avg_volume = df['volume'].rolling(window=20).mean().iloc[-1]
                volume_ratio = (current_volume / avg_volume) if avg_volume > 0 else 0

                def format_volume(vol):
                    if vol >= 1e9:
                        return f"{vol / 1e9:.1f}B"
                    elif vol >= 1e6:
                        return f"{vol / 1e6:.1f}M"
                    elif vol >= 1e3:
                        return f"{vol / 1e3:.1f}K"
                    else:
                        return f"{vol:.0f}"

                volume_color = "success" if volume_ratio > 1.5 else "warning" if volume_ratio > 0.8 else "muted"
                volume_status = "High" if volume_ratio > 1.5 else "Normal" if volume_ratio > 0.8 else "Low"

                summary_items.append({
                    "title": "Volume",
                    "value": format_volume(current_volume),
                    "status": f"{volume_ratio:.1f}x avg ({volume_status})",
                    "color": volume_color
                })

            # Convert summary items to Dash components
            return _create_summary_components(summary_items)

        except Exception as e:
            logger.error(f"Error updating technical analysis summary: {e}")
            return f"Error loading analysis: {str(e)}"


def _create_summary_components(summary_items):
    """Convert summary item dictionaries to Dash HTML components"""
    from dash import html
    import dash_bootstrap_components as dbc
    
    if not summary_items:
        return html.P("No technical analysis data available", className="text-muted")
    
    components = []
    for item in summary_items:
        # Create a card for each summary item
        card_content = [
            html.H6(item["title"], className="card-title text-muted mb-1"),
            html.H4(item["value"], className=f"card-text text-{item['color']} mb-0")
        ]
        
        # Add change or status if available
        if "change" in item:
            card_content.append(
                html.Small(item["change"], className=f"text-{item['color']}")
            )
        elif "status" in item:
            card_content.append(
                html.Small(item["status"], className="text-muted")
            )
        
        card = dbc.Card([
            dbc.CardBody(card_content)
        ], className="text-center mb-2")
        
        components.append(dbc.Col(card, width=12, md=4))
    
    return dbc.Row(components)