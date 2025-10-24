#!/bin/bash

# SIEMply Backend Startup Script
# Single comprehensive script for starting the backend server with enhanced stability

# Text colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print header
echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}     SIEMply Backend Startup        ${NC}"
echo -e "${BLUE}======================================${NC}"

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}Virtual environment not found. Please run setup_siemply.sh first.${NC}"
    exit 1
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
echo -e "${GREEN}Using Python: $PYTHON_VERSION${NC}"

# Check if required packages are installed
echo -e "${YELLOW}Checking required packages...${NC}"
if ! python3 -c "import fastapi, uvicorn" 2>/dev/null; then
    echo -e "${RED}Required packages not found. Installing...${NC}"
    pip install -r backend/requirements.txt
fi

# Check if backend directory exists
if [ ! -d "backend" ]; then
    echo -e "${RED}Backend directory not found.${NC}"
    exit 1
fi

# Set environment variables
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"
export SIEMPLY_API_PORT=${SIEMPLY_API_PORT:-5050}
export SIEMPLY_UI_PORT=${SIEMPLY_UI_PORT:-8500}

echo -e "${GREEN}Environment configured:${NC}"
echo -e "  API Port: $SIEMPLY_API_PORT"
echo -e "  UI Port: $SIEMPLY_UI_PORT"
echo -e "  Python Path: $PYTHONPATH"

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}Shutting down SIEMply backend...${NC}"
    if [ ! -z "$BACKEND_PID" ]; then
        echo -e "${YELLOW}Stopping backend process (PID: $BACKEND_PID)...${NC}"
        kill -TERM "$BACKEND_PID" 2>/dev/null
        wait "$BACKEND_PID" 2>/dev/null
    fi
    echo -e "${GREEN}Backend stopped.${NC}"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM EXIT

# Start the backend server with enhanced configuration
echo -e "${YELLOW}Starting SIEMply backend server...${NC}"
echo -e "${BLUE}Server will be available at: http://0.0.0.0:$SIEMPLY_API_PORT${NC}"
echo -e "${BLUE}Health check: http://0.0.0.0:$SIEMPLY_API_PORT/health${NC}"
echo -e "${BLUE}Connection health: http://0.0.0.0:$SIEMPLY_API_PORT/health/connection${NC}"
echo -e "${BLUE}Press Ctrl+C to stop the server${NC}"
echo -e "${BLUE}======================================${NC}"

# Start the server with enhanced uvicorn configuration
python3 -m uvicorn backend.main:app \
    --host 0.0.0.0 \
    --port $SIEMPLY_API_PORT \
    --reload \
    --log-level info \
    --timeout-keep-alive 60 \
    --timeout-graceful-shutdown 60 \
    --access-log \
    --limit-concurrency 50 \
    --limit-max-requests 500 \
    --workers 1 \
    --loop asyncio &
BACKEND_PID=$!

# Wait for the server to start
echo -e "${YELLOW}Waiting for server to start...${NC}"
sleep 5

# Check if server is running
if kill -0 "$BACKEND_PID" 2>/dev/null; then
    echo -e "${GREEN}✓ Backend server started successfully (PID: $BACKEND_PID)${NC}"
    
    # Test the health endpoint
    echo -e "${YELLOW}Testing server health...${NC}"
    if curl -s "http://localhost:$SIEMPLY_API_PORT/health" >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Server is responding to health checks${NC}"
    else
        echo -e "${YELLOW}⚠ Server started but health check failed${NC}"
    fi
    
    # Test connection health endpoint
    if curl -s "http://localhost:$SIEMPLY_API_PORT/health/connection" >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Connection health check passed${NC}"
    else
        echo -e "${YELLOW}⚠ Connection health check failed${NC}"
    fi
    
    # Keep the script running
    echo -e "${GREEN}Server is running. Press Ctrl+C to stop.${NC}"
    wait "$BACKEND_PID"
else
    echo -e "${RED}✗ Failed to start backend server${NC}"
    exit 1
fi
