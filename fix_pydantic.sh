#!/bin/bash

# Script to fix Pydantic BaseSettings import issue
# For use with existing SIEMply installations

# Text colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print header
echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}  SIEMply Pydantic Settings Fix      ${NC}"
echo -e "${BLUE}======================================${NC}"

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if running in standard or Ubuntu installation
if [ -d "/opt/SIEMPLY" ]; then
    # Ubuntu installation
    INSTALL_DIR="/opt/SIEMPLY"
    VENV_PATH="/opt/SIEMPLY/venv"
    SETTINGS_FILE="/opt/SIEMPLY/backend/config/settings.py"
    
    # Check if running as root
    if [ "$EUID" -ne 0 ]; then
        echo -e "${YELLOW}This script requires root privileges for Ubuntu installation.${NC}"
        echo -e "${YELLOW}Please run with sudo:${NC} sudo $0"
        exit 1
    fi
else
    # Standard installation
    INSTALL_DIR="$SCRIPT_DIR"
    VENV_PATH="$SCRIPT_DIR/venv"
    SETTINGS_FILE="$SCRIPT_DIR/backend/config/settings.py"
fi

echo -e "\n${YELLOW}Installation detected at:${NC} $INSTALL_DIR"

# Activate virtual environment
echo -e "\n${YELLOW}Activating virtual environment...${NC}"
if [ -f "$VENV_PATH/bin/activate" ]; then
    source "$VENV_PATH/bin/activate"
    echo -e "${GREEN}✓ Virtual environment activated${NC}"
else
    echo -e "${RED}✗ Virtual environment not found at $VENV_PATH${NC}"
    echo -e "${YELLOW}Creating a new virtual environment...${NC}"
    
    python3 -m venv "$VENV_PATH"
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ Failed to create virtual environment.${NC}"
        echo -e "${YELLOW}Please install python3-venv:${NC} sudo apt install python3-venv"
        exit 1
    fi
    source "$VENV_PATH/bin/activate"
    echo -e "${GREEN}✓ New virtual environment created and activated${NC}"
fi

# Install pydantic-settings
echo -e "\n${YELLOW}Installing pydantic-settings package...${NC}"
pip install pydantic-settings
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Failed to install pydantic-settings${NC}"
    exit 1
fi
echo -e "${GREEN}✓ pydantic-settings installed${NC}"

# Fix BaseSettings import in settings.py
echo -e "\n${YELLOW}Fixing BaseSettings import in settings.py...${NC}"
if [ -f "$SETTINGS_FILE" ]; then
    # Create a backup of the original file
    cp "$SETTINGS_FILE" "${SETTINGS_FILE}.bak"
    echo -e "${GREEN}✓ Backup created at ${SETTINGS_FILE}.bak${NC}"
    
    # Check if we need to fix the Field import
    if grep -q "from pydantic_settings import BaseSettings, Field" "$SETTINGS_FILE"; then
        echo -e "${YELLOW}Fixing incorrect Field import...${NC}"
        
        # Update the import statements
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS requires different sed syntax
            sed -i '' 's/from pydantic_settings import BaseSettings, Field/from pydantic import Field\nfrom pydantic_settings import BaseSettings/' "$SETTINGS_FILE"
        else
            # Linux
            sed -i 's/from pydantic_settings import BaseSettings, Field/from pydantic import Field\nfrom pydantic_settings import BaseSettings/' "$SETTINGS_FILE"
        fi
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ Field import fixed${NC}"
        else
            echo -e "${RED}✗ Failed to update Field import${NC}"
            echo -e "${YELLOW}Please manually edit $SETTINGS_FILE and change:${NC}"
            echo -e "  from pydantic_settings import BaseSettings, Field"
            echo -e "to:"
            echo -e "  from pydantic import Field"
            echo -e "  from pydantic_settings import BaseSettings"
            exit 1
        fi
    # Check if we need to fix just the BaseSettings import
    elif grep -q "from pydantic import BaseSettings" "$SETTINGS_FILE"; then
        echo -e "${YELLOW}Fixing BaseSettings import...${NC}"
        
        # Update the import statement
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS requires different sed syntax
            sed -i '' 's/from pydantic import BaseSettings/from pydantic_settings import BaseSettings/' "$SETTINGS_FILE"
        else
            # Linux
            sed -i 's/from pydantic import BaseSettings/from pydantic_settings import BaseSettings/' "$SETTINGS_FILE"
        fi
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ BaseSettings import fixed${NC}"
        else
            echo -e "${RED}✗ Failed to update import statement${NC}"
            echo -e "${YELLOW}Please manually edit $SETTINGS_FILE and change:${NC}"
            echo -e "  from pydantic import BaseSettings"
            echo -e "to:"
            echo -e "  from pydantic_settings import BaseSettings"
            exit 1
        fi
    else
        echo -e "${GREEN}✓ Imports already correct${NC}"
    fi
else
    echo -e "${RED}✗ Settings file not found at $SETTINGS_FILE${NC}"
    exit 1
fi

echo -e "\n${GREEN}======================================${NC}"
echo -e "${GREEN}      Fix Complete!                  ${NC}"
echo -e "${GREEN}======================================${NC}"
echo -e "\nYou should now be able to run the application without the Pydantic error."
echo -e "If you're using the Ubuntu installation, restart the service with:"
echo -e "  ${YELLOW}sudo systemctl restart siemply${NC}"
echo -e "\nOr run the application manually with:"
echo -e "  ${YELLOW}$INSTALL_DIR/start.sh${NC}" 