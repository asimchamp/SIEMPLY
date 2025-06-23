#!/bin/bash

# SIEMply All-in-One Fix Script
# This script applies all fixes for common SIEMply issues

# Text colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print header
echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}  SIEMply All-in-One Fix Script      ${NC}"
echo -e "${BLUE}======================================${NC}"

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if running in standard or Ubuntu installation
if [ -d "/opt/SIEMPLY" ]; then
    # Ubuntu installation
    INSTALL_DIR="/opt/SIEMPLY"
    FRONTEND_DIR="/opt/SIEMPLY/frontend"
    BACKEND_DIR="/opt/SIEMPLY/backend"
    SETTINGS_FILE="/opt/SIEMPLY/backend/config/settings.py"
    ENV_FILE="/opt/SIEMPLY/frontend/.env"
    MAIN_ENV_FILE="/opt/SIEMPLY/.env"
    
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
    BACKEND_DIR="$SCRIPT_DIR/backend"
    SETTINGS_FILE="$SCRIPT_DIR/backend/config/settings.py"
    ENV_FILE="$SCRIPT_DIR/frontend/.env"
    MAIN_ENV_FILE="$SCRIPT_DIR/.env"
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

echo -e "\n${YELLOW}Server IP address:${NC} $SERVER_IP"

# Fix 1: Pydantic BaseSettings import
echo -e "\n${YELLOW}Fix 1: Checking Pydantic BaseSettings import...${NC}"
if [ -f "$SETTINGS_FILE" ]; then
    # Create a backup of the original file
    cp "$SETTINGS_FILE" "${SETTINGS_FILE}.bak"
    
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
        
        echo -e "${GREEN}✓ Field import fixed${NC}"
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
        
        echo -e "${GREEN}✓ BaseSettings import fixed${NC}"
    else
        echo -e "${GREEN}✓ Imports already correct${NC}"
    fi
else
    echo -e "${RED}✗ Settings file not found at $SETTINGS_FILE${NC}"
fi

# Fix 2: SECRET_KEY in .env
echo -e "\n${YELLOW}Fix 2: Checking SECRET_KEY in .env...${NC}"
if [ -f "$MAIN_ENV_FILE" ]; then
    # Check if SECRET_KEY already exists in .env
    if grep -q "SIEMPLY_SECRET_KEY" "$MAIN_ENV_FILE"; then
        echo -e "${GREEN}✓ SIEMPLY_SECRET_KEY already exists in .env file${NC}"
    else
        # Generate a random secret key
        echo -e "${YELLOW}Generating a new SECRET_KEY...${NC}"
        SECRET_KEY=$(openssl rand -hex 32)
        
        # Add SECRET_KEY to .env file
        echo "SIEMPLY_SECRET_KEY=${SECRET_KEY}" >> "$MAIN_ENV_FILE"
        echo -e "${GREEN}✓ SIEMPLY_SECRET_KEY added to .env file${NC}"
    fi
else
    echo -e "${YELLOW}⚠ .env file not found, creating one...${NC}"
    
    # Generate a random secret key
    SECRET_KEY=$(openssl rand -hex 32)
    
    # Create .env file with SECRET_KEY
    cat > "$MAIN_ENV_FILE" << EOL
# SIEMply Environment Configuration
SIEMPLY_API_PORT=5000
SIEMPLY_UI_PORT=8500
SIEMPLY_DB_URI=sqlite:///siemply.db
SIEMPLY_SECRET_KEY=${SECRET_KEY}
SIEMPLY_FRONTEND_URL=http://${SERVER_IP}:8500
EOL
    echo -e "${GREEN}✓ New .env file created with SECRET_KEY${NC}"
fi

# Fix 3: Network binding for frontend
echo -e "\n${YELLOW}Fix 3: Checking network binding for frontend...${NC}"
FRONTEND_SCRIPT="$INSTALL_DIR/start_frontend.sh"
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
        
        echo -e "${GREEN}✓ Frontend script updated to bind to all interfaces${NC}"
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

# Fix 4: Network binding for backend
echo -e "\n${YELLOW}Fix 4: Checking network binding for backend...${NC}"
BACKEND_SCRIPT="$INSTALL_DIR/start_backend.sh"
if [ -f "$BACKEND_SCRIPT" ]; then
    # Create backup
    cp "$BACKEND_SCRIPT" "${BACKEND_SCRIPT}.bak"
    
    # Check if script already has host parameter
    if grep -q "\-\-host 0.0.0.0" "$BACKEND_SCRIPT"; then
        echo -e "${GREEN}✓ Backend script already configured to bind to all interfaces${NC}"
    else
        # Update script to add host parameter
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS requires different sed syntax
            sed -i '' 's/python main.py/python main.py --host 0.0.0.0/' "$BACKEND_SCRIPT"
        else
            # Linux
            sed -i 's/python main.py/python main.py --host 0.0.0.0/' "$BACKEND_SCRIPT"
        fi
        
        echo -e "${GREEN}✓ Backend script updated to bind to all interfaces${NC}"
    fi
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

# Fix 5: API connection in frontend
echo -e "\n${YELLOW}Fix 5: Configuring API connection in frontend...${NC}"

# Create frontend directory if it doesn't exist
mkdir -p "$FRONTEND_DIR"

# Create .env file for frontend
cat > "$ENV_FILE" << EOL
# SIEMply Frontend Environment Variables
VITE_API_URL=http://${SERVER_IP}:5000
EOL
echo -e "${GREEN}✓ Frontend .env file created with API URL: http://${SERVER_IP}:5000${NC}"

# Create public directory if it doesn't exist
mkdir -p "$FRONTEND_DIR/public"

# Create update-settings.html for localStorage
cat > "$FRONTEND_DIR/public/update-settings.html" << EOL
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
        
        // Redirect after 3 seconds
        setTimeout(() => {
            window.location.href = '/';
        }, 3000);
    </script>
</head>
<body>
    <h1>SIEMply Settings Update</h1>
    <p>This page updates the localStorage settings for SIEMply.</p>
    <p>You will be redirected to the main application in 3 seconds...</p>
</body>
</html>
EOL
echo -e "${GREEN}✓ Settings update page created${NC}"

# Fix 6: Install pydantic-settings
echo -e "\n${YELLOW}Fix 6: Installing pydantic-settings package...${NC}"
if [ -d "/opt/SIEMPLY" ]; then
    # Ubuntu installation
    source /opt/SIEMPLY/venv/bin/activate
else
    # Standard installation
    source venv/bin/activate
fi

pip install pydantic-settings
echo -e "${GREEN}✓ pydantic-settings installed${NC}"

echo -e "\n${GREEN}======================================${NC}"
echo -e "${GREEN}      All Fixes Applied!             ${NC}"
echo -e "${GREEN}======================================${NC}"
echo -e "\nYou should now be able to run the application without errors."
echo -e "Please restart the application:"
echo -e "  ${YELLOW}sudo systemctl restart siemply${NC} (for Ubuntu installation)"
echo -e "  ${YELLOW}./start.sh${NC} (for standard installation)"
echo -e "\nThen open the application in your browser:"
echo -e "  ${BLUE}http://${SERVER_IP}:8500${NC}"
echo -e "\nIMPORTANT: On first run, visit:"
echo -e "  ${BLUE}http://${SERVER_IP}:8500/update-settings.html${NC}"
echo -e "This will update your browser settings to connect to the API server." 