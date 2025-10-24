import React, { useState, useEffect } from 'react';
import {
  Card,
  Button,
  Modal,
  message,
  Space,
  Typography,
  Row,
  Col,
  Select,
  Tag,
  Alert,
  Spin,
  Empty,
  List,
  Avatar
} from 'antd';
import {
  PlusOutlined,
  PlayCircleOutlined,
  ClusterOutlined,
  CloudOutlined,
  DatabaseOutlined,
  SearchOutlined,
  MonitorOutlined,
  FileTextOutlined,
  ThunderboltOutlined,
  FireOutlined,
  CheckCircleOutlined,
  CloseOutlined,
  ReloadOutlined,
  EyeOutlined,
  KeyOutlined,
  DeleteOutlined
} from '@ant-design/icons';
import { hostService, jobService, packageService, Host, SoftwarePackage } from '../services/api';
import { workflowsService } from '../services/workflowsService';
import { useNavigate } from 'react-router-dom';
import './Build.css';

const { Title, Text } = Typography;
const { Option } = Select;

// Splunk component types with icons and colors
const SPLUNK_COMPONENTS = {
  'splunk_cm': { 
    label: 'Cluster Master', 
    icon: <ClusterOutlined />, 
    color: '#52c41a',
    description: 'Splunk Cluster Master for indexer cluster management',
    defaultPort: 8089,
    category: 'cluster'
  },
  'splunk_deployer': { 
    label: 'Deployer', 
    icon: <CloudOutlined />, 
    color: '#1890ff',
    description: 'Splunk Deployer for search head cluster configuration',
    defaultPort: 8089,
    category: 'search'
  },
  'splunk_license_master': { 
    label: 'License Master', 
    icon: <KeyOutlined />, 
    color: '#722ed1',
    description: 'Splunk License Master for license management',
    defaultPort: 8089,
    category: 'management'
  },
  'splunk_monitoring_console': { 
    label: 'Monitoring Console', 
    icon: <MonitorOutlined />, 
    color: '#fa8c16',
    description: 'Splunk Monitoring Console for system monitoring',
    defaultPort: 8089,
    category: 'management'
  },
  'splunk_deployment_server': { 
    label: 'Deployment Server', 
    icon: <DatabaseOutlined />, 
    color: '#13c2c2',
    description: 'Splunk Deployment Server for forwarder management',
    defaultPort: 8089,
    category: 'forwarder'
  },
  'splunk_search_head': { 
    label: 'Search Head', 
    icon: <SearchOutlined />, 
    color: '#eb2f96',
    description: 'Splunk Search Head for search and reporting',
    defaultPort: 8000,
    category: 'search'
  },
  'splunk_indexer': { 
    label: 'Indexer', 
    icon: <DatabaseOutlined />, 
    color: '#fa541c',
    description: 'Splunk Indexer for data storage and indexing',
    defaultPort: 8089,
    category: 'cluster'
  },
  'splunk_hf': { 
    label: 'Heavy Forwarder', 
    icon: <ThunderboltOutlined />, 
    color: '#f5222d',
    description: 'Splunk Heavy Forwarder for data processing',
    defaultPort: 8089,
    category: 'forwarder'
  },
  'splunk_uf': { 
    label: 'Universal Forwarder', 
    icon: <FileTextOutlined />, 
    color: '#a0d911',
    description: 'Splunk Universal Forwarder for data collection',
    defaultPort: 9997,
    category: 'forwarder'
  },
  'splunk_enterprise': { 
    label: 'Enterprise', 
    icon: <FireOutlined />, 
    color: '#faad14',
    description: 'Splunk Enterprise standalone installation',
    defaultPort: 8000,
    category: 'standalone'
  }
};

// Standard Splunk configuration
const STANDARD_CONFIG = {
  adminPassword: 'changeme',
  installDir: '/opt',
  runUser: 'splunk',
  runGroup: 'splunk',
  defaultPorts: {
    web: 8000,
    management: 8089,
    forwarder: 9997
  }
};

interface SplunkComponent {
  type: string;
  hostId?: number;
  host?: Host;
  packageId?: number;
  package?: any; // SoftwarePackage; // Removed as package management is removed
  isConfigured: boolean;
}

const Build: React.FC = () => {
  const navigate = useNavigate();
  const [components, setComponents] = useState<SplunkComponent[]>([]);
  const [existingClusters, setExistingClusters] = useState<any[]>([]);
  const [selectedCluster, setSelectedCluster] = useState<any>(null);
  const [clustersLoading, setClustersLoading] = useState(true);
  const [showClusterModal, setShowClusterModal] = useState(true);
  const [availableHosts, setAvailableHosts] = useState<Host[]>([]);
  const [deployModalVisible, setDeployModalVisible] = useState(false);
  const [deploying, setDeploying] = useState(false);
  const [deployResults, setDeployResults] = useState<any[]>([]);
  const [deploymentProgress, setDeploymentProgress] = useState(0);
  const [availablePackages, setAvailablePackages] = useState<SoftwarePackage[]>([]); // Removed as package management is removed
  const [componentModalVisible, setComponentModalVisible] = useState(false);
  const [selectedEnterpriseVersion, setSelectedEnterpriseVersion] = useState<string>('');
  const [selectedUFVersion, setSelectedUFVersion] = useState<string>('');
  const [multiRoleMode, setMultiRoleMode] = useState(false);
  const [buildSaved, setBuildSaved] = useState(false);

  // Load available hosts and existing clusters on component mount
  useEffect(() => {
    fetchHosts();
    fetchExistingClusters();
    fetchAvailablePackages();
  }, []);

  // Debug selectedCluster changes
  useEffect(() => {
    console.log('selectedCluster changed:', selectedCluster);
  }, [selectedCluster]);

  const fetchHosts = async () => {
    try {
      const hosts = await hostService.getAllHosts();
      setAvailableHosts(hosts.filter(host => host.is_active));
    } catch (error) {
      console.error('Failed to fetch hosts:', error);
      message.error('Failed to load available hosts');
    }
  };

  const fetchExistingClusters = async () => {
    try {
      setClustersLoading(true);
      console.log('Fetching existing clusters...');
      const clusters = await workflowsService.listClusters();
      console.log('Clusters fetched:', clusters);
      console.log('Cluster data structure:', clusters.map(c => ({
        name: c.cluster_name,
        total_folders: c.total_folders,
        components: c.components,
        created_at: c.created_at
      })));
      setExistingClusters(clusters);
    } catch (error) {
      console.error('Failed to fetch existing clusters:', error);
      message.error('Failed to load clusters. Please check the console for details.');
    } finally {
      setClustersLoading(false);
    }
  };

  const fetchAvailablePackages = async () => {
    try {
      const packages = await packageService.getPackages({ 
        vendor: 'Splunk Inc.',
        status: 'active'
      });
      setAvailablePackages(packages);
      
      // Auto-select the first available versions if none are selected
      if (packages.length > 0) {
        // Auto-select Enterprise version
        if (!selectedEnterpriseVersion) {
          const enterprisePackage = packages.find(pkg => 
            pkg.package_type === 'splunk_enterprise' && pkg.is_default
          ) || packages.find(pkg => pkg.package_type === 'splunk_enterprise') || packages[0];
          if (enterprisePackage) {
            setSelectedEnterpriseVersion(enterprisePackage.version);
          }
        }
        
        // Auto-select UF version
        if (!selectedUFVersion) {
          const ufPackage = packages.find(pkg => 
            pkg.package_type === 'splunk_uf' && pkg.is_default
          ) || packages.find(pkg => pkg.package_type === 'splunk_uf');
          if (ufPackage) {
            setSelectedUFVersion(ufPackage.version);
          }
        }
      }
    } catch (error) {
      console.error('Failed to fetch packages:', error);
      message.error('Failed to load available packages');
    }
  };

  // Create a complete Splunk cluster with one click
  const createCompleteCluster = async () => {
    if (!selectedCluster) {
      message.error('Please select a cluster first');
      return;
    }

    if (!selectedEnterpriseVersion) {
      message.error('Please select a Splunk Enterprise version first before creating a complete cluster');
      return;
    }

    try {
      // Clear existing components
      setComponents([]);
      
      // Add all essential Splunk components
      const essentialComponents = [
        'splunk_cm',           // Cluster Master
        'splunk_deployer',     // Deployer
        'splunk_search_head',  // Search Head
        'splunk_indexer',      // Indexer
        'splunk_deployment_server', // Deployment Server
        'splunk_license_master',    // License Master
        'splunk_monitoring_console' // Monitoring Console
      ];

      message.loading('Creating complete cluster...', 0);
      
      for (const component of essentialComponents) {
        await addComponent(component);
        // Small delay to prevent overwhelming the API
        await new Promise(resolve => setTimeout(resolve, 100));
      }

      message.destroy();
      message.success('Complete cluster created! All components are ready for deployment.');
      
    } catch (error) {
      message.destroy();
      console.error('Failed to create complete cluster:', error);
      message.error('Failed to create complete cluster');
    }
  };

  // Add new component
  const addComponent = async (type: string) => {
    if (!type) return;
    
    // Determine which version to use based on component type
    const isUniversalForwarder = type === 'splunk_uf';
    const requiredVersion = isUniversalForwarder ? selectedUFVersion : selectedEnterpriseVersion;
    
    if (!requiredVersion) {
      const packageType = isUniversalForwarder ? 'Universal Forwarder' : 'Enterprise';
      message.error(`Please select a Splunk ${packageType} version first before adding components`);
      return;
    }
    
    try {
      // Map component types to available package types
      const getPackageType = (componentType: string) => {
        switch (componentType) {
          case 'splunk_cm':
          case 'splunk_deployer':
          case 'splunk_search_head':
          case 'splunk_indexer':
          case 'splunk_deployment_server':
          case 'splunk_license_master':
          case 'splunk_monitoring_console':
          case 'splunk_hf':
            return 'splunk_enterprise'; // All these use Enterprise package
          case 'splunk_uf':
            return 'splunk_uf'; // Universal Forwarder uses UF package
          default:
            return 'splunk_enterprise'; // Default to Enterprise
        }
      };

      const packageType = getPackageType(type);
      console.log(`Looking for package type: ${packageType} for component: ${type}`);
      
      // Auto-assign host if available
      let hostId: number | undefined;
      let host: Host | undefined;
      
      if (availableHosts.length > 0) {
        const componentIndex = components.length;
        const hostIndex = componentIndex % availableHosts.length;
        hostId = availableHosts[hostIndex].id;
        host = availableHosts[hostIndex];
      }
      
            // Get package for this component type with selected version
      const packages = await packageService.getPackages({ 
        package_type: packageType,
        vendor: 'Splunk Inc.',
        status: 'active'
      });
      
      console.log(`Found ${packages.length} packages for type ${packageType}:`, packages);
      
      // Find package with selected version, fallback to default or first available
      let selectedPackage = packages.find(pkg => pkg.version === requiredVersion);
      if (!selectedPackage) {
        selectedPackage = packages.find(pkg => pkg.is_default) || packages[0];
      }
      
      if (!selectedPackage) {
        // Fallback: try to get any Splunk package
        console.log('No specific package found, trying fallback...');
        const fallbackPackages = await packageService.getPackages({ 
          vendor: 'Splunk Inc.',
          status: 'active'
        });
        
        if (fallbackPackages.length === 0) {
          message.error(`No Splunk packages available in database. Please add packages first.`);
          return;
        }
        
        // Use the first available Splunk package as fallback
        const fallbackPackage = fallbackPackages[0];
        console.log(`Using fallback package: ${fallbackPackage.name} v${fallbackPackage.version}`);
        
        const newComponent: SplunkComponent = {
          type,
          hostId,
          host,
          packageId: fallbackPackage.id,
          package: fallbackPackage,
          isConfigured: true
        };
        
        setComponents(prev => [...prev, newComponent]);
        message.success(`Added ${type} using fallback package: ${fallbackPackage.name} v${fallbackPackage.version}`);
        return;
      }

      const newComponent: SplunkComponent = {
        type,
        hostId,
        host,
        packageId: selectedPackage.id, // Removed as package management is removed
        package: selectedPackage, // Removed as package management is removed
        isConfigured: true // Auto-configured with selected package
      };
      
      setComponents(prev => [...prev, newComponent]);
      message.success(`Added ${type}`);
    } catch (error) {
      console.error('Failed to add component:', error);
      message.error('Failed to add component');
    }
  };

  // Remove component
  const removeComponent = (index: number) => {
    setComponents(prev => prev.filter((_, i) => i !== index));
    message.success('Component removed');
  };

  // Show component selection modal
  const showComponentSelection = () => {
    setComponentModalVisible(true);
  };

  // Check if host can accommodate multiple roles
  const canHostAccommodateRole = (hostId: number, componentType: string) => {
    const host = availableHosts.find(h => h.id === hostId);
    if (!host) return false;
    
    // Get existing components on this host
    const existingComponents = components.filter(c => c.hostId === hostId);
    
    // Check if this component type is already on this host
    const hasSameType = existingComponents.some(c => c.type === componentType);
    if (hasSameType) return false; // Can't have duplicate component types on same host
    
    // Define role compatibility rules
    const roleCompatibility: Record<string, string[]> = {
      'splunk_license_master': ['splunk_monitoring_console', 'splunk_deployment_server'],
      'splunk_monitoring_console': ['splunk_license_master', 'splunk_deployment_server'],
      'splunk_deployment_server': ['splunk_license_master', 'splunk_monitoring_console'],
      'splunk_cm': ['splunk_deployment_server'],
      'splunk_deployer': ['splunk_deployment_server'],
      'splunk_search_head': ['splunk_deployment_server'],
      'splunk_indexer': ['splunk_deployment_server'],
      'splunk_hf': ['splunk_deployment_server'],
      'splunk_uf': [], // UF can't share hosts with other roles
      'splunk_enterprise': ['splunk_deployment_server']
    };
    
    // Check if existing components are compatible with new component
    const newComponentRules: string[] = roleCompatibility[componentType] || [];
    const existingComponentTypes = existingComponents.map(c => c.type);
    
    // All existing components must be compatible with the new one
    return existingComponentTypes.every(existingType => 
      newComponentRules.includes(existingType) || 
      roleCompatibility[existingType]?.includes(componentType)
    );
  };

  // Get recommended hosts for a component
  const getRecommendedHosts = (componentType: string) => {
    interface HostRecommendation {
      host: Host;
      priority: 'high' | 'medium' | 'low';
      reason: string;
      existingRoles: number;
    }
    
    const recommendations: HostRecommendation[] = [];
    
    // First priority: hosts with compatible existing components
    for (const host of availableHosts) {
      if (canHostAccommodateRole(host.id, componentType)) {
        const existingComponents = components.filter(c => c.hostId === host.id);
        recommendations.push({
          host,
          priority: 'high',
          reason: `Compatible with existing ${existingComponents.map(c => c.type.replace('splunk_', '')).join(', ')}`,
          existingRoles: existingComponents.length
        });
      }
    }
    
    // Second priority: empty hosts
    const emptyHosts = availableHosts.filter(host => 
      !components.some(c => c.hostId === host.id)
    );
    emptyHosts.forEach(host => {
      recommendations.push({
        host,
        priority: 'medium',
        reason: 'Empty host - good for new roles',
        existingRoles: 0
      });
    });
    
    // Third priority: hosts with deployment server (can manage this component)
    const deploymentServerHosts = availableHosts.filter(host => 
      components.some(c => c.hostId === host.id && c.type === 'splunk_deployment_server')
    );
    deploymentServerHosts.forEach(host => {
      if (!recommendations.some(r => r.host.id === host.id)) {
        recommendations.push({
          host,
          priority: 'low',
          reason: 'Has Deployment Server - can manage this component',
          existingRoles: components.filter(c => c.hostId === host.id).length
        });
      }
    });
    
    return recommendations.sort((a, b) => {
      if (a.priority === 'high' && b.priority !== 'high') return -1;
      if (b.priority === 'high' && a.priority !== 'high') return 1;
      if (a.priority === 'medium' && b.priority === 'low') return -1;
      if (b.priority === 'medium' && a.priority === 'low') return 1;
      return a.existingRoles - b.existingRoles; // Prefer hosts with fewer roles
    });
  };

  // Update component host
  const updateComponentHost = (index: number, hostId: number) => {
    const host = availableHosts.find(h => h.id === hostId);
    setComponents(prev => prev.map((comp, i) => 
      i === index ? { ...comp, hostId, host, isConfigured: true } : comp
    ));
    message.success('Component host updated');
  };

  // Select cluster for building
  const selectCluster = (cluster: any) => {
    console.log('Selecting cluster:', cluster);
    setSelectedCluster(cluster);
    setShowClusterModal(false);
    setBuildSaved(false); // Reset build saved state for new cluster
    message.success(`Selected cluster: ${cluster.cluster_name}`);
  };

  // Deploy environment
  const deployEnvironment = async () => {
    if (components.length === 0) {
      message.warning('No components to deploy');
      return;
    }

    if (!selectedCluster) {
      message.error('Please select a cluster first');
      return;
    }

    if (!buildSaved) {
      message.error('Please save your build configuration first before deploying. Use the "Save Build" button to update cluster configuration files with actual host IPs.');
      return;
    }

    const unconfiguredComponents = components.filter(comp => !comp.isConfigured);
    if (unconfiguredComponents.length > 0) {
      message.warning(`Please configure ${unconfiguredComponents.length} component(s) before deployment`);
      return;
    }

    setDeployModalVisible(true);
    setDeploying(true);
    setDeployResults([]);

    try {
      const results = [];
      
      // Auto-assign hosts if not already assigned
      const availableHosts = await hostService.getAllHosts();
      const activeHosts = availableHosts.filter(host => host.is_active);
      
      if (activeHosts.length === 0) {
        message.error('No active hosts available for deployment');
        return;
      }

      // Check for existing jobs to prevent duplicates
      const existingJobs = await jobService.getAllJobs();
      const duplicateCheck = new Map<string, boolean>();

      for (let i = 0; i < components.length; i++) {
        const component = components[i];
        
        // Update progress
        const progress = Math.round(((i + 1) / components.length) * 100);
        setDeploymentProgress(progress);
        
        // Auto-assign host if not already assigned
        if (!component.hostId) {
          const hostIndex = i % activeHosts.length;
          component.hostId = activeHosts[hostIndex].id;
          component.host = activeHosts[hostIndex];
        }

        // Check for existing jobs for this host and component type
        const host = availableHosts.find(h => h.id === component.hostId);
        const duplicateKey = `${component.hostId}-${component.type}`;
        
        if (duplicateCheck.has(duplicateKey)) {
          results.push({
            componentType: component.type,
            status: 'skipped',
            message: `Skipped: Duplicate component type for host ${host?.hostname || component.hostId}`,
            jobId: null
          });
          continue;
        }

        // Check if there's already a pending or running job for this host and component type
        const existingJob = existingJobs.find(job => 
          job.host_id === component.hostId && 
          job.job_type === (component.type === 'splunk_uf' ? 'splunk_uf_install' : 'splunk_enterprise_install') &&
          ['pending', 'running'].includes(job.status)
        );

        if (existingJob) {
          results.push({
            componentType: component.type,
            status: 'skipped',
            message: `Skipped: Job already exists (${existingJob.job_id}) for host ${host?.hostname || component.hostId}`,
            jobId: existingJob.job_id
          });
          continue;
        }

        duplicateCheck.set(duplicateKey, true);

        try {
          // Get package details for deployment
          let packageDetails: SoftwarePackage | undefined; // Removed as package management is removed
          if (component.packageId) {
            try {
              packageDetails = await packageService.getPackage(component.packageId);
            } catch (error) {
              console.error(`Failed to get package details for component ${component.type}:`, error);
            }
          }

          // Use standard configuration with package overrides
          const parameters = {
            version: component.type === 'splunk_uf' ? selectedUFVersion : selectedEnterpriseVersion || packageDetails?.version || '9.1.1', // Removed as package management is removed
            port: STANDARD_CONFIG.defaultPorts.management, // Default management port
            admin_password: STANDARD_CONFIG.adminPassword,
            install_dir: STANDARD_CONFIG.installDir,
            user: STANDARD_CONFIG.runUser, // Backend expects 'user' parameter
            // Add cluster information for configuration file copying
            cluster_name: selectedCluster.cluster_name,
            cluster_role: component.type.replace('splunk_', '')
          };

          let job;
          if (component.type === 'splunk_uf') {
            job = await jobService.installSplunkUF(component.hostId, parameters);
          } else {
            // For all other component types, use enterprise installation
            job = await jobService.installSplunkEnterprise(component.hostId, parameters);
          }

          results.push({
            componentType: component.type,
            status: 'success',
            message: `Job created: ${job.job_id}`,
            jobId: job.job_id
          });
        } catch (error: any) {
          results.push({
            componentType: component.type,
            status: 'error',
            message: error.message || 'Deployment failed'
          });
        }
      }

      setDeployResults(results);
      
      // Show success message
      const successCount = results.filter(r => r.status === 'success').length;
      if (successCount === results.length) {
        message.success(`Successfully deployed ${successCount} components to ${selectedCluster.cluster_name}!`);
      } else if (successCount > 0) {
        message.warning(`Deployed ${successCount}/${results.length} components successfully. Check results for details.`);
      } else {
        message.error('Deployment failed for all components. Check results for details.');
      }
      
    } catch (error) {
      console.error('Deployment failed:', error);
      message.error('Deployment failed');
    } finally {
      setDeploying(false);
      setDeploymentProgress(0);
    }
  };

  // Save build configuration
  const saveBuildConfiguration = async () => {
    if (!selectedCluster) {
      message.error('Please select a cluster first to save the build configuration.');
      return;
    }

    if (components.length === 0) {
      message.warning('No components to save. Please add components first.');
      return;
    }

    const unconfiguredComponents = components.filter(comp => !comp.isConfigured);
    if (unconfiguredComponents.length > 0) {
      message.warning(`Please configure ${unconfiguredComponents.length} component(s) before saving the build.`);
      return;
    }

    try {
      message.loading('Saving build configuration...', 0);
      
      const buildData = {
        cluster_name: selectedCluster.cluster_name,
        components: components.map(comp => ({
          type: comp.type,
          hostId: comp.hostId,
          host: comp.host,
          packageId: comp.packageId,
          package: comp.package,
          isConfigured: comp.isConfigured
        }))
      };
      
      const results = await workflowsService.saveBuildConfiguration(buildData);
      
      message.destroy();
      
      if (results.success) {
        message.success('Build configuration saved successfully!');
        console.log('Build configuration saved:', results);
        
        // Show what was updated
        if (results.host_mapping) {
          message.info(`Updated configuration files with host mappings: ${Object.entries(results.host_mapping).map(([key, ip]) => `${key}: ${ip}`).join(', ')}`);
        }
        setBuildSaved(true);
      } else {
        message.error(`Failed to save build configuration: ${results.message}`);
      }
    } catch (error: any) {
      message.destroy();
      console.error('Failed to save build configuration:', error);
      message.error('Failed to save build configuration');
    }
  };

  return (
    <div className="build-page" style={{ height: '100vh', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <div className="build-header" style={{ flexShrink: 0 }}>
        <Row justify="space-between" align="middle">
          <Col>
            <Title level={2} style={{ margin: 0, color: '#ffffff' }}>
              <ClusterOutlined style={{ marginRight: 12, color: '#1890ff' }} />
              Splunk Environment Builder
            </Title>
            <Text style={{ color: '#8c8c8c' }}>
              Simple form-based Splunk cluster deployment with automatic configuration
            </Text>
          </Col>
          <Col>
            <Space>
              <Button icon={<ReloadOutlined />} onClick={fetchHosts}>
                Refresh Hosts
              </Button>
              <Button icon={<EyeOutlined />} onClick={() => window.open('/database/files', '_blank')}>
                Manage Clusters
              </Button>
            </Space>
          </Col>
        </Row>
      </div>

      <div className="build-content" style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        {/* Main Content */}
        <div className="build-main">
          {/* Cluster Selection */}
          <Card title="Cluster Selection" style={{ marginBottom: 24 }}>
            {!selectedCluster ? (
              <div>
                <Alert
                  message="Cluster Selection Required"
                  description="Please select a cluster below to start building your Splunk environment"
                  type="warning"
                  showIcon
                  style={{ marginBottom: 16 }}
                />
                
                {clustersLoading ? (
                  <div style={{ textAlign: 'center', padding: '20px 0' }}>
                    <Spin size="large" />
                    <div style={{ color: '#8c8c8c', marginTop: 8 }}>
                      Loading clusters...
                    </div>
                  </div>
                ) : existingClusters.length > 0 ? (
                  <div style={{ display: 'grid', gap: 12 }}>
                    {existingClusters.filter(cluster => cluster && cluster.cluster_name).map((cluster) => (
                      <div
                        key={cluster.cluster_name}
                        onClick={() => selectCluster(cluster)}
                        style={{
                          padding: 16,
                          backgroundColor: '#2a2a2a',
                          border: '2px solid #404040',
                          borderRadius: 8,
                          cursor: 'pointer',
                          transition: 'all 0.3s ease'
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.backgroundColor = '#3a3a3a';
                          e.currentTarget.style.borderColor = '#1890ff';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.backgroundColor = '#2a2a2a';
                          e.currentTarget.style.borderColor = '#404040';
                        }}
                      >
                        <div style={{ 
                          display: 'flex', 
                          alignItems: 'center', 
                          justifyContent: 'space-between',
                          marginBottom: 8
                        }}>
                          <Text strong style={{ color: '#ffffff', fontSize: '14px' }}>
                            {cluster.cluster_name}
                          </Text>
                          <Tag color="blue" style={{ fontSize: '10px' }}>
                            {Math.floor((cluster.total_folders || 16) / 2)} roles
                          </Tag>
                        </div>
                        
                        <div style={{ 
                          display: 'flex', 
                          alignItems: 'center', 
                          justifyContent: 'space-between',
                          fontSize: '11px',
                          color: '#8c8c8c'
                        }}>
                          <span>Created: {cluster.created_at ? new Date(cluster.created_at).toLocaleDateString() : 'Unknown'}</span>
                          <span>{cluster.components?.length || 8} components</span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <Empty
                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                    description="No clusters found"
                    style={{ color: '#8c8c8c' }}
                  >
                    <Text style={{ color: '#8c8c8c', fontSize: '12px' }}>
                      Create your first cluster in Files → Clustering to get started
                    </Text>
                  </Empty>
                )}
              </div>
            ) : (
              <Alert
                message={`Selected: ${selectedCluster.cluster_name}`}
                description={`Building within cluster: ${selectedCluster.cluster_name}`}
                type="success"
                showIcon
                action={
                  <Button size="small" onClick={() => setSelectedCluster(null)}>
                    Change Cluster
                  </Button>
                }
              />
            )}
          </Card>

                     {/* Component Management */}
           {selectedCluster && (
             <Card 
               title={
                 <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                   <span>Component Management</span>
                   <Tag color="blue">{components.length} components</Tag>
                 </div>
               } 
               style={{ marginBottom: 24 }}
             >
               {/* Splunk Version Selection */}
               <div style={{ 
                 marginBottom: 24, 
                 padding: 16, 
                 backgroundColor: '#1a1a1a', 
                 borderRadius: 6,
                 border: '1px solid #303030'
               }}>
                 <Title level={5} style={{ color: '#ffffff', marginBottom: 16 }}>
                   Splunk Package Versions
                 </Title>
                 
                 <Row gutter={24}>
                   <Col span={12}>
                     <div style={{ marginBottom: 12 }}>
                       <Text strong style={{ color: '#ffffff', marginRight: 12 }}>
                         Enterprise Version:
                       </Text>
                       <Select
                         value={selectedEnterpriseVersion}
                         onChange={setSelectedEnterpriseVersion}
                         style={{ width: '100%' }}
                         placeholder="Select Enterprise version"
                       >
                         {Array.from(new Set(
                           availablePackages
                             .filter(pkg => pkg.package_type === 'splunk_enterprise')
                             .map(pkg => pkg.version)
                         )).map(version => (
                           <Option key={version} value={version}>
                             {version}
                           </Option>
                         ))}
                       </Select>
                     </div>
                     <Tag color="blue" style={{ marginBottom: 8 }}>
                       {availablePackages.filter(pkg => 
                         pkg.package_type === 'splunk_enterprise' && 
                         pkg.version === selectedEnterpriseVersion
                       ).length} Enterprise packages available
                     </Tag>
                     <Text style={{ color: '#8c8c8c', fontSize: '11px' }}>
                       Used for: CM, Deployer, Search Head, Indexer, Deployment Server, License Master, Monitoring Console, Heavy Forwarder
                     </Text>
                   </Col>
                   
                   <Col span={12}>
                     <div style={{ marginBottom: 12 }}>
                       <Text strong style={{ color: '#ffffff', marginRight: 12 }}>
                         Universal Forwarder Version:
                       </Text>
                       <Select
                         value={selectedUFVersion}
                         onChange={setSelectedUFVersion}
                         style={{ width: '100%' }}
                         placeholder="Select UF version"
                       >
                         {Array.from(new Set(
                           availablePackages
                             .filter(pkg => pkg.package_type === 'splunk_uf')
                             .map(pkg => pkg.version)
                         )).map(version => (
                           <Option key={version} value={version}>
                             {version}
                           </Option>
                         ))}
                       </Select>
                     </div>
                     <Tag color="green" style={{ marginBottom: 8 }}>
                       {availablePackages.filter(pkg => 
                         pkg.package_type === 'splunk_uf' && 
                         pkg.version === selectedUFVersion
                       ).length} UF packages available
                     </Tag>
                     <Text style={{ color: '#8c8c8c', fontSize: '11px' }}>
                       Used for: Universal Forwarder only
                     </Text>
                   </Col>
                 </Row>
                 
                 <div style={{ 
                   marginTop: 16, 
                   padding: 12, 
                   backgroundColor: '#2a2a2a', 
                   borderRadius: 4,
                   border: '1px solid #404040'
                 }}>
                   <Text style={{ color: '#ffffff', fontSize: '12px', fontWeight: 'bold', marginBottom: 8 }}>
                     💡 Package Assignment Rules:
                   </Text>
                   <div style={{ color: '#8c8c8c', fontSize: '11px', lineHeight: '1.5' }}>
                     <div>• <strong>Enterprise Package:</strong> All components except Universal Forwarder</div>
                     <div>• <strong>Universal Forwarder Package:</strong> Universal Forwarder components only</div>
                     <div>• <strong>Automatic Assignment:</strong> Components automatically get the appropriate package based on their type</div>
                   </div>
                 </div>
               </div>

               <div style={{ marginBottom: 16 }}>
                 <div style={{ display: 'flex', alignItems: 'center', marginBottom: 12 }}>
                   <Text strong style={{ color: '#ffffff', marginRight: 12 }}>
                     Multi-Role Host Mode:
                   </Text>
                   <Button
                     type={multiRoleMode ? 'primary' : 'default'}
                     icon={<ClusterOutlined />}
                     onClick={() => setMultiRoleMode(!multiRoleMode)}
                     style={{ marginRight: 8 }}
                   >
                     {multiRoleMode ? 'Enabled' : 'Disabled'}
                   </Button>
                   <Tag color={multiRoleMode ? 'green' : 'orange'}>
                     {multiRoleMode ? 'Multiple roles per host allowed' : 'Single role per host'}
                   </Tag>
                 </div>
                 
                 {multiRoleMode && (
                   <Alert
                     message="Multi-Role Mode Active"
                     description="You can now assign multiple compatible roles to the same host. License Master + Monitoring Console is a common combination."
                     type="info"
                     showIcon
                     style={{ marginBottom: 12, fontSize: '11px' }}
                   />
                 )}
                 
                 <div>
                   <Button
                     type="primary"
                     icon={<ClusterOutlined />}
                     onClick={createCompleteCluster}
                     style={{ marginRight: 8 }}
                   >
                     Create Complete Cluster
                   </Button>
                   <Button
                     icon={<PlusOutlined />}
                     onClick={showComponentSelection}
                   >
                     Add Component
                   </Button>
                 </div>
               </div>

              {components.length === 0 ? (
                <Empty
                  description="No components added yet"
                  image={Empty.PRESENTED_IMAGE_SIMPLE}
                >
                  <Text style={{ color: '#8c8c8c', fontSize: '12px' }}>
                    Use the buttons above to add components or create a complete cluster
                  </Text>
                </Empty>
              ) : (
                                 <div className="component-list-container">
                   {components.length > 6 && (
                     <div className="scroll-indicator">
                       📜 Scroll to see all {components.length} components
                     </div>
                   )}
                   {components.map((component, index) => {
                     const componentInfo = SPLUNK_COMPONENTS[component.type as keyof typeof SPLUNK_COMPONENTS];
                     return (
                       <Card
                         key={index}
                         size="small"
                         className="component-card"
                         style={{ 
                           borderLeftColor: componentInfo?.color || '#1890ff'
                         }}
                       >
                        <Row gutter={16} align="middle">
                          <Col span={6}>
                            <div style={{ display: 'flex', alignItems: 'center' }}>
                              <div style={{ 
                                color: componentInfo?.color || '#1890ff', 
                                fontSize: '16px', 
                                marginRight: 8 
                              }}>
                                {componentInfo?.icon}
                              </div>
                              <div>
                                <div style={{ color: '#ffffff', fontSize: '12px', fontWeight: 'bold' }}>
                                  {componentInfo?.label || component.type}
                                </div>
                                <div style={{ color: '#8c8c8c', fontSize: '10px' }}>
                                  {component.type === 'splunk_uf' ? selectedUFVersion : selectedEnterpriseVersion || 'No Version Selected'}
                                </div>
                              </div>
                            </div>
                          </Col>
                          
                          <Col span={6}>
                            <Select
                              placeholder="Select Host"
                              value={component.hostId}
                              onChange={(value) => updateComponentHost(index, value)}
                              style={{ width: '100%' }}
                              showSearch
                              filterOption={(input, option) =>
                                (option?.children?.toString() || '').toLowerCase().includes(input.toLowerCase())
                              }
                            >
                              {getRecommendedHosts(component.type).map((rec) => (
                                <Option key={rec.host.id} value={rec.host.id}>
                                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <span>{rec.host.hostname} ({rec.host.ip_address})</span>
                                    <Tag 
                                      color={rec.priority === 'high' ? 'green' : rec.priority === 'medium' ? 'blue' : 'orange'}
                                    >
                                      {rec.priority}
                                    </Tag>
                                  </div>
                                </Option>
                              ))}
                            </Select>
                            {component.hostId && (
                              <div style={{ marginTop: 4 }}>
                                <Text style={{ color: '#8c8c8c', fontSize: '10px' }}>
                                  {multiRoleMode ? 'Multi-role enabled' : 'Single role only'}
                                </Text>
                              </div>
                            )}
                          </Col>
                          
                          <Col span={6}>
                            <div style={{ 
                              padding: '8px 12px', 
                              backgroundColor: '#2a2a2a', 
                              borderRadius: 4,
                              marginTop: 8
                            }}>
                              <Text style={{ color: '#8c8c8c', fontSize: '10px' }}>
                                Version: {component.type === 'splunk_uf' ? selectedUFVersion : selectedEnterpriseVersion || 'Not Set'}
                              </Text>
                            </div>
                          </Col>
                          
                          <Col span={4}>
                            <Tag color={component.isConfigured ? 'green' : 'orange'}>
                              {component.isConfigured ? 'Configured' : 'Not Configured'}
                            </Tag>
                          </Col>
                          
                          <Col span={2}>
                            <Button
                              danger
                              size="small"
                              icon={<CloseOutlined />}
                              onClick={() => removeComponent(index)}
                            />
                          </Col>
                        </Row>
                      </Card>
                    );
                  })}
                </div>
              )}
            </Card>
          )}

          {/* Deployment */}
          {selectedCluster && components.length > 0 && (
            <Card title="Deployment" style={{ marginBottom: 24 }}>
              <div style={{ marginBottom: 16 }}>
                {buildSaved ? (
                  <Alert
                    message="Build Configuration Saved"
                    description={`${components.filter(c => c.isConfigured).length} of ${components.length} components are configured and ready for deployment. Build configuration has been saved with actual host IPs.`}
                    type="success"
                    showIcon
                  />
                ) : (
                  <Alert
                    message="Build Configuration Not Saved"
                    description={`${components.filter(c => c.isConfigured).length} of ${components.length} components are configured, but you must save the build configuration first to update cluster files with actual host IPs.`}
                    type="warning"
                    showIcon
                  />
                )}
              </div>
              
              <div style={{ display: 'flex', gap: 12, marginBottom: 16 }}>
                <Button
                  type="primary"
                  size="large"
                  icon={<PlayCircleOutlined />}
                  onClick={deployEnvironment}
                  disabled={!components.every(c => c.isConfigured) || !buildSaved}
                  style={{ flex: 1 }}
                >
                  {buildSaved ? 'Deploy All Components' : 'Save Build First'}
                </Button>
                
                <Button
                  type="default"
                  size="large"
                  icon={<DeleteOutlined />}
                  onClick={async () => {
                    try {
                      const result = await jobService.cleanupDuplicateJobs();
                      if (result.success) {
                        message.success(result.message);
                        // Refresh the page or update state as needed
                      } else {
                        message.error(`Cleanup failed: ${result.message}`);
                      }
                    } catch (error) {
                      message.error('Failed to cleanup duplicate jobs');
                    }
                  }}
                  title="Clean up duplicate jobs for the same host and type"
                >
                  Cleanup Duplicates
                </Button>
              </div>
              
              {!buildSaved && (
                <div style={{ marginTop: 12, textAlign: 'center' }}>
                  <Text style={{ color: '#faad14', fontSize: '12px' }}>
                    ⚠️ You must save your build configuration before deployment
                  </Text>
                </div>
              )}
            </Card>
          )}

          {/* Build Configuration Save */}
          {selectedCluster && components.length > 0 && (
            <Card title="Build Configuration" style={{ marginBottom: 24 }}>
              <div style={{ marginBottom: 16 }}>
                <Alert
                  message="Configuration Files Ready"
                  description="Your build configuration is ready. Click 'Save Build' to update cluster configuration files with actual host IPs before deployment."
                  type="info"
                  showIcon
                />
              </div>
              
              <div style={{ marginBottom: 16 }}>
                <Text style={{ color: '#8c8c8c', fontSize: '12px' }}>
                  This will update the following configuration files with actual host IPs:
                </Text>
                <ul style={{ color: '#8c8c8c', fontSize: '11px', marginTop: 8, paddingLeft: 20 }}>
                  <li>Cluster Manager server.conf - manager_uri</li>
                  <li>Indexer server.conf - manager_uri and license manager_uri</li>
                  <li>Search Head server.conf - manager_uri and deployer_uri</li>
                  <li>Universal Forwarder outputs.conf - indexer discovery</li>
                  <li>All other component configurations</li>
                </ul>
              </div>
              
              <Button
                type="default"
                size="large"
                icon={<ClusterOutlined />}
                onClick={saveBuildConfiguration}
                disabled={!components.every(c => c.isConfigured)}
                style={{ marginRight: 16 }}
              >
                Save Build
              </Button>
              
              <Text style={{ color: '#8c8c8c', fontSize: '11px' }}>
                Save your build configuration to update cluster files with actual host IPs
              </Text>
            </Card>
          )}

                     {/* Host Overview */}
           {multiRoleMode && components.length > 0 && (
             <Card title="Multi-Role Host Overview" style={{ marginBottom: 24 }}>
               <div style={{ marginBottom: 16 }}>
                 <Text style={{ color: '#8c8c8c', fontSize: '12px' }}>
                   Hosts with multiple Splunk roles assigned:
                 </Text>
               </div>
               
               {(() => {
                 const hostRoleMap = new Map<number, { host: Host; roles: string[] }>();
                 
                 components.forEach(comp => {
                   if (comp.hostId) {
                     if (!hostRoleMap.has(comp.hostId)) {
                       const host = availableHosts.find(h => h.id === comp.hostId);
                       if (host) {
                         hostRoleMap.set(comp.hostId, { host, roles: [] });
                       }
                     }
                     const hostData = hostRoleMap.get(comp.hostId);
                     if (hostData) {
                       hostData.roles.push(comp.type.replace('splunk_', ''));
                     }
                   }
                 });
                 
                 const multiRoleHosts = Array.from(hostRoleMap.values()).filter(h => h.roles.length > 1);
                 
                 if (multiRoleHosts.length === 0) {
                   return (
                     <Empty
                       description="No multi-role hosts yet"
                       image={Empty.PRESENTED_IMAGE_SIMPLE}
                       style={{ color: '#8c8c8c' }}
                     >
                       <Text style={{ color: '#8c8c8c', fontSize: '11px' }}>
                         Assign multiple compatible roles to the same host to see them here
                       </Text>
                     </Empty>
                   );
                 }
                 
                 return (
                   <div style={{ display: 'grid', gap: 12 }}>
                     {multiRoleHosts.map(({ host, roles }) => (
                       <div
                         key={host.id}
                         style={{
                           padding: 12,
                           backgroundColor: '#2a2a2a',
                           border: '1px solid #404040',
                           borderRadius: 6
                         }}
                       >
                         <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                           <Text strong style={{ color: '#ffffff', fontSize: '12px' }}>
                             {host.hostname} ({host.ip_address})
                           </Text>
                           <Tag color="green">{roles.length} roles</Tag>
                         </div>
                         <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                           {roles.map(role => (
                             <Tag key={role} color="blue" style={{ fontSize: '10px' }}>
                               {role.toUpperCase()}
                             </Tag>
                           ))}
                         </div>
                       </div>
                     ))}
                   </div>
                 );
               })()}
             </Card>
           )}

           {/* Back to Top Button */}
           {components.length > 8 && (
             <div style={{ textAlign: 'center', marginTop: 16 }}>
               <Button
                 type="text"
                 icon={<ClusterOutlined />}
                 onClick={() => {
                   const mainElement = document.querySelector('.build-main');
                   if (mainElement) {
                     mainElement.scrollTo({ top: 0, behavior: 'smooth' });
                   }
                 }}
                 style={{ color: '#1890ff' }}
               >
                 Back to Top
               </Button>
             </div>
           )}
        </div>
      </div>

      {/* Cluster Selection Required Alert */}
      {showClusterModal && !selectedCluster && existingClusters.length > 0 && (
        <Modal
          title="Cluster Selection Required"
          open={true}
          footer={null}
          closable={true}
          onCancel={() => setShowClusterModal(false)}
          width={500}
          maskClosable={false}
          style={{ top: '20%' }}
        >
          <div style={{ textAlign: 'center', padding: '20px 0' }}>
            <ClusterOutlined style={{ fontSize: 48, color: '#1890ff', marginBottom: 16 }} />
            <Title level={4} style={{ color: '#ffffff', marginBottom: 16 }}>
              Select a Cluster First
            </Title>
            <Text style={{ color: '#8c8c8c', display: 'block', marginBottom: 24 }}>
              Please select an existing cluster from the <strong>Cluster Selection section above</strong> to start building your Splunk environment.
              <br />
              <br />
              You can create new clusters in the Files → Clustering tab.
            </Text>
            <div style={{ display: 'flex', gap: 8, justifyContent: 'center' }}>
              <Button 
                type="primary" 
                onClick={() => window.open('/database/files', '_blank')}
                icon={<ClusterOutlined />}
              >
                Go to Clustering
              </Button>
              <Button 
                onClick={() => setShowClusterModal(false)}
              >
                I'll Select a Cluster
              </Button>
            </div>
          </div>
        </Modal>
      )}

      {/* No Clusters Available Alert */}
      {!selectedCluster && existingClusters.length === 0 && (
        <Modal
          title="No Clusters Available"
          open={true}
          footer={null}
          closable={false}
          width={500}
        >
          <div style={{ textAlign: 'center', padding: '20px 0' }}>
            <ClusterOutlined style={{ fontSize: 48, color: '#fa8c16', marginBottom: 16 }} />
            <Title level={4} style={{ color: '#ffffff', marginBottom: 16 }}>
              Create Your First Cluster
            </Title>
            <Text style={{ color: '#8c8c8c', display: 'block', marginBottom: 24 }}>
              No clusters are available yet. Please create your first cluster in the Files → Clustering tab.
              <br />
              <br />
              After creating a cluster, return here to start building your Splunk environment.
            </Text>
            <Button 
              type="primary" 
              onClick={() => window.open('/database/files', '_blank')}
              icon={<ClusterOutlined />}
            >
              Go to Clustering
            </Button>
          </div>
        </Modal>
      )}

      {/* Deployment Modal */}
      <Modal
        title="Deploy Splunk Environment"
        open={deployModalVisible}
        onCancel={() => setDeployModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setDeployModalVisible(false)}>
            Close
          </Button>
        ]}
        width={800}
      >
        {deploying ? (
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <Spin size="large" />
            <div style={{ marginTop: 16, color: '#ffffff', marginBottom: 16 }}>
              Deploying Splunk environment...
            </div>
            <div style={{ width: '100%', marginBottom: 16 }}>
              <div style={{ 
                width: '100%', 
                height: 8, 
                backgroundColor: '#2a2a2a', 
                borderRadius: 4,
                overflow: 'hidden'
              }}>
                <div style={{
                  width: `${deploymentProgress}%`,
                  height: '100%',
                  backgroundColor: '#1890ff',
                  transition: 'width 0.3s ease'
                }} />
              </div>
              <div style={{ marginTop: 8, color: '#8c8c8c', fontSize: '12px' }}>
                {deploymentProgress}% Complete
              </div>
            </div>
          </div>
        ) : deployResults.length > 0 ? (
          <div>
            <Alert
              message={`Deployment completed with ${deployResults.filter(r => r.status === 'success').length} successful and ${deployResults.filter(r => r.status === 'error').length} failed`}
              type={deployResults.some(r => r.status === 'error') ? 'warning' : 'success'}
              showIcon
              style={{ marginBottom: 16 }}
            />
            
            <List
              size="small"
              dataSource={deployResults}
              renderItem={(result) => (
                <List.Item key={result.componentType || `result-${Date.now()}`}>
                  <List.Item.Meta
                    avatar={
                      <Avatar
                        icon={
                          result.status === 'success' ? <CheckCircleOutlined /> :
                          result.status === 'error' ? <CloseOutlined /> :
                          <CloseOutlined />
                        }
                        style={{
                          backgroundColor: result.status === 'success' ? '#52c41a' :
                                        result.status === 'error' ? '#f5222d' : '#faad14'
                        }}
                      />
                    }
                    title={
                      <div style={{ color: '#ffffff', fontSize: '12px' }}>
                        {SPLUNK_COMPONENTS[result.componentType as keyof typeof SPLUNK_COMPONENTS]?.label || result.componentType}
                      </div>
                    }
                    description={
                      <div style={{ color: '#8c8c8c', fontSize: '10px' }}>
                        {result.message}
                        {result.jobId && (
                          <div style={{ marginTop: 4 }}>
                            <Button
                              size="small"
                              type="link"
                              onClick={() => navigate(`/jobs?job_id=${result.jobId}`)}
                              style={{ padding: 0, height: 'auto', color: '#1890ff' }}
                            >
                              View Job
                            </Button>
                          </div>
                        )}
                      </div>
                    }
                  />
                </List.Item>
              )}
            />
          </div>
        ) : null}
      </Modal>

      {/* Component Selection Modal */}
      <Modal
        title={
          <div>
            <div>Select Splunk Component Type</div>
            <div style={{ fontSize: '12px', color: '#8c8c8c', fontWeight: 'normal', marginTop: 4 }}>
              {selectedEnterpriseVersion && (
                <span style={{ marginRight: 12 }}>
                  Enterprise: <Tag color="blue">{selectedEnterpriseVersion}</Tag>
                </span>
              )}
              {selectedUFVersion && (
                <span>
                  UF: <Tag color="green">{selectedUFVersion}</Tag>
                </span>
              )}
            </div>
          </div>
        }
        open={componentModalVisible}
        onCancel={() => setComponentModalVisible(false)}
        footer={null}
        width={800}
        style={{ top: '10%' }}
      >
        <div style={{ padding: '16px 0' }}>
          <Text style={{ color: '#8c8c8c', display: 'block', marginBottom: 24 }}>
            Choose the type of Splunk component you want to add to your environment:
          </Text>
          
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16 }}>
            {Object.entries(SPLUNK_COMPONENTS).map(([key, component]) => (
              <div
                key={key}
                onClick={() => {
                  addComponent(key);
                  setComponentModalVisible(false);
                }}
                style={{
                  padding: 16,
                  backgroundColor: '#2a2a2a',
                  border: `2px solid ${component.color}`,
                  borderRadius: 8,
                  cursor: 'pointer',
                  transition: 'all 0.3s ease',
                  textAlign: 'center'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = '#3a3a3a';
                  e.currentTarget.style.transform = 'translateY(-2px)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = '#2a2a2a';
                  e.currentTarget.style.transform = 'translateY(0)';
                }}
              >
                <div style={{ 
                  color: component.color, 
                  fontSize: '24px', 
                  marginBottom: 8 
                }}>
                  {component.icon}
                </div>
                <div style={{ 
                  color: '#ffffff', 
                  fontSize: '14px', 
                  fontWeight: 'bold',
                  marginBottom: 4
                }}>
                  {component.label}
                </div>
                <div style={{ 
                  color: '#8c8c8c', 
                  fontSize: '11px',
                  lineHeight: '1.4'
                }}>
                  {component.description}
                </div>
                <div style={{ 
                  marginTop: 8,
                  padding: '4px 8px',
                  backgroundColor: component.color,
                  color: '#ffffff',
                  borderRadius: 4,
                  fontSize: '10px',
                  fontWeight: 'bold'
                }}>
                  Port: {component.defaultPort}
                </div>
              </div>
            ))}
          </div>
          
          <div style={{ 
            marginTop: 24, 
            padding: 16, 
            backgroundColor: '#1a1a1a', 
            borderRadius: 6,
            border: '1px solid #303030'
          }}>
            <Text style={{ color: '#ffffff', fontSize: '12px', fontWeight: 'bold', marginBottom: 8 }}>
              💡 Component Information:
            </Text>
            <div style={{ color: '#8c8c8c', fontSize: '11px', lineHeight: '1.5' }}>
              <div>• <strong>Cluster Master (CM):</strong> Manages indexer cluster configuration</div>
              <div>• <strong>Deployer:</strong> Distributes configurations to search head cluster</div>
              <div>• <strong>Search Head:</strong> Provides search interface and coordinates searches</div>
              <div>• <strong>Indexer:</strong> Stores and indexes data</div>
              <div>• <strong>Deployment Server:</strong> Manages forwarder configurations</div>
              <div>• <strong>License Master:</strong> Manages Splunk licenses</div>
              <div>• <strong>Monitoring Console:</strong> Provides system monitoring</div>
              <div>• <strong>Heavy Forwarder:</strong> Processes data before forwarding</div>
              <div>• <strong>Universal Forwarder:</strong> Collects and forwards data</div>
            </div>
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default Build;
