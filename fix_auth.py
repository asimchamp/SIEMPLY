#!/usr/bin/env python3
"""
Fix authentication and CORS issues for SIEMply
"""
import os
import sys
import json
import socket
import re

def get_ip_address():
    """Get the IP address of the machine"""
    try:
        # Create a socket to determine the IP address
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
        s.close()
        return ip_address
    except:
        return "127.0.0.1"

def fix_cors():
    """Fix CORS configuration in main.py"""
    ip_address = get_ip_address()
    print(f"Detected IP address: {ip_address}")
    
    # Read the main.py file
    with open("backend/main.py", "r") as f:
        content = f.read()
    
    # Define the new CORS configuration
    cors_config = f'''# Configure CORS
# Allow specific origins including localhost and your frontend IP
origins = [
    "http://localhost:8500",
    "http://127.0.0.1:8500",
    "http://{ip_address}:8500",  # Your frontend IP
    # Add any other origins you need
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)'''
    
    # Replace the CORS configuration
    pattern = r'# Configure CORS.*?expose_headers=\[".*?"\],?\n\)'
    new_content = re.sub(pattern, cors_config, content, flags=re.DOTALL)
    
    # Write the updated content back to main.py
    with open("backend/main.py", "w") as f:
        f.write(new_content)
    
    print("CORS configuration updated in backend/main.py")

def update_api_url():
    """Update API URL in frontend .env file"""
    ip_address = get_ip_address()
    
    # Create or update .env file
    with open("frontend/.env", "w") as f:
        f.write(f"VITE_API_URL=http://{ip_address}:5000\n")
    
    print(f"API URL updated in frontend/.env to http://{ip_address}:5000")

def main():
    """Main function"""
    print("Fixing authentication and CORS issues for SIEMply...")
    
    fix_cors()
    update_api_url()
    
    print("\nChanges applied successfully!")
    print("\nNext steps:")
    print("1. Restart the backend server:")
    print("   ./start_backend.sh")
    print("2. Restart the frontend server:")
    print("   ./start_frontend.sh")
    print("3. Log in with:")
    print("   Username: admin")
    print("   Password: admin123")
    print("\nNote: If you haven't created an admin user yet, run:")
    print("   cd backend && python3 -m pip install -r requirements.txt && python3 create_admin.py")

if __name__ == "__main__":
    main() 