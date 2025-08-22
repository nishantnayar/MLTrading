#!/usr/bin/env python3
"""
Root Directory Cleanup and Reorganization
Moves standalone files from root to appropriate subdirectories
"""

import os
import shutil
from pathlib import Path

def reorganize_root_directory():
    """Reorganize files from root directory into logical subdirectories"""
    
    repo_root = Path(__file__).parent.parent
    print("=== Root Directory Reorganization ===")
    print(f"Repository root: {repo_root}")
    
    moves = []
    
    # 1. Move runner scripts to scripts/ directory
    runner_files = [
        "run_regression_tests.py",
        "run_tests.py", 
        "run_ui.py"
    ]
    
    for file_name in runner_files:
        source = repo_root / file_name
        dest = repo_root / "scripts" / file_name
        if source.exists():
            try:
                shutil.move(str(source), str(dest))
                moves.append(f"Moved {file_name} to scripts/")
                print(f"Moved {file_name} -> scripts/")
            except Exception as e:
                print(f"Failed to move {file_name}: {e}")
    
    # 2. Move test reports to tests/ directory  
    test_reports = [
        "regression_test_report.md"
    ]
    
    for file_name in test_reports:
        source = repo_root / file_name
        dest = repo_root / "tests" / file_name
        if source.exists():
            try:
                shutil.move(str(source), str(dest))
                moves.append(f"Moved {file_name} to tests/")
                print(f"Moved {file_name} -> tests/")
            except Exception as e:
                print(f"Failed to move {file_name}: {e}")
    
    # 3. Create tools/ directory and move development tools
    tools_dir = repo_root / "tools"
    tools_dir.mkdir(exist_ok=True)
    
    # Move chromedriver to tools/
    chrome_driver = repo_root / "chromedriver.exe"
    if chrome_driver.exists():
        try:
            shutil.move(str(chrome_driver), str(tools_dir / "chromedriver.exe"))
            moves.append("Moved chromedriver.exe to tools/")
            print("Moved chromedriver.exe -> tools/")
        except Exception as e:
            print(f"Failed to move chromedriver.exe: {e}")
    
    # 4. Create deployment/ directory for deployment configs
    deployment_dir = repo_root / "deployment"
    deployment_dir.mkdir(exist_ok=True)
    
    # Move environment.yml to deployment/
    env_yml = repo_root / "environment.yml"
    if env_yml.exists():
        try:
            shutil.move(str(env_yml), str(deployment_dir / "environment.yml"))
            moves.append("Moved environment.yml to deployment/")
            print("Moved environment.yml -> deployment/")
        except Exception as e:
            print(f"Failed to move environment.yml: {e}")
    
    # Move pytest.ini to deployment/ (testing config)
    pytest_ini = repo_root / "pytest.ini"
    if pytest_ini.exists():
        try:
            shutil.move(str(pytest_ini), str(deployment_dir / "pytest.ini"))
            moves.append("Moved pytest.ini to deployment/")
            print("Moved pytest.ini -> deployment/")
        except Exception as e:
            print(f"Failed to move pytest.ini: {e}")
    
    # Move pyproject.toml to deployment/
    pyproject = repo_root / "pyproject.toml"  
    if pyproject.exists():
        try:
            shutil.move(str(pyproject), str(deployment_dir / "pyproject.toml"))
            moves.append("Moved pyproject.toml to deployment/")
            print("Moved pyproject.toml -> deployment/")
        except Exception as e:
            print(f"Failed to move pyproject.toml: {e}")
    
    # Create __init__.py files for new directories
    init_files = [tools_dir, deployment_dir]
    for dir_path in init_files:
        init_file = dir_path / "__init__.py"
        if not init_file.exists():
            with open(init_file, 'w') as f:
                f.write(f'"""{dir_path.name.title()} utilities"""\n')
            print(f"Created {dir_path.name}/__init__.py")
    
    # 5. Update runner script paths (since they moved to scripts/)
    update_runner_scripts(repo_root)
    
    # 6. Create a new streamlined run script in root
    create_main_runner(repo_root)
    
    print(f"\n=== Reorganization Summary ===")
    print(f"Files moved: {len(moves)}")
    for move in moves:
        print(f"  - {move}")
    
    print(f"\n=== New Root Directory Structure ===")
    show_new_structure(repo_root)
    
    return len(moves)

def update_runner_scripts(repo_root):
    """Update import paths in moved runner scripts"""
    
    scripts_dir = repo_root / "scripts"
    
    # Update paths in moved scripts
    scripts_to_update = [
        "run_regression_tests.py",
        "run_tests.py",
        "run_ui.py"
    ]
    
    for script_name in scripts_to_update:
        script_path = scripts_dir / script_name
        if script_path.exists():
            try:
                with open(script_path, 'r') as f:
                    content = f.read()
                
                # Update sys.path to go up one more level
                updated_content = content.replace(
                    'sys.path.append(os.path.dirname(__file__))',
                    'sys.path.append(os.path.dirname(os.path.dirname(__file__)))'
                )
                updated_content = updated_content.replace(
                    'sys.path.insert(0, os.getcwd())',
                    'sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))'
                )
                
                with open(script_path, 'w') as f:
                    f.write(updated_content)
                    
                print(f"Updated import paths in {script_name}")
                
            except Exception as e:
                print(f"Failed to update {script_name}: {e}")

def create_main_runner(repo_root):
    """Create a main runner script in root for convenience"""
    
    main_runner = repo_root / "run.py"
    
    content = '''#!/usr/bin/env python3
"""
ML Trading System - Main Runner
Convenient entry point for common operations
"""

import sys
import subprocess
from pathlib import Path

def main():
    """Main runner with command options"""
    
    if len(sys.argv) < 2:
        print("ML Trading System Runner")
        print("Usage: python run.py [command]")
        print("")
        print("Available commands:")
        print("  ui          - Start the dashboard")
        print("  tests       - Run all tests")
        print("  regression  - Run regression tests")
        print("  collector   - Run Yahoo data collector")
        print("  prefect     - Setup Prefect")
        print("  cleanup     - Clean repository")
        return
    
    command = sys.argv[1].lower()
    scripts_dir = Path(__file__).parent / "scripts"
    
    if command == "ui":
        subprocess.run([sys.executable, str(scripts_dir / "run_ui.py")])
    elif command == "tests":
        subprocess.run([sys.executable, str(scripts_dir / "run_tests.py")])
    elif command == "regression":
        subprocess.run([sys.executable, str(scripts_dir / "run_regression_tests.py")])
    elif command == "collector":
        subprocess.run([sys.executable, str(scripts_dir / "run_yahoo_collector.py")])
    elif command == "prefect":
        subprocess.run([sys.executable, str(scripts_dir / "setup_prefect.py")])
    elif command == "cleanup":
        subprocess.run([sys.executable, str(scripts_dir / "comprehensive_cleanup.py")])
    else:
        print(f"Unknown command: {command}")
        print("Run 'python run.py' for available commands")

if __name__ == "__main__":
    main()
'''
    
    with open(main_runner, 'w') as f:
        f.write(content)
    
    print("Created run.py - main entry point")

def show_new_structure(repo_root):
    """Show the new clean root directory structure"""
    
    root_files = []
    for item in repo_root.iterdir():
        if item.is_file():
            root_files.append(item.name)
    
    print("Root files after cleanup:")
    for file_name in sorted(root_files):
        print(f"  {file_name}")
    
    print("\nNew directories:")
    for item in repo_root.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            print(f"  {item.name}/")

if __name__ == "__main__":
    reorganize_root_directory()