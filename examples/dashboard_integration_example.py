"""
Example of integrating data extraction APIs into Dash dashboard.
This shows how to use the APIs in Dash callbacks and components.
"""

import dash
from dash import dcc, html, Input, Output, callback
import plotly.graph_objs as go
import plotly.express as px
from datetime import datetime, timedelta
import pandas as pd

# Import the data service
from src.api.services.data_service import get_data_service

# Initialize Dash app
app = dash.Dash(__name__)

# Initialize data service
data_service = get_data_service()

# Layout with data-driven components
app.layout = html.Div([
    html.H1("ML Trading Dashboard - API Integration Example"),
    
    # Symbol selector using API data
    html.Div([
        html.Label("Select Symbol:"),
        dcc.Dropdown(
            id='symbol-dropdown',
            placeholder="Loading symbols..."
        )
    ]),
    
    # Date range selector
    html.Div([
        html.Label("Date Range:"),
        dcc.DatePickerRange(
            id='date-range',
            start_date=(datetime.now() - timedelta(days=30)).date(),
            end_date=datetime.now().date()
        )
    ]),
    
    # Market data chart
    html.Div([
        html.H3("Market Data"),
        dcc.Graph(id='price-chart')
    ]),
    
    # Stock information
    html.Div([
        html.H3("Stock Information"),
        html.Div(id='stock-info')
    ]),
    
    # Sector analysis
    html.Div([
        html.H3("Sector Analysis"),
        dcc.Dropdown(id='sector-dropdown', placeholder="Select sector..."),
        html.Div(id='sector-stocks')
    ]),
    
    # Data summary
    html.Div([
        html.H3("System Summary"),
        html.Div(id='data-summary')
    ])
])

# Callback to load symbols from API
@callback(
    Output('symbol-dropdown', 'options'),
    Input('symbol-dropdown', 'id')
)
def load_symbols(_):
    """Load available symbols from API."""
    try:
        symbols = data_service.get_symbols()
        return [{'label': symbol, 'value': symbol} for symbol in symbols[:50]]  # Show first 50
    except Exception as e:
        print(f"Error loading symbols: {e}")
        return []

# Callback to load sectors from API
@callback(
    Output('sector-dropdown', 'options'),
    Input('sector-dropdown', 'id')
)
def load_sectors(_):
    """Load available sectors from API."""
    try:
        sectors = data_service.get_sectors()
        return [{'label': sector, 'value': sector} for sector in sectors]
    except Exception as e:
        print(f"Error loading sectors: {e}")
        return []

# Callback to update price chart
@callback(
    Output('price-chart', 'figure'),
    Input('symbol-dropdown', 'value'),
    Input('date-range', 'start_date'),
    Input('date-range', 'end_date')
)
def update_price_chart(symbol, start_date, end_date):
    """Update price chart with data from API."""
    if not symbol or not start_date or not end_date:
        return go.Figure()
    
    try:
        # Convert dates
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
        
        # Get market data from API
        df = data_service.get_market_data(symbol, start_dt, end_dt)
        
        if df.empty:
            return go.Figure().add_annotation(
                text="No data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
        
        # Create candlestick chart
        fig = go.Figure(data=[go.Candlestick(
            x=df['timestamp'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name=symbol
        )])
        
        fig.update_layout(
            title=f'{symbol} Price Chart',
            xaxis_title='Date',
            yaxis_title='Price ($)',
            height=500
        )
        
        return fig
        
    except Exception as e:
        print(f"Error updating chart: {e}")
        return go.Figure().add_annotation(
            text=f"Error loading data: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )

# Callback to update stock information
@callback(
    Output('stock-info', 'children'),
    Input('symbol-dropdown', 'value')
)
def update_stock_info(symbol):
    """Update stock information from API."""
    if not symbol:
        return html.P("Select a symbol to view information")
    
    try:
        stock_info = data_service.get_stock_info(symbol)
        
        if not stock_info:
            return html.P(f"No information available for {symbol}")
        
        return html.Div([
            html.H4(f"Company: {stock_info.get('company_name', 'N/A')}"),
            html.P(f"Sector: {stock_info.get('sector', 'N/A')}"),
            html.P(f"Industry: {stock_info.get('industry', 'N/A')}"),
            html.P(f"Market Cap: ${stock_info.get('market_cap', 0):,.0f}" if stock_info.get('market_cap') else "Market Cap: N/A"),
            html.P(f"Exchange: {stock_info.get('exchange', 'N/A')}"),
            html.P(f"Country: {stock_info.get('country', 'N/A')}")
        ])
        
    except Exception as e:
        return html.P(f"Error loading stock info: {str(e)}")

# Callback to update sector stocks
@callback(
    Output('sector-stocks', 'children'),
    Input('sector-dropdown', 'value')
)
def update_sector_stocks(sector):
    """Update stocks in selected sector from API."""
    if not sector:
        return html.P("Select a sector to view stocks")
    
    try:
        stocks = data_service.get_stocks_by_sector(sector)
        
        if not stocks:
            return html.P(f"No stocks found in {sector}")
        
        # Create a table of stocks
        stock_rows = []
        for i, stock in enumerate(stocks[:20]):  # Show first 20 stocks
            stock_rows.append(html.Tr([
                html.Td(stock),
                html.Td("Click to view")
            ]))
        
        return html.Div([
            html.H4(f"Stocks in {sector}"),
            html.Table([
                html.Thead(html.Tr([html.Th("Symbol"), html.Th("Actions")])),
                html.Tbody(stock_rows)
            ])
        ])
        
    except Exception as e:
        return html.P(f"Error loading sector stocks: {str(e)}")

# Callback to update data summary
@callback(
    Output('data-summary', 'children'),
    Input('symbol-dropdown', 'id')
)
def update_data_summary(_):
    """Update system data summary from API."""
    try:
        summary = data_service.get_data_summary()
        
        return html.Div([
            html.H4("System Overview"),
            html.P(f"Total Symbols: {summary.get('total_symbols', 0)}"),
            html.P(f"Total Sectors: {summary.get('total_sectors', 0)}"),
            html.P(f"Total Industries: {summary.get('total_industries', 0)}"),
            html.H5("Sample Sectors:"),
            html.Ul([html.Li(sector) for sector in summary.get('sectors', [])[:5]]),
            html.H5("Sample Symbols:"),
            html.Ul([html.Li(symbol) for symbol in summary.get('sample_symbols', [])[:5]])
        ])
        
    except Exception as e:
        return html.P(f"Error loading data summary: {str(e)}")

if __name__ == '__main__':
    print("🚀 Starting Dashboard with API Integration")
    print("📊 This example shows how to use data extraction APIs in Dash")
    print("🌐 Dashboard will be available at: http://localhost:8050")
    print("🔗 API is already running at: http://localhost:8000")
    
    app.run_server(debug=True, port=8050) 