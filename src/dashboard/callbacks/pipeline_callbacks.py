"""
Pipeline Status Callbacks
Handles interactions with Prefect pipeline status components
"""

import dash
from dash import Input, Output, State, callback_context, html
import dash_bootstrap_components as dbc
from datetime import datetime
import traceback

from ..components.pipeline_status import (
    create_pipeline_status_card,
    create_data_freshness_indicator,
    create_system_health_summary,
    create_multi_deployment_status_card
)
from ...services.prefect_service import get_prefect_service
from ...utils.logging_config import get_ui_logger
from ...utils.deployment_config import get_deployment_config

logger = get_ui_logger("pipeline_callbacks")


def register_pipeline_callbacks(app):
    """Register all pipeline-related callbacks"""

    @app.callback(
        Output("pipeline-status-card", "children"),
        [Input("pipeline-status-interval", "n_intervals")]
    )


    def update_pipeline_status_card(n_intervals):
        """Update the main pipeline status card"""
        try:
            prefect_service = get_prefect_service()
            config_manager = get_deployment_config()

            # Get primary deployment from config
            primary_deployments = config_manager.get_primary_deployments()
            if not primary_deployments:
                return dbc.Alert([
                    html.I(className="fas fa-info-circle me-2"),
                    "No deployments configured"
                ], color="info")

            # Get deployment status for primary deployment
            status_data = prefect_service.get_deployment_status(primary_deployments[0])

            return create_pipeline_status_card(status_data)

        except Exception as e:
            logger.error(f"Error updating pipeline status: {e}")
            logger.error(traceback.format_exc())

            # Return error card
            return dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                f"Error loading pipeline status: {str(e)}"
            ], color="danger")

    @app.callback(
        Output("system-health-summary", "children"),
        [Input("pipeline-status-interval", "n_intervals")]
    )


    def update_system_health_summary(n_intervals):
        """Update the system health summary"""
        try:
            prefect_service = get_prefect_service()
            health_data = prefect_service.get_system_health()

            return create_system_health_summary(health_data)

        except Exception as e:
            logger.error(f"Error updating system health: {e}")

            return dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                "Error loading system health"
            ], color="warning", className="mb-0")

    @app.callback(
        Output("data-freshness-indicator", "children"),
        [Input("pipeline-status-interval", "n_intervals")]
    )


    def update_data_freshness_indicator(n_intervals):
        """Update the data freshness indicator"""
        try:
            prefect_service = get_prefect_service()
            freshness_data = prefect_service.get_data_freshness_metrics()

            return create_data_freshness_indicator(freshness_data)

        except Exception as e:
            logger.error(f"Error updating data freshness: {e}")

            # Return empty div on error to avoid breaking the layout
            return html.Div()

    @app.callback(
        [Output("pipeline-history-modal", "is_open"),
         Output("pipeline-history-content", "children")],
        [Input("close-pipeline-history-modal", "n_clicks")],
        [State("pipeline-history-modal", "is_open")],
        prevent_initial_call=True
    )


    def toggle_pipeline_history_modal(close_clicks, is_open):
        """Toggle the pipeline history modal and load data"""
        ctx = callback_context

        if not ctx.triggered:
            return False, html.Div()

        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

        if trigger_id == "close-pipeline-history-modal":
            # Close modal
            return False, html.Div()

        return is_open, dash.no_update

    @app.callback(
        Output("trigger-pipeline-notification", "children"),
        [Input("trigger-pipeline-btn", "n_clicks")],
        prevent_initial_call=True
    )


    def trigger_pipeline_run(trigger_clicks):
        """Handle manual pipeline trigger"""
        if not trigger_clicks:
            return dash.no_update

        try:
            prefect_service = get_prefect_service()
            config_manager = get_deployment_config()

            # Get primary deployment to trigger
            primary_deployments = config_manager.get_primary_deployments()
            if not primary_deployments:
                return dbc.Toast([
                    html.P([
                        html.I(className="fas fa-exclamation-triangle me-2 text-warning"),
                        "No deployments configured"
                    ], className="mb-0")
                ],
                    header="No Deployments",
                    id="pipeline-trigger-error-toast",
                    is_open=True,
                    dismissable=True,
                    duration=5000,
                    style={"position": "fixed", "top": 66, "right": 10, "width": 350}
                )

            # Trigger the flow run for the primary deployment
            deployment_name = primary_deployments[0]
            flow_run = prefect_service.trigger_flow_run(deployment_name)

            if flow_run:
                return dbc.Toast([
                    html.P([
                        html.I(className="fas fa-check-circle me-2 text-success"),
                        "Pipeline run triggered successfully!"
                    ], className="mb-0"),
                    html.Small(f"Run ID: {flow_run.get('id', 'Unknown')[:8]}...", className="text-muted")
                ],
                    header="Pipeline Triggered",
                    id="pipeline-trigger-toast",
                    is_open=True,
                    dismissable=True,
                    duration=5000,
                    style={"position": "fixed", "top": 66, "right": 10, "width": 350}
                )
            else:
                return dbc.Toast([
                    html.P([
                        html.I(className="fas fa-exclamation-triangle me-2 text-warning"),
                        "Failed to trigger pipeline run"
                    ], className="mb-0")
                ],
                    header="Pipeline Trigger Failed",
                    id="pipeline-trigger-error-toast",
                    is_open=True,
                    dismissable=True,
                    duration=5000,
                    style={"position": "fixed", "top": 66, "right": 10, "width": 350}
                )

        except Exception as e:
            logger.error(f"Error triggering pipeline: {e}")

            return dbc.Toast([
                html.P([
                    html.I(className="fas fa-times-circle me-2 text-danger"),
                    f"Error triggering pipeline: {str(e)}"
                ], className="mb-0")
            ],
                header="Pipeline Error",
                id="pipeline-trigger-error-toast",
                is_open=True,
                dismissable=True,
                duration=7000,
                style={"position": "fixed", "top": 66, "right": 10, "width": 350}
            )

    @app.callback(
        Output("pipeline-status-alert", "children"),
        [Input("pipeline-status-interval", "n_intervals")]
    )


    def check_pipeline_health_alerts(n_intervals):
        """Check for critical pipeline issues and show alerts"""
        try:
            prefect_service = get_prefect_service()
            config_manager = get_deployment_config()

            # Check if we're connected
            if not prefect_service.is_connected():
                return html.Div()  # Don't show alert if not connected

            # Get primary deployment from config
            primary_deployments = config_manager.get_primary_deployments()
            if not primary_deployments:
                return html.Div()  # No deployments to check

            deployment_name = primary_deployments[0]

            # Get recent runs to check for failures
            recent_runs = prefect_service.get_flow_runs(
                deployment_name=deployment_name,
                limit=5
            )

            # Check for consecutive failures
            if recent_runs:
                recent_states = [run.get('state', {}).get('type', 'UNKNOWN') for run in recent_runs[:3]]

                # If last 3 runs failed, show critical alert
                if all(state == 'FAILED' for state in recent_states):
                    return dbc.Alert([
                        html.I(className="fas fa-exclamation-circle me-2"),
                        html.Strong("Critical: "),
                        "Data pipeline has failed multiple times. Manual intervention may be required."
                    ], color="danger", dismissable=True, className="mt-2")

                # If last run failed and it's been more than 2 hours, show warning
                last_run = recent_runs[0]
                if last_run.get('state', {}).get('type') == 'FAILED':
                    try:
                        end_time = last_run.get('end_time')
                        if end_time:
                            if isinstance(end_time, str):
                                end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))

                            time_since_failure = datetime.now().astimezone() - end_time.astimezone()

                            if time_since_failure.total_seconds() > 7200:  # 2 hours
                                return dbc.Alert([
                                    html.I(className="fas fa-exclamation-triangle me-2"),
                                    html.Strong("Warning: "),
                                    f"Data pipeline failed {int(time_since_failure.total_seconds() / 3600)}h ago. "
                                    "Data may be stale."
                                ], color="warning", dismissable=True, className="mt-2")
                    except Exception:
                        pass

            return html.Div()  # No alerts needed

        except Exception as e:
            logger.error(f"Error checking pipeline health alerts: {e}")
            return html.Div()  # Don't show errors for health checks

    # New callback for multiple deployments overview
    @app.callback(
        Output("multi-deployment-status", "children"),
        [Input("pipeline-status-interval", "n_intervals")]
    )


    def update_multi_deployment_status(n_intervals):
        """Update status for multiple deployments"""
        try:
            prefect_service = get_prefect_service()
            config_manager = get_deployment_config()

            # Get all configured deployments
            primary_deployments = config_manager.get_primary_deployments()
            if not primary_deployments:
                return html.Div([
                    dbc.Alert([
                        html.I(className="fas fa-info-circle me-2"),
                        "No deployments configured for monitoring"
                    ], color="info")
                ])

            # Get status for multiple deployments
            deployments_status = prefect_service.get_multiple_deployment_status(primary_deployments)

            return create_multi_deployment_status_card(deployments_status)

        except Exception as e:
            logger.error(f"Error updating multi-deployment status: {e}")

            return dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                "Error loading deployment status"
            ], color="warning", className="mb-0")

