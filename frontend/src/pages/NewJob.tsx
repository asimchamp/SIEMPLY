import { useState, useEffect, useRef } from 'react';
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
  Tooltip,
  Radio
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
  DesktopOutlined,
  RightOutlined,
  ClusterOutlined,
  EyeOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
// We'll handle the framer-motion import with a dynamic import to avoid build errors
// if the package isn't installed yet
// import { motion } from 'framer-motion';
import { hostService, jobService, packageService, Host, SoftwarePackage } from '../services/api';
import { serverClassService, ServerClass } from '../services/serverclassService';

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

// Define target type enum
enum TargetType {
  HOST = 'host',
  SERVER_CLASS = 'server_class'
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
    { value: 'system_update', label: 'System Update' },
    { value: 'syslog_install', label: 'Enable Syslog-NG' }
  ],
  [InstallCategory.SPLUNK]: [
    { value: 'splunk_uf', label: 'Universal Forwarder' },
    { value: 'splunk_enterprise', label: 'Enterprise' }
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

// Cribl versions (will be replaced with Package Inventory data later)
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
  const [form] = Form.useForm();
  const [loading, setLoading] = useState<boolean>(false);
  const [hosts, setHosts] = useState<Host[]>([]);
  const [selectedHost, setSelectedHost] = useState<Host | null>(null);
  const [hostsLoading, setHostsLoading] = useState<boolean>(true);
  const [jobId, setJobId] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const [packages, setPackages] = useState<SoftwarePackage[]>([]);
  const [packagesLoading, setPackagesLoading] = useState<boolean>(false);
  const [splunkState, setSplunkState] = useState<string>('fresh_install');
  const [targetType, setTargetType] = useState<TargetType>(TargetType.HOST);
  const [serverClasses, setServerClasses] = useState<ServerClass[]>([]);
  const [serverClassesLoading, setServerClassesLoading] = useState<boolean>(true);
  const [selectedServerClass, setSelectedServerClass] = useState<ServerClass | null>(null);
  
  // Ref to prevent duplicate submissions (especially in React Strict Mode)
  const isSubmittingRef = useRef<boolean>(false);

  const navigate = useNavigate();

  // Fetch hosts, packages, and server classes when component mounts
  useEffect(() => {
    fetchHosts();
    fetchPackages();
    fetchServerClasses();
  }, []);

  // Fetch server classes
  const fetchServerClasses = async (): Promise<void> => {
    try {
      setServerClassesLoading(true);
      const serverClassesData = await serverClassService.getAllServerClasses();
      setServerClasses(serverClassesData);
    } catch (error) {
      console.error('Failed to fetch server classes:', error);
      message.error('Failed to load server classes');
    } finally {
      setServerClassesLoading(false);
    }
  };

  // Fetch available packages from Package Inventory
  const fetchPackages = async (): Promise<void> => {
    try {
      setPackagesLoading(true);
      const packagesData = await packageService.getAllPackages();
      setPackages(packagesData);
    } catch (error) {
      console.error('Failed to fetch packages:', error);
      message.error('Failed to load package inventory');
    } finally {
      setPackagesLoading(false);
    }
  };

  // Get available versions for a package type
  const getAvailableVersions = (packageType: string): string[] => {
    return packages
      .filter(pkg => pkg.package_type === packageType && pkg.status === 'active')
      .map(pkg => pkg.version)
      .filter((version, index, self) => self.indexOf(version) === index) // Remove duplicates
      .sort((a, b) => b.localeCompare(a)); // Sort descending
  };

  // Get available architectures for a package type and version
  const getAvailableArchitectures = (packageType: string, version: string): string[] => {
    const pkg = packages.find(p => p.package_type === packageType && p.version === version);
    if (!pkg || !pkg.downloads || pkg.downloads.length === 0) {
      // Fallback to legacy architecture field
      return pkg?.architecture ? [pkg.architecture] : ['x86_64'];
    }
    return pkg.downloads.map(d => d.architecture);
  };

  // Set default values for the current installation type
  useEffect(() => {
    if (installType && form && packages.length > 0) {
      if (installType.includes('splunk')) {
        const packageType = installType === 'splunk_uf' ? 'splunk_uf' : 'splunk_enterprise';
        
        // Set default values for Splunk installations (but not version)
        const defaultValues = {
          run_user: 'splunk',
          install_dir: '/opt',
          admin_password: 'changeme'
        };

        // Only set version if it's not already set by user
        const currentVersion = form.getFieldValue('version');
        if (!currentVersion) {
          const availableVersions = getAvailableVersions(packageType);
          const defaultVersion = availableVersions[0]; // Get latest version
          
          if (defaultVersion) {
            const availableArchs = getAvailableArchitectures(packageType, defaultVersion);
            const defaultArch = availableArchs.includes('x86_64') ? 'x86_64' : availableArchs[0];
            
            form.setFieldsValue({
              ...defaultValues,
              version: defaultVersion,
              architecture: defaultArch
            });
          } else {
            form.setFieldsValue(defaultValues);
          }
        } else {
          // User has already selected a version, just set other defaults
          form.setFieldsValue(defaultValues);
        }
        
        console.log("Form values set in useEffect:", form.getFieldsValue());
        console.log("Current version in form after useEffect:", form.getFieldValue('version'));
      }
    }
  }, [installType, form, packages]);

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

  // Handle host selection (now handled in the form)
  const handleHostSelect = (host: Host | null): void => {
    setSelectedHost(host);
    setSelectedServerClass(null);
    if (host) {
      form.setFieldValue('host_id', host.id);
    } else {
      form.setFieldValue('host_id', undefined);
    }
  };

  const handleServerClassSelect = (serverClass: ServerClass | null): void => {
    setSelectedServerClass(serverClass);
    setSelectedHost(null);
    if (serverClass) {
      form.setFieldValue('server_class_name', serverClass.name);
    } else {
      form.setFieldValue('server_class_name', undefined);
    }
  };

  const handleTargetTypeChange = (type: TargetType): void => {
    setTargetType(type);
    setSelectedHost(null);
    setSelectedServerClass(null);
    form.setFieldValue('host_id', undefined);
    form.setFieldValue('server_class_name', undefined);
  };

  // Handle category selection
  const handleCategorySelect = (category: InstallCategory): void => {
    setSelectedCategory(category);
    setInstallType('');
    setCurrentStep(0);
    setSelectedHost(null); // Reset host selection
    
    // Reset form with appropriate initial values based on category
    form.resetFields();
    
    // Initialize default values based on category
    if (category === InstallCategory.SPLUNK) {
      form.setFieldsValue({
        // Don't set version here - let user select from available versions
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
      // Don't set version here - let user select from available versions
      formValues.run_user = 'splunk';
      formValues.install_dir = type === 'splunk_uf' ? '/opt' : '/opt/splunk';
      formValues.admin_password = 'changeme';
    } else if (type.includes('cribl')) {
      formValues.version = '3.4.1';
      formValues.run_user = 'cribl';
      formValues.install_dir = '/opt/cribl';
    } else if (type === 'syslog_install') {
      formValues.run_user = 'syslog';
      formValues.port = 514;
      formValues.log_dir = '/var/log/centralized';
      formValues.additional_users = '';
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
    console.log(`Version in form after setting ${type} defaults:`, form.getFieldValue('version'));
  };

  // Handle modal close
  const handleModalClose = (): void => {
    setSelectedCategory(InstallCategory.NONE);
    setInstallType('');
    setCurrentStep(0);
    setSelectedHost(null);
    form.resetFields();
    console.log("Form reset in handleModalClose");
  };

  // Handle next step
  const handleNext = async (): Promise<void> => {
    try {
      // For step 0, validate target selection based on type
      if (currentStep === 0) {
        if (targetType === TargetType.HOST && !selectedHost) {
          message.error('Please select a host');
          return;
        } else if (targetType === TargetType.SERVER_CLASS && !selectedServerClass) {
          message.error('Please select a server class');
          return;
        }
      } else {
        // For other steps, validate form fields
        await form.validateFields();
      }
      setCurrentStep(currentStep + 1);
    } catch (error) {
      console.error('Validation failed:', error);
    }
  };

  // Handle previous step
  const handlePrev = (): void => {
    setCurrentStep(currentStep - 1);
  };

  // Handle form submission
  const handleSubmit = async (): Promise<void> => {
    // Prevent duplicate submissions (especially important for React Strict Mode)
    if (loading || isSubmittingRef.current) {
      console.log("Submission already in progress, ignoring duplicate call");
      return;
    }
    
    try {
      isSubmittingRef.current = true;
      setLoading(true);
      setError(null);
      
      // Validate target selection based on type
      if (targetType === TargetType.HOST) {
        if (!selectedHost || !selectedHost.id) {
          throw new Error("No host selected");
        }
      } else if (targetType === TargetType.SERVER_CLASS) {
        if (!selectedServerClass || !selectedServerClass.name) {
          throw new Error("No server class selected");
        }
      }
      
      // Set default values for required fields if missing (but preserve user selections)
      const formValuesBeforeDefaults = form.getFieldsValue(true);
      console.log("Current form values before setting defaults:", formValuesBeforeDefaults);
      const defaultValues: Record<string, any> = {};
      
      // Set target ID based on type
      if (targetType === TargetType.HOST && selectedHost) {
        defaultValues.host_id = selectedHost.id;
      } else if (targetType === TargetType.SERVER_CLASS && selectedServerClass) {
        defaultValues.server_class_name = selectedServerClass.name;
      }
      
      // Add defaults based on installation type (but don't override existing values)
      if (installType === 'splunk_uf') {
        if (!formValuesBeforeDefaults.admin_password) defaultValues['admin_password'] = 'changeme';
        if (!formValuesBeforeDefaults.install_dir) defaultValues['install_dir'] = '/opt';
        if (!formValuesBeforeDefaults.run_user) defaultValues['run_user'] = 'splunk';
        // Add cluster information if available
        if (formValuesBeforeDefaults.cluster_name && formValuesBeforeDefaults.cluster_role) {
          defaultValues['cluster_name'] = formValuesBeforeDefaults.cluster_name;
          defaultValues['cluster_role'] = formValuesBeforeDefaults.cluster_role;
        }
      }
      
      // Only set values that are not already set by user
      if (Object.keys(defaultValues).length > 1) { // More than just host_id
        form.setFieldsValue(defaultValues);
      }
      
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
      
      // Get target information based on type
      let targetId: number | string;
      if (targetType === TargetType.HOST && selectedHost) {
        targetId = selectedHost.id;
      } else if (targetType === TargetType.SERVER_CLASS && selectedServerClass) {
        targetId = selectedServerClass.name;
      } else {
        throw new Error("Invalid target selection");
      }
      
      // Submit job based on installation type
      let job;
      
      switch (installType) {
        case 'splunk_uf':
          // Transform form values to match backend API expectations
          const splunkUFParams = {
            ...values,
            user: values.run_user, // Backend expects 'user', form sends 'run_user'
          };
          delete splunkUFParams.run_user; // Remove the original field
          
          console.log("Splunk UF parameters being sent to API:", splunkUFParams);
          console.log("Version in splunkUFParams:", splunkUFParams.version);
          console.log("Splunk state:", values.splunk_state);
          
          // Use different service based on splunk state
          if (values.splunk_state === 'upgrade') {
            // Use upgrade service for Splunk UF
            job = await jobService.upgradeSplunkUF(targetId, splunkUFParams, values.is_dry_run);
          } else {
            // Use install service for fresh install
            job = await jobService.installSplunkUF(targetId, splunkUFParams, values.is_dry_run);
          }
          break;
          
        case 'splunk_enterprise':
          // Transform parameters to match backend expectations
          const splunkEntParams = {
            ...values,
            user: values.run_user,
          };
          delete splunkEntParams.run_user;
          
          console.log("Splunk Enterprise parameters being sent to API:", splunkEntParams);
          console.log("Splunk state:", values.splunk_state);
          
          // Use different service based on splunk state
          if (values.splunk_state === 'upgrade') {
            // Use upgrade service for Splunk Enterprise
            job = await jobService.upgradeSplunkEnterprise(targetId, splunkEntParams, values.is_dry_run);
          } else {
            // Use install service for fresh install
            job = await jobService.installSplunkEnterprise(targetId, splunkEntParams, values.is_dry_run);
          }
          break;
          
        case 'cribl_leader':
          job = await jobService.installCriblLeader(targetId, values, values.is_dry_run);
          break;
          
        case 'cribl_worker':
          job = await jobService.installCriblWorker(targetId, values, values.is_dry_run);
          break;
          
        case 'syslog_install':
          job = await jobService.installSyslog(targetId, values, values.is_dry_run);
          break;
          
        case 'custom_command':
        case 'bash_script':
          // Transform for custom command/script
          const customParams = {
            ...values,
            user: values.run_user,
            command: values.command
          };
          delete customParams.run_user;
          delete customParams.command;
          
          job = await jobService.createCustomJob(targetId, installType, customParams, values.is_dry_run);
          break;
          
        default:
          throw new Error(`Unsupported installation type: ${installType}`);
      }
      
      // Update state with job ID
          setJobId(job.job_id);
      setCurrentStep(currentStep + 1);
      
      // Auto-redirect to job history after a short delay
      setTimeout(() => {
        navigate(`/jobs?job_id=${job.job_id}`);
      }, 2000); // 2 second delay to show the success message
      
    } catch (error) {
      console.error('Failed to submit job:', error);
      setError('Failed to submit installation job. Please try again.');
    } finally {
      setLoading(false);
      isSubmittingRef.current = false;
    }
  };

  // Get installation form fields based on type
  const getInstallationFormFields = (): React.ReactNode => {
    if (!installType) return null;
    
    const commonFields = (
      <>
        {/* Conditional target field based on type */}
        {targetType === TargetType.HOST && (
          <Form.Item
            name="host_id"
            label="Target Host"
            initialValue={selectedHost?.id}
            rules={[{ required: true, message: 'Please select a host' }]}
            hidden={true}
          >
            <Input type="hidden" />
          </Form.Item>
        )}
        
        {targetType === TargetType.SERVER_CLASS && (
          <Form.Item
            name="server_class_name"
            label="Target Server Class"
            initialValue={selectedServerClass?.name}
            rules={[{ required: true, message: 'Please select a server class' }]}
            hidden={true}
          >
            <Input type="hidden" />
          </Form.Item>
        )}
        
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
            rules={[{ required: true, message: 'Please select a version' }]}
          >
            <Select 
              placeholder="Select Splunk version" 
              loading={packagesLoading}
              onChange={(value: string) => {
                console.log("Version selected by user:", value);
                // Reset architecture when version changes
                form.setFieldsValue({ architecture: undefined });
              }}
            >
              {getAvailableVersions(installType === 'splunk_uf' ? 'splunk_uf' : 'splunk_enterprise').map((version: string) => (
                <Option key={version} value={version}>{version}</Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="architecture"
            label="Architecture"
            rules={[{ required: true, message: 'Please select an architecture' }]}
          >
            <Select 
              placeholder="Select architecture"
              disabled={!form.getFieldValue('version')}
            >
              {form.getFieldValue('version') && 
                getAvailableArchitectures(
                  installType === 'splunk_uf' ? 'splunk_uf' : 'splunk_enterprise', 
                  form.getFieldValue('version')
                ).map((arch: string) => (
                  <Option key={arch} value={arch}>
                    {arch === 'x86_64' ? 'x86_64 (Intel/AMD)' : 
                     arch === 'arm64' ? 'ARM64' : 
                     arch === 'aarch64' ? 'AArch64' : 
                     arch}
                  </Option>
                ))
              }
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
              
              {/* Only show admin password for fresh installs, not upgrades */}
              {splunkState !== 'upgrade' && (
                <Form.Item
                  name="admin_password"
                  label="Admin Password"
                  initialValue="changeme"
                  rules={[{ required: true, message: 'Please enter admin password' }]}
                >
                  <Input.Password placeholder="Admin password" />
                </Form.Item>
              )}
            </>
          )}
          
          {installType === 'splunk_enterprise' && (
            <>
              {/* Only show admin password for fresh installs, not upgrades */}
              {splunkState !== 'upgrade' && (
                <Form.Item
                  name="admin_password"
                  label="Admin Password"
                  rules={[{ required: true, message: 'Please enter admin password' }]}
                >
                  <Input.Password placeholder="Admin password" />
                </Form.Item>
              )}
              
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
    } else if (installType === 'syslog_install') {
      return (
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

          <Form.Item
            name="run_user"
            label="Run As User"
            rules={[{ required: true, message: 'Please specify the user to run as' }]}
          >
            <Input placeholder="e.g., syslog" prefix={<UserOutlined />} />
          </Form.Item>
          
          <Form.Item
            name="port"
            label="Syslog Port"
            initialValue={514}
            rules={[{ required: true, message: 'Please specify syslog port' }]}
          >
            <Input type="number" placeholder="514" />
          </Form.Item>
          
          <Form.Item
            name="log_dir"
            label="Log Directory"
            initialValue="/var/log/centralized"
            rules={[{ required: true, message: 'Please specify log directory' }]}
          >
            <Input placeholder="/var/log/centralized" />
          </Form.Item>
          
          <Form.Item
            name="additional_users"
            label={
              <Tooltip title="Additional users who can manage syslog-ng service (comma-separated)">
                Additional Users
              </Tooltip>
            }
          >
            <Input placeholder="splunk,admin,user1" />
          </Form.Item>
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
        // Step 0: Select target type and host/server class
        return renderHostSelection();
      
      case 1:
        // Step 1: Select installation type
        return (
          <div>
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
            
            {/* Splunk State selection - only show for Splunk installations */}
            {installType.includes('splunk') && (
              <Form.Item
                name="splunk_state"
                label="Splunk State"
                rules={[{ required: true, message: 'Please select Splunk state' }]}
                initialValue="fresh_install"
              >
                <Select 
                  placeholder="Select Splunk state"
                  onChange={(value: string) => setSplunkState(value)}
                  value={splunkState}
                >
                  <Option value="fresh_install">Fresh Install</Option>
                  <Option value="upgrade">Upgrade</Option>
                </Select>
              </Form.Item>
            )}
          </div>
        );
      
      case 2:
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
      
      case 3:
        // Step 3: Confirm installation
        return (
          <div>
            <Alert
              message={installType.includes('splunk') && form.getFieldValue('splunk_state') === 'upgrade' ? "Ready to Upgrade" : "Ready to Install"}
              description={installType.includes('splunk') && form.getFieldValue('splunk_state') === 'upgrade' 
                ? "You are about to upgrade the selected software. This operation might take several minutes. You can monitor the progress in the Job History page."
                : "You are about to install the selected software. This operation might take several minutes. You can monitor the progress in the Job History page."
              }
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
            
            {/* Show Splunk State for Splunk installations */}
            {installType.includes('splunk') && (
              <div>
                <Text strong>Splunk State:</Text>
                <p>{form.getFieldValue('splunk_state') === 'fresh_install' ? 'Fresh Install' : 'Upgrade'}</p>
              </div>
            )}
            
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
      
      case 4:
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
        
        return (
          <Result
            status="success"
            title="Installation Job Started"
            subTitle={`Job ID: ${jobId}`}
            extra={[
              <Button key="view" type="primary" size="large" onClick={() => navigate(`/jobs?job_id=${jobId}`)} icon={<EyeOutlined />}>
                View Job Progress
              </Button>,
              <Button key="new" onClick={handleModalClose}>
                New Installation
              </Button>,
            ]}
          >
              <div style={{ textAlign: 'left', marginTop: 20 }}>
                <Divider />
              <Title level={5}>Job Details</Title>
                    <div>
                <Text strong>Host:</Text> {selectedHost?.hostname} ({selectedHost?.ip_address})
                    </div>
                    <div>
                <Text strong>Installation Type:</Text> {installType?.replace(/_/g, ' ').toUpperCase()}
                    </div>
              <div>
                <Text strong>Status:</Text> <Tag color="blue">Job Submitted</Tag>
              </div>
                      <Alert
                message="Job Started"
                description="Your installation job has been submitted and is running in the background. You will be automatically redirected to the Job History page to monitor progress."
                type="info"
                        showIcon
                        style={{ marginTop: 16 }}
                      />
                    </div>
          </Result>
        );
      
      default:
        return null;
    }
  };

  // Define steps
  const steps = [
    {
      title: 'Select Target',
      icon: <DesktopOutlined />,
    },
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
    return (
      <div>
        <Title level={4}>Select Target Type</Title>
        <div style={{ marginBottom: 24 }}>
          <Radio.Group 
            value={targetType} 
            onChange={(e) => handleTargetTypeChange(e.target.value)}
            style={{ marginBottom: 16 }}
          >
            <Radio.Button value={TargetType.HOST}>
              <DesktopOutlined /> Host
            </Radio.Button>
            <Radio.Button value={TargetType.SERVER_CLASS}>
              <ClusterOutlined /> Server Class
            </Radio.Button>
          </Radio.Group>
        </div>

        {targetType === TargetType.HOST && (
          <div>
            <Title level={4}>Select a Host</Title>
            {hostsLoading ? (
              <div style={{ textAlign: 'center', padding: 20 }}>
                <Spin size="large" />
                <p>Loading hosts...</p>
              </div>
            ) : hosts.length === 0 ? (
              <Empty
                description="No active hosts found. Please add hosts first."
                image={Empty.PRESENTED_IMAGE_SIMPLE}
              >
                <Button type="primary" onClick={() => navigate('/hosts')}>
                  Go to Host Management
                </Button>
              </Empty>
            ) : (
              <Form.Item
                name="host_id"
                label="Select Target Host"
                rules={[{ required: true, message: 'Please select a host' }]}
              >
                <Select 
                  placeholder="Select a host for installation"
                  onChange={(value) => {
                    if (value) {
                      const host = hosts.find(h => h.id === value);
                      handleHostSelect(host || null);
                    } else {
                      handleHostSelect(null);
                    }
                  }}
                  value={selectedHost?.id}
                  showSearch
                  filterOption={(input, option) =>
                    (option?.children as unknown as string)?.toLowerCase().includes(input.toLowerCase())
                  }
                  optionFilterProp="children"
                >
                  {hosts.map(host => (
                    <Option key={host.id} value={host.id}>
                      {host.hostname} ({host.ip_address}) - {host.roles.join(', ')}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            )}
          </div>
        )}

        {targetType === TargetType.SERVER_CLASS && (
          <div>
            <Title level={4}>Select a Server Class</Title>
            {serverClassesLoading ? (
              <div style={{ textAlign: 'center', padding: 20 }}>
                <Spin size="large" />
                <p>Loading server classes...</p>
              </div>
            ) : serverClasses.length === 0 ? (
              <Empty
                description="No server classes found. Please create server classes first."
                image={Empty.PRESENTED_IMAGE_SIMPLE}
              >
                <Button type="primary" onClick={() => navigate('/hosts/server-classes')}>
                  Go to Server Classes
                </Button>
              </Empty>
            ) : (
              <Form.Item
                name="server_class_name"
                label="Select Target Server Class"
                rules={[{ required: true, message: 'Please select a server class' }]}
              >
                <Select 
                  placeholder="Select a server class for installation"
                  onChange={(value) => {
                    if (value) {
                      const serverClass = serverClasses.find(sc => sc.name === value);
                      handleServerClassSelect(serverClass || null);
                    } else {
                      handleServerClassSelect(null);
                    }
                  }}
                  value={selectedServerClass?.name}
                  showSearch
                  filterOption={(input, option) =>
                    (option?.children as unknown as string)?.toLowerCase().includes(input.toLowerCase())
                  }
                  optionFilterProp="children"
                >
                  {serverClasses.map(serverClass => (
                    <Option key={serverClass.id} value={serverClass.name}>
                      {serverClass.name} ({serverClass.host_count} hosts) - {serverClass.description}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            )}
          </div>
        )}
      </div>
    );
  };

  // Render category selection
  const renderCategorySelection = () => {
    return (
      <div>
        <div style={{ marginBottom: 16 }}>
          <Title level={4}>
            Select an installation category to begin
          </Title>
          <Text>Choose the type of software or command you want to install</Text>
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
      {selectedCategory === InstallCategory.NONE ? (
        renderCategorySelection()
      ) : null}

      {/* Installation Modal */}
      <Modal
        title={
          <Title level={4}>
            {getCategoryIcon(selectedCategory)} {selectedCategory.charAt(0).toUpperCase() + selectedCategory.slice(1)} Installation
          </Title>
        }
        open={selectedCategory !== InstallCategory.NONE}
        onCancel={handleModalClose}
        width={800}
        footer={null}
        destroyOnClose={false}
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
            preserve={true}
            initialValues={{ 
              // Don't set version here - let user select from available versions
              admin_password: installType?.includes('splunk') ? 'changeme' : undefined,
              run_user: installType?.includes('splunk') ? 'splunk' : 'root',
              install_dir: installType === 'splunk_uf' ? '/opt' : 
                           installType?.includes('splunk') ? '/opt/splunk' : 
                           installType?.includes('cribl') ? '/opt/cribl' : '/opt',
              splunk_state: 'fresh_install'
            }}
          >
            {renderStepContent()}
          </Form>
          
          <div style={{ marginTop: 24, textAlign: 'right' }}>
            {currentStep > 0 && currentStep < 4 && (
              <Button style={{ marginRight: 8 }} onClick={handlePrev}>
                Previous
              </Button>
            )}
            
            {currentStep < 3 && (
              <Button type="primary" onClick={handleNext}>
                Next
              </Button>
            )}
            
            {currentStep === 3 && (
              <Button 
                type="primary" 
                onClick={handleSubmit} 
                loading={loading}
              >
                {form.getFieldValue('is_dry_run') 
                  ? 'Start Dry Run' 
                  : (installType.includes('splunk') && form.getFieldValue('splunk_state') === 'upgrade' ? 'Upgrade' : 'Install')
                }
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