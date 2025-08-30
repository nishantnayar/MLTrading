# Yahoo Finance Data Collection Deployment

Simple deployment that wraps the working `scripts/run_yahoo_collector.py` script.

## Files

- `yahoo_flow.py` - Prefect flow that wraps the working Yahoo collector
- `feature_engineering_flow.py` - Prefect flow that wraps the working feature engineering processor
- `prefect.yaml` - Deployment configuration for both flows
- `README.md` - This file

## Deploy

```bash
cd deployments
prefect deploy --all
```

## Test Locally

```bash
cd deployments

# Test Yahoo data collection
python yahoo_flow.py

# Test feature engineering
python feature_engineering_flow.py
```

## Run Deployments

```bash
# Run Yahoo data collection
prefect deployment run yahoo-finance-data-collection/yahoo-data-collection

# Run feature engineering
prefect deployment run feature-engineering/feature-engineering
```

## Monitor

```bash
prefect deployment ls
prefect flow-run ls --limit 5
```

These deployments use the proven working scripts and simply wrap them in Prefect flows for scheduling:

1. **Yahoo Data Collection** - Wraps `scripts/run_yahoo_collector.py`
2. **Feature Engineering** - Wraps `scripts/feature_engineering_processor.py`

Both use subprocess isolation and sequential processing for reliability.