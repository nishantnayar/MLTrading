"""
Chart components for the dashboard.
Contains reusable chart creation functions.
"""

import plotly.graph_objs as go
from dash import html
import dash_bootstrap_components as dbc
import pandas as pd

# Import colors from centralized configuration
from ..config import CHART_COLORS


def create_empty_chart(title="No Data Available"):
    """Create an empty chart with a message"""
    return go.Figure(
        data=[],
        layout=go.Layout(
            title=dict(
                text=title,
                font=dict(size=20, color=CHART_COLORS['primary']),
                x=0.5,
                xanchor='center'
            ),
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
            margin=dict(l=40, r=40, t=80, b=40),
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
    )


def create_loading_chart(message="Loading market data..."):
    """Create a loading chart with spinner animation"""
    return go.Figure(
        data=[],
        layout=go.Layout(
            title=dict(
                text="",
                font=dict(size=16, color=CHART_COLORS['primary']),
                x=0.5,
                xanchor='center'
            ),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            annotations=[{
                'text': f'<i class="fas fa-spinner fa-spin"></i> {message}',
                'xref': 'paper',
                'yref': 'paper',
                'showarrow': False,
                'font': {'size': 16, 'color': CHART_COLORS['primary']},
                'x': 0.5,
                'y': 0.5
            }],
            template='plotly_white',
            margin=dict(l=40, r=40, t=80, b=40),
            plot_bgcolor='white',
            paper_bgcolor='white',
            height=400
        )
    )


def create_error_chart(error_type="unknown", details="", symbol=""):
    """Create informative error charts based on error type"""
    error_messages = {
        'no_data': f'No market data available for {symbol}' if symbol else 'No market data available',
        'db_error': 'Database connection issue - please try refreshing',
        'timeout': 'Request timed out - check your connection',
        'network_error': 'Network error - please check your internet connection',
        'api_error': 'External API error - please try again later',
        'validation_error': 'Invalid input parameters provided'
    }

    main_message = error_messages.get(error_type, "An unexpected error occurred")

    # Choose appropriate icon and color based on error type
    error_styles = {
        'no_data': {'icon': 'fas fa-chart-line', 'color': CHART_COLORS['secondary']},
        'db_error': {'icon': 'fas fa-database', 'color': CHART_COLORS['warning']},
        'timeout': {'icon': 'fas fa-clock', 'color': CHART_COLORS['warning']},
        'network_error': {'icon': 'fas fa-wifi', 'color': CHART_COLORS['danger']},
        'api_error': {'icon': 'fas fa-exclamation-triangle', 'color': CHART_COLORS['danger']},
        'validation_error': {'icon': 'fas fa-times-circle', 'color': CHART_COLORS['danger']}
    }

    style = error_styles.get(error_type, {'icon': 'fas fa-question-circle', 'color': CHART_COLORS['secondary']})

    annotation_text = f'<i class="{style["icon"]}"></i><br>{main_message}'
    if details:
        annotation_text += f'<br><small>{details}</small>'

    return go.Figure(
        data=[],
        layout=go.Layout(
            title=dict(
                text="Error Loading Data",
                font=dict(size=18, color=style['color']),
                x=0.5,
                xanchor='center'
            ),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            annotations=[{
                'text': annotation_text,
                'xref': 'paper',
                'yref': 'paper',
                'showarrow': False,
                'font': {'size': 14, 'color': style['color']},
                'x': 0.5,
                'y': 0.5
            }],
            template='plotly_white',
            margin=dict(l=40, r=40, t=80, b=40),
            plot_bgcolor='white',
            paper_bgcolor='white',
            height=400
        )
    )


def create_horizontal_bar_chart(data, title, color=CHART_COLORS['primary']):
    """Create a horizontal bar chart"""
    if not data or not data.get('categories') or not data.get('counts'):
        return create_empty_chart(title)

    # Sort by count in ascending order for horizontal bars (so highest values appear at top)
    # In horizontal bar charts, the last item in the list appears at the top
    sorted_data = sorted(zip(data['categories'], data['counts']),
                        key=lambda x: x[1], reverse=False)
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
        title=dict(
            text=title,
            font=dict(size=20, color=CHART_COLORS['primary']),  # H3 styling with Cerulean blue
            x=0.5,
            xanchor='center'
        ),
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
        margin=dict(l=40, r=40, t=80, b=40),  # Top margin for H3 title
        template='plotly_white',
        height=400,
        plot_bgcolor='white',
        paper_bgcolor='white',
        bargap=0.1,
        bargroupgap=0.05,
        clickmode='event',  # Enable click events for filtering
        selectdirection='any',
        dragmode=False
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
    """Create an enhanced volume chart with color coding and moving average"""
    if data.empty:
        return create_empty_chart("No Volume Data Available")

    # Calculate volume moving average
    volume_ma = data['volume'].rolling(window=20).mean()

    # Color code volume bars based on price direction and volume level
    colors = []
    for i in range(len(data)):
        vol = data['volume'].iloc[i]
        avg_vol = volume_ma.iloc[i] if not pd.isna(volume_ma.iloc[i]) else vol

        # Determine price direction if OHLC data available
        if 'close' in data.columns and 'open' in data.columns:
            price_up = data['close'].iloc[i] >= data['open'].iloc[i]
        else:
            price_up = True  # Default color

        # Determine volume level
        high_volume = vol > (avg_vol * 1.5) if avg_vol > 0 else False

        if high_volume:
            colors.append(CHART_COLORS['success'] if price_up else CHART_COLORS['danger'])
        else:
            colors.append(CHART_COLORS['info'] if price_up else CHART_COLORS['warning'])

    fig = go.Figure()

    # Add volume bars
    fig.add_trace(go.Bar(
        x=data.index,
        y=data['volume'],
        name='Volume',
        marker=dict(color=colors),
        hovertemplate='<b>%{x}</b><br>Volume: %{y:,.0f}<br>vs 20MA: %{customdata:.1f}x<extra></extra>',
        customdata=[data['volume'].iloc[i] / volume_ma.iloc[i] if not pd.isna(volume_ma.iloc[i]) and volume_ma.iloc[i] > 0 else 1 for i in range(len(data))]
    ))

    # Add volume moving average line
    fig.add_trace(go.Scatter(
        x=data.index,
        y=volume_ma,
        mode='lines',
        name='20-Day MA',
        line=dict(color=CHART_COLORS['secondary'], width=2, dash='dash'),
        hovertemplate='<b>%{x}</b><br>20-Day MA: %{y:,.0f}<extra></extra>'
    ))

    fig.update_layout(
        title="Volume Chart with Moving Average",
        xaxis_title="Date",
        yaxis_title="Volume",
        height=250,  # Slightly taller for better visibility
        margin=dict(l=40, r=40, t=40, b=40),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
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
        title=dict(
            text=f"{symbol} Price Chart ({time_range})",
            font=dict(size=20, color=CHART_COLORS['primary']),  # H3 styling with Cerulean blue
            x=0.5,
            xanchor='center'
        ),
        xaxis_title="Date",
        yaxis_title="Price ($)",
        height=350,
        margin=dict(l=40, r=40, t=80, b=40),  # Top margin for H3 title
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

# Note: create_chart_card function moved to shared_components.py


def create_volume_summary_card(data):
    """Create a summary card for volume analysis"""
    if data.empty or 'volume' not in data.columns:
        return html.Div("No volume data available", className="text-muted")

    # Calculate volume metrics
    current_volume = data['volume'].iloc[-1]
    avg_volume_20 = data['volume'].rolling(window=20).mean().iloc[-1]
    max_volume = data['volume'].max()

    # Volume ratio and status
    volume_ratio = (current_volume / avg_volume_20) if avg_volume_20 > 0 else 0
    volume_status = "High" if volume_ratio > 1.5 else "Normal" if volume_ratio > 0.8 else "Low"
    volume_color = "success" if volume_ratio > 1.5 else "warning" if volume_ratio > 0.8 else "secondary"

    # Format volume function


    def format_volume(vol):
        if vol >= 1e9:
            return f"{vol/1e9:.2f}B"
        elif vol >= 1e6:
            return f"{vol/1e6:.1f}M"
        elif vol >= 1e3:
            return f"{vol/1e3:.0f}K"
        else:
            return f"{vol:.0f}"

    return dbc.Card([
        dbc.CardHeader(html.H6("Volume Analysis", className="mb-0")),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Small("Current Volume", className="text-muted"),
                    html.H5(format_volume(current_volume), className="mb-2")
                ], width=6),
                dbc.Col([
                    html.Small("vs 20-Day Avg", className="text-muted"),
                    html.H5([
                        dbc.Badge(f"{volume_ratio:.1f}x", color=volume_color),
                        " ", volume_status
                    ], className="mb-2")
                ], width=6)
            ]),
            dbc.Progress(
                value=min(100, (current_volume / max_volume) * 100),
                label=f"{(current_volume / max_volume) * 100:.0f}% of max",
                style={"height": "20px"},
                className="mb-2"
            ),
            html.Small([
                "20-Day Avg: ", format_volume(avg_volume_20), " | ",
                "Max: ", format_volume(max_volume)
            ], className="text-muted")
        ])
    ], className="h-100")


def create_volume_heatmap_chart(data, symbol=""):
    """Create a volume heatmap showing volume by hour/day"""
    if data.empty or 'volume' not in data.columns:
        return create_empty_chart("No Volume Data Available")

    try:
        # Create volume intensity chart
        data_copy = data.copy()
        data_copy['date'] = pd.to_datetime(data_copy.index).date
        data_copy['hour'] = pd.to_datetime(data_copy.index).hour if len(data) > 50 else None

        # For daily data, create volume by day of week
        if data_copy['hour'].isna().all():
            data_copy['day_of_week'] = pd.to_datetime(data_copy.index).day_name()
            volume_by_day = data_copy.groupby('day_of_week')['volume'].mean()

            fig = go.Figure(data=[
                go.Bar(
                    x=['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
                    y=[volume_by_day.get(day, 0) for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']],
                    marker=dict(
                        color=[volume_by_day.get(day, 0) for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']],
                        colorscale='Viridis',
                        showscale=True,
                        colorbar=dict(title="Volume")
                    ),
                    hovertemplate='<b>%{x}</b><br>Avg Volume: %{y:,.0f}<extra></extra>'
                )
            ])

            fig.update_layout(
                title=f"{symbol} Average Volume by Day of Week",
                xaxis_title="Day of Week",
                yaxis_title="Average Volume",
                height=300
            )
        else:
            # For intraday data, create heatmap
            pivot_data = data_copy.pivot_table(
                values='volume',
                index='date',
                columns='hour',
                aggfunc='mean'
            )

            fig = go.Figure(data=go.Heatmap(
                z=pivot_data.values,
                x=pivot_data.columns,
                y=pivot_data.index,
                colorscale='Viridis',
                hovertemplate='<b>%{y}</b> %{x}:00<br>Volume: %{z:,.0f}<extra></extra>'
            ))

            fig.update_layout(
                title=f"{symbol} Volume Heatmap",
                xaxis_title="Hour of Day",
                yaxis_title="Date",
                height=400
            )

        return fig

    except Exception:
        return create_empty_chart("Volume Analysis Unavailable")


def create_symbol_comparison_bar_chart(symbols_data, metric='volume', title="Symbol Comparison"):
    """Create a bar chart comparing symbols by various metrics"""
    if not symbols_data or not symbols_data.get('symbols') or not symbols_data.get(metric):
        return create_empty_chart(title)

    symbols = symbols_data['symbols']
    values = symbols_data[metric]

    # Sort by value in descending order
    sorted_data = sorted(zip(symbols, values), key=lambda x: x[1], reverse=True)
    sorted_symbols, sorted_values = zip(*sorted_data)

    fig = go.Figure(data=[
        go.Bar(
            x=sorted_symbols,
            y=sorted_values,
            marker=dict(
                color=sorted_values,
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title=metric.title())
            ),
            hovertemplate='<b>%{x}</b><br>' + metric.title() + ': %{y}<extra></extra>'
        )
    ])

    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=20, color=CHART_COLORS['primary']),
            x=0.5,
            xanchor='center'
        ),
        xaxis=dict(
            title="Symbols",
            tickangle=45,
            showgrid=False,
            tickcolor=CHART_COLORS['secondary']
        ),
        yaxis=dict(
            title=metric.title(),
            showgrid=True,
            gridcolor='rgba(128,128,128,0.2)',
            tickcolor=CHART_COLORS['secondary']
        ),
        margin=dict(l=60, r=40, t=80, b=100),
        template='plotly_white',
        height=400,
        plot_bgcolor='white',
        paper_bgcolor='white'
    )

    return fig


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

