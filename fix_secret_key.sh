#!/bin/bash

# Script to fix SECRET_KEY issue in .env file
# For use with existing SIEMply installations

# Text colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print header
echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}  SIEMply SECRET_KEY Fix            ${NC}"
echo -e "${BLUE}======================================${NC}"

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if running in standard or Ubuntu installation
if [ -d "/opt/SIEMPLY" ]; then
    # Ubuntu installation
    INSTALL_DIR="/opt/SIEMPLY"
    ENV_FILE="/opt/SIEMPLY/.env"
    
    # Check if running as root
    if [ "$EUID" -ne 0 ]; then
        echo -e "${YELLOW}This script requires root privileges for Ubuntu installation.${NC}"
        echo -e "${YELLOW}Please run with sudo:${NC} sudo $0"
        exit 1
    fi
else
    # Standard installation
    INSTALL_DIR="$SCRIPT_DIR"
    ENV_FILE="$SCRIPT_DIR/.env"
fi

echo -e "\n${YELLOW}Installation detected at:${NC} $INSTALL_DIR"

# Check if .env file exists
echo -e "\n${YELLOW}Checking .env file...${NC}"
if [ -f "$ENV_FILE" ]; then
    echo -e "${GREEN}✓ .env file found${NC}"
    
    # Check if SECRET_KEY already exists in .env
    if grep -q "SIEMPLY_SECRET_KEY" "$ENV_FILE"; then
        echo -e "${GREEN}✓ SIEMPLY_SECRET_KEY already exists in .env file${NC}"
    else
        # Generate a random secret key
        echo -e "${YELLOW}Generating a new SECRET_KEY...${NC}"
        SECRET_KEY=$(openssl rand -hex 32)
        
        # Add SECRET_KEY to .env file
        echo "SIEMPLY_SECRET_KEY=${SECRET_KEY}" >> "$ENV_FILE"
        echo -e "${GREEN}✓ SIEMPLY_SECRET_KEY added to .env file${NC}"
    fi
else
    echo -e "${YELLOW}⚠ .env file not found, creating one...${NC}"
    
    # Generate a random secret key
    SECRET_KEY=$(openssl rand -hex 32)
    
    # Create .env file with SECRET_KEY
    cat > "$ENV_FILE" << EOL
# SIEMply Environment Configuration
SIEMPLY_API_PORT=5000
SIEMPLY_UI_PORT=8500
SIEMPLY_DB_URI=sqlite:///siemply.db
SIEMPLY_SECRET_KEY=${SECRET_KEY}
EOL
    echo -e "${GREEN}✓ New .env file created with SECRET_KEY${NC}"
fi

echo -e "\n${GREEN}======================================${NC}"
echo -e "${GREEN}      Fix Complete!                  ${NC}"
echo -e "${GREEN}======================================${NC}"
echo -e "\nYou should now be able to run the application without the SECRET_KEY error."
echo -e "If you're using the Ubuntu installation, restart the service with:"
echo -e "  ${YELLOW}sudo systemctl restart siemply${NC}"
echo -e "\nOr run the application manually with:"
echo -e "  ${YELLOW}$INSTALL_DIR/start.sh${NC}" 