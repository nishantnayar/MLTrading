"""Dashboard callback modules."""

from .chart_callbacks import register_chart_callbacks
from .overview_callbacks import register_overview_callbacks
from .comparison_callbacks import register_comparison_callbacks

__all__ = [
    'register_chart_callbacks',
    'register_overview_callbacks',
    'register_comparison_callbacks'
]