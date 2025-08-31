"""
Callbacks for the comprehensive detailed analysis tab.
Handles visualization of all 90+ features and advanced indicators.
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from dash import Input, Output, callback, html
import dash_bootstrap_components as dbc

from ..services.unified_data_service import MarketDataService
from ..services.feature_data_service import FeatureDataService


# Initialize services
market_service = MarketDataService()
feature_service = FeatureDataService()


@callback(
    Output("detailed-analysis-symbol", "options"),
    [Input("detailed-analysis-symbol", "search_value")]
)


def update_detailed_analysis_symbols(search_value):
    """Update symbol options for detailed analysis dropdown."""
    try:
        symbols = market_service.get_available_symbols()
        options = [{"label": f"{s['symbol']} - {s['company_name']}", "value": s['symbol']}
                  for s in symbols[:100]]  # Limit to first 100

        return options
    except Exception:
        return [{"label": "AAPL - Apple Inc.", "value": "AAPL"}]


@callback(
    Output("macd-detailed-chart", "figure"),
    [Input("detailed-analysis-symbol", "value"),
     Input("detailed-analysis-period", "value")]
)


def update_macd_detailed_chart(symbol, days):
    """Create comprehensive MACD chart with all MACD indicators."""
    if not symbol:
        symbol = "AAPL"

    try:
        # Get comprehensive feature data
        df = feature_service.get_feature_data(symbol=symbol, days=days or 30)

        if df is None or df.empty:
            return create_empty_chart("No MACD data available")

        # Filter for MACD columns
        macd_columns = [col for col in df.columns if 'macd' in col.lower()]

        if not macd_columns:
            return create_empty_chart("No MACD indicators found")

        # Create subplots
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Price & MACD Line', 'MACD Histogram & Signal'),
            vertical_spacing=0.1,
            shared_xaxes=True,
            row_heights=[0.6, 0.4]
        )

        # Add price line
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'], y=df['close'],
                name='Price', line=dict(color='blue', width=2)
            ), row=1, col=1
        )

        # Add MACD indicators
        if 'macd' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'], y=df['macd'],
                    name='MACD', line=dict(color='orange', width=2)
                ), row=1, col=1
            )

        if 'macd_signal' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'], y=df['macd_signal'],
                    name='MACD Signal', line=dict(color='red', width=1)
                ), row=2, col=1
            )

        if 'macd_histogram' in df.columns:
            fig.add_trace(
                go.Bar(
                    x=df['timestamp'], y=df['macd_histogram'],
                    name='MACD Histogram', marker_color='green', opacity=0.7
                ), row=2, col=1
            )

        if 'macd_normalized' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'], y=df['macd_normalized'],
                    name='MACD Normalized', line=dict(color='purple', width=1, dash='dash')
                ), row=2, col=1
            )

        # Update layout
        fig.update_layout(
            title=f"MACD Comprehensive Analysis - {symbol}",
            height=600,
            showlegend=True,
            template="plotly_white"
        )

        fig.update_xaxes(title_text="Date", row=2, col=1)
        fig.update_yaxes(title_text="Price ($)", row=1, col=1)
        fig.update_yaxes(title_text="MACD Values", row=2, col=1)

        return fig

    except Exception as e:
        return create_empty_chart(f"Error loading MACD data: {str(e)}")


@callback(
    Output("ma-ratios-chart", "figure"),
    [Input("detailed-analysis-symbol", "value"),
     Input("detailed-analysis-period", "value")]
)


def update_ma_ratios_chart(symbol, days):
    """Create moving averages and ratios chart."""
    if not symbol:
        symbol = "AAPL"

    try:
        # Get comprehensive feature data
        df = feature_service.get_feature_data(symbol=symbol, days=days or 30)

        if df is None or df.empty:
            return create_empty_chart("No moving averages data available")

        # Find moving average and ratio columns
        ma_columns = [col for col in df.columns if any(ma_term in col.lower()
                     for ma_term in ['ma_', 'price_ma', 'price_to_ma', 'ma_short', 'ma_med', 'ma_long'])]
        ratio_columns = [col for col in df.columns if 'ratio' in col.lower() and 'ma' in col.lower()]

        if not ma_columns and not ratio_columns:
            return create_empty_chart("No moving averages or ratios found")

        # Create subplots
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Price & Moving Averages', 'MA Ratios & Relationships'),
            vertical_spacing=0.1,
            shared_xaxes=True,
            row_heights=[0.6, 0.4]
        )

        # Add price line
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'], y=df['close'],
                name='Price', line=dict(color='blue', width=2)
            ), row=1, col=1
        )

        # Add moving averages
        colors = ['red', 'orange', 'green', 'purple', 'brown']
        for i, col in enumerate(ma_columns[:5]):  # Limit to 5 to avoid clutter
            if col in df.columns and col != 'close':
                fig.add_trace(
                    go.Scatter(
                        x=df['timestamp'], y=df[col],
                        name=col.replace('_', ' ').title(),
                        line=dict(color=colors[i % len(colors)], width=1)
                    ), row=1, col=1
                )

        # Add ratios
        ratio_colors = ['cyan', 'magenta', 'yellow', 'lime', 'pink']
        for i, col in enumerate(ratio_columns[:5]):  # Limit to 5 to avoid clutter
            if col in df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df['timestamp'], y=df[col],
                        name=col.replace('_', ' ').title(),
                        line=dict(color=ratio_colors[i % len(ratio_colors)], width=1)
                    ), row=2, col=1
                )

        # Update layout
        fig.update_layout(
            title=f"Moving Averages & Ratios - {symbol}",
            height=600,
            showlegend=True,
            template="plotly_white"
        )

        fig.update_xaxes(title_text="Date", row=2, col=1)
        fig.update_yaxes(title_text="Price ($)", row=1, col=1)
        fig.update_yaxes(title_text="Ratio Values", row=2, col=1)

        return fig

    except Exception as e:
        return create_empty_chart(f"Error loading moving averages data: {str(e)}")


@callback(
    Output("vol-ratios-chart", "figure"),
    [Input("detailed-analysis-symbol", "value"),
     Input("detailed-analysis-period", "value")]
)


def update_vol_ratios_chart(symbol, days):
    """Create volatility ratios and regime chart."""
    if not symbol:
        symbol = "AAPL"

    try:
        # Get comprehensive feature data
        df = feature_service.get_feature_data(symbol=symbol, days=days or 30)

        if df is None or df.empty:
            return create_empty_chart("No volatility data available")

        # Find volatility ratio columns
        vol_ratio_columns = [col for col in df.columns if 'vol_ratio' in col.lower() or 'vol_of_vol' in col.lower()]
        vol_columns = [col for col in df.columns if any(vol_term in col.lower()
                      for vol_term in ['realized_vol', 'gk_volatility', 'returns_squared'])]

        if not vol_ratio_columns and not vol_columns:
            return create_empty_chart("No volatility ratios found")

        # Create subplots
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Volatility Ratios', 'Volatility Regime Analysis'),
            vertical_spacing=0.1,
            shared_xaxes=True,
            row_heights=[0.6, 0.4]
        )

        # Add volatility ratios
        colors = ['red', 'orange', 'green', 'purple', 'brown']
        for i, col in enumerate(vol_ratio_columns[:5]):
            if col in df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df['timestamp'], y=df[col],
                        name=col.replace('_', ' ').title(),
                        line=dict(color=colors[i % len(colors)], width=2)
                    ), row=1, col=1
                )

        # Add volatility levels for regime analysis
        regime_colors = ['cyan', 'magenta', 'yellow', 'lime']
        for i, col in enumerate(vol_columns[:4]):
            if col in df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df['timestamp'], y=df[col],
                        name=col.replace('_', ' ').title(),
                        line=dict(color=regime_colors[i % len(regime_colors)], width=1, dash='dash')
                    ), row=2, col=1
                )

        # Update layout
        fig.update_layout(
            title=f"Volatility Ratios & Regime - {symbol}",
            height=600,
            showlegend=True,
            template="plotly_white"
        )

        fig.update_xaxes(title_text="Date", row=2, col=1)
        fig.update_yaxes(title_text="Ratio Values", row=1, col=1)
        fig.update_yaxes(title_text="Volatility Levels", row=2, col=1)

        return fig

    except Exception as e:
        return create_empty_chart(f"Error loading volatility ratios: {str(e)}")


@callback(
    Output("advanced-vol-chart", "figure"),
    [Input("detailed-analysis-symbol", "value"),
     Input("detailed-analysis-period", "value")]
)


def update_advanced_vol_chart(symbol, days):
    """Create advanced volatility estimators chart."""
    if not symbol:
        symbol = "AAPL"

    try:
        # Get comprehensive feature data
        df = feature_service.get_feature_data(symbol=symbol, days=days or 30)

        if df is None or df.empty:
            return create_empty_chart("No advanced volatility data available")

        # Find advanced volatility columns
        advanced_vol_columns = [col for col in df.columns if any(vol_term in col.lower()
                               for vol_term in ['gk_volatility', 'atr', 'realized_vol'])]

        if not advanced_vol_columns:
            return create_empty_chart("No advanced volatility estimators found")

        # Create subplots
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Garman-Klass vs Realized Volatility', 'ATR & Advanced Estimators'),
            vertical_spacing=0.1,
            shared_xaxes=True,
            row_heights=[0.5, 0.5]
        )

        # Add GK vs Realized Volatility comparison
        if 'gk_volatility' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'], y=df['gk_volatility'],
                    name='Garman-Klass Volatility',
                    line=dict(color='blue', width=2)
                ), row=1, col=1
            )

        if 'realized_vol_short' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'], y=df['realized_vol_short'],
                    name='Realized Vol (Short)',
                    line=dict(color='red', width=2)
                ), row=1, col=1
            )

        if 'realized_vol_med' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'], y=df['realized_vol_med'],
                    name='Realized Vol (Med)',
                    line=dict(color='orange', width=1, dash='dash')
                ), row=1, col=1
            )

        # Add ATR and other advanced estimators
        if 'atr' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'], y=df['atr'],
                    name='ATR',
                    line=dict(color='green', width=2)
                ), row=2, col=1
            )

        if 'atr_normalized' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'], y=df['atr_normalized'],
                    name='ATR Normalized',
                    line=dict(color='purple', width=1)
                ), row=2, col=1
            )

        if 'vol_of_vol' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'], y=df['vol_of_vol'],
                    name='Vol of Vol',
                    line=dict(color='brown', width=1, dash='dot')
                ), row=2, col=1
            )

        # Update layout
        fig.update_layout(
            title=f"Advanced Volatility Estimators - {symbol}",
            height=600,
            showlegend=True,
            template="plotly_white"
        )

        fig.update_xaxes(title_text="Date", row=2, col=1)
        fig.update_yaxes(title_text="Volatility %", row=1, col=1)
        fig.update_yaxes(title_text="Estimator Values", row=2, col=1)

        return fig

    except Exception as e:
        return create_empty_chart(f"Error loading advanced volatility: {str(e)}")


@callback(
    Output("money-flow-chart", "figure"),
    [Input("detailed-analysis-symbol", "value"),
     Input("detailed-analysis-period", "value")]
)


def update_money_flow_chart(symbol, days):
    """Create money flow analysis chart with MFI and volume indicators."""
    if not symbol:
        symbol = "AAPL"

    try:
        # Get comprehensive feature data
        df = feature_service.get_feature_data(symbol=symbol, days=days or 30)

        if df is None or df.empty:
            return create_empty_chart("No money flow data available")

        # Create subplots
        fig = make_subplots(
            rows=3, cols=1,
            subplot_titles=('Price & Volume', 'Money Flow Index (MFI)', 'Volume Analysis'),
            vertical_spacing=0.08,
            shared_xaxes=True,
            row_heights=[0.4, 0.3, 0.3]
        )

        # Add price
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'], y=df['close'],
                name='Price', line=dict(color='blue', width=2)
            ), row=1, col=1
        )

        # Add volume bars
        fig.add_trace(
            go.Bar(
                x=df['timestamp'], y=df['volume'],
                name='Volume', marker_color='lightblue', opacity=0.7
            ), row=1, col=1
        )

        # Add MFI
        if 'mfi' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'], y=df['mfi'],
                    name='Money Flow Index',
                    line=dict(color='purple', width=2)
                ), row=2, col=1
            )

            # Add MFI reference lines
            fig.add_hline(y=80, line_dash="dash", line_color="red", row=2, col=1)
            fig.add_hline(y=20, line_dash="dash", line_color="green", row=2, col=1)

        # Add volume indicators
        if 'volume_ratio' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'], y=df['volume_ratio'],
                    name='Volume Ratio',
                    line=dict(color='orange', width=2)
                ), row=3, col=1
            )

        if 'log_volume' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'], y=df['log_volume'],
                    name='Log Volume',
                    line=dict(color='red', width=1, dash='dash')
                ), row=3, col=1
            )

        # Update layout
        fig.update_layout(
            title=f"Money Flow Analysis - {symbol}",
            height=700,
            showlegend=True,
            template="plotly_white"
        )

        fig.update_xaxes(title_text="Date", row=3, col=1)
        fig.update_yaxes(title_text="Price ($) / Volume", row=1, col=1)
        fig.update_yaxes(title_text="MFI", row=2, col=1)
        fig.update_yaxes(title_text="Volume Metrics", row=3, col=1)

        return fig

    except Exception as e:
        return create_empty_chart(f"Error loading money flow data: {str(e)}")


@callback(
    Output("vpt-chart", "figure"),
    [Input("detailed-analysis-symbol", "value"),
     Input("detailed-analysis-period", "value")]
)


def update_vpt_chart(symbol, days):
    """Create Volume Price Trend (VPT) chart."""
    if not symbol:
        symbol = "AAPL"

    try:
        # Get comprehensive feature data
        df = feature_service.get_feature_data(symbol=symbol, days=days or 30)

        if df is None or df.empty:
            return create_empty_chart("No VPT data available")

        # Create subplots
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Price & VPT', 'VPT Analysis'),
            vertical_spacing=0.1,
            shared_xaxes=True,
            row_heights=[0.6, 0.4]
        )

        # Add price
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'], y=df['close'],
                name='Price', line=dict(color='blue', width=2)
            ), row=1, col=1
        )

        # Add VPT
        if 'vpt' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'], y=df['vpt'],
                    name='VPT', line=dict(color='green', width=2),
                    yaxis='y2'
                ), row=1, col=1
            )

        # Add VPT moving average and normalized
        if 'vpt_ma' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'], y=df['vpt_ma'],
                    name='VPT MA',
                    line=dict(color='orange', width=2)
                ), row=2, col=1
            )

        if 'vpt_normalized' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'], y=df['vpt_normalized'],
                    name='VPT Normalized',
                    line=dict(color='red', width=1, dash='dash')
                ), row=2, col=1
            )

        # Update layout
        fig.update_layout(
            title=f"Volume Price Trend (VPT) - {symbol}",
            height=600,
            showlegend=True,
            template="plotly_white"
        )

        # Create secondary y-axis for VPT on first subplot
        fig.update_layout(yaxis2=dict(overlaying='y', side='right'))

        fig.update_xaxes(title_text="Date", row=2, col=1)
        fig.update_yaxes(title_text="Price ($)", row=1, col=1)
        fig.update_yaxes(title_text="VPT Analysis", row=2, col=1)

        return fig

    except Exception as e:
        return create_empty_chart(f"Error loading VPT data: {str(e)}")


@callback(
    Output("intraday-features-chart", "figure"),
    [Input("detailed-analysis-symbol", "value"),
     Input("detailed-analysis-period", "value")]
)


def update_intraday_features_chart(symbol, days):
    """Create intraday reference points chart."""
    if not symbol:
        symbol = "AAPL"

    try:
        # Get comprehensive feature data
        df = feature_service.get_feature_data(symbol=symbol, days=days or 30)

        if df is None or df.empty:
            return create_empty_chart("No intraday data available")

        # Find intraday columns
        intraday_columns = [col for col in df.columns if any(term in col.lower()
                           for term in ['intraday', 'overnight_gap', 'returns_from_daily_open', 'position_in_range'])]

        if not intraday_columns:
            return create_empty_chart("No intraday features found")

        # Create subplots
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Price & Intraday Range', 'Intraday Metrics'),
            vertical_spacing=0.1,
            shared_xaxes=True,
            row_heights=[0.6, 0.4]
        )

        # Add price
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'], y=df['close'],
                name='Price', line=dict(color='blue', width=2)
            ), row=1, col=1
        )

        # Add intraday high/low if available
        if 'intraday_high' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'], y=df['intraday_high'],
                    name='Intraday High', line=dict(color='green', width=1, dash='dot')
                ), row=1, col=1
            )

        if 'intraday_low' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'], y=df['intraday_low'],
                    name='Intraday Low', line=dict(color='red', width=1, dash='dot')
                ), row=1, col=1
            )

        # Add intraday metrics
        intraday_metrics = ['position_in_range', 'intraday_range_pct', 'returns_from_daily_open', 'overnight_gap']
        colors = ['purple', 'orange', 'brown', 'pink']

        for i, metric in enumerate(intraday_metrics):
            if metric in df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df['timestamp'], y=df[metric],
                        name=metric.replace('_', ' ').title(),
                        line=dict(color=colors[i % len(colors)], width=1)
                    ), row=2, col=1
                )

        # Update layout
        fig.update_layout(
            title=f"Intraday Reference Points - {symbol}",
            height=600,
            showlegend=True,
            template="plotly_white"
        )

        fig.update_xaxes(title_text="Date", row=2, col=1)
        fig.update_yaxes(title_text="Price ($)", row=1, col=1)
        fig.update_yaxes(title_text="Intraday Metrics", row=2, col=1)

        return fig

    except Exception as e:
        return create_empty_chart(f"Error loading intraday features: {str(e)}")


@callback(
    Output("lagged-features-heatmap", "figure"),
    [Input("detailed-analysis-symbol", "value"),
     Input("detailed-analysis-period", "value")]
)


def update_lagged_features_heatmap(symbol, days):
    """Create lagged features correlation heatmap."""
    if not symbol:
        symbol = "AAPL"

    try:
        # Get comprehensive feature data
        df = feature_service.get_feature_data(symbol=symbol, days=days or 30)

        if df is None or df.empty:
            return create_empty_chart("No lagged features data available")

        # Find lagged feature columns
        lagged_columns = [col for col in df.columns if 'lag_' in col.lower()]

        if not lagged_columns:
            return create_empty_chart("No lagged features found")

        # Add current period features for comparison
        base_features = ['returns', 'realized_vol_short', 'volume_ratio']
        correlation_features = []

        for feature in base_features:
            if feature in df.columns:
                correlation_features.append(feature)

        # Add lagged features
        correlation_features.extend([col for col in lagged_columns if col in df.columns])

        if len(correlation_features) < 2:
            return create_empty_chart("Insufficient features for correlation analysis")

        # Calculate correlation matrix
        correlation_data = df[correlation_features].corr()

        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=correlation_data.values,
            x=[col.replace('_', ' ').title() for col in correlation_data.columns],
            y=[col.replace('_', ' ').title() for col in correlation_data.index],
            colorscale='RdBu',
            zmid=0,
            text=np.round(correlation_data.values, 2),
            texttemplate="%{text}",
            textfont={"size": 10},
            hoverongaps=False
        ))

        fig.update_layout(
            title=f"Lagged Features Correlation - {symbol}",
            height=600,
            template="plotly_white"
        )

        return fig

    except Exception as e:
        return create_empty_chart(f"Error creating correlation heatmap: {str(e)}")


@callback(
    Output("rolling-stats-chart", "figure"),
    [Input("detailed-analysis-symbol", "value"),
     Input("detailed-analysis-period", "value")]
)


def update_rolling_stats_chart(symbol, days):
    """Create rolling statistics chart (Mean, Std, Skew, Kurtosis)."""
    if not symbol:
        symbol = "AAPL"

    try:
        # Get comprehensive feature data
        df = feature_service.get_feature_data(symbol=symbol, days=days or 30)

        if df is None or df.empty:
            return create_empty_chart("No rolling statistics data available")

        # Find rolling statistics columns
        rolling_columns = [col for col in df.columns if any(stat in col.lower()
                          for stat in ['_mean_', '_std_', '_skew_', '_kurt_']) and 'returns' in col.lower()]

        if not rolling_columns:
            return create_empty_chart("No rolling statistics found")

        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Rolling Mean', 'Rolling Std', 'Rolling Skewness', 'Rolling Kurtosis'),
            vertical_spacing=0.1,
            horizontal_spacing=0.1
        )

        # Group by statistic type
        stats_groups = {
            'mean': [col for col in rolling_columns if '_mean_' in col],
            'std': [col for col in rolling_columns if '_std_' in col],
            'skew': [col for col in rolling_columns if '_skew_' in col],
            'kurt': [col for col in rolling_columns if '_kurt_' in col]
        }

        # Colors for different windows
        colors = ['blue', 'red', 'green']

        # Add traces for each statistic
        for i, (stat_type, columns) in enumerate(stats_groups.items()):
            row = (i // 2) + 1
            col = (i % 2) + 1

            for j, column in enumerate(columns[:3]):  # Limit to 3 windows
                if column in df.columns:
                    # Extract window size from column name
                    window = column.split('_')[-1]
                    fig.add_trace(
                        go.Scatter(
                            x=df['timestamp'], y=df[column],
                            name=f'{stat_type.title()} {window}',
                            line=dict(color=colors[j % len(colors)], width=1),
                            showlegend=(i == 0)  # Only show legend for first subplot
                        ), row=row, col=col
                    )

        # Update layout
        fig.update_layout(
            title=f"Rolling Statistics (Mean, Std, Skew, Kurtosis) - {symbol}",
            height=600,
            showlegend=True,
            template="plotly_white"
        )

        return fig

    except Exception as e:
        return create_empty_chart(f"Error loading rolling statistics: {str(e)}")


def create_empty_chart(message):
    """Create an empty chart with a message."""
    return {
        'data': [],
        'layout': {
            'title': message,
            'showlegend': False,
            'template': 'plotly_white',
            'height': 400,
            'annotations': [{
                'text': message,
                'x': 0.5,
                'y': 0.5,
                'xref': 'paper',
                'yref': 'paper',
                'showarrow': False,
                'font': {'size': 16, 'color': 'gray'}
            }]
        }
    }


@callback(
    Output("rsi-multi-chart", "figure"),
    [Input("detailed-analysis-symbol", "value"),
     Input("detailed-analysis-period", "value")]
)


def update_rsi_multi_chart(symbol, days):
    """Create RSI multiple timeframes chart."""
    if not symbol:
        symbol = "AAPL"

    try:
        rsi_data = market_service.get_rsi(symbol, days, '1d')  # Get base data
        feature_data = market_service.feature_service.get_feature_data(symbol, days)

        if feature_data.empty:
            return create_empty_figure("No RSI data available")

        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=["RSI Multiple Timeframes", "RSI Comparison"],
            vertical_spacing=0.1
        )

        # Multiple RSI timeframes
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
        rsi_columns = ['rsi_1d', 'rsi_3d', 'rsi_1w', 'rsi_2w', 'rsi_ema']
        labels = ['1 Day', '3 Days', '1 Week', '2 Weeks', 'EMA RSI']

        for i, (col, label, color) in enumerate(zip(rsi_columns, labels, colors)):
            if col in feature_data.columns:
                fig.add_trace(
                    go.Scatter(
                        x=feature_data.index,
                        y=feature_data[col],
                        name=f"RSI {label}",
                        line=dict(color=color, width=2),
                        hovertemplate=f"RSI {label}: %{{y:.1f}}<extra></extra>"
                    ),
                    row=1, col=1
                )

        # RSI difference (1d vs 1w)
        if 'rsi_1d' in feature_data.columns and 'rsi_1w' in feature_data.columns:
            rsi_diff = feature_data['rsi_1d'] - feature_data['rsi_1w']
            fig.add_trace(
                go.Scatter(
                    x=feature_data.index,
                    y=rsi_diff,
                    name="RSI 1D - 1W Dif",
                    line=dict(color='purple', width=2),
                    fill='tonexty' if len(rsi_diff) > 1 else None,
                    hovertemplate="Difference: %{y:.1f}<extra></extra>"
                ),
                row=2, col=1
            )

        # Add RSI reference lines
        fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.7, row=1, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.7, row=1, col=1)
        fig.add_hline(y=50, line_dash="dot", line_color="gray", opacity=0.5, row=1, col=1)

        fig.update_layout(
            title=f"RSI Analysis - {symbol}",
            height=600,
            showlegend=True,
            template="plotly_white"
        )

        return fig

    except Exception as e:
        return create_empty_figure(f"Error loading RSI data: {str(e)}")


@callback(
    Output("bollinger-detailed-chart", "figure"),
    [Input("detailed-analysis-symbol", "value"),
     Input("detailed-analysis-period", "value")]
)


def update_bollinger_detailed_chart(symbol, days):
    """Create detailed Bollinger Bands chart with position and squeeze."""
    if not symbol:
        symbol = "AAPL"

    try:
        feature_data = market_service.feature_service.get_feature_data(symbol, days)

        if feature_data.empty:
            return create_empty_figure("No Bollinger Bands data available")

        fig = make_subplots(
            rows=3, cols=1,
            subplot_titles=["Price & Bollinger Bands", "BB Position", "BB Squeeze"],
            vertical_spacing=0.08,
            row_heights=[0.6, 0.2, 0.2]
        )

        # Price and Bollinger Bands
        if 'close' in feature_data.columns:
            fig.add_trace(
                go.Scatter(
                    x=feature_data.index,
                    y=feature_data['close'],
                    name="Close Price",
                    line=dict(color='black', width=2)
                ),
                row=1, col=1
            )

        # Bollinger Bands
        bb_cols = ['bb_upper', 'bb_lower', 'price_ma_short']
        bb_names = ['Upper Band', 'Lower Band', 'Middle Band']
        bb_colors = ['red', 'green', 'blue']

        for col, name, color in zip(bb_cols, bb_names, bb_colors):
            if col in feature_data.columns:
                fig.add_trace(
                    go.Scatter(
                        x=feature_data.index,
                        y=feature_data[col],
                        name=name,
                        line=dict(color=color, width=1, dash='dash')
                    ),
                    row=1, col=1
                )

        # BB Position
        if 'bb_position' in feature_data.columns:
            fig.add_trace(
                go.Scatter(
                    x=feature_data.index,
                    y=feature_data['bb_position'],
                    name="BB Position",
                    line=dict(color='purple', width=2),
                    fill='tozeroy'
                ),
                row=2, col=1
            )

            # Add reference lines for BB position
            fig.add_hline(y=0.8, line_dash="dash", line_color="red", opacity=0.7, row=2, col=1)
            fig.add_hline(y=0.2, line_dash="dash", line_color="green", opacity=0.7, row=2, col=1)

        # BB Squeeze
        if 'bb_squeeze' in feature_data.columns:
            fig.add_trace(
                go.Scatter(
                    x=feature_data.index,
                    y=feature_data['bb_squeeze'],
                    name="BB Squeeze",
                    line=dict(color='orange', width=2),
                    fill='tozeroy'
                ),
                row=3, col=1
            )

        fig.update_layout(
            title=f"Bollinger Bands Analysis - {symbol}",
            height=800,
            showlegend=True,
            template="plotly_white"
        )

        return fig

    except Exception as e:
        return create_empty_figure(f"Error loading Bollinger Bands data: {str(e)}")


@callback(
    Output("volatility-spectrum-chart", "figure"),
    [Input("detailed-analysis-symbol", "value"),
     Input("detailed-analysis-period", "value")]
)


def update_volatility_spectrum_chart(symbol, days):
    """Create comprehensive volatility spectrum chart."""
    if not symbol:
        symbol = "AAPL"

    try:
        vol_data = market_service.get_volatility_indicators(symbol, days)

        if not vol_data:
            return create_empty_figure("No volatility data available")

        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=["Volatility Spectrum", "Vol of Vol & Ratios"],
            vertical_spacing=0.1
        )

        # Volatility spectrum
        vol_columns = ['realized_vol_short', 'realized_vol_med', 'realized_vol_long', 'gk_volatility']
        vol_labels = ['12h Realized', '24h Realized', '120h Realized', 'Garman-Klass']
        vol_colors = ['blue', 'green', 'red', 'purple']

        for col, label, color in zip(vol_columns, vol_labels, vol_colors):
            if col in vol_data and not vol_data[col].empty:
                fig.add_trace(
                    go.Scatter(
                        x=vol_data[col].index,
                        y=vol_data[col],
                        name=label,
                        line=dict(color=color, width=2)
                    ),
                    row=1, col=1
                )

        # Vol of Vol and ratios
        if 'vol_of_vol' in vol_data and not vol_data['vol_of_vol'].empty:
            fig.add_trace(
                go.Scatter(
                    x=vol_data['vol_of_vol'].index,
                    y=vol_data['vol_of_vol'],
                    name="Vol of Vol",
                    line=dict(color='black', width=2)
                ),
                row=2, col=1
            )

        if 'vol_ratio_short_med' in vol_data and not vol_data['vol_ratio_short_med'].empty:
            fig.add_trace(
                go.Scatter(
                    x=vol_data['vol_ratio_short_med'].index,
                    y=vol_data['vol_ratio_short_med'],
                    name="Short/Med Ratio",
                    line=dict(color='orange', width=2)
                ),
                row=2, col=1
            )

        fig.update_layout(
            title=f"Volatility Spectrum Analysis - {symbol}",
            height=600,
            showlegend=True,
            template="plotly_white"
        )

        return fig

    except Exception as e:
        return create_empty_figure(f"Error loading volatility data: {str(e)}")


@callback(
    Output("volume-indicators-chart", "figure"),
    [Input("detailed-analysis-symbol", "value"),
     Input("detailed-analysis-period", "value")]
)


def update_volume_indicators_chart(symbol, days):
    """Create volume indicators chart."""
    if not symbol:
        symbol = "AAPL"

    try:
        volume_data = market_service.get_volume_indicators(symbol, days)

        if not volume_data:
            return create_empty_figure("No volume data available")

        fig = make_subplots(
            rows=3, cols=1,
            subplot_titles=["Volume & Volume MA", "Volume Ratio", "Money Flow Index"],
            vertical_spacing=0.1
        )

        # Volume and Volume MA
        if 'volume' in volume_data and 'volume_ma' in volume_data:
            # Get volume from feature data (since volume_data might not have raw volume)
            feature_data = market_service.feature_service.get_feature_data(symbol, days)
            if 'volume' in feature_data.columns:
                fig.add_trace(
                    go.Bar(
                        x=feature_data.index,
                        y=feature_data['volume'],
                        name="Volume",
                        opacity=0.7,
                        marker_color='lightblue'
                    ),
                    row=1, col=1
                )

            if not volume_data['volume_ma'].empty:
                fig.add_trace(
                    go.Scatter(
                        x=volume_data['volume_ma'].index,
                        y=volume_data['volume_ma'],
                        name="Volume MA",
                        line=dict(color='red', width=2)
                    ),
                    row=1, col=1
                )

        # Volume Ratio
        if 'volume_ratio' in volume_data and not volume_data['volume_ratio'].empty:
            fig.add_trace(
                go.Scatter(
                    x=volume_data['volume_ratio'].index,
                    y=volume_data['volume_ratio'],
                    name="Volume Ratio",
                    line=dict(color='purple', width=2),
                    fill='tonexty'
                ),
                row=2, col=1
            )

            # Add reference line at 1.0
            fig.add_hline(y=1.0, line_dash="dash", line_color="gray", opacity=0.7, row=2, col=1)

        # Money Flow Index
        if 'mfi' in volume_data and not volume_data['mfi'].empty:
            fig.add_trace(
                go.Scatter(
                    x=volume_data['mfi'].index,
                    y=volume_data['mfi'],
                    name="Money Flow Index",
                    line=dict(color='green', width=2)
                ),
                row=3, col=1
            )

            # Add MFI reference lines
            fig.add_hline(y=80, line_dash="dash", line_color="red", opacity=0.7, row=3, col=1)
            fig.add_hline(y=20, line_dash="dash", line_color="green", opacity=0.7, row=3, col=1)

        fig.update_layout(
            title=f"Volume Indicators - {symbol}",
            height=800,
            showlegend=True,
            template="plotly_white"
        )

        return fig

    except Exception as e:
        return create_empty_figure(f"Error loading volume data: {str(e)}")


@callback(
    Output("data-availability-summary", "children"),
    [Input("detailed-analysis-symbol", "value")]
)


def update_data_availability_summary(symbol):
    """Update data availability summary."""
    if not symbol:
        symbol = "AAPL"

    try:
        availability = market_service.get_data_availability(symbol)

        if not availability.get('available'):
            return dbc.Alert("No feature data available for this symbol", color="warning")

        cards = []
        for version_info in availability.get('versions', []):
            cards.append(
                dbc.Card([
                    dbc.CardHeader(f"Version {version_info['version']}"),
                    dbc.CardBody([
                        html.P([
                            html.Strong("Records: "),
                            f"{version_info['total_records']:,}"
                        ]),
                        html.P([
                            html.Strong("Date Range: "),
                            version_info['date_range']
                        ]),
                        html.Div([
                            html.H6("Feature Coverage:", className="mb-2"),
                            html.Ul([
                                html.Li(f"RSI: {version_info['coverage']['rsi']}"),
                                html.Li(f"Moving Averages: {version_info['coverage']['moving_averages']}"),
                                html.Li(f"Bollinger Bands: {version_info['coverage']['bollinger_bands']}")
                            ])
                        ])
                    ])
                ], className="mb-2", color="light", outline=True)
            )

        return cards

    except Exception as e:
        return dbc.Alert(f"Error loading availability data: {str(e)}", color="danger")


@callback(
    Output("feature-categories-overview", "children"),
    [Input("detailed-analysis-symbol", "value")]
)


def update_feature_categories_overview(symbol):
    """Update feature categories overview."""
    try:
        metadata = market_service.get_feature_metadata()

        categories = []
        for category, info in metadata.items():
            categories.append(
                dbc.Card([
                    dbc.CardHeader([
                        html.H5([
                            html.I(className="fas fa-folder me-2"),
                            category.replace('_', ' ').title()
                        ], className="mb-0")
                    ]),
                    dbc.CardBody([
                        html.P(info['description'], className="text-muted mb-2"),
                        html.P([
                            html.Strong("Type: "),
                            dbc.Badge(info['type'], color="primary", className="me-2")
                        ]),
                        html.P([
                            html.Strong("Features: "),
                            f"{len(info['features'])} indicators"
                        ]),
                        html.Div([
                            html.P("Sample features:", className="mb-1 small text-muted"),
                            html.Ul([
                                html.Li(feature, className="small") for feature in info['features'][:8]  # Show first 8
                            ] + ([html.Li(f"... and {len(info['features']) - 8} more", className="small text-muted")]
                                if len(info['features']) > 8 else []), className="mb-0")
                        ])
                    ])
                ], className="mb-3", color="light", outline=True)
            )

        return categories

    except Exception as e:
        return dbc.Alert(f"Error loading feature categories: {str(e)}", color="danger")


def create_empty_figure(message="No data available"):
    """Create an empty figure with a message."""
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        xref="paper", yref="paper",
        x=0.5, y=0.5,
        xanchor='center', yanchor='middle',
        font=dict(size=16, color="gray")
    )
    fig.update_layout(
        template="plotly_white",
        height=400,
        showlegend=False,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False)
    )
    return fig


def register_detailed_analysis_callbacks(app):
    """Register all detailed analysis callbacks with the app."""
    # The callbacks are already registered using the @callback decorator
    # This function exists for consistency with other callback modules
    pass

