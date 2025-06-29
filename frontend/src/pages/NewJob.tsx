import { useState, useEffect } from 'react';
import { 
  Typography, 
  Card, 
  Button, 
  Row, 
  Col, 
  Divider, 
  Modal, 
  Form, 
  Input, 
  Select, 
  Switch, 
  Steps, 
  Alert, 
  Result, 
  Spin,
  message,
  Empty,
  Tag,
  Tooltip
} from 'antd';
import { 
  CloudDownloadOutlined, 
  CodeOutlined, 
  FireOutlined, 
  ThunderboltOutlined,
  SettingOutlined,
  CheckCircleOutlined,
  UserOutlined,
  FolderOutlined,
  ArrowRightOutlined,
  DesktopOutlined,
  RightOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
// We'll handle the framer-motion import with a dynamic import to avoid build errors
// if the package isn't installed yet
// import { motion } from 'framer-motion';
import { hostService, jobService, splunkService, Host } from '../services/api';

const { Title, Text } = Typography;
const { Option } = Select;
const { Step } = Steps;

// Installation categories
enum InstallCategory {
  NONE = 'none',
  ROOT = 'root',
  SPLUNK = 'splunk',
  CRIBL = 'cribl',
  USER = 'user'
}

// Define installation type interface
interface InstallTypeOption {
  value: string;
  label: string;
}

// Installation types with proper typing
const INSTALLATION_TYPES: Record<InstallCategory, InstallTypeOption[]> = {
  [InstallCategory.NONE]: [],
  [InstallCategory.ROOT]: [
    { value: 'custom_script', label: 'Custom Script' },
    { value: 'system_update', label: 'System Update' }
  ],
  [InstallCategory.SPLUNK]: [
    { value: 'splunk_uf', label: 'Universal Forwarder' },
    { value: 'splunk_enterprise', label: 'Enterprise' },
    { value: 'splunk_heavy_forwarder', label: 'Heavy Forwarder' }
  ],
  [InstallCategory.CRIBL]: [
    { value: 'cribl_leader', label: 'Stream Leader' },
    { value: 'cribl_worker', label: 'Stream Worker' },
    { value: 'cribl_edge', label: 'Edge' }
  ],
  [InstallCategory.USER]: [
    { value: 'custom_command', label: 'Custom Command' },
    { value: 'bash_script', label: 'Bash Script' }
  ]
};

// Splunk versions
const SPLUNK_VERSIONS = ['9.4.3', '9.1.1', '9.0.5', '8.2.9', '8.1.5'];

// Cribl versions
const CRIBL_VERSIONS = ['3.4.1', '3.3.0', '3.0.5', '2.4.5'];

// Animation variants for cards
const cardVariants = {
  initial: { scale: 0.96, opacity: 0 },
  animate: { scale: 1, opacity: 1 },
  hover: { scale: 1.05, boxShadow: '0 10px 20px rgba(0,0,0,0.19), 0 6px 6px rgba(0,0,0,0.23)' },
  tap: { scale: 0.98 }
};

// Create a simple motion div component to use until framer-motion is installed
const MotionDiv: React.FC<{
  children: React.ReactNode;
  variants?: any;
  initial?: string;
  animate?: string;
  whileHover?: string;
  whileTap?: string;
  transition?: any;
}> = ({ children }) => {
  return <div className="motion-card">{children}</div>;
};

const NewJob: React.FC = () => {
  const [selectedCategory, setSelectedCategory] = useState<InstallCategory>(InstallCategory.NONE);
  const [installType, setInstallType] = useState<string>('');
  const [currentStep, setCurrentStep] = useState<number>(0);
  const [isModalVisible, setIsModalVisible] = useState<boolean>(false);
  const [form] = Form.useForm();
  const [loading, setLoading] = useState<boolean>(false);
  const [hosts, setHosts] = useState<Host[]>([]);
  const [selectedHost, setSelectedHost] = useState<Host | null>(null);
  const [hostsLoading, setHostsLoading] = useState<boolean>(true);
  const [jobId, setJobId] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [directInstallResult, setDirectInstallResult] = useState<Record<string, any> | null>(null);
  const navigate = useNavigate();

  // Fetch hosts when component mounts
  useEffect(() => {
    fetchHosts();
  }, []);

  // Set default values for the current installation type
  useEffect(() => {
    if (installType && form) {
      if (installType.includes('splunk')) {
        // Set default values for Splunk installations
        form.setFieldsValue({
          version: '9.4.3',
          run_user: 'splunk',
          install_dir: installType === 'splunk_uf' ? '/opt/splunkforwarder' : '/opt/splunk',
          admin_password: 'changeme'
        });
        console.log("Form values set in useEffect:", form.getFieldsValue());
      }
    }
  }, [installType, form]);

  // Fetch available hosts
  const fetchHosts = async (): Promise<void> => {
    try {
      setHostsLoading(true);
      const hostsData = await hostService.getAllHosts();
      // Only show active hosts
      setHosts(hostsData.filter(host => host.is_active));
    } catch (error) {
      console.error('Failed to fetch hosts:', error);
      setError('Failed to load host data');
    } finally {
      setHostsLoading(false);
    }
  };

  // Handle host selection
  const handleHostSelect = (host: Host): void => {
    setSelectedHost(host);
    setIsModalVisible(true);
    
    // Reset the form and initialize with host ID
    form.resetFields();
    
    // Explicitly set the host_id field with the host's ID
    setTimeout(() => {
      form.setFieldsValue({
        host_id: host.id
      });
      console.log("Form initialized with host_id:", form.getFieldValue('host_id'));
    }, 0);
  };

  // Handle category selection
  const handleCategorySelect = (category: InstallCategory): void => {
    setSelectedCategory(category);
    setInstallType('');
    setCurrentStep(0);
    
    // Reset form with appropriate initial values based on category
    form.resetFields();
    form.setFieldsValue({
      host_id: selectedHost?.id
    });
    
    // Initialize default values based on category
    if (category === InstallCategory.SPLUNK) {
      form.setFieldsValue({
        version: '9.4.3',
        run_user: 'splunk',
        admin_password: 'changeme'
      });
    } else if (category === InstallCategory.CRIBL) {
      form.setFieldsValue({
        version: '3.4.1',
        run_user: 'cribl'
      });
    } else {
      form.setFieldsValue({
        run_user: 'root'
      });
    }
  };

  // Handle installation type change
  const handleInstallTypeChange = (type: string): void => {
    setInstallType(type);
    
    // Create a complete form values object with all required fields
    const formValues: Record<string, any> = {
      host_id: selectedHost?.id, // Ensure host_id is always set
      install_type: type
    };
    
    // Add type-specific default values
    if (type.includes('splunk')) {
      formValues.version = '9.4.3';
      formValues.run_user = 'splunk';
      formValues.install_dir = type === 'splunk_uf' ? '/opt/splunkforwarder' : '/opt/splunk';
      formValues.admin_password = 'changeme';
    } else if (type.includes('cribl')) {
      formValues.version = '3.4.1';
      formValues.run_user = 'cribl';
      formValues.install_dir = '/opt/cribl';
    } else if (type.includes('custom_command') || type.includes('bash_script')) {
      formValues.run_user = 'root';
      formValues.command = type.includes('custom_command') ? 'echo "Hello World"' : '#!/bin/bash\n\necho "Hello World"';
    } else {
      formValues.run_user = 'root';
      formValues.install_dir = '/opt';
    }
    
    // Set all form values at once
    form.setFieldsValue(formValues);
    
    // Log the form values for debugging
    console.log(`Form values after setting ${type} defaults:`, form.getFieldsValue());
  };

  // Handle modal close
  const handleModalClose = (): void => {
    setIsModalVisible(false);
    setSelectedCategory(InstallCategory.NONE);
    setInstallType('');
    setCurrentStep(0);
    form.resetFields();
  };

  // Handle next step
  const handleNext = async (): Promise<void> => {
    try {
      // Ensure host_id is set before validation
      if (selectedHost?.id) {
        form.setFieldValue('host_id', selectedHost.id);
      }
      
      await form.validateFields();
      setCurrentStep(currentStep + 1);
    } catch (error) {
      console.error('Validation failed:', error);
    }
  };

  // Handle previous step
  const handlePrev = (): void => {
    setCurrentStep(currentStep - 1);
  };

  // Handle back to host selection
  const handleBackToHosts = (): void => {
    setSelectedHost(null);
    setSelectedCategory(InstallCategory.NONE);
    setInstallType('');
  };

  // Handle form submission
  const handleSubmit = async (): Promise<void> => {
    try {
      setLoading(true);
      setError(null);
      
      // Make sure we have the host ID from the selected host
      if (!selectedHost || !selectedHost.id) {
        throw new Error("No host selected");
      }
      
      // Set default values for required fields if missing
      const defaultValues: Record<string, any> = {
        host_id: selectedHost.id
      };
      
      // Add defaults based on installation type
      if (installType === 'splunk_uf') {
        defaultValues['version'] = '9.4.3';
        defaultValues['admin_password'] = 'changeme';
        defaultValues['install_dir'] = '/opt/splunkforwarder';
        defaultValues['run_user'] = 'splunk';
      }
      
      // Set default values in form
      form.setFieldsValue(defaultValues);
      
      // Wait for form updates to apply
      await new Promise(resolve => setTimeout(resolve, 100));
      
      // Get current form values
      const currentValues = form.getFieldsValue(true);
      console.log("Current form values before validation:", currentValues);
      
      // Validate form fields
      await form.validateFields();
      
      // Get validated values
      const values = form.getFieldsValue(true);
      console.log("Form values on submit:", values);
      
      // Always use the host ID from the selected host object
      const host_id = selectedHost.id;
      
      // Submit job based on installation type
      let job;
      let result;
      let isDirectInstall = false;
      
      switch (installType) {
        case 'splunk_uf':
          // Use direct installation for Splunk UF
          isDirectInstall = true;
          
          // Create parameters object with explicit defaults
          const splunkUFParams = {
            version: values.version || '9.4.3',
            install_dir: values.install_dir || '/opt/splunkforwarder',
            admin_password: values.admin_password || 'changeme',
            user: values.run_user || 'splunk',
            group: values.run_user || 'splunk',
            deployment_server: values.deployment_server,
            deployment_app: values.deployment_app,
            is_dry_run: values.is_dry_run || false
          };
          
          console.log("Installing Splunk UF with validated parameters:", splunkUFParams);
          
          result = await splunkService.installSplunkUF(host_id, splunkUFParams);
          
          // Set job ID for consistency in UI
          setJobId(`direct-splunk-uf-${Date.now()}`);
          setDirectInstallResult(result);
          break;
          
        case 'splunk_enterprise':
          job = await jobService.installSplunkEnterprise(host_id, values, values.is_dry_run || false);
          setJobId(job.job_id);
          break;
          
        case 'cribl_leader':
          job = await jobService.installCriblLeader(host_id, values, values.is_dry_run || false);
          setJobId(job.job_id);
          break;
          
        case 'cribl_worker':
          job = await jobService.installCriblWorker(host_id, values, values.is_dry_run || false);
          setJobId(job.job_id);
          break;
          
        case 'custom_command':
        case 'bash_script':
          // Use a generic job submission for user commands
          job = await jobService.submitCustomJob(host_id, installType, values, values.is_dry_run || false);
          setJobId(job.job_id);
          break;
          
        default:
          // For other types
          job = await jobService.installSplunkUF(host_id, values, values.is_dry_run || false);
          setJobId(job.job_id);
          break;
      }
      
      // Move to next step
      setCurrentStep(currentStep + 1);
      message.success(isDirectInstall 
        ? 'Installation completed directly via SSH' 
        : 'Job submitted successfully');
    } catch (error: any) {
      console.error('Failed to submit job:', error);
      
      // Extract error details from response if available
      let errorDetail = error.response?.data?.detail || error.message || 'Failed to submit installation job. Please try again.';
      
      // Format error detail if it's an array
      if (Array.isArray(errorDetail)) {
        errorDetail = errorDetail.map(err => err.msg || err).join(', ');
      }
      
      setError(typeof errorDetail === 'string' ? errorDetail : JSON.stringify(errorDetail));
    } finally {
      setLoading(false);
    }
  };

  // Get installation form fields based on type
  const getInstallationFormFields = (): React.ReactNode => {
    if (!installType) return null;
    
    const commonFields = (
      <>
        <Form.Item
          name="host_id"
          label="Target Host"
          initialValue={selectedHost?.id}
          rules={[{ required: true, message: 'Please select a host' }]}
          hidden={true} // Hide this since we already selected the host
        >
          <Input type="hidden" />
        </Form.Item>
        
        {!installType.includes('custom_command') && !installType.includes('bash_script') && (
          <Form.Item
            name="install_dir"
            label="Installation Directory"
            rules={[{ required: true, message: 'Please specify installation directory' }]}
          >
            <Input placeholder="/opt" prefix={<FolderOutlined />} />
          </Form.Item>
        )}

        <Form.Item
          name="run_user"
          label="Run As User"
          rules={[{ required: true, message: 'Please specify the user to run as' }]}
        >
          <Input placeholder="e.g., splunk" prefix={<UserOutlined />} />
        </Form.Item>
      </>
    );
    
    // Render fields based on installation type
    if (installType.includes('splunk')) {
      return (
        <>
          {commonFields}
          
          <Form.Item
            name="version"
            label="Splunk Version"
            initialValue="9.4.3"
            rules={[{ required: true, message: 'Please select a version' }]}
          >
            <Select placeholder="Select Splunk version" defaultValue="9.4.3">
              {SPLUNK_VERSIONS.map(version => (
                <Option key={version} value={version}>{version}</Option>
              ))}
            </Select>
          </Form.Item>
          
          {installType === 'splunk_uf' && (
            <>
              <Form.Item
                name="deployment_server"
                label={
                  <Tooltip title="Optional: Splunk Deployment Server for UF configuration">
                    Deployment Server
                  </Tooltip>
                }
              >
                <Input placeholder="deployserver:8089" />
              </Form.Item>
              
              <Form.Item
                name="deployment_app"
                label={
                  <Tooltip title="Optional: Deployment app name for UF configuration">
                    Deployment App
                  </Tooltip>
                }
              >
                <Input placeholder="deployment-apps/uf-config" />
              </Form.Item>
              
              <Form.Item
                name="admin_password"
                label="Admin Password"
                initialValue="changeme"
                rules={[{ required: true, message: 'Please enter admin password' }]}
              >
                <Input.Password placeholder="Admin password" />
              </Form.Item>
            </>
          )}
          
          {installType === 'splunk_enterprise' && (
            <>
              <Form.Item
                name="admin_password"
                label="Admin Password"
                rules={[{ required: true, message: 'Please enter admin password' }]}
              >
                <Input.Password placeholder="Admin password" />
              </Form.Item>
              
              <Form.Item
                name="license_master"
                label={
                  <Tooltip title="Optional: Splunk License Master">
                    License Master
                  </Tooltip>
                }
              >
                <Input placeholder="license-master:8089" />
              </Form.Item>
            </>
          )}
        </>
      );
    } else if (installType.includes('cribl')) {
      return (
        <>
          {commonFields}
          
          <Form.Item
            name="version"
            label="Cribl Version"
            rules={[{ required: true, message: 'Please select a version' }]}
          >
            <Select placeholder="Select Cribl version">
              {CRIBL_VERSIONS.map(version => (
                <Option key={version} value={version}>{version}</Option>
              ))}
            </Select>
          </Form.Item>
          
          {installType === 'cribl_worker' && (
            <>
              <Form.Item
                name="leader_url"
                label="Leader URL"
                rules={[{ required: true, message: 'Please enter leader URL' }]}
              >
                <Input placeholder="https://leader:9000" />
              </Form.Item>
              
              <Form.Item
                name="auth_token"
                label="Authentication Token"
                rules={[{ required: true, message: 'Please enter auth token' }]}
              >
                <Input.Password placeholder="Authentication token" />
              </Form.Item>
            </>
          )}
        </>
      );
    } else if (installType === 'custom_command' || installType === 'bash_script') {
      return (
        <>
          {commonFields}
          
          <Form.Item
            name="command"
            label={installType === 'custom_command' ? "Command" : "Script Content"}
            rules={[{ required: true, message: 'Please enter a command or script' }]}
          >
            <Input.TextArea 
              rows={installType === 'custom_command' ? 2 : 10} 
              placeholder={installType === 'custom_command' ? 'Enter command to execute' : 'Enter bash script content'} 
            />
          </Form.Item>
        </>
      );
    } else {
      // Custom script or other installation types
      return commonFields;
    }
  };

  // Render step content
  const renderStepContent = (): React.ReactNode => {
    switch (currentStep) {
      case 0:
        // Step 1: Select installation type
        return (
          <div>
            <Form.Item
              name="host_id"
              hidden={true}
              initialValue={selectedHost?.id}
            >
              <Input type="hidden" />
            </Form.Item>
            
            <Form.Item
              name="install_type"
              label="Installation Type"
              rules={[{ required: true, message: 'Please select an installation type' }]}
            >
              <Select 
                placeholder={`Select ${selectedCategory} installation type`}
                onChange={handleInstallTypeChange}
                value={installType}
              >
                {INSTALLATION_TYPES[selectedCategory]?.map(type => (
                  <Option key={type.value} value={type.value}>{type.label}</Option>
                ))}
              </Select>
            </Form.Item>
          </div>
        );
      
      case 1:
        // Step 2: Configure installation
        return (
          <div>
            {getInstallationFormFields()}
            
            <Divider />
            
            <Form.Item
              name="is_dry_run"
              label={
                <Tooltip title="Simulate the installation without actually installing anything">
                  Dry Run
                </Tooltip>
              }
              valuePropName="checked"
            >
              <Switch />
            </Form.Item>
          </div>
        );
      
      case 2:
        // Step 3: Confirm installation
        return (
          <div>
            <Alert
              message="Ready to Install"
              description="You are about to install the selected software. This operation might take several minutes. You can monitor the progress in the Job History page."
              type="info"
              showIcon
              style={{ marginBottom: 16 }}
            />
            
            {form.getFieldValue('is_dry_run') && (
              <Alert
                message="Dry Run Enabled"
                description="This is a simulation only. No actual changes will be made to the target system."
                type="warning"
                showIcon
                style={{ marginBottom: 16 }}
              />
            )}
            
            <Divider />
            
            <div>
              <Text strong>Target Host:</Text>
              <p>{selectedHost?.hostname} ({selectedHost?.ip_address})</p>
            </div>
            
            <div>
              <Text strong>Installation Category:</Text>
              <p>{selectedCategory.toUpperCase()}</p>
            </div>
            
            <div>
              <Text strong>Installation Type:</Text>
              <p>
                {INSTALLATION_TYPES[selectedCategory]?.find(type => type.value === installType)?.label || installType}
              </p>
            </div>
            
            {(installType !== 'custom_command' && installType !== 'bash_script') && (
              <div>
                <Text strong>Version:</Text>
                <p>{form.getFieldValue('version') || 'N/A'}</p>
              </div>
            )}

            <div>
              <Text strong>Run As User:</Text>
              <p>{form.getFieldValue('run_user') || 'root'}</p>
            </div>

            {(installType === 'custom_command' || installType === 'bash_script') && (
              <div>
                <Text strong>{installType === 'custom_command' ? 'Command' : 'Script'}:</Text>
                <pre style={{ background: '#f5f5f5', padding: '10px', borderRadius: '4px', maxHeight: '200px', overflow: 'auto' }}>
                  {form.getFieldValue('command')}
                </pre>
              </div>
            )}
          </div>
        );
      
      case 3:
        // Step 4: Result
        if (loading) {
          return (
            <div style={{ textAlign: 'center', padding: '20px 0' }}>
              <Spin size="large" />
              <p>Submitting installation job...</p>
            </div>
          );
        }
        
        if (error) {
          return (
            <Result
              status="error"
              title="Installation Failed"
              subTitle={error}
              extra={[
                <Button key="retry" type="primary" onClick={() => setCurrentStep(0)}>
                  Try Again
                </Button>,
                <Button key="cancel" onClick={handleModalClose}>
                  Close
                </Button>,
              ]}
            />
          );
        }
        
        // Check if this was a direct installation
        const isDirectInstall = directInstallResult !== null;
        
        return (
          <Result
            status="success"
            title={isDirectInstall ? "Installation Completed" : "Installation Job Started"}
            subTitle={isDirectInstall 
              ? `Installed on ${selectedHost?.hostname} (${selectedHost?.ip_address})` 
              : `Job ID: ${jobId}`}
            extra={[
              <Button key="view" type="primary" onClick={() => navigate(isDirectInstall ? '/hosts' : '/jobs')}>
                {isDirectInstall ? 'View Hosts' : 'View in Job History'}
              </Button>,
              <Button key="new" onClick={handleModalClose}>
                New Installation
              </Button>,
            ]}
          >
            {isDirectInstall && directInstallResult && (
              <div style={{ textAlign: 'left', marginTop: 20 }}>
                <Divider />
                <Title level={5}>Installation Details</Title>
                {directInstallResult.success ? (
                  <>
                    <div>
                      <Text strong>Status:</Text> <Tag color="green">Success</Tag>
                    </div>
                    <div>
                      <Text strong>Message:</Text> {directInstallResult.message}
                    </div>
                    {directInstallResult.is_dry_run && (
                      <Alert
                        message="Dry Run Mode"
                        description="This was a simulation. No actual changes were made."
                        type="warning"
                        showIcon
                        style={{ marginTop: 16 }}
                      />
                    )}
                  </>
                ) : (
                  <>
                    <div>
                      <Text strong>Status:</Text> <Tag color="red">Failed</Tag>
                    </div>
                    <div>
                      <Text strong>Error:</Text> {directInstallResult.message}
                    </div>
                  </>
                )}
              </div>
            )}
          </Result>
        );
      
      default:
        return null;
    }
  };

  // Define steps
  const steps = [
    {
      title: 'Select Type',
      icon: <CodeOutlined />,
    },
    {
      title: 'Configure',
      icon: <SettingOutlined />,
    },
    {
      title: 'Confirm',
      icon: <CheckCircleOutlined />,
    },
    {
      title: 'Install',
      icon: <CloudDownloadOutlined />,
    }
  ];

  // Get icon for category
  const getCategoryIcon = (category: InstallCategory): React.ReactNode => {
    switch (category) {
      case InstallCategory.ROOT:
        return <CodeOutlined style={{ fontSize: '3rem' }} />;
      case InstallCategory.SPLUNK:
        return <FireOutlined style={{ fontSize: '3rem' }} />;
      case InstallCategory.CRIBL:
        return <ThunderboltOutlined style={{ fontSize: '3rem' }} />;
      case InstallCategory.USER:
        return <UserOutlined style={{ fontSize: '3rem' }} />;
      default:
        return <CloudDownloadOutlined style={{ fontSize: '3rem' }} />;
    }
  };

  // Render host selection view
  const renderHostSelection = () => {
    if (hostsLoading) {
      return (
        <div style={{ textAlign: 'center', padding: 50 }}>
          <Spin size="large" />
          <p>Loading hosts...</p>
        </div>
      );
    }

    if (hosts.length === 0) {
      return (
        <Empty
          description="No active hosts found. Please add hosts first."
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        >
          <Button type="primary" onClick={() => navigate('/hosts')}>
            Go to Host Management
          </Button>
        </Empty>
      );
    }

    return (
      <div>
        <Title level={4}>Select a Host</Title>
        <Row gutter={[16, 16]}>
          {hosts.map(host => (
            <Col xs={24} sm={12} md={8} key={host.id}>
              <Card 
                hoverable
                onClick={() => handleHostSelect(host)}
              >
                <div style={{ display: 'flex', alignItems: 'center' }}>
                  <DesktopOutlined style={{ fontSize: '24px', marginRight: '16px' }} />
                  <div>
                    <div><strong>{host.hostname}</strong></div>
                    <div>{host.ip_address}</div>
                    <div>
                      {host.roles.map(role => (
                        <Tag key={role}>{role}</Tag>
                      ))}
                    </div>
                  </div>
                </div>
              </Card>
            </Col>
          ))}
        </Row>
      </div>
    );
  };

  // Render category selection
  const renderCategorySelection = () => {
    return (
      <div>
        <div style={{ marginBottom: 16 }}>
          <Button 
            type="link" 
            icon={<ArrowRightOutlined style={{ transform: 'rotate(180deg)' }} />}
            onClick={handleBackToHosts}
          >
            Back to Host Selection
          </Button>
        </div>
        <div style={{ marginBottom: 16 }}>
          <Title level={4}>
            Selected Host: {selectedHost?.hostname} ({selectedHost?.ip_address})
          </Title>
          <Text>Select an installation category to begin</Text>
        </div>
        <Row gutter={[24, 24]}>
          {Object.values(InstallCategory).filter(cat => cat !== InstallCategory.NONE).map((category) => (
            <Col xs={24} sm={8} key={category}>
              <MotionDiv
                variants={cardVariants}
                initial="initial"
                animate="animate"
                whileHover="hover"
                whileTap="tap"
                transition={{ duration: 0.3 }}
              >
                <Card
                  hoverable
                  style={{ textAlign: 'center', height: '100%' }}
                  onClick={() => handleCategorySelect(category as InstallCategory)}
                >
                  <div style={{ padding: '20px 0' }}>
                    {getCategoryIcon(category as InstallCategory)}
                    <Title level={3} style={{ marginTop: 16 }}>
                      {category.charAt(0).toUpperCase() + category.slice(1)}
                    </Title>
                    <Text type="secondary">
                      {category === InstallCategory.ROOT && "System-level installations"}
                      {category === InstallCategory.SPLUNK && "Splunk components"}
                      {category === InstallCategory.CRIBL && "Cribl Stream components"}
                      {category === InstallCategory.USER && "User commands and scripts"}
                    </Text>
                  </div>
                  <div style={{ marginTop: 16 }}>
                    <Button type="primary" ghost>
                      Select <RightOutlined />
                    </Button>
                  </div>
                </Card>
              </MotionDiv>
            </Col>
          ))}
        </Row>
      </div>
    );
  };

  return (
    <div className="new-job-container">
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>
          <CloudDownloadOutlined /> New Installation
        </Title>
        <Text>Install software or run commands on hosts</Text>
      </div>

      {/* Main content */}
      {!selectedHost ? (
        renderHostSelection()
      ) : (
        selectedCategory === InstallCategory.NONE ? (
          renderCategorySelection()
        ) : null
      )}

      {/* Installation Modal */}
      <Modal
        title={
          <Title level={4}>
            {getCategoryIcon(selectedCategory)} {selectedCategory.charAt(0).toUpperCase() + selectedCategory.slice(1)} Installation
          </Title>
        }
        open={isModalVisible && selectedCategory !== InstallCategory.NONE}
        onCancel={handleModalClose}
        width={800}
        footer={null}
        destroyOnClose={true}
      >
        <div className="install-modal-content">
          <Steps current={currentStep} style={{ marginBottom: 24 }}>
            {steps.map(item => (
              <Step key={item.title} title={item.title} icon={item.icon} />
            ))}
          </Steps>
          
          <Form
            form={form}
            layout="vertical"
            name="installation_form"
            preserve={false}
            initialValues={{ 
              host_id: selectedHost?.id,
              version: installType?.includes('splunk') ? '9.4.3' : undefined,
              admin_password: installType?.includes('splunk') ? 'changeme' : undefined,
              run_user: installType?.includes('splunk') ? 'splunk' : 'root',
              install_dir: installType === 'splunk_uf' ? '/opt/splunkforwarder' : 
                           installType?.includes('splunk') ? '/opt/splunk' : 
                           installType?.includes('cribl') ? '/opt/cribl' : '/opt'
            }}
          >
            {renderStepContent()}
          </Form>
          
          <div style={{ marginTop: 24, textAlign: 'right' }}>
            {currentStep > 0 && currentStep < 3 && (
              <Button style={{ marginRight: 8 }} onClick={handlePrev}>
                Previous
              </Button>
            )}
            
            {currentStep < 2 && (
              <Button type="primary" onClick={handleNext}>
                Next
              </Button>
            )}
            
            {currentStep === 2 && (
              <Button 
                type="primary" 
                onClick={handleSubmit} 
                loading={loading}
              >
                {form.getFieldValue('is_dry_run') ? 'Start Dry Run' : 'Install'}
              </Button>
            )}
            
            {currentStep === 3 && !error && (
              <Button type="primary" onClick={handleModalClose}>
                Close
              </Button>
            )}
          </div>
        </div>
      </Modal>
    </div>
  );
};

export default NewJob; 