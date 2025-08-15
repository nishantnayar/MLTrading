"""
Configuration constants for the ML Trading Dashboard.
Contains theme colors, time ranges, and other configurable values.
"""

# Theme Colors - Enhanced Cerulean Bootstrap Theme
CHART_COLORS = {
    'primary': '#2fa4e7',      # Cerulean Primary Blue
    'primary_dark': '#1d82c7', # Darker primary for hover states
    'primary_light': '#64b5ea', # Lighter primary for highlights
    'success': '#73a839',      # Cerulean Success Green
    'success_light': '#95c95f', # Light success
    'danger': '#c71c22',       # Cerulean Danger Red
    'danger_light': '#e74c52', # Light danger
    'secondary': '#e9ecef',    # Cerulean Secondary Gray
    'warning': '#dd5600',      # Cerulean Warning Orange
    'warning_light': '#ff8c42', # Light warning
    'info': '#033c73',         # Cerulean Info Dark Blue
    'info_light': '#4a90e2',   # Light info
    'light': '#f8f9fa',        # Light gray background
    'dark': '#212529',         # Dark text
    'muted': '#6c757d',        # Muted text
    'border': 'rgba(0,0,0,0.1)' # Subtle borders
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
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css",
    "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap"
]

# Custom CSS for enhanced styling
CUSTOM_CSS = {
    'font_family': '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    'smooth_scrolling': 'scroll-behavior: smooth;',
    'focus_ring': 'box-shadow: 0 0 0 3px rgba(47, 164, 231, 0.25);'
}

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
    "box-shadow": "0 4px 6px rgba(0,0,0,0.07)",
    "border-radius": "8px",
    "transition": "box-shadow 0.3s ease, transform 0.2s ease"
}

CARD_STYLE_NONE = {
    "border": "none", 
    "box-shadow": "none",
    "border-radius": "8px"
}

# Enhanced card styles for different contexts
CARD_STYLE_HOVER = {
    **CARD_STYLE,
    "cursor": "pointer"
}

CARD_STYLE_ELEVATED = {
    "border": "none",
    "box-shadow": "0 8px 16px rgba(0,0,0,0.12)",
    "border-radius": "12px",
    "transition": "box-shadow 0.3s ease, transform 0.2s ease"
}

# Animation and transition constants
TRANSITION_FAST = "0.15s ease"
TRANSITION_NORMAL = "0.3s ease"
TRANSITION_SLOW = "0.5s ease"