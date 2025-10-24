# SIEMply - SIEM Installation & Management System

SIEMply is a centralized platform for installing, configuring, and managing Splunk and Cribl instances across your infrastructure.

## Features

- **Host Management**: Inventory and track all your Splunk and Cribl hosts
- **Automated Installations**: Deploy Splunk Universal Forwarders, Enterprise instances, and Cribl Stream workers/leaders
- **Job Tracking**: Monitor installation and configuration jobs with detailed logs
- **SSH Automation**: Secure remote execution with retry logic and timeout handling
- **Customizable Ports**: Configure both API and UI on custom ports (API: 5050, UI: 8500)
- **Modern UI**: Responsive React-based interface with dark/light mode
- **Role-Based Access Control**: Secure authentication with role-based permissions
- **Configuration Push**: Deploy configuration files to Splunk and Cribl instances
- **Task Scheduling**: Schedule recurring tasks and monitor their execution
- **Monitoring**: Track the status and health of your SIEM infrastructure

## Requirements

### Backend
- Python 3.8+
- PostgreSQL (optional, SQLite supported by default)
- SSH access to target hosts

### Frontend
- Node.js 16+
- npm or yarn

## Setup

### Automated Setup (Recommended)

The easiest way to get started is to use our setup script:

```bash
./setup_siemply.sh
```

This script will:
1. Configure environment settings
2. Set up network binding for both frontend and backend
3. Create an admin user
4. Generate a secure secret key
5. Create necessary configuration files

### Manual Setup

#### Backend Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. Configure environment:
   - Create `.env` file in the root directory with the following content:
   ```
   SIEMPLY_API_PORT=5050
   SIEMPLY_UI_PORT=8500
   SIEMPLY_DB_URI=sqlite:///backend/siemply.db
   SIEMPLY_SECRET_KEY=your-secret-key-here
   SIEMPLY_FRONTEND_URL=http://localhost:8500
   ```

4. Initialize the database:
   ```bash
   python backend/init_db.py
   ```

5. Create an admin user:
   ```bash
   python backend/create_admin.py --username admin --password admin123
   ```

#### Frontend Setup

1. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```

2. Create `.env` file in the frontend directory:
   ```
   VITE_API_URL=http://YOUR_IP:5050
   ```

## Start Application

### Using Scripts (After Automated Setup)

```bash
# Terminal 1: Start the backend
./start_backend.sh

# Terminal 2: Start the frontend
./start_frontend.sh
```

### Manual Start

```bash
# Terminal 1: Start the backend
cd backend
python main.py --host 0.0.0.0

# Terminal 2: Start the frontend
cd frontend
npm run dev -- --port 8500 --host 0.0.0.0
```

### Access the Application

- Main application: http://YOUR_IP:8500
- Settings update page: http://YOUR_IP:8500/update-settings.html (visit this first)

**Default Login Credentials:**
- Username: admin
- Password: admin123

## Dashboard

The SIEMply dashboard provides a comprehensive overview of your SIEM infrastructure:

### Key Features
- **System Overview**: Real-time status of all managed hosts
- **Health Monitoring**: Visual indicators for system health and connectivity
- **Quick Actions**: Fast access to common operations
- **Recent Activity**: Latest job executions and system events
- **Resource Usage**: CPU, memory, and disk utilization metrics

### Navigation
- Access the main dashboard at: http://YOUR_IP:8500
- Use the sidebar navigation to switch between different sections
- Dashboard updates automatically every 30 seconds

## Jobs

The Jobs section manages all installation and configuration tasks:

### Job Types
- **Splunk Installations**: Universal Forwarder, Enterprise, Search Head
- **Cribl Installations**: Stream workers and leaders
- **Configuration Push**: Deploy config files to remote hosts
- **Maintenance Tasks**: Updates, restarts, and health checks

### Job Management
- **Create Jobs**: Use the job wizard to set up new installations
- **Monitor Progress**: Real-time job status and progress tracking
- **View Logs**: Detailed execution logs for troubleshooting
- **Job History**: Complete audit trail of all executed jobs
- **Retry Failed Jobs**: Re-run failed operations with modified parameters

### Job Status Indicators
- 🟢 **Completed**: Job finished successfully
- 🟡 **Running**: Job currently in progress
- 🔴 **Failed**: Job encountered an error
- ⏸️ **Paused**: Job temporarily stopped
- ⏳ **Pending**: Job queued for execution

## Database

SIEMply uses a flexible database system for storing configuration and operational data:

### Database Options
- **SQLite** (Default): Lightweight, file-based database
- **PostgreSQL**: Production-grade database for larger deployments

### Database Configuration
```bash
# SQLite (Default)
SIEMPLY_DB_URI=sqlite:///backend/siemply.db

# PostgreSQL
SIEMPLY_DB_URI=postgresql://username:password@localhost:5432/siemply
```

### Database Management
- **Initialize**: `python backend/init_db.py`
- **Backup**: Database files are located in `backend/siemply.db`
- **Reset**: Delete database file and re-run initialization
- **Migration**: Automatic schema updates on application startup

### Stored Data
- User accounts and authentication
- Host inventory and configurations
- Job history and execution logs
- System settings and preferences
- SSH keys and credentials (encrypted)

## Settings

Configure SIEMply behavior and system preferences:

### System Settings
- **API Port**: Backend API listening port (default: 5050)
- **UI Port**: Frontend web interface port (default: 8500)
- **Database URI**: Database connection string
- **Secret Key**: JWT token signing key
- **Frontend URL**: Public URL for the web interface

### SSH Configuration
- **Default SSH Port**: Standard SSH port (22)
- **Connection Timeout**: SSH connection timeout in seconds
- **Retry Attempts**: Number of retry attempts for failed connections
- **Key Management**: Centralized SSH key storage

### Security Settings
- **Authentication**: Enable/disable user authentication
- **Session Timeout**: User session duration
- **Password Policy**: Password complexity requirements
- **API Rate Limiting**: Request rate limits per user

### Accessing Settings
1. Navigate to: http://YOUR_IP:8500/update-settings.html
2. Modify configuration values as needed
3. Save changes to apply new settings
4. Restart services if required 