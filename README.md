# SIEMply - SIEM Installation & Management System

SIEMply is a centralized platform for installing, configuring, and managing Splunk and Cribl instances across your infrastructure.

## Features

- **Host Management**: Inventory and track all your Splunk and Cribl hosts
- **Automated Installations**: Deploy Splunk Universal Forwarders, Enterprise instances, and Cribl Stream workers/leaders
- **Job Tracking**: Monitor installation and configuration jobs with detailed logs
- **SSH Automation**: Secure remote execution with retry logic and timeout handling
- **Customizable Ports**: Configure both API and UI on custom ports (API: 5000, UI: 8500)
- **Modern UI**: Responsive React-based interface with dark/light mode

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

## Getting Started

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
   - Create `.env` file in the backend directory with the following content:
   ```
   SIEMPLY_DB_TYPE=sqlite
   SIEMPLY_DB_URI=sqlite:///./siemply.db
   SIEMPLY_API_PORT=5000
   SIEMPLY_API_HOST=0.0.0.0
   SIEMPLY_DEBUG=true
   SIEMPLY_UI_PORT=8500
   SIEMPLY_SECRET_KEY=your-secret-key-here
   ```

4. Initialize the database:
   ```
   python init_db.py
   ```

5. Start the backend server:
   ```
   python main.py --port 5000
   ```

### Frontend Setup

1. Install dependencies:
   ```
   cd frontend
   npm install
   ```

2. Fix TypeScript type definitions:
   ```
   ./fix-typescript.sh
   ```

3. Start the development server:
   ```
   npm run dev
   ```
   This will start the UI on port 8500 (http://localhost:8500)

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

### In Progress
- 🔄 Backend API Development (Phase 2)
- 🔄 Frontend UI (Phase 3)
- 🔄 Advanced Features (Phase 4)

## License

[Specify your license here] 