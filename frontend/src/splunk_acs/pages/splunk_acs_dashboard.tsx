import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, Row, Col, Typography, Button, Space, Tag, Statistic, Alert, message, Select } from 'antd';
import { 
  CloudOutlined, 
  SecurityScanOutlined, 
  SettingOutlined, 
  UserOutlined,
  AppstoreOutlined,
  DatabaseOutlined,
  ClockCircleOutlined,
  KeyOutlined,
  BarChartOutlined,
  FileTextOutlined,
  ToolOutlined,
  SafetyOutlined,
  ReloadOutlined,
  PlusOutlined
} from '@ant-design/icons';
import { acsApiService, ACSStats, SplunkCloudConfig } from '../services/splunk_acs_services_index';

const { Title, Text } = Typography;



interface ConfigCategory {
  key: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  color: string;
  count?: number;
  status: 'active' | 'warning' | 'error' | 'inactive';
}

const SplunkACSDashboard: React.FC = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState<ACSStats>({
    totalConfigs: 0,
    activeConfigs: 0,
    pendingChanges: 0,
    totalChanges: 0,
    lastSync: 'Never'
  });
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [configurations, setConfigurations] = useState<SplunkCloudConfig[]>([]);
  const [selectedConfig, setSelectedConfig] = useState<SplunkCloudConfig | null>(null);

  // Fetch real data from API
  useEffect(() => {
    handleRefresh();
  }, []);

  // Refresh dashboard data
  const handleRefresh = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const dashboardStats = await acsApiService.getDashboardStats();
      setStats(dashboardStats);
      message.success('Dashboard data refreshed successfully');
    } catch (error) {
      console.error('Failed to refresh dashboard data:', error);
      setError(error instanceof Error ? error.message : 'Failed to refresh dashboard data');
      message.error('Failed to refresh dashboard data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Configuration categories based on Splunk ACS capabilities
  const configCategories: ConfigCategory[] = [
    {
      key: 'ip_allow_lists',
      title: 'IP Allow Lists',
      description: 'Manage IP address allow lists for network access control',
      icon: <SecurityScanOutlined />,
      color: '#52c41a',
      status: selectedConfig ? 'active' : 'inactive'
    },
    {
      key: 'outbound_ports',
      title: 'Outbound Ports',
      description: 'Configure outbound port access for external communications',
      icon: <ToolOutlined />,
      color: '#1890ff',
      status: selectedConfig ? 'active' : 'inactive'
    },
    {
      key: 'private_connectivity',
      title: 'Private Connectivity',
      description: 'Manage private network connections and VPN settings',
      icon: <SafetyOutlined />,
      color: '#722ed1',
      status: selectedConfig ? 'active' : 'inactive'
    },
    {
      key: 'apps',
      title: 'Applications',
      description: 'Deploy and manage Splunk applications and add-ons',
      icon: <AppstoreOutlined />,
      color: '#fa8c16',
      status: selectedConfig ? 'active' : 'inactive'
    },
    {
      key: 'indexes',
      title: 'Indexes',
      description: 'Create and configure data indexes for log storage',
      icon: <DatabaseOutlined />,
      color: '#13c2c2',
      status: selectedConfig ? 'active' : 'inactive'
    },
    {
      key: 'users',
      title: 'Users',
      description: 'Manage user accounts and authentication settings',
      icon: <UserOutlined />,
      color: '#eb2f96',
      status: selectedConfig ? 'active' : 'inactive'
    },
    {
      key: 'roles',
      title: 'Roles & Permissions',
      description: 'Configure role-based access control and permissions',
      icon: <KeyOutlined />,
      color: '#fa541c',
      status: selectedConfig ? 'active' : 'inactive'
    },
    {
      key: 'auth_tokens',
      title: 'Authentication Tokens',
      description: 'Manage API tokens and authentication credentials',
      icon: <KeyOutlined />,
      color: '#f5222d',
      status: selectedConfig ? 'active' : 'inactive'
    },
    {
      key: 'maintenance_windows',
      title: 'Maintenance Windows',
      description: 'Schedule and manage system maintenance periods',
      icon: <ClockCircleOutlined />,
      color: '#2f54eb',
      status: selectedConfig ? 'active' : 'inactive'
    },
    {
      key: 'hec_tokens',
      title: 'HEC Tokens',
      description: 'HTTP Event Collector tokens for data ingestion',
      icon: <FileTextOutlined />,
      color: '#faad14',
      status: selectedConfig ? 'active' : 'inactive'
    },
    {
      key: 'limits_conf',
      title: 'Limits Configuration',
      description: 'Configure system limits and resource constraints',
      icon: <BarChartOutlined />,
      color: '#a0d911',
      status: selectedConfig ? 'active' : 'inactive'
    },
    {
      key: 'ddss_storage',
      title: 'DDSS Storage',
      description: 'Data Deduplication and Storage System configuration',
      icon: <DatabaseOutlined />,
      color: '#08979c',
      status: selectedConfig ? 'active' : 'inactive'
    }
  ];

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const [dashboardStats, configs] = await Promise.all([
        acsApiService.getDashboardStats(),
        acsApiService.getConfigurations()
      ]);
      setStats(dashboardStats);
      setConfigurations(configs);
      
      // Auto-select first active configuration if none selected
      if (!selectedConfig && configs.length > 0) {
        const activeConfig = configs.find(c => c.is_active) || configs[0];
        setSelectedConfig(activeConfig);
      }
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
      setError('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const handleCategoryClick = (category: ConfigCategory) => {
    if (!selectedConfig) {
      message.warning('Please select a Splunk environment first');
      return;
    }
    
    // Navigate to specific category page with selected config
    switch (category.key) {
      case 'ip_allow_lists':
        navigate('/splunk-acs/ip-allow-lists');
        break;
      default:
        console.log(`Navigating to ${category.title} for config: ${selectedConfig.name}`);
        message.info(`Opening ${category.title} for ${selectedConfig.name}`);
    }
  };



  const handleAddConfig = () => {
    // TODO: Navigate to add configuration page
    console.log('Adding new configuration');
  };

  if (loading) {
    return (
      <div style={{ padding: '24px', textAlign: 'center' }}>
        <Title level={3}>Loading Splunk ACS Dashboard...</Title>
      </div>
    );
  }

  if (error) {
    return (
      <Alert
        message="Error Loading Dashboard"
        description={error}
        type="error"
        showIcon
        action={
          <Button size="small" onClick={handleRefresh}>
            Retry
          </Button>
        }
      />
    );
  }

  return (
    <div style={{ padding: '24px' }}>
      {/* Header */}
      <div style={{ marginBottom: '24px' }}>
        <Row justify="space-between" align="middle">
          <Col>
            <Title level={2}>
              <CloudOutlined style={{ marginRight: '8px', color: '#1890ff' }} />
              Splunk ACS Dashboard
            </Title>
            <Text type="secondary">
              Admin Config Service for Splunk Cloud Management
            </Text>
          </Col>
          <Col>
            <Space>
              <div>
                <Text strong style={{ marginRight: 8 }}>Environment:</Text>
                <Select
                  style={{ width: 200 }}
                  placeholder="Select Splunk Environment"
                  value={selectedConfig?.id}
                  onChange={(configId) => {
                    const config = configurations.find(c => c.id === configId);
                    setSelectedConfig(config || null);
                  }}
                  disabled={configurations.length === 0}
                >
                  {configurations.map(config => (
                    <Select.Option key={config.id} value={config.id}>
                      <Space>
                        <CloudOutlined style={{ color: config.is_active ? '#52c41a' : '#d9d9d9' }} />
                        {config.name}
                        <Tag color={config.is_active ? 'success' : 'default'}>
                          {config.environment}
                        </Tag>
                      </Space>
                    </Select.Option>
                  ))}
                </Select>
              </div>
              <Button 
                icon={<ReloadOutlined />} 
                onClick={handleRefresh}
                loading={loading}
              >
                Refresh
              </Button>
              <Button 
                type="primary" 
                icon={<PlusOutlined />} 
                onClick={handleAddConfig}
              >
                Add Configuration
              </Button>
            </Space>
          </Col>
        </Row>
      </div>

      {/* Statistics */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Total Configurations"
              value={stats.totalConfigs}
              prefix={<SettingOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Active Configurations"
              value={stats.activeConfigs}
              prefix={<CloudOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Pending Changes"
              value={stats.pendingChanges}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: '#fa8c16' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Total Changes"
              value={stats.totalChanges}
              prefix={<BarChartOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Last Sync Info */}
      <Alert
        message={`Last synchronized: ${stats.lastSync}`}
        type="info"
        showIcon
        style={{ marginBottom: '24px' }}
      />

      {/* Configuration Categories */}
      <Title level={3} style={{ marginBottom: '16px' }}>
        Configuration Categories
      </Title>
      
      <Row gutter={[16, 16]}>
        {configCategories.map((category) => (
          <Col xs={24} sm={12} md={8} lg={6} key={category.key}>
            <Card
              hoverable
              onClick={() => handleCategoryClick(category)}
              style={{ cursor: 'pointer' }}
            >
              <div style={{ textAlign: 'center' }}>
                <div 
                  style={{ 
                    fontSize: '32px', 
                    color: category.color,
                    marginBottom: '8px'
                  }}
                >
                  {category.icon}
                </div>
                <Title level={5} style={{ margin: '8px 0' }}>
                  {category.title}
                </Title>
                <Text type="secondary" style={{ fontSize: '12px' }}>
                  {category.description}
                </Text>
                <div style={{ marginTop: '12px' }}>
                  <Tag color={category.color}>
                    {category.status.charAt(0).toUpperCase() + category.status.slice(1)}
                  </Tag>
                  {category.count !== undefined && (
                    <Tag color="blue">{category.count} items</Tag>
                  )}
                </div>
              </div>
            </Card>
          </Col>
        ))}
      </Row>

      {/* Quick Actions */}
      <div style={{ marginTop: '32px' }}>
        <Title level={3} style={{ marginBottom: '16px' }}>
          Quick Actions
        </Title>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} md={8}>
            <Card>
              <Title level={5}>Change Requests</Title>
              <Text type="secondary">
                View and manage pending change requests
              </Text>
              <div style={{ marginTop: '16px' }}>
                <Button type="primary" block>
                  View Changes
                </Button>
              </div>
            </Card>
          </Col>
          <Col xs={24} sm={12} md={8}>
            <Card>
              <Title level={5}>Version History</Title>
              <Text type="secondary">
                Track configuration changes and rollback options
              </Text>
              <div style={{ marginTop: '16px' }}>
                <Button type="primary" block>
                  View History
                </Button>
              </div>
            </Card>
          </Col>
          <Col xs={24} sm={12} md={8}>
            <Card>
              <Title level={5}>Health Check</Title>
              <Text type="secondary">
                Monitor Splunk Cloud API health and connectivity
              </Text>
              <div style={{ marginTop: '16px' }}>
                <Button type="primary" block>
                  Check Health
                </Button>
              </div>
            </Card>
          </Col>
        </Row>
      </div>
    </div>
  );
};

export default SplunkACSDashboard;
