# API Reference

Detailed API documentation for all MLTrading modules, classes, and functions.

## Overview

The MLTrading API is organized into several key modules:

- **Data Layer**: Data collection, processing, and storage
- **Dashboard Services**: Web interface and data services  
- **Trading Components**: Broker integration and trading logic
- **Utilities**: Logging, configuration, and helper functions

## Auto-Generated API Documentation

For detailed API reference with automatic documentation from docstrings, visit the **[Sphinx API Documentation](../../api-docs/_build/html/index.html)**.

The Sphinx documentation includes:

- **Class and method signatures**
- **Parameter descriptions** 
- **Return value documentation**
- **Example usage**
- **Inheritance hierarchies**
- **Source code links**

## Key Modules

### Data Collection
- `src.data.collectors.yahoo_collector` - Yahoo Finance data collection
- `src.data.processors.feature_engineering` - ML feature generation
- `src.data.storage.database` - Database management

### Dashboard Services  
- `src.dashboard.services.market_data_service` - Market data access
- `src.dashboard.services.feature_data_service` - Feature data access
- `src.dashboard.services.unified_data_service` - Combined data services

### Trading Integration
- `src.trading.brokers.alpaca_service` - Alpaca broker integration

### Utilities
- `src.utils.logging_config` - Logging configuration
- `src.utils.connection_config` - Database connection settings

## Development

For development and contributing to the API:

1. **Install development dependencies**:
   ```bash
   pip install -r requirements-dev.txt
   ```

2. **Run tests**:
   ```bash
   python -m pytest tests/
   ```

3. **Generate API docs**:
   ```bash
   cd api-docs
   sphinx-build -b html . _build/html
   ```

4. **Follow coding standards**:
   - Use type hints
   - Write docstrings in Google format
   - Include examples in docstrings
   - Add unit tests for new functions

## API Design Principles

- **Separation of concerns**: Each module has a single responsibility
- **Dependency injection**: Services are injected rather than hardcoded
- **Error handling**: Comprehensive exception handling with logging
- **Type safety**: Full type hints for better IDE support
- **Caching**: Intelligent caching for performance optimization