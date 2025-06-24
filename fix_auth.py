#!/usr/bin/env python3
"""
SIEMply Auth Fix Script
This script fixes authentication issues in the SIEMply application
"""
import os
import sys
import socket
import argparse
import secrets
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
    print(f"{BLUE}  SIEMply Auth Fix                  {NC}")
    print(f"{BLUE}======================================{NC}")

def get_server_ip():
    """Get server IP address"""
    try:
        # Get all network interfaces
        hostname = socket.gethostname()
        ip_addresses = socket.gethostbyname_ex(hostname)[2]
        # Filter out localhost
        ip_addresses = [ip for ip in ip_addresses if not ip.startswith("127.")]
        if ip_addresses:
            return ip_addresses[0]
    except Exception as e:
        print(f"{YELLOW}Could not automatically detect server IP: {e}{NC}")
    
    # Ask user for IP address
    print(f"{YELLOW}Please enter the server IP address:{NC}")
    server_ip = input("> ")
    
    if not server_ip:
        print(f"{RED}✗ No IP address provided. Using localhost.{NC}")
        return "localhost"
    
    return server_ip

def create_env_file(server_ip):
    """Create or update .env file"""
    print(f"\n{YELLOW}Creating/updating .env file...{NC}")
    
    # Get script directory
    script_dir = Path(__file__).parent
    env_file = script_dir / ".env"
    
    # Generate a random secret key
    secret_key = secrets.token_hex(32)
    
    # Check if .env file exists
    if env_file.exists():
        print(f"{YELLOW}Updating existing .env file...{NC}")
        
        # Read existing content
        with open(env_file, 'r') as f:
            content = f.read()
        
        # Check if SECRET_KEY already exists
        if "SIEMPLY_SECRET_KEY" in content:
            print(f"{GREEN}✓ SECRET_KEY already exists in .env file{NC}")
        else:
            # Add SECRET_KEY to .env file
            with open(env_file, 'a') as f:
                f.write(f"\nSIEMPLY_SECRET_KEY={secret_key}\n")
            print(f"{GREEN}✓ SECRET_KEY added to .env file{NC}")
        
        # Check if FRONTEND_URL already exists
        if "SIEMPLY_FRONTEND_URL" in content:
            # Update FRONTEND_URL
            lines = content.split('\n')
            with open(env_file, 'w') as f:
                for line in lines:
                    if line.startswith("SIEMPLY_FRONTEND_URL="):
                        f.write(f"SIEMPLY_FRONTEND_URL=http://{server_ip}:8500\n")
                    else:
                        f.write(f"{line}\n")
            print(f"{GREEN}✓ FRONTEND_URL updated in .env file{NC}")
        else:
            # Add FRONTEND_URL to .env file
            with open(env_file, 'a') as f:
                f.write(f"\nSIEMPLY_FRONTEND_URL=http://{server_ip}:8500\n")
            print(f"{GREEN}✓ FRONTEND_URL added to .env file{NC}")
    else:
        print(f"{YELLOW}Creating new .env file...{NC}")
        
        # Create .env file
        with open(env_file, 'w') as f:
            f.write(f"""# SIEMply Environment Configuration
SIEMPLY_API_PORT=5000
SIEMPLY_UI_PORT=8500
SIEMPLY_DB_URI=sqlite:///backend/siemply.db
SIEMPLY_SECRET_KEY={secret_key}
SIEMPLY_FRONTEND_URL=http://{server_ip}:8500
""")
        print(f"{GREEN}✓ New .env file created{NC}")

def main():
    """Main function"""
    print_header()
    
    # Get server IP address
    server_ip = get_server_ip()
    print(f"\n{YELLOW}Server IP address:{NC} {server_ip}")
    
    # Create/update .env file
    create_env_file(server_ip)
    
    print(f"\n{GREEN}======================================{NC}")
    print(f"{GREEN}      Auth Fix Complete!             {NC}")
    print(f"{GREEN}======================================{NC}")
    print(f"\nYou should now be able to authenticate with the API server.")
    print(f"Please restart the application to apply the changes.")
    print(f"\nThen open the application in your browser:")
    print(f"  {BLUE}http://{server_ip}:8500{NC}")

if __name__ == "__main__":
    main() 