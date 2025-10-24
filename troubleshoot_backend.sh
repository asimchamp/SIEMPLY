#!/bin/bash

# SIEMply Backend Troubleshooting Script
# This script helps diagnose and fix common backend connection issues

# Text colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}  SIEMply Backend Troubleshooting    ${NC}"
echo -e "${BLUE}======================================${NC}"

# Function to check if process is running
check_process() {
    local process_name=$1
    if pgrep -f "$process_name" > /dev/null; then
        echo -e "${GREEN}✓ $process_name is running${NC}"
        return 0
    else
        echo -e "${RED}✗ $process_name is not running${NC}"
        return 1
    fi
}

# Function to check port status
check_port() {
    local port=$1
    local service_name=$2
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        echo -e "${GREEN}✓ Port $port is in use by $service_name${NC}"
        return 0
    else
        echo -e "${RED}✗ Port $port is not in use${NC}"
        return 1
    fi
}

# Function to check network connectivity
check_network() {
    echo -e "\n${YELLOW}Checking network connectivity...${NC}"
    
    # Check localhost
    if ping -c 1 localhost >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Localhost connectivity OK${NC}"
    else
        echo -e "${RED}✗ Localhost connectivity failed${NC}"
    fi
    
    # Check external connectivity
    if ping -c 1 8.8.8.8 >/dev/null 2>&1; then
        echo -e "${GREEN}✓ External connectivity OK${NC}"
    else
        echo -e "${RED}✗ External connectivity failed${NC}"
    fi
}

# Function to check system resources
check_resources() {
    echo -e "\n${YELLOW}Checking system resources...${NC}"
    
    # Check memory
    local mem_usage=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
    echo -e "Memory usage: ${mem_usage}%"
    if (( $(echo "$mem_usage > 90" | bc -l) )); then
        echo -e "${RED}⚠ High memory usage detected${NC}"
    else
        echo -e "${GREEN}✓ Memory usage OK${NC}"
    fi
    
    # Check disk space
    local disk_usage=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    echo -e "Disk usage: ${disk_usage}%"
    if [ "$disk_usage" -gt 90 ]; then
        echo -e "${RED}⚠ High disk usage detected${NC}"
    else
        echo -e "${GREEN}✓ Disk usage OK${NC}"
    fi
    
    # Check open file descriptors
    local open_files=$(lsof | wc -l)
    echo -e "Open files: ${open_files}"
    if [ "$open_files" -gt 10000 ]; then
        echo -e "${RED}⚠ High number of open files${NC}"
    else
        echo -e "${GREEN}✓ Open files OK${NC}"
    fi
}

# Function to check backend logs
check_logs() {
    echo -e "\n${YELLOW}Checking backend logs...${NC}"
    
    if [ -f "backend/backend.log" ]; then
        echo -e "Recent backend errors:"
        tail -20 backend/backend.log | grep -i "error\|exception\|traceback" | tail -5 || echo "No recent errors found"
    else
        echo -e "${RED}✗ Backend log file not found${NC}"
    fi
    
    # Check system logs for SIEMply
    echo -e "\nRecent system logs for SIEMply:"
    journalctl -u siemply-backend --since "1 hour ago" | grep -i "error\|exception\|traceback" | tail -5 || echo "No systemd service found or no recent errors"
}

# Function to restart backend
restart_backend() {
    echo -e "\n${YELLOW}Restarting backend...${NC}"
    
    # Kill existing processes
    pkill -f "python main.py" 2>/dev/null || true
    sleep 2
    
    # Check if systemd service exists
    if systemctl list-unit-files | grep -q "siemply-backend"; then
        echo -e "Using systemd service..."
        systemctl restart siemply-backend
        systemctl status siemply-backend --no-pager -l
    else
        echo -e "Starting backend manually..."
        cd backend
        source ../venv/bin/activate
        export PYTHONUNBUFFERED=1
        export PYTHONPATH="/opt/SIEMPLY:$PYTHONPATH"
        nohup python main.py --port 5050 --debug > backend.log 2>&1 &
        echo "Backend started with PID: $!"
    fi
    
    # Wait and check
    sleep 5
    if check_process "python main.py"; then
        echo -e "${GREEN}✓ Backend restarted successfully${NC}"
    else
        echo -e "${RED}✗ Backend restart failed${NC}"
    fi
}

# Function to test backend connectivity
test_backend() {
    echo -e "\n${YELLOW}Testing backend connectivity...${NC}"
    
    # Test health endpoint
    if curl -s "http://localhost:5050/health" >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend health check passed${NC}"
        
        # Test root endpoint
        if curl -s "http://localhost:5050/" >/dev/null 2>&1; then
            echo -e "${GREEN}✓ Backend root endpoint accessible${NC}"
        else
            echo -e "${RED}✗ Backend root endpoint failed${NC}"
        fi
    else
        echo -e "${RED}✗ Backend health check failed${NC}"
    fi
}

# Function to show connection statistics
show_connections() {
    echo -e "\n${YELLOW}Connection statistics...${NC}"
    
    # Show active connections
    echo -e "Active TCP connections:"
    ss -tuln | grep :5050 || echo "No connections on port 5050"
    
    # Show connection count
    local conn_count=$(ss -s | grep "TCP:" | awk '{print $2}' | sed 's/,//')
    echo -e "Total TCP connections: ${conn_count}"
    
    # Show process file descriptors
    local backend_pid=$(pgrep -f "python main.py")
    if [ -n "$backend_pid" ]; then
        local fd_count=$(ls /proc/$backend_pid/fd 2>/dev/null | wc -l)
        echo -e "Backend file descriptors: ${fd_count}"
    fi
}

# Main troubleshooting flow
main() {
    echo -e "\n${YELLOW}Starting comprehensive backend diagnosis...${NC}"
    
    # Check processes
    echo -e "\n${YELLOW}Checking running processes...${NC}"
    check_process "python main.py"
    
    # Check ports
    echo -e "\n${YELLOW}Checking port usage...${NC}"
    check_port 5050 "Backend"
    
    # Check network
    check_network
    
    # Check resources
    check_resources
    
    # Check logs
    check_logs
    
    # Show connections
    show_connections
    
    # Test connectivity
    test_backend
    
    echo -e "\n${BLUE}======================================${NC}"
    echo -e "${BLUE}  Troubleshooting Complete           ${NC}"
    echo -e "${BLUE}======================================${NC}"
    
    # Ask if user wants to restart
    echo -e "\n${YELLOW}Would you like to restart the backend? (y/n)${NC}"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        restart_backend
        echo -e "\n${YELLOW}Testing after restart...${NC}"
        sleep 3
        test_backend
    fi
    
    echo -e "\n${GREEN}Troubleshooting complete. Check the output above for issues.${NC}"
}

# Run main function
main
