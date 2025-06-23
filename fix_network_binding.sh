#!/bin/bash

# Script to fix network binding for SIEMply
# This ensures the services are accessible from other machines on the network

# Text colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print header
echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}  SIEMply Network Binding Fix        ${NC}"
echo -e "${BLUE}======================================${NC}"

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if running in standard or Ubuntu installation
if [ -d "/opt/SIEMPLY" ]; then
    # Ubuntu installation
    INSTALL_DIR="/opt/SIEMPLY"
    FRONTEND_SCRIPT="/opt/SIEMPLY/start_frontend.sh"
    BACKEND_SCRIPT="/opt/SIEMPLY/start_backend.sh"
    
    # Check if running as root
    if [ "$EUID" -ne 0 ]; then
        echo -e "${YELLOW}This script requires root privileges for Ubuntu installation.${NC}"
        echo -e "${YELLOW}Please run with sudo:${NC} sudo $0"
        exit 1
    fi
else
    # Standard installation
    INSTALL_DIR="$SCRIPT_DIR"
    FRONTEND_SCRIPT="$SCRIPT_DIR/start_frontend.sh"
    BACKEND_SCRIPT="$SCRIPT_DIR/start_backend.sh"
fi

echo -e "\n${YELLOW}Installation detected at:${NC} $INSTALL_DIR"

# Fix frontend script
echo -e "\n${YELLOW}Updating frontend script to bind to all network interfaces...${NC}"
if [ -f "$FRONTEND_SCRIPT" ]; then
    # Create backup
    cp "$FRONTEND_SCRIPT" "${FRONTEND_SCRIPT}.bak"
    
    # Check if script already has host parameter
    if grep -q "\-\-host 0.0.0.0" "$FRONTEND_SCRIPT"; then
        echo -e "${GREEN}✓ Frontend script already configured to bind to all interfaces${NC}"
    else
        # Update script to add host parameter
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS requires different sed syntax
            sed -i '' 's/npm run dev -- --port 8500/npm run dev -- --port 8500 --host 0.0.0.0/' "$FRONTEND_SCRIPT"
        else
            # Linux
            sed -i 's/npm run dev -- --port 8500/npm run dev -- --port 8500 --host 0.0.0.0/' "$FRONTEND_SCRIPT"
        fi
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ Frontend script updated to bind to all interfaces${NC}"
        else
            echo -e "${RED}✗ Failed to update frontend script${NC}"
            echo -e "${YELLOW}Please manually edit $FRONTEND_SCRIPT and add --host 0.0.0.0 parameter${NC}"
        fi
    fi
else
    echo -e "${RED}✗ Frontend script not found at $FRONTEND_SCRIPT${NC}"
    echo -e "${YELLOW}Creating new frontend script...${NC}"
    
    if [ -d "/opt/SIEMPLY" ]; then
        # Ubuntu installation
        cat > "$FRONTEND_SCRIPT" << EOL
#!/bin/bash
# Start SIEMply frontend server
cd /opt/SIEMPLY/frontend
npm run dev -- --port 8500 --host 0.0.0.0
EOL
    else
        # Standard installation
        cat > "$FRONTEND_SCRIPT" << EOL
#!/bin/bash
# Start SIEMply frontend server
cd frontend
npm run dev -- --port 8500 --host 0.0.0.0
EOL
    fi
    
    chmod +x "$FRONTEND_SCRIPT"
    echo -e "${GREEN}✓ New frontend script created with correct network binding${NC}"
fi

# Fix backend script if needed
echo -e "\n${YELLOW}Checking backend script...${NC}"
if [ -f "$BACKEND_SCRIPT" ]; then
    # The backend should already be binding to 0.0.0.0 by default
    echo -e "${GREEN}✓ Backend script exists${NC}"
else
    echo -e "${RED}✗ Backend script not found at $BACKEND_SCRIPT${NC}"
    echo -e "${YELLOW}Creating new backend script...${NC}"
    
    if [ -d "/opt/SIEMPLY" ]; then
        # Ubuntu installation
        cat > "$BACKEND_SCRIPT" << EOL
#!/bin/bash
# Start SIEMply backend server
source /opt/SIEMPLY/venv/bin/activate
cd /opt/SIEMPLY/backend
python main.py --host 0.0.0.0
EOL
    else
        # Standard installation
        cat > "$BACKEND_SCRIPT" << EOL
#!/bin/bash
# Start SIEMply backend server
source venv/bin/activate
cd backend
python main.py --host 0.0.0.0
EOL
    fi
    
    chmod +x "$BACKEND_SCRIPT"
    echo -e "${GREEN}✓ New backend script created with correct network binding${NC}"
fi

# Update .env file to ensure correct frontend URL
echo -e "\n${YELLOW}Checking .env file for FRONTEND_URL...${NC}"
ENV_FILE="$INSTALL_DIR/.env"

if [ -f "$ENV_FILE" ]; then
    # Get server IP address
    SERVER_IP=$(hostname -I | awk '{print $1}')
    
    if [ -z "$SERVER_IP" ]; then
        SERVER_IP="0.0.0.0"
        echo -e "${YELLOW}⚠ Could not determine server IP, using 0.0.0.0${NC}"
    fi
    
    # Check if SIEMPLY_FRONTEND_URL exists
    if grep -q "SIEMPLY_FRONTEND_URL" "$ENV_FILE"; then
        # Update existing entry
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS requires different sed syntax
            sed -i '' "s|SIEMPLY_FRONTEND_URL=.*|SIEMPLY_FRONTEND_URL=http://$SERVER_IP:8500|" "$ENV_FILE"
        else
            # Linux
            sed -i "s|SIEMPLY_FRONTEND_URL=.*|SIEMPLY_FRONTEND_URL=http://$SERVER_IP:8500|" "$ENV_FILE"
        fi
    else
        # Add new entry
        echo "SIEMPLY_FRONTEND_URL=http://$SERVER_IP:8500" >> "$ENV_FILE"
    fi
    echo -e "${GREEN}✓ FRONTEND_URL updated in .env file to http://$SERVER_IP:8500${NC}"
else
    echo -e "${RED}✗ .env file not found at $ENV_FILE${NC}"
fi

echo -e "\n${GREEN}======================================${NC}"
echo -e "${GREEN}      Fix Complete!                  ${NC}"
echo -e "${GREEN}======================================${NC}"
echo -e "\nYou should now be able to access the application from other machines on your network."
echo -e "If you're using the Ubuntu installation, restart the service with:"
echo -e "  ${YELLOW}sudo systemctl restart siemply${NC}"
echo -e "\nOr run the application manually with:"
echo -e "  ${YELLOW}$INSTALL_DIR/start.sh${NC}"
echo -e "\nFrontend should be accessible at: ${BLUE}http://$SERVER_IP:8500${NC}"
echo -e "Backend should be accessible at: ${BLUE}http://$SERVER_IP:5000${NC}" 