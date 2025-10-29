#!/bin/bash

# SIEMply Setup Script
# This script sets up the SIEMply environment with systemctl service support
# Compatible with: Ubuntu/Debian, RHEL/CentOS/Fedora/Rocky/AlmaLinux

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

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    IS_ROOT=true
    echo -e "${YELLOW}Running as root - will install systemctl services${NC}"
else
    IS_ROOT=false
    echo -e "${YELLOW}Running as non-root user - systemctl services will not be installed${NC}"
    echo -e "${YELLOW}Run with sudo to install systemctl services${NC}"
fi

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Detect OS type
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS_NAME=$ID
    OS_VERSION=$VERSION_ID
    echo -e "\n${YELLOW}Detected OS:${NC} $NAME $VERSION"
    
    # Determine package manager
    if [[ "$OS_NAME" == "ubuntu" ]] || [[ "$OS_NAME" == "debian" ]]; then
        PKG_MANAGER="apt"
        OS_FAMILY="debian"
        echo -e "${GREEN}✓ Debian/Ubuntu-based system detected${NC}"
    elif [[ "$OS_NAME" == "rhel" ]] || [[ "$OS_NAME" == "centos" ]] || [[ "$OS_NAME" == "fedora" ]] || [[ "$OS_NAME" == "rocky" ]] || [[ "$OS_NAME" == "almalinux" ]]; then
        PKG_MANAGER="yum"
        OS_FAMILY="redhat"
        # Check if dnf is available (newer RHEL/CentOS/Fedora)
        if command -v dnf &>/dev/null; then
            PKG_MANAGER="dnf"
        fi
        echo -e "${GREEN}✓ RedHat-based system detected (using $PKG_MANAGER)${NC}"
    else
        echo -e "${YELLOW}⚠ Unknown OS: $OS_NAME. Attempting to detect package manager...${NC}"
        if command -v apt &>/dev/null; then
            PKG_MANAGER="apt"
            OS_FAMILY="debian"
        elif command -v dnf &>/dev/null; then
            PKG_MANAGER="dnf"
            OS_FAMILY="redhat"
        elif command -v yum &>/dev/null; then
            PKG_MANAGER="yum"
            OS_FAMILY="redhat"
        else
            echo -e "${RED}✗ Could not detect package manager${NC}"
            exit 1
        fi
    fi
else
    echo -e "${RED}✗ Cannot detect OS type. /etc/os-release not found.${NC}"
    exit 1
fi

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
        if [ "$OS_FAMILY" == "debian" ]; then
            echo -e "${YELLOW}Please install python3-venv:${NC} sudo apt install python3-venv"
        else
            echo -e "${YELLOW}Please install python3-devel:${NC} sudo $PKG_MANAGER install python3-devel"
        fi
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

# Step 8.5: Build frontend for production (if running as root for systemctl services)
if [ "$IS_ROOT" = true ]; then
    echo -e "\n${YELLOW}Step 8.5: Building frontend for production...${NC}"
    cd "$SCRIPT_DIR/frontend"
    npm run build
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ Failed to build frontend${NC}"
        echo -e "${YELLOW}Services will use dev mode instead${NC}"
    else
        echo -e "${GREEN}✓ Frontend built successfully${NC}"
    fi
    cd "$SCRIPT_DIR"
fi

# Step 9: Create systemctl service files (if running as root)
if [ "$IS_ROOT" = true ]; then
    echo -e "\n${YELLOW}Step 9: Creating systemctl service files...${NC}"
    
    # Create backend service file
    cat > /etc/systemd/system/siemply-backend.service << EOL
[Unit]
Description=SIEMply Backend Service
After=network.target

[Service]
Type=simple
User=${SUDO_USER:-$USER}
WorkingDirectory=$SCRIPT_DIR
Environment="PATH=$SCRIPT_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONPATH=$SCRIPT_DIR"
ExecStart=$SCRIPT_DIR/venv/bin/python $SCRIPT_DIR/backend/main.py --port 5050
Restart=always
RestartSec=10
StandardOutput=append:$SCRIPT_DIR/logs/backend.log
StandardError=append:$SCRIPT_DIR/logs/backend-error.log

# Security settings
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOL

    echo -e "${GREEN}✓ Backend service file created${NC}"
    
    # Create frontend service file
    cat > /etc/systemd/system/siemply-frontend.service << EOL
[Unit]
Description=SIEMply Frontend Service
After=network.target

[Service]
Type=simple
User=${SUDO_USER:-$USER}
WorkingDirectory=$SCRIPT_DIR/frontend
Environment="PATH=/usr/local/bin:/usr/bin:/bin"
ExecStart=/usr/bin/npm run preview -- --host 0.0.0.0 --port 8500
Restart=always
RestartSec=10
StandardOutput=append:$SCRIPT_DIR/logs/frontend.log
StandardError=append:$SCRIPT_DIR/logs/frontend-error.log

# Security settings
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOL

    echo -e "${GREEN}✓ Frontend service file created${NC}"
    
    # Create combined service file
    cat > /etc/systemd/system/siemply.service << EOL
[Unit]
Description=SIEMply Application (Backend + Frontend)
After=network.target

[Service]
Type=oneshot
ExecStart=/bin/true
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
Requires=siemply-backend.service siemply-frontend.service
EOL

    echo -e "${GREEN}✓ Combined service file created${NC}"
    
    # Create logs directory
    mkdir -p "$SCRIPT_DIR/logs"
    chown -R ${SUDO_USER:-$USER}:${SUDO_USER:-$USER} "$SCRIPT_DIR/logs"
    
    # Reload systemd
    echo -e "${YELLOW}Reloading systemd daemon...${NC}"
    systemctl daemon-reload
    
    # Ask user if they want to enable and start services
    echo -e "\n${YELLOW}Do you want to enable and start the systemctl services now? (y/n)${NC}"
    read -r ENABLE_SERVICES
    
    if [[ "$ENABLE_SERVICES" =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Enabling services...${NC}"
        systemctl enable siemply-backend.service
        systemctl enable siemply-frontend.service
        systemctl enable siemply.service
        
        echo -e "${YELLOW}Starting services...${NC}"
        systemctl start siemply-backend.service
        sleep 3
        systemctl start siemply-frontend.service
        
        echo -e "${GREEN}✓ Services enabled and started${NC}"
        
        # Check service status
        echo -e "\n${YELLOW}Service Status:${NC}"
        systemctl status siemply-backend.service --no-pager | head -5
        systemctl status siemply-frontend.service --no-pager | head -5
    else
        echo -e "${YELLOW}Services created but not enabled. You can enable them later with:${NC}"
        echo -e "  ${BLUE}sudo systemctl enable siemply-backend.service${NC}"
        echo -e "  ${BLUE}sudo systemctl enable siemply-frontend.service${NC}"
        echo -e "  ${BLUE}sudo systemctl start siemply-backend.service${NC}"
        echo -e "  ${BLUE}sudo systemctl start siemply-frontend.service${NC}"
    fi
else
    echo -e "\n${YELLOW}Step 9: Skipping systemctl service creation (not running as root)${NC}"
    echo -e "${YELLOW}To create systemctl services, run this script with sudo${NC}"
fi

echo -e "\n${GREEN}======================================${NC}"
echo -e "${GREEN}      Setup Complete!                 ${NC}"
echo -e "${GREEN}======================================${NC}"

if [ "$IS_ROOT" = true ] && [[ "$ENABLE_SERVICES" =~ ^[Yy]$ ]]; then
    echo -e "\n${GREEN}✓ Services are running!${NC}"
    echo -e "\nManage services with:"
    echo -e "  ${YELLOW}sudo systemctl status siemply-backend${NC}  - Check backend status"
    echo -e "  ${YELLOW}sudo systemctl status siemply-frontend${NC} - Check frontend status"
    echo -e "  ${YELLOW}sudo systemctl restart siemply-backend${NC} - Restart backend"
    echo -e "  ${YELLOW}sudo systemctl restart siemply-frontend${NC} - Restart frontend"
    echo -e "  ${YELLOW}sudo systemctl stop siemply${NC} - Stop all services"
    echo -e "  ${YELLOW}sudo journalctl -u siemply-backend -f${NC} - View backend logs"
else
    echo -e "\nYou can now start the application manually:"
    echo -e "  ${YELLOW}./start.sh${NC}"
fi

echo -e "\nThen open the application in your browser:"
echo -e "  ${BLUE}http://${SERVER_IP}:8500${NC}"
echo -e "\nYou can log in with:"
echo -e "  Username: ${YELLOW}admin${NC}"
echo -e "  Password: ${YELLOW}admin123${NC}"

echo -e "\n${YELLOW}Note:${NC} Logs are stored in: ${BLUE}$SCRIPT_DIR/logs/${NC}" 