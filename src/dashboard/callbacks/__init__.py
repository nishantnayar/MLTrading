"""Dashboard callback modules."""

from .chart_callbacks import register_chart_callbacks
from .overview_callbacks import register_overview_callbacks

__all__ = [
    'register_chart_callbacks',
    'register_overview_callbacks'
]