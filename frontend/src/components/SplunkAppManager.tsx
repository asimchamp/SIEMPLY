import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  message,
  Modal,
  Form,
  Select,
  Input,
  Tag,
  Typography,
  Popconfirm,
  Alert,
  Tooltip,
  Badge
} from 'antd';
import {
  AppstoreOutlined,
  DeleteOutlined,
  ReloadOutlined,
  PlusOutlined,
  InfoCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';
import { hostService, Host } from '../services/api';
import api from '../services/api';

const { Title, Text } = Typography;
const { Option } = Select;

interface SplunkApp {
  name: string;
  path: string;
  is_siemply: boolean;
  has_app_conf: boolean;
}

interface SplunkAppManagerProps {
  visible: boolean;
  onClose: () => void;
}

const SplunkAppManager: React.FC<SplunkAppManagerProps> = ({ visible, onClose }) => {
  const [hosts, setHosts] = useState<Host[]>([]);
  const [selectedHost, setSelectedHost] = useState<number | null>(null);
  const [apps, setApps] = useState<SplunkApp[]>([]);
  const [loading, setLoading] = useState(false);
  const [deployModalVisible, setDeployModalVisible] = useState(false);
  const [deployForm] = Form.useForm();
  const [deploying, setDeploying] = useState(false);

  // Load hosts when component becomes visible
  useEffect(() => {
    if (visible) {
      fetchHosts();
    }
  }, [visible]);

  // Load apps when host changes
  useEffect(() => {
    if (selectedHost) {
      fetchApps(selectedHost);
    }
  }, [selectedHost]);

  const fetchHosts = async () => {
    try {
      const allHosts = await hostService.getAllHosts();
      const splunkHosts = allHosts.filter(host => 
        host.roles.some(role => role.includes('splunk'))
      );
      setHosts(splunkHosts);
    } catch (error) {
      console.error('Failed to fetch hosts:', error);
      message.error('Failed to load host data');
    }
  };

  const fetchApps = async (hostId: number) => {
    try {
      setLoading(true);
      const response = await api.get(`/configs/splunk/apps/${hostId}`);
      setApps(response.data.apps || []);
    } catch (error) {
      console.error('Failed to fetch apps:', error);
      message.error('Failed to load Splunk apps');
      setApps([]);
    } finally {
      setLoading(false);
    }
  };

  const handleDeployApp = async (values: any) => {
    try {
      setDeploying(true);
      const response = await api.post(`/configs/splunk/apps/${selectedHost}`, {
        cluster_name: values.cluster_name,
        component_type: values.component_type,
        target_base_dir: '/opt/splunk/etc/apps'
      });

      if (response.data.success) {
        message.success(`Successfully deployed app: ${response.data.app_name}`);
        setDeployModalVisible(false);
        deployForm.resetFields();
        // Refresh apps list
        if (selectedHost) {
          fetchApps(selectedHost);
        }
      } else {
        message.error(`Deployment failed: ${response.data.message}`);
      }
    } catch (error: any) {
      console.error('Failed to deploy app:', error);
      message.error(`Deployment failed: ${error.response?.data?.detail || error.message}`);
    } finally {
      setDeploying(false);
    }
  };

  const handleRemoveApp = async (appName: string) => {
    try {
      const response = await api.delete(`/configs/splunk/apps/${selectedHost}/${appName}`);
      
      if (response.data.success) {
        message.success(`App ${appName} removed successfully`);
        // Refresh apps list
        if (selectedHost) {
          fetchApps(selectedHost);
        }
      } else {
        message.error(`Failed to remove app: ${response.data.error}`);
      }
    } catch (error: any) {
      console.error('Failed to remove app:', error);
      message.error(`Failed to remove app: ${error.response?.data?.detail || error.message}`);
    }
  };

  const columns = [
    {
      title: 'App Name',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record: SplunkApp) => (
        <Space>
          <Text strong>{name}</Text>
          {record.is_siemply && (
            <Tag color="blue" icon={<AppstoreOutlined />}>
              SIEMply
            </Tag>
          )}
        </Space>
      ),
    },
    {
      title: 'Path',
      dataIndex: 'path',
      key: 'path',
      render: (path: string) => (
        <Text code style={{ fontSize: '12px' }}>
          {path}
        </Text>
      ),
    },
    {
      title: 'Status',
      key: 'status',
      render: (record: SplunkApp) => (
        <Space>
          {record.has_app_conf ? (
            <Badge 
              status="success" 
              text={
                <Space>
                  <CheckCircleOutlined style={{ color: '#52c41a' }} />
                  <Text style={{ color: '#52c41a' }}>Valid</Text>
                </Space>
              }
            />
          ) : (
            <Badge 
              status="warning" 
              text={
                <Space>
                  <ExclamationCircleOutlined style={{ color: '#faad14' }} />
                  <Text style={{ color: '#faad14' }}>No app.conf</Text>
                </Space>
              }
            />
          )}
        </Space>
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (record: SplunkApp) => (
        <Space>
          <Tooltip title="View app details">
            <Button 
              type="text" 
              icon={<InfoCircleOutlined />} 
              size="small"
              onClick={() => message.info(`App path: ${record.path}`)}
            />
          </Tooltip>
          <Popconfirm
            title={`Remove app "${record.name}"?`}
            description="This will delete the app configuration and restart Splunk. Are you sure?"
            onConfirm={() => handleRemoveApp(record.name)}
            okText="Yes"
            cancelText="No"
            okType="danger"
          >
            <Button 
              type="text" 
              danger 
              icon={<DeleteOutlined />} 
              size="small"
            />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <Modal
      title={
        <Title level={4}>
          <AppstoreOutlined style={{ marginRight: 8 }} />
          Splunk Configuration App Manager
        </Title>
      }
      open={visible}
      onCancel={onClose}
      width={1000}
      footer={null}
      destroyOnClose={false}
    >
      <div style={{ marginBottom: 16 }}>
        <Space>
          <Text strong>Target Host:</Text>
          <Select
            placeholder="Select a host"
            style={{ width: 300 }}
            value={selectedHost}
            onChange={setSelectedHost}
            showSearch
            optionFilterProp="children"
          >
            {hosts.map(host => (
              <Option key={host.id} value={host.id}>
                {host.hostname} ({host.ip_address})
              </Option>
            ))}
          </Select>
          
          {selectedHost && (
            <>
              <Button
                icon={<PlusOutlined />}
                type="primary"
                onClick={() => setDeployModalVisible(true)}
              >
                Deploy New App
              </Button>
              <Button
                icon={<ReloadOutlined />}
                onClick={() => fetchApps(selectedHost)}
                loading={loading}
              >
                Refresh
              </Button>
            </>
          )}
        </Space>
      </div>

      {selectedHost && (
        <Card title="Splunk Configuration Apps" size="small">
          <Table
            columns={columns}
            dataSource={apps}
            rowKey="name"
            loading={loading}
            pagination={false}
            size="small"
            locale={{
              emptyText: 'No configuration apps found on this host'
            }}
          />
        </Card>
      )}

      {/* Deploy App Modal */}
      <Modal
        title="Deploy Splunk Configuration App"
        open={deployModalVisible}
        onCancel={() => setDeployModalVisible(false)}
        footer={null}
        destroyOnClose={false}
      >
        <Form
          form={deployForm}
          layout="vertical"
          onFinish={handleDeployApp}
        >
          <Form.Item
            name="cluster_name"
            label="Cluster Name"
            rules={[{ required: true, message: 'Please enter cluster name' }]}
          >
            <Input placeholder="e.g., splunk_prod_new" />
          </Form.Item>
          
          <Form.Item
            name="component_type"
            label="Component Type"
            rules={[{ required: true, message: 'Please select component type' }]}
          >
            <Select placeholder="Select component type">
              <Option value="splunk_cm">Cluster Master</Option>
              <Option value="splunk_deployer">Deployer</Option>
              <Option value="splunk_license_master">License Master</Option>
              <Option value="splunk_monitoring_console">Monitoring Console</Option>
              <Option value="splunk_deployment_server">Deployment Server</Option>
              <Option value="splunk_search_head">Search Head</Option>
              <Option value="splunk_indexer">Indexer</Option>
              <Option value="splunk_hf">Heavy Forwarder</Option>
              <Option value="splunk_uf">Universal Forwarder</Option>
            </Select>
          </Form.Item>

          <Alert
            message="Configuration Deployment"
            description="This will copy configuration files from the cluster configuration directory to the target host as a Splunk app. The app will be created in /opt/splunk/etc/apps/ and Splunk will be restarted automatically."
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />

          <Form.Item>
            <Space>
              <Button 
                type="primary" 
                htmlType="submit" 
                loading={deploying}
              >
                Deploy App
              </Button>
              <Button onClick={() => setDeployModalVisible(false)}>
                Cancel
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </Modal>
  );
};

export default SplunkAppManager;
