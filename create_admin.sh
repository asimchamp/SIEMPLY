#!/bin/bash

# Create admin user for SIEMply

echo "Setting up environment and creating admin user..."

# Navigate to backend directory
cd backend

# Install requirements
echo "Installing required packages..."
python3 -m pip install -r requirements.txt

# Create admin user
echo "Creating admin user..."
python3 create_admin.py --username admin --email admin@example.com --password admin123 --full-name "SIEMply Admin"

echo "Done! You can now log in with:"
echo "Username: admin"
echo "Password: admin123" 