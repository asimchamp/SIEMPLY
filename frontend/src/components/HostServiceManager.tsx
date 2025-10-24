import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Button, 
  Progress, 
  Statistic, 
  Row, 
  Col, 
  Alert, 
  Space, 
  Tag,
  Tooltip,
  Spin,
  message,
  Typography,
  Divider
} from 'antd';
import { 
  CheckCircleOutlined, 
  CloseCircleOutlined, 
  ExclamationCircleOutlined,
  QuestionCircleOutlined,
  ReloadOutlined,
  ToolOutlined,
  PlayCircleOutlined,
  DownloadOutlined,
  SettingOutlined
} from '@ant-design/icons';
import { hostService } from '../services/api';

const { Text } = Typography;

interface Service {
  name: string;
  status: 'running' | 'stopped' | 'not_installed' | 'error';
  required: boolean;
  details: string;
}

interface HostServiceManagerProps {
  hostId: number;
  hostname: string;
  hideTitle?: boolean;
}

const HostServiceManager: React.FC<HostServiceManagerProps> = ({ 
  hostId, 
  hostname, 
  hideTitle = false 
}) => {
  const [services, setServices] = useState<Service[]>([]);
  const [loading, setLoading] = useState(false);
  const [checking, setChecking] = useState(false);

  const checkServices = async () => {
    setChecking(true);
    try {
      const response = await hostService.checkServices(hostId);
      setServices(response.services);
      message.success('Services checked successfully');
    } catch (error: any) {
      message.error(`Failed to check services: ${error.response?.data?.detail || error.message}`);
    } finally {
      setChecking(false);
    }
  };

  const fixSftp = async () => {
    setLoading(true);
    try {
      const response = await hostService.fixSftp(hostId);
      if (response.success) {
        message.success(response.message);
        // Wait a moment for the fix to take effect, then recheck services
        setTimeout(async () => {
          await checkServices();
        }, 2000);
      } else {
        message.error(response.message);
      }
    } catch (error: any) {
      message.error(`Failed to fix SFTP: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const installSyslogNg = async () => {
    setLoading(true);
    try {
      const response = await hostService.installSyslogNg(hostId);
      if (response.success) {
        message.success(response.message);
        // Wait a moment for the installation to complete, then recheck services
        setTimeout(async () => {
          await checkServices();
        }, 3000);
      } else {
        message.error(response.message);
      }
    } catch (error: any) {
      message.error(`Failed to install syslog-ng: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const startSyslogNg = async () => {
    setLoading(true);
    try {
      const response = await hostService.startSyslogNg(hostId);
      if (response.success) {
        message.success(response.message);
        // Wait a moment for the service to start, then recheck services
        setTimeout(async () => {
          await checkServices();
        }, 2000);
      } else {
        message.error(response.message);
      }
    } catch (error: any) {
      message.error(`Failed to start syslog-ng: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const debugServices = async () => {
    try {
      const debugData = await hostService.debugServices(hostId);
      console.log('Service Debug Data:', debugData);
      message.info('Debug data logged to console. Check browser developer tools.');
      
      // Show debug info in an alert for easy viewing
      const debugInfo = `
Host: ${debugData.hostname}
SSH Status: ${debugData.ssh_status}
SSH Test Output: ${debugData.ssh_test_output}

OS Info: ${debugData.debug_info?.os_info?.stdout || 'N/A'}
SSH Config: ${debugData.debug_info?.ssh_config?.stdout || 'N/A'}
SSHD Status: ${debugData.debug_info?.sshd_status?.stdout || 'N/A'}

Services:
${debugData.services.map((s: any) => `- ${s.name}: ${s.status} (${s.details})`).join('\n')}
      `;
      
      alert(debugInfo);
    } catch (error: any) {
      message.error(`Failed to debug services: ${error.response?.data?.detail || error.message}`);
    }
  };

  const getServiceIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'stopped':
        return <ExclamationCircleOutlined style={{ color: '#faad14' }} />;
      case 'not_installed':
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;
      case 'error':
        return <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />;
      default:
        return <QuestionCircleOutlined style={{ color: '#8c8c8c' }} />;
    }
  };

  const getServiceTag = (status: string) => {
    switch (status) {
      case 'running':
        return <Tag color="success">Running</Tag>;
      case 'stopped':
        return <Tag color="warning">Stopped</Tag>;
      case 'not_installed':
        return <Tag color="error">Not Installed</Tag>;
      case 'error':
        return <Tag color="error">Error</Tag>;
      default:
        return <Tag color="default">Unknown</Tag>;
    }
  };

  const getServiceActions = (service: Service) => {
    switch (service.name) {
      case 'SFTP':
        if (service.status !== 'running') {
          return (
            <Button 
              type="primary" 
              size="small" 
              icon={<ToolOutlined />}
              onClick={fixSftp}
              loading={loading}
            >
              Fix SFTP
            </Button>
          );
        }
        break;
      case 'syslog-ng':
        if (service.status === 'not_installed') {
          return (
            <Button 
              type="primary" 
              size="small" 
              icon={<DownloadOutlined />}
              onClick={installSyslogNg}
              loading={loading}
            >
              Install
            </Button>
          );
        } else if (service.status === 'stopped') {
          return (
            <Button 
              type="primary" 
              size="small" 
              icon={<PlayCircleOutlined />}
              onClick={startSyslogNg}
              loading={loading}
            >
              Start
            </Button>
          );
        }
        break;
    }
    return null;
  };

  const requiredServices = services.filter(s => s.required);
  const optionalServices = services.filter(s => !s.required);
  const runningServices = services.filter(s => s.status === 'running');
  const totalServices = services.length;

  const progressPercent = totalServices > 0 ? (runningServices.length / totalServices) * 100 : 0;

  useEffect(() => {
    // Automatically check services when component mounts
    checkServices();
  }, []);

  return (
    <Card
      title={!hideTitle ? (
        <Space>
          <SettingOutlined />
          <span>Service Management</span>
        </Space>
      ) : undefined}
      extra={!hideTitle ? (
        <Space>
          <Button
            icon={<ReloadOutlined />}
            onClick={checkServices}
            loading={checking}
            size="small"
          >
            Refresh
          </Button>
          <Button
            icon={<ToolOutlined />}
            onClick={debugServices}
            size="small"
            type="dashed"
          >
            Debug
          </Button>
        </Space>
      ) : (
        <Space>
          <Button
            icon={<ReloadOutlined />}
            onClick={checkServices}
            loading={checking}
            size="small"
          >
            Refresh
          </Button>
          <Button
            icon={<ToolOutlined />}
            onClick={debugServices}
            size="small"
            type="dashed"
          >
            Debug
          </Button>
        </Space>
      )}
      style={{ marginBottom: hideTitle ? 0 : 16 }}
    >
      {/* Statistics */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={6}>
          <Statistic 
            title="Total Services" 
            value={totalServices} 
            prefix={<QuestionCircleOutlined />}
          />
        </Col>
        <Col span={6}>
          <Statistic 
            title="Running" 
            value={runningServices.length} 
            prefix={<CheckCircleOutlined />}
            valueStyle={{ color: '#52c41a' }}
          />
        </Col>
        <Col span={6}>
          <Statistic 
            title="Required" 
            value={requiredServices.length} 
            prefix={<ExclamationCircleOutlined />}
            valueStyle={{ color: '#faad14' }}
          />
        </Col>
        <Col span={6}>
          <Statistic 
            title="Issues" 
            value={services.filter(s => s.status !== 'running').length} 
            prefix={<CloseCircleOutlined />}
            valueStyle={{ color: '#ff4d4f' }}
          />
        </Col>
      </Row>

      {/* Progress Bar */}
      <Progress 
        percent={Math.round(progressPercent)} 
        status={progressPercent === 100 ? 'success' : 'active'}
        strokeColor={{
          '0%': '#108ee9',
          '100%': '#52c41a',
        }}
        style={{ marginBottom: 16 }}
      />

      {/* Required Services */}
      {requiredServices.length > 0 && (
        <div style={{ marginBottom: 16 }}>
          <h4 style={{ color: '#ff4d4f', marginBottom: 8 }}>
            Required Services (Critical)
          </h4>
          {requiredServices.map((service, index) => (
            <div key={index} style={{ marginBottom: 12 }}>
              <Row align="middle" gutter={16}>
                <Col span={2}>
                  {getServiceIcon(service.status)}
                </Col>
                <Col span={6}>
                  <Text strong>{service.name}</Text>
                </Col>
                <Col span={4}>
                  {getServiceTag(service.status)}
                </Col>
                <Col span={8}>
                  <Text type="secondary">{service.details}</Text>
                </Col>
                <Col span={4}>
                  {getServiceActions(service)}
                </Col>
              </Row>
              {index < requiredServices.length - 1 && <Divider style={{ margin: '8px 0' }} />}
            </div>
          ))}
        </div>
      )}

      {/* Optional Services */}
      {optionalServices.length > 0 && (
        <div>
          <h4 style={{ color: '#8c8c8c', marginBottom: 8 }}>
            Optional Services
          </h4>
          {optionalServices.map((service, index) => (
            <div key={index} style={{ marginBottom: 12 }}>
              <Row align="middle" gutter={16}>
                <Col span={2}>
                  {getServiceIcon(service.status)}
                </Col>
                <Col span={6}>
                  <Text strong>{service.name}</Text>
                </Col>
                <Col span={4}>
                  {getServiceTag(service.status)}
                </Col>
                <Col span={8}>
                  <Text type="secondary">{service.details}</Text>
                </Col>
                <Col span={4}>
                  {getServiceActions(service)}
                </Col>
              </Row>
              {index < optionalServices.length - 1 && <Divider style={{ margin: '8px 0' }} />}
            </div>
          ))}
        </div>
      )}

      {/* No Services Message */}
      {services.length === 0 && !checking && (
        <Alert
          message="No services found"
          description="Click 'Refresh' to check services on this host."
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      {/* Loading State */}
      {checking && (
        <div style={{ textAlign: 'center', padding: '20px' }}>
          <Spin size="large" />
          <div style={{ marginTop: 8 }}>Checking services...</div>
        </div>
      )}
    </Card>
  );
};

export default HostServiceManager;
