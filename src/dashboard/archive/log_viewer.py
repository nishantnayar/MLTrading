import dash
from dash import html, dcc, Input, Output, State
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
    return html.Div([
        html.H3("System Logs", className="mb-3"),
        
        # Filters
        html.Div([
            html.Div([
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
            ], className="col-md-4"),
            
            html.Div([
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
            ], className="col-md-4"),
            
            html.Div([
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
            ], className="col-md-4")
        ], className="row mb-3"),
        
        # Additional filters for structured logs
        html.Div([
            html.Div([
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
            ], className="col-md-6"),
            
            html.Div([
                html.Label("Symbol (Trading):", className="form-label"),
                dcc.Dropdown(
                    id="log-symbol-filter",
                    options=[{"label": "All Symbols", "value": "all"}],
                    value="all",
                    clearable=False,
                    className="mb-2"
                )
            ], className="col-md-6")
        ], className="row mb-3"),
        
        # Controls
        html.Div([
            html.Button("Refresh Logs", id="refresh-logs-btn", className="btn btn-primary me-2"),
            html.Button("Clear Logs", id="clear-logs-btn", className="btn btn-warning me-2"),
            html.Button("Download Logs", id="download-logs-btn", className="btn btn-success me-2"),
            html.Button("Analytics", id="analytics-btn", className="btn btn-info"),
            dcc.Download(id="download-logs")
        ], className="mb-3"),
        
        # Analytics section
        html.Div(id="analytics-section", className="mb-3", style={"display": "none"}),
        
        # Log display
        html.Div([
            html.Div(id="log-stats", className="mb-2"),
            html.Div(id="log-content", className="border rounded p-3", style={
                "maxHeight": "600px",
                "overflowY": "auto",
                "fontFamily": "monospace",
                "fontSize": "12px",
                "backgroundColor": "#f8f9fa"
            })
        ])
    ])

def parse_log_line(line):
    """
    Parse a log line into components
    
    Args:
        line: Log line string
        
    Returns:
        Dictionary with parsed log components
    """
    try:
        # Check for structured log format first
        if 'STRUCTURED_LOG:' in line:
            try:
                # Find the position of STRUCTURED_LOG:
                start_pos = line.find('STRUCTURED_LOG: ') + 16
                json_str = line[start_pos:]
                structured_log = json.loads(json_str)
                return {
                    'timestamp': structured_log.get('timestamp', ''),
                    'logger': structured_log.get('component', 'unknown'),
                    'level': structured_log.get('level', 'INFO'),
                    'message': structured_log.get('message', ''),
                    'metadata': structured_log.get('metadata', {}),
                    'is_structured': True
                }
            except (json.JSONDecodeError, IndexError) as e:
                logging.error(f"JSON decode error: {e}")
                pass
        
        # Pattern for detailed format: timestamp - logger_name - level - message
        detailed_pattern = r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - ([^-]+) - (\w+) - (.+)$'
        
        # Pattern for simple format: timestamp - level - message
        simple_pattern = r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - (\w+) - (.+)$'
        
        detailed_match = re.match(detailed_pattern, line.strip())
        if detailed_match:
            return {
                'timestamp': detailed_match.group(1),
                'logger': detailed_match.group(2),
                'level': detailed_match.group(3),
                'message': detailed_match.group(4),
                'metadata': {},
                'is_structured': False
            }
        
        simple_match = re.match(simple_pattern, line.strip())
        if simple_match:
            return {
                'timestamp': simple_match.group(1),
                'logger': 'unknown',
                'level': simple_match.group(2),
                'message': simple_match.group(3),
                'metadata': {},
                'is_structured': False
            }
        
        return None
    except Exception as e:
        logging.error(f"Error parsing log line: {e}")
        return None

def load_and_filter_logs(component_filter="all", level_filter="all", time_filter="24h",
                        event_type_filter="all", symbol_filter="all"):
    """
    Load and filter logs from the combined log file
    
    Args:
        component_filter: Component to filter by
        level_filter: Log level to filter by
        time_filter: Time range to filter by
        event_type_filter: Event type to filter by
        symbol_filter: Symbol to filter by
        
    Returns:
        List of filtered log entries
    """
    try:
        combined_log_path = Path("logs/mltrading_combined.log")
        
        if not combined_log_path.exists():
            return []
        
        # Read file in chunks to avoid memory issues
        logs = []
        chunk_size = 1000  # Process 1000 lines at a time
        
        with open(combined_log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Process logs in chunks
        for i in range(0, len(lines), chunk_size):
            chunk = lines[i:i + chunk_size]
            
            # Parse logs in chunk
            for line in chunk:
                try:
                    parsed = parse_log_line(line)
                    if parsed:
                        logs.append(parsed)
                except Exception as e:
                    # Skip malformed lines
                    continue
        
        if not logs:
            return []
        
        try:
            # Convert to DataFrame for easier filtering
            df = pd.DataFrame(logs)
            
            # Handle timestamp conversion more safely
            try:
                df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
                # Remove rows with invalid timestamps
                df = df.dropna(subset=['timestamp'])
            except Exception as e:
                logging.error(f"Error converting timestamps: {e}")
                return []
            
            # Apply filters
            if component_filter != "all":
                df = df[df['logger'].str.contains(component_filter, na=False)]
            
            if level_filter != "all":
                df = df[df['level'] == level_filter]
            
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
                    cutoff = datetime.min
                
                df = df[df['timestamp'] >= cutoff]
            
            # Apply structured log filters more safely
            if event_type_filter != "all":
                # Filter by event type in metadata
                df = df[df['metadata'].apply(lambda x: x.get('event_type', '') == event_type_filter)]
            
            if symbol_filter != "all":
                # Filter by symbol in metadata
                df = df[df['metadata'].apply(lambda x: x.get('symbol', '') == symbol_filter)]
            
            return df.to_dict('records')
        except Exception as e:
            logging.error(f"Error filtering logs: {e}")
            return []
            
    except Exception as e:
        logging.error(f"Error reading log file: {e}")
        return []

def format_log_display(logs):
    """
    Format logs for display
    
    Args:
        logs: List of log dictionaries
        
    Returns:
        HTML formatted log display
    """
    try:
        if not logs:
            return html.Div("No logs found matching the current filters.", className="text-muted")
        
        log_elements = []
        
        for log in logs:
            # Determine color based on log level using Cerulean theme colors
            level_colors = {
                'ERROR': '#c71c22',    # Cerulean Danger Red
                'WARNING': '#dd5600',   # Cerulean Warning Orange
                'INFO': '#2fa4e7',      # Cerulean Primary Blue
                'DEBUG': '#e9ecef'      # Cerulean Secondary Gray
            }
            
            color = level_colors.get(log['level'], '#000000')
            
            # Format timestamp
            timestamp = log['timestamp']
            if isinstance(timestamp, str):
                try:
                    dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S,%f')
                    timestamp = format_datetime_display(dt)
                except:
                    pass
            
            # Create log entry
            log_entry = [
                html.Span(f"[{timestamp}] ", style={"color": "#e9ecef"}),  # Cerulean Secondary Gray
                html.Span(f"[{log['logger']}] ", style={"color": "#495057"}),
                html.Span(f"[{log['level']}] ", style={"color": color, "fontWeight": "bold"}),
                html.Span(log['message'])
            ]
            
            # Add structured data indicator
            if log.get('is_structured', False):
                log_entry.append(
                    html.Span(" [STRUCTURED]", style={"color": "#28a745", "fontSize": "10px"})
                )
            
            log_elements.append(
                html.Div(log_entry, className="mb-1")
            )
        
        return html.Div(log_elements)
    except Exception as e:
        return html.Div(f"Error formatting logs: {str(e)}", className="text-danger")

def get_log_stats(logs):
    """
    Get statistics about the filtered logs
    
    Args:
        logs: List of log dictionaries
        
    Returns:
        HTML formatted statistics
    """
    try:
        if not logs:
            return html.Div("No logs to analyze.", className="text-muted")
        
        # Count by level
        level_counts = {}
        component_counts = {}
        event_type_counts = {}
        structured_count = 0
        
        for log in logs:
            level = log['level']
            component = log['logger']
            
            level_counts[level] = level_counts.get(level, 0) + 1
            component_counts[component] = component_counts.get(component, 0) + 1
            
            if log.get('is_structured', False):
                structured_count += 1
                event_type = log.get('metadata', {}).get('event_type', 'unknown')
                event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1
        
        stats_html = [
            html.Div([
                html.Strong(f"Total Logs: {len(logs)}"),
                html.Br(),
                html.Strong("Structured Logs: "),
                html.Span(f"{structured_count}"),
                html.Br(),
                html.Strong("By Level: "),
                ", ".join([f"{level}: {count}" for level, count in level_counts.items()]),
                html.Br(),
                html.Strong("By Component: "),
                ", ".join([f"{comp}: {count}" for comp, count in list(component_counts.items())[:5]])
            ])
        ]
        
        if event_type_counts:
            stats_html.append(
                html.Div([
                    html.Br(),
                    html.Strong("By Event Type: "),
                    ", ".join([f"{event}: {count}" for event, count in event_type_counts.items()])
                ])
            )
        
        return html.Div(stats_html, className="text-muted small")
    except Exception as e:
        return html.Div(f"Error generating stats: {str(e)}", className="text-danger")

def generate_log_analytics(logs):
    """
    Generate analytics from logs
    
    Args:
        logs: List of log dictionaries
        
    Returns:
        HTML formatted analytics
    """
    try:
        if not logs:
            return html.Div("No logs available for analytics.", className="text-muted")
        
        df = pd.DataFrame(logs)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Performance analytics
        performance_logs = df[df['metadata'].apply(lambda x: x.get('event_type') == 'performance')]
        
        # Error rate
        error_count = len(df[df['level'] == 'ERROR'])
        total_count = len(df)
        error_rate = (error_count / total_count * 100) if total_count > 0 else 0
        
        # Component activity
        component_activity = df['logger'].value_counts().head(5)
        
        # Time distribution
        df['hour'] = df['timestamp'].dt.hour
        hourly_distribution = df['hour'].value_counts().sort_index()
        
        analytics_html = [
            html.H5("Log Analytics", className="mb-3"),
            html.Div([
                html.Div([
                    html.H6("Error Rate"),
                    html.P(f"{error_rate:.1f}%", className="text-danger")
                ], className="col-md-3"),
                html.Div([
                    html.H6("Total Logs"),
                    html.P(f"{total_count}", className="text-primary")
                ], className="col-md-3"),
                html.Div([
                    html.H6("Structured Logs"),
                    html.P(f"{len(df[df.get('is_structured', False)])}", className="text-success")
                ], className="col-md-3"),
                html.Div([
                    html.H6("Performance Events"),
                    html.P(f"{len(performance_logs)}", className="text-info")
                ], className="col-md-3")
            ], className="row mb-3"),
            
            html.Div([
                html.Div([
                    html.H6("Most Active Components"),
                    html.Ul([html.Li(f"{comp}: {count}") for comp, count in component_activity.items()])
                ], className="col-md-6"),
                html.Div([
                    html.H6("Hourly Distribution"),
                    html.P("Peak activity: " + str(hourly_distribution.idxmax()) + ":00")
                ], className="col-md-6")
            ], className="row")
        ]
        
        return html.Div(analytics_html, className="border rounded p-3 bg-light")
    except Exception as e:
        return html.Div(f"Error generating analytics: {str(e)}", className="text-danger") 