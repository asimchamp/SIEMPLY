#!/bin/bash

# Script to set up frontend environment variables
# This creates or updates the .env file in the frontend directory

# Text colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print header
echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}  SIEMply Frontend Environment Setup  ${NC}"
echo -e "${BLUE}======================================${NC}"

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

# Get server IP address
SERVER_IP=$(hostname -I | awk '{print $1}')
if [ -z "$SERVER_IP" ]; then
    echo -e "${YELLOW}Could not automatically detect server IP.${NC}"
    echo -e "${YELLOW}Using localhost instead.${NC}"
    SERVER_IP="localhost"
fi

echo -e "\n${YELLOW}Server IP address:${NC} $SERVER_IP"

# Create .env file for frontend
echo -e "\n${YELLOW}Creating .env file for frontend...${NC}"
ENV_FILE="$FRONTEND_DIR/.env"

# Create frontend directory if it doesn't exist
mkdir -p "$FRONTEND_DIR"

# Create .env file
cat > "$ENV_FILE" << EOL
# SIEMply Frontend Environment Variables
VITE_API_URL=http://${SERVER_IP}:5000
EOL

echo -e "${GREEN}✓ Frontend .env file created with API URL: http://${SERVER_IP}:5000${NC}"

# Create update-settings.html for localStorage
echo -e "\n${YELLOW}Creating localStorage update page...${NC}"

# Create public directory if it doesn't exist
mkdir -p "$FRONTEND_DIR/public"

# Create update-settings.html
cat > "$FRONTEND_DIR/public/update-settings.html" << EOL
<!DOCTYPE html>
<html>
<head>
    <title>Update SIEMply Settings</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #1890ff;
        }
        .success {
            color: #52c41a;
            font-weight: bold;
        }
        .api-url {
            font-family: monospace;
            background-color: #f0f0f0;
            padding: 8px;
            border-radius: 4px;
            margin: 10px 0;
        }
        .countdown {
            font-weight: bold;
            color: #1890ff;
        }
    </style>
    <script>
        // Update localStorage settings
        const settings = {
            apiUrl: 'http://${SERVER_IP}:5000',
            theme: 'dark',
            defaultSplunkVersion: '9.1.1',
            defaultCriblVersion: '3.4.1',
            defaultInstallDir: '/opt'
        };
        
        window.onload = function() {
            // Save settings to localStorage
            localStorage.setItem('siemply_settings', JSON.stringify(settings));
            
            // Update display
            document.getElementById('apiUrl').textContent = settings.apiUrl;
            
            // Countdown timer
            let seconds = 5;
            const countdownElement = document.getElementById('countdown');
            const timer = setInterval(() => {
                seconds--;
                countdownElement.textContent = seconds;
                if (seconds <= 0) {
                    clearInterval(timer);
                    window.location.href = '/';
                }
            }, 1000);
        }
    </script>
</head>
<body>
    <div class="container">
        <h1>SIEMply Settings Update</h1>
        <p class="success">✅ Settings updated successfully!</p>
        <p>API URL set to: <span class="api-url" id="apiUrl"></span></p>
        <p>This page updates the localStorage settings for SIEMply.</p>
        <p>You will be redirected to the main application in <span class="countdown" id="countdown">5</span> seconds...</p>
    </div>
</body>
</html>
EOL

echo -e "${GREEN}✓ Settings update page created${NC}"

echo -e "\n${GREEN}======================================${NC}"
echo -e "${GREEN}      Setup Complete!                 ${NC}"
echo -e "${GREEN}======================================${NC}"
echo -e "\nFrontend environment is now configured."
echo -e "When you start the application, visit:"
echo -e "  ${BLUE}http://${SERVER_IP}:8500/update-settings.html${NC}"
echo -e "This will update your browser settings to connect to the API server." 