#!/usr/bin/env python3
"""
Feature Engineering Processor - Final implementation
Processes all symbols with proper connection management
"""

import os
import sys
import time
import subprocess
from pathlib import Path
from typing import List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.data.storage.database import get_db_manager


def get_remaining_symbols() -> List[str]:
    """Get symbols that need feature engineering."""
    db_manager = get_db_manager()

    try:
        conn = db_manager.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT DISTINCT md.symbol
                    FROM market_data md
                    LEFT JOIN feature_engineered_data fed ON md.symbol = fed.symbol
                    WHERE fed.symbol IS NULL
                    ORDER BY md.symbol
                """)
                symbols = [row[0] for row in cursor.fetchall()]
                return symbols
        finally:
            db_manager.return_connection(conn)
    except Exception as e:
        print(f"Error getting symbols: {e}")
        return []

def process_single_symbol_subprocess(symbol: str) -> bool:
    """Process a single symbol using subprocess isolation."""
    
    script_content = f'''
import os
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.data.processors.feature_engineering import FeatureEngineerPhase1And2

try:
    engineer = FeatureEngineerPhase1And2()
    success = engineer.process_symbol_phase1_and_phase2("{symbol}", initial_run=True)
    print("SUCCESS" if success else "FAILED")
    sys.exit(0 if success else 1)
except Exception as e:
    print(f"ERROR: {{e}}")
    sys.exit(1)
'''
    
    # Write temporary script
    temp_script = project_root / f"temp_process_{symbol}.py"
    
    try:
        with open(temp_script, 'w') as f:
            f.write(script_content)
        
        # Run subprocess with timeout
        result = subprocess.run(
            [sys.executable, str(temp_script)],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(project_root)
        )
        
        success = result.returncode == 0 and "SUCCESS" in result.stdout
        
        return success
        
    except subprocess.TimeoutExpired:
        print(f"TIMEOUT")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False
    finally:
        # Clean up temp script
        try:
            if temp_script.exists():
                temp_script.unlink()
        except:
            pass

def main():
    """Process all symbols using subprocess isolation."""
    
    print("FEATURE ENGINEERING PROCESSOR")
    print("Using subprocess isolation for complete connection management")
    print("="*70)
    
    # Get remaining symbols
    symbols = get_remaining_symbols()
    
    if not symbols:
        print("All symbols already processed!")
        return
    
    total = len(symbols)
    print(f"Found {total} symbols to process")
    print()
    
    # Process each symbol
    start_time = time.time()
    successful = 0
    failed = 0
    failed_symbols = []
    
    for i, symbol in enumerate(symbols, 1):
        print(f"[{i:4d}/{total}] {symbol:6s} ... ", end="", flush=True)
        
        symbol_start = time.time()
        success = process_single_symbol_subprocess(symbol)
        symbol_time = time.time() - symbol_start
        
        if success:
            print(f"SUCCESS ({symbol_time:.1f}s)")
            successful += 1
        else:
            print(f"FAILED  ({symbol_time:.1f}s)")
            failed += 1
            failed_symbols.append(symbol)
        
        # Progress every 25 symbols
        if i % 25 == 0:
            elapsed = time.time() - start_time
            rate = i / elapsed if elapsed > 0 else 0
            remaining_time = (total - i) / rate if rate > 0 else 0
            
            print(f"    Progress: {i}/{total} | "
                  f"Success: {successful} | Failed: {failed} | "
                  f"Rate: {rate:.1f}/min | ETA: {remaining_time/60:.1f}m")
            print()
    
    # Final results
    total_time = time.time() - start_time
    success_rate = successful / total * 100 if total else 0
    
    print()
    print("="*70)
    print("PROCESSING COMPLETE")
    print("="*70)
    print(f"Total symbols: {total}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Success rate: {success_rate:.1f}%")
    print(f"Total time: {total_time/60:.1f} minutes")
    print(f"Average per symbol: {total_time/total:.1f}s")
    
    if failed_symbols:
        print(f"\\nFailed symbols ({len(failed_symbols)}):")
        for i in range(0, len(failed_symbols), 10):
            batch = failed_symbols[i:i+10]
            print(f"  {', '.join(batch)}")

if __name__ == "__main__":
    main()
