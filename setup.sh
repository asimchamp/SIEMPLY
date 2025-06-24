#!/bin/bash

# SIEMply Setup Script
# This script sets up the SIEMply environment

# Text colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print header
echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}  SIEMply Setup Script               ${NC}"
echo -e "${BLUE}======================================${NC}"

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

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

# Step 1: Check system dependencies
echo -e "\n${YELLOW}Step 1: Checking system dependencies...${NC}"

# Check Python
if command -v python3 &>/dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d ' ' -f 2)
    echo -e "${GREEN}✓ Python $PYTHON_VERSION is installed${NC}"
else
    echo -e "${RED}✗ Python 3 is not installed${NC}"
    echo -e "${YELLOW}Please install Python 3.8 or higher${NC}"
    exit 1
fi

# Check pip
if command -v pip3 &>/dev/null; then
    PIP_VERSION=$(pip3 --version | cut -d ' ' -f 2)
    echo -e "${GREEN}✓ pip $PIP_VERSION is installed${NC}"
else
    echo -e "${RED}✗ pip is not installed${NC}"
    echo -e "${YELLOW}Please install pip${NC}"
    exit 1
fi

# Check Node.js
if command -v node &>/dev/null; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✓ Node.js $NODE_VERSION is installed${NC}"
else
    echo -e "${RED}✗ Node.js is not installed${NC}"
    echo -e "${YELLOW}Please install Node.js 16 or higher${NC}"
    exit 1
fi

# Check npm
if command -v npm &>/dev/null; then
    NPM_VERSION=$(npm --version)
    echo -e "${GREEN}✓ npm $NPM_VERSION is installed${NC}"
else
    echo -e "${RED}✗ npm is not installed${NC}"
    echo -e "${YELLOW}Please install npm${NC}"
    exit 1
fi

# Step 2: Create Python virtual environment
echo -e "\n${YELLOW}Step 2: Setting up Python virtual environment...${NC}"
if [ -d "$SCRIPT_DIR/venv" ]; then
    echo -e "${GREEN}✓ Virtual environment already exists${NC}"
else
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv "$SCRIPT_DIR/venv"
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ Failed to create virtual environment${NC}"
        echo -e "${YELLOW}Please install python3-venv:${NC} sudo apt install python3-venv"
        exit 1
    fi
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source "$SCRIPT_DIR/venv/bin/activate"
echo -e "${GREEN}✓ Virtual environment activated${NC}"

# Step 3: Install Python dependencies
echo -e "\n${YELLOW}Step 3: Installing Python dependencies...${NC}"
pip install --upgrade pip
pip install -r "$SCRIPT_DIR/backend/requirements.txt"
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Failed to install Python dependencies${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python dependencies installed${NC}"

# Step 4: Install Node.js dependencies
echo -e "\n${YELLOW}Step 4: Installing Node.js dependencies...${NC}"
cd "$SCRIPT_DIR/frontend"
npm install
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Failed to install Node.js dependencies${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Node.js dependencies installed${NC}"
cd "$SCRIPT_DIR"

# Step 5: Create .env file
echo -e "\n${YELLOW}Step 5: Creating .env file...${NC}"
if [ -f "$SCRIPT_DIR/.env" ]; then
    # Check if SECRET_KEY already exists in .env
    if grep -q "SIEMPLY_SECRET_KEY" "$SCRIPT_DIR/.env"; then
        echo -e "${GREEN}✓ SIEMPLY_SECRET_KEY already exists in .env file${NC}"
    else
        # Generate a random secret key
        echo -e "${YELLOW}Generating a new SECRET_KEY...${NC}"
        SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')
        
        # Add SECRET_KEY to .env file
        echo "SIEMPLY_SECRET_KEY=${SECRET_KEY}" >> "$SCRIPT_DIR/.env"
        echo -e "${GREEN}✓ SIEMPLY_SECRET_KEY added to .env file${NC}"
    fi
else
    echo -e "${YELLOW}⚠ .env file not found, creating one...${NC}"
    
    # Generate a random secret key
    SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')
    
    # Create .env file with SECRET_KEY
    cat > "$SCRIPT_DIR/.env" << EOL
# SIEMply Environment Configuration
SIEMPLY_API_PORT=5000
SIEMPLY_UI_PORT=8500
SIEMPLY_DB_URI=sqlite:///backend/siemply.db
SIEMPLY_SECRET_KEY=${SECRET_KEY}
SIEMPLY_FRONTEND_URL=http://${SERVER_IP}:8500
EOL
    echo -e "${GREEN}✓ New .env file created with SECRET_KEY${NC}"
fi

# Step 6: Create frontend .env file
echo -e "\n${YELLOW}Step 6: Creating frontend .env file...${NC}"
FRONTEND_ENV_FILE="$SCRIPT_DIR/frontend/.env"

# Create .env file
cat > "$FRONTEND_ENV_FILE" << EOL
# SIEMply Frontend Environment Variables
VITE_API_URL=http://${SERVER_IP}:5000
EOL

echo -e "${GREEN}✓ Frontend .env file created with API URL: http://${SERVER_IP}:5000${NC}"

# Step 7: Create update-settings.html for localStorage
echo -e "\n${YELLOW}Step 7: Creating localStorage update page...${NC}"

# Create public directory if it doesn't exist
mkdir -p "$SCRIPT_DIR/frontend/public"

# Create update-settings.html
cat > "$SCRIPT_DIR/frontend/public/update-settings.html" << EOL
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

# Step 8: Initialize database
echo -e "\n${YELLOW}Step 8: Initializing database...${NC}"
cd "$SCRIPT_DIR"
python backend/init_db.py
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Failed to initialize database${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Database initialized${NC}"

# Step 9: Create admin user
echo -e "\n${YELLOW}Step 9: Creating admin user...${NC}"
cd "$SCRIPT_DIR"
python backend/create_admin.py --username admin --email admin@example.com --password admin123 --full-name "SIEMply Admin"
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Failed to create admin user${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Admin user created${NC}"

# Step 10: Make start scripts executable
echo -e "\n${YELLOW}Step 10: Making start scripts executable...${NC}"
chmod +x "$SCRIPT_DIR/start.sh"
chmod +x "$SCRIPT_DIR/start_backend.sh"
chmod +x "$SCRIPT_DIR/start_frontend.sh"
echo -e "${GREEN}✓ Start scripts are now executable${NC}"

echo -e "\n${GREEN}======================================${NC}"
echo -e "${GREEN}      Setup Complete!                 ${NC}"
echo -e "${GREEN}======================================${NC}"
echo -e "\nYou can now start the application:"
echo -e "  ${YELLOW}./start.sh${NC} (starts both backend and frontend)"
echo -e "  or separately:"
echo -e "  ${YELLOW}./start_backend.sh${NC} (in one terminal)"
echo -e "  ${YELLOW}./start_frontend.sh${NC} (in another terminal)"
echo -e "\nThen open the application in your browser:"
echo -e "  ${BLUE}http://${SERVER_IP}:8500${NC}"
echo -e "\nIMPORTANT: On first run, visit:"
echo -e "  ${BLUE}http://${SERVER_IP}:8500/update-settings.html${NC}"
echo -e "This will update your browser settings to connect to the API server."
echo -e "\nYou can log in with:"
echo -e "  Username: ${YELLOW}admin${NC}"
echo -e "  Password: ${YELLOW}admin123${NC}" 