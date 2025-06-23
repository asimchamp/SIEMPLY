import { useState, useEffect } from 'react';
import { 
  Card, 
  Typography, 
  Table, 
  Button, 
  Modal, 
  Form, 
  Input, 
  InputNumber, 
  Select, 
  Switch, 
  Tag, 
  message, 
  Popconfirm,
  Space,
  Divider,
  Tooltip
} from 'antd';
import { 
  DatabaseOutlined, 
  PlusOutlined, 
  EditOutlined, 
  DeleteOutlined, 
  SyncOutlined,
  LinkOutlined
} from '@ant-design/icons';
import { hostService, Host, CreateHostData, UpdateHostData } from '../services/api';
import { ColumnType } from 'antd/es/table';

const { Title, Text } = Typography;
const { Option } = Select;

// Available roles for hosts
const HOST_ROLES = ['splunk_uf', 'splunk_indexer', 'splunk_search_head', 'cribl_leader', 'cribl_worker'];

// OS types
const OS_TYPES = ['linux', 'windows'];

const HostManagement: React.FC = () => {
  // State for hosts data
  const [hosts, setHosts] = useState<Host[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [editingHost, setEditingHost] = useState<Host | null>(null);
  const [isModalVisible, setIsModalVisible] = useState<boolean>(false);
  const [isCreating, setIsCreating] = useState<boolean>(true);
  const [selectedRoles, setSelectedRoles] = useState<string[]>([]);
  const [form] = Form.useForm();
  const [testingConnection, setTestingConnection] = useState<boolean>(false);

  // Load hosts on component mount
  useEffect(() => {
    fetchHosts();
  }, []);

  // Fetch hosts from API
  const fetchHosts = async () => {
    try {
      setLoading(true);
      const data = await hostService.getAllHosts();
      setHosts(data);
    } catch (error) {
      console.error('Failed to fetch hosts:', error);
      message.error('Failed to load host data');
    } finally {
      setLoading(false);
    }
  };

  // Open modal for creating a new host
  const showCreateModal = () => {
    form.resetFields();
    setIsCreating(true);
    setSelectedRoles([]);
    setEditingHost(null);
    setIsModalVisible(true);
  };

  // Open modal for editing a host
  const showEditModal = (host: Host) => {
    setEditingHost(host);
    setIsCreating(false);
    setSelectedRoles(host.roles);
    form.setFieldsValue({
      hostname: host.hostname,
      ip_address: host.ip_address,
      port: host.port,
      username: host.username,
      os_type: host.os_type,
      os_version: host.os_version,
      is_active: host.is_active
    });
    setIsModalVisible(true);
  };

  // Handle modal cancel
  const handleCancel = () => {
    setIsModalVisible(false);
  };

  // Handle form submission
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      
      if (isCreating) {
        // Create new host
        const hostData: CreateHostData = {
          ...values,
          roles: selectedRoles,
          port: Number(values.port)
        };
        
        await hostService.createHost(hostData);
        message.success('Host created successfully');
      } else if (editingHost) {
        // Update existing host
        const hostData: UpdateHostData = {
          ...values,
          roles: selectedRoles,
          port: Number(values.port)
        };
        
        await hostService.updateHost(editingHost.id, hostData);
        message.success('Host updated successfully');
      }
      
      setIsModalVisible(false);
      fetchHosts();
    } catch (error) {
      console.error('Form submission error:', error);
      message.error('Failed to save host');
    }
  };

  // Handle delete host
  const handleDelete = async (id: number) => {
    try {
      await hostService.deleteHost(id);
      message.success('Host deleted successfully');
      fetchHosts();
    } catch (error) {
      console.error('Failed to delete host:', error);
      message.error('Failed to delete host');
    }
  };

  // Handle role selection
  const handleRoleChange = (roles: string[]) => {
    setSelectedRoles(roles);
  };

  // Test connection to a host
  const handleTestConnection = async (hostId: number) => {
    try {
      setTestingConnection(true);
      const result = await hostService.testConnection(hostId);
      
      if (result.success) {
        message.success('Connection successful');
      } else {
        message.error(`Connection failed: ${result.message}`);
      }
    } catch (error) {
      console.error('Connection test failed:', error);
      message.error('Connection test failed');
    } finally {
      setTestingConnection(false);
    }
  };

  // Define table columns
  const columns: ColumnType<Host>[] = [
    {
      title: 'Hostname',
      dataIndex: 'hostname',
      key: 'hostname',
      sorter: (a: Host, b: Host) => a.hostname.localeCompare(b.hostname)
    },
    {
      title: 'IP Address',
      dataIndex: 'ip_address',
      key: 'ip_address'
    },
    {
      title: 'OS',
      dataIndex: 'os_type',
      key: 'os_type',
      render: (os: string, record: Host) => {
        const osVersion = record.os_version ? ` (${record.os_version})` : '';
        return `${os}${osVersion}`;
      }
    },
    {
      title: 'Roles',
      dataIndex: 'roles',
      key: 'roles',
      render: (roles: string[]) => (
        <span>
          {roles.map(role => {
            let color = '';
            if (role.includes('splunk')) color = 'green';
            else if (role.includes('cribl')) color = 'blue';
            
            return <Tag color={color} key={role}>{role}</Tag>;
          })}
        </span>
      ),
      filters: HOST_ROLES.map(role => ({ text: role, value: role })),
      onFilter: (value: any, record: Host) => record.roles.includes(value as string)
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const color = status === 'active' ? 'green' : 'orange';
        return <Tag color={color}>{status.toUpperCase()}</Tag>;
      }
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: unknown, record: Host) => (
        <Space size="small">
          <Tooltip title="Test Connection">
            <Button 
              icon={<LinkOutlined />} 
              size="small" 
              onClick={() => handleTestConnection(record.id)}
              loading={testingConnection}
            />
          </Tooltip>
          <Tooltip title="Edit">
            <Button 
              icon={<EditOutlined />} 
              size="small" 
              onClick={() => showEditModal(record)} 
            />
          </Tooltip>
          <Tooltip title="Delete">
            <Popconfirm
              title="Are you sure you want to delete this host?"
              onConfirm={() => handleDelete(record.id)}
              okText="Yes"
              cancelText="No"
            >
              <Button 
                icon={<DeleteOutlined />} 
                size="small" 
                danger
              />
            </Popconfirm>
          </Tooltip>
        </Space>
      )
    }
  ];

  return (
    <div className="host-management-container">
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>
          <DatabaseOutlined /> Host Management
        </Title>
        <Text>Manage hosts for Splunk and Cribl deployments</Text>
      </div>

      <div style={{ marginBottom: 16 }}>
        <Button 
          type="primary"
          icon={<PlusOutlined />}
          onClick={showCreateModal}
        >
          Add Host
        </Button>
        <Button 
          icon={<SyncOutlined />}
          onClick={fetchHosts}
          style={{ marginLeft: 8 }}
        >
          Refresh
        </Button>
      </div>

      <Card>
        <Table
          dataSource={hosts}
          columns={columns}
          rowKey="id"
          loading={loading}
        />
      </Card>

      {/* Host Form Modal */}
      <Modal
        title={isCreating ? 'Add New Host' : 'Edit Host'}
        open={isModalVisible}
        onOk={handleSubmit}
        onCancel={handleCancel}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{ port: 22, os_type: 'linux', is_active: true }}
        >
          <Form.Item
            name="hostname"
            label="Hostname"
            rules={[{ required: true, message: 'Please enter a hostname' }]}
          >
            <Input placeholder="e.g., splunk-server01" />
          </Form.Item>

          <Form.Item
            name="ip_address"
            label="IP Address"
            rules={[{ required: true, message: 'Please enter an IP address' }]}
          >
            <Input placeholder="e.g., 192.168.1.100" />
          </Form.Item>

          <Form.Item
            name="port"
            label="SSH Port"
            rules={[{ required: true, message: 'Please enter port number' }]}
          >
            <InputNumber style={{ width: '100%' }} min={1} max={65535} />
          </Form.Item>

          <Form.Item
            name="username"
            label="Username"
            rules={[{ required: true, message: 'Please enter username' }]}
          >
            <Input placeholder="e.g., root" />
          </Form.Item>

          {isCreating && (
            <Form.Item
              name="password"
              label="Password"
              rules={[{ message: 'Please enter password or provide SSH key path' }]}
              extra="Either password or SSH key path is required"
            >
              <Input.Password placeholder="SSH Password" />
            </Form.Item>
          )}

          <Form.Item
            name="ssh_key_path"
            label="SSH Key Path"
          >
            <Input placeholder="/path/to/private_key" />
          </Form.Item>

          <Divider orientation="left">Configuration</Divider>

          <Form.Item
            name="os_type"
            label="Operating System"
            rules={[{ required: true, message: 'Please select an OS' }]}
          >
            <Select placeholder="Select OS">
              {OS_TYPES.map(os => (
                <Option key={os} value={os}>{os.charAt(0).toUpperCase() + os.slice(1)}</Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="os_version"
            label="OS Version"
          >
            <Input placeholder="e.g., Ubuntu 20.04, RHEL 8, etc." />
          </Form.Item>

          <Form.Item
            label="Roles"
            required
            help="Select one or more roles for this host"
          >
            <Select
              mode="multiple"
              placeholder="Select roles"
              value={selectedRoles}
              onChange={handleRoleChange}
              style={{ width: '100%' }}
            >
              {HOST_ROLES.map(role => (
                <Option key={role} value={role}>{role.replace('_', ' ')}</Option>
              ))}
            </Select>
          </Form.Item>

          {!isCreating && (
            <Form.Item
              name="is_active"
              label="Active"
              valuePropName="checked"
            >
              <Switch />
            </Form.Item>
          )}
        </Form>
      </Modal>
    </div>
  );
};

export default HostManagement; 