"""
Heavy analytics components that are lazy-loaded.
Contains computationally intensive analysis components.
"""

import dash_bootstrap_components as dbc
from dash import html, dcc
import plotly.graph_objs as go
import pandas as pd
import numpy as np
from typing import Dict, List, Any

from ..config import CHART_COLORS
from ..services.analytics_service import AnalyticsService
from ...utils.logging_config import get_ui_logger

logger = get_ui_logger("analytics_components")


def create_performance_analysis_layout() -> html.Div:
    """Create performance analysis layout with heavy computations."""
    try:
        analytics_service = AnalyticsService()
        # batch_service = BatchDataService()  # Currently unused

        # Heavy computation: Get top performers for different periods
        daily_performers = analytics_service.get_top_performers(days=1, limit=10)
        weekly_performers = analytics_service.get_top_performers(days=7, limit=10)
        monthly_performers = analytics_service.get_top_performers(days=30, limit=10)

        # Create performance comparison chart
        fig = create_performance_comparison_chart(daily_performers, weekly_performers, monthly_performers)

        return html.Div([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H5("Performance Analysis")),
                        dbc.CardBody([
                            dcc.Graph(figure=fig, id="performance-comparison-chart")
                        ])
                    ])
                ], width=12)
            ], className="mb-4"),

            dbc.Row([
                dbc.Col([
                    create_performers_table("Daily Top Performers", daily_performers)
                ], width=4),
                dbc.Col([
                    create_performers_table("Weekly Top Performers", weekly_performers)
                ], width=4),
                dbc.Col([
                    create_performers_table("Monthly Top Performers", monthly_performers)
                ], width=4)
            ])
        ])

    except Exception as e:
        logger.error(f"Error creating performance analysis: {e}")
        return dbc.Alert([
            html.H5("Error", className="alert-heading"),
            html.P(f"Failed to load performance analysis: {str(e)}")
        ], color="danger")


def create_correlation_matrix_layout() -> html.Div:
    """Create correlation matrix layout with heavy computations."""
    try:
        analytics_service = AnalyticsService()
        # batch_service = BatchDataService()  # Currently unused

        # Heavy computation: Get correlation data for top symbols
        symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX']
        correlation_data = analytics_service.get_symbol_correlation(symbols, days=90)

        if correlation_data and 'correlations' in correlation_data:
            fig = create_correlation_heatmap(correlation_data)
        else:
            fig = create_empty_correlation_chart()

        return html.Div([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H5("Symbol Correlation Matrix")),
                        dbc.CardBody([
                            dcc.Graph(figure=fig, id="correlation-matrix-chart"),
                            html.P(
                                "Correlation matrix shows relationships between major tech stocks over the last 90 days.",
                                className="text-muted mt-2"
                            )
                        ])
                    ])
                ], width=12)
            ])
        ])

    except Exception as e:
        logger.error(f"Error creating correlation matrix: {e}")
        return dbc.Alert([
            html.H5("Error", className="alert-heading"),
            html.P(f"Failed to load correlation matrix: {str(e)}")
        ], color="danger")


def create_volatility_analysis_layout() -> html.Div:
    """Create volatility analysis layout with heavy computations."""
    try:
        analytics_service = AnalyticsService()

        # Heavy computation: Calculate volatility for multiple symbols
        symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
        volatility_data = []

        for symbol in symbols:
            vol_metrics = analytics_service.get_volatility_metrics(symbol, days=30)
            if vol_metrics:
                volatility_data.append(vol_metrics)

        if volatility_data:
            fig = create_volatility_comparison_chart(volatility_data)
        else:
            fig = create_empty_volatility_chart()

        return html.Div([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H5("Volatility Analysis")),
                        dbc.CardBody([
                            dcc.Graph(figure=fig, id="volatility-analysis-chart"),
                            html.P(
                                "Volatility comparison showing daily and annualized volatility for major stocks.",
                                className="text-muted mt-2"
                            )
                        ])
                    ])
                ], width=8),
                dbc.Col([
                    create_volatility_stats_table(volatility_data)
                ], width=4)
            ])
        ])

    except Exception as e:
        logger.error(f"Error creating volatility analysis: {e}")
        return dbc.Alert([
            html.H5("Error", className="alert-heading"),
            html.P(f"Failed to load volatility analysis: {str(e)}")
        ], color="danger")


def create_risk_metrics_layout() -> html.Div:
    """Create risk metrics layout with heavy computations."""
    try:
        analytics_service = AnalyticsService()

        # Heavy computation: Portfolio performance simulation
        portfolio_performance = analytics_service.get_portfolio_performance(days=90)

        # Create risk metrics charts
        risk_fig = create_risk_metrics_chart(portfolio_performance)
        drawdown_fig = create_drawdown_chart()

        return html.Div([
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H5("Risk Metrics Dashboard")),
                        dbc.CardBody([
                            dbc.Row([
                                dbc.Col([
                                    create_risk_metric_card("Sharpe Ratio", portfolio_performance.get('sharpe_ratio', 0),
                                                            "primary")
                                ], width=3),
                                dbc.Col([
                                    create_risk_metric_card("Max Drawdown", f"{portfolio_performance.get('max_drawdown', 0):.1f}%",
                                                            "warning")
                                ], width=3),
                                dbc.Col([
                                    create_risk_metric_card("Win Rate", f"{portfolio_performance.get('win_rate', 0):.1f}%",
                                                            "success")
                                ], width=3),
                                dbc.Col([
                                    create_risk_metric_card("Total Return", f"{portfolio_performance.get('total_return_percent', 0):.1f}%",
                                                            "info")
                                ], width=3)
                            ], className="mb-4")
                        ])
                    ])
                ], width=12)
            ], className="mb-4"),

            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H5("Risk Distribution")),
                        dbc.CardBody([
                            dcc.Graph(figure=risk_fig, id="risk-metrics-chart")
                        ])
                    ])
                ], width=6),
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader(html.H5("Drawdown Analysis")),
                        dbc.CardBody([
                            dcc.Graph(figure=drawdown_fig, id="drawdown-chart")
                        ])
                    ])
                ], width=6)
            ])
        ])

    except Exception as e:
        logger.error(f"Error creating risk metrics: {e}")
        return dbc.Alert([
            html.H5("Error", className="alert-heading"),
            html.P(f"Failed to load risk metrics: {str(e)}")
        ], color="danger")


# Helper functions for chart creation


def create_performance_comparison_chart(daily: List, weekly: List, monthly: List) -> go.Figure:
    """Create performance comparison chart."""
    periods = ['1 Day', '1 Week', '1 Month']

    if daily and weekly and monthly:
        avg_returns = [
            np.mean([p['change'] for p in daily]) if daily else 0,
            np.mean([p['change'] for p in weekly]) if weekly else 0,
            np.mean([p['change'] for p in monthly]) if monthly else 0
        ]
    else:
        avg_returns = [0, 0, 0]

    fig = go.Figure(data=[
        go.Bar(x=periods, y=avg_returns, marker_color=CHART_COLORS['primary'])
    ])

    fig.update_layout(
        title="Average Performance by Period",
        xaxis_title="Time Period",
        yaxis_title="Average Return (%)",
        height=300
    )

    return fig


def create_correlation_heatmap(correlation_data: Dict) -> go.Figure:
    """Create correlation heatmap."""
    symbols = correlation_data.get('symbols', [])
    correlations = correlation_data.get('correlations', {})

    if not symbols or not correlations:
        return create_empty_correlation_chart()

    # Create correlation matrix
    correlation_matrix = []
    for symbol1 in symbols:
        row = []
        for symbol2 in symbols:
            corr_value = correlations.get(symbol1, {}).get(symbol2, 0)
            row.append(corr_value)
        correlation_matrix.append(row)

    fig = go.Figure(data=go.Heatmap(
        z=correlation_matrix,
        x=symbols,
        y=symbols,
        colorscale='RdBu',
        zmid=0
    ))

    fig.update_layout(
        title="Stock Correlation Matrix",
        height=400
    )

    return fig


def create_volatility_comparison_chart(volatility_data: List) -> go.Figure:
    """Create volatility comparison chart."""
    symbols = [data['symbol'] for data in volatility_data]
    daily_vol = [data['daily_volatility'] for data in volatility_data]
    annual_vol = [data['annualized_volatility'] for data in volatility_data]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name='Daily Volatility',
        x=symbols,
        y=daily_vol,
        marker_color=CHART_COLORS['primary']
    ))

    fig.add_trace(go.Bar(
        name='Annualized Volatility',
        x=symbols,
        y=annual_vol,
        marker_color=CHART_COLORS['secondary']
    ))

    fig.update_layout(
        title="Volatility Comparison",
        xaxis_title="Symbol",
        yaxis_title="Volatility (%)",
        barmode='group',
        height=300
    )

    return fig


def create_risk_metrics_chart(portfolio_data: Dict) -> go.Figure:
    """Create risk metrics visualization."""
    # Mock risk distribution data
    risk_categories = ['Low Risk', 'Medium Risk', 'High Risk']
    risk_values = [30, 50, 20]  # Placeholder percentages

    fig = go.Figure(data=[go.Pie(
        labels=risk_categories,
        values=risk_values,
        hole=0.3
    )])

    fig.update_layout(
        title="Portfolio Risk Distribution",
        height=300
    )

    return fig


def create_drawdown_chart() -> go.Figure:
    """Create drawdown analysis chart."""
    # Mock drawdown data
    dates = pd.date_range(start='2025-01-01', periods=30, freq='D')
    drawdown = np.random.uniform(-10, 0, 30)  # Mock drawdown values

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates,
        y=drawdown,
        fill='tonexty',
        mode='lines',
        name='Drawdown',
        line_color=CHART_COLORS['warning']
    ))

    fig.update_layout(
        title="Portfolio Drawdown",
        xaxis_title="Date",
        yaxis_title="Drawdown (%)",
        height=300
    )

    return fig


def create_performers_table(title: str, performers: List) -> dbc.Card:
    """Create performers table component."""
    if not performers:
        table_body = [html.Tr([html.Td("No data available", colSpan=3)])]
    else:
        table_body = []
        for performer in performers[:5]:  # Top 5
            table_body.append(html.Tr([
                html.Td(performer.get('symbol', 'N/A')),
                html.Td(f"${performer.get('current_price', 0):.2f}"),
                html.Td(
                    f"{performer.get('change', 0):.2f}%",
                    style={'color': CHART_COLORS['success'] if performer.get('change', 0) > 0 else CHART_COLORS['danger']}
                )
            ]))

    return dbc.Card([
        dbc.CardHeader(html.H6(title)),
        dbc.CardBody([
            html.Table([
                html.Thead([
                    html.Tr([
                        html.Th("Symbol"),
                        html.Th("Price"),
                        html.Th("Change")
                    ])
                ]),
                html.Tbody(table_body)
            ], className="table table-sm")
        ])
    ])


def create_volatility_stats_table(volatility_data: List) -> dbc.Card:
    """Create volatility statistics table."""
    if not volatility_data:
        table_body = [html.Tr([html.Td("No data available", colSpan=3)])]
    else:
        table_body = []
        for data in volatility_data:
            table_body.append(html.Tr([
                html.Td(data.get('symbol', 'N/A')),
                html.Td(f"{data.get('daily_volatility', 0):.2f}%"),
                html.Td(f"{data.get('annualized_volatility', 0):.1f}%")
            ]))

    return dbc.Card([
        dbc.CardHeader(html.H6("Volatility Stats")),
        dbc.CardBody([
            html.Table([
                html.Thead([
                    html.Tr([
                        html.Th("Symbol"),
                        html.Th("Daily Vol"),
                        html.Th("Annual Vol")
                    ])
                ]),
                html.Tbody(table_body)
            ], className="table table-sm")
        ])
    ])


def create_risk_metric_card(title: str, value: Any, color: str) -> dbc.Card:
    """Create risk metric card."""
    return dbc.Card([
        dbc.CardBody([
            html.H4(str(value), className=f"text-{color}"),
            html.P(title, className="text-muted mb-0")
        ])
    ], className="text-center")


def create_empty_correlation_chart() -> go.Figure:
    """Create empty correlation chart."""
    fig = go.Figure()
    fig.update_layout(
        title="Correlation Matrix - No Data Available",
        xaxis={'visible': False},
        yaxis={'visible': False},
        annotations=[{
            'text': 'No correlation data available',
            'showarrow': False,
            'x': 0.5,
            'y': 0.5
        }]
    )
    return fig


def create_empty_volatility_chart() -> go.Figure:
    """Create empty volatility chart."""
    fig = go.Figure()
    fig.update_layout(
        title="Volatility Analysis - No Data Available",
        xaxis={'visible': False},
        yaxis={'visible': False},
        annotations=[{
            'text': 'No volatility data available',
            'showarrow': False,
            'x': 0.5,
            'y': 0.5
        }]
    )
    return fig
