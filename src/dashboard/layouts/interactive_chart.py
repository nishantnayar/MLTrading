"""
Interactive chart components with technical indicators and advanced controls.
Provides comprehensive chart analysis tools for trading dashboard.
"""

import plotly.graph_objs as go
from plotly.subplots import make_subplots
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, callback_context
import pandas as pd
from typing import Dict, List, Any, Optional

from ..services.technical_indicators import TechnicalIndicatorService
from ..services.market_data_service import MarketDataService

from ...utils.logging_config import get_ui_logger

logger = get_ui_logger("interactive_chart")


class InteractiveChartBuilder:
    """Builder for creating interactive charts with technical indicators."""


    def __init__(self):
        self.indicator_service = TechnicalIndicatorService()
        self.market_service = MarketDataService()
        self.chart_config = self.indicator_service.get_indicator_config()

        # Debug: Check chart configuration
        logger.info(f"Chart configuration loaded: {list(self.chart_config.keys())}")
        if 'bollinger' in self.chart_config:
            logger.info(f"Bollinger Bands config: {self.chart_config['bollinger']}")
        else:
            logger.warning("Bollinger Bands config not found!")


    def get_chart_colors(self):
        """Get chart colors from constants"""
        from ..config.constants import CHART_COLORS
        return CHART_COLORS


    def create_advanced_price_chart(self,
                                  df: pd.DataFrame,
                                  symbol: str,
                                  indicators: List[str] = None,
                                  show_volume: bool = True,
                                  chart_type: str = 'candlestick',
                                  volume_display: str = 'bars_ma',
                                  color_by_price: bool = True) -> go.Figure:
        """
        Create advanced price chart with technical indicators and volume.

        Args:
            df: Market data DataFrame
            symbol: Stock symbol
            indicators: List of indicators to display
            show_volume: Whether to show volume subplot
            chart_type: Type of chart ('candlestick', 'ohlc', 'line', 'bar')
            volume_display: Volume display mode ('bars', 'bars_ma', 'profile')
            color_by_price: Whether to color volume bars by price direction

        Returns:
            Plotly figure with advanced features
        """
        try:
            if df.empty:
                return self._create_empty_chart(f"No data available for {symbol}")

            # Calculate technical indicators
            indicator_data = self.indicator_service.calculate_all_indicators(df)

            # Determine subplot configuration with better height allocation

            oscillator_indicators = []
            if indicators:
                oscillator_indicators = [ind for ind in indicators
                                       if self.chart_config.get(ind, {}).get('type') == 'oscillator']

            # Improved height allocation with more generous space for volume
            total_rows = 1
            if show_volume and oscillator_indicators:
                # Price: 60%, Volume: 25%, Oscillators: 15% (more volume space)
                row_heights = [0.60, 0.25, 0.15]
                total_rows = 3
            elif show_volume:
                # Price: 70%, Volume: 30% (even more space for volume when no oscillators)
                row_heights = [0.70, 0.30]
                total_rows = 2
            elif oscillator_indicators:
                # Price: 75%, Oscillators: 25%
                row_heights = [0.75, 0.25]
                total_rows = 2
            else:
                # Price only: 100%
                row_heights = [1.0]

            # Create subplots
            fig = make_subplots(
                rows=total_rows,
                cols=1,
                shared_xaxes=True,
                vertical_spacing=0.05,
                row_heights=row_heights,
                specs=[[{"secondary_y": False}] for _ in range(total_rows)]
            )

            # Add main price chart
            self._add_price_chart(fig, df, symbol, chart_type, 1)

            # Add technical indicators overlays
            if indicators:
                logger.info(f"Adding overlay indicators: {indicators}")
                self._add_overlay_indicators(fig, df, indicator_data, indicators, 1)
            else:
                logger.info("No indicators specified for overlay")

            # Add volume chart
            current_row = 2
            if show_volume:
                self._add_volume_chart(fig, df, indicator_data, current_row, volume_display, color_by_price)
                current_row += 1

            # Add oscillator charts (all in one subplot)
            if oscillator_indicators:
                self._add_oscillator_charts(fig, df, indicator_data, oscillator_indicators, current_row)
                current_row += 1

            # Update layout with advanced features
            self._update_chart_layout(fig, symbol, total_rows)

            return fig

        except Exception as e:
            logger.error(f"Error creating advanced chart: {e}")
            return self._create_empty_chart(f"Error loading chart for {symbol}")


    def _add_price_chart(self, fig: go.Figure, df: pd.DataFrame, symbol: str, chart_type: str, row: int):
        """Add main price chart (candlestick, OHLC, or line)."""
        colors = self.get_chart_colors()

        if chart_type == 'candlestick':
            fig.add_trace(
                go.Candlestick(
                    x=df['timestamp'],
                    open=df['open'],
                    high=df['high'],
                    low=df['low'],
                    close=df['close'],
                    name=symbol,
                    increasing_line_color=colors['success'],
                    decreasing_line_color=colors['danger'],
                    showlegend=False
                ),
                row=row, col=1
            )
        elif chart_type == 'ohlc':
            fig.add_trace(
                go.Ohlc(
                    x=df['timestamp'],
                    open=df['open'],
                    high=df['high'],
                    low=df['low'],
                    close=df['close'],
                    name=symbol,
                    increasing_line_color=colors['success'],
                    decreasing_line_color=colors['danger'],
                    showlegend=False
                ),
                row=row, col=1
            )
        elif chart_type == 'line':
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=df['close'],
                    mode='lines',
                    name=f'{symbol} Close',
                    line=dict(color=colors['primary'], width=2),
                    showlegend=False
                ),
                row=row, col=1
            )
        elif chart_type == 'bar':
            # Create bar chart using OHLC data - bars colored by price direction
            bar_colors = []
            for i in range(len(df)):
                if df['close'].iloc[i] >= df['open'].iloc[i]:
                    bar_colors.append(colors['success'])  # Green for up days
                else:
                    bar_colors.append(colors['danger'])   # Red for down days

            fig.add_trace(
                go.Bar(
                    x=df['timestamp'],
                    y=df['close'],
                    name=f'{symbol} Close',
                    marker=dict(color=bar_colors),
                    showlegend=False,
                    hovertemplate='<b>%{x}</b><br>Close: $%{y:.2f}<extra></extra>'
                ),
                row=row, col=1
            )


    def _add_overlay_indicators(self, fig: go.Figure, df: pd.DataFrame, indicator_data: Dict, indicators: List[str], row: int):
        """Add overlay indicators (SMA, EMA, Bollinger Bands, etc.)."""
        logger.info(f"Adding overlay indicators: {indicators}")
        logger.info(f"Available indicator data: {list(indicator_data.keys())}")

        for indicator in indicators:
            config = self.chart_config.get(indicator, {})
            logger.info(f"Processing indicator: {indicator}, config: {config}")

            if config.get('type') != 'overlay':
                logger.info(f"Skipping {indicator} - not an overlay indicator")
                continue

            if indicator == 'sma':
                # Add multiple SMA periods
                for period in [20, 50]:
                    if f'sma_{period}' in indicator_data:
                        fig.add_trace(
                            go.Scatter(
                                x=df['timestamp'],
                                y=indicator_data[f'sma_{period}'],
                                mode='lines',
                                name=f'SMA({period})',
                                line=dict(color=config['color'], width=1.5),
                                opacity=0.8
                            ),
                            row=row, col=1
                        )

            elif indicator == 'ema':
                # Add multiple EMA periods
                for period in [12, 26]:
                    if f'ema_{period}' in indicator_data:
                        fig.add_trace(
                            go.Scatter(
                                x=df['timestamp'],
                                y=indicator_data[f'ema_{period}'],
                                mode='lines',
                                name=f'EMA({period})',
                                line=dict(color=config['color'], width=1.5, dash='dot'),
                                opacity=0.8
                            ),
                            row=row, col=1
                        )

            elif indicator == 'bollinger' and 'bollinger' in indicator_data:
                bb = indicator_data['bollinger']
                colors = config.get('colors', {})

                # Debug logging
                logger.info(f"Adding Bollinger Bands: {bb.keys()}")
                logger.info(f"Bollinger Bands data sample: upper={bb['upper'].iloc[-5:].tolist() if not bb['upper'].empty else 'empty'}")
                logger.info(f"Bollinger Bands colors: {colors}")

                # Check if we have valid data
                if bb['upper'].empty or bb['lower'].empty or bb['middle'].empty:
                    logger.warning("Bollinger Bands data is empty, skipping")
                    continue

                # Add Bollinger Bands
                fig.add_trace(
                    go.Scatter(
                        x=df['timestamp'],
                        y=bb['upper'],
                        mode='lines',
                        name='BB Upper',
                        line=dict(color=colors.get('upper', '#dc3545'), width=1),
                        opacity=0.6
                    ),
                    row=row, col=1
                )

                fig.add_trace(
                    go.Scatter(
                        x=df['timestamp'],
                        y=bb['lower'],
                        mode='lines',
                        name='BB Lower',
                        line=dict(color=colors.get('lower', '#dc3545'), width=1),
                        fill='tonexty',
                        fillcolor='rgba(220, 53, 69, 0.1)',
                        opacity=0.6
                    ),
                    row=row, col=1
                )

                fig.add_trace(
                    go.Scatter(
                        x=df['timestamp'],
                        y=bb['middle'],
                        mode='lines',
                        name='BB Middle',
                        line=dict(color=colors.get('middle', '#6c757d'), width=1, dash='dash'),
                        opacity=0.8
                    ),
                    row=row, col=1
                )

            elif indicator == 'vwap' and 'vwap' in indicator_data:
                fig.add_trace(
                    go.Scatter(
                        x=df['timestamp'],
                        y=indicator_data['vwap'],
                        mode='lines',
                        name='VWAP',
                        line=dict(color=config['color'], width=2),
                        opacity=0.8
                    ),
                    row=row, col=1
                )


    def _add_volume_chart(self, fig: go.Figure, df: pd.DataFrame, indicator_data: Dict, row: int, volume_display: str = 'bars_ma', color_by_price: bool = True):
        """Add volume chart with configurable display options."""
        colors = self.get_chart_colors()

        # Color volume bars based on price movement if enabled
        if color_by_price:
            bar_colors = []
            for i in range(len(df)):
                if i == 0:
                    bar_colors.append(colors['primary'])
                else:
                    # Color based on price direction
                    color = colors['success'] if df.iloc[i]['close'] >= df.iloc[i-1]['close'] else colors['danger']
                    bar_colors.append(color)
        else:
            # Use single color for all bars
            bar_colors = colors['info']

        # Add volume bars (always show for now)
        fig.add_trace(
            go.Bar(
                x=df['timestamp'],
                y=df['volume'],
                name='Volume',
                marker_color=bar_colors,
                opacity=0.7,
                showlegend=False,
                hovertemplate='<b>%{x}</b><br>Volume: %{y:,.0f}<extra></extra>'
            ),
            row=row, col=1
        )

        # Add volume SMA if available and requested
        if volume_display in ['bars_ma'] and 'volume_sma' in indicator_data:
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=indicator_data['volume_sma'],
                    mode='lines',
                    name='Volume SMA(20)',
                    line=dict(color=colors['warning'], width=2),
                    opacity=0.8,
                    hovertemplate='<b>%{x}</b><br>Volume SMA: %{y:,.0f}<extra></extra>'
                ),
                row=row, col=1
            )


    def _add_oscillator_chart(self, fig: go.Figure, df: pd.DataFrame, indicator_data: Dict, indicator: str, row: int):
        """Add oscillator charts (RSI, MACD, Stochastic)."""
        config = self.chart_config.get(indicator, {})

        if indicator == 'rsi' and 'rsi' in indicator_data:
            # Add RSI line
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=indicator_data['rsi'],
                    mode='lines',
                    name='RSI(14)',
                    line=dict(color=config['color'], width=2),
                    showlegend=False
                ),
                row=row, col=1
            )

            # Add overbought/oversold lines
            fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.5, row=row, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.5, row=row, col=1)
            fig.add_hline(y=50, line_dash="dot", line_color="gray", opacity=0.3, row=row, col=1)

        elif indicator == 'macd' and 'macd' in indicator_data:
            macd_data = indicator_data['macd']
            colors = config['colors']

            # Add MACD line
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=macd_data['macd'],
                    mode='lines',
                    name='MACD',
                    line=dict(color=colors['macd'], width=2),
                    showlegend=False
                ),
                row=row, col=1
            )

            # Add Signal line
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=macd_data['signal'],
                    mode='lines',
                    name='Signal',
                    line=dict(color=colors['signal'], width=1.5),
                    showlegend=False
                ),
                row=row, col=1
            )

            # Add Histogram
            fig.add_trace(
                go.Bar(
                    x=df['timestamp'],
                    y=macd_data['histogram'],
                    name='Histogram',
                    marker_color=colors['histogram'],
                    opacity=0.6,
                    showlegend=False
                ),
                row=row, col=1
            )

        elif indicator == 'stochastic' and 'stochastic' in indicator_data:
            stoch_data = indicator_data['stochastic']
            colors = config['colors']

            # Add %K line
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=stoch_data['k_percent'],
                    mode='lines',
                    name='%K',
                    line=dict(color=colors['k'], width=2),
                    showlegend=False
                ),
                row=row, col=1
            )

            # Add %D line
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=stoch_data['d_percent'],
                    mode='lines',
                    name='%D',
                    line=dict(color=colors['d'], width=1.5),
                    showlegend=False
                ),
                row=row, col=1
            )

            # Add overbought/oversold lines
            fig.add_hline(y=80, line_dash="dash", line_color="red", opacity=0.5, row=row, col=1)
            fig.add_hline(y=20, line_dash="dash", line_color="green", opacity=0.5, row=row, col=1)


    def _add_oscillator_charts(self, fig: go.Figure, df: pd.DataFrame, indicator_data: Dict, indicators: List[str], row: int):
        """Add multiple oscillator charts in one subplot with normalized scaling."""
        # We'll normalize oscillators to 0-100 range for better visualization
        for indicator in indicators:
            config = self.chart_config.get(indicator, {})

            if indicator == 'rsi' and 'rsi' in indicator_data:
                # RSI is already 0-100, add directly
                fig.add_trace(
                    go.Scatter(
                        x=df['timestamp'],
                        y=indicator_data['rsi'],
                        mode='lines',
                        name='RSI(14)',
                        line=dict(color=config['color'], width=2),
                        yaxis=f'y{row}' if row > 1 else 'y'
                    ),
                    row=row, col=1
                )

                # Add RSI reference lines
                fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.5, row=row, col=1)
                fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.5, row=row, col=1)
                fig.add_hline(y=50, line_dash="dot", line_color="gray", opacity=0.3, row=row, col=1)

            elif indicator == 'stochastic' and 'stochastic' in indicator_data:
                # Stochastic is already 0-100, add directly
                stoch_data = indicator_data['stochastic']
                colors = config['colors']

                fig.add_trace(
                    go.Scatter(
                        x=df['timestamp'],
                        y=stoch_data['k_percent'],
                        mode='lines',
                        name='%K',
                        line=dict(color=colors['k'], width=1.5),
                        yaxis=f'y{row}' if row > 1 else 'y'
                    ),
                    row=row, col=1
                )

                fig.add_trace(
                    go.Scatter(
                        x=df['timestamp'],
                        y=stoch_data['d_percent'],
                        mode='lines',
                        name='%D',
                        line=dict(color=colors['d'], width=1.5),
                        yaxis=f'y{row}' if row > 1 else 'y'
                    ),
                    row=row, col=1
                )

                # Add Stochastic reference lines
                fig.add_hline(y=80, line_dash="dash", line_color="red", opacity=0.5, row=row, col=1)
                fig.add_hline(y=20, line_dash="dash", line_color="green", opacity=0.5, row=row, col=1)

        # Handle MACD separately if present (it has different scaling)
        has_macd = 'macd' in indicators and 'macd' in indicator_data
        has_other_oscillators = any(ind in ['rsi', 'stochastic'] for ind in indicators)

        if has_macd:
            macd_data = indicator_data['macd']
            colors = self.chart_config.get('macd', {}).get('colors', {})

            # Add MACD line
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=macd_data['macd'],
                    mode='lines',
                    name='MACD',
                    line=dict(color=colors.get('macd', '#6f42c1'), width=2),
                    yaxis=f'y{row}2' if has_other_oscillators else f'y{row}' if row > 1 else 'y'
                ),
                row=row, col=1
            )

            # Add Signal line
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=macd_data['signal'],
                    mode='lines',
                    name='Signal',
                    line=dict(color=colors.get('signal', '#e83e8c'), width=1.5),
                    yaxis=f'y{row}2' if has_other_oscillators else f'y{row}' if row > 1 else 'y'
                ),
                row=row, col=1
            )

            # Add Histogram as bar chart
            fig.add_trace(
                go.Bar(
                    x=df['timestamp'],
                    y=macd_data['histogram'],
                    name='Histogram',
                    marker_color=colors.get('histogram', '#20c997'),
                    opacity=0.7,
                    yaxis=f'y{row}2' if has_other_oscillators else f'y{row}' if row > 1 else 'y'
                ),
                row=row, col=1
            )

            # Add zero line for MACD
            fig.add_hline(y=0, line_dash="solid", line_color="gray", opacity=0.5, row=row, col=1)

        # Set appropriate Y-axis range
        if has_other_oscillators and not has_macd:
            # Only RSI/Stochastic - use 0-100 range
            fig.update_yaxes(range=[0, 100], row=row, col=1)
        elif has_macd and not has_other_oscillators:
            # Only MACD - let it auto-scale
            pass
        # If both, they'll share the space with different y-axes


    def _update_chart_layout(self, fig: go.Figure, symbol: str, total_rows: int):
        """Update chart layout with advanced features."""
        colors = self.get_chart_colors()

        fig.update_layout(
            title=dict(
                text=f"{symbol} - Advanced Technical Analysis",
                font=dict(size=20, color=colors['primary']),
                x=0.5,
                xanchor='center'
            ),
            height=600 + (total_rows - 1) * 150,  # Dynamic height based on subplots
            margin=dict(l=50, r=170, t=80, b=50),  # Increased right margin for vertical legend
            plot_bgcolor='white',
            paper_bgcolor='white',
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.02,
                bgcolor="rgba(255, 255, 255, 0.9)",
                bordercolor="rgba(0, 0, 0, 0.1)",
                borderwidth=1
            ),
            hovermode='x unified',
            # Advanced zoom and pan controls
            dragmode='zoom',
        )

        # Update x-axis for all subplots
        for i in range(1, total_rows + 1):
            fig.update_xaxes(
                type='date',
                rangeslider_visible=False,
                rangebreaks=[
                    dict(bounds=["sat", "mon"]),  # Hide weekends
                    dict(bounds=[17, 9], pattern='hour')  # Hide non-trading hours
                ],
                row=i, col=1
            )

            # Only show x-axis labels on bottom subplot
            if i < total_rows:
                fig.update_xaxes(showticklabels=False, row=i, col=1)

        # Add range selector buttons
        fig.update_layout(
            xaxis=dict(
                rangeselector=dict(
                    buttons=list([
                        dict(count=1, label="1D", step="day", stepmode="backward"),
                        dict(count=7, label="7D", step="day", stepmode="backward"),
                        dict(count=30, label="1M", step="day", stepmode="backward"),
                        dict(count=90, label="3M", step="day", stepmode="backward"),
                        dict(count=180, label="6M", step="day", stepmode="backward"),
                        dict(count=365, label="1Y", step="day", stepmode="backward"),
                        dict(step="all", label="ALL")
                    ]),
                    bgcolor=colors['light'],
                    activecolor=colors['primary']
                ),
                type="date"
            )
        )


    def _create_empty_chart(self, message: str) -> go.Figure:
        """Create empty chart with message."""
        fig = go.Figure()
        fig.update_layout(
            title=message,
            xaxis={'visible': False},
            yaxis={'visible': False},
            annotations=[{
                'text': message,
                'xref': 'paper',
                'yref': 'paper',
                'showarrow': False,
                'font': {'size': 16, 'color': '#666666'},
                'x': 0.5,
                'y': 0.5
            }],
            height=400
        )
        return fig


def create_chart_controls() -> html.Div:
    """Create interactive chart control panel."""
    indicator_service = TechnicalIndicatorService()
    chart_config = indicator_service.get_indicator_config()

    # Organize indicators by type
    overlay_indicators = []
    oscillator_indicators = []

    for key, config in chart_config.items():
        option = {'label': config['name'], 'value': key}
        if config['type'] == 'overlay':
            overlay_indicators.append(option)
        elif config['type'] == 'oscillator':
            oscillator_indicators.append(option)

    return dbc.Card([
        dbc.CardHeader([
            dbc.Row([
                dbc.Col([
                    html.H5("Chart Controls", className="mb-0")
                ], width=6),
                dbc.Col([
                    dbc.Button(
                        [html.I(className="fas fa-cog me-1"), "Advanced"],
                        id="chart-controls-toggle",
                        color="outline-secondary",
                        size="sm",
                        className="float-end"
                    )
                ], width=6)
            ])
        ]),
        dbc.CardBody([
            # Main Controls Row - Always Visible
            dbc.Row([
                # Chart Type Selection
                dbc.Col([
                    html.Label("Chart Type:", className="form-label small"),
                    dbc.ButtonGroup([
                        dbc.Button("📈", id="chart-type-candlestick", size="sm",
                                 color="primary", outline=False, className="chart-type-btn",
                                 title="Candlestick"),
                        dbc.Button("📊", id="chart-type-ohlc", size="sm",
                                 color="primary", outline=True, className="chart-type-btn",
                                 title="OHLC"),
                        dbc.Button("📉", id="chart-type-line", size="sm",
                                 color="primary", outline=True, className="chart-type-btn",
                                 title="Line"),
                        dbc.Button("📋", id="chart-type-bar", size="sm",
                                 color="primary", outline=True, className="chart-type-btn",
                                 title="Bar")
                    ], className="w-100"),
                    # Hidden stores
                    dcc.Store(id="chart-type-store", data='candlestick'),
                    dcc.Store(id="overlay-indicators-store", data=['sma', 'ema']),
                    dcc.Store(id="oscillator-indicators-store", data=['rsi'])
                ], width=3),

                # Quick Indicator Toggles
                dbc.Col([
                    html.Label("Quick Indicators:", className="form-label small"),
                    html.Div([
                        dbc.ButtonGroup([
                            dbc.Button("SMA", id="indicator-sma-btn", size="sm",
                                     color="success", outline=False, className="indicator-btn"),
                            dbc.Button("EMA", id="indicator-ema-btn", size="sm",
                                     color="success", outline=False, className="indicator-btn"),
                            dbc.Button("BB", id="indicator-bollinger-btn", size="sm",
                                     color="info", outline=True, className="indicator-btn",
                                     title="Bollinger Bands"),
                            dbc.Button("RSI", id="indicator-rsi-btn", size="sm",
                                     color="warning", outline=False, className="indicator-btn")
                        ], className="w-100")
                    ])
                ], width=6),

                # Volume & Options
                dbc.Col([
                    html.Label("Options:", className="form-label small"),
                    html.Div([
                        dbc.ButtonGroup([
                            dbc.Button("📊", id="volume-toggle-btn", size="sm",
                                     color="info", outline=False, className="volume-btn",
                                     title="Toggle Volume"),
                            dbc.Button("⚙️", id="chart-settings-btn", size="sm",
                                     color="secondary", outline=True,
                                     title="Chart Settings"),
                            dbc.Button("📤", id="export-chart-btn", size="sm",
                                     color="secondary", outline=True,
                                     title="Export Chart")
                        ], className="w-100")
                    ])
                ], width=3)
            ], className="mb-3"),

            # Advanced Controls - Collapsible
            dbc.Collapse([
                html.Hr(),
                dbc.Row([
                    # Overlay Indicators Section
                    dbc.Col([
                        html.Label("Overlay Indicators:", className="form-label small fw-bold"),
                        html.Div([
                            html.Div([
                                dbc.Button(opt['label'],
                                         id=f"overlay-{opt['value']}-btn",
                                         size="sm",
                                         color="success" if opt['value'] in ['sma', 'ema'] else "outline-success",
                                         className="me-1 mb-1 overlay-indicator-btn")
                                for opt in overlay_indicators
                            ])
                        ])
                    ], width=6),

                    # Oscillator Indicators Section
                    dbc.Col([
                        html.Label("Oscillator Indicators:", className="form-label small fw-bold"),
                        html.Div([
                            html.Div([
                                dbc.Button(opt['label'],
                                         id=f"oscillator-{opt['value']}-btn",
                                         size="sm",
                                         color="warning" if opt['value'] == 'rsi' else "outline-warning",
                                         className="me-1 mb-1 oscillator-indicator-btn")
                                for opt in oscillator_indicators
                            ])
                        ])
                    ], width=6)
                ], className="mb-3"),

                dbc.Row([
                    # Volume Options
                    dbc.Col([
                        html.Label("Volume Display:", className="form-label small fw-bold"),
                        dbc.ButtonGroup([
                            dbc.Button("Hide", id="volume-hide-btn", size="sm",
                                     color="outline-secondary", className="volume-display-btn"),
                            dbc.Button("Bars", id="volume-bars-btn", size="sm",
                                     color="info", outline=False, className="volume-display-btn"),
                            dbc.Button("Bars + MA", id="volume-bars-ma-btn", size="sm",
                                     color="outline-info", className="volume-display-btn")
                        ], className="w-100"),
                        dcc.Store(id="volume-display-store", data="bars_ma")
                    ], width=4),

                    # Chart Tools
                    dbc.Col([
                        html.Label("Chart Tools:", className="form-label small fw-bold"),
                        dbc.ButtonGroup([
                            dbc.Button("🖊️", id="trend-line-btn", size="sm", outline=True,
                                     title="Trend Line", className="chart-tool-btn"),
                            dbc.Button("📏", id="support-resistance-btn", size="sm", outline=True,
                                     title="Support/Resistance", className="chart-tool-btn"),
                            dbc.Button("🗑️", id="clear-drawings-btn", size="sm", outline=True,
                                     color="danger", title="Clear All", className="chart-tool-btn")
                        ], className="w-100")
                    ], width=4),

                    # Export Options
                    dbc.Col([
                        html.Label("Export Format:", className="form-label small fw-bold"),
                        dbc.ButtonGroup([
                            dbc.Button("PNG", id="export-png-btn", size="sm", outline=True,
                                     className="export-btn"),
                            dbc.Button("PDF", id="export-pdf-btn", size="sm", outline=True,
                                     className="export-btn"),
                            dbc.Button("SVG", id="export-svg-btn", size="sm", outline=True,
                                     className="export-btn")
                        ], className="w-100")
                    ], width=4)
                ])
            ], id="advanced-chart-controls", is_open=False)
        ])
    ], className="mb-4")


def create_indicator_info_panel() -> html.Div:
    """Create indicator information panel."""
    indicator_service = TechnicalIndicatorService()
    chart_config = indicator_service.get_indicator_config()

    indicator_cards = []
    for key, config in chart_config.items():
        card = dbc.Card([
            dbc.CardBody([
                html.H6(config['name'], className="card-title"),
                html.P(config['description'], className="card-text text-muted small"),
                html.Div([
                    dbc.Badge(config['type'].title(), color="primary", className="me-1"),
                    dbc.Badge(f"Color: {config.get('color', 'Various')}", color="secondary")
                ])
            ])
        ], className="mb-2")
        indicator_cards.append(card)

    return dbc.Collapse([
        html.H5("Technical Indicators Guide", className="mb-3"),
        html.Div(indicator_cards)
    ], id="indicator-info-collapse", is_open=False)

