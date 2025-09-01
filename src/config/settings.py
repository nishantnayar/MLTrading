"""
Unified Configuration Management System

Consolidates all configuration files into a single, validated configuration system
using Pydantic for type safety and environment variable integration.
"""

import os
from typing import Dict, List, Optional
from pathlib import Path
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings
import yaml


class DatabaseConfig(BaseModel):
    """Database connection configuration"""
    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=5432, description="Database port")
    name: str = Field(default="mltrading", description="Database name")
    user: str = Field(default="postgres", description="Database user")
    password: str = Field(default="", description="Database password")
    min_connections: int = Field(default=1, ge=1, le=50, description="Minimum pool connections")
    max_connections: int = Field(default=20, ge=1, le=50, description="Maximum pool connections")
    timeout: int = Field(default=30, ge=5, le=300, description="Connection timeout in seconds")


class AlpacaConfig(BaseModel):
    """Alpaca trading API configuration"""
    paper_base_url: str = Field(default="https://paper-api.alpaca.markets", description="Paper trading API URL")
    live_base_url: str = Field(default="https://api.alpaca.markets", description="Live trading API URL")
    paper_api_key: Optional[str] = Field(default=None, description="Paper trading API key")
    paper_secret_key: Optional[str] = Field(default=None, description="Paper trading secret key")
    live_api_key: Optional[str] = Field(default=None, description="Live trading API key")
    live_secret_key: Optional[str] = Field(default=None, description="Live trading secret key")


class TradingConfig(BaseModel):
    """Trading execution configuration"""
    mode: str = Field(default="paper", description="Trading mode: paper or live")
    default_order_type: str = Field(default="market", description="Default order type")
    default_time_in_force: str = Field(default="day", description="Default order time in force")
    max_order_value: float = Field(default=10000.0, gt=0, description="Maximum dollar value per order")

    @validator('mode')
    def validate_mode(cls, v):
        if v not in ['paper', 'live']:
            raise ValueError('Trading mode must be "paper" or "live"')
        return v


class RiskConfig(BaseModel):
    """Risk management configuration"""
    max_daily_orders: int = Field(default=25, ge=1, le=1000, description="Maximum orders per day")
    max_position_size: int = Field(default=1000, ge=1, description="Maximum shares per position")
    max_total_positions: int = Field(default=10, ge=1, le=100, description="Maximum total positions")
    max_portfolio_risk: float = Field(default=0.15, ge=0.01, le=1.0, description="Maximum portfolio risk ratio")
    emergency_stop_loss: float = Field(default=0.10, ge=0.01, le=1.0, description="Emergency stop loss ratio")
    emergency_stop: bool = Field(default=False, description="Emergency stop all trading")


class StrategyParams(BaseModel):
    """Strategy-specific parameters"""
    short_window: Optional[int] = Field(default=None, ge=1, description="Short-term window")
    long_window: Optional[int] = Field(default=None, ge=1, description="Long-term window")
    min_signal_strength: Optional[float] = Field(default=None, ge=0, le=1, description="Minimum signal strength")
    lookback_period: Optional[int] = Field(default=None, ge=1, description="Lookback period")
    rsi_period: Optional[int] = Field(default=14, ge=1, description="RSI calculation period")
    rsi_oversold: Optional[float] = Field(default=30, ge=0, le=100, description="RSI oversold threshold")
    rsi_overbought: Optional[float] = Field(default=70, ge=0, le=100, description="RSI overbought threshold")


class StrategyRiskParams(BaseModel):
    """Strategy risk parameters"""
    max_position_size: int = Field(ge=1, description="Maximum position size for this strategy")
    risk_per_trade: float = Field(ge=0.001, le=1.0, description="Risk per trade as portfolio percentage")
    stop_loss_pct: float = Field(ge=0.001, le=1.0, description="Stop loss percentage")
    take_profit_pct: float = Field(ge=0.001, le=1.0, description="Take profit percentage")


class StrategyConfig(BaseModel):
    """Individual strategy configuration"""
    class_name: str = Field(description="Strategy class name")
    enabled: bool = Field(default=True, description="Whether strategy is enabled")
    symbols: List[str] = Field(description="List of symbols for this strategy")
    parameters: StrategyParams = Field(description="Strategy parameters")
    risk_params: StrategyRiskParams = Field(description="Strategy risk parameters")
    max_positions: int = Field(default=1, ge=1, description="Maximum concurrent positions")


class ExecutionConfig(BaseModel):
    """Trading execution settings"""
    signal_processing_interval: int = Field(default=30, ge=1, description="Signal processing interval in seconds")
    market_data_refresh: int = Field(default=60, ge=1, description="Market data refresh interval in seconds")
    order_timeout: int = Field(default=300, ge=1, description="Order timeout in seconds")
    retry_failed_orders: bool = Field(default=True, description="Whether to retry failed orders")
    max_order_retries: int = Field(default=3, ge=0, le=10, description="Maximum order retry attempts")


class BacktestingConfig(BaseModel):
    """Backtesting configuration"""
    default_initial_capital: float = Field(default=100000.0, gt=0, description="Default initial capital")
    default_commission: float = Field(default=1.0, ge=0, description="Default commission per trade")
    default_slippage: float = Field(default=0.001, ge=0, description="Default slippage ratio")
    lookback_period_days: int = Field(default=252, ge=1, description="Default lookback period in days")


class ScheduleConfig(BaseModel):
    """Schedule configuration"""
    cron: str = Field(description="Cron expression")
    timezone: str = Field(default="America/New_York", description="Timezone for schedule")
    description: str = Field(description="Human-readable schedule description")


class DeploymentConfig(BaseModel):
    """Deployment configuration"""
    name: str = Field(description="Deployment name")
    display_name: str = Field(description="Display name for dashboard")
    description: str = Field(description="Deployment description")
    category: str = Field(description="Deployment category")
    priority: int = Field(ge=1, le=10, description="Priority level (1=highest)")
    schedule_type: str = Field(description="Schedule type reference")
    tags: List[str] = Field(default_factory=list, description="Deployment tags")
    expected_runtime_minutes: int = Field(ge=1, description="Expected runtime in minutes")
    alert_threshold_hours: int = Field(ge=1, description="Alert threshold in hours")


class DashboardConfig(BaseModel):
    """Dashboard display configuration"""
    primary_deployments: List[str] = Field(description="Primary deployments to display")
    max_visible_deployments: int = Field(default=10, ge=1, description="Maximum visible deployments")
    refresh_intervals: Dict[str, int] = Field(description="Refresh intervals for different components")


class FeatureEngineeringConfig(BaseModel):
    """Feature engineering configuration"""
    short_window: int = Field(default=24, description="Short-term window (1 day)")
    med_window: int = Field(default=120, description="Medium-term window (5 days)")
    long_window: int = Field(default=480, description="Long-term window (20 days)")
    min_lookback_hours: int = Field(default=600, description="Minimum lookback hours for calculations")
    rsi_windows: Dict[str, int] = Field(
        default={
            'rsi_1d': 7,
            'rsi_3d': 21,
            'rsi_1w': 35,
            'rsi_2w': 70
        },
        description="RSI calculation windows for different timeframes"
    )
    lag_periods: List[int] = Field(default=[1, 2, 4, 8, 24], description="Lag periods for temporal features")
    rolling_windows: List[int] = Field(default=[6, 12, 24], description="Rolling statistics windows")


class LoggingConfig(BaseModel):
    """Logging system configuration"""
    level: str = Field(default="INFO", description="Default logging level")
    file_log_level: str = Field(default="DEBUG", description="File logging level")
    db_log_level: str = Field(default="INFO", description="Database logging level")
    enable_database_logging: bool = Field(default=True, description="Enable database logging")
    max_log_file_size_mb: int = Field(default=50, ge=1, description="Maximum log file size in MB")
    backup_count: int = Field(default=5, ge=1, description="Number of backup log files")
    cleanup_interval_hours: int = Field(default=24, ge=1, description="Log cleanup interval in hours")


class Settings(BaseSettings):
    """
    Unified configuration management for ML Trading System.

    Automatically loads configuration from environment variables and YAML files,
    with full validation and type safety using Pydantic.

    Example:
        >>> settings = Settings()
        >>> print(f"Database: {settings.database.host}:{settings.database.port}")
        Database: localhost:5432
        >>> print(f"Trading mode: {settings.trading.mode}")
        Trading mode: paper
        >>> print(f"Feature windows: {list(settings.feature_engineering.rsi_windows.keys())}")
        Feature windows: ['rsi_1d', 'rsi_3d', 'rsi_1w', 'rsi_2w']
    """

    # Core system configurations
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    alpaca: AlpacaConfig = Field(default_factory=AlpacaConfig)
    trading: TradingConfig = Field(default_factory=TradingConfig)
    risk: RiskConfig = Field(default_factory=RiskConfig)
    execution: ExecutionConfig = Field(default_factory=ExecutionConfig)
    backtesting: BacktestingConfig = Field(default_factory=BacktestingConfig)
    feature_engineering: FeatureEngineeringConfig = Field(default_factory=FeatureEngineeringConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    # Deployment and dashboard configurations
    strategies: Dict[str, StrategyConfig] = Field(default_factory=dict)
    deployments: Dict[str, DeploymentConfig] = Field(default_factory=dict)
    schedule_types: Dict[str, ScheduleConfig] = Field(default_factory=dict)
    dashboard: Optional[DashboardConfig] = Field(default=None)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"  # Allow DB__HOST=localhost format
        case_sensitive = False
        extra = "ignore"  # Ignore extra environment variables

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._load_yaml_configs()
        self._load_environment_overrides()

    def _load_yaml_configs(self):
        """Load configuration from unified config file"""
        config_dir = Path("config")
        unified_config_file = config_dir / "config.yaml"
        
        if unified_config_file.exists():
            config_data = self._load_unified_config_file(unified_config_file)
            if config_data:
                self._apply_unified_config_data(config_data)
                print("Loaded unified configuration from config.yaml")
                return

        # Fallback to legacy config files if unified config not available
        print("Loading from legacy configuration files...")
        self._load_legacy_configs()

    def _load_unified_config_file(self, config_file: Path) -> dict:
        """Load and parse unified config file"""
        try:
            with open(config_file, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Warning: Could not load unified config: {e}")
            return None

    def _apply_unified_config_data(self, config_data: dict):
        """Apply configuration data to settings attributes"""
        config_mappings = {
            'database': (DatabaseConfig, 'database'),
            'alpaca': (AlpacaConfig, 'alpaca'),
            'trading': (TradingConfig, 'trading'),
            'risk': (RiskConfig, 'risk'),
            'execution': (ExecutionConfig, 'execution'),
            'backtesting': (BacktestingConfig, 'backtesting'),
            'feature_engineering': (FeatureEngineeringConfig, 'feature_engineering'),
            'logging': (LoggingConfig, 'logging'),
            'dashboard': (DashboardConfig, 'dashboard'),
        }

        # Apply simple config sections
        for section_name, (config_class, attr_name) in config_mappings.items():
            if section_name in config_data:
                setattr(self, attr_name, config_class(**config_data[section_name]))

        # Apply dict-based config sections
        if 'strategies' in config_data:
            self.strategies = {
                name: StrategyConfig(**config)
                for name, config in config_data['strategies'].items()
            }

        if 'deployments' in config_data:
            self.deployments = {
                name: DeploymentConfig(**config)
                for name, config in config_data['deployments'].items()
            }

        if 'schedule_types' in config_data:
            self.schedule_types = {
                name: ScheduleConfig(**config)
                for name, config in config_data['schedule_types'].items()
            }

    def _load_legacy_configs(self):
        """Load from legacy configuration files (backward compatibility)"""
        config_dir = Path("config")
        
        self._load_deployments_config(config_dir)
        self._load_strategies_config(config_dir)
        self._load_alpaca_config(config_dir)

    def _load_deployments_config(self, config_dir: Path):
        """Load deployments configuration file"""
        deployments_file = config_dir / "deployments_config.yaml"
        if not deployments_file.exists():
            return

        try:
            with open(deployments_file, 'r') as f:
                deployments_data = yaml.safe_load(f)

            if 'deployments' in deployments_data:
                self.deployments = {
                    name: DeploymentConfig(**config)
                    for name, config in deployments_data['deployments'].items()
                }

            if 'schedule_types' in deployments_data:
                self.schedule_types = {
                    name: ScheduleConfig(**config)
                    for name, config in deployments_data['schedule_types'].items()
                }

            if 'dashboard' in deployments_data:
                self.dashboard = DashboardConfig(**deployments_data['dashboard'])

        except Exception as e:
            print(f"Warning: Could not load deployments config: {e}")

    def _load_strategies_config(self, config_dir: Path):
        """Load strategies configuration file"""
        strategies_file = config_dir / "strategies_config.yaml"
        if not strategies_file.exists():
            return

        try:
            with open(strategies_file, 'r') as f:
                strategies_data = yaml.safe_load(f)

            if 'strategies' in strategies_data:
                self.strategies = {
                    name: StrategyConfig(class_name=config.get('class', ''), **config)
                    for name, config in strategies_data['strategies'].items()
                }

            self._apply_legacy_risk_config(strategies_data)
            self._apply_legacy_execution_config(strategies_data)
            self._apply_legacy_backtesting_config(strategies_data)

        except Exception as e:
            print(f"Warning: Could not load strategies config: {e}")

    def _apply_legacy_risk_config(self, strategies_data: dict):
        """Apply global risk settings from strategies config"""
        if 'global_risk' not in strategies_data:
            return

        global_risk = strategies_data['global_risk']
        self.risk = RiskConfig(
            max_total_positions=global_risk.get('max_total_positions', self.risk.max_total_positions),
            max_daily_orders=global_risk.get('max_daily_orders', self.risk.max_daily_orders),
            max_portfolio_risk=global_risk.get('max_portfolio_risk', self.risk.max_portfolio_risk),
            emergency_stop_loss=global_risk.get('emergency_stop_loss', self.risk.emergency_stop_loss)
        )

    def _apply_legacy_execution_config(self, strategies_data: dict):
        """Apply execution settings from strategies config"""
        if 'execution' in strategies_data:
            exec_data = strategies_data['execution']
            self.execution = ExecutionConfig(**exec_data)

    def _apply_legacy_backtesting_config(self, strategies_data: dict):
        """Apply backtesting settings from strategies config"""
        if 'backtesting' in strategies_data:
            backtest_data = strategies_data['backtesting']
            self.backtesting = BacktestingConfig(**backtest_data)

    def _load_alpaca_config(self, config_dir: Path):
        """Load alpaca configuration file"""
        alpaca_file = config_dir / "alpaca_config.yaml"
        if not alpaca_file.exists():
            return

        try:
            with open(alpaca_file, 'r') as f:
                alpaca_data = yaml.safe_load(f)

            if 'trading' in alpaca_data:
                trading_data = alpaca_data['trading']
                self.trading = TradingConfig(**trading_data)

            if 'risk' in alpaca_data:
                risk_data = alpaca_data['risk']
                # Merge with existing risk config
                current_risk = self.risk.dict()
                current_risk.update(risk_data)
                self.risk = RiskConfig(**current_risk)

        except Exception as e:
            print(f"Warning: Could not load alpaca config: {e}")

    def _load_environment_overrides(self):
        """Load environment variable overrides"""
        # Database environment variables
        if os.getenv('DB_HOST'):
            self.database.host = os.getenv('DB_HOST')
        if os.getenv('DB_PORT'):
            self.database.port = int(os.getenv('DB_PORT'))
        if os.getenv('DB_NAME'):
            self.database.name = os.getenv('DB_NAME')
        if os.getenv('DB_USER'):
            self.database.user = os.getenv('DB_USER')
        if os.getenv('DB_PASSWORD'):
            self.database.password = os.getenv('DB_PASSWORD')

        # Alpaca environment variables
        if os.getenv('ALPACA_PAPER_API_KEY'):
            self.alpaca.paper_api_key = os.getenv('ALPACA_PAPER_API_KEY')
        if os.getenv('ALPACA_PAPER_SECRET_KEY'):
            self.alpaca.paper_secret_key = os.getenv('ALPACA_PAPER_SECRET_KEY')
        if os.getenv('ALPACA_LIVE_API_KEY'):
            self.alpaca.live_api_key = os.getenv('ALPACA_LIVE_API_KEY')
        if os.getenv('ALPACA_LIVE_SECRET_KEY'):
            self.alpaca.live_secret_key = os.getenv('ALPACA_LIVE_SECRET_KEY')

    def get_database_url(self) -> str:
        """Get database connection URL"""
        return (f"postgresql://{self.database.user}:{self.database.password}@"
                f"{self.database.host}:{self.database.port}/{self.database.name}")

    def get_alpaca_credentials(self) -> Dict[str, str]:
        """Get Alpaca credentials based on trading mode"""
        if self.trading.mode == "paper":
            return {
                "api_key": self.alpaca.paper_api_key,
                "secret_key": self.alpaca.paper_secret_key,
                "base_url": self.alpaca.paper_base_url
            }
        else:
            return {
                "api_key": self.alpaca.live_api_key,
                "secret_key": self.alpaca.live_secret_key,
                "base_url": self.alpaca.live_base_url
            }

    def get_enabled_strategies(self) -> Dict[str, StrategyConfig]:
        """Get only enabled strategies"""
        return {name: config for name, config in self.strategies.items() if config.enabled}

    def validate_configuration(self) -> List[str]:
        """Validate configuration and return list of issues"""
        issues = []

        # Check required database password
        if not self.database.password:
            issues.append("Database password is required")

        # Check Alpaca credentials for current mode
        creds = self.get_alpaca_credentials()
        if not creds["api_key"] or not creds["secret_key"]:
            issues.append(f"Alpaca credentials missing for {self.trading.mode} mode")

        # Validate strategy windows
        for name, strategy in self.strategies.items():
            if strategy.parameters.short_window and strategy.parameters.long_window:
                if strategy.parameters.short_window >= strategy.parameters.long_window:
                    issues.append(f"Strategy {name}: short_window must be less than long_window")

        return issues


# Global settings instance
_settings_instance = None


def get_settings() -> Settings:
    """
    Get global settings instance (singleton pattern).

    Returns:
        Settings instance with all configurations loaded and validated

    Example:
        >>> settings = get_settings()
        >>> db_config = settings.database
        >>> print(f"Database URL: {settings.get_database_url()}")
        Database URL: postgresql://postgres:admin123@localhost:5432/mltrading
    """
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance


def reload_settings() -> Settings:
    """
    Force reload settings from files and environment.

    Returns:
        Fresh settings instance
    """
    global _settings_instance
    _settings_instance = None
    return get_settings()


# Convenience functions for backward compatibility


def get_database_config() -> DatabaseConfig:
    """Get database configuration"""
    return get_settings().database


def get_trading_config() -> TradingConfig:
    """Get trading configuration"""
    return get_settings().trading


def get_risk_config() -> RiskConfig:
    """Get risk management configuration"""
    return get_settings().risk


if __name__ == "__main__":
    # Configuration validation script
    settings = get_settings()
    issues = settings.validate_configuration()

    if issues:
        print("Configuration Issues Found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✓ Configuration validation passed!")
        print(f"✓ Database: {settings.database.host}:{settings.database.port}")
        print(f"✓ Trading mode: {settings.trading.mode}")
        print(f"✓ Enabled strategies: {len(settings.get_enabled_strategies())}")
