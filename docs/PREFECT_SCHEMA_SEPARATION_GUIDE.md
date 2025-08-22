# 🔄 Prefect 3.x Schema Separation Implementation Guide

## 📋 **Overview**

This guide documents the implementation of Prefect 3.x workflow orchestration using PostgreSQL schema separation. The approach maintains clean separation between application data (`public` schema) and workflow orchestration data (`prefect` schema) while enabling cross-schema integration when needed.

---

## 🏗️ **Architecture Overview**

### **Database Schema Structure**
```
mltrading (PostgreSQL Database)
├── public schema (Application Data)
│   ├── market_data
│   ├── stock_info
│   ├── system_logs
│   ├── trading_signals (future)
│   ├── orders (future)
│   └── portfolios (future)
└── prefect schema (Workflow Orchestration)
    ├── flow_run
    ├── task_run
    ├── deployment
    ├── work_queue
    ├── flow
    └── task_run_state
```

### **Benefits of Schema Separation**

| Benefit | Description | Impact |
|---------|-------------|--------|
| **Clean Separation** | Application and workflow data isolated | Better organization, easier maintenance |
| **Security** | Different access patterns for different data types | Enhanced security model |
| **Performance** | Independent indexing and optimization | Better query performance |
| **Backup Strategy** | Schema-specific backup and recovery | More flexible data management |
| **Development** | Clear boundaries between application and orchestration | Cleaner architecture |

---

## 🛠️ **Implementation Components**

### **1. Database Schema Setup**
**File:** `src/data/storage/create_prefect_schema.sql`

```sql
-- Create dedicated schema for Prefect
CREATE SCHEMA IF NOT EXISTS prefect;

-- Grant permissions to application user
GRANT USAGE ON SCHEMA prefect TO your_app_user;
GRANT CREATE ON SCHEMA prefect TO your_app_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA prefect TO your_app_user;

-- Set search path to include both schemas
ALTER DATABASE mltrading SET search_path = public, prefect;
```

### **2. Configuration Management**
**File:** `config/prefect_config.yaml`

```yaml
database:
  connection_url: "postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}"
  schema: "prefect"
  
server:
  database:
    connection_url: "postgresql://user:pass@host:port/mltrading?options=-csearch_path%3Dprefect"
```

### **3. Database Integration Layer**
**File:** `src/utils/prefect_database_integration.py`

Key components:
- **PrefectDatabaseManager**: Manages connections to both schemas
- **Schema verification**: Ensures proper setup
- **Cross-schema logging**: Integrates workflow events with application logs
- **Health checks**: Monitors both schema connections

---

## 🔧 **Setup Instructions**

### **Prerequisites**
- PostgreSQL database (existing ML Trading database)
- Python 3.8+
- Prefect 3.x installed (`pip install prefect`)
- Environment variables configured

### **Step 1: Environment Setup**
1. Copy `env.example` to `.env`
2. Update database credentials
3. Set Prefect-specific variables:
```bash
# Database connection URL for Prefect (with schema separation)
PREFECT_API_DATABASE_CONNECTION_URL=postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}?options=-csearch_path%3Dprefect
```

### **Step 2: Database Schema Creation**
```bash
# Run SQL script to create Prefect schema
psql -d mltrading -f src/data/storage/create_prefect_schema.sql
```

### **Step 3: Automated Setup**
```bash
# Run the automated setup script
python scripts/setup_prefect.py
```

This script will:
- ✅ Check prerequisites
- ✅ Initialize database schema
- ✅ Configure Prefect server
- ✅ Create work pools
- ✅ Deploy example workflows

### **Step 4: Start Prefect Server**
```bash
# Start Prefect server with PostgreSQL backend
prefect server start --host 0.0.0.0 --port 4200
```

### **Step 5: Start Workers**
```bash
# Start worker for processing workflows
prefect worker start --pool ml-trading-pool
```

---

## 🔄 **Workflow Integration**

### **Cross-Schema Data Access**

#### **From Workflow to Application Data**
```python
from src.data.storage.database import get_db_manager
from src.utils.prefect_database_integration import get_prefect_db_manager

@task
def process_market_data_task():
    # Access application data (public schema)
    app_db = get_db_manager()
    with app_db.get_connection() as conn:
        market_data = conn.execute("SELECT * FROM market_data LIMIT 10")
    
    # Log workflow event (integrates with application logging)
    prefect_db = get_prefect_db_manager()
    prefect_db.log_workflow_event(
        event_type='data_processing',
        workflow_name='market_analysis',
        status='success',
        metadata={'records_processed': len(market_data)}
    )
```

#### **Application Access to Workflow Data**
```python
# From application code, access workflow status
prefect_db = get_prefect_db_manager()
with prefect_db.prefect_session() as session:
    # Query Prefect schema for workflow status
    recent_runs = session.execute("""
        SELECT name, state_type, start_time 
        FROM flow_run 
        WHERE start_time >= NOW() - INTERVAL '1 hour'
    """).fetchall()
```

### **Logging Integration**

The system maintains unified logging across schemas:

```python
# Workflow events are logged to application system_logs table
prefect_db.log_workflow_event(
    event_type='batch_collection',
    workflow_name='data_collection', 
    status='success',
    metadata={
        'symbols_processed': 100,
        'records_collected': 5000,
        'processing_time': 45.2
    }
)
```

---

## 📊 **Monitoring & Operations**

### **Health Checks**
```python
# Comprehensive health check for both schemas
prefect_db = get_prefect_db_manager()
health_status = prefect_db.health_check()

# Returns:
{
    'overall_status': 'healthy',
    'checks': {
        'app_database': 'healthy',
        'prefect_schema': 'healthy', 
        'schema_separation': 'healthy'
    }
}
```

### **Schema Verification**
```python
# Verify schema setup and separation
verification = prefect_db.verify_schema_separation()

# Returns detailed information about both schemas
{
    'public_schema': {'exists': True, 'tables': ['market_data', 'stock_info', ...]},
    'prefect_schema': {'exists': True, 'tables': ['flow_run', 'task_run', ...]},
    'connection_test': True,
    'search_path': 'public, prefect'
}
```

### **Performance Monitoring**
```python
# Get workflow execution statistics
stats = prefect_db.get_workflow_statistics()

# Returns performance metrics
{
    'total_flows': 245,
    'successful_runs': 230,
    'failed_runs': 15,
    'average_duration': 127.5,
    'recent_activity': [...]
}
```

---

## 🔧 **Maintenance Operations**

### **Data Cleanup**
```python
# Clean old workflow execution data
cleanup_results = prefect_db.cleanup_old_workflow_data(days_to_keep=30)

# Returns cleanup statistics
{
    'flow_runs_deleted': 150,
    'task_runs_deleted': 1200,
    'logs_deleted': 500
}
```

### **Backup Strategy**

#### **Schema-Specific Backups**
```bash
# Backup application data only (public schema)
pg_dump -h localhost -U postgres -n public mltrading > mltrading_app_backup.sql

# Backup workflow data only (prefect schema)  
pg_dump -h localhost -U postgres -n prefect mltrading > mltrading_workflow_backup.sql

# Full database backup
pg_dump -h localhost -U postgres mltrading > mltrading_full_backup.sql
```

#### **Restoration**
```bash
# Restore application data
psql -h localhost -U postgres -d mltrading < mltrading_app_backup.sql

# Restore workflow data
psql -h localhost -U postgres -d mltrading < mltrading_workflow_backup.sql
```

---

## 🎯 **Best Practices**

### **1. Connection Management**
- **Reuse application connection pools** for cost efficiency
- **Use schema-specific connections** for Prefect operations
- **Monitor connection usage** to prevent pool exhaustion

### **2. Data Access Patterns**
- **Application data**: Use existing `DatabaseManager`
- **Workflow data**: Use `PrefectDatabaseManager`
- **Cross-schema queries**: Use search path configuration

### **3. Security**
- **Schema-level permissions**: Grant minimal required access
- **Connection string security**: Use environment variables
- **Audit trail**: Maintain logs for both schemas

### **4. Performance Optimization**
- **Index strategy**: Independent indexing per schema
- **Query optimization**: Schema-specific query plans
- **Connection pooling**: Shared pools with schema routing

---

## 🚨 **Troubleshooting**

### **Common Issues**

#### **1. Schema Not Found**
```
ERROR: schema "prefect" does not exist
```
**Solution:**
```bash
# Run schema creation script
psql -d mltrading -f src/data/storage/create_prefect_schema.sql
```

#### **2. Permission Denied**
```
ERROR: permission denied for schema prefect
```
**Solution:**
```sql
GRANT USAGE ON SCHEMA prefect TO your_app_user;
GRANT CREATE ON SCHEMA prefect TO your_app_user;
```

#### **3. Connection String Issues**
```
ERROR: could not connect to server
```
**Solution:**
- Verify environment variables
- Check connection string format
- Ensure PostgreSQL is running

#### **4. Search Path Issues**
```
ERROR: relation "flow_run" does not exist
```
**Solution:**
```sql
-- Set search path to include prefect schema
SET search_path TO public, prefect;
-- Or use fully qualified table names
SELECT * FROM prefect.flow_run;
```

### **Diagnostic Commands**
```python
# Check schema separation setup
from src.utils.prefect_database_integration import get_prefect_db_manager

prefect_db = get_prefect_db_manager()

# Verify schemas exist
verification = prefect_db.verify_schema_separation()
print("Verification:", verification)

# Test health
health = prefect_db.health_check()
print("Health:", health)

# Check connection
try:
    with prefect_db.prefect_session() as session:
        result = session.execute("SELECT 1").scalar()
        print("Prefect connection: OK")
except Exception as e:
    print(f"Prefect connection failed: {e}")
```

---

## 📈 **Migration Strategy**

### **From No Orchestration to Prefect**
1. **Phase 1**: Set up schema separation
2. **Phase 2**: Migrate Yahoo collector to Prefect tasks
3. **Phase 3**: Add signal generation workflows
4. **Phase 4**: Implement risk management workflows

### **From SQLite to PostgreSQL Schema**
If migrating from Prefect's default SQLite:
1. Export existing flow definitions
2. Set up PostgreSQL schema
3. Recreate deployments with new database
4. Migrate execution history if needed

---

## 🔮 **Future Enhancements**

### **Planned Features**
- **Multi-tenant support**: Additional schemas for different trading accounts
- **Advanced monitoring**: Real-time workflow dashboards
- **Auto-scaling**: Dynamic worker pool management
- **Disaster recovery**: Cross-region schema replication

### **Integration Roadmap**
- **MLflow integration**: Model training workflows
- **Real-time streaming**: Event-driven workflow triggers  
- **Advanced analytics**: Workflow performance optimization
- **Cloud deployment**: Kubernetes orchestration

---

## 📚 **Resources**

### **Configuration Files**
- `config/prefect_config.yaml`: Main Prefect configuration
- `src/data/storage/create_prefect_schema.sql`: Database schema setup
- `env.example`: Environment variable template
- `scripts/setup_prefect.py`: Automated setup script

### **Integration Modules**  
- `src/utils/prefect_database_integration.py`: Database integration layer
- `src/workflows/data_pipeline/data_collection_flows.py`: Example workflows
- `src/data/storage/database.py`: Application database manager

### **Documentation**
- [Prefect 3.x Documentation](https://docs.prefect.io)
- [PostgreSQL Schema Documentation](https://www.postgresql.org/docs/current/ddl-schemas.html)
- ML Trading System Architecture Guide

---

**The schema separation approach provides a robust foundation for workflow orchestration while maintaining clean architecture and operational simplicity.**