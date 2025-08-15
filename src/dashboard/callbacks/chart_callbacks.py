"""
Chart-related callback functions for the dashboard.
Handles price charts, sector/industry distribution charts, and symbol filtering.
"""

import plotly.graph_objs as go
from dash import Input, Output, State, callback_context

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
    
    # Note: All chart callbacks have been moved to interactive_chart_callbacks.py
    # The sector/industry charts have been removed from the simplified dashboard
    # This file is kept for backwards compatibility but contains no active callbacks
    pass