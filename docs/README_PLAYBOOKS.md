# SIEMPLY Automation Playbooks

This document describes the automation playbook system in SIEMPLY, which allows users to create, manage, and execute automation tasks through a user-friendly GUI interface.

## Overview

The playbook system provides a visual interface for creating automation playbooks that follow a structured YAML format. Users can build complex automation workflows without directly editing YAML files, while the system handles the YAML generation in the background.

## Features

### GUI Playbook Builder
- **Visual Interface**: Create playbooks through an intuitive web interface
- **Module Selection**: Choose from predefined automation modules (service, git, command, script, etc.)
- **Parameter Configuration**: Configure module parameters through form inputs
- **Real-time Preview**: Preview the generated YAML as you build
- **Validation**: Built-in validation to ensure playbook correctness

### Playbook Management
- **List View**: Browse and search existing playbooks
- **Preview**: View playbook content and metadata
- **Delete**: Remove playbooks from the system
- **Execute**: Run playbooks (execution engine to be implemented)

### YAML Structure

The system generates playbooks in the following format:

```yaml
automation_playbook:
  - job:
      id: unique_job_id
      name: "Human readable job name"
      
      targets:
        server_class: webservers
        hosts:
          - host1.example.com
          - host2.example.com
        exclude_hosts:
          - test-server.example.com
      
      execution_options:
        remote_user: deploy_user
        become: yes
        become_user: root
        on_failure: stop
      
      vars:
        app_version: "1.5.2"
        source_repo: "git@github.com:company/app.git"
      
      tasks:
        - name: "Task description"
          module_name:
            param1: value1
            param2: value2
          when: condition
          register: output_variable
```

## Available Modules

### Service Management
- **Module**: `service`
- **Parameters**: `name`, `state` (started/stopped), `enabled` (yes/no)

### Git Operations
- **Module**: `git`
- **Parameters**: `repo`, `dest`, `version`

### Command Execution
- **Module**: `command`
- **Parameters**: `cmd`

### Script Execution
- **Module**: `script`
- **Parameters**: `path`

### Package Management
- **Module**: `package`
- **Parameters**: `name`, `state` (present/absent/latest)

### File Operations
- **Module**: `file`
- **Parameters**: `path`, `state`

### File Copy
- **Module**: `copy`
- **Parameters**: `src`, `dest`

### Template Processing
- **Module**: `template`
- **Parameters**: `src`, `dest`

### Debug Output
- **Module**: `debug`
- **Parameters**: `msg`

### System Reboot
- **Module**: `reboot`
- **Parameters**: `reboot_timeout`

### User Management
- **Module**: `user`
- **Parameters**: `name`, `state`

### Group Management
- **Module**: `group`
- **Parameters**: `name`, `state`

## Usage

### Creating a New Playbook

1. Navigate to **Playbooks > Playbook Builder** in the sidebar
2. Click **Add Job** to create a new job
3. Configure the job details:
   - **Job ID**: Unique identifier for the job
   - **Job Name**: Human-readable description
   - **Targets**: Specify server classes or individual hosts
   - **Execution Options**: Set remote user, privilege escalation, and failure handling
   - **Variables**: Define job-specific variables
4. Add tasks to the job:
   - Click **Add Task** within the job
   - Select a module from the dropdown
   - Configure module parameters
   - Add conditional execution (`when`) and output registration (`register`) if needed
5. Preview the generated YAML using the **Preview YAML** button
6. Save the playbook using the **Save Playbook** button

### Managing Playbooks

1. Navigate to **Playbooks > Playbook List** in the sidebar
2. View all available playbooks in a table format
3. Use the search functionality to find specific playbooks
4. Click the **Preview** button to view playbook content
5. Click the **Execute** button to run the playbook (when implemented)
6. Click the **Delete** button to remove playbooks

## API Endpoints

The playbook system provides the following API endpoints:

- `POST /api/playbooks` - Create a new playbook
- `GET /api/playbooks` - List all playbooks
- `GET /api/playbooks/{id}` - Get a specific playbook
- `DELETE /api/playbooks/{id}` - Delete a playbook
- `POST /api/playbooks/{id}/validate` - Validate a playbook
- `POST /api/playbooks/{id}/execute` - Execute a playbook

## File Storage

Playbooks are stored as YAML files in the `/opt/SIEMPLY/backend/playbooks/` directory. Each playbook is saved as a separate `.yml` file with a unique name.

## Future Enhancements

- **Execution Engine**: Implement actual playbook execution logic
- **Scheduling**: Add ability to schedule playbook execution
- **Templates**: Provide pre-built playbook templates
- **Version Control**: Track playbook versions and changes
- **Collaboration**: Allow multiple users to work on playbooks
- **Testing**: Add playbook testing and validation features
- **Monitoring**: Track execution status and results

## Example Playbook

See `/opt/SIEMPLY/backend/playbooks/example_web_deployment.yml` for a complete example playbook that demonstrates:

- Multiple jobs in a single playbook
- Different target configurations
- Various module types
- Conditional execution
- Variable usage
- Error handling strategies

## Security Considerations

- Playbooks are executed with the specified remote user credentials
- Privilege escalation (sudo) can be configured per job
- Host targeting can be restricted to specific server classes
- Execution can be limited to authorized users only
- All playbook operations are logged for audit purposes 