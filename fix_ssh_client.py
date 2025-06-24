#!/usr/bin/env python3
"""
Fix SSH client import issue in configs.py
"""
import os
import sys
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
    print(f"{BLUE}  SIEMply SSH Client Fix             {NC}")
    print(f"{BLUE}======================================{NC}")

def fix_configs_py():
    """Fix the SSH client import in configs.py"""
    # Get script directory
    script_dir = Path(__file__).parent
    configs_py_path = script_dir / "backend" / "api" / "configs.py"
    
    if not configs_py_path.exists():
        print(f"{RED}✗ configs.py not found at {configs_py_path}{NC}")
        return False
    
    print(f"{YELLOW}Fixing SSH client import in configs.py...{NC}")
    
    # Read the file
    with open(configs_py_path, 'r') as f:
        content = f.read()
    
    # Check if the file already has the correct import
    if "from backend.automation.ssh_client import SIEMplySSHClient" in content:
        print(f"{GREEN}✓ configs.py already has the correct import{NC}")
        return True
    
    # Replace the import
    content = content.replace(
        "from backend.automation.ssh_client import SshClient",
        "from backend.automation.ssh_client import SIEMplySSHClient, create_ssh_client_from_host"
    )
    
    # Replace SshClient usage
    content = content.replace(
        "ssh_client = SshClient(",
        "ssh_client = create_ssh_client_from_host(host)"
    )
    
    # Replace exec_command with execute_command
    content = content.replace("ssh_client.exec_command(", "ssh_client.execute_command(")
    
    # Replace upload_file method
    content = content.replace(
        "ssh_client.upload_file(file_path, remote_path)",
        "# For now, use cat to create the file\n                with open(file_path, \"r\") as f:\n                    file_content = f.read()\n                    ssh_client.execute_command(f\"cat > {remote_path} << 'EOF'\\n{file_content}\\nEOF\")"
    )
    
    # Write the updated content back to the file
    with open(configs_py_path, 'w') as f:
        f.write(content)
    
    print(f"{GREEN}✓ SSH client import fixed in configs.py{NC}")
    return True

def main():
    """Main function"""
    print_header()
    
    if fix_configs_py():
        print(f"\n{GREEN}======================================{NC}")
        print(f"{GREEN}      SSH Client Fix Complete!        {NC}")
        print(f"{GREEN}======================================{NC}")
        print(f"\nYou should now be able to start the application.")
        print(f"Please restart the backend server.")
    else:
        print(f"\n{RED}======================================{NC}")
        print(f"{RED}      SSH Client Fix Failed!          {NC}")
        print(f"{RED}======================================{NC}")
        sys.exit(1)

if __name__ == "__main__":
    main() 