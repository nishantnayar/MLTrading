"""
Overview tab callback functions for the dashboard.
Handles market overview, statistics, and time-related information.
"""

import plotly.graph_objs as go
from dash import Input, Output, html
from datetime import datetime, timedelta
import pytz

from ..config import CHART_COLORS, MARKET_HOURS
from ..layouts.chart_components import create_empty_chart
from ..services.data_service import MarketDataService
from ...utils.logging_config import get_ui_logger

# Initialize logger and data service
logger = get_ui_logger("dashboard")
data_service = MarketDataService()


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
            
            # Calculate next market open and close using config
            market_open = now.replace(
                hour=MARKET_HOURS['open_hour'], 
                minute=MARKET_HOURS['open_minute'], 
                second=0, 
                microsecond=0
            )
            market_close = now.replace(
                hour=MARKET_HOURS['close_hour'], 
                minute=MARKET_HOURS['close_minute'], 
                second=0, 
                microsecond=0
            )
            
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
            
            # Format market times
            next_open_str = next_open.strftime("%I:%M %p")
            next_close_str = next_close.strftime("%I:%M %p")
            
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