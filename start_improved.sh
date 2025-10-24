#!/bin/bash

# SIEMply Improved Start Script
# This script starts both backend and frontend servers with better error handling

# Text colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print header
echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}  SIEMply Improved Start Script      ${NC}"
echo -e "${BLUE}======================================${NC}"

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Get server IP address
SERVER_IP=$(hostname -I | awk '{print $1}')
if [ -z "$SERVER_IP" ]; then
    SERVER_IP="localhost"
fi

echo -e "\n${YELLOW}Starting SIEMply servers with improved error handling...${NC}"

# Check if virtual environment exists
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    echo -e "${RED}✗ Virtual environment not found. Please run ./setup.sh first.${NC}"
    exit 1
fi

# Check if .env file exists
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    echo -e "${RED}✗ .env file not found. Please run ./setup.sh first.${NC}"
    exit 1
fi

# Function to check if port is available
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${RED}✗ Port $port is already in use${NC}"
        return 1
    fi
    return 0
}

# Check ports before starting
echo -e "\n${YELLOW}Checking port availability...${NC}"
if ! check_port 5050; then
    echo -e "${YELLOW}Attempting to kill existing backend process...${NC}"
    pkill -f "python main.py" 2>/dev/null || true
    sleep 2
    if ! check_port 5050; then
        echo -e "${RED}✗ Cannot free port 5050. Please check manually.${NC}"
        exit 1
    fi
fi

if ! check_port 8500; then
    echo -e "${YELLOW}Attempting to kill existing frontend process...${NC}"
    pkill -f "npm run dev" 2>/dev/null || true
    sleep 2
    if ! check_port 8500; then
        echo -e "${RED}✗ Cannot free port 8500. Please check manually.${NC}"
        exit 1
    fi
fi

# Start backend server with improved configuration
echo -e "\n${YELLOW}Starting backend server...${NC}"
source "$SCRIPT_DIR/venv/bin/activate"
cd "$SCRIPT_DIR/backend"

# Set environment variables for better stability
export PYTHONUNBUFFERED=1
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"

# Start backend with better error handling and logging
python main.py --port 5050 --debug > backend.log 2>&1 &
BACKEND_PID=$!

# Wait and check if backend started successfully
sleep 3
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo -e "${RED}✗ Backend failed to start. Check backend.log for details.${NC}"
    exit 1
fi

# Check if backend is responding
echo -e "${YELLOW}Waiting for backend to be ready...${NC}"
for i in {1..30}; do
    if curl -s "http://localhost:5050/health" >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend is ready${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}✗ Backend failed to respond after 30 seconds${NC}"
        kill $BACKEND_PID 2>/dev/null
        exit 1
    fi
    sleep 1
done

# Start frontend server
echo -e "\n${YELLOW}Starting frontend server...${NC}"
cd "$SCRIPT_DIR/frontend"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing frontend dependencies...${NC}"
    npm install
fi

# Start frontend with better error handling
npm run dev -- --port 8500 --host 0.0.0.0 > frontend.log 2>&1 &
FRONTEND_PID=$!

# Wait and check if frontend started successfully
sleep 5
if ! kill -0 $FRONTEND_PID 2>/dev/null; then
    echo -e "${RED}✗ Frontend failed to start. Check frontend.log for details.${NC}"
    kill $BACKEND_PID 2>/dev/null
    exit 1
fi

# Check if frontend is responding
echo -e "${YELLOW}Waiting for frontend to be ready...${NC}"
for i in {1..30}; do
    if curl -s "http://localhost:8500" >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Frontend is ready${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}✗ Frontend failed to respond after 30 seconds${NC}"
        kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
        exit 1
    fi
    sleep 1
done

echo -e "\n${GREEN}======================================${NC}"
echo -e "${GREEN}      SIEMply is running!             ${NC}"
echo -e "${GREEN}======================================${NC}"
echo -e "\nFrontend: ${BLUE}http://${SERVER_IP}:8500${NC}"
echo -e "Backend:  ${BLUE}http://${SERVER_IP}:5050${NC}"
echo -e "Health:   ${BLUE}http://${SERVER_IP}:5050/health${NC}"
echo -e "\nLogs:"
echo -e "  Backend:  ${YELLOW}backend/backend.log${NC}"
echo -e "  Frontend: ${YELLOW}frontend/frontend.log${NC}"
echo -e "\nLogin credentials:"
echo -e "  Username: ${YELLOW}admin${NC}"
echo -e "  Password: ${YELLOW}admin123${NC}"
echo -e "\nPress ${YELLOW}Ctrl+C${NC} to stop both servers."

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}Stopping servers...${NC}"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    echo -e "${GREEN}✓ Servers stopped${NC}"
    exit 0
}

# Set trap to cleanup on exit
trap cleanup INT TERM

# Function to monitor server health
monitor_servers() {
    while true; do
        sleep 30
        # Check backend health
        if ! curl -s "http://localhost:5050/health" >/dev/null 2>&1; then
            echo -e "${RED}⚠ Backend health check failed${NC}"
        fi
        # Check if processes are still running
        if ! kill -0 $BACKEND_PID 2>/dev/null; then
            echo -e "${RED}✗ Backend process died unexpectedly${NC}"
            break
        fi
        if ! kill -0 $FRONTEND_PID 2>/dev/null; then
            echo -e "${RED}✗ Frontend process died unexpectedly${NC}"
            break
        fi
    done
}

# Start monitoring in background
monitor_servers &
MONITOR_PID=$!

# Wait for background processes
wait

# Cleanup monitoring
kill $MONITOR_PID 2>/dev/null
cleanup
