"""
Configuration Migration Utility

Helps migrate from legacy configuration files to the unified settings system.
Provides validation and compatibility checking.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, List
try:
    from .settings import get_settings, Settings
except ImportError:
    # Handle running as script
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent.parent))
    from src.config.settings import get_settings, Settings


def validate_legacy_configs() -> Dict[str, Any]:
    """
    Validate existing configuration files and environment variables.
    
    Returns:
        Dictionary with validation results and migration recommendations
    """
    results = {
        'config_files': {},
        'environment_vars': {},
        'migration_needed': [],
        'status': 'success'
    }
    
    config_dir = Path("config")
    
    # Check config files
    config_files = [
        'alpaca_config.yaml',
        'deployments_config.yaml', 
        'strategies_config.yaml'
    ]
    
    for config_file in config_files:
        file_path = config_dir / config_file
        if file_path.exists():
            try:
                with open(file_path, 'r') as f:
                    data = yaml.safe_load(f)
                results['config_files'][config_file] = {
                    'status': 'valid',
                    'keys': list(data.keys()) if data else [],
                    'size_kb': file_path.stat().st_size / 1024
                }
            except Exception as e:
                results['config_files'][config_file] = {
                    'status': 'error',
                    'error': str(e)
                }
        else:
            results['config_files'][config_file] = {'status': 'missing'}
    
    # Check environment variables
    env_vars = [
        'DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER', 'DB_PASSWORD',
        'ALPACA_PAPER_API_KEY', 'ALPACA_PAPER_SECRET_KEY',
        'PREFECT_API_URL', 'ENVIRONMENT'
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        results['environment_vars'][var] = {
            'present': value is not None,
            'masked_value': f"{value[:4]}***" if value and len(value) > 4 else "***" if value else None
        }
    
    return results


def test_unified_config() -> Dict[str, Any]:
    """
    Test the unified configuration system.
    
    Returns:
        Test results and configuration status
    """
    results = {
        'unified_config': {},
        'backward_compatibility': {},
        'recommendations': [],
        'status': 'success'
    }
    
    try:
        # Test unified settings
        settings = get_settings()
        results['unified_config'] = {
            'loaded': True,
            'database_configured': bool(settings.database.password),
            'trading_mode': settings.trading.mode,
            'strategies_count': len(settings.strategies),
            'deployments_count': len(settings.deployments)
        }
        
        # Test configuration validation
        issues = settings.validate_configuration()
        results['unified_config']['validation_issues'] = len(issues)
        
        # Test backward compatibility
        try:
            from src.utils.connection_config import get_safe_db_config
            legacy_config = get_safe_db_config()
            results['backward_compatibility']['legacy_config_works'] = True
            results['backward_compatibility']['matches_unified'] = (
                legacy_config['host'] == settings.database.host and
                legacy_config['port'] == settings.database.port
            )
        except Exception as e:
            results['backward_compatibility']['legacy_config_works'] = False
            results['backward_compatibility']['error'] = str(e)
        
        # Generate recommendations
        if not settings.database.password:
            results['recommendations'].append("Set DB_PASSWORD environment variable")
        
        if len(settings.strategies) == 0:
            results['recommendations'].append("No strategies configured - check strategies_config.yaml")
            
        if settings.trading.mode == "live" and not settings.alpaca.live_api_key:
            results['recommendations'].append("Live trading mode requires Alpaca live API credentials")
    
    except Exception as e:
        results['status'] = 'error'
        results['error'] = str(e)
    
    return results


def generate_migration_report() -> str:
    """
    Generate a comprehensive migration report.
    
    Returns:
        Formatted migration report as string
    """
    legacy_results = validate_legacy_configs()
    unified_results = test_unified_config()
    
    report = []
    report.append("# Configuration Migration Report")
    report.append("=" * 50)
    report.append("")
    
    # Legacy configuration status
    report.append("## Legacy Configuration Files")
    for file_name, info in legacy_results['config_files'].items():
        status = info['status']
        if status == 'valid':
            report.append(f"[PASS] {file_name}: {len(info['keys'])} sections, {info['size_kb']:.1f}KB")
        elif status == 'missing':
            report.append(f"[WARN] {file_name}: Not found")
        else:
            report.append(f"[FAIL] {file_name}: Error - {info.get('error', 'Unknown')}")
    
    report.append("")
    
    # Environment variables status
    report.append("## Environment Variables")
    for var, info in legacy_results['environment_vars'].items():
        status = "[PASS]" if info['present'] else "[WARN]"
        value = info['masked_value'] or "Not set"
        report.append(f"{status} {var}: {value}")
    
    report.append("")
    
    # Unified configuration status
    report.append("## Unified Configuration System")
    if unified_results['status'] == 'success':
        unified = unified_results['unified_config']
        report.append(f"[PASS] System loaded successfully")
        report.append(f"[PASS] Database configured: {unified['database_configured']}")
        report.append(f"[PASS] Trading mode: {unified['trading_mode']}")
        report.append(f"[PASS] Strategies loaded: {unified['strategies_count']}")
        report.append(f"[PASS] Deployments loaded: {unified['deployments_count']}")
        
        if unified['validation_issues'] > 0:
            report.append(f"[WARN] Validation issues: {unified['validation_issues']}")
    else:
        report.append(f"[FAIL] System failed to load: {unified_results.get('error', 'Unknown error')}")
    
    report.append("")
    
    # Backward compatibility
    report.append("## Backward Compatibility")
    compat = unified_results.get('backward_compatibility', {})
    if compat.get('legacy_config_works'):
        report.append("[PASS] Legacy configuration system still works")
        if compat.get('matches_unified'):
            report.append("[PASS] Legacy and unified configurations match")
        else:
            report.append("[WARN] Legacy and unified configurations differ")
    else:
        report.append("[WARN] Legacy configuration system has issues")
    
    report.append("")
    
    # Recommendations
    recommendations = unified_results.get('recommendations', [])
    if recommendations:
        report.append("## Recommendations")
        for rec in recommendations:
            report.append(f"- {rec}")
    else:
        report.append("## Status: Configuration Ready!")
        report.append("No immediate actions required.")
    
    return "\n".join(report)


if __name__ == "__main__":
    # Run migration analysis
    print("Running configuration migration analysis...")
    print()
    
    report = generate_migration_report()
    print(report)
    
    # Save report to file
    report_file = Path("logs") / "config_migration_report.md"
    report_file.parent.mkdir(exist_ok=True)
    
    with open(report_file, 'w') as f:
        f.write(report)
    
    print(f"\nReport saved to: {report_file}")