"""
Callbacks for the comprehensive detailed analysis tab.
Handles visualization of all 90+ features and advanced indicators.
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from dash import Input, Output, callback, html
import dash_bootstrap_components as dbc

from ..services.unified_data_service import MarketDataService


# Initialize services
market_service = MarketDataService()


@callback(
    [Output("detailed-analysis-symbol", "options"),
     Output("detailed-analysis-symbol", "value")],
    [Input("detailed-analysis-symbol", "search_value")]
)
def update_detailed_analysis_symbols(search_value):
    """Update symbol options for detailed analysis dropdown."""
    try:
        symbols = market_service.get_available_symbols()
        options = [{"label": f"{s['symbol']} - {s['company_name']}", "value": s['symbol']} 
                  for s in symbols[:100]]  # Limit to first 100
        
        # Set default value
        default_value = "AAPL" if not search_value else search_value
        
        return options, default_value
    except:
        return [{"label": "AAPL - Apple Inc.", "value": "AAPL"}], "AAPL"


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
                    name="RSI 1D - 1W Diff",
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