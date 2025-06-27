#!/bin/bash

# SIEMply Setup Script
# This script sets up the SIEMply environment and applies all necessary fixes

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
FRONTEND_DIR="$SCRIPT_DIR/frontend"
BACKEND_DIR="$SCRIPT_DIR/backend"
SETTINGS_FILE="$SCRIPT_DIR/backend/config/settings.py"
MAIN_ENV_FILE="$SCRIPT_DIR/.env"

echo -e "\n${YELLOW}Installation directory:${NC} $SCRIPT_DIR"

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

# Step 1: Create main .env file with SECRET_KEY
echo -e "\n${YELLOW}Step 1: Creating main .env file...${NC}"
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
SIEMPLY_API_PORT=5050
SIEMPLY_UI_PORT=8500
SIEMPLY_DB_URI=sqlite:///backend/siemply.db
SIEMPLY_SECRET_KEY=${SECRET_KEY}
SIEMPLY_FRONTEND_URL=http://${SERVER_IP}:8500
EOL
    echo -e "${GREEN}✓ New .env file created with SECRET_KEY${NC}"
fi

# Step 2: Create frontend .env file
echo -e "\n${YELLOW}Step 2: Creating frontend .env file...${NC}"
FRONTEND_ENV_FILE="$FRONTEND_DIR/.env"

# Create frontend directory if it doesn't exist
mkdir -p "$FRONTEND_DIR"

# Create .env file
cat > "$FRONTEND_ENV_FILE" << EOL
# SIEMply Frontend Environment Variables
VITE_API_URL=http://${SERVER_IP}:5050
EOL

echo -e "${GREEN}✓ Frontend .env file created with API URL: http://${SERVER_IP}:5050${NC}"

# Step 3: Create update-settings.html for localStorage
echo -e "\n${YELLOW}Step 3: Creating localStorage update page...${NC}"

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

# Step 4: Check network binding for start scripts
echo -e "\n${YELLOW}Step 4: Checking network binding for start scripts...${NC}"

# Check frontend script
FRONTEND_SCRIPT="$SCRIPT_DIR/start_frontend.sh"
if [ -f "$FRONTEND_SCRIPT" ]; then
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
    
    cat > "$FRONTEND_SCRIPT" << EOL
#!/bin/bash
# Start SIEMply frontend server
cd frontend
npm run dev -- --port 8500 --host 0.0.0.0
EOL
    
    chmod +x "$FRONTEND_SCRIPT"
    echo -e "${GREEN}✓ New frontend script created with correct network binding${NC}"
fi

# Check backend script
BACKEND_SCRIPT="$SCRIPT_DIR/start_backend.sh"
if [ -f "$BACKEND_SCRIPT" ]; then
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
    
    cat > "$BACKEND_SCRIPT" << EOL
#!/bin/bash
# Start SIEMply backend server
source venv/bin/activate
cd backend
python main.py --host 0.0.0.0
EOL
    
    chmod +x "$BACKEND_SCRIPT"
    echo -e "${GREEN}✓ New backend script created with correct network binding${NC}"
fi

# Step 5: Create admin user
echo -e "\n${YELLOW}Step 5: Creating admin user...${NC}"
python backend/create_admin.py --username admin --email admin@example.com --password admin123 --full-name "SIEMply Admin"
echo -e "${GREEN}✓ Admin user created${NC}"

# Step 6: Fix SSH client import issue
echo -e "\n${YELLOW}Step 6: Fixing SSH client import issue...${NC}"
if [ -f "fix_ssh_client.py" ]; then
    python fix_ssh_client.py
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ SSH client import fixed${NC}"
    else
        echo -e "${RED}✗ Failed to fix SSH client import${NC}"
    fi
else
    echo -e "${RED}✗ fix_ssh_client.py not found${NC}"
fi

echo -e "\n${GREEN}======================================${NC}"
echo -e "${GREEN}      Setup Complete!                 ${NC}"
echo -e "${GREEN}======================================${NC}"
echo -e "\nYou can now start the application:"
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