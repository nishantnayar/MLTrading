"""
Overview tab callback functions for the dashboard.
Handles market overview, statistics, and time-related information.
"""

import plotly.graph_objs as go
from dash import Input, Output, html, dcc, State, callback_context
import dash_bootstrap_components as dbc
from datetime import datetime, timedelta
import pytz

from ..config import CHART_COLORS, MARKET_HOURS
from ...trading.brokers.alpaca_service import get_alpaca_service
from ..layouts.chart_components import create_empty_chart, create_horizontal_bar_chart
from ..services.data_service import MarketDataService
from ..services.symbol_service import SymbolService
from ...utils.logging_config import get_ui_logger

# Initialize logger and data service
logger = get_ui_logger("dashboard")
data_service = MarketDataService()
symbol_service = SymbolService()


def register_overview_callbacks(app):
    """Register all overview-related callbacks with the app"""

    @app.callback(
        Output("market-overview-chart", "figure"),
        [Input("refresh-data-btn", "n_clicks"),
         Input("refresh-overview-btn", "n_clicks")],
        prevent_initial_call=False
    )


    def update_market_overview_chart(refresh_clicks, overview_refresh_clicks):
        """Update market overview chart with real data"""
        try:
            # Get market overview data
            market_data = data_service.get_market_overview()

            if not market_data or not market_data.get('dates') or not market_data.get('values'):
                logger.warning("No market overview data available")
                return create_empty_chart("No Market Data Available")

            dates = market_data['dates']
            values = market_data['values']

            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=dates,
                y=values,
                mode='lines',
                name='Market Index',
                line=dict(color=CHART_COLORS['primary'], width=2),
                hovertemplate='<b>%{x}</b><br>Value: %{y}<extra></extra>'
            ))

            fig.update_layout(
                title=dict(
                    text="Market Overview (Last 30 Days)",
                    font=dict(size=20, color=CHART_COLORS['primary']),
                    x=0.5,
                    xanchor='center'
                ),
                xaxis_title="Date",
                yaxis_title="Index Value",
                height=350,
                margin=dict(l=40, r=40, t=80, b=40),
                plot_bgcolor='white',
                paper_bgcolor='white',
                xaxis=dict(
                    rangeslider=dict(visible=False),
                    type='date'
                )
            )

            return fig

        except Exception as e:
            logger.error(f"Error updating market overview chart: {e}")
            return create_empty_chart("Error Loading Market Data")

    @app.callback(
        Output("top-performers-list", "children"),
        [Input("refresh-data-btn", "n_clicks"),
         Input("refresh-overview-btn", "n_clicks")],
        prevent_initial_call=False
    )


    def update_top_performers(refresh_clicks, overview_refresh_clicks):
        """Update top performers list with real data"""
        try:
            # Get top performers data
            performers_data = data_service.get_top_performers()

            if not performers_data:
                return html.P("No data available", className="text-muted")

            performers_list = []
            for i, performer in enumerate(performers_data[:5], 1):  # Show top 5
                performers_list.append(
                    html.Div([
                        html.Span(f"{i}. {performer['symbol']}", className="fw-bold"),
                        html.Span(f" +{performer['change']}%", className="text-success ms-2")
                    ], className="mb-2")
                )

            return performers_list

        except Exception as e:
            logger.error(f"Error updating top performers: {e}")
            return html.P("Error loading data", className="text-danger")

    @app.callback(
        Output("recent-activity-list", "children"),
        [Input("refresh-data-btn", "n_clicks"),
         Input("refresh-overview-btn", "n_clicks")],
        prevent_initial_call=False
    )


    def update_recent_activity(refresh_clicks, overview_refresh_clicks):
        """Update recent activity list with real data"""
        try:
            # Get recent activity data
            activity_data = data_service.get_recent_activity()

            if not activity_data:
                return html.P("No recent activity", className="text-muted")

            activity_list = []
            for activity in activity_data[:5]:  # Show last 5 activities
                activity_list.append(
                    html.Div([
                        html.Span(f"{activity['time']} - ", className="text-muted"),
                        html.Span(f"{activity['action']} {activity['symbol']}", className="fw-bold"),
                        html.Span(f" @ ${activity['price']}", className="text-info")
                    ], className="mb-2")
                )

            return activity_list

        except Exception as e:
            logger.error(f"Error updating recent activity: {e}")
            return html.P("Error loading data", className="text-danger")

    @app.callback(
        [Output("total-symbols", "children"),
         Output("active-trades", "children"),
         Output("portfolio-value", "children"),
         Output("daily-pnl", "children")],
        [Input("refresh-data-btn", "n_clicks"),
         Input("refresh-overview-btn", "n_clicks")],
        prevent_initial_call=False
    )


    def update_summary_stats(refresh_clicks, overview_refresh_clicks):
        """Update summary statistics with real data"""
        try:
            # Get summary statistics
            stats_data = data_service.get_summary_statistics()

            if not stats_data:
                return "0", "0", "$0", "$0"

            total_symbols = stats_data.get('total_symbols', 0)
            active_trades = stats_data.get('active_trades', 0)
            portfolio_value = f"${stats_data.get('portfolio_value', 0):,.0f}"
            daily_pnl = f"${stats_data.get('daily_pnl', 0):+,.0f}"

            return str(total_symbols), str(active_trades), portfolio_value, daily_pnl

        except Exception as e:
            logger.error(f"Error updating summary stats: {e}")
            return "0", "0", "$0", "$0"

    @app.callback(
        [Output("current-time", "children"),
         Output("next-market-open", "children"),
         Output("next-market-close", "children")],
        [Input("refresh-stats-btn", "n_clicks")],
        prevent_initial_call=False
    )


    def update_time_and_market_info(refresh_clicks):
        """Update current time and market hours information"""
        try:
            # Get current time in Chicago time (Central Time)
            chicago = pytz.timezone('US/Central')
            now = datetime.now(chicago)

            # Format current time
            current_time = now.strftime("%I:%M %p CST")

            # Try to get real market hours from Alpaca
            try:
                alpaca_service = get_alpaca_service()
                market_hours = alpaca_service.get_market_hours()

                if market_hours and 'next_open' in market_hours and 'next_close' in market_hours:
                    # Convert to Central Time for display
                    next_open = market_hours['next_open'].astimezone(chicago)
                    next_close = market_hours['next_close'].astimezone(chicago)

                    # Format market times with day information
                    today = now.date()
                    open_date = next_open.date()
                    close_date = next_close.date()

                    # Add day information if not today
                    if open_date == today:
                        next_open_str = next_open.strftime("%I:%M %p")
                    elif open_date == today + timedelta(days=1):
                        next_open_str = next_open.strftime("Tomorrow %I:%M %p")
                    else:
                        next_open_str = next_open.strftime("%A %I:%M %p")

                    if close_date == today:
                        next_close_str = next_close.strftime("%I:%M %p")
                    elif close_date == today + timedelta(days=1):
                        next_close_str = next_close.strftime("Tomorrow %I:%M %p")
                    else:
                        next_close_str = next_close.strftime("%A %I:%M %p")

                    return current_time, next_open_str, next_close_str
                else:
                    logger.warning("Could not get market hours from Alpaca, falling back to hardcoded values")
                    raise Exception("Alpaca market hours not available")

            except Exception as alpaca_error:
                logger.warning(f"Alpaca API unavailable for market hours: {alpaca_error}, using fallback")

                # Fallback to hardcoded market hours (existing logic)
                market_open = now.replace(
                    hour=MARKET_HOURS['open_hour'],
                    minute=MARKET_HOURS['open_minute'],
                    second=0,
                    microsecond=0
                )
                # market_close is calculated but not used in current logic
                # market_close = now.replace(
                #     hour=MARKET_HOURS['close_hour'],
                #     minute=MARKET_HOURS['close_minute'],
                #     second=0,
                #     microsecond=0
                # )

                # If it's weekend, next open is Monday
                if now.weekday() >= 5:  # Saturday = 5, Sunday = 6
                    days_until_monday = (7 - now.weekday()) % 7
                    next_open = now + timedelta(days=days_until_monday)
                    next_open = next_open.replace(hour=9, minute=30, second=0, microsecond=0)
                else:
                    # If it's before market open today
                    if now.time() < market_open.time():
                        next_open = market_open
                    else:
                        # Next open is tomorrow (or Monday if Friday)
                        if now.weekday() == 4:  # Friday
                            next_open = now + timedelta(days=3)  # Monday
                        else:
                            next_open = now + timedelta(days=1)
                        next_open = next_open.replace(
                            hour=MARKET_HOURS['open_hour'],
                            minute=MARKET_HOURS['open_minute'],
                            second=0,
                            microsecond=0
                        )

                # Next close is the same day as next open
                next_close = next_open.replace(
                    hour=MARKET_HOURS['close_hour'],
                    minute=MARKET_HOURS['close_minute'],
                    second=0,
                    microsecond=0
                )

                # Format market times with day information
                today = now.date()
                open_date = next_open.date()
                close_date = next_close.date()

                # Add day information if not today
                if open_date == today:
                    next_open_str = next_open.strftime("%I:%M %p")
                elif open_date == today + timedelta(days=1):
                    next_open_str = next_open.strftime("Tomorrow %I:%M %p")
                else:
                    next_open_str = next_open.strftime("%A %I:%M %p")

                if close_date == today:
                    next_close_str = next_close.strftime("%I:%M %p")
                elif close_date == today + timedelta(days=1):
                    next_close_str = next_close.strftime("Tomorrow %I:%M %p")
                else:
                    next_close_str = next_close.strftime("%A %I:%M %p")

                return current_time, next_open_str, next_close_str

        except Exception as e:
            logger.error(f"Error updating time and market info: {e}")
            return "Error", "Error", "Error"

    @app.callback(
        [Output("total-symbols-db", "children"),
         Output("data-range", "children")],
        [Input("refresh-stats-btn", "n_clicks")],
        prevent_initial_call=False
    )


    def update_database_stats(refresh_clicks):
        """Update database statistics"""
        try:
            # Get total symbols in database
            symbols_data = data_service.get_available_symbols()
            total_symbols = len(symbols_data) if symbols_data else 0

            # Get data range from database
            data_range = data_service.get_data_date_range()

            return str(total_symbols), data_range

        except Exception as e:
            logger.error(f"Error updating database stats: {e}")
            return "0", "Error"

    @app.callback(
        [Output("sector-distribution-chart", "figure"),
         Output("selected-sector-store", "data")],
        [Input("refresh-overview-btn", "n_clicks"),
         Input("refresh-stats-btn", "n_clicks")],
        prevent_initial_call=False
    )


    def update_sector_distribution_chart(overview_refresh, stats_refresh):
        """Update sector distribution bar chart"""
        try:
            sector_data = symbol_service.get_sector_distribution()

            if not sector_data or not sector_data.get('sectors'):
                logger.warning("No sector distribution data available")
                return create_empty_chart("No Sector Data Available"), ""

            chart_data = {
                'categories': sector_data['sectors'],
                'counts': sector_data['counts']
            }

            # Set default sector to the one with highest count (first in list due to sorting)
            default_sector = sector_data['sectors'][0] if sector_data['sectors'] else ""

            return create_horizontal_bar_chart(
                chart_data,
                "Stocks by Sector",
                color=CHART_COLORS['primary']
            ), default_sector

        except Exception as e:
            logger.error(f"Error updating sector distribution chart: {e}")
            return create_empty_chart("Error Loading Sector Data"), ""

    @app.callback(
        [Output("industry-distribution-chart", "figure"),
         Output("selected-sector-badge", "children"),
         Output("selected-sector-badge", "style")],
        [Input("sector-distribution-chart", "clickData"),
         Input("selected-sector-store", "data"),
         Input("refresh-overview-btn", "n_clicks"),
         Input("refresh-stats-btn", "n_clicks")],
        prevent_initial_call=False
    )


    def update_industry_distribution_chart(sector_click, default_sector, overview_refresh, stats_refresh):
        """Update industry distribution chart based on selected sector"""
        try:
            # Determine which sector to use
            selected_sector = default_sector  # Default to highest sector

            # Check if user clicked on sector chart
            ctx = callback_context
            if ctx.triggered:
                trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
                if trigger_id == "sector-distribution-chart" and sector_click:
                    if 'points' in sector_click and sector_click['points']:
                        selected_sector = sector_click['points'][0]['y']  # Get clicked sector

            if not selected_sector:
                return create_empty_chart("No Sector Selected"), "", {"display": "none"}

            # Get industry distribution for selected sector
            industry_data = symbol_service.get_industry_distribution(selected_sector)

            if not industry_data or not industry_data.get('industries'):
                return (create_empty_chart(f"No Industries Found in {selected_sector}"),
                        selected_sector,
                        {"display": "inline-block", "font-size": "0.7em"})

            chart_data = {
                'categories': industry_data['industries'],
                'counts': industry_data['counts']
            }

            return (create_horizontal_bar_chart(
                chart_data,
                f"Industries in {selected_sector}",
                color=CHART_COLORS['info']
            ), selected_sector, {"display": "inline-block", "font-size": "0.7em"})

        except Exception as e:
            logger.error(f"Error updating industry distribution chart: {e}")
            return (create_empty_chart("Error Loading Industry Data"), 
                    "Error", {"display": "inline-block", "font-size": "0.7em"})

    @app.callback(
        Output("top-volume-chart", "figure"),
        [Input("refresh-overview-btn", "n_clicks"),
         Input("refresh-stats-btn", "n_clicks")],
        prevent_initial_call=False
    )


    def update_top_volume_chart(overview_refresh, stats_refresh):
        """Update top symbols by volume bar chart"""
        try:
            # Get top 15 symbols by recent volume
            symbols = data_service.get_available_symbols()[:15]  # Limit to top 15

            if not symbols:
                return create_empty_chart("No Volume Data Available")

            volume_data = []
            symbol_names = []

            for symbol_info in symbols:
                symbol = symbol_info['symbol']
                try:
                    # Get recent market data for volume
                    market_data = data_service.get_market_data(symbol, days=7)
                    if not market_data.empty and 'volume' in market_data.columns:
                        avg_volume = market_data['volume'].mean()
                        volume_data.append(avg_volume)
                        symbol_names.append(symbol)
                except Exception:
                    continue

            if not volume_data:
                return create_empty_chart("No Volume Data Available")

            # Sort by volume descending
            sorted_pairs = sorted(zip(symbol_names, volume_data), key=lambda x: x[1], reverse=True)
            sorted_symbols, sorted_volumes = zip(*sorted_pairs)

            chart_data = {
                'categories': list(sorted_symbols[:10]),  # Top 10
                'counts': [vol/1000000 for vol in sorted_volumes[:10]]  # Convert to millions
            }

            return create_horizontal_bar_chart(
                chart_data,
                "Top 10 Symbols by Volume (7-day avg, millions)",
                color=CHART_COLORS['info']
            )

        except Exception as e:
            logger.error(f"Error updating top volume chart: {e}")
            return create_empty_chart("Error Loading Volume Data")

    @app.callback(
        Output("price-performance-chart", "figure"),
        [Input("refresh-overview-btn", "n_clicks"),
         Input("refresh-stats-btn", "n_clicks")],
        prevent_initial_call=False
    )


    def update_price_performance_chart(overview_refresh, stats_refresh):
        """Update 7-day price performance bar chart"""
        try:
            # Get sample of symbols for performance analysis
            symbols = data_service.get_available_symbols()[:20]  # Top 20 symbols

            if not symbols:
                return create_empty_chart("No Price Data Available")

            performance_data = []
            symbol_names = []

            for symbol_info in symbols:
                symbol = symbol_info['symbol']
                try:
                    # Get 7-day price change
                    price_change = data_service.get_price_change(symbol, days=7)
                    if price_change and 'change_percent' in price_change:
                        performance_data.append(price_change['change_percent'])
                        symbol_names.append(symbol)
                except Exception:
                    continue

            if not performance_data:
                return create_empty_chart("No Performance Data Available")

            # Sort by performance descending
            sorted_pairs = sorted(zip(symbol_names, performance_data), key=lambda x: x[1], reverse=True)
            sorted_symbols, sorted_performance = zip(*sorted_pairs)

            chart_data = {
                'categories': list(sorted_symbols[:10]),  # Top 10 performers
                'counts': list(sorted_performance[:10])
            }

            return create_horizontal_bar_chart(
                chart_data,
                "Top 10 Price Performance (7-day %)",
                color=CHART_COLORS['success']
            )

        except Exception as e:
            logger.error(f"Error updating price performance chart: {e}")
            return create_empty_chart("Error Loading Performance Data")

    @app.callback(
        Output("market-activity-chart", "figure"),
        [Input("refresh-overview-btn", "n_clicks"),
         Input("refresh-stats-btn", "n_clicks")],
        prevent_initial_call=False
    )


    def update_market_activity_chart(overview_refresh, stats_refresh):
        """Update market activity summary bar chart"""
        try:
            # Get symbols and calculate basic activity metrics
            symbols = data_service.get_available_symbols()[:15]

            if not symbols:
                return create_empty_chart("No Activity Data Available")

            activity_scores = []
            symbol_names = []

            for symbol_info in symbols:
                symbol = symbol_info['symbol']
                try:
                    # Calculate activity score based on volume and price volatility
                    market_data = data_service.get_market_data(symbol, days=5)
                    if not market_data.empty:
                        avg_volume = market_data['volume'].mean() if 'volume' in market_data.columns else 0
                        price_volatility = market_data['close'].std() if 'close' in market_data.columns else 0

                        # Simple activity score (normalized)
                        activity_score = (avg_volume / 1000000) + (price_volatility * 10)
                        activity_scores.append(activity_score)
                        symbol_names.append(symbol)
                except Exception:
                    continue

            if not activity_scores:
                return create_empty_chart("No Activity Data Available")

            # Sort by activity score descending
            sorted_pairs = sorted(zip(symbol_names, activity_scores), key=lambda x: x[1], reverse=True)
            sorted_symbols, sorted_scores = zip(*sorted_pairs)

            chart_data = {
                'categories': list(sorted_symbols[:10]),  # Top 10 most active
                'counts': list(sorted_scores[:10])
            }

            return create_horizontal_bar_chart(
                chart_data,
                "Market Activity Index (Volume + Volatility)",
                color=CHART_COLORS['warning']
            )

        except Exception as e:
            logger.error(f"Error updating market activity chart: {e}")
            return create_empty_chart("Error Loading Activity Data")

    @app.callback(
        Output("last-updated", "children"),
        [Input("refresh-overview-btn", "n_clicks"),
         Input("refresh-stats-btn", "n_clicks")],
        prevent_initial_call=False
    )


    def update_last_updated_timestamp(overview_refresh, stats_refresh):
        """Update the last updated timestamp"""
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")

    @app.callback(
        [Output("filtered-symbols-display", "children"),
         Output("filtered-symbols-store", "data"),
         Output("filter-status-badge", "children"),
         Output("filter-status-badge", "style")],
        [Input("sector-distribution-chart", "clickData"),
         Input("industry-distribution-chart", "clickData"),
         Input("top-volume-chart", "clickData"),
         Input("price-performance-chart", "clickData"),
         Input("market-activity-chart", "clickData")],
        prevent_initial_call=True
    )


    def update_filtered_symbols(sector_click, industry_click, volume_click, performance_click, activity_click):
        """Update filtered symbols based on bar chart clicks"""
        try:
            ctx = callback_context
            if not ctx.triggered:
                return (html.P("Click on any bar in the charts above to filter symbols by that category.",
                              className="text-muted text-center m-4"), [], "", {"display": "none"})

            triggered_chart = ctx.triggered[0]['prop_id'].split('.')[0]
            clicked_data = ctx.triggered[0]['value']

            # Add logging to debug the issue
            logger.info(f"Bar chart clicked - Chart: {triggered_chart}, Data: {clicked_data}")

            if not clicked_data or 'points' not in clicked_data:
                return (html.P("No data selected. Try clicking on a bar.", className="text-muted"), [], "", {"display": "none"})

            clicked_point = clicked_data['points'][0]
            category = clicked_point['y']  # The category name (sector, symbol, etc.)
            # value = clicked_point['x']     # The value (unused in current logic)

            filtered_symbols = []
            filter_type = ""

            if triggered_chart == "sector-distribution-chart":
                # Filter symbols by sector
                filter_type = "Sector"
                filtered_symbols = symbol_service.get_symbols_by_sector(category)

            elif triggered_chart == "industry-distribution-chart":
                # Filter symbols by industry
                filter_type = "Industry"
                filtered_symbols = symbol_service.get_symbols_by_industry(category)

            elif triggered_chart == "top-volume-chart":
                # Show details for the clicked symbol
                filter_type = "High Volume Symbol"
                symbol_info = data_service.get_available_symbols()
                filtered_symbols = [s for s in symbol_info if s['symbol'] == category]

            elif triggered_chart == "price-performance-chart":
                # Show details for the clicked symbol
                filter_type = "Top Performer"
                symbol_info = data_service.get_available_symbols()
                filtered_symbols = [s for s in symbol_info if s['symbol'] == category]

            elif triggered_chart == "market-activity-chart":
                # Show details for the clicked symbol
                filter_type = "High Activity Symbol"
                symbol_info = data_service.get_available_symbols()
                filtered_symbols = [s for s in symbol_info if s['symbol'] == category]

            if not filtered_symbols:
                return (html.P(f"No symbols found for {category}", className="text-muted"), [], "", {"display": "none"})

            # Create symbol cards
            symbol_cards = []
            for symbol_data in filtered_symbols[:20]:  # Limit to 20 symbols
                symbol = symbol_data.get('symbol', '')
                company_name = symbol_data.get('company_name', symbol)

                card = dbc.Card([
                    dbc.CardBody([
                        html.H6(symbol, className="card-title mb-1"),
                        html.P(company_name, className="card-text small text-muted mb-2"),
                        html.Div([
                            dbc.Button("Analyze",
                                       id={"type": "analyze-symbol-btn", "index": symbol},
                                       size="sm",
                                       color="primary",
                                       className="btn-sm me-1"),
                            dbc.Button("Compare",
                                       id={"type": "compare-symbol-btn", "index": symbol},
                                       size="sm",
                                       color="outline-info",
                                       className="btn-sm")
                        ])
                    ])
                ], className="h-100")

                symbol_cards.append(
                    dbc.Col(card, width=6, lg=4, xl=3, className="mb-3")
                )

            header = html.Div([
                html.H6(f"Filtered by {filter_type}: {category}", className="mb-2"),
                html.P(f"Found {len(filtered_symbols)} symbols", className="text-muted small mb-3")
            ])

            # Store filtered symbols for use in Charts tab
            symbols_data = [s['symbol'] for s in filtered_symbols]

            # Create filter status badge
            badge_text = f"Active: {filter_type}"
            badge_style = {"display": "inline-block"}

            return ([header, dbc.Row(symbol_cards)], symbols_data, badge_text, badge_style)

        except Exception as e:
            logger.error(f"Error filtering symbols: {e}")
            return (html.P("Error filtering symbols. Please try again.", className="text-danger"), [], "", {"display": "none"})

