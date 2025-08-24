"""
Deployment Configuration Utility
Loads and manages Prefect deployment configurations for dashboard monitoring
"""

import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import pytz

try:
    from .logging_config import get_ui_logger
except ImportError:
    # Fallback for when running directly
    import sys
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    from src.utils.logging_config import get_ui_logger

logger = get_ui_logger("deployment_config")


@dataclass
class DeploymentConfig:
    """Configuration for a single deployment"""
    name: str
    display_name: str
    description: str
    category: str
    priority: int
    schedule_type: str
    tags: List[str]
    expected_runtime_minutes: int
    alert_threshold_hours: int
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        if self.priority < 1:
            raise ValueError(f"Priority must be >= 1, got {self.priority}")
        if self.expected_runtime_minutes <= 0:
            raise ValueError(f"Expected runtime must be > 0, got {self.expected_runtime_minutes}")
        if self.alert_threshold_hours <= 0:
            raise ValueError(f"Alert threshold must be > 0, got {self.alert_threshold_hours}")


@dataclass
class ScheduleType:
    """Schedule type definition"""
    cron: str
    timezone: str
    description: str


class DeploymentConfigManager:
    """Manages deployment configurations for the dashboard"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize with config file path"""
        if config_path is None:
            # Default to config/deployments_config.yaml in project root
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "config" / "deployments_config.yaml"
        
        self.config_path = Path(config_path)
        self._config_data = None
        self._deployments = {}
        self._schedule_types = {}
        self._dashboard_settings = {}
        
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from YAML file"""
        try:
            if not self.config_path.exists():
                raise FileNotFoundError(f"Config file not found: {self.config_path}")
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config_data = yaml.safe_load(f)
            
            # Parse deployments
            deployments_data = self._config_data.get('deployments', {})
            for name, config in deployments_data.items():
                try:
                    self._deployments[name] = DeploymentConfig(
                        name=config['name'],
                        display_name=config['display_name'],
                        description=config['description'],
                        category=config['category'],
                        priority=config['priority'],
                        schedule_type=config['schedule_type'],
                        tags=config.get('tags', []),
                        expected_runtime_minutes=config['expected_runtime_minutes'],
                        alert_threshold_hours=config['alert_threshold_hours']
                    )
                except (KeyError, ValueError) as e:
                    logger.error(f"Invalid deployment config for '{name}': {e}")
                    continue
            
            # Parse schedule types
            schedule_types_data = self._config_data.get('schedule_types', {})
            for name, config in schedule_types_data.items():
                self._schedule_types[name] = ScheduleType(
                    cron=config['cron'],
                    timezone=config['timezone'],
                    description=config['description']
                )
            
            # Parse dashboard settings
            self._dashboard_settings = self._config_data.get('dashboard', {})
            
            logger.info(f"Loaded {len(self._deployments)} deployment configs and {len(self._schedule_types)} schedule types")
            
        except Exception as e:
            logger.error(f"Error loading deployment config: {e}")
            # Initialize with empty configs to prevent crashes
            self._deployments = {}
            self._schedule_types = {}
            self._dashboard_settings = {}
    
    def get_deployment(self, name: str) -> Optional[DeploymentConfig]:
        """Get deployment configuration by name"""
        return self._deployments.get(name)
    
    def get_all_deployments(self) -> Dict[str, DeploymentConfig]:
        """Get all deployment configurations"""
        return self._deployments.copy()
    
    def get_deployments_by_category(self, category: str) -> Dict[str, DeploymentConfig]:
        """Get deployments filtered by category"""
        return {
            name: config for name, config in self._deployments.items() 
            if config.category == category
        }
    
    def get_deployments_by_priority(self, limit: Optional[int] = None) -> List[DeploymentConfig]:
        """Get deployments sorted by priority (highest first)"""
        sorted_deployments = sorted(
            self._deployments.values(), 
            key=lambda x: x.priority
        )
        
        if limit is not None:
            sorted_deployments = sorted_deployments[:limit]
        
        return sorted_deployments
    
    def get_primary_deployments(self) -> List[str]:
        """Get list of primary deployment names for dashboard"""
        primary = self._dashboard_settings.get('primary_deployments', [])
        
        # If no primary deployments configured, return top priority ones
        if not primary:
            top_deployments = self.get_deployments_by_priority(limit=3)
            return [d.name for d in top_deployments]
        
        return primary
    
    def get_schedule_type(self, name: str) -> Optional[ScheduleType]:
        """Get schedule type by name"""
        return self._schedule_types.get(name)
    
    def get_dashboard_setting(self, key: str, default: Any = None) -> Any:
        """Get dashboard setting by key"""
        return self._dashboard_settings.get(key, default)
    
    def calculate_next_run(self, deployment_name: str, current_time: Optional[datetime] = None) -> Optional[datetime]:
        """Calculate next scheduled run for a deployment"""
        deployment = self.get_deployment(deployment_name)
        if not deployment:
            return None
        
        schedule_type = self.get_schedule_type(deployment.schedule_type)
        if not schedule_type:
            return None
        
        if current_time is None:
            current_time = datetime.now()
        
        # Convert to deployment timezone
        try:
            tz = pytz.timezone(schedule_type.timezone)
            current_time = current_time.astimezone(tz)
        except Exception:
            logger.warning(f"Invalid timezone {schedule_type.timezone}, using UTC")
            tz = pytz.UTC
            current_time = current_time.astimezone(tz)
        
        return self._calculate_next_run_from_cron(schedule_type.cron, current_time, tz)
    
    def _calculate_next_run_from_cron(self, cron: str, current_time: datetime, tz: pytz.BaseTzInfo) -> Optional[datetime]:
        """Calculate next run from cron expression (simplified implementation)"""
        try:
            # This is a simplified implementation for common patterns
            # For production, consider using croniter library
            
            if cron == "0 9-16 * * 1-5":  # Market hours pattern
                return self._calculate_market_hours_next_run(current_time, tz)
            elif cron.startswith("0 ") and cron.count(" ") == 4:  # Daily patterns
                hour = int(cron.split()[1])
                return self._calculate_daily_next_run(current_time, tz, hour)
            elif cron.startswith("*/"):  # Interval patterns
                interval = int(cron.split()[0][2:])
                return self._calculate_interval_next_run(current_time, interval)
            else:
                logger.warning(f"Unsupported cron pattern: {cron}")
                return None
                
        except Exception as e:
            logger.error(f"Error calculating next run from cron '{cron}': {e}")
            return None
    
    def _calculate_market_hours_next_run(self, current_time: datetime, tz: pytz.BaseTzInfo) -> datetime:
        """Calculate next run for market hours schedule (9 AM - 4 PM EST, weekdays)"""
        now = current_time.astimezone(tz)
        
        # Market hours: 9 AM - 4 PM (16:00), Monday-Friday
        if now.weekday() < 5:  # Weekday
            if 9 <= now.hour < 16:  # During market hours
                # Next hour at :00
                next_run = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
            elif now.hour < 9:  # Before market opens
                next_run = now.replace(hour=9, minute=0, second=0, microsecond=0)
            else:  # After market closes
                # Next trading day at 9 AM
                next_day = now + timedelta(days=1)
                while next_day.weekday() >= 5:  # Skip weekends
                    next_day += timedelta(days=1)
                next_run = next_day.replace(hour=9, minute=0, second=0, microsecond=0)
        else:  # Weekend
            # Next Monday at 9 AM
            days_until_monday = (7 - now.weekday()) % 7
            if days_until_monday == 0:
                days_until_monday = 1
            next_monday = now + timedelta(days=days_until_monday)
            next_run = next_monday.replace(hour=9, minute=0, second=0, microsecond=0)
        
        return next_run
    
    def _calculate_daily_next_run(self, current_time: datetime, tz: pytz.BaseTzInfo, hour: int) -> datetime:
        """Calculate next run for daily schedule at specific hour"""
        now = current_time.astimezone(tz)
        
        if now.hour < hour:
            # Today at the specified hour
            next_run = now.replace(hour=hour, minute=0, second=0, microsecond=0)
        else:
            # Tomorrow at the specified hour
            tomorrow = now + timedelta(days=1)
            next_run = tomorrow.replace(hour=hour, minute=0, second=0, microsecond=0)
        
        return next_run
    
    def _calculate_interval_next_run(self, current_time: datetime, interval_minutes: int) -> datetime:
        """Calculate next run for interval-based schedule"""
        # Round up to next interval boundary
        minutes_since_hour = current_time.minute
        next_boundary = ((minutes_since_hour // interval_minutes) + 1) * interval_minutes
        
        if next_boundary >= 60:
            next_run = current_time.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1, minutes=next_boundary-60)
        else:
            next_run = current_time.replace(minute=next_boundary, second=0, microsecond=0)
        
        return next_run
    
    def should_alert(self, deployment_name: str, last_failure_time: datetime) -> bool:
        """Check if an alert should be raised for a failed deployment"""
        deployment = self.get_deployment(deployment_name)
        if not deployment:
            return False
        
        time_since_failure = datetime.now() - last_failure_time
        return time_since_failure.total_seconds() > (deployment.alert_threshold_hours * 3600)
    
    def reload_config(self) -> None:
        """Reload configuration from file"""
        logger.info("Reloading deployment configuration...")
        self._load_config()


# Global instance
_deployment_config = None

def get_deployment_config() -> DeploymentConfigManager:
    """Get global deployment configuration manager instance"""
    global _deployment_config
    if _deployment_config is None:
        _deployment_config = DeploymentConfigManager()
    return _deployment_config