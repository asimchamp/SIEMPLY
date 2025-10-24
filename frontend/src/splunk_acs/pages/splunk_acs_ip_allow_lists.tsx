import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Row, 
  Col, 
  Typography, 
  Button, 
  Space, 
  Table, 
  Tag, 
  Modal, 
  Form, 
  Input, 
  Select, 
  DatePicker, 
  Switch, 
  Alert, 
  message, 
  Popconfirm, 
  Tooltip, 
  Badge,
  Tabs,
  Timeline,
  Descriptions,
  Divider,
  Statistic,
  Progress
} from 'antd';
import { 
  PlusOutlined, 
  EditOutlined, 
  DeleteOutlined, 
  EyeOutlined, 
  HistoryOutlined,
  SecurityScanOutlined,
  CloudOutlined,
  ReloadOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  ClockCircleOutlined,
  GlobalOutlined,
  LockOutlined,
  UnlockOutlined,
  UserOutlined
} from '@ant-design/icons';
import { acsApiService, IPAllowList as BaseIPAllowList } from '../services/splunk_acs_services_index';
import dayjs from 'dayjs';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;
const { TextArea } = Input;
const { TabPane } = Tabs;

// Extended interface for the page with additional properties
interface IPAllowList extends BaseIPAllowList {
  status: 'active' | 'inactive' | 'pending' | 'error';
  priority: 'high' | 'medium' | 'low';
  created_by: string;
  last_modified_by: string;
  expiration_date?: string;
  is_temporary: boolean;
  tags?: string[];
  notes?: string;
  countries?: string[];
}

interface IPAllowListFormData {
  name: string;
  description: string;
  ip_ranges: string[];
  countries: string[];
  priority: 'high' | 'medium' | 'low';
  expiration_date?: string;
  is_temporary: boolean;
  tags: string[];
  notes: string;
}

interface ChangeHistory {
  id: string;
  change_type: 'created' | 'updated' | 'deleted' | 'activated' | 'deactivated';
  timestamp: string;
  user: string;
  description: string;
  old_value?: any;
  new_value?: any;
  status: 'success' | 'pending' | 'failed';
}

const SplunkACSIPAllowLists: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [ipAllowLists, setIPAllowLists] = useState<IPAllowList[]>([]);
  const [selectedConfig, setSelectedConfig] = useState<any>(null);
  const [configurations, setConfigurations] = useState<any[]>([]);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingItem, setEditingItem] = useState<IPAllowList | null>(null);
  const [form] = Form.useForm();
  const [activeTab, setActiveTab] = useState('current');
  const [changeHistory, setChangeHistory] = useState<ChangeHistory[]>([]);
  const [stats, setStats] = useState({
    total: 0,
    active: 0,
    inactive: 0,
    pending: 0,
    highPriority: 0
  });

  // Fetch data on component mount
  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [configs, lists] = await Promise.all([
        acsApiService.getConfigurations(),
        selectedConfig ? acsApiService.getIPAllowLists(selectedConfig.id) : Promise.resolve([])
      ]);
      
      setConfigurations(configs);
      // Cast the data to our extended interface type
      const extendedData: IPAllowList[] = lists.map((item: BaseIPAllowList) => ({
        ...item,
        status: 'active' as const, // Default status
        priority: 'medium' as const, // Default priority
        created_by: 'System', // Default creator
        last_modified_by: 'System', // Default modifier
        expiration_date: undefined,
        is_temporary: false,
        tags: [],
        notes: '',
        countries: []
      }));
      setIPAllowLists(extendedData);
      
      // Auto-select first active configuration
      if (configs.length > 0 && !selectedConfig) {
        const activeConfig = configs.find(c => c.is_active) || configs[0];
        setSelectedConfig(activeConfig);
      }
      
      // Calculate stats
      calculateStats(lists);
      
      // Generate mock change history
      generateChangeHistory(lists);
      
    } catch (error) {
      console.error('Failed to fetch data:', error);
      message.error('Failed to load IP Allow Lists data');
    } finally {
      setLoading(false);
    }
  };

  const calculateStats = (lists: BaseIPAllowList[]) => {
    setStats({
      total: lists.length,
      active: lists.length, // Assume all are active for now
      inactive: 0,
      pending: 0,
      highPriority: 0
    });
  };

  const generateChangeHistory = (lists: BaseIPAllowList[]) => {
    const history: ChangeHistory[] = [];
    
    lists.forEach((list, index) => {
      // Add creation history
      history.push({
        id: `create_${index}`,
        change_type: 'created',
        timestamp: list.created_at,
        user: 'System', // Default user
        description: `Created IP Allow List "${list.name}"`,
        status: 'success'
      });
      
      // Add update history if recently updated
      if (list.updated_at !== list.created_at) {
        history.push({
          id: `update_${index}`,
          change_type: 'updated',
          timestamp: list.updated_at,
          user: 'System', // Default user
          description: `Updated IP Allow List "${list.name}"`,
          status: 'success'
        });
      }
    });
    
    // Sort by timestamp descending
    history.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
    setChangeHistory(history);
  };

  const handleAddNew = () => {
    setEditingItem(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEdit = (record: IPAllowList) => {
    setEditingItem(record);
            form.setFieldsValue({
          name: record.name,
          description: record.description || '',
          ip_ranges: record.ip_ranges || [],
          countries: [],
          priority: record.priority || 'medium',
          expiration_date: record.expiration_date ? dayjs(record.expiration_date) : undefined,
          is_temporary: record.is_temporary || false,
          tags: record.tags || [],
          notes: record.notes || ''
        });
    setModalVisible(true);
  };

  const handleDelete = async (record: IPAllowList) => {
    try {
      if (selectedConfig) {
        await acsApiService.deleteIPAllowList(selectedConfig.id, record.id);
        message.success(`IP Allow List "${record.name}" deleted successfully`);
        fetchData();
      } else {
        message.error('Please select an environment first');
      }
    } catch (error) {
      console.error('Failed to delete IP Allow List:', error);
      message.error('Failed to delete IP Allow List');
    }
  };

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields();
      
      if (editingItem && selectedConfig) {
        // Update existing
        await acsApiService.updateIPAllowList(selectedConfig.id, editingItem.id, values);
        message.success(`IP Allow List "${values.name}" updated successfully`);
      } else if (selectedConfig) {
        // Create new
        await acsApiService.createIPAllowList(selectedConfig.id, values);
        message.success(`IP Allow List "${values.name}" created successfully`);
      } else {
        message.error('Please select an environment first');
        return;
      }
      
      setModalVisible(false);
      fetchData();
    } catch (error) {
      console.error('Failed to save IP Allow List:', error);
      message.error('Failed to save IP Allow List');
    }
  };

  const handleStatusToggle = async (record: IPAllowList) => {
    try {
      if (selectedConfig) {
        const newStatus = record.status === 'active' ? 'inactive' : 'active';
        // Create a proper update object without status to avoid type issues
        const updateData = {
          name: record.name,
          description: record.description,
          ip_ranges: record.ip_ranges,
          countries: record.countries || [],
          priority: record.priority,
          expiration_date: record.expiration_date,
          is_temporary: record.is_temporary,
          tags: record.tags || [],
          notes: record.notes || '',
          status: newStatus
        };
        await acsApiService.updateIPAllowList(selectedConfig.id, record.id, updateData);
        message.success(`IP Allow List "${record.name}" ${newStatus === 'active' ? 'activated' : 'deactivated'}`);
        fetchData();
      } else {
        message.error('Please select an environment first');
      }
    } catch (error) {
      console.error('Failed to toggle status:', error);
      message.error('Failed to update status');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'success';
      case 'inactive': return 'default';
      case 'pending': return 'processing';
      case 'error': return 'error';
      default: return 'default';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'red';
      case 'medium': return 'orange';
      case 'low': return 'green';
      default: return 'default';
    }
  };

  const columns = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: IPAllowList) => (
        <Space direction="vertical" size="small">
          <Text strong>{text}</Text>
          {record.description && (
            <Text type="secondary" style={{ fontSize: '12px' }}>
              {record.description}
            </Text>
          )}
        </Space>
      )
    },
    {
      title: 'IP Addresses',
      dataIndex: 'ip_addresses',
      key: 'ip_addresses',
      render: (addresses: string[]) => (
        <Space wrap>
          {addresses.slice(0, 3).map((addr, index) => (
            <Tag key={index} color="blue">{addr}</Tag>
          ))}
          {addresses.length > 3 && (
            <Tag color="default">+{addresses.length - 3} more</Tag>
          )}
        </Space>
      )
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string, record: IPAllowList) => (
        <Space>
          <Badge 
            status={status === 'active' ? 'success' : status === 'pending' ? 'processing' : 'default'} 
            text={status.charAt(0).toUpperCase() + status.slice(1)} 
          />
          <Switch
            size="small"
            checked={status === 'active'}
            onChange={() => handleStatusToggle(record)}
            checkedChildren={<CheckCircleOutlined />}
            unCheckedChildren={<ExclamationCircleOutlined />}
          />
        </Space>
      )
    },
    {
      title: 'Priority',
      dataIndex: 'priority',
      key: 'priority',
      render: (priority: string) => (
        <Tag color={getPriorityColor(priority)}>
          {priority.charAt(0).toUpperCase() + priority.slice(1)}
        </Tag>
      )
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => dayjs(date).format('MMM DD, YYYY')
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: IPAllowList) => (
        <Space>
          <Tooltip title="View Details">
            <Button 
              type="text" 
              icon={<EyeOutlined />} 
              size="small"
            />
          </Tooltip>
          <Tooltip title="Edit">
            <Button 
              type="text" 
              icon={<EditOutlined />} 
              size="small"
              onClick={() => handleEdit(record)}
            />
          </Tooltip>
          <Tooltip title="Delete">
            <Popconfirm
              title="Delete IP Allow List"
              description={`Are you sure you want to delete "${record.name}"?`}
              onConfirm={() => handleDelete(record)}
              okText="Yes"
              cancelText="No"
            >
              <Button 
                type="text" 
                danger 
                icon={<DeleteOutlined />} 
                size="small"
              />
            </Popconfirm>
          </Tooltip>
        </Space>
      )
    }
  ];

  const renderCurrentConfig = () => (
    <div>
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Total Lists"
              value={stats.total}
              prefix={<SecurityScanOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Active Lists"
              value={stats.active}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="High Priority"
              value={stats.highPriority}
              prefix={<ExclamationCircleOutlined />}
              valueStyle={{ color: '#fa541c' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Coverage"
              value={stats.total > 0 ? Math.round((stats.active / stats.total) * 100) : 0}
              suffix="%"
              prefix={<GlobalOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      <Card
        title={
          <Space>
            <SecurityScanOutlined />
            <span>IP Allow Lists</span>
            <Badge count={stats.total} style={{ backgroundColor: '#1890ff' }} />
          </Space>
        }
        extra={
          <Space>
            <Select
              style={{ width: 200 }}
              placeholder="Select Environment"
              value={selectedConfig?.id}
              onChange={(configId) => {
                const config = configurations.find(c => c.id === configId);
                setSelectedConfig(config || null);
              }}
            >
              {configurations.map(config => (
                <Select.Option key={config.id} value={config.id}>
                  <Space>
                    <CloudOutlined />
                    {config.name}
                    <Tag color={config.is_active ? 'success' : 'default'}>
                      {config.environment}
                    </Tag>
                  </Space>
                </Select.Option>
              ))}
            </Select>
            <Button 
              type="primary" 
              icon={<PlusOutlined />}
              onClick={handleAddNew}
            >
              Add New List
            </Button>
            <Button 
              icon={<ReloadOutlined />}
              onClick={fetchData}
              loading={loading}
            >
              Refresh
            </Button>
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={ipAllowLists}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => 
              `${range[0]}-${range[1]} of ${total} items`
          }}
        />
      </Card>
    </div>
  );

  const renderChangeHistory = () => (
    <Card
      title={
        <Space>
          <HistoryOutlined />
          <span>Change History</span>
          <Badge count={changeHistory.length} style={{ backgroundColor: '#722ed1' }} />
        </Space>
      }
    >
      <Timeline>
        {changeHistory.map((change) => (
          <Timeline.Item
            key={change.id}
            color={
              change.status === 'success' ? 'green' : 
              change.status === 'pending' ? 'blue' : 'red'
            }
            dot={
              change.change_type === 'created' ? <PlusOutlined /> :
              change.change_type === 'updated' ? <EditOutlined /> :
              change.change_type === 'deleted' ? <DeleteOutlined /> :
              <ClockCircleOutlined />
            }
          >
            <Space direction="vertical" size="small">
              <Space>
                <Text strong>{change.description}</Text>
                <Tag color={getStatusColor(change.status)}>
                  {change.status.charAt(0).toUpperCase() + change.status.slice(1)}
                </Tag>
              </Space>
              <Space size="large">
                <Text type="secondary">
                  <ClockCircleOutlined /> {dayjs(change.timestamp).format('MMM DD, YYYY HH:mm')}
                </Text>
                <Text type="secondary">
                  <UserOutlined /> {change.user}
                </Text>
              </Space>
            </Space>
          </Timeline.Item>
        ))}
      </Timeline>
    </Card>
  );

  const renderActiveInfoOnly = () => (
    <div>
      <Card
        title={
          <Space>
            <CheckCircleOutlined />
            <span>Active IP Allow Lists</span>
            <Badge count={stats.active} style={{ backgroundColor: '#52c41a' }} />
          </Space>
        }
        extra={
          <Button 
            icon={<ReloadOutlined />}
            onClick={fetchData}
          >
            Refresh
          </Button>
        }
      >
        <Table
          dataSource={ipAllowLists.filter(list => list.status === 'active')}
          columns={columns.filter(col => col.key !== 'actions')} // Remove actions column for read-only view
          rowKey="id"
          pagination={false}
          size="small"
          scroll={{ x: 1200 }}
        />
      </Card>
    </div>
  );

  const renderConfigurationForm = () => (
    <Modal
      title={
        <Space>
          <SecurityScanOutlined />
          <span>{editingItem ? 'Edit IP Allow List' : 'Create New IP Allow List'}</span>
        </Space>
      }
      open={modalVisible}
      onOk={handleModalOk}
      onCancel={() => setModalVisible(false)}
      width={800}
      okText={editingItem ? 'Update' : 'Create'}
      cancelText="Cancel"
    >
      <Form
        form={form}
        layout="vertical"
        initialValues={{
          priority: 'medium',
          is_temporary: false,
          tags: [],
          ip_ranges: [],
          countries: []
        }}
      >
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              name="name"
              label="List Name"
              rules={[{ required: true, message: 'Please enter a name' }]}
            >
              <Input placeholder="e.g., Corporate Office IPs" />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              name="priority"
              label="Priority"
              rules={[{ required: true, message: 'Please select priority' }]}
            >
              <Select>
                <Option value="high">High</Option>
                <Option value="medium">Medium</Option>
                <Option value="low">Low</Option>
              </Select>
            </Form.Item>
          </Col>
        </Row>

        <Form.Item
          name="description"
          label="Description"
        >
          <TextArea 
            rows={3} 
            placeholder="Describe the purpose of this IP allow list"
          />
        </Form.Item>

        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              name="ip_ranges"
              label="IP Addresses & CIDR Blocks"
              rules={[{ required: true, message: 'Please enter at least one IP address or CIDR block' }]}
            >
              <Select
                mode="tags"
                placeholder="Enter IP addresses (e.g., 192.168.1.1) or CIDR blocks (e.g., 192.168.1.0/24)"
                open={false}
                onSelect={(value) => {
                  const current = form.getFieldValue('ip_ranges') || [];
                  // Prevent duplicate entries
                  if (!current.includes(value)) {
                    form.setFieldValue('ip_ranges', [...current, value]);
                  }
                }}
                onDeselect={(value: string) => {
                  const current = form.getFieldValue('ip_ranges') || [];
                  form.setFieldValue('ip_ranges', current.filter((item: string) => item !== value));
                }}
              />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              name="countries"
              label="Countries"
            >
              <Select
                mode="multiple"
                placeholder="Select countries"
                showSearch
                optionFilterProp="children"
              >
                <Option value="US">United States</Option>
                <Option value="CA">Canada</Option>
                <Option value="GB">United Kingdom</Option>
                <Option value="DE">Germany</Option>
                <Option value="FR">France</Option>
                <Option value="JP">Japan</Option>
                <Option value="AU">Australia</Option>
                <Option value="IN">India</Option>
              </Select>
            </Form.Item>
          </Col>
        </Row>

        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              name="expiration_date"
              label="Expiration Date"
            >
              <DatePicker 
                style={{ width: '100%' }}
                placeholder="Select expiration date"
                showTime
              />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              name="is_temporary"
              label="Temporary List"
              valuePropName="checked"
            >
              <Switch 
                checkedChildren="Yes" 
                unCheckedChildren="No"
              />
            </Form.Item>
          </Col>
        </Row>

        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              name="tags"
              label="Tags"
            >
              <Select
                mode="tags"
                placeholder="Add tags for organization"
                open={false}
              />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              name="notes"
              label="Notes"
            >
              <TextArea 
                rows={3}
                placeholder="Additional notes about this IP allow list"
              />
            </Form.Item>
          </Col>
        </Row>

        <Form.Item
          name="notes"
          label="Notes"
        >
          <TextArea 
            rows={3} 
            placeholder="Additional notes or comments"
          />
        </Form.Item>
      </Form>
    </Modal>
  );

  if (loading && ipAllowLists.length === 0) {
    return (
      <div style={{ padding: '24px', textAlign: 'center' }}>
        <Title level={3}>Loading IP Allow Lists...</Title>
      </div>
    );
  }

  return (
    <div style={{ padding: '24px' }}>
      <Row justify="space-between" align="middle" style={{ marginBottom: 24 }}>
        <Col>
          <Title level={2}>
            <SecurityScanOutlined style={{ marginRight: 12, color: '#1890ff' }} />
            IP Allow Lists Management
          </Title>
          <Paragraph type="secondary">
            Configure and manage IP address allow lists for network access control in your Splunk Cloud environment
          </Paragraph>
        </Col>
      </Row>

      {!selectedConfig && (
        <Alert
          message="No Environment Selected"
          description="Please select a Splunk Cloud environment from the dropdown above to manage IP Allow Lists."
          type="warning"
          showIcon
          style={{ marginBottom: 24 }}
        />
      )}

      <Tabs 
        activeKey={activeTab} 
        onChange={setActiveTab}
        items={[
          {
            key: 'current',
            label: (
              <Space>
                <SecurityScanOutlined />
                Current Configuration
                <Badge count={stats.total} style={{ backgroundColor: '#1890ff' }} />
              </Space>
            ),
            children: renderCurrentConfig()
          },
          {
            key: 'active',
            label: (
              <Space>
                <CheckCircleOutlined />
                Active Info Only
                <Badge count={stats.active} style={{ backgroundColor: '#52c41a' }} />
              </Space>
            ),
            children: renderActiveInfoOnly()
          },
          {
            key: 'history',
            label: (
              <Space>
                <HistoryOutlined />
                Change History
                <Badge count={changeHistory.length} style={{ backgroundColor: '#722ed1' }} />
              </Space>
            ),
            children: renderChangeHistory()
          }
        ]}
      />

      {renderConfigurationForm()}
    </div>
  );
};

export default SplunkACSIPAllowLists;
