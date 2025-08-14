"""
Configuration constants for the ML Trading Dashboard.
Contains theme colors, time ranges, and other configurable values.
"""

# Theme Colors - Cerulean Bootstrap Theme
CHART_COLORS = {
    'primary': '#2fa4e7',      # Cerulean Primary Blue
    'success': '#73a839',      # Cerulean Success Green
    'danger': '#c71c22',       # Cerulean Danger Red
    'secondary': '#e9ecef',    # Cerulean Secondary Gray
    'warning': '#dd5600',      # Cerulean Warning Orange
    'info': '#033c73',         # Cerulean Info Dark Blue
    'light': '#f8f9fa'         # Light gray background
}

# Time Range Configurations
TIME_RANGE_OPTIONS = [
    {"label": "1 Week", "value": "1w"},
    {"label": "1 Month", "value": "1m"},
    {"label": "3 Months", "value": "3m"},
    {"label": "1 Year", "value": "1y"}
]

TIME_RANGE_DAYS = {
    '1d': 1,
    '1w': 7,
    '1m': 30,
    '3m': 90,
    '1y': 365
}

# Chart Configuration
DEFAULT_CHART_HEIGHT = "400px"
DEFAULT_TIME_RANGE = "1m"
DEFAULT_SYMBOL = "AAPL"

# Market Hours (in CST - Central Standard Time)
MARKET_HOURS = {
    'open_hour': 8,     # 9:30 AM EST = 8:30 AM CST
    'open_minute': 30,
    'close_hour': 15,   # 4:00 PM EST = 3:00 PM CST
    'close_minute': 0
}

# Dashboard Configuration
DASHBOARD_CONFIG = {
    'default_tab': 'overview-tab',
    'refresh_interval': 30000,  # milliseconds
    'host': '0.0.0.0',
    'port': 8050,
    'debug': True
}

# External Stylesheets
EXTERNAL_STYLESHEETS = [
    "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css",
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"
]

# Navigation Items
NAV_ITEMS = [
    {"label": "Dashboard", "id": "nav-dashboard"},
    {"label": "Tests", "id": "nav-tests"},
    {"label": "Logs", "id": "nav-logs"},

    {"label": "Help", "id": "nav-help"},
    {"label": "Author", "id": "nav-author"}
]

# Card Styling
CARD_STYLE = {
    "border": "none", 
    "box-shadow": "0 2px 4px rgba(0,0,0,0.1)"
}

CARD_STYLE_NONE = {
    "border": "none", 
    "box-shadow": "none"
}