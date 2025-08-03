import dash
from dash import dcc, html, callback_context
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils.logging_config import get_ui_logger
from src.dashboard.archive.services.data_service import MarketDataService

# Initialize logger and data service
logger = get_ui_logger("dashboard")
data_service = MarketDataService()

# Constants
CHART_COLORS = {
    'primary': '#2fa4e7',  # Cerulean Primary Blue
    'success': '#73a839',  # Cerulean Success Green
    'info': '#033c73'      # Cerulean Info Dark Blue
}

# Helper functions
def create_empty_chart(title="No Data Available"):
    """Create an empty chart with a message"""
    return go.Figure(
        data=[],
        layout=go.Layout(
            title=title,
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            annotations=[{
                'text': 'No data available',
                'xref': 'paper',
                'yref': 'paper',
                'showarrow': False,
                'font': {'size': 14}
            }],
            template='plotly_white',
            margin=dict(l=40, r=40, t=60, b=40),
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
    )

def create_horizontal_bar_chart(data, title, color=CHART_COLORS['primary']):
    """Create a horizontal bar chart"""
    if not data or not data.get('categories') or not data.get('counts'):
        return create_empty_chart(title)
    
    # Sort by count in descending order
    sorted_data = sorted(zip(data['categories'], data['counts']), 
                        key=lambda x: x[1], reverse=True)
    categories, counts = zip(*sorted_data)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=counts,
        y=categories,
        orientation='h',
        marker_color='blue',
        hovertemplate='<b>%{y}</b><br>Count: %{x}<extra></extra>'
    ))
    
    fig.update_layout(
        title=title,
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
        margin=dict(l=40, r=40, t=60, b=40),
        height=300,
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    return fig

def create_chart_card(chart_id, height="400px"):
    """Create a card container for charts"""
    return dbc.Card([
        dbc.CardBody([
            dcc.Graph(id=chart_id, style={'height': height})
        ], className="p-0")
    ], style={"border": "none", "box-shadow": "none"})

# Initialize Dash app with Bootstrap Cerulean theme
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.CERULEAN,
        "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"
    ],
    suppress_callback_exceptions=True
)

# Simple layout with navigation and header
app.layout = dbc.Container([
    # Interval to trigger initial callbacks
    dcc.Interval(id="initial-interval", interval=1000, n_intervals=0),
    
    # Navigation Bar
    dbc.Navbar(
        dbc.Container([
            dbc.NavbarBrand("ML Trading", className="text-white"),
            dbc.Nav([
                dbc.NavItem(dbc.NavLink("Dashboard", href="#", className="text-white")),
                dbc.NavItem(dbc.NavLink("Logs", href="#", className="text-white")),
                dbc.NavItem(dbc.NavLink("Settings", href="#", className="text-white")),
                dbc.NavItem(dbc.NavLink("Help", href="#", className="text-white"))
            ], className="me-auto")
        ]),
        color="primary",
        dark=True,
        className="mb-4"
    ),
    
    # Header
    dbc.Row([
        dbc.Col([
            html.Div([
                html.H2("ML Trading Dashboard", className="text-center mb-2"),
                html.P("Welcome Nishant, Good Evening", className="text-center text-muted mb-0")
            ])
        ])
    ], className="mb-4"),
    
    # Main Content Area with Tabs
    dbc.Row([
        dbc.Col([
            dbc.Tabs([
                dbc.Tab(
                    dbc.Card([
                        dbc.CardHeader("Overview", className="text-center p-2"),
                        dbc.CardBody([
                            html.Div([
                                html.H5("Market Overview", className="text-center mb-3"),
                                html.P("Real-time market data and analysis will be displayed here.", className="text-center text-muted")
                            ], className="p-4")
                        ], className="p-0")
                    ], style={"border": "none", "box-shadow": "none"}),
                    label="Overview",
                    tab_id="overview-tab"
                ),
                dbc.Tab(
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
                                            html.H6("Chart Controls", className="text-center mb-3"),
                                            dbc.Row([
                                                dbc.Col([
                                                    html.Label("Select Symbol:", className="form-label"),
                                                    dcc.Dropdown(
                                                        id="symbol-dropdown",
                                                        options=[],
                                                        value="AAPL",
                                                        className="mb-3"
                                                    )
                                                ], width=6),
                                                dbc.Col([
                                                    html.Label("Time Range:", className="form-label"),
                                                    dcc.Dropdown(
                                                        id="time-range-dropdown",
                                                        options=[
                                                            {"label": "1 Day", "value": "1d"},
                                                            {"label": "1 Week", "value": "1w"},
                                                            {"label": "1 Month", "value": "1m"},
                                                            {"label": "3 Months", "value": "3m"},
                                                            {"label": "1 Year", "value": "1y"}
                                                        ],
                                                        value="1m",
                                                        className="mb-3"
                                                    )
                                                ], width=6)
                                            ]),
                                            dbc.Button("Refresh Data", id="refresh-data-btn", color="primary", className="w-100")
                                        ], className="p-3")
                                    ], style={"border": "none", "box-shadow": "none"})
                                ], width=12)
                            ], className="mb-3"),
                            
                            # Price Chart Row
                            dbc.Row([
                                dbc.Col([
                                    create_chart_card("price-chart", "400px")
                                ], width=12)
                            ], className="mb-3")
                        ], className="p-0")
                    ], style={"border": "none", "box-shadow": "none"}),
                    label="Charts",
                    tab_id="charts-tab"
                ),
                dbc.Tab(
                    dbc.Card([
                        dbc.CardHeader("Analysis", className="text-center p-2"),
                        dbc.CardBody([
                            html.Div([
                                html.H5("Trading Analysis", className="text-center mb-3"),
                                html.P("Advanced trading analysis and insights will be displayed here.", className="text-center text-muted")
                            ], className="p-4")
                        ], className="p-0")
                    ], style={"border": "none", "box-shadow": "none"}),
                    label="Analysis",
                    tab_id="analysis-tab"
                ),
                dbc.Tab(
                    dbc.Card([
                        dbc.CardHeader("Settings", className="text-center p-2"),
                        dbc.CardBody([
                            html.Div([
                                html.H5("Dashboard Settings", className="text-center mb-3"),
                                html.P("Configure your dashboard preferences and trading parameters.", className="text-center text-muted")
                            ], className="p-4")
                        ], className="p-0")
                    ], style={"border": "none", "box-shadow": "none"}),
                    label="Settings",
                    tab_id="settings-tab"
                )
            ], id="dashboard-tabs", active_tab="overview-tab")
        ])
    ], className="mb-3"),
    
    # Footer
    dbc.Row([
        dbc.Col([
            html.Div([
                html.Span("Last Updated: ", className="text-muted"),
                html.Span("2nd Aug, 2025 5:54 PM", className="text-muted")
            ], className="text-center")
        ])
    ], className="mt-5")
    
], fluid=True)

# Callbacks
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
        # Convert time range to days
        time_range_days = {
            '1d': 1,
            '1w': 7,
            '1m': 30,
            '3m': 90,
            '1y': 365
        }
        
        days = time_range_days.get(time_range, 30)  # Default to 30 days
        
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
            title=f"{symbol} Price Chart ({time_range})",
            xaxis_title="Date",
            yaxis_title="Price ($)",
            height=350,
            margin=dict(l=40, r=40, t=40, b=40),
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
            title="Sector Distribution",
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
            margin=dict(l=40, r=40, t=60, b=40),
            bargap=0.2,
            bargroupgap=0.1,
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
        
        return fig
        
    except Exception as e:
        logger.error(f"Error updating sector chart: {e}")
        # Return empty chart on error
        return go.Figure()

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
                title="Industry Distribution",
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
                margin=dict(l=40, r=40, t=60, b=40),
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
        return go.Figure()

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

if __name__ == '__main__':
    print("Starting simple Dash dashboard...")
    app.run(debug=True, host='0.0.0.0', port=8050) 