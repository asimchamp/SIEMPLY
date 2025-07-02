import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Typography, 
  Table, 
  Button, 
  Modal, 
  Form, 
  Input, 
  Select, 
  Switch, 
  Tag, 
  message, 
  Popconfirm,
  Space,
  Divider,
  Tooltip,
  InputNumber,
  DatePicker,
  Upload,
  Row,
  Col,
  Tabs,
  Badge,
  List
} from 'antd';
import { 
  DatabaseOutlined, 
  PlusOutlined, 
  EditOutlined, 
  DeleteOutlined, 
  SyncOutlined,
  DownloadOutlined,
  UploadOutlined,
  SettingOutlined,
  InfoCircleOutlined,
  FireOutlined,
  ThunderboltOutlined,
  StarOutlined,
  StarFilled,
  MinusCircleOutlined
} from '@ant-design/icons';
import { packageService, SoftwarePackage, CreatePackageData, UpdatePackageData, DownloadEntry } from '../services/api';
import { ColumnType } from 'antd/es/table';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { Option } = Select;
const { TextArea } = Input;

// Package types with icons and display names
const PACKAGE_TYPES: Record<string, { label: string; icon: React.ReactNode; color: string }> = {
  'splunk_uf': { label: 'Splunk Universal Forwarder', icon: <FireOutlined />, color: 'green' },
  'splunk_enterprise': { label: 'Splunk Enterprise', icon: <FireOutlined />, color: 'green' },
  'cribl_stream_leader': { label: 'Cribl Stream Leader', icon: <ThunderboltOutlined />, color: 'blue' },
  'cribl_stream_worker': { label: 'Cribl Stream Worker', icon: <ThunderboltOutlined />, color: 'blue' },
  'cribl_edge': { label: 'Cribl Edge', icon: <ThunderboltOutlined />, color: 'blue' }
};

const PACKAGE_STATUSES: Record<string, { label: string; color: string }> = {
  'active': { label: 'Active', color: 'success' },
  'deprecated': { label: 'Deprecated', color: 'warning' },
  'beta': { label: 'Beta', color: 'processing' },
  'archived': { label: 'Archived', color: 'default' }
};

const Database: React.FC = () => {
  const [packages, setPackages] = useState<SoftwarePackage[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [modalVisible, setModalVisible] = useState<boolean>(false);
  const [editingPackage, setEditingPackage] = useState<SoftwarePackage | null>(null);
  const [form] = Form.useForm();
  const [activeTab, setActiveTab] = useState<string>('all');
  const [availableTypes, setAvailableTypes] = useState<string[]>([]);
  const [availableStatuses, setAvailableStatuses] = useState<string[]>([]);

  // Load packages on component mount
  useEffect(() => {
    fetchPackages();
    fetchMetadata();
  }, []);

  const fetchPackages = async () => {
    try {
      setLoading(true);
      const packagesData = await packageService.getAllPackages();
      setPackages(packagesData);
      setError(null);
    } catch (err) {
      console.error('Error fetching packages:', err);
      setError('Failed to fetch package data. Please check your connection to the API server.');
    } finally {
      setLoading(false);
    }
  };

  const fetchMetadata = async () => {
    try {
      const [types, statuses] = await Promise.all([
        packageService.getAvailableTypes(),
        packageService.getAvailableStatuses()
      ]);
      setAvailableTypes(types);
      setAvailableStatuses(statuses);
    } catch (err) {
      console.error('Error fetching metadata:', err);
    }
  };

  // Show create modal
  const showCreateModal = () => {
    setEditingPackage(null);
    form.resetFields();
    // Initialize with one empty download entry
    form.setFieldsValue({
      downloads: [{ architecture: 'x86_64', download_url: '', file_size: undefined, checksum: '', os_compatibility: ['linux'] }]
    });
    setModalVisible(true);
  };

  // Show edit modal
  const showEditModal = (pkg: SoftwarePackage) => {
    setEditingPackage(pkg);
    const downloads = pkg.downloads && pkg.downloads.length > 0 
      ? pkg.downloads 
      : pkg.download_url 
        ? [{ 
            architecture: pkg.architecture, 
            download_url: pkg.download_url, 
            file_size: pkg.file_size, 
            checksum: pkg.checksum,
            os_compatibility: pkg.os_compatibility || ['linux']
          }] 
        : [{ architecture: 'x86_64', download_url: '', file_size: undefined, checksum: '', os_compatibility: ['linux'] }];
    
    form.setFieldsValue({
      ...pkg,
      downloads,
      release_date: pkg.release_date ? dayjs(pkg.release_date) : null,
      support_end_date: pkg.support_end_date ? dayjs(pkg.support_end_date) : null,
      default_ports: pkg.default_ports ? JSON.stringify(pkg.default_ports, null, 2) : null,
      min_requirements: pkg.min_requirements ? JSON.stringify(pkg.min_requirements, null, 2) : null
    });
    setModalVisible(true);
  };

  // Handle form submission
  const handleSubmit = async (values: any) => {
    try {
      // Ensure downloads array has at least one entry
      if (!values.downloads || values.downloads.length === 0) {
        message.error('Please add at least one download entry');
        return;
      }

      // Validate downloads
      for (const download of values.downloads) {
        if (!download.download_url || !download.architecture) {
          message.error('Each download entry must have a URL and architecture');
          return;
        }
      }

      const formData: CreatePackageData | UpdatePackageData = {
        ...values,
        downloads: values.downloads,
        release_date: values.release_date ? values.release_date.toISOString() : null,
        support_end_date: values.support_end_date ? values.support_end_date.toISOString() : null,
        default_ports: values.default_ports ? JSON.parse(values.default_ports) : null,
        min_requirements: values.min_requirements ? JSON.parse(values.min_requirements) : null
      };

      if (editingPackage) {
        await packageService.updatePackage(editingPackage.id, formData);
        message.success('Package updated successfully');
      } else {
        await packageService.createPackage(formData as CreatePackageData);
        message.success('Package created successfully');
      }

      setModalVisible(false);
      form.resetFields();
      fetchPackages();
    } catch (err: any) {
      console.error('Error saving package:', err);
      message.error(err.response?.data?.detail || 'Failed to save package');
    }
  };

  // Handle delete
  const handleDelete = async (id: number) => {
    try {
      await packageService.deletePackage(id);
      message.success('Package deleted successfully');
      fetchPackages();
    } catch (err: any) {
      console.error('Error deleting package:', err);
      message.error(err.response?.data?.detail || 'Failed to delete package');
    }
  };

  // Handle set default
  const handleSetDefault = async (id: number) => {
    try {
      await packageService.setDefaultPackage(id);
      message.success('Package set as default successfully');
      fetchPackages();
    } catch (err: any) {
      console.error('Error setting default package:', err);
      message.error(err.response?.data?.detail || 'Failed to set default package');
    }
  };

  // Filter packages by type
  const getPackagesByType = (type?: string) => {
    if (!type || type === 'all') return packages;
    return packages.filter(pkg => pkg.package_type === type);
  };

  // Get package count by type
  const getPackageCount = (type: string) => {
    if (type === 'all') return packages.length;
    return packages.filter(pkg => pkg.package_type === type).length;
  };

  // Table columns
  const columns: ColumnType<SoftwarePackage>[] = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: SoftwarePackage) => (
        <Space>
          {PACKAGE_TYPES[record.package_type]?.icon}
          <span>{text}</span>
          {record.is_default && (
            <Tooltip title="Default version for this package type">
              <StarFilled style={{ color: '#faad14' }} />
            </Tooltip>
          )}
        </Space>
      ),
    },
    {
      title: 'Type',
      dataIndex: 'package_type',
      key: 'package_type',
      render: (type: string) => (
        <Tag color={PACKAGE_TYPES[type]?.color || 'default'}>
          {PACKAGE_TYPES[type]?.label || type.replace(/_/g, ' ').toUpperCase()}
        </Tag>
      ),
      filters: Object.keys(PACKAGE_TYPES).map(type => ({
        text: PACKAGE_TYPES[type].label,
        value: type
      })),
      onFilter: (value: any, record: SoftwarePackage) => record.package_type === value,
    },
    {
      title: 'Version',
      dataIndex: 'version',
      key: 'version',
      sorter: (a: SoftwarePackage, b: SoftwarePackage) => a.version.localeCompare(b.version),
    },
    {
      title: 'Vendor',
      dataIndex: 'vendor',
      key: 'vendor',
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={PACKAGE_STATUSES[status]?.color || 'default'}>
          {PACKAGE_STATUSES[status]?.label || status.toUpperCase()}
        </Tag>
      ),
      filters: Object.keys(PACKAGE_STATUSES).map(status => ({
        text: PACKAGE_STATUSES[status].label,
        value: status
      })),
      onFilter: (value: any, record: SoftwarePackage) => record.status === value,
    },
    {
      title: 'Downloads',
      key: 'downloads',
      render: (_, record: SoftwarePackage) => {
        const downloads = record.downloads || [];
        if (downloads.length === 0) {
          // Show legacy download if no new downloads
          return record.download_url ? (
            <Tag color="blue">{record.architecture}</Tag>
          ) : 'No downloads';
        }
        return (
          <Space direction="vertical" size="small">
            {downloads.map((download, index) => (
              <Tag key={index} color="blue">
                {download.architecture} 
                {download.file_size && ` (${download.file_size.toFixed(2)}MB)`}
              </Tag>
            ))}
          </Space>
        );
      },
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => dayjs(date).format('YYYY-MM-DD'),
      sorter: (a: SoftwarePackage, b: SoftwarePackage) => 
        new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record: SoftwarePackage) => (
        <Space>
          <Tooltip title="Edit package">
            <Button
              type="text"
              icon={<EditOutlined />}
              size="small"
              onClick={() => showEditModal(record)}
            />
          </Tooltip>
          {!record.is_default && (
            <Tooltip title="Set as default">
              <Button
                type="text"
                icon={<StarOutlined />}
                size="small"
                onClick={() => handleSetDefault(record.id)}
              />
            </Tooltip>
          )}
          <Popconfirm
            title="Are you sure you want to delete this package?"
            onConfirm={() => handleDelete(record.id)}
            okText="Yes"
            cancelText="No"
          >
            <Tooltip title="Delete package">
              <Button
                type="text"
                icon={<DeleteOutlined />}
                size="small"
                danger
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  // Modal footer
  const modalFooter = [
    <Button key="cancel" onClick={() => setModalVisible(false)}>
      Cancel
    </Button>,
    <Button key="submit" type="primary" onClick={() => form.submit()}>
      {editingPackage ? 'Update' : 'Create'}
    </Button>
  ];

  const tabItems = [
    {
      key: 'all',
      label: (
        <span>
          <DatabaseOutlined />
          All Packages
          <Badge count={getPackageCount('all')} showZero style={{ marginLeft: 8 }} />
        </span>
      ),
      children: (
        <Table 
          dataSource={getPackagesByType(activeTab)} 
          columns={columns} 
          rowKey="id" 
          loading={loading} 
          pagination={{ pageSize: 20 }}
        />
      )
    },
    ...Object.entries(PACKAGE_TYPES).map(([type, config]) => ({
      key: type,
      label: (
        <span>
          {config.icon}
          {config.label}
          <Badge count={getPackageCount(type)} showZero style={{ marginLeft: 8 }} />
        </span>
      ),
      children: (
        <Table 
          dataSource={getPackagesByType(type)} 
          columns={columns} 
          rowKey="id" 
          loading={loading} 
          pagination={{ pageSize: 20 }}
        />
      )
    }))
  ];

  return (
    <div className="database-container">
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>
          <DatabaseOutlined /> Software Package Database
        </Title>
        <Text>Manage Splunk and Cribl software package inventory</Text>
      </div>

      <Card>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
          <Title level={4}>
            <DatabaseOutlined /> Package Inventory
          </Title>
          <Space>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={showCreateModal}
            >
              Add Package
            </Button>
            <Button
              icon={<SyncOutlined spin={loading} />}
              onClick={fetchPackages}
              disabled={loading}
            >
              Refresh
            </Button>
          </Space>
        </div>

        {error && (
          <div style={{ marginBottom: 16 }}>
            <Text type="danger">{error}</Text>
          </div>
        )}

        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={tabItems}
        />
      </Card>

      {/* Package Form Modal */}
      <Modal
        title={
          <Title level={4}>
            <DatabaseOutlined /> {editingPackage ? 'Edit Package' : 'Add New Package'}
          </Title>
        }
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={modalFooter}
        width={800}
        destroyOnClose={true}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="name"
                label="Package Name"
                rules={[{ required: true, message: 'Please enter package name' }]}
              >
                <Input placeholder="e.g., Splunk Universal Forwarder" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="package_type"
                label="Package Type"
                rules={[{ required: true, message: 'Please select package type' }]}
              >
                <Select placeholder="Select package type">
                  {availableTypes.map(type => (
                    <Option key={type} value={type}>
                      {PACKAGE_TYPES[type]?.label || type.replace(/_/g, ' ').toUpperCase()}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                name="version"
                label="Version"
                rules={[{ required: true, message: 'Please enter version' }]}
              >
                <Input placeholder="e.g., 9.4.3" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="vendor"
                label="Vendor"
                initialValue="Splunk Inc."
              >
                <Select>
                  <Option value="Splunk Inc.">Splunk Inc.</Option>
                  <Option value="Cribl Inc.">Cribl Inc.</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="status"
                label="Status"
                initialValue="active"
              >
                <Select>
                  {availableStatuses.map(status => (
                    <Option key={status} value={status}>
                      {PACKAGE_STATUSES[status]?.label || status.toUpperCase()}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="description"
            label="Description"
          >
            <TextArea rows={3} placeholder="Package description..." />
          </Form.Item>

          {/* Downloads Section */}
          <Divider orientation="left">Download Options</Divider>
          <Form.List
            name="downloads"
            initialValue={[{ architecture: 'x86_64', download_url: '', file_size: undefined, checksum: '', os_compatibility: ['linux'] }]}
          >
            {(fields, { add, remove }) => (
              <>
                {fields.map(({ key, name, ...restField }) => (
                  <Card 
                    key={key} 
                    size="small" 
                    style={{ marginBottom: 16 }}
                    title={`Download Option ${name + 1}`}
                    extra={
                      fields.length > 1 && (
                        <Button
                          type="text"
                          danger
                          icon={<MinusCircleOutlined />}
                          onClick={() => remove(name)}
                        />
                      )
                    }
                  >
                    <Row gutter={16}>
                      <Col span={8}>
                        <Form.Item
                          {...restField}
                          name={[name, 'architecture']}
                          label="Architecture"
                          rules={[{ required: true, message: 'Architecture is required' }]}
                        >
                          <Select placeholder="Select architecture">
                            <Option value="x86_64">x86_64</Option>
                            <Option value="arm64">ARM64</Option>
                            <Option value="aarch64">AArch64</Option>
                            <Option value="universal">Universal</Option>
                          </Select>
                        </Form.Item>
                      </Col>
                      <Col span={10}>
                        <Form.Item
                          {...restField}
                          name={[name, 'download_url']}
                          label="Download URL"
                          rules={[{ required: true, message: 'Download URL is required' }]}
                        >
                          <Input placeholder="https://..." />
                        </Form.Item>
                      </Col>
                      <Col span={6}>
                        <Form.Item
                          {...restField}
                          name={[name, 'file_size']}
                          label="File Size (MB)"
                        >
                          <InputNumber min={0} placeholder="Size in MB" style={{ width: '100%' }} />
                        </Form.Item>
                      </Col>
                    </Row>
                    <Row gutter={16}>
                      <Col span={12}>
                        <Form.Item
                          {...restField}
                          name={[name, 'checksum']}
                          label="Checksum (SHA256)"
                        >
                          <Input placeholder="SHA256 hash" />
                        </Form.Item>
                      </Col>
                      <Col span={12}>
                        <Form.Item
                          {...restField}
                          name={[name, 'os_compatibility']}
                          label="OS Compatibility"
                          initialValue={['linux']}
                        >
                          <Select mode="multiple" placeholder="Select OS types">
                            <Option value="linux">Linux</Option>
                            <Option value="windows">Windows</Option>
                            <Option value="macos">macOS</Option>
                          </Select>
                        </Form.Item>
                      </Col>
                    </Row>
                  </Card>
                ))}
                <Form.Item>
                  <Button
                    type="dashed"
                    onClick={() => add({ architecture: 'x86_64', download_url: '', file_size: undefined, checksum: '', os_compatibility: ['linux'] })}
                    block
                    icon={<PlusOutlined />}
                  >
                    Add Download Option
                  </Button>
                </Form.Item>
              </>
            )}
          </Form.List>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                name="default_install_dir"
                label="Default Install Directory"
                initialValue="/opt"
              >
                <Input placeholder="/opt" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="default_user"
                label="Default User"
                initialValue="splunk"
              >
                <Input placeholder="splunk" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="default_group"
                label="Default Group"
                initialValue="splunk"
              >
                <Input placeholder="splunk" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="default_ports"
                label="Default Ports (JSON)"
                tooltip='JSON format: {"web": 8000, "management": 8089}'
              >
                <TextArea 
                  placeholder='{"web": 8000, "management": 8089}'
                  rows={2}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="min_requirements"
                label="Minimum Requirements (JSON)"
                tooltip='JSON format: {"ram": 4096, "disk": 20480}'
              >
                <TextArea 
                  placeholder='{"ram": 4096, "disk": 20480}'
                  rows={2}
                />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="release_date"
                label="Release Date"
              >
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="support_end_date"
                label="Support End Date"
              >
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="installation_notes"
            label="Installation Notes"
          >
            <TextArea rows={4} placeholder="Special installation instructions or notes..." />
          </Form.Item>

          <Form.Item
            name="is_default"
            label="Set as Default"
            valuePropName="checked"
            tooltip="Set this as the default version for this package type"
          >
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Database; 