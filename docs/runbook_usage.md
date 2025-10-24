# Runbook Automation System

The Runbook system in SIEMply allows you to create, manage, and execute automation playbooks using YAML files. This system integrates with the Files page and ServerClass functionality to provide powerful automation capabilities.

## Overview

The Runbook system consists of:

1. **Runbook Management**: Create, edit, and manage runbook definitions
2. **YAML Parser**: Parse and validate YAML automation playbooks
3. **Execution Engine**: Execute runbooks on target hosts or server classes
4. **Task Execution**: Execute individual tasks (service, command, script, etc.)
5. **Execution History**: Track and monitor runbook executions

## YAML Structure

Runbooks use a structured YAML format that defines automation jobs and tasks:

```yaml
automation_playbook:
  
  - job:
      id: unique_job_id
      name: "Human readable job name"
      
      targets:
        server_class: webservers  # Target by server class
        # OR
        hosts: [1, 2, 3]  # Target specific host IDs
      
      execution_options:
        remote_user: root
        on_failure: stop  # stop, continue, rollback
      
      vars:
        variable_name: "value"
        
      tasks:
        - name: "Task description"
          service:
            name: nginx
            state: started
            enabled: yes
```

## Supported Task Types

### 1. Service Tasks
Manage system services:

```yaml
- name: "Start nginx service"
  service:
    name: nginx
    state: started  # started, stopped, restarted
    enabled: yes    # Enable on boot
```

### 2. Command Tasks
Execute shell commands:

```yaml
- name: "Update package cache"
  command: "apt-get update"
```

### 3. Script Tasks
Execute scripts:

```yaml
- name: "Run backup script"
  script: "/opt/scripts/backup.sh"
```

### 4. Git Tasks
Manage Git repositories:

```yaml
- name: "Clone application repository"
  git:
    repo: "git@github.com:company/app.git"
    dest: "/var/www/app"
    version: "v1.2.0"
```

### 5. Package Tasks
Manage software packages:

```yaml
- name: "Install nginx package"
  package:
    name: nginx
    state: present  # present, latest, absent
```

### 6. Debug Tasks
Display debug information:

```yaml
- name: "Show system info"
  debug:
    msg: "System information: {{ system_info.stdout }}"
```

### 7. Reboot Tasks
Reboot systems:

```yaml
- name: "Reboot system"
  reboot:
    reboot_timeout: 600  # Timeout in seconds
```

## Target Configuration

### Server Classes
Target hosts using server classes:

```yaml
targets:
  server_class: webservers
```

### Specific Hosts
Target specific hosts by ID:

```yaml
targets:
  hosts: [1, 2, 3]
```

### Hostnames
Target hosts by hostname:

```yaml
targets:
  hosts: "web1.internal,web2.internal,web3.internal"
```

## Variables

Use variables to make runbooks dynamic:

```yaml
vars:
  app_version: "2.1.0"
  deployment_server: "splunk-deployment-server.internal"

tasks:
  - name: "Download version {{ app_version }}"
    command: "wget https://example.com/app-{{ app_version }}.tar.gz"
```

## Execution Options

Configure how jobs are executed:

```yaml
execution_options:
  remote_user: root          # User to execute as
  on_failure: stop           # stop, continue, rollback
  become: yes                # Use sudo
  become_user: root          # User to become
```

## API Endpoints

### Runbook Management

- `GET /runbooks` - List all runbooks
- `GET /runbooks/{id}` - Get specific runbook
- `POST /runbooks` - Create new runbook
- `PUT /runbooks/{id}` - Update runbook
- `DELETE /runbooks/{id}` - Delete runbook

### Runbook Execution

- `POST /runbooks/{id}/execute` - Execute runbook
- `GET /runbooks/executions` - List executions
- `GET /runbooks/executions/{id}` - Get execution details
- `GET /runbooks/executions/{id}/tasks` - Get execution tasks

### Validation

- `POST /runbooks/{id}/validate` - Validate YAML content

### File Integration

- `POST /runbooks/from-file` - Create runbook from file

## Usage Examples

### 1. Create Runbook from File

```bash
curl -X POST "http://localhost:5050/runbooks/from-file" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "file_path=sample_runbook.yaml&name=Sample Runbook&description=Test automation"
```

### 2. Execute Runbook

```bash
curl -X POST "http://localhost:5050/runbooks/1/execute" \
  -H "Content-Type: application/json" \
  -d '{"parameters": {"custom_var": "value"}}'
```

### 3. Validate Runbook

```bash
curl -X POST "http://localhost:5050/runbooks/1/validate"
```

## Integration with Files Page

1. **Upload YAML Files**: Upload runbook YAML files to the Files page
2. **Create from File**: Use the "Create from File" endpoint to create runbooks from uploaded files
3. **Edit in Files**: Edit YAML files directly in the Files page
4. **Version Control**: Track changes to runbook files

## Integration with ServerClass

1. **Target by Server Class**: Use server classes to target multiple hosts
2. **Dynamic Hosting**: Server classes automatically include all hosts with specific roles
3. **Flexible Targeting**: Combine server classes with specific host targeting

## Best Practices

### 1. Naming Conventions
- Use descriptive job and task names
- Use consistent naming patterns
- Include version numbers in job IDs

### 2. Error Handling
- Set appropriate `on_failure` behavior
- Include rollback procedures
- Use conditional tasks with `when` clauses

### 3. Security
- Use least privilege principle
- Validate all inputs
- Use secure authentication methods

### 4. Monitoring
- Include debug tasks for troubleshooting
- Register command outputs for analysis
- Use proper logging

### 5. Testing
- Test runbooks in development environment
- Use dry-run mode when available
- Validate YAML before execution

## Sample Runbooks

### Splunk Deployment
```yaml
automation_playbook:
  - job:
      id: deploy_splunk_uf
      name: "Deploy Splunk Universal Forwarder"
      targets:
        server_class: webservers
      execution_options:
        remote_user: root
      tasks:
        - name: "Install Splunk UF"
          command: "rpm -i splunkforwarder.rpm"
        - name: "Configure deployment client"
          command: "/opt/splunkforwarder/bin/splunk set deploy-poll server:8089"
        - name: "Start service"
          service:
            name: SplunkForwarder
            state: started
```

### System Maintenance
```yaml
automation_playbook:
  - job:
      id: system_maintenance
      name: "System Maintenance"
      targets:
        server_class: all_servers
      execution_options:
        remote_user: root
        on_failure: continue
      tasks:
        - name: "Update packages"
          command: "apt-get update && apt-get upgrade -y"
        - name: "Clean up"
          command: "apt-get autoremove -y"
        - name: "Check disk space"
          command: "df -h"
```

## Troubleshooting

### Common Issues

1. **YAML Validation Errors**
   - Check YAML syntax
   - Validate required fields
   - Ensure proper indentation

2. **Target Host Issues**
   - Verify server class exists
   - Check host connectivity
   - Validate SSH credentials

3. **Task Execution Failures**
   - Check command syntax
   - Verify file permissions
   - Review error messages

4. **Performance Issues**
   - Limit concurrent executions
   - Use appropriate timeouts
   - Monitor resource usage

### Debugging

1. **Enable Debug Logging**
   - Set log level to DEBUG
   - Review execution logs
   - Check task outputs

2. **Use Debug Tasks**
   - Add debug tasks to runbooks
   - Display variable values
   - Show system information

3. **Monitor Executions**
   - Track execution status
   - Review task results
   - Analyze failure patterns 