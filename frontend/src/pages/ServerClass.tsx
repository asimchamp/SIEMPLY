import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Tag,
  Modal,
  Form,
  Input,
  Select,
  Typography,
  Row,
  Col,
  Statistic,
  Badge,
  Tooltip,
  Popconfirm,
  message,
  Transfer,
  Divider,
  List,
  Avatar,
  Descriptions,
  Switch,
  InputNumber,
  Alert
} from 'antd';
import {
  ClusterOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  CopyOutlined,
  SettingOutlined,
  TeamOutlined,
  DatabaseOutlined,
  CheckCircleOutlined,
  LinkOutlined,
  SearchOutlined,
  FilterOutlined,
  ExportOutlined,
  ImportOutlined
} from '@ant-design/icons';
import { hostService, Host } from '../services/api';
import { serverClassService, ServerClass as ServerClassType } from '../services/serverclassService';

interface ServerClassProps {
  hosts?: Host[];
}

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;
const { TextArea } = Input;



interface ServerClassFormData {
  name: string;
  description: string;
  tags: string[];
  is_active: boolean;
  host_ids: string[];
}

const ServerClass: React.FC<ServerClassProps> = ({ hosts: propHosts }) => {
  const [serverClasses, setServerClasses] = useState<ServerClassType[]>([]);
  const [hosts, setHosts] = useState<Host[]>([]);
  const [loading, setLoading] = useState(false);
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [isCreating, setIsCreating] = useState(true);
  const [selectedServerClass, setSelectedServerClass] = useState<ServerClassType | null>(null);
  const [selectedHostIds, setSelectedHostIds] = useState<string[]>([]);
  const [form] = Form.useForm();
  const [activeTab, setActiveTab] = useState('overview');

  // Load hosts from props or fetch from API
  useEffect(() => {
    if (propHosts && propHosts.length > 0) {
      setHosts(propHosts);
    } else {
      // Fallback to API if no props provided
      const fetchHosts = async () => {
        try {
          setLoading(true);
          const data = await hostService.getAllHosts();
          setHosts(data);
        } catch (error) {
          console.error('Failed to fetch hosts:', error);
        } finally {
          setLoading(false);
        }
      };
      fetchHosts();
    }
  }, [propHosts]);

  // Load server classes from API
  useEffect(() => {
    const fetchServerClasses = async () => {
      try {
        setLoading(true);
        const data = await serverClassService.getAllServerClasses();
        setServerClasses(data);
      } catch (error) {
        console.error('Failed to fetch server classes:', error);
        message.error('Failed to load server classes');
      } finally {
        setLoading(false);
      }
    };
    
    fetchServerClasses();
  }, []);



  const serverClassColumns = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: ServerClassType) => (
        <div>
          <Text strong>{text}</Text>
          <br />
          <Text type="secondary" style={{ fontSize: '12px' }}>
            {record.host_count} hosts • {record.created_by}
          </Text>
        </div>
      ),
    },
    {
      title: 'Description',
      dataIndex: 'description',
      key: 'description',
      render: (text: string) => (
        <Text style={{ fontSize: '12px' }}>{text}</Text>
      ),
    },
    {
      title: 'Hosts',
      key: 'hosts',
      render: (record: ServerClassType) => (
        <div>
          <Text style={{ fontSize: '12px' }}>
            {record.host_count} hosts
          </Text>
          <div style={{ marginTop: 4 }}>
            {record.hostnames.slice(0, 2).map((hostname, index) => (
              <Tag key={index} color="blue">
                {hostname}
              </Tag>
            ))}
            {record.hostnames.length > 2 && (
              <Tag>+{record.hostnames.length - 2}</Tag>
            )}
          </div>
        </div>
      ),
    },
    {
      title: 'Tags',
      dataIndex: 'tags',
      key: 'tags',
      render: (tags: string[]) => (
        <div>
          {tags.slice(0, 2).map(tag => (
            <Tag key={tag}>{tag}</Tag>
          ))}
          {tags.length > 2 && <Tag>+{tags.length - 2}</Tag>}
        </div>
      ),
    },
        {
      title: 'Status',
      key: 'status',
      render: (record: ServerClassType) => (
        <div>
          <Tag color={record.is_active ? 'green' : 'red'}>
            {record.is_active ? 'ACTIVE' : 'INACTIVE'}
          </Tag>
        </div>
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (record: ServerClassType) => (
        <Space>
          <Tooltip title="View Details">
            <Button 
              size="small" 
              icon={<EyeOutlined />}
              onClick={() => handleViewServerClass(record)}
            />
          </Tooltip>
          <Tooltip title="Edit Server Class">
            <Button 
              size="small" 
              icon={<EditOutlined />}
              onClick={() => handleEditServerClass(record)}
            />
          </Tooltip>
          <Tooltip title="Duplicate Server Class">
            <Button 
              size="small" 
              icon={<CopyOutlined />}
              onClick={() => handleDuplicateServerClass(record)}
            />
          </Tooltip>
          <Popconfirm
            title="Are you sure you want to delete this server class?"
            onConfirm={() => handleDeleteServerClass(record.id)}
          >
            <Tooltip title="Delete Server Class">
              <Button 
                size="small" 
                danger 
                icon={<DeleteOutlined />}
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];



  const handleViewServerClass = (serverClass: ServerClassType) => {
    setSelectedServerClass(serverClass);
    setActiveTab('details');
  };

  const handleEditServerClass = (serverClass: ServerClassType) => {
    setSelectedServerClass(serverClass);
    setSelectedHostIds(serverClass.host_ids.map(id => id.toString()));
    form.setFieldsValue({
      name: serverClass.name,
      description: serverClass.description,
      tags: serverClass.tags,
      is_active: serverClass.is_active
    });
    setIsCreating(false);
    setIsModalVisible(true);
  };

  const handleDuplicateServerClass = (serverClass: ServerClassType) => {
    message.success(`Server class "${serverClass.name}" duplicated successfully`);
  };

  const handleDeleteServerClass = async (serverClassId: string) => {
    try {
      const serverClass = serverClasses.find(sc => sc.id === serverClassId);
      if (serverClass) {
        await serverClassService.deleteServerClass(serverClass.name);
        setServerClasses(serverClasses.filter(sc => sc.id !== serverClassId));
        message.success('Server class deleted successfully');
      }
    } catch (error) {
      console.error('Error deleting server class:', error);
      message.error('Failed to delete server class');
    }
  };

  const showCreateModal = () => {
    form.resetFields();
    setIsCreating(true);
    setSelectedHostIds([]);
    setSelectedServerClass(null);
    setIsModalVisible(true);
  };

  const handleModalCancel = () => {
    setIsModalVisible(false);
    setSelectedHostIds([]);
  };

  const handleModalSubmit = async () => {
    try {
      const values = await form.validateFields();
      
      if (isCreating) {
        // Create new server class via API
        const hostIds = selectedHostIds.map(id => parseInt(id));
        const newServerClass = await serverClassService.createServerClass({
          name: values.name,
          description: values.description,
          host_ids: hostIds,
          tags: values.tags || [],
          is_active: values.is_active
        });
        
        setServerClasses([...serverClasses, newServerClass]);
        message.success('Server class created successfully');
      } else if (selectedServerClass) {
        // Update existing server class via API
        const hostIds = selectedHostIds.map(id => parseInt(id));
        const updatedServerClass = await serverClassService.updateServerClass(selectedServerClass.name, {
          description: values.description,
          host_ids: hostIds,
          tags: values.tags || [],
          is_active: values.is_active
        });
        
        setServerClasses(serverClasses.map(sc => 
          sc.id === selectedServerClass.id ? updatedServerClass : sc
        ));
        message.success('Server class updated successfully');
      }
      
      setIsModalVisible(false);
      setSelectedHostIds([]);
    } catch (error) {
      console.error('Form submission error:', error);
      message.error('Failed to save server class');
    }
  };

  const handleTransferChange = (targetKeys: React.Key[]) => {
    setSelectedHostIds(targetKeys.map(key => key.toString()));
  };

  const getServerClassStats = () => {
    const total = serverClasses.length;
    const active = serverClasses.filter(sc => sc.is_active).length;
    const totalHosts = serverClasses.reduce((sum, sc) => sum + sc.host_count, 0);
    
    return { total, active, totalHosts };
  };

  const stats = getServerClassStats();

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>
          <ClusterOutlined style={{ marginRight: 8 }} />
          Server Classes
        </Title>
        <Text type="secondary">
          Group hosts together to perform tasks on multiple servers simultaneously
        </Text>
      </div>

      {/* Statistics Cards */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Total Server Classes"
              value={stats.total}
              prefix={<ClusterOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Active Classes"
              value={stats.active}
              prefix={<CheckCircleOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Total Hosts"
              value={stats.totalHosts}
              prefix={<DatabaseOutlined />}
            />
          </Card>
        </Col>

      </Row>

      {/* Main Content */}
      <Card>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
          <Title level={4}>
            <ClusterOutlined /> Server Classes
          </Title>
          <Space>
            <Button 
              type="primary" 
              icon={<PlusOutlined />}
              onClick={showCreateModal}
            >
              New Server Class
            </Button>
            <Button icon={<ImportOutlined />}>
              Import
            </Button>
            <Button icon={<ExportOutlined />}>
              Export
            </Button>
          </Space>
        </div>

        <Table
          dataSource={serverClasses}
          columns={serverClassColumns}
          rowKey="id"
          pagination={{ pageSize: 10 }}
        />
      </Card>

      {/* Server Class Creation/Edit Modal */}
      <Modal
        title={isCreating ? 'Create New Server Class' : 'Edit Server Class'}
        open={isModalVisible}
        onCancel={handleModalCancel}
        onOk={handleModalSubmit}
        width={800}
        okText={isCreating ? 'Create' : 'Update'}
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{ is_active: true }}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="name"
                label="Server Class Name"
                rules={[{ required: true, message: 'Please enter a name' }]}
              >
                <Input placeholder="e.g., Web Servers, Database Servers" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="is_active"
                label="Active"
                valuePropName="checked"
              >
                <Switch />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="description"
            label="Description"
            rules={[{ required: true, message: 'Please enter a description' }]}
          >
            <TextArea 
              placeholder="Describe the purpose of this server class"
              rows={3}
            />
          </Form.Item>

          <Form.Item
            name="tags"
            label="Tags"
          >
            <Select mode="tags" placeholder="Add tags">
              <Option value="web">Web</Option>
              <Option value="database">Database</Option>
              <Option value="production">Production</Option>
              <Option value="staging">Staging</Option>
              <Option value="development">Development</Option>
              <Option value="splunk">Splunk</Option>
              <Option value="cribl">Cribl</Option>
            </Select>
          </Form.Item>

          <Divider orientation="left">Host Selection</Divider>

          <Alert
            message="Select hosts to include in this server class"
            description="You can select multiple hosts to group them together for batch operations."
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />

          <Form.Item
            label="Available Hosts"
            required
            help={`Selected ${selectedHostIds.length} hosts`}
          >
            <Transfer
              dataSource={hosts.map(host => ({
                key: host.id.toString(),
                title: `${host.hostname} (${host.ip_address})`,
                description: `${host.os_type} ${host.os_version} - ${host.roles.join(', ')}`,
                disabled: false
              }))}
              titles={['Available Hosts', 'Selected Hosts']}
              targetKeys={selectedHostIds}
              onChange={handleTransferChange}
              render={item => (
                <div>
                  <div style={{ fontWeight: 'bold' }}>{item.title}</div>
                  <div style={{ fontSize: '12px', color: '#666' }}>{item.description}</div>
                </div>
              )}
              listStyle={{
                width: 300,
                height: 400,
              }}
            />
          </Form.Item>
        </Form>
      </Modal>

      {/* Server Class Details Modal */}
      {selectedServerClass && (
        <Modal
          title={`Server Class: ${selectedServerClass.name}`}
          open={activeTab === 'details'}
          onCancel={() => setActiveTab('overview')}
          footer={[
            <Button key="close" onClick={() => setActiveTab('overview')}>
              Close
            </Button>
          ]}
          width={1000}
        >
          <Descriptions column={2} style={{ marginBottom: 24 }}>
            <Descriptions.Item label="Description">{selectedServerClass.description}</Descriptions.Item>
            <Descriptions.Item label="Created By">{selectedServerClass.created_by}</Descriptions.Item>
            <Descriptions.Item label="Host Count">{selectedServerClass.host_count}</Descriptions.Item>
            <Descriptions.Item label="Status">
              <Tag color={selectedServerClass.is_active ? 'green' : 'red'}>
                {selectedServerClass.is_active ? 'ACTIVE' : 'INACTIVE'}
              </Tag>
            </Descriptions.Item>
          </Descriptions>

          <Divider orientation="left">Hosts in this Server Class</Divider>

          <List
            dataSource={selectedServerClass.hostnames}
            renderItem={(hostname) => {
              // Find the corresponding host data
              const host = hosts.find(h => h.hostname === hostname);
              return (
                <List.Item
                  actions={[
                    <Button size="small" icon={<LinkOutlined />}>Connect</Button>,
                    <Button size="small" icon={<EyeOutlined />}>View</Button>
                  ]}
                >
                  <List.Item.Meta
                    avatar={<Avatar icon={<DatabaseOutlined />} />}
                    title={
                      <div>
                        <Text strong>{hostname}</Text>
                        {host && <Tag color="blue" style={{ marginLeft: 8 }}>{host.ip_address}</Tag>}
                      </div>
                    }
                    description={
                      <div>
                        {host && (
                          <>
                            <Text>{host.os_type} {host.os_version}</Text>
                            <br />
                            <Text type="secondary" style={{ fontSize: '12px' }}>
                              Roles: {host.roles.join(', ')}
                            </Text>
                            <br />
                            <Tag color={host.status === 'online' ? 'green' : 'red'}>
                              {host.status.toUpperCase()}
                            </Tag>
                          </>
                        )}
                      </div>
                    }
                  />
                </List.Item>
              );
            }}
          />
        </Modal>
      )}
    </div>
  );
};

export default ServerClass; 