import { useState, useEffect } from 'react';
import { 
  Modal, 
  Form, 
  Input, 
  Select, 
  Button, 
  Switch, 
  Divider, 
  Typography, 
  Alert, 
  Steps,
  Result,
  Spin,
  Space
} from 'antd';
import { 
  CloudDownloadOutlined, 
  FileOutlined, 
  SettingOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';
import { hostService, jobService, Host } from '../services/api';

const { Title, Text } = Typography;
const { Option } = Select;
const { Step } = Steps;

interface InstallModalProps {
  visible: boolean;
  onClose: () => void;
  onSuccess?: (jobId: string) => void;
}

const InstallModal: React.FC<InstallModalProps> = ({ visible, onClose, onSuccess }) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState<boolean>(false);
  const [hosts, setHosts] = useState<Host[]>([]);
  const [hostsLoading, setHostsLoading] = useState<boolean>(true);
  const [currentStep, setCurrentStep] = useState<number>(0);
  const [installType, setInstallType] = useState<string>('');
  const [jobId, setJobId] = useState<string>('');
  const [error, setError] = useState<string | null>(null);

  // Installation types
  const INSTALLATION_TYPES = [
    { value: 'splunk_uf', label: 'Splunk Universal Forwarder' },
    { value: 'splunk_enterprise', label: 'Splunk Enterprise' },
    { value: 'cribl_leader', label: 'Cribl Stream Leader' },
    { value: 'cribl_worker', label: 'Cribl Stream Worker' }
  ];

  // Splunk versions
  const SPLUNK_VERSIONS = ['9.1.1', '9.0.5', '8.2.9', '8.1.5', '7.3.9'];

  // Cribl versions
  const CRIBL_VERSIONS = ['3.4.1', '3.3.0', '3.0.5', '2.4.5'];

  // Fetch hosts on component mount and when modal becomes visible
  useEffect(() => {
    if (visible) {
      fetchHosts();
      setCurrentStep(0);
      setInstallType('');
      setJobId('');
      setError(null);
      form.resetFields();
    }
  }, [visible, form]);

  // Fetch available hosts
  const fetchHosts = async () => {
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

  // Handle installation type change
  const handleInstallTypeChange = (type: string) => {
    setInstallType(type);
    
    // Reset version and other fields based on type
    if (type.includes('splunk')) {
      form.setFieldsValue({ version: '9.1.1' });
    } else if (type.includes('cribl')) {
      form.setFieldsValue({ version: '3.4.1' });
    }
  };

  // Handle next step
  const handleNext = async () => {
    try {
      await form.validateFields();
      setCurrentStep(currentStep + 1);
    } catch (error) {
      console.error('Validation failed:', error);
    }
  };

  // Handle previous step
  const handlePrev = () => {
    setCurrentStep(currentStep - 1);
  };

  // Handle form submission
  const handleSubmit = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const values = form.getFieldsValue();
      const { host_id, version, install_dir, is_dry_run } = values;
      
      // Prepare parameters based on installation type
      const parameters: Record<string, any> = {
        version,
        install_dir: install_dir || '/opt'
      };
      
      // Add additional parameters based on installation type
      if (installType === 'splunk_uf') {
        parameters.deployment_server = values.deployment_server;
        parameters.deployment_app = values.deployment_app;
      } else if (installType === 'splunk_enterprise') {
        parameters.admin_password = values.admin_password;
        parameters.license_master = values.license_master;
      } else if (installType === 'cribl_worker') {
        parameters.leader_url = values.leader_url;
        parameters.auth_token = values.auth_token;
      }
      
      // Submit job based on installation type
      let job;
      switch (installType) {
        case 'splunk_uf':
          job = await jobService.installSplunkUF(host_id, parameters, is_dry_run);
          break;
        case 'splunk_enterprise':
          job = await jobService.installSplunkEnterprise(host_id, parameters, is_dry_run);
          break;
        case 'cribl_leader':
          job = await jobService.installCriblLeader(host_id, parameters, is_dry_run);
          break;
        case 'cribl_worker':
          job = await jobService.installCriblWorker(host_id, parameters, is_dry_run);
          break;
        default:
          throw new Error('Invalid installation type');
      }
      
      // Update state with job ID
      setJobId(job.job_id);
      setCurrentStep(currentStep + 1);
      
      // Call onSuccess callback if provided
      if (onSuccess) {
        onSuccess(job.job_id);
      }
    } catch (error) {
      console.error('Failed to submit job:', error);
      setError('Failed to submit installation job. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Handle modal close
  const handleClose = () => {
    onClose();
  };

  // Get form based on installation type
  const getInstallationFormFields = () => {
    if (!installType) return null;
    
    const commonFields = (
      <>
        <Form.Item
          name="host_id"
          label="Target Host"
          rules={[{ required: true, message: 'Please select a host' }]}
        >
          <Select 
            placeholder="Select host for installation" 
            loading={hostsLoading}
            showSearch
            optionFilterProp="children"
          >
            {hosts.map(host => (
              <Option key={host.id} value={host.id}>
                {host.hostname} ({host.ip_address})
              </Option>
            ))}
          </Select>
        </Form.Item>
        
        <Form.Item
          name="install_dir"
          label="Installation Directory"
          initialValue="/opt"
        >
          <Input placeholder="/opt" />
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
            initialValue="9.1.1"
            rules={[{ required: true, message: 'Please select a version' }]}
          >
            <Select placeholder="Select Splunk version">
              {SPLUNK_VERSIONS.map(version => (
                <Option key={version} value={version}>{version}</Option>
              ))}
            </Select>
          </Form.Item>
          
          {installType === 'splunk_uf' && (
            <>
              <Form.Item
                name="deployment_server"
                label="Deployment Server"
                tooltip="Optional: Splunk Deployment Server for UF configuration"
              >
                <Input placeholder="deployserver:8089" />
              </Form.Item>
              
              <Form.Item
                name="deployment_app"
                label="Deployment App"
                tooltip="Optional: Deployment app name for UF configuration"
              >
                <Input placeholder="deployment-apps/universal_forwarder" />
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
                <Input.Password placeholder="Admin password for Splunk" />
              </Form.Item>
              
              <Form.Item
                name="license_master"
                label="License Master"
                tooltip="Optional: Splunk License Master server"
              >
                <Input placeholder="licensemaster:8089" />
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
            initialValue="3.4.1"
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
                <Input placeholder="https://cribl-leader:9000" />
              </Form.Item>
              
              <Form.Item
                name="auth_token"
                label="Authentication Token"
                rules={[{ required: true, message: 'Please enter authentication token' }]}
              >
                <Input.Password placeholder="Leader authentication token" />
              </Form.Item>
            </>
          )}
        </>
      );
    }
    
    return null;
  };

  // Render steps content
  const renderStepContent = () => {
    switch (currentStep) {
      case 0:
        // Step 1: Select installation type
        return (
          <div>
            <Form.Item
              name="install_type"
              label="Installation Type"
              rules={[{ required: true, message: 'Please select an installation type' }]}
            >
              <Select 
                placeholder="Select what you want to install" 
                onChange={handleInstallTypeChange}
                value={installType}
              >
                {INSTALLATION_TYPES.map(type => (
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
              label="Dry Run"
              valuePropName="checked"
              tooltip="Simulate the installation without actually installing anything"
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
              <Text strong>Installation Type:</Text>
              <p>
                {INSTALLATION_TYPES.find(type => type.value === installType)?.label}
              </p>
            </div>
            
            <div>
              <Text strong>Target Host:</Text>
              <p>
                {hosts.find(host => host.id === form.getFieldValue('host_id'))?.hostname}
              </p>
            </div>
            
            <div>
              <Text strong>Version:</Text>
              <p>{form.getFieldValue('version')}</p>
            </div>
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
                <Button key="cancel" onClick={handleClose}>
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
              <Button key="view" type="primary" onClick={handleClose}>
                View in Job History
              </Button>,
              <Button key="new" onClick={() => setCurrentStep(0)}>
                New Installation
              </Button>,
            ]}
          />
        );
      
      default:
        return null;
    }
  };

  // Define steps
  const steps = [
    {
      title: 'Select Type',
      icon: <FileOutlined />,
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

  return (
    <Modal
      title={
        <Title level={4}>
          <CloudDownloadOutlined /> Install Software
        </Title>
      }
      open={visible}
      onCancel={handleClose}
      width={700}
      footer={null}
      destroyOnHidden
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
          initialValues={{ is_dry_run: false }}
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
            <Button type="primary" onClick={handleClose}>
              Close
            </Button>
          )}
        </div>
      </div>
    </Modal>
  );
};

export default InstallModal; 