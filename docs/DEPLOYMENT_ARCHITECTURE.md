# ML Trading Deployment Architecture

## 🎯 **Three-Deployment Strategy**

### **1. Complete On-Demand Job (Initial Setup)**
**File**: `deployments/complete_data_and_features_ondemand.py`
- **Purpose**: Complete system initialization 
- **Data**: 1 year of historical data for ALL stocks
- **Features**: ALL 36 features (Phase 1+2) with initial run mode
- **Trigger**: Manual on-demand only
- **Runtime**: 25-45 minutes
- **Use Case**: First-time setup or complete data refresh

```bash
python deployments/complete_data_and_features_ondemand.py
```

### **2. Regular Yahoo Ingestion (Production)**  
**File**: `deployments/yahoo_production_deployment.py`
- **Purpose**: Regular optimized data collection
- **Data**: 3-day window (incremental updates)
- **Schedule**: Every hour during market hours (9 AM - 4 PM EST)
- **Runtime**: 5-10 minutes
- **Use Case**: Daily trading operations

```bash
python deployments/yahoo_production_deployment.py
```

### **3. Sequential Feature Engineering (Production)**
**File**: `deployments/feature_engineering_production_deployment.py`  
- **Purpose**: Calculate features on fresh data
- **Features**: 36 features (Phase 1+2) with incremental mode
- **Schedule**: 5 minutes after data collection (hourly)
- **Runtime**: <3 seconds for 100+ symbols
- **Use Case**: Real-time feature calculation

```bash
python deployments/feature_engineering_production_deployment.py
```

## 📊 **Production Flow**

```
9:00 AM → Yahoo Data Collection (3-day data)
9:05 AM → Feature Engineering (recent data)
10:00 AM → Yahoo Data Collection  
10:05 AM → Feature Engineering
...continues hourly...
```

## ✅ **Ready to Use**

All three deployments are configured and ready for production use!