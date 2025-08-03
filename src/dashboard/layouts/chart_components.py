"""
Chart components for the dashboard.
Contains reusable chart creation functions.
"""

import plotly.graph_objs as go
import plotly.express as px
from dash import html, dcc
import pandas as pd

# Constants
CHART_COLORS = {
    'primary': '#2fa4e7',  # Cerulean Primary Blue
    'success': '#73a839',  # Cerulean Success Green
    'danger': '#c71c22',   # Cerulean Danger Red
    'secondary': '#e9ecef', # Cerulean Secondary Gray
    'warning': '#dd5600',  # Cerulean Warning Orange
    'info': '#033c73'      # Cerulean Info Dark Blue
}

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
    
    fig = go.Figure(data=[
        go.Bar(
            x=counts,
            y=categories,
            orientation='h',
            marker=dict(color=color),
            hovertemplate='<b>%{y}</b><br>Count: %{x}<extra></extra>'
        )
    ])
    
    fig.update_layout(
        title=title,
        xaxis=dict(
            title="",
            showgrid=False,
            zeroline=False,
            showticklabels=False,
            tickcolor=CHART_COLORS['secondary']
        ),
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            tickcolor=CHART_COLORS['secondary'],
            tickfont=dict(size=10),
            ticklen=0,
            ticklabelstandoff=5
        ),
        margin=dict(l=40, r=40, t=60, b=40),
        template='plotly_white',
        height=400,
        plot_bgcolor='white',
        paper_bgcolor='white',
        bargap=0.1,
        bargroupgap=0.05
    )
    
    return fig

def create_price_chart(data):
    """Create a price chart from OHLC data"""
    if data.empty:
        return create_empty_chart("No Price Data Available")
    
    fig = go.Figure(data=[
        go.Scatter(
            x=data.index,
            y=data['close'],
            mode='lines',
            name='Close Price',
            line=dict(color=CHART_COLORS['primary'], width=2),
            hovertemplate='<b>%{x}</b><br>Price: $%{y:.2f}<extra></extra>'
        )
    ])
    
    fig.update_layout(
        title="Price Chart",
        xaxis_title="Date",
        yaxis_title="Price ($)",
        height=350,
        margin=dict(l=40, r=40, t=40, b=40),
        showlegend=False,
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    return fig

def create_volume_chart(data):
    """Create a volume chart"""
    if data.empty:
        return create_empty_chart("No Volume Data Available")
    
    fig = go.Figure(data=[
        go.Bar(
            x=data.index,
            y=data['volume'],
            name='Volume',
            marker=dict(color=CHART_COLORS['info']),
            hovertemplate='<b>%{x}</b><br>Volume: %{y:,.0f}<extra></extra>'
        )
    ])
    
    fig.update_layout(
        title="Volume Chart",
        xaxis_title="Date",
        yaxis_title="Volume",
        height=200,
        margin=dict(l=40, r=40, t=40, b=40),
        showlegend=False,
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    return fig

def create_candlestick_chart(data, symbol="", time_range=""):
    """Create a candlestick chart from OHLC data"""
    if data.empty:
        return create_empty_chart(f"No Data Available for {symbol}")
    
    fig = go.Figure(data=[
        go.Candlestick(
            x=data['timestamp'],
            open=data['open'],
            high=data['high'],
            low=data['low'],
            close=data['close'],
            name=symbol,
            increasing_line_color=CHART_COLORS['success'],
            decreasing_line_color=CHART_COLORS['danger']
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
    
    return fig

def create_stats_card(title, value, change=None, change_type="neutral", id=None):
    """Create a stats card"""
    card_content = [
        html.H6(title, className="card-subtitle mb-2 text-muted"),
        html.H4(value, className="card-title mb-0", id=id)
    ]
    
    if change is not None:
        change_class = {
            "positive": "text-success",
            "negative": "text-danger", 
            "neutral": "text-muted"
        }.get(change_type, "text-muted")
        
        card_content.append(
            html.Small(f"({change})", className=f"card-text {change_class}")
        )
    
    return html.Div(card_content, className="card-body")

def create_chart_card(title, chart_id, height="400px"):
    """Create a card container for a chart"""
    return html.Div([
        html.Div([
            dcc.Graph(
                id=chart_id,
                config={'displayModeBar': False},
                style={'height': height}
            )
        ], className="card-body")
    ], className="card h-100")

def create_signals_html(signals):
    """Create HTML for recent signals"""
    if not signals:
        return html.P("No recent signals available", className="text-muted")
    
    signal_items = []
    for signal in signals:
        signal_class = {
            'BUY': 'text-success',
            'SELL': 'text-danger',
            'HOLD': 'text-muted'
        }.get(signal['signal'], 'text-muted')
        
        signal_items.append(html.Li([
            html.Strong(signal['date']), " - ",
            html.Span(signal['signal'], className=signal_class), " - ",
            html.Span(f"${signal['price']:.2f}")
        ], className="list-group-item"))
    
    return html.Ul(signal_items, className="list-group list-group-flush") 