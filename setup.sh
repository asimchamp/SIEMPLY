#!/bin/bash

# SIEMply Project Setup Script
# This script sets up the SIEMply project environment and starts the servers

# Text colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print header
echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}      SIEMply Project Setup          ${NC}"
echo -e "${BLUE}======================================${NC}"

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

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

# Setup virtual environment
echo -e "\n${YELLOW}Setting up Python virtual environment...${NC}"
if [ -d "venv" ]; then
    echo -e "${GREEN}✓ Virtual environment already exists${NC}"
else
    echo -e "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ Failed to create virtual environment. Please install python3-venv package.${NC}"
        echo -e "${YELLOW}On Ubuntu/Debian: sudo apt install python3-venv${NC}"
        echo -e "${YELLOW}On RHEL/CentOS: sudo yum install python3-devel${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate virtual environment
echo -e "\n${YELLOW}Activating virtual environment...${NC}"
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    source venv/Scripts/activate
else
    # Linux/macOS
    source venv/bin/activate
fi
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
        sed -i.bak 's/from pydantic_settings import BaseSettings, Field/from pydantic import Field\nfrom pydantic_settings import BaseSettings/' "$SETTINGS_FILE"
        if [ $? -ne 0 ]; then
            # If sed fails (e.g., on macOS), try with different syntax
            sed -i '' 's/from pydantic_settings import BaseSettings, Field/from pydantic import Field\nfrom pydantic_settings import BaseSettings/' "$SETTINGS_FILE"
        fi
        echo -e "${GREEN}✓ Field import fixed${NC}"
    # Check if we need to fix just the BaseSettings import
    elif grep -q "from pydantic import BaseSettings" "$SETTINGS_FILE"; then
        # Update the import statement
        sed -i.bak 's/from pydantic import BaseSettings/from pydantic_settings import BaseSettings/' "$SETTINGS_FILE"
        if [ $? -ne 0 ]; then
            # If sed fails (e.g., on macOS), try with different syntax
            sed -i '' 's/from pydantic import BaseSettings/from pydantic_settings import BaseSettings/' "$SETTINGS_FILE"
        fi
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
SIEMPLY_API_PORT=5000
SIEMPLY_UI_PORT=8500
SIEMPLY_DB_URI=sqlite:///siemply.db
SIEMPLY_SECRET_KEY=${SECRET_KEY}
SIEMPLY_FRONTEND_URL=http://${SERVER_IP}:8500
EOL
    echo -e "${GREEN}✓ Default .env file created${NC}"
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
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
VITE_API_URL=http://${SERVER_IP}:5000
EOL
echo -e "${GREEN}✓ Frontend .env file created${NC}"

# Create update-settings.html for localStorage
cat > frontend/public/update-settings.html << EOL
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
source venv/bin/activate
cd backend
python main.py
EOL
chmod +x start_backend.sh

# Create start script for frontend
cat > start_frontend.sh << EOL
#!/bin/bash
# Start SIEMply frontend server
cd frontend
npm run dev -- --port 8500 --host 0.0.0.0
EOL
chmod +x start_frontend.sh

echo -e "${GREEN}✓ Start scripts created${NC}"

# Create combined start script
cat > start.sh << EOL
#!/bin/bash
# Start both backend and frontend servers
echo "Starting SIEMply Backend..."
./start_backend.sh &
BACKEND_PID=\$!

echo "Starting SIEMply Frontend..."
./start_frontend.sh &
FRONTEND_PID=\$!

# Get server IP address
SERVER_IP=\$(hostname -I | awk '{print \$1}')
if [ -z "\$SERVER_IP" ]; then
    SERVER_IP="localhost"
fi

echo "Both servers are running."
echo "Frontend should be accessible at: http://\$SERVER_IP:8500"
echo "Backend should be accessible at: http://\$SERVER_IP:5000"
echo "Press Ctrl+C to stop."
trap "kill \$BACKEND_PID \$FRONTEND_PID; exit" INT TERM
wait
EOL
chmod +x start.sh

echo -e "\n${GREEN}======================================${NC}"
echo -e "${GREEN}      Setup Complete!                ${NC}"
echo -e "${GREEN}======================================${NC}"
echo -e "\nTo start the backend server: ${YELLOW}./start_backend.sh${NC}"
echo -e "To start the frontend server: ${YELLOW}./start_frontend.sh${NC}"
echo -e "To start both servers: ${YELLOW}./start.sh${NC}"
echo -e "\nBackend will be available at: ${BLUE}http://${SERVER_IP}:5000${NC}"
echo -e "Frontend will be available at: ${BLUE}http://${SERVER_IP}:8500${NC}"
echo -e "\nIMPORTANT: On first run, visit: ${BLUE}http://${SERVER_IP}:8500/update-settings.html${NC}"
echo -e "This will update your browser settings to connect to the API server." 