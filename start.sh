#!/bin/bash

# SIEMply Start Script
# Starts both the backend and frontend servers

# Text colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Get server IP address
SERVER_IP=$(hostname -I | awk '{print $1}')
if [ -z "$SERVER_IP" ]; then
    SERVER_IP="localhost"
fi

# Start backend
echo "Starting SIEMply Backend..."
cd "$SCRIPT_DIR"
source venv/bin/activate 2>/dev/null || true
cd backend
python main.py --host 0.0.0.0 > ../backend.log 2>&1 &
BACKEND_PID=$!

# Initialize database if needed
echo "Initializing database..."
cd "$SCRIPT_DIR"
python backend/init_db.py

# Start frontend
echo "Starting SIEMply Frontend..."
cd "$SCRIPT_DIR/frontend"
npm run dev -- --port 8500 --host 0.0.0.0 > ../frontend.log 2>&1 &
FRONTEND_PID=$!

# Wait a moment to ensure processes have started
sleep 2

# Check if processes are running
if ps -p $BACKEND_PID > /dev/null; then
    BACKEND_RUNNING=true
else
    BACKEND_RUNNING=false
    echo -e "${RED}✗ Backend failed to start. Check backend.log for errors.${NC}"
fi

if ps -p $FRONTEND_PID > /dev/null; then
    FRONTEND_RUNNING=true
else
    FRONTEND_RUNNING=false
    echo -e "${RED}✗ Frontend failed to start. Check frontend.log for errors.${NC}"
fi

if [ "$BACKEND_RUNNING" = true ] && [ "$FRONTEND_RUNNING" = true ]; then
    echo "Both servers are running."
    echo -e "Frontend should be accessible at: ${BLUE}http://${SERVER_IP}:8500${NC}"
    echo -e "Backend should be accessible at: ${BLUE}http://${SERVER_IP}:5000${NC}"
    echo "Press Ctrl+C to stop."
    
    # Save PIDs to file for later cleanup
    echo "$BACKEND_PID $FRONTEND_PID" > "$SCRIPT_DIR/.siemply_pids"
    
    # Wait for Ctrl+C
    trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; rm -f $SCRIPT_DIR/.siemply_pids; echo -e '\nStopping servers...'; exit 0" INT
    wait
else
    # Clean up if something failed
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 1
fi 