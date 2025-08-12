import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
from pathlib import Path
import re
import json
from datetime import datetime, timedelta
import logging
import sys

# Add the project root to Python path if not already added
if 'src' not in sys.modules:
    project_root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(project_root))

from src.utils.helpers.date_utils import format_datetime_display

def create_log_viewer():
    """
    Create a log viewer component for displaying combined logs
    
    Returns:
        Dash layout for log viewer
    """
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H3("System Logs", className="mb-3")
            ], width=12)
        ]),
        
        # Filters
        dbc.Row([
            dbc.Col([
                html.Label("Component Filter:", className="form-label"),
                dcc.Dropdown(
                    id="log-component-filter",
                    options=[
                        {"label": "All Components", "value": "all"},
                        {"label": "UI Launcher", "value": "mltrading.ui.launcher"},
                        {"label": "Dashboard", "value": "mltrading.ui.dashboard"},
                        {"label": "API", "value": "mltrading.ui.api"},
                        {"label": "Main System", "value": "mltrading.main"},
                        {"label": "Trading", "value": "trading"},
                        {"label": "System", "value": "system"},
                        {"label": "Performance", "value": "performance"},
                        {"label": "Data Extraction", "value": "data_extraction"}
                    ],
                    value="all",
                    clearable=False,
                    className="mb-2"
                )
            ], width=4),
            
            dbc.Col([
                html.Label("Log Level:", className="form-label"),
                dcc.Dropdown(
                    id="log-level-filter",
                    options=[
                        {"label": "All Levels", "value": "all"},
                        {"label": "ERROR", "value": "ERROR"},
                        {"label": "WARNING", "value": "WARNING"},
                        {"label": "INFO", "value": "INFO"},
                        {"label": "DEBUG", "value": "DEBUG"}
                    ],
                    value="all",
                    clearable=False,
                    className="mb-2"
                )
            ], width=4),
            
            dbc.Col([
                html.Label("Time Range:", className="form-label"),
                dcc.Dropdown(
                    id="log-time-filter",
                    options=[
                        {"label": "Last Hour", "value": "1h"},
                        {"label": "Last 6 Hours", "value": "6h"},
                        {"label": "Last 24 Hours", "value": "24h"},
                        {"label": "Last 7 Days", "value": "7d"},
                        {"label": "All Time", "value": "all"}
                    ],
                    value="24h",
                    clearable=False,
                    className="mb-2"
                )
            ], width=4)
        ], className="mb-3"),
        
        # Additional filters for structured logs
        dbc.Row([
            dbc.Col([
                html.Label("Event Type:", className="form-label"),
                dcc.Dropdown(
                    id="log-event-type-filter",
                    options=[
                        {"label": "All Events", "value": "all"},
                        {"label": "Trading Events", "value": "trading"},
                        {"label": "System Events", "value": "system"},
                        {"label": "Performance Events", "value": "performance"},
                        {"label": "API Requests", "value": "api"}
                    ],
                    value="all",
                    clearable=False,
                    className="mb-2"
                )
            ], width=6),
            
            dbc.Col([
                html.Label("Symbol Filter:", className="form-label"),
                dcc.Dropdown(
                    id="log-symbol-filter",
                    options=[
                        {"label": "All Symbols", "value": "all"},
                        {"label": "AAPL", "value": "AAPL"},
                        {"label": "GOOGL", "value": "GOOGL"},
                        {"label": "MSFT", "value": "MSFT"},
                        {"label": "TSLA", "value": "TSLA"},
                        {"label": "AMZN", "value": "AMZN"}
                    ],
                    value="all",
                    clearable=False,
                    className="mb-2"
                )
            ], width=6)
        ], className="mb-3"),
        
        # Log display area
        dbc.Row([
            dbc.Col([
                html.Div(id="log-stats", className="mb-2"),
                html.Div(id="log-analytics", className="mb-3"),
                dcc.Loading(
                    id="log-loading",
                    children=[
                        html.Div(id="log-content", className="log-content")
                    ],
                    type="default"
                )
            ], width=12)
        ]),
        
        # Refresh button
        dbc.Row([
            dbc.Col([
                dbc.Button(
                    "Refresh Logs",
                    id="refresh-logs-btn",
                    color="primary",
                    className="w-100"
                )
            ], width=12)
        ], className="mt-3")
    ], fluid=True)

def parse_log_line(line):
    """
    Parse a log line to extract structured information
    
    Args:
        line (str): Raw log line
        
    Returns:
        dict: Parsed log entry with timestamp, level, component, message, etc.
    """
    try:
        # Actual log format: 2025-08-01 18:41:14,948 - mltrading.ui.dashboard - INFO - MarketDataService initialized
        pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),(\d{3}) - ([^-]+) - (\w+) - (.+)'
        match = re.match(pattern, line.strip())
        
        if match:
            timestamp_str, milliseconds, component, level, message = match.groups()
            timestamp = datetime.strptime(f"{timestamp_str},{milliseconds}", "%Y-%m-%d %H:%M:%S,%f")
            
            return {
                'timestamp': timestamp,
                'level': level,
                'component': component.strip(),
                'message': message.strip(),
                'raw': line.strip()
            }
        
        # Try alternative format: 2025-01-15 10:30:45 - INFO - message (no component)
        alt_pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) - (\w+) - (.+)'
        alt_match = re.match(alt_pattern, line.strip())
        
        if alt_match:
            timestamp_str, level, message = alt_match.groups()
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            
            return {
                'timestamp': timestamp,
                'level': level,
                'component': 'yahoo_extraction',
                'message': message.strip(),
                'raw': line.strip()
            }
        
        # Fallback for unstructured logs
        return {
            'timestamp': datetime.now(),
            'level': 'INFO',
            'component': 'unknown',
            'message': line.strip(),
            'raw': line.strip()
        }
        
    except Exception as e:
        return {
            'timestamp': datetime.now(),
            'level': 'ERROR',
            'component': 'log_parser',
            'message': f"Failed to parse log line: {e}",
            'raw': line.strip()
        }

def load_and_filter_logs(component_filter="all", level_filter="all", time_filter="24h",
                        event_type_filter="all", symbol_filter="all"):
    """
    Load and filter logs based on various criteria
    
    Args:
        component_filter (str): Component to filter by
        level_filter (str): Log level to filter by
        time_filter (str): Time range to filter by
        event_type_filter (str): Event type to filter by
        symbol_filter (str): Symbol to filter by
        
    Returns:
        list: Filtered log entries
    """
    try:
        # Define log file paths
        log_files = [
            "logs/ui_dashboard.log",
            "logs/ui_api.log",
            "logs/ui_launcher.log",
            "logs/ui_utils.log",
            "logs/yahoo_extraction.log",
            "logs/mltrading_combined.log"
        ]
        
        all_logs = []
        
        # Load logs from all files
        for log_file in log_files:
            try:
                log_path = Path(log_file)
                if log_path.exists():
                    # Try different encodings
                    encodings = ['utf-8', 'latin-1', 'cp1252']
                    for encoding in encodings:
                        try:
                            with open(log_path, 'r', encoding=encoding) as f:
                                current_message = ""
                                for line in f:
                                    line = line.strip()
                                    if not line:
                                        continue
                                    
                                    # Check if this line starts with a timestamp (new log entry)
                                    # Look for the pattern: YYYY-MM-DD HH:MM:SS,mmm - COMPONENT - LEVEL - MESSAGE
                                    if re.match(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} - [^-]+ - \w+ -', line):
                                        # If we have a previous message, save it
                                        if current_message:
                                            log_entry = parse_log_line(current_message)
                                            all_logs.append(log_entry)
                                        current_message = line
                                    else:
                                        # This is a continuation of the previous message
                                        current_message += "\n" + line
                                
                                # Don't forget the last message
                                if current_message:
                                    log_entry = parse_log_line(current_message)
                                    all_logs.append(log_entry)
                            break  # If successful, break out of encoding loop
                        except UnicodeDecodeError:
                            continue  # Try next encoding
                    else:
                        print(f"Could not read {log_file} with any encoding")
            except Exception as e:
                print(f"Error reading log file {log_file}: {e}")
        
        # Sort by timestamp
        all_logs.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Apply time filter
        if time_filter != "all":
            now = datetime.now()
            if time_filter == "1h":
                cutoff = now - timedelta(hours=1)
            elif time_filter == "6h":
                cutoff = now - timedelta(hours=6)
            elif time_filter == "24h":
                cutoff = now - timedelta(hours=24)
            elif time_filter == "7d":
                cutoff = now - timedelta(days=7)
            else:
                cutoff = now - timedelta(hours=24)
            
            all_logs = [log for log in all_logs if log['timestamp'] >= cutoff]
        
        # Apply component filter
        if component_filter != "all":
            all_logs = [log for log in all_logs if component_filter.lower() in log['component'].lower()]
        
        # Apply level filter
        if level_filter != "all":
            all_logs = [log for log in all_logs if log['level'] == level_filter]
        
        # Apply event type filter
        if event_type_filter != "all":
            all_logs = [log for log in all_logs if event_type_filter.lower() in log['message'].lower()]
        
        # Apply symbol filter
        if symbol_filter != "all":
            all_logs = [log for log in all_logs if symbol_filter in log['message']]
        
        return all_logs
        
    except Exception as e:
        print(f"Error loading logs: {e}")
        return []

def format_log_display(logs):
    """
    Format logs for display in the UI
    
    Args:
        logs (list): List of log entries
        
    Returns:
        html.Div: Formatted log display
    """
    if not logs:
        return html.Div([
            html.P("No logs found matching the current filters.", className="text-muted")
        ])
    
    log_entries = []
    for log in logs:
        # Determine CSS class based on log level
        level_class = {
            'ERROR': 'text-danger',
            'WARNING': 'text-warning', 
            'INFO': 'text-info',
            'DEBUG': 'text-muted'
        }.get(log['level'], 'text-dark')
        
        # Format timestamp
        timestamp_str = format_datetime_display(log['timestamp'])
        
        log_entries.append(html.Div([
            html.Span(f"[{timestamp_str}] ", className="text-muted"),
            html.Span(f"{log['level']} ", className=level_class),
            html.Span(f"[{log['component']}] ", className="text-secondary"),
            html.Span(log['message'], className="text-dark")
        ], className="log-entry mb-1 p-2 border-bottom"))
    
    return html.Div(log_entries, className="log-container")

def get_log_stats(logs):
    """
    Generate statistics for the logs
    
    Args:
        logs (list): List of log entries
        
    Returns:
        html.Div: Statistics display
    """
    if not logs:
        return html.Div("No logs available", className="text-muted")
    
    # Count by level
    level_counts = {}
    component_counts = {}
    
    for log in logs:
        level_counts[log['level']] = level_counts.get(log['level'], 0) + 1
        component_counts[log['component']] = component_counts.get(log['component'], 0) + 1
    
    # Find most common component
    most_common_component = max(component_counts.items(), key=lambda x: x[1]) if component_counts else ("None", 0)
    
    # Find most common level
    most_common_level = max(level_counts.items(), key=lambda x: x[1]) if level_counts else ("None", 0)
    
    stats_html = [
        html.Div([
            html.Strong("Total Logs: "), html.Span(str(len(logs))),
            html.Br(),
            html.Strong("Most Common Level: "), html.Span(f"{most_common_level[0]} ({most_common_level[1]})"),
            html.Br(),
            html.Strong("Most Common Component: "), html.Span(f"{most_common_component[0]} ({most_common_component[1]})")
        ], className="text-sm")
    ]
    
    return html.Div(stats_html, className="log-stats p-2 bg-light rounded")

def generate_log_analytics(logs):
    """
    Generate analytics and insights from logs
    
    Args:
        logs (list): List of log entries
        
    Returns:
        html.Div: Analytics display
    """
    if not logs:
        return html.Div("No analytics available", className="text-muted")
    
    # Analyze error patterns
    errors = [log for log in logs if log['level'] == 'ERROR']
    warnings = [log for log in logs if log['level'] == 'WARNING']
    
    # Find most common error messages
    error_messages = {}
    for error in errors:
        msg = error['message'][:50] + "..." if len(error['message']) > 50 else error['message']
        error_messages[msg] = error_messages.get(msg, 0) + 1
    
    analytics_html = []
    
    if errors:
        analytics_html.append(html.H5("Error Analysis", className="text-danger"))
        analytics_html.append(html.P(f"Total Errors: {len(errors)}"))
        
        if error_messages:
            most_common_error = max(error_messages.items(), key=lambda x: x[1])
            analytics_html.append(html.P(f"Most Common Error: {most_common_error[0]} ({most_common_error[1]} times)"))
    
    if warnings:
        analytics_html.append(html.H5("Warning Analysis", className="text-warning"))
        analytics_html.append(html.P(f"Total Warnings: {len(warnings)}"))
    
    # Performance insights
    performance_logs = [log for log in logs if 'performance' in log['message'].lower()]
    if performance_logs:
        analytics_html.append(html.H5("Performance Insights", className="text-info"))
        analytics_html.append(html.P(f"Performance-related logs: {len(performance_logs)}"))
    
    return html.Div(analytics_html, className="log-analytics p-2 bg-light rounded mt-2") 