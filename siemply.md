# SIEMply - SIEM Installation & Management System

## Project Overview
**Name**: SIEMply  
**Host Platform**: Linux (Ubuntu/RHEL recommended)  

### Tech Stack
- **Backend**: Python (FastAPI or Flask)
- **Frontend**: React or Vue.js
- **SSH Automation**: Paramiko / Fabric
- **Windows Support** (Future): pywinrm
- **Database**: PostgreSQL or SQLite
- **Optional**: Dockerized environment

## Project Structure
```
SIEMply/
├── backend/
│   ├── api/             # API endpoints
│   ├── automation/      # SSH logic
│   ├── installers/      # Installer scripts
│   ├── models/          # Database models
│   └── tests/           # Unit tests
├── frontend/
│   ├── components/      # UI components
│   ├── pages/           # Page containers
│   ├── services/        # API service wrappers
│   └── tests/           # Frontend tests
├── scripts/             # Utility scripts
└── docs/                # Documentation
```

## Project Phases

### Phase 1: System Foundation ✅ (COMPLETED)
| Task | Description | Status |
|------|-------------|--------|
| task-init-system | Set up Linux host with required packages (Python, Node.js, Git, Docker if needed) | ✅ |
| task-project-scaffold | Scaffold backend and frontend folders (backend/, frontend/, scripts/, etc.) | ✅ |
| task-env-setup | Create .env config loader for things like port, DB URI, Cribl token | ✅ |
| task-port-config | Implement configurable ports for frontend UI (e.g., localhost:8500) and API endpoints | ✅ |
| task-database-models | Define host inventory, job logs, user auth (ORM models) | ✅ |

### Phase 2: Backend API Development ✅ (COMPLETED)
| Task | Description | Status |
|------|-------------|--------|
| task-api-host-management | Create APIs to add, edit, delete, and tag hosts with roles (Splunk/Cribl) | ✅ |
| task-api-job-runner | Create endpoint to trigger install jobs (e.g., POST /install/splunk) | ✅ |
| task-ssh-module | Implement secure SSH task runner (with timeout, retry logic) | ✅ |
| task-cribl-installer | Script for Cribl install + config (cribl_worker, cribl_leader) | ✅ |
| task-splunk-installer | Script for Splunk UF and Enterprise installs | ✅ |
| task-job-logger | Capture stdout, stderr, return codes in logs table | ✅ |

### Phase 3: Frontend UI ✅ (COMPLETED)
| Task | Description | Status |
|------|-------------|--------|
| task-ui-dashboard | Build the main dashboard to show hosts, jobs, and quick actions | ✅ |
| task-ui-host-table | Display host inventory with filters by role/status | ✅ |
| task-ui-job-history | Show past job logs (status, type, time) | ✅ |
| task-ui-install-modal | Create UI flow for installing Splunk/Cribl (select version, role, host) | ✅ |
| task-ui-settings-page | Manage API keys, tokens, ports, backend URLs | ✅ |

### Phase 3.5: Installation & Compatibility Fixes ✅ (COMPLETED)
| Task | Description | Status |
|------|-------------|--------|
| task-ubuntu-setup | Create Ubuntu-specific setup script to fix externally-managed-environment error | ✅ |
| task-pydantic-fix | Fix Pydantic v2 compatibility (BaseSettings moved to pydantic-settings) | ✅ |
| task-install-docs | Create comprehensive installation documentation | ✅ |

### Phase 4: Advanced Features
| Task | Description |
|------|-------------|
| task-auth-system | Add login system with role-based access (admin, user) |
| task-config-push | Push Splunk/Cribl config files like inputs.conf, cribl.yml |
| task-cron-or-scheduler | Allow task scheduling (e.g., nightly install check) |
| task-api-cribl-monitor | Query Cribl REST API for health/status of leader + workers |
| task-api-splunk-monitor | Query Splunk REST for health check or forwarder status |

### Optional: Deployment
| Task | Description |
|------|-------------|
| task-dockerize-app | Create Dockerfiles for frontend/backend, build image |
| task-nginx-reverse-proxy | Setup NGINX + SSL for frontend/backend |
| task-systemd-services | Setup systemd units to auto-start backend and frontend on boot |

## Development Standards

### Code Style & Structure
- All Python code must be type hinted and follow PEP8
- Use async functions in FastAPI routes where I/O is expected
- React components must be functional (no class components)
- All network/SSH modules must log start/stop/error times

### File Structure Rules
- API endpoints live in `backend/api/`
- SSH logic lives in `backend/automation/`
- Installer scripts go in `backend/installers/`
- Frontend components in `frontend/components/`

### Task Conventions
Every API route must:
- Return proper HTTP status codes
- Log requests to a file/db

Every job task (e.g., install Splunk) must:
- Be re-runnable safely
- Have a unique job_id logged
- Support dry-run/test mode

### Security Rules
- Never hardcode credentials or tokens in source files
- Always read secrets from .env or key vault
- For SSH: Use keys if possible; fallback to password if absolutely needed

### Testing
- Use pytest for backend unit tests
- Ensure at least 80% coverage on core modules (installer, SSH, jobs)
- Frontend components should have snapshot tests using Jest or Vitest

## Getting Started

### Prerequisites
- Python 3.8+
- Node.js 16+
- PostgreSQL or SQLite
- Git

### Setup Instructions
1. Clone the repository
2. Set up virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r backend/requirements.txt
   ```
3. Set up frontend:
   ```
   cd frontend
   npm install
   ```
4. Create .env file with required configuration
5. Initialize database:
   ```
   cd backend
   python init_db.py
   ```
6. Start development servers:
   ```
   # Backend
   cd backend
   python main.py --port 5000  # Customizable API port (avoid 8000 as it's used by Splunk)
   
   # Frontend
   cd frontend
   npm run dev -- --port 8500  # Customizable UI port, access via localhost:8500
   ```

## License
[Specify your license here] 