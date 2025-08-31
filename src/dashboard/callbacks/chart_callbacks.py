"""
Chart-related callback functions for the dashboard.
Handles price charts, sector/industry distribution charts, and symbol filtering.
"""


from ..services.data_service import MarketDataService
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

