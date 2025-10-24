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
    echo -e "${YELLOW}Could not automatically detect server IP. Using localhost.${NC}"
    SERVER_IP="localhost"
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

# Check Node.js
if command -v node &>/dev/null; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✓ Node.js $NODE_VERSION is installed${NC}"
else
    echo -e "${RED}✗ Node.js is not installed${NC}"
    echo -e "${YELLOW}Please install Node.js 16 or higher${NC}"
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
cd "$SCRIPT_DIR"
echo -e "${GREEN}✓ Node.js dependencies installed${NC}"

# Step 5: Create .env file
echo -e "\n${YELLOW}Step 5: Creating .env file...${NC}"
if [ -f "$SCRIPT_DIR/.env" ]; then
    echo -e "${GREEN}✓ .env file already exists${NC}"
else
    # Generate a random secret key
    SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')
    
    # Create .env file
    cat > "$SCRIPT_DIR/.env" << EOL
# SIEMply Environment Configuration
SIEMPLY_API_PORT=5050
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
VITE_API_URL=http://${SERVER_IP}:5050
EOL

echo -e "${GREEN}✓ Frontend .env file created with API URL: http://${SERVER_IP}:5050${NC}"

# Step 7: Initialize database
echo -e "\n${YELLOW}Step 7: Initializing database...${NC}"
cd "$SCRIPT_DIR"
python backend/init_db.py
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Failed to initialize database${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Database initialized${NC}"

# Step 8: Create admin user
echo -e "\n${YELLOW}Step 8: Creating admin user...${NC}"
cd "$SCRIPT_DIR"
python backend/create_admin.py --username admin --email admin@example.com --password admin123 --full-name "SIEMply Admin"
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Failed to create admin user${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Admin user created${NC}"

echo -e "\n${GREEN}======================================${NC}"
echo -e "${GREEN}      Setup Complete!                 ${NC}"
echo -e "${GREEN}======================================${NC}"
echo -e "\nYou can now start the application:"
echo -e "  ${YELLOW}./start.sh${NC}"
echo -e "\nThen open the application in your browser:"
echo -e "  ${BLUE}http://${SERVER_IP}:8500${NC}"
echo -e "\nYou can log in with:"
echo -e "  Username: ${YELLOW}admin${NC}"
echo -e "  Password: ${YELLOW}admin123${NC}" 