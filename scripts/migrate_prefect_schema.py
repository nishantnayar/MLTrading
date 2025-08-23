#!/usr/bin/env python3
"""
Migrate Prefect tables from public schema to prefect schema
This ensures proper schema separation as designed
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import psycopg2

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment
load_dotenv()

def migrate_prefect_tables():
    """Move Prefect tables from public to prefect schema"""
    
    # Prefect table names (from a standard Prefect installation)
    prefect_tables = [
        'agent', 'artifact', 'artifact_collection', 'automation', 'automation_bucket',
        'automation_event_follower', 'automation_related_resource', 'block_document',
        'block_document_reference', 'block_schema', 'block_schema_reference', 'block_type',
        'composite_trigger_child_firing', 'concurrency_limit', 'concurrency_limit_v2',
        'configuration', 'csrf_token', 'deployment', 'deployment_schedule', 'deployment_version',
        'event_resources', 'events', 'flow', 'flow_run', 'flow_run_input', 'flow_run_state',
        'log', 'saved_search', 'task_run', 'task_run_state', 'task_run_state_cache',
        'variable', 'work_pool', 'work_queue', 'worker'
    ]
    
    # Database connection
    conn_params = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 5432)),
        'database': os.getenv('DB_NAME', 'mltrading'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD')
    }
    
    print("=== Prefect Schema Migration ===")
    print(f"Database: {conn_params['database']}")
    
    try:
        with psycopg2.connect(**conn_params) as conn:
            with conn.cursor() as cur:
                
                # Check which Prefect tables exist in public schema
                cur.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = ANY(%s)
                """, (prefect_tables,))
                
                existing_tables = [row[0] for row in cur.fetchall()]
                
                if not existing_tables:
                    print("No Prefect tables found in public schema - migration not needed")
                    return
                
                print(f"Found {len(existing_tables)} Prefect tables in public schema")
                
                # Ensure prefect schema exists
                cur.execute("CREATE SCHEMA IF NOT EXISTS prefect")
                print("Created/verified prefect schema")
                
                # Move each table to prefect schema
                for table in existing_tables:
                    try:
                        # Check if table already exists in prefect schema
                        cur.execute("""
                            SELECT EXISTS (
                                SELECT 1 FROM information_schema.tables 
                                WHERE table_schema = 'prefect' AND table_name = %s
                            )
                        """, (table,))
                        
                        if cur.fetchone()[0]:
                            print(f"Table {table} already exists in prefect schema, dropping from public")
                            cur.execute(f'DROP TABLE IF EXISTS public."{table}" CASCADE')
                        else:
                            print(f"Moving {table} to prefect schema...")
                            cur.execute(f'ALTER TABLE public."{table}" SET SCHEMA prefect')
                            
                    except Exception as e:
                        print(f"Warning: Could not migrate table {table}: {e}")
                        continue
                
                # Update alembic version table if it exists and belongs to Prefect
                try:
                    cur.execute("""
                        SELECT version_num FROM public.alembic_version 
                        WHERE version_num LIKE '%prefect%' OR version_num LIKE '%flow%'
                        LIMIT 1
                    """)
                    if cur.fetchone():
                        print("Moving alembic_version (Prefect) to prefect schema...")
                        cur.execute('ALTER TABLE public.alembic_version SET SCHEMA prefect')
                except:
                    pass  # Table might not exist or not be Prefect-related
                
                conn.commit()
                print("Migration completed successfully!")
                
    except Exception as e:
        print(f"Migration failed: {e}")
        return False
    
    return True

def verify_migration():
    """Verify the migration was successful"""
    
    conn_params = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 5432)),
        'database': os.getenv('DB_NAME', 'mltrading'),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD')
    }
    
    try:
        with psycopg2.connect(**conn_params) as conn:
            with conn.cursor() as cur:
                
                # Count tables in each schema
                cur.execute("""
                    SELECT 
                        'public' as schema_name,
                        COUNT(*) as table_count
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    UNION ALL
                    SELECT 
                        'prefect' as schema_name,
                        COUNT(*) as table_count
                    FROM information_schema.tables 
                    WHERE table_schema = 'prefect'
                """)
                
                results = cur.fetchall()
                print("\n=== Schema Verification ===")
                for schema_name, table_count in results:
                    print(f"{schema_name} schema: {table_count} tables")
                
                # List some key tables in prefect schema
                cur.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'prefect' 
                    AND table_name IN ('flow', 'flow_run', 'task_run', 'work_pool')
                    ORDER BY table_name
                """)
                
                prefect_key_tables = [row[0] for row in cur.fetchall()]
                if prefect_key_tables:
                    print(f"Key Prefect tables in prefect schema: {', '.join(prefect_key_tables)}")
                else:
                    print("No key Prefect tables found in prefect schema")
                
    except Exception as e:
        print(f"Verification failed: {e}")

if __name__ == "__main__":
    if migrate_prefect_tables():
        verify_migration()
        print("\nNext steps:")
        print("1. Restart any running Prefect servers")
        print("2. Run: prefect server start --host 0.0.0.0 --port 4200")
        print("3. Verify Prefect is using the prefect schema")