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

    # Determine status color and icon
    if last_run:
        last_run_state = last_run.get('state', {}).get('type', 'UNKNOWN')
        if last_run_state == 'COMPLETED':
            status_color = 'success'
            status_icon = 'fas fa-check-circle'
            status_text = 'Healthy'
        elif last_run_state == 'FAILED':
            status_color = 'danger'
            status_icon = 'fas fa-exclamation-circle'
            status_text = 'Failed'
        elif last_run_state == 'RUNNING':
            status_color = 'info'
            status_icon = 'fas fa-sync fa-spin'
            status_text = 'Running'
        elif last_run_state == 'SCHEDULED':
            status_color = 'warning'
            status_icon = 'fas fa-clock'
            status_text = 'Scheduled'
        else:
            status_color = 'secondary'
            status_icon = 'fas fa-question-circle'
            status_text = 'Unknown'
    else:
        status_color = 'info'
        status_icon = 'fas fa-clock'
        status_text = 'Scheduled'

    # Format last run time - handle both completed and scheduled runs
    last_run_text = 'No runs yet'
    if last_run:
        try:
            # For completed/failed runs, use end_time
            if last_run.get('end_time'):
                end_time = last_run['end_time']
                if isinstance(end_time, str):
                    end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))

                now = datetime.now().astimezone()
                time_diff = now - end_time.astimezone()

                if time_diff.total_seconds() < 60:
                    last_run_text = 'Just now'
                elif time_diff.total_seconds() < 3600:
                    minutes = int(time_diff.total_seconds() / 60)
                    last_run_text = f'{minutes}m ago'
                elif time_diff.total_seconds() < 86400:
                    hours = int(time_diff.total_seconds() / 3600)
                    last_run_text = f'{hours}h ago'
                else:
                    days = int(time_diff.total_seconds() / 86400)
                    last_run_text = f'{days}d ago'

            # For scheduled/running runs, use created time with status
            elif last_run.get('created'):
                created_time = last_run['created']
                if isinstance(created_time, str):
                    created_time = datetime.fromisoformat(created_time.replace('Z', '+00:00'))

                now = datetime.now().astimezone()
                time_diff = now - created_time.astimezone()

                if time_diff.total_seconds() < 3600:
                    minutes = int(time_diff.total_seconds() / 60)
                    last_run_text = f'Scheduled {minutes}m ago'
                elif time_diff.total_seconds() < 86400:
                    hours = int(time_diff.total_seconds() / 3600)
                    last_run_text = f'Scheduled {hours}h ago'
                else:
                    days = int(time_diff.total_seconds() / 86400)
                    last_run_text = f'Scheduled {days}d ago'

        except Exception:
            last_run_text = 'Unknown'

    # If no runs yet but we have a next run, show that information
    if last_run_text == 'No runs yet' and next_run:
        try:
            if isinstance(next_run, str):
                next_run_dt = datetime.fromisoformat(next_run.replace('Z', '+00:00'))
            else:
                next_run_dt = next_run

            now = datetime.now().astimezone()
            if hasattr(next_run_dt, 'astimezone'):
                time_until = next_run_dt.astimezone() - now
            else:
                time_until = next_run_dt - now.replace(tzinfo=None)

            if time_until.total_seconds() > 0:
                if time_until.total_seconds() < 3600:  # Less than 1 hour
                    minutes = int(time_until.total_seconds() / 60)
                    last_run_text = f'First run in {minutes}m'
                elif time_until.total_seconds() < 86400:  # Less than 1 day
                    hours = int(time_until.total_seconds() / 3600)
                    last_run_text = f'First run in {hours}h'
                else:
                    days = int(time_until.total_seconds() / 86400)
                    last_run_text = f'First run in {days}d'
        except Exception:
            pass  # Keep default "No runs yet"

    # Format next run time
    next_run_text = 'Not scheduled'
    if next_run:
        try:
            if isinstance(next_run, str):
                next_run = datetime.fromisoformat(next_run)

            now = datetime.now()
            time_until = next_run - now

            if time_until.total_seconds() < 0:
                next_run_text = 'Overdue'
            elif time_until.total_seconds() < 60:
                next_run_text = 'Starting soon'
            elif time_until.total_seconds() < 3600:
                minutes = int(time_until.total_seconds() / 60)
                next_run_text = f'In {minutes}m'
            elif time_until.total_seconds() < 86400:
                hours = int(time_until.total_seconds() / 3600)
                next_run_text = f'In {hours}h'
            else:
                days = int(time_until.total_seconds() / 86400)
                next_run_text = f'In {days}d'

        except Exception:
            next_run_text = 'Unknown'

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
        # start_time = run.get('start_time', '')  # Currently unused
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
                # start_time = start_dt.strftime('%Y-%m-%d %H:%M')  # Currently unused
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

    if not status_data.get('connected', False):
        status_badge = dbc.Badge([
            html.I(className="fas fa-unlink me-1"),
            "Disconnected"
        ], color="secondary")
    else:
        last_run = status_data.get('last_run')
        if last_run:
            last_run_state = last_run.get('state', {}).get('type', 'UNKNOWN')
            if last_run_state == 'COMPLETED':
                status_badge = dbc.Badge([
                    html.I(className="fas fa-check-circle me-1"),
                    "Healthy"
                ], color="success")
            elif last_run_state == 'FAILED':
                status_badge = dbc.Badge([
                    html.I(className="fas fa-exclamation-circle me-1"),
                    "Failed"
                ], color="danger")
            elif last_run_state == 'RUNNING':
                status_badge = dbc.Badge([
                    html.I(className="fas fa-sync fa-spin me-1"),
                    "Running"
                ], color="info")
            else:
                status_badge = dbc.Badge([
                    html.I(className="fas fa-clock me-1"),
                    "Scheduled"
                ], color="warning")
        else:
            status_badge = dbc.Badge([
                html.I(className="fas fa-question-circle me-1"),
                "Unknown"
            ], color="secondary")

    # Calculate next run display
    next_run = status_data.get('next_run')
    if next_run:
        if isinstance(next_run, str):
            next_run = datetime.fromisoformat(next_run.replace('Z', '+00:00'))
        elif isinstance(next_run, datetime):
            pass
        else:
            next_run = None

    next_run_text = ""
    if next_run:
        now = datetime.now().astimezone()
        if hasattr(next_run, 'astimezone'):
            time_until = next_run.astimezone() - now
        else:
            time_until = next_run - now.replace(tzinfo=None)

        if time_until.total_seconds() < 3600:  # Less than 1 hour
            minutes = int(time_until.total_seconds() / 60)
            next_run_text = f"Next: {minutes}m"
        elif time_until.total_seconds() < 86400:  # Less than 1 day
            hours = int(time_until.total_seconds() / 3600)
            next_run_text = f"Next: {hours}h"
        else:
            days = int(time_until.total_seconds() / 86400)
            next_run_text = f"Next: {days}d"

    success_rate = status_data.get('success_rate', 0.0)

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

