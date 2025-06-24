#!/bin/bash

# Script to create admin user for SIEMply

# Text colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Setting up environment and creating admin user...${NC}"

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if virtual environment exists
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv "$SCRIPT_DIR/venv"
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source "$SCRIPT_DIR/venv/bin/activate"

# Install required packages
echo -e "${YELLOW}Installing required packages...${NC}"
pip install -r "$SCRIPT_DIR/backend/requirements.txt"

# Create admin user
echo -e "${YELLOW}Creating admin user...${NC}"
python "$SCRIPT_DIR/backend/create_admin.py" --username admin --email admin@example.com --password admin123 --full-name "SIEMply Admin"

echo -e "${GREEN}Done! You can now log in with:${NC}"
echo -e "Username: ${YELLOW}admin${NC}"
echo -e "Password: ${YELLOW}admin123${NC}" 