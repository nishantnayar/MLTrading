#!/usr/bin/env python3
"""
Test database connection for ML Trading System
"""

import os
import sys
from pathlib import Path

# Add the project root to the path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
try:
    from scripts.load_env import load_environment
    load_environment()
except ImportError:
    print("Environment variables not loaded, using system variables")

def test_database_connection():
    """Test basic database connection"""
    try:
        from src.data.storage.database import get_db_manager
        
        print("Testing database connection...")
        db_manager = get_db_manager()
        
        # Test connection
        conn = db_manager.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                version = cur.fetchone()[0]
                print(f"SUCCESS: Connected to PostgreSQL")
                print(f"Version: {version}")
        finally:
            db_manager.return_connection(conn)
            
        # Test table access
        conn = db_manager.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    ORDER BY table_name;
                """)
                tables = [row[0] for row in cur.fetchall()]
                print(f"Found {len(tables)} tables in public schema: {tables}")
        finally:
            db_manager.return_connection(conn)
            
        return True
        
    except Exception as e:
        print(f"FAILED: Database connection error: {e}")
        print("\nPlease check:")
        print("1. PostgreSQL is running")
        print("2. Database 'mltrading' exists")
        print("3. Credentials in .env file are correct")
        print("4. Database server is accessible")
        return False

if __name__ == "__main__":
    print("=== Database Connection Test ===")
    print(f"DB_HOST: {os.getenv('DB_HOST', 'not set')}")
    print(f"DB_PORT: {os.getenv('DB_PORT', 'not set')}")
    print(f"DB_NAME: {os.getenv('DB_NAME', 'not set')}")
    print(f"DB_USER: {os.getenv('DB_USER', 'not set')}")
    print(f"DB_PASSWORD: {'***' if os.getenv('DB_PASSWORD') else 'not set'}")
    print()
    
    success = test_database_connection()
    sys.exit(0 if success else 1)