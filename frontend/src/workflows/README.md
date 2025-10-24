# Splunk Environment Builder

The Build page provides a visual, drag-and-drop interface for designing and deploying entire Splunk environments, inspired by n8n.io's workflow automation platform.

## Features

### Visual Canvas
- **Drag & Drop Interface**: Add Splunk components to the canvas by dragging them from the sidebar
- **Node Positioning**: Click and drag nodes to position them on the canvas
- **Connection Lines**: Visual representation of relationships between components
- **Fullscreen Mode**: Toggle fullscreen for better workflow design experience

### Splunk Components
The sidebar provides access to all Splunk component types:

#### Cluster Management
- **Cluster Master (CM)**: Manages indexer cluster operations
- **Deployer**: Handles search head cluster configuration deployment

#### Search & Indexing
- **Search Head**: Provides search and reporting capabilities
- **Indexer**: Stores and indexes data
- **Search Head Cluster**: High-availability search head configuration

#### Forwarders
- **Universal Forwarder (UF)**: Lightweight data collection
- **Heavy Forwarder (HF)**: Data processing and filtering capabilities

#### Management
- **License Master**: Manages Splunk licenses
- **Monitoring Console**: System monitoring and health checks
- **Deployment Server**: Manages forwarder configurations

### Configuration
- **Host Assignment**: Assign target hosts from your Host Management inventory
- **Version Selection**: Choose Splunk versions (9.1.1, 9.0.5, 8.2.9, etc.)
- **Port Configuration**: Customize service ports
- **Authentication**: Set admin passwords and run users
- **Cluster Settings**: Configure replication factors and search factors

### Workflow Management
- **Save/Load**: Export and import workflow configurations as JSON files
- **Clear Canvas**: Reset the entire workflow design
- **Deployment**: One-click deployment of the entire environment

## Usage

### 1. Design Your Environment
1. Drag components from the sidebar to the canvas
2. Position nodes as desired
3. Configure each node with target hosts and settings

### 2. Configure Components
1. Click on a node to select it
2. Use the Properties panel to configure settings
3. Assign target hosts from your inventory
4. Set Splunk versions and authentication details

### 3. Deploy Environment
1. Ensure all nodes are configured (green "Configured" tag)
2. Click "Deploy Environment" button
3. Monitor deployment progress and results
4. View created jobs in the Job History

### 4. Save Your Work
- Use "Save Workflow" to export your design
- Use "Load Workflow" to import previous designs
- Workflows are saved as JSON files

## Clustering Support

The Build page integrates with the new Clustering tab in the Files page:

- **Automatic Cluster Creation**: When you specify a cluster name, the system automatically creates the necessary folder structure
- **Configuration Management**: Each cluster gets default and local configuration folders
- **Component Organization**: Structured organization for CM, Deployer, Search Heads, Indexers, etc.

## Integration

### Host Management
- Integrates with existing host inventory
- Only shows active hosts for assignment
- Supports host role filtering

### Job System
- Creates installation jobs using existing Splunk installation modules
- Supports both Universal Forwarder and Enterprise installations
- Job tracking and monitoring through existing Job History

### File System
- Cluster configurations stored in organized folder structures
- Default configurations provided automatically
- Local customizations supported

## Technical Details

### Architecture
- **Frontend**: React with TypeScript, Ant Design components
- **Backend**: FastAPI with cluster management service
- **Storage**: File-based cluster configuration storage
- **Integration**: RESTful API endpoints for workflow operations

### File Structure
```
clusters/
├── cluster-name/
│   ├── cm/
│   │   ├── default/
│   │   │   ├── server.conf
│   │   │   └── cluster.conf
│   │   └── local/
│   ├── deployer/
│   │   ├── default/
│   │   │   └── server.conf
│   │   └── local/
│   ├── sh/
│   │   ├── default/
│   │   │   ├── server.conf
│   │   │   └── cluster.conf
│   │   └── local/
│   ├── ds/
│   │   ├── default/
│   │   │   └── server.conf
│   │   └── local/
│   ├── uf/
│   │   ├── default/
│   │   │   ├── inputs.conf
│   │   │   └── outputs.conf
│   │   └── local/
│   ├── hf/
│   │   ├── default/
│   │   │   ├── inputs.conf
│   │   │   ├── outputs.conf
│   │   │   └── transforms.conf
│   │   └── local/
│   ├── lm/
│   │   ├── default/
│   │   │   ├── server.conf
│   │   │   └── licenses.conf
│   │   └── local/
│   ├── mc/
│   │   ├── default/
│   │   │   └── server.conf
│   │   └── local/
│   └── cluster.json
```

### API Endpoints
- `POST /workflows/clusters` - Create new cluster
- `GET /workflows/clusters` - List all clusters
- `GET /workflows/clusters/{name}` - Get cluster details
- `DELETE /workflows/clusters/{name}` - Delete cluster
- `POST /workflows/deploy` - Deploy environment
- `GET /workflows/health` - Service health check

## Best Practices

1. **Plan Your Architecture**: Design your Splunk environment before building
2. **Use Descriptive Names**: Choose meaningful cluster and component names
3. **Test Configurations**: Verify settings before deployment
4. **Monitor Deployments**: Check job status and logs after deployment
5. **Version Control**: Save workflow configurations for future reference

## Troubleshooting

### Common Issues
- **Node Not Configured**: Ensure all nodes have hosts assigned and settings configured
- **Deployment Failures**: Check host connectivity and SSH access
- **Missing Components**: Verify all required components are added to the canvas

### Debug Information
- Check browser console for JavaScript errors
- Review backend logs for API errors
- Verify cluster folder creation in the Files page
- Monitor job execution in Job History

## Future Enhancements

- **Connection Types**: Visual connection lines between components
- **Validation Rules**: Business logic validation for configurations
- **Templates**: Pre-built environment templates
- **Rollback**: Environment rollback capabilities
- **Monitoring**: Real-time deployment monitoring
- **Collaboration**: Multi-user workflow editing
