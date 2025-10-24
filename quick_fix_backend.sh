#!/bin/bash

# SIEMply Quick Backend Fix
# This script quickly fixes the TCP transport error

echo "🔧 Quick fixing backend TCP transport error..."

# Kill all existing backend processes
echo "Stopping existing backend processes..."
pkill -f "python main.py" 2>/dev/null || true
pkill -f "uvicorn" 2>/dev/null || true

# Wait for processes to stop
sleep 3

# Clear any stuck connections
echo "Clearing network connections..."
ss -K dst :5050 2>/dev/null || true

# Start backend with improved configuration
echo "Starting backend with improved configuration..."
cd backend
source ../venv/bin/activate

# Set environment variables for stability
export PYTHONUNBUFFERED=1
export PYTHONPATH="/opt/SIEMPLY:$PYTHONPATH"

# Start backend in background with logging
nohup python main.py --port 5050 --debug > ../backend.log 2>&1 &
BACKEND_PID=$!

echo "Backend started with PID: $BACKEND_PID"

# Wait for backend to be ready
echo "Waiting for backend to be ready..."
for i in {1..20}; do
    if curl -s "http://localhost:5050/health" >/dev/null 2>&1; then
        echo "✅ Backend is ready and responding!"
        echo "Health check: http://localhost:5050/health"
        echo "Logs: backend/backend.log"
        exit 0
    fi
    sleep 1
done

echo "❌ Backend failed to start properly. Check backend.log for details."
exit 1
