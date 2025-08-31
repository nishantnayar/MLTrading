# API Reference

Complete developer reference for the ML Trading System with interactive examples and source code.

## Core Data Pipeline

### Market Data Collection
::: data.collectors.yahoo_collector
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3

### Feature Engineering
::: data.processors.feature_engineering
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3

### Database Operations
::: data.storage.database
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3

## Dashboard & Analytics

### Unified Data Service
::: dashboard.services.unified_data_service
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3

### Feature Data Access
::: dashboard.services.feature_data_service
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3

### Market Data Access
::: dashboard.services.market_data_service
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3

## Trading Operations

### Alpaca Broker Integration
::: trading.brokers.alpaca_service
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3

## System Configuration

### Logging System
::: utils.logging_config
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3

### Database Configuration
::: utils.connection_config
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3

### Production Logging
::: utils.production_logging
    options:
      show_root_heading: true
      show_source: true
      heading_level: 3

## Development Notes

This API documentation is automatically generated from Python docstrings using mkdocstrings. 

**Key Features:**
- Live source code links
- Interactive examples
- Type hint integration
- Google-style docstring support
- Cross-references between modules