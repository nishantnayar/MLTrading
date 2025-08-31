"""
Prefect Service
Handles integration with Prefect API for data pipeline monitoring
"""

import os
import httpx
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
import asyncio
import json

try:
    from ..utils.logging_config import get_ui_logger
    from ..utils.deployment_config import get_deployment_config
except ImportError:
    # Fallback for when running directly
    import sys
    from pathlib import Path
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    from src.utils.logging_config import get_ui_logger
    from src.utils.deployment_config import get_deployment_config

# Load environment variables
load_dotenv()

logger = get_ui_logger("prefect_service")


class PrefectService:
    """Service for interacting with Prefect API"""


    def __init__(self, api_url: Optional[str] = None):
        """Initialize Prefect service"""
        self.api_url = api_url or os.getenv('PREFECT_API_URL', 'http://localhost:4200/api')
        self.client = httpx.Client(base_url=self.api_url, timeout=10.0)
        self._connected = False
        self.config = get_deployment_config()

        # Test connection on initialization
        self._test_connection()


    def _test_connection(self) -> bool:
        """Test connection to Prefect API"""
        try:
            response = self.client.get('/health')
            if response.status_code == 200:
                self._connected = True
                logger.info("Connected to Prefect API")
                return True
            else:
                logger.warning(f"Prefect API responded with status {response.status_code}")
                self._connected = False
                return False
        except Exception as e:
            logger.warning(f"Cannot connect to Prefect API: {e}")
            self._connected = False
            return False


    def is_connected(self) -> bool:
        """Check if connected to Prefect API"""
        return self._connected


    def get_deployments(self, name_filter: Optional[str] = None) -> List[Dict]:
        """Get deployments, optionally filtered by name"""
        if not self._connected:
            return []

        try:
            params = {}
            if name_filter:
                params['name'] = {'like_': f'%{name_filter}%'}

            response = self.client.post('/deployments/filter', json=params)
            response.raise_for_status()

            deployments = response.json()
            logger.debug(f"Retrieved {len(deployments)} deployments")
            return deployments

        except Exception as e:
            logger.error(f"Error getting deployments: {e}")
            return []


    def get_flow_runs(self, deployment_name: Optional[str] = None,
                      limit: int = 10, state_type: Optional[str] = None) -> List[Dict]:
        """Get recent flow runs"""
        if not self._connected:
            return []

        try:
            # Build filter
            filters = {
                'limit': limit,
                'sort': 'START_TIME_DESC'
            }

            if deployment_name:
                filters['deployments'] = {'name': {'any_': [deployment_name]}}

            if state_type:
                filters['flow_runs'] = {'state': {'type': {'any_': [state_type]}}}

            response = self.client.post('/flow_runs/filter', json=filters)
            response.raise_for_status()

            flow_runs = response.json()
            logger.debug(f"Retrieved {len(flow_runs)} flow runs")
            return flow_runs

        except Exception as e:
            logger.error(f"Error getting flow runs: {e}")
            return []


    def get_deployment_status(self, deployment_name: str) -> Dict:
        """Get comprehensive status for a specific deployment"""
        if not self._connected:
            return {
                'connected': False,
                'deployment': None,
                'last_run': None,
                'next_run': None,
                'recent_runs': [],
                'success_rate': 0.0,
                'config': None
            }

        try:
            # Get deployment info
            deployments = self.get_deployments(deployment_name)
            deployment = next((d for d in deployments if d['name'] == deployment_name), None)

            if not deployment:
                logger.warning(f"Deployment '{deployment_name}' not found")
                return {
                    'connected': True,
                    'deployment': None,
                    'last_run': None,
                    'next_run': None,
                    'recent_runs': [],
                    'success_rate': 0.0,
                    'error': f"Deployment '{deployment_name}' not found",
                    'config': self.config.get_deployment(deployment_name)
                }

            # Get recent flow runs for this deployment
            recent_runs = self.get_flow_runs(deployment_name=deployment_name, limit=20)

            # Get last run
            last_run = recent_runs[0] if recent_runs else None

            # Calculate success rate
            if recent_runs:
                completed_runs = [r for r in recent_runs if r.get('state', {}).get('type') in ['COMPLETED', 'FAILED', 'CANCELLED']]
                successful_runs = [r for r in completed_runs if r.get('state', {}).get('type') == 'COMPLETED']
                success_rate = (len(successful_runs) / len(completed_runs)) * 100 if completed_runs else 0.0
            else:
                success_rate = 0.0

            # Get next scheduled run using configuration
            next_run = self.config.calculate_next_run(deployment_name)

            # Get deployment config
            deployment_config = self.config.get_deployment(deployment_name)

            return {
                'connected': True,
                'deployment': deployment,
                'last_run': last_run,
                'next_run': next_run,
                'recent_runs': recent_runs[:10],  # Limit to 10 for UI
                'success_rate': success_rate,
                'config': deployment_config
            }

        except Exception as e:
            logger.error(f"Error getting deployment status for '{deployment_name}': {e}")
            return {
                'connected': True,
                'deployment': None,
                'last_run': None,
                'next_run': None,
                'recent_runs': [],
                'success_rate': 0.0,
                'error': str(e),
                'config': None
            }


    def get_multiple_deployment_status(self, deployment_names: Optional[List[str]] = None) -> Dict[str, Dict]:
        """Get status for multiple deployments"""
        if deployment_names is None:
            # Get primary deployments from config
            deployment_names = self.config.get_primary_deployments()

        results = {}
        for name in deployment_names:
            results[name] = self.get_deployment_status(name)

        return results


    def get_configured_deployments(self) -> Dict[str, Any]:
        """Get all configured deployments with their configs"""
        return {
            name: {
                'config': config,
                'status': self.get_deployment_status(name)
            }
            for name, config in self.config.get_all_deployments().items()
        }


    def _calculate_next_run(self, deployment: Dict) -> Optional[datetime]:
        """Calculate next scheduled run time (simplified)"""
        try:
            schedule = deployment.get('schedule')
            if not schedule:
                return None

            # This is a simplified implementation
            # In reality, you'd need to parse the cron expression properly
            cron = schedule.get('cron')
            if cron and 'cron' in schedule:
                # For the yahoo deployment: "0 9-16 * * 1-5" (hourly 9-4 EST, Mon-Fri)
                now = datetime.now()

                # Simple logic: if it's a weekday and before 4 PM, next run is next hour at :00
                if now.weekday() < 5:  # Monday = 0, Friday = 4
                    if 9 <= now.hour < 16:  # During market hours
                        next_hour = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
                        return next_hour
                    elif now.hour < 9:  # Before market opens
                        return now.replace(hour=9, minute=0, second=0, microsecond=0)
                    else:  # After market closes, next trading day at 9 AM
                        next_day = now + timedelta(days=1)
                        while next_day.weekday() >= 5:  # Skip weekends
                            next_day += timedelta(days=1)
                        return next_day.replace(hour=9, minute=0, second=0, microsecond=0)
                else:  # Weekend - next Monday at 9 AM
                    days_until_monday = (7 - now.weekday()) % 7
                    if days_until_monday == 0:
                        days_until_monday = 1
                    next_monday = now + timedelta(days=days_until_monday)
                    return next_monday.replace(hour=9, minute=0, second=0, microsecond=0)

            return None

        except Exception as e:
            logger.error(f"Error calculating next run: {e}")
            return None


    def trigger_flow_run(self, deployment_name: str, parameters: Optional[Dict] = None) -> Optional[Dict]:
        """Manually trigger a flow run"""
        if not self._connected:
            return None

        try:
            # Get deployment ID
            deployments = self.get_deployments(deployment_name)
            deployment = next((d for d in deployments if d['name'] == deployment_name), None)

            if not deployment:
                logger.error(f"Deployment '{deployment_name}' not found")
                return None

            deployment_id = deployment['id']

            # Create flow run
            flow_run_data = {
                'deployment_id': deployment_id,
                'parameters': parameters or {}
            }

            response = self.client.post('/deployments/{}/create_flow_run', json=flow_run_data)
            response.raise_for_status()

            flow_run = response.json()
            logger.info(f"Triggered flow run: {flow_run.get('id', 'unknown')}")
            return flow_run

        except Exception as e:
            logger.error(f"Error triggering flow run for '{deployment_name}': {e}")
            return None


    def get_data_freshness_metrics(self, deployment_name: Optional[str] = None) -> Dict:
        """Get data freshness metrics for a deployment"""
        if deployment_name is None:
            # Default to first primary deployment
            primary_deployments = self.config.get_primary_deployments()
            if not primary_deployments:
                return {'status': 'no_deployments', 'color': 'secondary'}
            deployment_name = primary_deployments[0]

        try:
            # Get the most recent successful runs for the deployment
            recent_runs = self.get_flow_runs(deployment_name=deployment_name, limit=5)
            successful_runs = [r for r in recent_runs if r.get('state', {}).get('type') == 'COMPLETED']

            if successful_runs:
                last_successful = successful_runs[0]
                end_time = last_successful.get('end_time')

                if end_time:
                    # Parse the timestamp
                    if isinstance(end_time, str):
                        last_update = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                    else:
                        last_update = end_time

                    # Calculate freshness
                    now = datetime.now().astimezone()
                    time_since_update = now - last_update.astimezone()

                    # Determine freshness status
                    if time_since_update.total_seconds() < 3600:  # Less than 1 hour
                        status = 'fresh'
                        color = 'success'
                    elif time_since_update.total_seconds() < 7200:  # Less than 2 hours
                        status = 'moderate'
                        color = 'warning'
                    else:
                        status = 'stale'
                        color = 'danger'

                    return {
                        'last_update': last_update,
                        'time_since_update': time_since_update,
                        'status': status,
                        'color': color,
                        'last_successful_run': last_successful
                    }

            # No successful runs found
            return {
                'last_update': None,
                'time_since_update': None,
                'status': 'unknown',
                'color': 'secondary',
                'last_successful_run': None
            }

        except Exception as e:
            logger.error(f"Error getting data freshness metrics: {e}")
            return {
                'last_update': None,
                'time_since_update': None,
                'status': 'error',
                'color': 'danger',
                'error': str(e)
            }


    def get_system_health(self) -> Dict:
        """Get overall system health metrics"""
        try:
            # Get configured deployments to focus health metrics
            configured_deployments = list(self.config.get_all_deployments().keys())

            # Get recent flow runs for configured deployments only
            all_runs = []
            for deployment_name in configured_deployments:
                deployment_runs = self.get_flow_runs(deployment_name=deployment_name, limit=20)
                all_runs.extend(deployment_runs)

            # If no configured deployments have runs, fall back to all runs
            if not all_runs:
                all_runs = self.get_flow_runs(limit=50)

            recent_runs = all_runs[:50]  # Limit to most recent 50

            # Categorize by status
            completed = len([r for r in recent_runs if r.get('state', {}).get('type') == 'COMPLETED'])
            failed = len([r for r in recent_runs if r.get('state', {}).get('type') == 'FAILED'])
            running = len([r for r in recent_runs if r.get('state', {}).get('type') == 'RUNNING'])
            scheduled = len([r for r in recent_runs if r.get('state', {}).get('type') == 'SCHEDULED'])

            # Calculate health score
            total_completed_or_failed = completed + failed
            success_rate = (completed / total_completed_or_failed * 100) if total_completed_or_failed > 0 else 100

            # Determine health status
            if success_rate >= 95:
                health_status = 'excellent'
                health_color = 'success'
            elif success_rate >= 85:
                health_status = 'good'
                health_color = 'success'
            elif success_rate >= 70:
                health_status = 'fair'
                health_color = 'warning'
            else:
                health_status = 'poor'
                health_color = 'danger'

            return {
                'connected': True,
                'success_rate': success_rate,
                'health_status': health_status,
                'health_color': health_color,
                'runs': {
                    'completed': completed,
                    'failed': failed,
                    'running': running,
                    'scheduled': scheduled,
                    'total': len(recent_runs)
                }
            }

        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return {
                'connected': False,
                'success_rate': 0.0,
                'health_status': 'error',
                'health_color': 'danger',
                'error': str(e),
                'runs': {
                    'completed': 0,
                    'failed': 0,
                    'running': 0,
                    'scheduled': 0,
                    'total': 0
                }
            }


    def __del__(self):
        """Clean up HTTP client"""
        try:
            if hasattr(self, 'client'):
                self.client.close()
        except Exception:
            pass


# Global instance for easy access
_prefect_service = None


def get_prefect_service() -> PrefectService:
    """Get global Prefect service instance"""
    global _prefect_service
    if _prefect_service is None:
        _prefect_service = PrefectService()
    return _prefect_service

