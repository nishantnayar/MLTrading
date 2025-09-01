"""
Data Pipeline Status Components
Dashboard components for displaying Prefect pipeline status and health
"""

import dash_bootstrap_components as dbc
from dash import html, dcc
from datetime import datetime
from typing import Dict, Optional, List, Any


def create_pipeline_status_card(status_data: Dict) -> dbc.Card:
    """Create the main pipeline status card"""

    if not status_data.get('connected', False):
        return _create_disconnected_card()

    deployment = status_data.get('deployment')
    if not deployment:
        return _create_no_deployment_card(status_data.get('error', 'Deployment not found'))

    last_run = status_data.get('last_run')
    next_run = status_data.get('next_run')
    success_rate = status_data.get('success_rate', 0.0)

    # Determine status using helper function
    status_color, status_icon, status_text = _determine_pipeline_status(last_run)

    # Format time displays using helper functions
    last_run_text = _format_last_run_time(last_run, next_run)
    next_run_text = _format_next_run_time(next_run)

    # Build card using helper function
    return _build_pipeline_status_card(
        deployment, status_color, status_icon, status_text,
        last_run_text, next_run_text, success_rate
    )


def _determine_pipeline_status(last_run):
    """Determine status color, icon and text based on last run"""
    if last_run:
        last_run_state = last_run.get('state', {}).get('type', 'UNKNOWN')
        status_map = {
            'COMPLETED': ('success', 'fas fa-check-circle', 'Healthy'),
            'FAILED': ('danger', 'fas fa-exclamation-circle', 'Failed'),
            'RUNNING': ('info', 'fas fa-sync fa-spin', 'Running'),
            'SCHEDULED': ('warning', 'fas fa-clock', 'Scheduled')
        }
        return status_map.get(last_run_state, ('secondary', 'fas fa-question-circle', 'Unknown'))
    else:
        return 'info', 'fas fa-clock', 'Scheduled'


def _format_last_run_time(last_run, next_run):
    """Format the last run time display"""
    last_run_text = 'No runs yet'
    
    if last_run:
        try:
            # For completed/failed runs, use end_time
            if last_run.get('end_time'):
                end_time = _parse_datetime(last_run['end_time'])
                last_run_text = _format_time_ago(end_time)
            
            # For scheduled/running runs, use created time with status
            elif last_run.get('created'):
                created_time = _parse_datetime(last_run['created'])
                last_run_text = _format_time_ago(created_time, prefix='Scheduled ')
        except Exception:
            last_run_text = 'Unknown'

    # If no runs yet but we have a next run, show that information
    if last_run_text == 'No runs yet' and next_run:
        try:
            next_run_dt = _parse_datetime(next_run)
            now = datetime.now().astimezone()
            
            if hasattr(next_run_dt, 'astimezone'):
                time_until = next_run_dt.astimezone() - now
            else:
                time_until = next_run_dt - now.replace(tzinfo=None)

            if time_until.total_seconds() > 0:
                last_run_text = _format_time_until(time_until, prefix='First run in ')
        except Exception:
            pass  # Keep default "No runs yet"

    return last_run_text


def _format_next_run_time(next_run):
    """Format the next run time display"""
    next_run_text = 'Not scheduled'
    
    if next_run:
        try:
            next_run_dt = _parse_datetime(next_run)
            now = datetime.now()
            time_until = next_run_dt - now

            if time_until.total_seconds() < 0:
                next_run_text = 'Overdue'
            elif time_until.total_seconds() < 60:
                next_run_text = 'Starting soon'
            else:
                next_run_text = _format_time_until(time_until, prefix='In ')
        except Exception:
            next_run_text = 'Error parsing time'

    return next_run_text


def _parse_datetime(dt_input):
    """Parse datetime from string or datetime object"""
    if isinstance(dt_input, str):
        return datetime.fromisoformat(dt_input.replace('Z', '+00:00'))
    return dt_input


def _format_time_ago(dt, prefix=''):
    """Format time difference as 'X ago' or with custom prefix"""
    now = datetime.now().astimezone()
    time_diff = now - dt.astimezone()
    
    seconds = time_diff.total_seconds()
    
    if seconds < 60:
        return 'Just now' if not prefix else f'{prefix}just now'
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f'{prefix}{minutes}m ago'
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f'{prefix}{hours}h ago'
    else:
        days = int(seconds / 86400)
        return f'{prefix}{days}d ago'


def _format_time_until(time_delta, prefix=''):
    """Format time delta as 'In X' or with custom prefix"""
    seconds = time_delta.total_seconds()
    
    if seconds < 3600:
        minutes = int(seconds / 60)
        return f'{prefix}{minutes}m'
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f'{prefix}{hours}h'
    else:
        days = int(seconds / 86400)
        return f'{prefix}{days}d'


def _build_pipeline_status_card(deployment, status_color, status_icon, status_text, 
                                last_run_text, next_run_text, success_rate):
    """Build the main pipeline status card UI"""
    # Success rate color
    if success_rate >= 95:
        success_color = 'success'
    elif success_rate >= 85:
        success_color = 'warning'
    else:
        success_color = 'danger'

    return dbc.Card([
        dbc.CardHeader([
            html.Div([
                html.I(className="fas fa-database me-2"),
                html.Strong("Data Pipeline Status"),
            ], className="d-flex align-items-center")
        ]),
        dbc.CardBody([
            # Main status indicator
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.I(className=f"{status_icon} me-2 text-{status_color}"),
                        html.Span(status_text, className=f"fw-bold text-{status_color}")
                    ], className="d-flex align-items-center mb-2")
                ], width=12)
            ]),

            # Key metrics
            dbc.Row([
                dbc.Col([
                    html.Small("Last Run:", className="text-muted d-block"),
                    html.Span(last_run_text, className="fw-medium")
                ], width=4),
                dbc.Col([
                    html.Small("Next Run:", className="text-muted d-block"),
                    html.Span(next_run_text, className="fw-medium")
                ], width=4),
                dbc.Col([
                    html.Small("Success Rate:", className="text-muted d-block"),
                    html.Span(f"{success_rate:.1f}%", className=f"fw-medium text-{success_color}")
                ], width=4),
            ], className="mb-3"),

            # Action buttons
            dbc.Row([
                dbc.Col([
                    dbc.ButtonGroup([
                        dbc.Button(
                            [html.I(className="fas fa-sync me-1"), "Trigger Run"],
                            id="trigger-pipeline-btn",
                            color="primary",
                            size="sm",
                            disabled=last_run_state == 'RUNNING' if last_run else False
                        ),
                        dbc.Button(
                            [html.I(className="fas fa-history me-1"), "View History"],
                            id="view-pipeline-history-btn",
                            color="outline-secondary",
                            size="sm"
                        )
                    ], size="sm")
                ], width=12)
            ])
        ])
    ], className="h-100")


def _create_disconnected_card() -> dbc.Card:
    """Create card for when Prefect is disconnected"""
    return dbc.Card([
        dbc.CardHeader([
            html.Div([
                html.I(className="fas fa-database me-2"),
                html.Strong("Data Pipeline Status"),
            ], className="d-flex align-items-center")
        ]),
        dbc.CardBody([
            dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                "Cannot connect to Prefect API. Check that the Prefect server is running."
            ], color="warning", className="mb-3"),

            html.P([
                "To start the Prefect server, run:",
                html.Code(" prefect server start", className="ms-2")
            ], className="mb-2"),

            dbc.Button(
                [html.I(className="fas fa-redo me-1"), "Retry Connection"],
                id="retry-prefect-connection-btn",
                color="primary",
                size="sm"
            )
        ])
    ], className="h-100")


def _create_no_deployment_card(error_msg: str) -> dbc.Card:
    """Create card when deployment is not found"""
    return dbc.Card([
        dbc.CardHeader([
            html.Div([
                html.I(className="fas fa-database me-2"),
                html.Strong("Data Pipeline Status"),
            ], className="d-flex align-items-center")
        ]),
        dbc.CardBody([
            dbc.Alert([
                html.I(className="fas fa-info-circle me-2"),
                f"Deployment not found: {error_msg}"
            ], color="info", className="mb-3"),

            html.P("Make sure the deployment is created and running with Prefect.",
                   className="mb-2"),

            dbc.Button(
                [html.I(className="fas fa-redo me-1"), "Refresh"],
                id="refresh-pipeline-status-btn",
                color="primary",
                size="sm"
            )
        ])
    ], className="h-100")


def create_data_freshness_indicator(freshness_data: Dict) -> html.Div:
    """Create a data freshness indicator component"""

    status = freshness_data.get('status', 'unknown')
    color = freshness_data.get('color', 'secondary')
    # last_update = freshness_data.get('last_update')  # Currently unused
    time_since_update = freshness_data.get('time_since_update')

    # Status text and icon
    status_config = {
        'fresh': {'text': 'Fresh', 'icon': 'fas fa-check-circle'},
        'moderate': {'text': 'Moderate', 'icon': 'fas fa-clock'},
        'stale': {'text': 'Stale', 'icon': 'fas fa-exclamation-triangle'},
        'unknown': {'text': 'Unknown', 'icon': 'fas fa-question-circle'},
        'error': {'text': 'Error', 'icon': 'fas fa-times-circle'}
    }

    config = status_config.get(status, status_config['unknown'])

    # Format time since update
    if time_since_update:
        total_seconds = time_since_update.total_seconds()
        if total_seconds < 60:
            time_text = "Just updated"
        elif total_seconds < 3600:
            minutes = int(total_seconds / 60)
            time_text = f"{minutes}m ago"
        elif total_seconds < 86400:
            hours = int(total_seconds / 3600)
            time_text = f"{hours}h ago"
        else:
            days = int(total_seconds / 86400)
            time_text = f"{days}d ago"
    else:
        time_text = "Never"

    return html.Div([
        dbc.Badge([
            html.I(className=f"{config['icon']} me-1"),
            f"Data: {config['text']} ({time_text})"
        ], color=color, className="d-flex align-items-center")
    ], className="data-freshness-indicator")


def create_pipeline_history_modal() -> dbc.Modal:
    """Create modal for viewing pipeline run history"""
    return dbc.Modal([
        dbc.ModalHeader([
            html.H4("Pipeline Run History", className="modal-title")
        ]),
        dbc.ModalBody([
            dcc.Loading(
                id="pipeline-history-loading",
                children=[
                    html.Div(id="pipeline-history-content")
                ],
                type="default"
            )
        ]),
        dbc.ModalFooter([
            dbc.Button("Close", id="close-pipeline-history-modal", color="secondary")
        ])
    ], id="pipeline-history-modal", size="lg")


def create_pipeline_run_table(runs: List[Dict]) -> html.Div:
    """Create table showing recent pipeline runs"""
    if not runs:
        return dbc.Alert("No pipeline runs found.", color="info")

    # Create table rows
    rows = []
    for run in runs:
        state = run.get('state', {})
        state_type = state.get('type', 'UNKNOWN')
        state_name = state.get('name', 'Unknown')

        # Format timestamps
        start_time = run.get('start_time', '')
        end_time = run.get('end_time', '')
        duration = 'N/A'

        try:
            if start_time and end_time:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                duration_td = end_dt - start_dt

                total_seconds = int(duration_td.total_seconds())
                minutes = total_seconds // 60
                seconds = total_seconds % 60
                duration = f"{minutes}m {seconds}s"

                # Format start time
                start_time = start_dt.strftime('%Y-%m-%d %H:%M')
        except Exception:
            pass

        # Status badge
        if state_type == 'COMPLETED':
            badge_color = 'success'
            badge_icon = 'fas fa-check'
        elif state_type == 'FAILED':
            badge_color = 'danger'
            badge_icon = 'fas fa-times'
        elif state_type == 'RUNNING':
            badge_color = 'info'
            badge_icon = 'fas fa-sync fa-spin'
        elif state_type == 'SCHEDULED':
            badge_color = 'warning'
            badge_icon = 'fas fa-clock'
        else:
            badge_color = 'secondary'
            badge_icon = 'fas fa-question'

        rows.append(html.Tr([
            html.Td([
                dbc.Badge([
                    html.I(className=f"{badge_icon} me-1"),
                    state_name
                ], color=badge_color)
            ]),
            html.Td(start_time),
            html.Td(duration),
            html.Td(run.get('name', 'N/A')[:20] + '...' if len(run.get('name', '')) > 20 else run.get('name', 'N/A'))
        ]))

    return dbc.Table([
        html.Thead([
            html.Tr([
                html.Th("Status"),
                html.Th("Start Time"),
                html.Th("Duration"),
                html.Th("Run Name")
            ])
        ]),
        html.Tbody(rows)
    ], striped=True, hover=True, responsive=True, size="sm")


def create_system_health_summary(health_data: Dict) -> html.Div:
    """Create system health summary component"""

    if not health_data.get('connected', False):
        return dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            "System health unavailable - Prefect not connected"
        ], color="warning")

    success_rate = health_data.get('success_rate', 0.0)
    health_status = health_data.get('health_status', 'unknown')
    health_color = health_data.get('health_color', 'secondary')
    runs = health_data.get('runs', {})

    return dbc.Card([
        dbc.CardBody([
            html.Div([
                html.H6([
                    html.I(className="fas fa-heartbeat me-2"),
                    "System Health"
                ], className="card-title mb-3"),

                # Health status
                html.Div([
                    dbc.Badge([
                        html.I(className="fas fa-check-circle me-1"),
                        f"{health_status.title()} ({success_rate:.1f}%)"
                    ], color=health_color, className="fs-6")
                ], className="text-center mb-3"),

                # Run statistics
                dbc.Row([
                    dbc.Col([
                        html.Small("Completed", className="text-muted d-block"),
                        html.Span(str(runs.get('completed', 0)), className="h5 text-success")
                    ], width=3, className="text-center"),
                    dbc.Col([
                        html.Small("Failed", className="text-muted d-block"),
                        html.Span(str(runs.get('failed', 0)), className="h5 text-danger")
                    ], width=3, className="text-center"),
                    dbc.Col([
                        html.Small("Running", className="text-muted d-block"),
                        html.Span(str(runs.get('running', 0)), className="h5 text-info")
                    ], width=3, className="text-center"),
                    dbc.Col([
                        html.Small("Scheduled", className="text-muted d-block"),
                        html.Span(str(runs.get('scheduled', 0)), className="h5 text-warning")
                    ], width=3, className="text-center"),
                ])
            ])
        ])
    ], className="h-100")


def create_multi_deployment_status_card(deployments_status: Dict[str, Dict]) -> dbc.Card:
    """Create a card showing status for multiple deployments"""

    if not deployments_status:
        return dbc.Card([
            dbc.CardBody([
                html.Div([
                    html.I(className="fas fa-info-circle me-2"),
                    "No deployments configured"
                ], className="text-muted")
            ])
        ])

    deployment_cards = []
    for deployment_name, status_data in deployments_status.items():
        deployment_cards.append(create_deployment_summary_row(deployment_name, status_data))

    return dbc.Card([
        dbc.CardHeader([
            html.H5([
                html.I(className="fas fa-tasks me-2"),
                "Deployment Status"
            ], className="mb-0")
        ]),
        dbc.CardBody(deployment_cards, className="py-2")
    ], className="mb-3")


def create_deployment_summary_row(deployment_name: str, status_data: Dict) -> html.Div:
    """Create a summary row for a single deployment"""

    config = status_data.get('config')
    display_name = config.display_name if config else deployment_name.replace('-', ' ').title()

    # Create status badge using helper function
    status_badge = _create_deployment_status_badge(status_data)
    
    # Format next run time using helper function
    next_run_text = _format_deployment_next_run(status_data.get('next_run'))
    
    success_rate = status_data.get('success_rate', 0.0)

    return _build_deployment_summary_ui(deployment_name, display_name, status_badge, 
                                       next_run_text, success_rate)


def _create_deployment_status_badge(status_data):
    """Create status badge for deployment summary"""
    if not status_data.get('connected', False):
        return dbc.Badge([
            html.I(className="fas fa-unlink me-1"),
            "Disconnected"
        ], color="secondary")

    last_run = status_data.get('last_run')
    if not last_run:
        return dbc.Badge([
            html.I(className="fas fa-question-circle me-1"),
            "Unknown"
        ], color="secondary")

    last_run_state = last_run.get('state', {}).get('type', 'UNKNOWN')
    
    status_config = {
        'COMPLETED': ('fas fa-check-circle me-1', 'Healthy', 'success'),
        'FAILED': ('fas fa-exclamation-circle me-1', 'Failed', 'danger'),
        'RUNNING': ('fas fa-sync fa-spin me-1', 'Running', 'info'),
        'SCHEDULED': ('fas fa-clock me-1', 'Scheduled', 'warning')
    }
    
    icon, text, color = status_config.get(last_run_state, 
                                        ('fas fa-clock me-1', 'Scheduled', 'warning'))
    
    return dbc.Badge([html.I(className=icon), text], color=color)


def _format_deployment_next_run(next_run):
    """Format next run time for deployment summary"""
    if not next_run:
        return ""

    try:
        next_run_dt = _parse_datetime(next_run)
        now = datetime.now().astimezone()
        
        if hasattr(next_run_dt, 'astimezone'):
            time_until = next_run_dt.astimezone() - now
        else:
            time_until = next_run_dt - now.replace(tzinfo=None)

        return _format_time_until(time_until, prefix="Next: ")
    except Exception:
        return ""


def _build_deployment_summary_ui(deployment_name, display_name, status_badge, 
                                next_run_text, success_rate):

    return html.Div([
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.Strong(display_name),
                    html.Small(f" ({deployment_name})", className="text-muted ms-1")
                ])
            ], width=4),
            dbc.Col([
                status_badge
            ], width=3),
            dbc.Col([
                html.Small([
                    html.I(className="fas fa-percentage me-1"),
                    f"{success_rate:.0f}% success"
                ], className="text-muted")
            ], width=3),
            dbc.Col([
                html.Small(next_run_text, className="text-muted") if next_run_text else html.Span()
            ], width=2)
        ], className="align-items-center")
    ], className="py-2 border-bottom border-light")

