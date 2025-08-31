"""
Data service for dashboard - now using modular architecture.
This file provides backwards compatibility while using the new service modules.
"""

# Import the new unified service
from .unified_data_service import MarketDataService

# This provides backwards compatibility for existing imports
__all__ = ['MarketDataService']

