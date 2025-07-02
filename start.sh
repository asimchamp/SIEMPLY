#!/bin/bash
# Start both backend and frontend servers
echo "Starting SIEMply Backend..."
/opt/SIEMPLY/start_backend.sh &
BACKEND_PID=$!

echo "Starting SIEMply Frontend..."
/opt/SIEMPLY/start_frontend.sh &
FRONTEND_PID=$!

# Get server IP address
SERVER_IP=$(hostname -I | awk '{print $1}')
if [ -z "$SERVER_IP" ]; then
    SERVER_IP="localhost"
fi

echo "Both servers are running."
echo "Frontend should be accessible at: http://$SERVER_IP:8500"
echo "Backend should be accessible at: http://$SERVER_IP:5050"
echo "Press Ctrl+C to stop."
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT TERM
wait
