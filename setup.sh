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

# Check and install curl (needed for NodeSource setup)
if ! command -v curl &>/dev/null; then
    echo -e "${YELLOW}✗ curl is not installed${NC}"
    if [ "$IS_ROOT" = true ]; then
        echo -e "${YELLOW}Installing curl...${NC}"
        if [ "$OS_FAMILY" == "debian" ]; then
            apt-get update && apt-get install -y curl
        else
            $PKG_MANAGER install -y curl
        fi
        
        if command -v curl &>/dev/null; then
            echo -e "${GREEN}✓ curl installed successfully${NC}"
        fi
    fi
fi

# Check and install sqlite3 (needed for database validation)
if ! command -v sqlite3 &>/dev/null; then
    echo -e "${YELLOW}✗ sqlite3 is not installed${NC}"
    if [ "$IS_ROOT" = true ]; then
        echo -e "${YELLOW}Installing sqlite3...${NC}"
        if [ "$OS_FAMILY" == "debian" ]; then
            apt-get install -y sqlite3
        else
            $PKG_MANAGER install -y sqlite
        fi
        
        if command -v sqlite3 &>/dev/null; then
            echo -e "${GREEN}✓ sqlite3 installed successfully${NC}"
        fi
    fi
else
    echo -e "${GREEN}✓ sqlite3 is installed${NC}"
fi

# Check Python
if command -v python3 &>/dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d ' ' -f 2)
    echo -e "${GREEN}✓ Python $PYTHON_VERSION is installed${NC}"
else
    echo -e "${YELLOW}✗ Python 3 is not installed${NC}"
    
    if [ "$IS_ROOT" = true ]; then
        echo -e "${YELLOW}Installing Python 3 automatically...${NC}"
        
        if [ "$OS_FAMILY" == "debian" ]; then
            apt-get update
            apt-get install -y python3 python3-pip python3-venv
        else
            $PKG_MANAGER install -y python3 python3-pip python3-devel
        fi
        
        if [ $? -ne 0 ]; then
            echo -e "${RED}✗ Failed to install Python 3${NC}"
            exit 1
        fi
        
        # Verify installation
        if command -v python3 &>/dev/null; then
            PYTHON_VERSION=$(python3 --version | cut -d ' ' -f 2)
            echo -e "${GREEN}✓ Python $PYTHON_VERSION installed successfully${NC}"
        else
            echo -e "${RED}✗ Python installation verification failed${NC}"
            exit 1
        fi
    else
        echo -e "${RED}✗ Cannot install Python automatically (not running as root)${NC}"
        echo -e "${YELLOW}Please install Python 3.8 or higher manually${NC}"
        exit 1
    fi
fi

# Check Node.js
if command -v node &>/dev/null; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✓ Node.js $NODE_VERSION is installed${NC}"
else
    echo -e "${YELLOW}✗ Node.js is not installed${NC}"
    
    if [ "$IS_ROOT" = true ]; then
        echo -e "${YELLOW}Installing Node.js automatically...${NC}"
        
        if [ "$OS_FAMILY" == "debian" ]; then
            # Install Node.js on Debian/Ubuntu using NodeSource repository
            echo -e "${YELLOW}Adding NodeSource repository...${NC}"
            curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
            if [ $? -ne 0 ]; then
                echo -e "${RED}✗ Failed to add NodeSource repository${NC}"
                exit 1
            fi
            
            echo -e "${YELLOW}Installing Node.js via apt...${NC}"
            apt-get install -y nodejs
            if [ $? -ne 0 ]; then
                echo -e "${RED}✗ Failed to install Node.js${NC}"
                exit 1
            fi
        else
            # Install Node.js on RedHat/CentOS/Fedora
            echo -e "${YELLOW}Installing Node.js via $PKG_MANAGER...${NC}"
            
            # For RHEL 9/CentOS 9, nodejs is available in default repos
            # For RHEL 8/CentOS 8, we may need to enable module
            if [[ "$OS_VERSION" == "9"* ]]; then
                $PKG_MANAGER install -y nodejs npm
            elif [[ "$OS_VERSION" == "8"* ]]; then
                # Enable nodejs:18 module stream for RHEL/CentOS 8
                $PKG_MANAGER module reset -y nodejs
                $PKG_MANAGER module enable -y nodejs:18
                $PKG_MANAGER install -y nodejs npm
            else
                # For RHEL 7 or Fedora, use EPEL or direct install
                if [[ "$OS_NAME" == "fedora" ]]; then
                    $PKG_MANAGER install -y nodejs npm
                else
                    # RHEL 7 - use NodeSource
                    curl -fsSL https://rpm.nodesource.com/setup_18.x | bash -
                    $PKG_MANAGER install -y nodejs
                fi
            fi
            
            if [ $? -ne 0 ]; then
                echo -e "${RED}✗ Failed to install Node.js${NC}"
                echo -e "${YELLOW}You may need to manually install Node.js 16 or higher${NC}"
                exit 1
            fi
        fi
        
        # Verify installation
        if command -v node &>/dev/null; then
            NODE_VERSION=$(node --version)
            echo -e "${GREEN}✓ Node.js $NODE_VERSION installed successfully${NC}"
        else
            echo -e "${RED}✗ Node.js installation verification failed${NC}"
            exit 1
        fi
    else
        echo -e "${RED}✗ Cannot install Node.js automatically (not running as root)${NC}"
        echo -e "${YELLOW}Please install Node.js 16 or higher manually:${NC}"
        
        if [ "$OS_FAMILY" == "debian" ]; then
            echo -e "  ${BLUE}curl -fsSL https://deb.nodesource.com/setup_18.x | sudo bash -${NC}"
            echo -e "  ${BLUE}sudo apt-get install -y nodejs${NC}"
        else
            if [[ "$OS_VERSION" == "9"* ]]; then
                echo -e "  ${BLUE}sudo $PKG_MANAGER install -y nodejs npm${NC}"
            elif [[ "$OS_VERSION" == "8"* ]]; then
                echo -e "  ${BLUE}sudo $PKG_MANAGER module enable -y nodejs:18${NC}"
                echo -e "  ${BLUE}sudo $PKG_MANAGER install -y nodejs npm${NC}"
            else
                echo -e "  ${BLUE}curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash -${NC}"
                echo -e "  ${BLUE}sudo $PKG_MANAGER install -y nodejs${NC}"
            fi
        fi
        exit 1
    fi
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

# Check for existing database file and validate it
DB_FILE="$SCRIPT_DIR/backend/siemply.db"
if [ -f "$DB_FILE" ]; then
    echo -e "${YELLOW}Existing database file found. Validating...${NC}"
    
    # Try to validate the database file
    if ! sqlite3 "$DB_FILE" "PRAGMA integrity_check;" &>/dev/null; then
        echo -e "${YELLOW}⚠ Database file is corrupted or invalid${NC}"
        echo -e "${YELLOW}Backing up and removing corrupted database...${NC}"
        
        # Backup the corrupted file with timestamp
        TIMESTAMP=$(date +%Y%m%d_%H%M%S)
        mv "$DB_FILE" "${DB_FILE}.corrupted.${TIMESTAMP}.bak" 2>/dev/null || rm -f "$DB_FILE"
        
        if [ -f "${DB_FILE}.corrupted.${TIMESTAMP}.bak" ]; then
            echo -e "${GREEN}✓ Corrupted database backed up as: siemply.db.corrupted.${TIMESTAMP}.bak${NC}"
        else
            echo -e "${GREEN}✓ Corrupted database removed${NC}"
        fi
    else
        echo -e "${YELLOW}Database file exists and appears valid. Backing up...${NC}"
        TIMESTAMP=$(date +%Y%m%d_%H%M%S)
        cp "$DB_FILE" "${DB_FILE}.backup.${TIMESTAMP}"
        echo -e "${GREEN}✓ Database backed up as: siemply.db.backup.${TIMESTAMP}${NC}"
    fi
fi

# Ensure backend directory exists
mkdir -p "$SCRIPT_DIR/backend"

# Initialize the database
cd "$SCRIPT_DIR"
python backend/init_db.py
if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Failed to initialize database${NC}"
    echo -e "${YELLOW}Trying to remove database file and retry...${NC}"
    rm -f "$DB_FILE"
    python backend/init_db.py
    if [ $? -ne 0 ]; then
        echo -e "${RED}✗ Failed to initialize database after retry${NC}"
        exit 1
    fi
fi

# Verify database was created successfully
if [ -f "$DB_FILE" ]; then
    # Check if database is valid
    if sqlite3 "$DB_FILE" "SELECT name FROM sqlite_master WHERE type='table' LIMIT 1;" &>/dev/null; then
        echo -e "${GREEN}✓ Database initialized and validated successfully${NC}"
    else
        echo -e "${RED}✗ Database file created but validation failed${NC}"
        exit 1
    fi
else
    echo -e "${RED}✗ Database file was not created${NC}"
    exit 1
fi

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