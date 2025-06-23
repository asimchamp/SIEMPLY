#!/bin/bash

# Script to fix CORS issues in SIEMply
# This ensures the frontend can communicate with the backend API

# Text colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print header
echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}  SIEMply CORS Fix                  ${NC}"
echo -e "${BLUE}======================================${NC}"

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if running in standard or Ubuntu installation
if [ -d "/opt/SIEMPLY" ]; then
    # Ubuntu installation
    INSTALL_DIR="/opt/SIEMPLY"
    BACKEND_DIR="/opt/SIEMPLY/backend"
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
    BACKEND_DIR="$SCRIPT_DIR/backend"
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

echo -e "\n${YELLOW}Server IP address:${NC} $SERVER_IP"

# Fix 1: Update main.py to allow all origins
echo -e "\n${YELLOW}Fix 1: Updating CORS configuration in main.py...${NC}"
MAIN_PY="$BACKEND_DIR/main.py"
if [ -f "$MAIN_PY" ]; then
    # Create backup
    cp "$MAIN_PY" "${MAIN_PY}.bak"
    
    # Check if we need to update CORS configuration
    if grep -q "CORSMiddleware" "$MAIN_PY"; then
        echo -e "${YELLOW}Updating CORS configuration...${NC}"
        
        # Create a temporary file with the updated CORS configuration
        TMP_FILE=$(mktemp)
        
        # Write the beginning of the file until the CORS configuration
        sed -n '1,/# Configure CORS/p' "$MAIN_PY" > "$TMP_FILE"
        
        # Add the new CORS configuration
        cat >> "$TMP_FILE" << 'EOL'
# Configure CORS
# For development, allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)
EOL
        
        # Write the rest of the file after the CORS middleware
        sed -n '/app.include_router/,$p' "$MAIN_PY" >> "$TMP_FILE"
        
        # Replace the original file with the updated one
        mv "$TMP_FILE" "$MAIN_PY"
        
        echo -e "${GREEN}✓ CORS configuration updated in main.py${NC}"
    else
        echo -e "${RED}✗ Could not find CORS configuration in main.py${NC}"
    fi
else
    echo -e "${RED}✗ main.py not found at $MAIN_PY${NC}"
fi

# Fix 2: Update frontend API service
echo -e "\n${YELLOW}Fix 2: Updating frontend API service...${NC}"
API_TS="$FRONTEND_DIR/src/services/api.ts"
if [ -f "$API_TS" ]; then
    # Create backup
    cp "$API_TS" "${API_TS}.bak"
    
    # Create a temporary file with the updated API service
    TMP_FILE=$(mktemp)
    
    # Add the new API service configuration
    cat > "$TMP_FILE" << 'EOL'
/**
 * API Service
 * Provides methods for interacting with the SIEMply backend API
 */
import axios from 'axios';

// Get API URL from environment or localStorage
const getApiUrl = () => {
  // First check localStorage for user settings
  const settingsJson = localStorage.getItem('siemply_settings');
  if (settingsJson) {
    try {
      const settings = JSON.parse(settingsJson);
      if (settings.apiUrl) {
        return settings.apiUrl;
      }
    } catch (e) {
      console.error('Error parsing settings from localStorage:', e);
    }
  }
  
  // Fall back to environment variable
  return import.meta.env.VITE_API_URL || 'http://localhost:5000';
};

// Create axios instance with base URL and default headers
const api = axios.create({
  baseURL: getApiUrl(),
  headers: {
    'Content-Type': 'application/json',
  },
  // Enable credentials for CORS
  withCredentials: false,
});

// Add request interceptor to update baseURL if it changes
api.interceptors.request.use((config) => {
  config.baseURL = getApiUrl();
  return config;
});
EOL
    
    # Write the rest of the file after the API configuration
    sed -n '/\/\/ Host types/,$p' "$API_TS" >> "$TMP_FILE"
    
    # Replace the original file with the updated one
    mv "$TMP_FILE" "$API_TS"
    
    echo -e "${GREEN}✓ API service updated${NC}"
else
    echo -e "${RED}✗ API service file not found at $API_TS${NC}"
fi

# Fix 3: Update frontend .env file
echo -e "\n${YELLOW}Fix 3: Updating frontend .env file...${NC}"
ENV_FILE="$FRONTEND_DIR/.env"

# Create frontend directory if it doesn't exist
mkdir -p "$FRONTEND_DIR"

# Create .env file for frontend
cat > "$ENV_FILE" << EOL
# SIEMply Frontend Environment Variables
VITE_API_URL=http://${SERVER_IP}:5000
EOL
echo -e "${GREEN}✓ Frontend .env file updated with API URL: http://${SERVER_IP}:5000${NC}"

# Fix 4: Update localStorage settings page
echo -e "\n${YELLOW}Fix 4: Creating localStorage update page...${NC}"

# Create public directory if it doesn't exist
mkdir -p "$FRONTEND_DIR/public"

# Create update-settings.html for localStorage
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
echo -e "${GREEN}      CORS Fix Complete!             ${NC}"
echo -e "${GREEN}======================================${NC}"
echo -e "\nYou should now be able to connect to the API server."
echo -e "Please restart the application:"
echo -e "  ${YELLOW}sudo systemctl restart siemply${NC} (for Ubuntu installation)"
echo -e "  ${YELLOW}./start.sh${NC} (for standard installation)"
echo -e "\nThen open the application in your browser:"
echo -e "  ${BLUE}http://${SERVER_IP}:8500${NC}"
echo -e "\nIMPORTANT: On first run, visit:"
echo -e "  ${BLUE}http://${SERVER_IP}:8500/update-settings.html${NC}"
echo -e "This will update your browser settings to connect to the API server." 