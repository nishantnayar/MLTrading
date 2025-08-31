# 🔧 Database Connection Troubleshooting Guide

## Common Database Issues & Solutions

### 1. **"fe_sendauth: no password supplied"**

**Problem:** PostgreSQL requires authentication but no password provided.

**Solutions:**

#### **Option A: Configure Password**
1. **Check if .env file exists:**
   ```bash
   ls -la .env
   ```

2. **Create .env from template:**
   ```bash
   copy .env.example .env  # Windows
   cp .env.example .env    # Linux/Mac
   ```

3. **Edit .env file and set your PostgreSQL password:**
   ```bash
   DB_PASSWORD=your_actual_password
   DATABASE_URL=postgresql://postgres:your_actual_password@localhost:5432/mltrading
   ```

#### **Option B: Allow Local Connections (Development Only)**
1. **Find PostgreSQL config file:**
   ```bash
   # Windows
   C:\Program Files\PostgreSQL\15\data\pg_hba.conf
   
   # Linux
   /etc/postgresql/15/main/pg_hba.conf
   
   # Mac
   /usr/local/var/postgresql@15/pg_hba.conf
   ```

2. **Edit pg_hba.conf:**
   ```bash
   # Change authentication method for local connections:
   local   all             all                     trust
   host    all             all     127.0.0.1/32    trust
   host    all             all     ::1/128         trust
   ```

3. **Restart PostgreSQL:**
   ```bash
   # Windows (as Administrator)
   net stop postgresql-x64-15
   net start postgresql-x64-15
   
   # Linux
   sudo systemctl restart postgresql
   
   # Mac
   brew services restart postgresql@15
   ```

### 2. **"connection to server failed"**

**Problem:** PostgreSQL server not running or wrong connection parameters.

**Solutions:**

#### **Check PostgreSQL Status**
```bash
# Windows
sc query postgresql-x64-15

# Linux
sudo systemctl status postgresql

# Mac
brew services list | grep postgresql
```

#### **Start PostgreSQL**
```bash
# Windows (as Administrator)
net start postgresql-x64-15

# Linux
sudo systemctl start postgresql

# Mac
brew services start postgresql@15
```

#### **Verify Connection Parameters**
```bash
# Test connection manually
psql -h localhost -p 5432 -U postgres -d mltrading

# Check if database exists
psql -U postgres -l | grep mltrading
```

### 3. **"database does not exist"**

**Problem:** The mltrading database hasn't been created.

**Solutions:**

#### **Create Database**
```bash
# Connect as postgres user
psql -U postgres

# Create database
CREATE DATABASE mltrading;

# Grant permissions
GRANT ALL PRIVILEGES ON DATABASE mltrading TO postgres;

# Exit
\q
```

#### **Verify Database Creation**
```bash
psql -U postgres -d mltrading -c "SELECT version();"
```

### 4. **"permission denied"**

**Problem:** User doesn't have permissions on database/tables.

**Solutions:**

#### **Grant Permissions**
```sql
-- Connect as superuser
psql -U postgres -d mltrading

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE mltrading TO postgres;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;
```

### 5. **"table does not exist"**

**Problem:** feature_engineered_data table hasn't been created.

**Solutions:**

#### **Create Table**
```bash
# Run table creation script
psql -U postgres -d mltrading -f src/data/storage/create_feature_engineered_data.sql
```

#### **Verify Table Exists**
```bash
psql -U postgres -d mltrading -c "\dt feature_engineered_data"
```

## 🚀 **Quick Database Setup (Complete)**

If you're starting fresh, here's the complete setup:

### **1. Install PostgreSQL**
```bash
# Windows: Download from postgresql.org
# Linux: sudo apt-get install postgresql postgresql-contrib
# Mac: brew install postgresql@15
```

### **2. Create Database & User**
```bash
# Start PostgreSQL service
sudo systemctl start postgresql  # Linux
brew services start postgresql@15  # Mac

# Create database
createdb -U postgres mltrading

# Test connection
psql -U postgres -d mltrading
```

### **3. Configure Environment**
```bash
# Copy environment template
cp .env.example .env

# Edit .env file
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mltrading
DB_USER=postgres
DB_PASSWORD=your_password_here
```

### **4. Create Tables**
```bash
# Create feature table
psql -U postgres -d mltrading -f src/data/storage/create_feature_engineered_data.sql
```

### **5. Apply Optimizations**
```bash
# Apply database optimizations
psql -U postgres -d mltrading -f scripts/apply_feature_optimization.sql
```

## 🔍 **Diagnostic Commands**

### **Test Database Connection**
```bash
# Test with Python script
python -c "
from src.data.storage.database import DatabaseManager
db = DatabaseManager()
with db.get_connection_context() as conn:
    with conn.cursor() as cur:
        cur.execute('SELECT version()')
        print('✅ Connection successful:', cur.fetchone()[0])
"
```

### **Check Table Status**
```sql
-- Connect to database
psql -U postgres -d mltrading

-- Check if tables exist
\dt

-- Check feature table structure
\d feature_engineered_data

-- Check row count
SELECT COUNT(*) FROM feature_engineered_data;

-- Check indexes
\di feature_engineered_data

-- Check table size
SELECT pg_size_pretty(pg_total_relation_size('feature_engineered_data'));
```

### **Performance Test Queries**
```sql
-- Test optimized query performance
EXPLAIN ANALYZE 
SELECT symbol, timestamp, close, rsi_1d 
FROM feature_engineered_data 
WHERE symbol = 'AAPL' 
AND timestamp >= NOW() - INTERVAL '30 days'
ORDER BY timestamp DESC 
LIMIT 100;

-- Check index usage
SELECT 
    schemaname,
    tablename,
    indexrelname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes 
WHERE tablename = 'feature_engineered_data'
ORDER BY idx_scan DESC;
```

## ⚡ **Alternative: Bypass Database Issues**

If you can't resolve the connection issues immediately:

### **1. Use Direct SQL Scripts**
```bash
# Apply optimizations directly
psql -U postgres -d mltrading -f scripts/apply_feature_optimization.sql

# Create materialized view refresh script
psql -U postgres -d mltrading -c "REFRESH MATERIALIZED VIEW mv_features_dashboard_summary;"
```

### **2. Use SQLite for Development**
Consider switching to SQLite for local development:

```python
# Quick SQLite alternative
import sqlite3
conn = sqlite3.connect('mltrading.db')
# Run your queries here
```

## 📞 **Getting Help**

### **Log Analysis**
```bash
# Check PostgreSQL logs
# Windows: C:\Program Files\PostgreSQL\15\data\log\
# Linux: /var/log/postgresql/
# Mac: /usr/local/var/log/postgresql@15.log

tail -f /var/log/postgresql/postgresql-15-main.log
```

### **Connection String Debug**
```python
# Debug connection parameters
from src.data.storage.database import DatabaseManager
db = DatabaseManager()
print("Connection params:", db.get_connection_params())
```

### **Environment Variable Check**
```bash
# Check environment variables
printenv | grep DB_
printenv | grep DATABASE_URL
```

---

**Quick Resolution Priority:**
1. ✅ Set DB_PASSWORD in .env file
2. ✅ Use standalone SQL script: `scripts/apply_feature_optimization.sql`  
3. ✅ Test with: `python run.py optimize-db --dry-run`
4. ✅ Apply with: `python run.py optimize-db` (once connection works)