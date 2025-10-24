#!/bin/bash

# SIEMply Start Script
# This script starts both backend and frontend servers

# Text colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print header
echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}  SIEMply Start Script               ${NC}"
echo -e "${BLUE}======================================${NC}"

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Get server IP address
SERVER_IP=$(hostname -I | awk '{print $1}')
if [ -z "$SERVER_IP" ]; then
    SERVER_IP="localhost"
fi

echo -e "\n${YELLOW}Starting SIEMply servers...${NC}"

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

# Start backend server
echo -e "\n${YELLOW}Starting backend server...${NC}"
source "$SCRIPT_DIR/venv/bin/activate"
cd "$SCRIPT_DIR/backend"
python main.py --port 5050 &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 2

# Start frontend server
echo -e "\n${YELLOW}Starting frontend server...${NC}"
cd "$SCRIPT_DIR/frontend"
npm run dev -- --port 8500 --host 0.0.0.0 &
FRONTEND_PID=$!

# Wait a moment for frontend to start
sleep 3

echo -e "\n${GREEN}======================================${NC}"
echo -e "${GREEN}      SIEMply is running!             ${NC}"
echo -e "${GREEN}======================================${NC}"
echo -e "\nFrontend: ${BLUE}http://${SERVER_IP}:8500${NC}"
echo -e "Backend:  ${BLUE}http://${SERVER_IP}:5050${NC}"
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

# Wait for background processes
wait
