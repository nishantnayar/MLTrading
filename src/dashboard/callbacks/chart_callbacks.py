"""
Chart-related callback functions for the dashboard.
Handles price charts, sector/industry distribution charts, and symbol filtering.
"""

import plotly.graph_objs as go
from dash import Input, Output

from ..config import CHART_COLORS, TIME_RANGE_DAYS
from ..layouts.chart_components import create_empty_chart, create_error_chart
from ..services.data_service import MarketDataService
from ..utils.validators import InputValidator
from ...utils.logging_config import get_ui_logger

# Initialize logger and data service
logger = get_ui_logger("dashboard")
data_service = MarketDataService()


def register_chart_callbacks(app):
    """Register all chart-related callbacks with the app"""
    
    @app.callback(
        Output("price-chart", "figure"),
        [Input("symbol-dropdown", "value"),
         Input("time-range-dropdown", "value"),
         Input("refresh-data-btn", "n_clicks")],
        prevent_initial_call=False
    )
    def update_price_chart(symbol, time_range, refresh_clicks):
        """Update price chart based on symbol and time range"""
        try:
            # Validate inputs
            if symbol:
                is_valid, error = InputValidator.validate_symbol(symbol)
                if not is_valid:
                    return create_error_chart('validation_error', error, symbol)
            
            if time_range:
                is_valid, error = InputValidator.validate_time_range(time_range)
                if not is_valid:
                    return create_error_chart('validation_error', error)
            
            days = TIME_RANGE_DAYS.get(time_range, 30)  # Default to 30 days
            
            # Get real market data
            df = data_service.get_market_data(symbol, days=days, source='yahoo', hourly=False)
            
            if df.empty:
                logger.warning(f"No market data available for {symbol}")
                return create_empty_chart(f"No Data Available for {symbol}")
            
            # Create candlestick chart with real data
            fig = go.Figure(data=[
                go.Candlestick(
                    x=df['timestamp'],
                    open=df['open'],
                    high=df['high'],
                    low=df['low'],
                    close=df['close'],
                    name=f'{symbol}',
                    increasing_line_color=CHART_COLORS['success'],
                    decreasing_line_color='#dc3545'
                )
            ])
            
            fig.update_layout(
                title=dict(
                    text=f"{symbol} Price Chart ({time_range})",
                    font=dict(size=20, color=CHART_COLORS['primary']),
                    x=0.5,
                    xanchor='center'
                ),
                xaxis_title="Date",
                yaxis_title="Price ($)",
                height=350,
                margin=dict(l=40, r=40, t=80, b=40),
                showlegend=False,
                plot_bgcolor='white',
                paper_bgcolor='white',
                xaxis=dict(
                    rangeslider=dict(visible=False),
                    type='date',
                    rangebreaks=[
                        # Hide weekends
                        dict(bounds=["sat", "mon"]),
                        # Hide holidays (example dates)
                        dict(values=["2025-01-01", "2025-07-04"]),
                        # Hide gaps outside trading hours (if intraday data)
                        dict(bounds=[17, 9], pattern='hour')
                    ]
                )
            )
            
            logger.info(f"Updated candlestick chart for {symbol} with {len(df)} data points")
            return fig
            
        except Exception as e:
            logger.error(f"Error updating price chart for {symbol}: {e}")
            return create_empty_chart(f"Error Loading Data for {symbol}")

    @app.callback(
        Output("sector-chart", "figure"),
        [Input("refresh-data-btn", "n_clicks")],
        prevent_initial_call=False
    )
    def update_sector_chart(refresh_clicks):
        """Update sector distribution chart with real data"""
        try:
            # Get real sector distribution data
            sector_data = data_service.get_sector_distribution()
            
            if not sector_data or not sector_data.get('sectors') or not sector_data.get('counts'):
                # No data available - return empty chart with error message
                logger.warning("No sector distribution data available")
                return create_empty_chart("No Sector Data Available")
            
            sectors = sector_data['sectors']
            counts = sector_data['counts']
            
            # Reverse the order so highest appears at top
            sectors = sectors[::-1]
            counts = counts[::-1]
            
            fig = go.Figure(data=[
                go.Bar(
                    x=counts,
                    y=sectors,
                    orientation='h',
                    marker_color=CHART_COLORS['primary'],
                    hovertemplate='<b>%{y}</b><br>Count: %{x}<extra></extra>'
                )
            ])
            
            fig.update_layout(
                title=dict(
                    text="Sector Distribution",
                    font=dict(size=20, color=CHART_COLORS['primary']),
                    x=0.5,
                    xanchor='center'
                ),
                xaxis=dict(
                    title="",
                    showgrid=False,
                    zeroline=False,
                    showticklabels=True
                ),
                yaxis=dict(
                    title="",
                    showgrid=False,
                    zeroline=False
                ),
                height=400,
                margin=dict(l=40, r=40, t=80, b=40),
                bargap=0.2,
                bargroupgap=0.1,
                plot_bgcolor='white',
                paper_bgcolor='white'
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Error updating sector chart: {e}")
            # Return empty chart on error
            return create_empty_chart("Error Loading Sector Data")

    @app.callback(
        Output("industry-chart", "figure"),
        [Input("sector-chart", "clickData"),
         Input("refresh-data-btn", "n_clicks")],
        prevent_initial_call=False
    )
    def update_industry_chart(sector_click, refresh_clicks):
        """Update industry distribution chart based on sector selection with real data"""
        try:
            if sector_click:
                selected_sector = sector_click['points'][0]['y']
                # Get real industry data for the selected sector
                industry_data = data_service.get_industry_distribution(selected_sector)
                
                if not industry_data or not industry_data.get('industries') or not industry_data.get('counts'):
                    # No data available - return empty chart with error message
                    logger.warning(f"No industry distribution data available for sector: {selected_sector}")
                    return create_empty_chart(f"No Industry Data Available for {selected_sector}")
                
                industries = industry_data['industries']
                counts = industry_data['counts']
                
                # Reverse the order so highest appears at top
                industries = industries[::-1]
                counts = counts[::-1]
                
                # Create chart with industry data
                fig = go.Figure(data=[
                    go.Bar(
                        x=counts,
                        y=industries,
                        orientation='h',
                        marker_color=CHART_COLORS['info'],
                        hovertemplate='<b>%{y}</b><br>Count: %{x}<extra></extra>'
                    )
                ])
                
                fig.update_layout(
                    title=dict(
                        text="Industry Distribution",
                        font=dict(size=20, color=CHART_COLORS['primary']),
                        x=0.5,
                        xanchor='center'
                    ),
                    xaxis=dict(
                        title="",
                        showgrid=False,
                        zeroline=False,
                        showticklabels=True
                    ),
                    yaxis=dict(
                        title="",
                        showgrid=False,
                        zeroline=False
                    ),
                    height=400,
                    margin=dict(l=40, r=40, t=80, b=40),
                    bargap=0.2,
                    bargroupgap=0.1,
                    plot_bgcolor='white',
                    paper_bgcolor='white'
                )
                
                return fig
            else:
                # Show message when no sector is selected
                fig = go.Figure()
                
                fig.update_layout(
                    title="Industry Distribution",
                    xaxis=dict(
                        showgrid=False,
                        zeroline=False,
                        showticklabels=False
                    ),
                    yaxis=dict(
                        showgrid=False,
                        zeroline=False,
                        showticklabels=False
                    ),
                    height=400,
                    margin=dict(l=40, r=40, t=60, b=40),
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    annotations=[{
                        'text': 'Please select a sector',
                        'xref': 'paper',
                        'yref': 'paper',
                        'showarrow': False,
                        'font': {'size': 16, 'color': '#666666'},
                        'x': 0.5,
                        'y': 0.5
                    }]
                )
                
                return fig
            
        except Exception as e:
            logger.error(f"Error updating industry chart: {e}")
            # Return empty chart on error
            return create_empty_chart("Error Loading Industry Data")

    @app.callback(
        [Output("symbol-dropdown", "options"),
         Output("symbol-dropdown", "value")],
        [Input("refresh-data-btn", "n_clicks"),
         Input("current-sector-filter", "children"),
         Input("current-industry-filter", "children")],
        prevent_initial_call=False
    )
    def update_symbol_options(refresh_clicks, selected_sector, selected_industry):
        """Update symbol dropdown based on selected sector and industry filters"""
        try:
            # Determine which filter to use
            if selected_industry and selected_industry != "All Industries":
                # Filter by specific industry
                symbols_data = data_service.get_symbols_by_industry(selected_industry)
                logger.info(f"Filtering symbols by industry: {selected_industry}")
            elif selected_sector and selected_sector != "All Sectors":
                # Filter by sector (shows all symbols from that sector)
                symbols_data = data_service.get_symbols_by_sector(selected_sector)
                logger.info(f"Filtering symbols by sector: {selected_sector}")
            else:
                # No filter - get all available symbols
                symbols_data = data_service.get_available_symbols()
                logger.info("Showing all available symbols")
            
            if not symbols_data:
                # No data available - return empty options with error message
                logger.warning(f"No symbols data available for filters: sector={selected_sector}, industry={selected_industry}")
                options = []
                selected_value = None
            else:
                # Convert real data to dropdown options
                options = [
                    {"label": f"{symbol['symbol']} - {symbol['company_name']}", "value": symbol['symbol']}
                    for symbol in symbols_data
                ]
                # Set the value to the first option if options exist
                selected_value = options[0]["value"] if options else None
            
            logger.info(f"Updated symbol dropdown with {len(options)} options")
            
            # Set the value to the first option if options exist
            selected_value = options[0]["value"] if options else "AAPL"
            
            return options, selected_value
            
        except Exception as e:
            logger.error(f"Error updating symbol options: {e}")
            # Return empty options on error
            return [], None

    @app.callback(
        [Output("current-sector-filter", "children"),
         Output("current-industry-filter", "children")],
        [Input("sector-chart", "clickData"),
         Input("industry-chart", "clickData")]
    )
    def update_filters(sector_click, industry_click):
        """Update filter display based on chart clicks"""
        sector_filter = "All Sectors"
        industry_filter = "All Industries"
        
        if sector_click:
            sector_filter = sector_click['points'][0]['y']
        
        if industry_click:
            industry_filter = industry_click['points'][0]['y']
        
        return sector_filter, industry_filter