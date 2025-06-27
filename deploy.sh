#!/bin/bash
# Deployment script for SIEMply

# Configuration
REMOTE_HOST="root@192.168.100.45"
REMOTE_PATH="/opt/SIEMPLY"

echo "Deploying SIEMply to $REMOTE_HOST:$REMOTE_PATH"

# Copy the SSH client fix
echo "Copying SSH client fix..."
scp backend/automation/ssh_client.py $REMOTE_HOST:$REMOTE_PATH/backend/automation/

# Copy the database initialization script
echo "Copying database initialization script..."
scp backend/init_db.py $REMOTE_HOST:$REMOTE_PATH/backend/

# Copy the authentication context fix
echo "Copying authentication context fix..."
scp frontend/src/services/authContext.tsx $REMOTE_HOST:$REMOTE_PATH/frontend/src/services/

# Copy the main.py with CORS fix
echo "Copying main.py with CORS fix..."
scp backend/main.py $REMOTE_HOST:$REMOTE_PATH/backend/

# Run the database initialization script on the remote server
echo "Initializing database on remote server..."
ssh $REMOTE_HOST "cd $REMOTE_PATH && python backend/init_db.py"

# Restart the application
echo "Restarting SIEMply..."
ssh $REMOTE_HOST "cd $REMOTE_PATH && ./start.sh"

echo "Deployment complete!" 