#!/usr/bin/env python3
"""
Create Prefect work pools after server is running
"""

import subprocess
import sys
from typing import List, Dict

def create_work_pools() -> bool:
    """Create Prefect work pools for different workflow types"""
    print("Creating Prefect work pools...")
    
    work_pools = [
        {
            'name': 'ml-trading-pool',
            'type': 'process',
            'description': 'Main work pool for ML trading workflows'
        },
        {
            'name': 'data-collection-pool',
            'type': 'process', 
            'description': 'Work pool for data collection workflows'
        },
        {
            'name': 'signal-generation-pool',
            'type': 'process',
            'description': 'Work pool for signal generation workflows'
        },
        {
            'name': 'risk-management-pool',
            'type': 'process',
            'description': 'Work pool for risk management workflows'
        }
    ]
    
    success_count = 0
    
    for pool in work_pools:
        try:
            print(f"Creating work pool: {pool['name']}")
            
            # Create work pool using Prefect CLI
            cmd = [
                'prefect', 'work-pool', 'create',
                pool['name'],
                '--type', pool['type']
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ Created work pool: {pool['name']}")
                success_count += 1
            else:
                # Work pool might already exist
                if 'already exists' in result.stderr:
                    print(f"ℹ️  Work pool already exists: {pool['name']}")
                    success_count += 1
                else:
                    print(f"❌ Failed to create work pool {pool['name']}: {result.stderr}")
                    
        except Exception as e:
            print(f"❌ Error creating work pool {pool['name']}: {e}")
    
    print(f"\nWork pool creation summary: {success_count}/{len(work_pools)} successful")
    return success_count == len(work_pools)

def check_server_status() -> bool:
    """Check if Prefect server is running"""
    try:
        result = subprocess.run(['prefect', 'server', 'status'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Prefect server is running")
            return True
        else:
            print("❌ Prefect server is not running")
            print("Please start the server first: prefect server start --host 0.0.0.0 --port 4200")
            return False
    except Exception as e:
        print(f"❌ Error checking server status: {e}")
        return False

def main():
    """Main function"""
    print("=== Prefect Work Pool Setup ===")
    
    # Check if server is running
    if not check_server_status():
        return False
    
    # Create work pools
    if create_work_pools():
        print("\n=== Work Pool Setup Complete ===")
        print("Next steps:")
        print("1. Start worker: prefect worker start --pool ml-trading-pool")
        print("2. Access UI: http://localhost:4200")
        print("3. Deploy workflows as needed")
        return True
    else:
        print("\n❌ Work pool setup failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)