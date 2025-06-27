#!/usr/bin/env python3
"""
SIEMply Environment Check Script
This script checks the environment and diagnoses issues
"""
import os
import sys
import importlib
import subprocess
from pathlib import Path

# Text colors for console output
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color

def print_header():
    """Print script header"""
    print(f"{BLUE}======================================{NC}")
    print(f"{BLUE}  SIEMply Environment Check          {NC}")
    print(f"{BLUE}======================================{NC}")

def check_python_version():
    """Check Python version"""
    print(f"\n{YELLOW}Checking Python version...{NC}")
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"{RED}✗ Python version must be 3.8 or higher{NC}")
        return False
    else:
        print(f"{GREEN}✓ Python version is 3.8 or higher{NC}")
        return True

def check_virtual_env():
    """Check if running in a virtual environment"""
    print(f"\n{YELLOW}Checking virtual environment...{NC}")
    
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print(f"{GREEN}✓ Running in a virtual environment{NC}")
        print(f"Virtual environment path: {sys.prefix}")
        return True
    else:
        print(f"{RED}✗ Not running in a virtual environment{NC}")
        print(f"Please activate the virtual environment with:")
        print(f"  source venv/bin/activate")
        return False

def check_dependencies():
    """Check if all required dependencies are installed"""
    print(f"\n{YELLOW}Checking required dependencies...{NC}")
    
    required_packages = [
        'fastapi',
        'uvicorn',
        'pydantic',
        'sqlalchemy',
        'paramiko',
        'python-jose',
        'passlib',
        'python-multipart',
        'python-dotenv',
        'pydantic-settings',
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            importlib.import_module(package.replace('-', '_'))
            print(f"{GREEN}✓ {package} is installed{NC}")
        except ImportError:
            print(f"{RED}✗ {package} is not installed{NC}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n{RED}Missing packages: {', '.join(missing_packages)}{NC}")
        print(f"Please install the missing packages with:")
        print(f"  pip install -r backend/requirements.txt")
        return False
    else:
        print(f"\n{GREEN}✓ All required packages are installed{NC}")
        return True

def check_env_file():
    """Check if .env file exists and has required variables"""
    print(f"\n{YELLOW}Checking .env file...{NC}")
    
    script_dir = Path(__file__).parent.parent
    env_file = script_dir / ".env"
    
    if not env_file.exists():
        print(f"{RED}✗ .env file not found{NC}")
        return False
    
    print(f"{GREEN}✓ .env file found{NC}")
    
    # Check required variables
    required_vars = [
        'SIEMPLY_SECRET_KEY',
        'SIEMPLY_API_PORT',
        'SIEMPLY_UI_PORT',
        'SIEMPLY_DB_URI',
    ]
    
    missing_vars = []
    
    with open(env_file, 'r') as f:
        content = f.read()
        
        for var in required_vars:
            if var not in content:
                print(f"{RED}✗ {var} not found in .env file{NC}")
                missing_vars.append(var)
            else:
                print(f"{GREEN}✓ {var} found in .env file{NC}")
    
    if missing_vars:
        print(f"\n{RED}Missing variables in .env file: {', '.join(missing_vars)}{NC}")
        return False
    else:
        print(f"\n{GREEN}✓ All required variables found in .env file{NC}")
        return True

def check_database():
    """Check if database exists and can be connected to"""
    print(f"\n{YELLOW}Checking database...{NC}")
    
    try:
        # Add parent directory to path
        sys.path.append(str(Path(__file__).parent.parent))
        from backend.models import get_db, Base, engine
        
        # Create tables if they don't exist
        Base.metadata.create_all(bind=engine)
        
        # Try to get a database session
        db = next(get_db())
        db.close()
        
        print(f"{GREEN}✓ Database connection successful{NC}")
        return True
    except Exception as e:
        print(f"{RED}✗ Database connection failed: {str(e)}{NC}")
        return False

def check_node_npm():
    """Check if Node.js and npm are installed"""
    print(f"\n{YELLOW}Checking Node.js and npm...{NC}")
    
    try:
        # Check Node.js
        node_version = subprocess.check_output(['node', '--version']).decode('utf-8').strip()
        print(f"Node.js version: {node_version}")
        
        # Check npm
        npm_version = subprocess.check_output(['npm', '--version']).decode('utf-8').strip()
        print(f"npm version: {npm_version}")
        
        print(f"{GREEN}✓ Node.js and npm are installed{NC}")
        return True
    except Exception as e:
        print(f"{RED}✗ Node.js and npm check failed: {str(e)}{NC}")
        print(f"Please install Node.js and npm")
        return False

def check_frontend_deps():
    """Check if frontend dependencies are installed"""
    print(f"\n{YELLOW}Checking frontend dependencies...{NC}")
    
    script_dir = Path(__file__).parent.parent
    node_modules = script_dir / "frontend" / "node_modules"
    
    if not node_modules.exists():
        print(f"{RED}✗ Frontend dependencies not installed{NC}")
        print(f"Please install frontend dependencies with:")
        print(f"  cd frontend && npm install")
        return False
    else:
        print(f"{GREEN}✓ Frontend dependencies are installed{NC}")
        return True

def main():
    """Main function"""
    print_header()
    
    checks = [
        check_python_version(),
        check_virtual_env(),
        check_dependencies(),
        check_env_file(),
        check_database(),
        check_node_npm(),
        check_frontend_deps(),
    ]
    
    if all(checks):
        print(f"\n{GREEN}======================================{NC}")
        print(f"{GREEN}      Environment Check Passed!      {NC}")
        print(f"{GREEN}======================================{NC}")
        print(f"\nYou can now start the application.")
        print(f"Start backend: cd backend && python main.py")
        print(f"Start frontend: cd frontend && npm run dev")
    else:
        print(f"\n{RED}======================================{NC}")
        print(f"{RED}      Environment Check Failed!      {NC}")
        print(f"{RED}======================================{NC}")
        print(f"\nPlease fix the issues above before starting the application.")
        return False

if __name__ == "__main__":
    main() 