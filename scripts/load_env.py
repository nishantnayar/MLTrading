"""
Environment variable loader for ML Trading System
"""

import os
from pathlib import Path
from dotenv import load_dotenv

def load_environment():
    """Load environment variables from .env file"""
    project_root = Path(__file__).parent.parent
    env_file = project_root / ".env"
    
    if env_file.exists():
        load_dotenv(env_file)
        print(f"✅ Loaded environment from {env_file}")
        return True
    else:
        env_example = project_root / "env.example"
        if env_example.exists():
            print(f"❌ .env file not found. Please copy {env_example} to .env and configure your settings")
        else:
            print("❌ No environment configuration found")
        return False

def get_database_url():
    """Get database connection URL from environment"""
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME', 'mltrading')
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', '')
    
    if not db_password:
        print("⚠️  Warning: DB_PASSWORD is not set")
    
    return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

if __name__ == "__main__":
    load_environment()
    print(f"Database URL: {get_database_url()}")