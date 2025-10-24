# SIEMply - Simplified Setup

SIEMply is a SIEM automation platform. This simplified setup uses just 2 scripts.

## Quick Start

### 1. Setup
Run the setup script to install dependencies and configure the environment:

```bash
./setup.sh
```

This script will:
- Check system dependencies (Python 3, Node.js)
- Create Python virtual environment
- Install Python and Node.js dependencies
- Create configuration files
- Initialize database
- Create admin user

### 2. Start
Run the start script to launch the application:

```bash
./start.sh
```

This script will:
- Start the backend server (port 5050)
- Start the frontend server (port 8500)
- Display access URLs and login credentials

## Access

- **Frontend**: http://your-server-ip:8500
- **Backend API**: http://your-server-ip:5050

## Login Credentials

- **Username**: admin
- **Password**: admin123

## System Requirements

- Python 3.8 or higher
- Node.js 16 or higher
- Linux/Ubuntu environment

## Troubleshooting

If you encounter issues:

1. Make sure all system dependencies are installed
2. Run `./setup.sh` again to reinstall dependencies
3. Check that ports 5050 and 8500 are available
4. Ensure you have proper permissions to create virtual environments

## Stopping the Application

Press `Ctrl+C` in the terminal where you ran `./start.sh` to stop both servers. 