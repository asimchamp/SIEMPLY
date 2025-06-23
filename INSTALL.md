# SIEMply Installation Guide

This guide provides instructions for installing and running the SIEMply project on different systems.

## Prerequisites

- Python 3.8 or higher
- Node.js 16 or higher
- Git

## Installation Options

### Option 1: Standard Installation (All Systems)

This method works for most systems where you have user-level permissions.

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/SIEMply.git
   cd SIEMply
   ```

2. Run the setup script:
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

3. Start the application:
   ```bash
   # To start both backend and frontend:
   ./start.sh
   
   # Or start them separately:
   ./start_backend.sh
   ./start_frontend.sh
   ```

### Option 2: Ubuntu/Debian System Installation

This method is recommended for Ubuntu/Debian systems, especially those with Python 3.12+ where you might encounter the "externally-managed-environment" error.

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/SIEMply.git
   cd SIEMply
   ```

2. Run the Ubuntu setup script with sudo:
   ```bash
   chmod +x setup_ubuntu.sh
   sudo ./setup_ubuntu.sh
   ```

3. Start the application:
   ```bash
   # As a systemd service:
   sudo systemctl start siemply
   
   # Enable auto-start on boot:
   sudo systemctl enable siemply
   
   # Or run manually:
   sudo /opt/SIEMPLY/start.sh
   ```

## Troubleshooting

### "externally-managed-environment" Error

If you encounter this error when installing Python packages:

```
error: externally-managed-environment
```

This is because newer Python versions (3.12+) on Debian/Ubuntu systems prevent installing packages directly to the system Python. Use one of these solutions:

1. **Recommended**: Use the `setup_ubuntu.sh` script which creates a virtual environment.

2. **Manual fix**: Create and use a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r backend/requirements.txt
   ```

3. **Not recommended**: Override the restriction (may break your system Python):
   ```bash
   pip install --break-system-packages -r backend/requirements.txt
   ```

### Pydantic BaseSettings Error

If you encounter this error:

```
pydantic.errors.PydanticImportError: `BaseSettings` has been moved to the `pydantic-settings` package.
```

This happens because the code was written for Pydantic v1, but you're using Pydantic v2. The setup scripts automatically fix this by:

1. Installing the pydantic-settings package
2. Updating the import statement in settings.py

If you need to fix this manually:

1. Install the required package:
   ```bash
   pip install pydantic-settings
   ```

2. Edit the settings.py file:
   ```bash
   # Change this line:
   from pydantic import BaseSettings, Field
   
   # To this:
   from pydantic import Field
   from pydantic_settings import BaseSettings
   ```

### Field Import Error

If you encounter this error:

```
ImportError: cannot import name 'Field' from 'pydantic_settings'
```

This happens because `Field` is still in the `pydantic` package, not in `pydantic_settings`. The setup scripts automatically fix this, but if you need to fix it manually:

1. Edit the settings.py file:
   ```bash
   # Change this line:
   from pydantic_settings import BaseSettings, Field
   
   # To this:
   from pydantic import Field
   from pydantic_settings import BaseSettings
   ```

2. Or run the fix script:
   ```bash
   # For standard installation:
   ./fix_pydantic.sh
   
   # For Ubuntu installation:
   sudo ./fix_pydantic.sh
   ```

### Missing SECRET_KEY Error

If you encounter this error:

```
ValidationError: 1 validation error for Settings
SECRET_KEY
  Field required [type=missing, input_value={}, input_type=dict]
```

This happens because the Settings class requires a SECRET_KEY. The setup scripts automatically generate one, but if you need to fix it manually:

1. Run the fix script:
   ```bash
   # For standard installation:
   ./fix_secret_key.sh
   
   # For Ubuntu installation:
   sudo ./fix_secret_key.sh
   ```

2. Or manually add SECRET_KEY to your .env file:
   ```bash
   # Generate a random secret key
   SECRET_KEY=$(openssl rand -hex 32)
   
   # Add it to .env file
   echo "SIEMPLY_SECRET_KEY=${SECRET_KEY}" >> .env
   ```

### Port Conflicts

If you encounter port conflicts:

1. Edit the `.env` file to change the ports:
   ```
   SIEMPLY_API_PORT=5000  # Change to another port if needed
   SIEMPLY_UI_PORT=8500   # Change to another port if needed
   ```

2. Restart the application.

## Accessing the Application

- Backend API: http://localhost:5000
- Frontend UI: http://localhost:8500

## Uninstalling

### Standard Installation
Delete the project directory.

### Ubuntu System Installation
```bash
sudo systemctl stop siemply
sudo systemctl disable siemply
sudo rm /etc/systemd/system/siemply.service
sudo systemctl daemon-reload
sudo rm -rf /opt/SIEMPLY
``` 