import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Table, 
  Button, 
  Space, 
  Modal, 
  Form, 
  Input, 
  Select, 
  Switch, 
  Tag, 
  Typography, 
  message, 
  Popconfirm,
  Tooltip,
  Badge
} from 'antd';
import { 
  PlusOutlined, 
  EditOutlined, 
  DeleteOutlined, 
  EyeOutlined,
  CloudOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';
import { acsApiService, SplunkCloudConfig } from '../services/splunk_acs_services_index';

const { Title, Text } = Typography;
const { Option } = Select;

interface ConfigFormData {
  name: string;
  stack_id: string;
  auth_token: string;
  region: string;
  environment: string;
  is_active: boolean;
}

const SplunkACSConfigs: React.FC = () => {
  const [configs, setConfigs] = useState<SplunkCloudConfig[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingConfig, setEditingConfig] = useState<SplunkCloudConfig | null>(null);
  const [form] = Form.useForm();

  const regions = [
    'us-east-1', 'us-west-2', 'eu-west-1', 'eu-central-1',
    'ap-southeast-1', 'ap-southeast-2', 'ap-northeast-1',
    'ca-central-1', 'sa-east-1', 'af-south-1'
  ];

  const environments = ['prod', 'dev', 'staging', 'test'];

  useEffect(() => {
    fetchConfigs();
  }, []);

  const fetchConfigs = async () => {
    try {
      setLoading(true);
      const data = await acsApiService.getConfigurations();
      setConfigs(data);
    } catch (error) {
      console.error('Error fetching configs:', error);
      message.error('Failed to fetch configurations');
    } finally {
      setLoading(false);
    }
  };

  const handleAddConfig = () => {
    setEditingConfig(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEditConfig = (config: SplunkCloudConfig) => {
    setEditingConfig(config);
    form.setFieldsValue({
      name: config.name,
      stack_id: config.stack_id,
      region: config.region,
      environment: config.environment,
      is_active: config.is_active
    });
    setModalVisible(true);
  };

  const handleDeleteConfig = async (id: number) => {
    try {
      console.log('Deleting config:', id);
      await acsApiService.deleteConfiguration(id);
      console.log('Delete successful');
      setConfigs(configs.filter(config => config.id !== id));
      message.success('Configuration deleted successfully');
    } catch (error) {
      console.error('Error deleting configuration:', error);
      message.error(`Failed to delete configuration: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields();
      console.log('Form values:', values);
      
      if (editingConfig) {
        // Update existing config
        console.log('Updating config:', editingConfig.id, values);
        const updatedConfig = await acsApiService.updateConfiguration(editingConfig.id, values);
        console.log('Update response:', updatedConfig);
        setConfigs(configs.map(config => 
          config.id === editingConfig.id ? updatedConfig : config
        ));
        message.success('Configuration updated successfully');
      } else {
        // Create new config
        console.log('Creating new config:', values);
        const newConfig = await acsApiService.createConfiguration(values);
        console.log('Create response:', newConfig);
        setConfigs([newConfig, ...configs]);
        message.success('Configuration created successfully');
      }
      
      setModalVisible(false);
      form.resetFields();
    } catch (error) {
      console.error('Error saving configuration:', error);
      message.error(`Failed to save configuration: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  const handleModalCancel = () => {
    setModalVisible(false);
    setEditingConfig(null);
    form.resetFields();
  };

  const columns = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: SplunkCloudConfig) => (
        <Space>
          <CloudOutlined style={{ color: record.is_active ? '#52c41a' : '#d9d9d9' }} />
          <Text strong>{text}</Text>
          {record.is_active && <Badge status="success" text="Active" />}
        </Space>
      )
    },
    {
      title: 'Stack ID',
      dataIndex: 'stack_id',
      key: 'stack_id',
      render: (text: string) => <Text code>{text}</Text>
    },
    {
      title: 'Region',
      dataIndex: 'region',
      key: 'region',
      render: (text: string) => <Tag color="blue">{text}</Tag>
    },
    {
      title: 'Environment',
      dataIndex: 'environment',
      key: 'environment',
      render: (text: string) => {
        const colors = {
          prod: 'red',
          dev: 'green',
          staging: 'orange',
          test: 'purple'
        };
        return <Tag color={colors[text as keyof typeof colors]}>{text.toUpperCase()}</Tag>;
      }
    },
    {
      title: 'Status',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (active: boolean) => (
        <Tag color={active ? 'success' : 'default'}>
          {active ? 'Active' : 'Inactive'}
        </Tag>
      )
    },
    {
      title: 'Last Updated',
      dataIndex: 'updated_at',
      key: 'updated_at',
      render: (text: string) => new Date(text).toLocaleDateString()
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: SplunkCloudConfig) => (
        <Space>
          <Tooltip title="View Details">
            <Button 
              type="text" 
              icon={<EyeOutlined />} 
              size="small"
            />
          </Tooltip>
          <Tooltip title="Edit Configuration">
            <Button 
              type="text" 
              icon={<EditOutlined />} 
              size="small"
              onClick={() => handleEditConfig(record)}
            />
          </Tooltip>
          <Popconfirm
            title="Delete Configuration"
            description="Are you sure you want to delete this configuration? This action cannot be undone."
            onConfirm={() => handleDeleteConfig(record.id)}
            okText="Yes"
            cancelText="No"
            okType="danger"
          >
            <Tooltip title="Delete Configuration">
              <Button 
                type="text" 
                icon={<DeleteOutlined />} 
                size="small"
                danger
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      )
    }
  ];

  return (
    <div style={{ padding: '24px' }}>
      {/* Header */}
      <div style={{ marginBottom: '24px' }}>
        <Title level={2}>
          <CloudOutlined style={{ marginRight: '8px', color: '#1890ff' }} />
          Splunk Cloud Configurations
        </Title>
        <Text type="secondary">
          Manage your Splunk Cloud stack configurations and credentials
        </Text>
      </div>

      {/* Actions */}
      <div style={{ marginBottom: '16px' }}>
        <Button 
          type="primary" 
          icon={<PlusOutlined />} 
          onClick={handleAddConfig}
        >
          Add Configuration
        </Button>
      </div>

      {/* Configurations Table */}
      <Card>
        <Table
          columns={columns}
          dataSource={configs}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => 
              `${range[0]}-${range[1]} of ${total} configurations`
          }}
        />
      </Card>

      {/* Add/Edit Modal */}
      <Modal
        title={editingConfig ? 'Edit Configuration' : 'Add Configuration'}
        open={modalVisible}
        onOk={handleModalOk}
        onCancel={handleModalCancel}
        width={600}
        okText={editingConfig ? 'Update' : 'Create'}
        cancelText="Cancel"
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{ is_active: true, environment: 'prod' }}
        >
          <Form.Item
            name="name"
            label="Configuration Name"
            rules={[
              { required: true, message: 'Please enter configuration name' },
              { min: 3, message: 'Name must be at least 3 characters' }
            ]}
          >
            <Input placeholder="e.g., Production Splunk Cloud" />
          </Form.Item>

          <Form.Item
            name="stack_id"
            label="Stack ID"
            rules={[
              { required: true, message: 'Please enter stack ID' },
              { pattern: /^[a-zA-Z0-9-_]+$/, message: 'Invalid stack ID format' }
            ]}
          >
            <Input placeholder="e.g., prod-stack-123" />
          </Form.Item>

          <Form.Item
            name="auth_token"
            label="Authentication Token"
            rules={[
              { required: true, message: 'Please enter authentication token' }
            ]}
          >
            <Input.Password placeholder="Enter your Splunk Cloud auth token" />
          </Form.Item>

          <Form.Item
            name="region"
            label="Region"
            rules={[
              { required: true, message: 'Please select a region' }
            ]}
          >
            <Select placeholder="Select region">
              {regions.map(region => (
                <Option key={region} value={region}>
                  {region.toUpperCase()}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="environment"
            label="Environment"
            rules={[
              { required: true, message: 'Please select an environment' }
            ]}
          >
            <Select placeholder="Select environment">
              {environments.map(env => (
                <Option key={env} value={env}>
                  {env.charAt(0).toUpperCase() + env.slice(1)}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="is_active"
            label="Active Status"
            valuePropName="checked"
          >
            <Switch 
              checkedChildren={<CheckCircleOutlined />} 
              unCheckedChildren={<CloseCircleOutlined />}
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default SplunkACSConfigs;
