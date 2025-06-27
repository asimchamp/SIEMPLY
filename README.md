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

## Project Structure

```
SIEMply/
├── backend/               # Python FastAPI backend
│   ├── api/               # API endpoints
│   ├── automation/        # SSH automation logic
│   ├── config/            # Environment configuration
│   ├── installers/        # Splunk/Cribl installer scripts
│   ├── models/            # Database models
│   └── tests/             # Unit tests
├── frontend/              # React/TypeScript frontend
│   ├── src/
│   │   ├── components/    # Reusable UI components
│   │   ├── pages/         # Page components
│   │   └── services/      # API service wrappers
│   └── public/            # Static assets
└── docs/                  # Documentation
```

## Requirements

### Backend
- Python 3.8+
- PostgreSQL (optional, SQLite supported by default)
- SSH access to target hosts

### Frontend
- Node.js 16+
- npm or yarn

## Quick Start

The easiest way to get started is to use our setup script:

```
./setup_siemply.sh
```

This script will:
1. Configure environment settings
2. Set up network binding for both frontend and backend
3. Create an admin user
4. Generate a secure secret key
5. Create necessary configuration files

After running the setup script, start the application:

```
# Terminal 1: Start the backend
./start_backend.sh

# Terminal 2: Start the frontend
./start_frontend.sh
```

Then visit:
- Main application: http://YOUR_IP:8500
- Settings update page: http://YOUR_IP:8500/update-settings.html (visit this first)

Log in with:
- Username: admin
- Password: admin123

## Manual Setup

### Backend Setup

1. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```
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
   ```
   python backend/init_db.py
   ```

5. Create an admin user:
   ```
   python backend/create_admin.py --username admin --password admin123
   ```

6. Start the backend server:
   ```
   cd backend
   python main.py --host 0.0.0.0
   ```

### Frontend Setup

1. Install dependencies:
   ```
   cd frontend
   npm install
   ```

2. Create `.env` file in the frontend directory:
   ```
   VITE_API_URL=http://YOUR_IP:5050
   ```

3. Start the development server:
   ```
   npm run dev -- --port 8500 --host 0.0.0.0
   ```
   This will start the UI on port 8500 (http://YOUR_IP:8500)

## Development Workflow

### Code Quality

This project enforces strict code quality standards through linting and type checking:

#### Backend
- Run the setup script to install linting tools:
  ```
  cd backend
  ./setup-linting.sh
  ```
- Python code is checked with:
  - **flake8**: Style guide enforcement
  - **mypy**: Static type checking
  - **black**: Code formatting
  - **isort**: Import sorting

#### Frontend
- TypeScript is strictly enforced
- ESLint is configured for React best practices
- Pre-commit hooks ensure code quality

### Development Status

#### Completed
- ✅ System Foundation (Phase 1)
  - Project structure setup
  - Environment configuration
  - Database models
  - SSH automation framework
  - Custom port configuration
- ✅ Backend API Development (Phase 2)
  - Host management endpoints
  - Job tracking and execution
  - SSH automation
  - Installer scripts
- ✅ Frontend UI (Phase 3)
  - Responsive React interface
  - Host management
  - Job history and tracking
  - Installation wizards
- ✅ Advanced Features (Phase 4)
  - Authentication and RBAC
  - Configuration push
  - Task scheduling
  - Monitoring

## License

[MIT License] 