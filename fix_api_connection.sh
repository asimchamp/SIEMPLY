#!/bin/bash

# Script to fix API connection issues between frontend and backend
# For use with existing SIEMply installations

# Text colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print header
echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}  SIEMply API Connection Fix         ${NC}"
echo -e "${BLUE}======================================${NC}"

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if running in standard or Ubuntu installation
if [ -d "/opt/SIEMPLY" ]; then
    # Ubuntu installation
    INSTALL_DIR="/opt/SIEMPLY"
    FRONTEND_DIR="/opt/SIEMPLY/frontend"
    
    # Check if running as root
    if [ "$EUID" -ne 0 ]; then
        echo -e "${YELLOW}This script requires root privileges for Ubuntu installation.${NC}"
        echo -e "${YELLOW}Please run with sudo:${NC} sudo $0"
        exit 1
    fi
else
    # Standard installation
    INSTALL_DIR="$SCRIPT_DIR"
    FRONTEND_DIR="$SCRIPT_DIR/frontend"
fi

echo -e "\n${YELLOW}Installation detected at:${NC} $INSTALL_DIR"

# Get server IP address
SERVER_IP=$(hostname -I | awk '{print $1}')
if [ -z "$SERVER_IP" ]; then
    echo -e "${YELLOW}Could not automatically detect server IP.${NC}"
    echo -e "${YELLOW}Please enter the server IP address:${NC}"
    read -p "> " SERVER_IP
    
    if [ -z "$SERVER_IP" ]; then
        echo -e "${RED}✗ No IP address provided. Using localhost.${NC}"
        SERVER_IP="localhost"
    fi
fi

# Create .env file for frontend
echo -e "\n${YELLOW}Creating .env file for frontend...${NC}"
ENV_FILE="$FRONTEND_DIR/.env"

cat > "$ENV_FILE" << EOL
# SIEMply Frontend Environment Variables
VITE_API_URL=http://${SERVER_IP}:5000
EOL

echo -e "${GREEN}✓ Frontend .env file created with API URL: http://${SERVER_IP}:5000${NC}"

# Update settings.js file if it exists
SETTINGS_JS="$FRONTEND_DIR/src/settings.js"
if [ -f "$SETTINGS_JS" ]; then
    echo -e "\n${YELLOW}Updating settings.js file...${NC}"
    
    # Create backup
    cp "$SETTINGS_JS" "${SETTINGS_JS}.bak"
    
    # Update API URL in settings.js
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS requires different sed syntax
        sed -i '' "s|apiUrl:.*|apiUrl: 'http://${SERVER_IP}:5000',|" "$SETTINGS_JS"
    else
        # Linux
        sed -i "s|apiUrl:.*|apiUrl: 'http://${SERVER_IP}:5000',|" "$SETTINGS_JS"
    fi
    
    echo -e "${GREEN}✓ settings.js updated with API URL: http://${SERVER_IP}:5000${NC}"
fi

# Update localStorage settings if vite is installed
if command -v npm &>/dev/null; then
    echo -e "\n${YELLOW}Creating localStorage update script...${NC}"
    
    # Create a temporary HTML file to update localStorage
    TEMP_HTML="$FRONTEND_DIR/update-settings.html"
    
    cat > "$TEMP_HTML" << EOL
<!DOCTYPE html>
<html>
<head>
    <title>Update SIEMply Settings</title>
    <script>
        // Update localStorage settings
        const settings = {
            apiUrl: 'http://${SERVER_IP}:5000',
            theme: 'dark',
            defaultSplunkVersion: '9.1.1',
            defaultCriblVersion: '3.4.1',
            defaultInstallDir: '/opt'
        };
        
        localStorage.setItem('siemply_settings', JSON.stringify(settings));
        document.write('<p>Settings updated successfully!</p>');
        document.write('<p>API URL set to: ' + settings.apiUrl + '</p>');
    </script>
</head>
<body>
    <h1>SIEMply Settings Update</h1>
    <p>This page updates the localStorage settings for SIEMply.</p>
</body>
</html>
EOL
    
    echo -e "${GREEN}✓ localStorage update script created${NC}"
    echo -e "${YELLOW}NOTE: After restarting the application, open the browser and visit:${NC}"
    echo -e "${BLUE}http://${SERVER_IP}:8500/update-settings.html${NC}"
    echo -e "${YELLOW}Then navigate back to the main application.${NC}"
fi

# Rebuild frontend if needed
if [ -f "$FRONTEND_DIR/package.json" ]; then
    echo -e "\n${YELLOW}Do you want to rebuild the frontend? (y/n)${NC}"
    read -p "> " rebuild
    
    if [[ "$rebuild" == "y" || "$rebuild" == "Y" ]]; then
        echo -e "\n${YELLOW}Rebuilding frontend...${NC}"
        cd "$FRONTEND_DIR"
        npm run build
        echo -e "${GREEN}✓ Frontend rebuilt${NC}"
    else
        echo -e "${YELLOW}Skipping frontend rebuild.${NC}"
    fi
fi

echo -e "\n${GREEN}======================================${NC}"
echo -e "${GREEN}      Fix Complete!                  ${NC}"
echo -e "${GREEN}======================================${NC}"
echo -e "\nYou should now be able to connect to the API server."
echo -e "Please restart the application:"
echo -e "  ${YELLOW}sudo systemctl restart siemply${NC} (for Ubuntu installation)"
echo -e "  ${YELLOW}./start.sh${NC} (for standard installation)"
echo -e "\nThen open the application in your browser:"
echo -e "  ${BLUE}http://${SERVER_IP}:8500${NC}" 