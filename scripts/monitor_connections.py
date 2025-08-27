#!/usr/bin/env python3
"""
Database Connection Monitor
Monitors PostgreSQL connections and provides diagnostics for connection issues
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.storage.database import DatabaseManager
from src.utils.connection_config import ConnectionConfig


def check_connection_status():
    """Check current connection status and limits"""
    print("PostgreSQL Connection Status")
    print("=" * 50)
    
    try:
        dm = DatabaseManager()
        
        with dm.get_connection_context() as conn:
            cur = conn.cursor()
            
            # Check max_connections setting
            cur.execute('SHOW max_connections;')
            max_conn = cur.fetchone()[0]
            print(f"PostgreSQL max_connections: {max_conn}")
            
            # Check current active connections
            cur.execute('SELECT count(*) FROM pg_stat_activity WHERE state = \'active\';')
            active_conn = cur.fetchone()[0]
            print(f"Current active connections: {active_conn}")
            
            # Check total connections
            cur.execute('SELECT count(*) FROM pg_stat_activity;')
            total_conn = cur.fetchone()[0]
            print(f"Total connections (active + idle): {total_conn}")
            
            # Check connections by database
            cur.execute("""
                SELECT datname, count(*) 
                FROM pg_stat_activity 
                WHERE datname IS NOT NULL 
                GROUP BY datname 
                ORDER BY count(*) DESC
            """)
            db_conns = cur.fetchall()
            print("\nConnections by database:")
            for db, count in db_conns:
                print(f"  {db}: {count}")
            
            # Check connections by application
            cur.execute("""
                SELECT COALESCE(application_name, 'Unknown'), count(*) 
                FROM pg_stat_activity 
                GROUP BY application_name 
                ORDER BY count(*) DESC
            """)
            app_conns = cur.fetchall()
            print("\nConnections by application:")
            for app, count in app_conns:
                print(f"  {app}: {count}")
            
            # Check connection states
            cur.execute("""
                SELECT state, count(*) 
                FROM pg_stat_activity 
                WHERE state IS NOT NULL 
                GROUP BY state 
                ORDER BY count(*) DESC
            """)
            state_conns = cur.fetchall()
            print("\nConnections by state:")
            for state, count in state_conns:
                print(f"  {state}: {count}")
                
            # Calculate utilization
            utilization = (total_conn / int(max_conn)) * 100
            print(f"\nConnection utilization: {utilization:.1f}% ({total_conn}/{max_conn})")
            
            if utilization > 80:
                print("⚠️  WARNING: High connection utilization!")
            elif utilization > 90:
                print("🚨 CRITICAL: Very high connection utilization!")
            else:
                print("✅ Connection utilization is healthy")
                
    except Exception as e:
        print(f"Error checking connection status: {e}")


def show_mltrading_config():
    """Show MLTrading connection configuration"""
    print("\nMLTrading Connection Configuration")
    print("=" * 50)
    
    ConnectionConfig.log_configuration()
    
    print(f"\nRecommended limits:")
    print(f"  Max concurrent processes: {ConnectionConfig.MAX_PROCESSES_EXPECTED}")
    print(f"  Connections per process: {ConnectionConfig.MAX_POOL_SIZE}")
    print(f"  Total MLTrading connections: {ConnectionConfig.MAX_PROCESSES_EXPECTED * ConnectionConfig.MAX_POOL_SIZE}")


def test_connection_creation():
    """Test creating multiple DatabaseManager instances"""
    print("\nConnection Creation Test")
    print("=" * 50)
    
    managers = []
    successful = 0
    
    try:
        for i in range(5):
            try:
                dm = DatabaseManager()
                
                # Test connection
                with dm.get_connection_context() as conn:
                    cur = conn.cursor()
                    cur.execute('SELECT 1')
                    result = cur.fetchone()[0]
                    
                managers.append(dm)
                successful += 1
                print(f"DatabaseManager {i+1}: ✅ SUCCESS")
                
            except Exception as e:
                print(f"DatabaseManager {i+1}: ❌ FAILED - {e}")
        
        print(f"\nSuccessfully created {successful}/5 DatabaseManager instances")
        
        if successful == 5:
            print("✅ Connection management is working correctly")
        else:
            print("⚠️  Some connection issues detected")
            
    finally:
        # Clean up
        for dm in managers:
            try:
                if dm.pool:
                    dm.pool.closeall()
            except:
                pass


def main():
    """Run connection monitoring"""
    print("Database Connection Monitor")
    print("MLTrading System")
    print("\n")
    
    # Show current connection status
    check_connection_status()
    
    # Show MLTrading configuration
    show_mltrading_config()
    
    # Test connection creation
    test_connection_creation()
    
    print("\n" + "=" * 50)
    print("Monitor complete")


if __name__ == "__main__":
    main()