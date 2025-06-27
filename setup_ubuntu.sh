#!/bin/bash

# SIEMply Project Setup Script for Ubuntu/Debian
# This script addresses the "externally-managed-environment" issue in newer Python versions

# Text colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print header
echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}  SIEMply Project Setup for Ubuntu    ${NC}"
echo -e "${BLUE}======================================${NC}"

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if running as root (needed for apt)
if [ "$EUID" -ne 0 ]; then
  echo -e "${YELLOW}This script installs system packages and requires root privileges.${NC}"
  echo -e "${YELLOW}Please run with sudo:${NC} sudo $0"
  exit 1
fi

# Check and install required system packages
echo -e "\n${YELLOW}Checking and installing required system packages...${NC}"
apt update
apt install -y python3-full python3-venv python3-pip nodejs npm

# Check if Python 3 is installed
echo -e "\n${YELLOW}Checking Python installation...${NC}"
if command -v python3 &>/dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✓ Python is installed: $PYTHON_VERSION${NC}"
else
    echo -e "${RED}✗ Python 3 is not installed. Please install Python 3.8 or higher.${NC}"
    exit 1
fi

# Check if Node.js is installed
echo -e "\n${YELLOW}Checking Node.js installation...${NC}"
if command -v node &>/dev/null; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✓ Node.js is installed: $NODE_VERSION${NC}"
else
    echo -e "${RED}✗ Node.js is not installed. Please install Node.js 16 or higher.${NC}"
    exit 1
fi

# Create project directory if it doesn't exist
if [ ! -d "/opt/SIEMPLY" ]; then
    echo -e "\n${YELLOW}Creating project directory at /opt/SIEMPLY...${NC}"
    mkdir -p /opt/SIEMPLY
    echo -e "${GREEN}✓ Project directory created${NC}"
fi

# Copy project files to installation directory
echo -e "\n${YELLOW}Copying project files to installation directory...${NC}"
cp -r * /opt/SIEMPLY/
echo -e "${GREEN}✓ Project files copied${NC}"

# Change to installation directory
cd /opt/SIEMPLY

# Setup virtual environment
echo -e "\n${YELLOW}Setting up Python virtual environment...${NC}"
if [ -d "venv" ]; then
    echo -e "${GREEN}✓ Virtual environment already exists${NC}"
else
    echo -e "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ Failed to create virtual environment.${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate virtual environment
echo -e "\n${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"

# Install backend dependencies
echo -e "\n${YELLOW}Installing backend dependencies...${NC}"
pip install -r backend/requirements.txt
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Failed to install backend dependencies${NC}"
    exit 1
fi

# Install pydantic-settings for Pydantic v2 compatibility
echo -e "\n${YELLOW}Installing pydantic-settings for Pydantic v2 compatibility...${NC}"
pip install pydantic-settings
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Failed to install pydantic-settings${NC}"
    exit 1
fi
echo -e "${GREEN}✓ pydantic-settings installed${NC}"

echo -e "${GREEN}✓ Backend dependencies installed${NC}"

# Fix BaseSettings import in settings.py
echo -e "\n${YELLOW}Fixing BaseSettings import in settings.py...${NC}"
SETTINGS_FILE="backend/config/settings.py"
if [ -f "$SETTINGS_FILE" ]; then
    # Create a backup of the original file
    cp "$SETTINGS_FILE" "${SETTINGS_FILE}.bak"
    
    # Check if we need to fix the Field import
    if grep -q "from pydantic_settings import BaseSettings, Field" "$SETTINGS_FILE"; then
        # Update the import statements
        sed -i 's/from pydantic_settings import BaseSettings, Field/from pydantic import Field\nfrom pydantic_settings import BaseSettings/' "$SETTINGS_FILE"
        echo -e "${GREEN}✓ Field import fixed${NC}"
    # Check if we need to fix just the BaseSettings import
    elif grep -q "from pydantic import BaseSettings" "$SETTINGS_FILE"; then
        # Update the import statement
        sed -i 's/from pydantic import BaseSettings/from pydantic_settings import BaseSettings/' "$SETTINGS_FILE"
        echo -e "${GREEN}✓ BaseSettings import fixed${NC}"
    else
        echo -e "${GREEN}✓ Imports already correct${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Settings file not found at $SETTINGS_FILE${NC}"
fi

# Install frontend dependencies
echo -e "\n${YELLOW}Installing frontend dependencies...${NC}"
cd frontend
npm install
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Failed to install frontend dependencies${NC}"
    exit 1
fi
cd ..
echo -e "${GREEN}✓ Frontend dependencies installed${NC}"

# Check if .env file exists, create if not
echo -e "\n${YELLOW}Checking environment configuration...${NC}"
if [ ! -f ".env" ]; then
    echo -e "Creating default .env file..."
    # Generate a random secret key
    SECRET_KEY=$(openssl rand -hex 32)
    
    # Get server IP address
    SERVER_IP=$(hostname -I | awk '{print $1}')
    if [ -z "$SERVER_IP" ]; then
        SERVER_IP="localhost"
    fi
    
    cat > .env << EOL
# SIEMply Environment Configuration
SIEMPLY_API_PORT=5050
SIEMPLY_UI_PORT=8500
SIEMPLY_DB_URI=sqlite:////opt/SIEMPLY/backend/siemply.db
SIEMPLY_SECRET_KEY=${SECRET_KEY}
SIEMPLY_FRONTEND_URL=http://${SERVER_IP}:8500
EOL
    echo -e "${GREEN}✓ Default .env file created${NC}"
else
    # Update DB_URI in existing .env file
    sed -i 's|SIEMPLY_DB_URI=.*|SIEMPLY_DB_URI=sqlite:////opt/SIEMPLY/backend/siemply.db|' .env
    # Update API port to avoid conflicts
    sed -i 's|SIEMPLY_API_PORT=.*|SIEMPLY_API_PORT=5050|' .env
    echo -e "${GREEN}✓ Updated .env file${NC}"
fi

# Configure frontend API connection
echo -e "\n${YELLOW}Configuring frontend API connection...${NC}"
# Get server IP address
SERVER_IP=$(hostname -I | awk '{print $1}')
if [ -z "$SERVER_IP" ]; then
    SERVER_IP="localhost"
fi

# Add FRONTEND_URL to .env if not already present
if ! grep -q "SIEMPLY_FRONTEND_URL" .env; then
    echo "SIEMPLY_FRONTEND_URL=http://${SERVER_IP}:8500" >> .env
    echo -e "${GREEN}✓ Added FRONTEND_URL to .env file${NC}"
fi

# Create .env file for frontend
mkdir -p frontend
cat > frontend/.env << EOL
# SIEMply Frontend Environment Variables
VITE_API_URL=http://${SERVER_IP}:5050
EOL
echo -e "${GREEN}✓ Frontend .env file created${NC}"

# Create update-settings.html for localStorage
mkdir -p frontend/public
cat > frontend/public/update-settings.html << EOL
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
            apiUrl: 'http://${SERVER_IP}:5050',
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

# Create database directory and set permissions
echo -e "\n${YELLOW}Setting up database directory...${NC}"
mkdir -p /opt/SIEMPLY/backend
touch /opt/SIEMPLY/backend/siemply.db
chmod 777 /opt/SIEMPLY/backend/siemply.db
echo -e "${GREEN}✓ Database file created with proper permissions${NC}"

# Initialize database
echo -e "\n${YELLOW}Initializing database...${NC}"
cd backend
python init_db.py
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Failed to initialize database${NC}"
    exit 1
fi
cd ..
echo -e "${GREEN}✓ Database initialized${NC}"

# Create start script for backend
echo -e "\n${YELLOW}Creating start scripts...${NC}"
cat > start_backend.sh << EOL
#!/bin/bash
# Start SIEMply backend server
source /opt/SIEMPLY/venv/bin/activate
cd /opt/SIEMPLY/backend
python main.py --port 5050
EOL
chmod +x start_backend.sh

# Create start script for frontend
cat > start_frontend.sh << EOL
#!/bin/bash
# Start SIEMply frontend server
cd /opt/SIEMPLY/frontend
npm run dev -- --port 8500 --host 0.0.0.0
EOL
chmod +x start_frontend.sh

# Create combined start script
cat > start.sh << EOL
#!/bin/bash
# Start both backend and frontend servers
echo "Starting SIEMply Backend..."
/opt/SIEMPLY/start_backend.sh &
BACKEND_PID=\$!

echo "Starting SIEMply Frontend..."
/opt/SIEMPLY/start_frontend.sh &
FRONTEND_PID=\$!

# Get server IP address
SERVER_IP=\$(hostname -I | awk '{print \$1}')
if [ -z "\$SERVER_IP" ]; then
    SERVER_IP="localhost"
fi

echo "Both servers are running."
echo "Frontend should be accessible at: http://\$SERVER_IP:8500"
echo "Backend should be accessible at: http://\$SERVER_IP:5050"
echo "Press Ctrl+C to stop."
trap "kill \$BACKEND_PID \$FRONTEND_PID; exit" INT TERM
wait
EOL
chmod +x start.sh

# Create systemd service for SIEMply
echo -e "\n${YELLOW}Creating systemd service...${NC}"
cat > /etc/systemd/system/siemply.service << EOL
[Unit]
Description=SIEMply - SIEM Installation & Management System
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/SIEMPLY
ExecStart=/opt/SIEMPLY/start.sh
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOL

# Reload systemd
systemctl daemon-reload
echo -e "${GREEN}✓ Systemd service created${NC}"

# Set proper permissions
echo -e "\n${YELLOW}Setting proper permissions...${NC}"
chown -R root:root /opt/SIEMPLY
chmod +x /opt/SIEMPLY/*.sh
# Ensure database directory is writable
chmod -R 755 /opt/SIEMPLY/backend
echo -e "${GREEN}✓ Permissions set${NC}"

echo -e "\n${GREEN}======================================${NC}"
echo -e "${GREEN}      Setup Complete!                ${NC}"
echo -e "${GREEN}======================================${NC}"
echo -e "\nTo start the services manually:"
echo -e "  Backend: ${YELLOW}/opt/SIEMPLY/start_backend.sh${NC}"
echo -e "  Frontend: ${YELLOW}/opt/SIEMPLY/start_frontend.sh${NC}"
echo -e "  Both: ${YELLOW}/opt/SIEMPLY/start.sh${NC}"
echo -e "\nTo start as a system service:"
echo -e "  ${YELLOW}systemctl start siemply${NC}"
echo -e "\nTo enable automatic start on boot:"
echo -e "  ${YELLOW}systemctl enable siemply${NC}"
echo -e "\nBackend will be available at: ${BLUE}http://${SERVER_IP}:5050${NC}"
echo -e "Frontend will be available at: ${BLUE}http://${SERVER_IP}:8500${NC}"
echo -e "\nIMPORTANT: On first run, visit: ${BLUE}http://${SERVER_IP}:8500/update-settings.html${NC}"
echo -e "This will update your browser settings to connect to the API server." 