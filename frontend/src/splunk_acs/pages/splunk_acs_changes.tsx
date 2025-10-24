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
  DatePicker, 
  Tag, 
  Typography, 
  message, 
  Popconfirm,
  Tooltip,
  Badge,
  Steps,
  Descriptions,
  Divider,
  Alert,
  Row,
  Col
} from 'antd';
import { 
  PlusOutlined, 
  EditOutlined, 
  DeleteOutlined, 
  EyeOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
  ExclamationCircleOutlined,
  UserOutlined,
  TeamOutlined,
  SafetyOutlined,
  PlayCircleOutlined,
  RollbackOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { acsApiService, ChangeRequest } from '../services/splunk_acs_services_index';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;
const { TextArea } = Input;
const { Step } = Steps;

interface ChangeRequestFormData {
  title: string;
  description: string;
  change_type: 'configuration' | 'emergency' | 'scheduled';
  priority: 'low' | 'medium' | 'high' | 'critical';
  resource_type: string;
  resource_id?: string;
  scheduled_date?: string;
  risk_assessment: 'low' | 'medium' | 'high';
  implementation_plan?: string;
  rollback_plan?: string;
  proposed_changes: string;
}

const SplunkACSChanges: React.FC = () => {
  const [changeRequests, setChangeRequests] = useState<ChangeRequest[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [selectedChange, setSelectedChange] = useState<ChangeRequest | null>(null);
  const [editingChange, setEditingChange] = useState<ChangeRequest | null>(null);
  const [form] = Form.useForm();

  const changeTypes = [
    { value: 'configuration', label: 'Configuration Change', color: 'blue' },
    { value: 'emergency', label: 'Emergency Change', color: 'red' },
    { value: 'scheduled', label: 'Scheduled Change', color: 'orange' }
  ];

  const priorities = [
    { value: 'low', label: 'Low', color: 'green' },
    { value: 'medium', label: 'Medium', color: 'blue' },
    { value: 'high', label: 'High', color: 'orange' },
    { value: 'critical', label: 'Critical', color: 'red' }
  ];

  const riskLevels = [
    { value: 'low', label: 'Low', color: 'green' },
    { value: 'medium', label: 'Medium', color: 'orange' },
    { value: 'high', label: 'High', color: 'red' }
  ];

  const resourceTypes = [
    'ip_allow_list', 'index', 'app', 'user', 'role', 'auth_token',
    'maintenance_window', 'hec_token', 'limits_conf', 'ddss_storage'
  ];

  useEffect(() => {
    fetchChangeRequests();
  }, []);

  const fetchChangeRequests = async () => {
    try {
      setLoading(true);
      const data = await acsApiService.getChangeRequests();
      setChangeRequests(data);
    } catch (error) {
      console.error('Error fetching change requests:', error);
      message.error('Failed to fetch change requests');
    } finally {
      setLoading(false);
    }
  };

  const handleAddChange = () => {
    setEditingChange(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEditChange = (change: ChangeRequest) => {
    if (change.status !== 'draft') {
      message.warning('Only draft changes can be edited');
      return;
    }
    
    setEditingChange(change);
    form.setFieldsValue({
      title: change.title,
      description: change.description,
      change_type: change.change_type,
      priority: change.priority,
      resource_type: change.resource_type,
      resource_id: change.resource_id,
      scheduled_date: change.scheduled_date ? dayjs(change.scheduled_date) : undefined,
      risk_assessment: change.risk_assessment,
      implementation_plan: change.implementation_plan,
      rollback_plan: change.rollback_plan,
      proposed_changes: JSON.stringify(change.proposed_changes, null, 2)
    });
    setModalVisible(true);
  };

  const handleViewDetails = (change: ChangeRequest) => {
    setSelectedChange(change);
    setDetailModalVisible(true);
  };

  const handleDeleteChange = async (id: number) => {
    try {
      // TODO: Replace with actual API call when delete endpoint is available
      // await acsApiService.deleteChangeRequest(id);
      
      setChangeRequests(changeRequests.filter(change => change.id !== id));
      message.success('Change request deleted successfully');
    } catch (error) {
      message.error('Failed to delete change request');
    }
  };

  const handleModalOk = async () => {
    try {
      const values = await form.validateFields();
      
      if (editingChange) {
        // Update existing change request
        // TODO: Replace with actual API call
        setChangeRequests(changeRequests.map(change => 
          change.id === editingChange.id 
            ? { ...change, ...values, updated_at: new Date().toISOString() }
            : change
        ));
        message.success('Change request updated successfully');
      } else {
        // Create new change request
        const newChange: ChangeRequest = {
          id: Date.now().toString(),
          request_id: `CR-2024-${String(changeRequests.length + 1).padStart(3, '0')}`,
          ...values,
          status: 'draft',
          requester_id: 1, // TODO: Get from auth context
          requester_name: 'Current User', // TODO: Get from auth context
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          proposed_changes: JSON.parse(values.proposed_changes || '{}')
        };
        
        setChangeRequests([newChange, ...changeRequests]);
        message.success('Change request created successfully');
      }
      
      setModalVisible(false);
      form.resetFields();
    } catch (error) {
      message.error('Failed to save change request');
    }
  };

  const handleModalCancel = () => {
    setModalVisible(false);
    setEditingChange(null);
    form.resetFields();
  };

  const getStatusColor = (status: string) => {
    const colors = {
      draft: 'default',
      pending: 'processing',
      approved: 'success',
      implementing: 'warning',
      implemented: 'success',
      rejected: 'error',
      failed: 'error'
    };
    return colors[status as keyof typeof colors] || 'default';
  };

  const getStatusIcon = (status: string) => {
    const icons = {
      draft: <EditOutlined />,
      pending: <ClockCircleOutlined />,
      approved: <CheckCircleOutlined />,
      implementing: <PlayCircleOutlined />,
      implemented: <CheckCircleOutlined />,
      rejected: <CloseCircleOutlined />,
      failed: <ExclamationCircleOutlined />
    };
    return icons[status as keyof typeof icons] || <ClockCircleOutlined />;
  };

  const columns = [
    {
      title: 'Request ID',
      dataIndex: 'request_id',
      key: 'request_id',
      render: (text: string) => <Text code>{text}</Text>
    },
    {
      title: 'Title',
      dataIndex: 'title',
      key: 'title',
      render: (text: string, record: ChangeRequest) => (
        <Space direction="vertical" size="small">
          <Text strong>{text}</Text>
          <Space size="small">
            <Tag color={changeTypes.find(t => t.value === record.change_type)?.color}>
              {changeTypes.find(t => t.value === record.change_type)?.label}
            </Tag>
            <Tag color={priorities.find(p => p.value === record.priority)?.color}>
              {priorities.find(p => p.value === record.priority)?.label}
            </Tag>
          </Space>
        </Space>
      )
    },
    {
      title: 'Resource',
      key: 'resource',
      render: (_: any, record: ChangeRequest) => (
        <Space direction="vertical" size="small">
          <Text>{record.resource_type?.replace('_', ' ').toUpperCase() || 'N/A'}</Text>
          {record.resource_id && <Text code>{record.resource_id}</Text>}
        </Space>
      )
    },
    {
      title: 'Requester',
      dataIndex: 'requester_name',
      key: 'requester_name',
      render: (text: string) => (
        <Space>
          <UserOutlined />
          <Text>{text}</Text>
        </Space>
      )
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string, record: ChangeRequest) => (
        <Space>
          {getStatusIcon(status)}
          <Tag color={getStatusColor(status)}>
            {status.charAt(0).toUpperCase() + status.slice(1)}
          </Tag>
          {record.scheduled_date && status === 'pending' && (
            <Tag color="blue">
              {dayjs(record.scheduled_date).format('MMM DD, YYYY')}
            </Tag>
          )}
        </Space>
      )
    },
    {
      title: 'Risk',
      dataIndex: 'risk_assessment',
      key: 'risk_assessment',
      render: (risk: string) => (
        <Tag color={riskLevels.find(r => r.value === risk)?.color}>
          {riskLevels.find(r => r.value === risk)?.label}
        </Tag>
      )
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (text: string) => dayjs(text).format('MMM DD, YYYY')
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: ChangeRequest) => (
        <Space>
          <Tooltip title="View Details">
            <Button 
              type="text" 
              icon={<EyeOutlined />} 
              size="small"
              onClick={() => handleViewDetails(record)}
            />
          </Tooltip>
          {record.status === 'draft' && (
            <Tooltip title="Edit Change Request">
              <Button 
                type="text" 
                icon={<EditOutlined />} 
                size="small"
                onClick={() => handleEditChange(record)}
              />
            </Tooltip>
          )}
          {record.status === 'draft' && (
            <Popconfirm
              title="Delete Change Request"
              description="Are you sure you want to delete this change request?"
              onConfirm={() => handleDeleteChange(record.id)}
              okText="Yes"
              cancelText="No"
              okType="danger"
            >
              <Tooltip title="Delete Change Request">
                <Button 
                  type="text" 
                  icon={<DeleteOutlined />} 
                  size="small"
                  danger
                />
              </Tooltip>
            </Popconfirm>
          )}
        </Space>
      )
    }
  ];

  const getWorkflowSteps = (change: ChangeRequest) => {
    const steps: Array<{ title: string; status: 'wait' | 'process' | 'finish' | 'error' }> = [
      { title: 'Draft', status: 'finish' },
      { title: 'Team Lead Review', status: 'finish' },
      { title: 'Admin Review', status: 'finish' },
      { title: 'Security Review', status: 'finish' },
      { title: 'Implementation', status: 'finish' },
      { title: 'Complete', status: 'finish' }
    ];

    // Adjust based on change type and priority
    if (change.change_type === 'emergency') {
      steps[1].status = 'finish'; // Skip some approvals for emergency
    }

    if (change.priority === 'low') {
      steps[2].status = 'finish'; // Skip admin review for low priority
    }

    // Set current step based on status
    const statusIndex = {
      draft: 0,
      pending: 1,
      approved: 3,
      implementing: 4,
      implemented: 5,
      rejected: 1,
      failed: 4
    };

    const currentStep = statusIndex[change.status as keyof typeof statusIndex] || 0;
    
    steps.forEach((step, index) => {
      if (index < currentStep) {
        step.status = 'finish';
      } else if (index === currentStep) {
        step.status = 'process';
      } else {
        step.status = 'wait';
      }
    });

    return steps;
  };

  return (
    <div style={{ padding: '24px' }}>
      {/* Header */}
      <div style={{ marginBottom: '24px' }}>
        <Title level={2}>
          <EditOutlined style={{ marginRight: '8px', color: '#1890ff' }} />
          Change Requests
        </Title>
        <Text type="secondary">
          Manage configuration changes with JIRA-like workflow and approval system
        </Text>
      </div>

      {/* Actions */}
      <div style={{ marginBottom: '16px' }}>
        <Button 
          type="primary" 
          icon={<PlusOutlined />} 
          onClick={handleAddChange}
        >
          Create Change Request
        </Button>
      </div>

      {/* Change Requests Table */}
      <Card>
        <Table
          columns={columns}
          dataSource={changeRequests}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => 
              `${range[0]}-${range[1]} of ${total} change requests`
          }}
        />
      </Card>

      {/* Add/Edit Modal */}
      <Modal
        title={editingChange ? 'Edit Change Request' : 'Create Change Request'}
        open={modalVisible}
        onOk={handleModalOk}
        onCancel={handleModalCancel}
        width={800}
        okText={editingChange ? 'Update' : 'Create'}
        cancelText="Cancel"
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{ 
            change_type: 'configuration', 
            priority: 'medium', 
            risk_assessment: 'low' 
          }}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="title"
                label="Title"
                rules={[
                  { required: true, message: 'Please enter change request title' }
                ]}
              >
                <Input placeholder="Brief description of the change" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="change_type"
                label="Change Type"
                rules={[
                  { required: true, message: 'Please select change type' }
                ]}
              >
                <Select placeholder="Select change type">
                  {changeTypes.map(type => (
                    <Option key={type.value} value={type.value}>
                      {type.label}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="description"
            label="Description"
            rules={[
              { required: true, message: 'Please enter change description' }
            ]}
          >
            <TextArea 
              rows={3} 
              placeholder="Detailed description of what needs to be changed and why"
            />
          </Form.Item>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                name="priority"
                label="Priority"
                rules={[
                  { required: true, message: 'Please select priority' }
                ]}
              >
                <Select placeholder="Select priority">
                  {priorities.map(priority => (
                    <Option key={priority.value} value={priority.value}>
                      {priority.label}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="resource_type"
                label="Resource Type"
                rules={[
                  { required: true, message: 'Please select resource type' }
                ]}
              >
                <Select placeholder="Select resource type">
                  {resourceTypes.map(type => (
                    <Option key={type} value={type}>
                      {type.replace('_', ' ').toUpperCase()}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="risk_assessment"
                label="Risk Assessment"
                rules={[
                  { required: true, message: 'Please select risk level' }
                ]}
              >
                <Select placeholder="Select risk level">
                  {riskLevels.map(risk => (
                    <Option key={risk.value} value={risk.value}>
                      {risk.label}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="resource_id"
                label="Resource ID (Optional)"
              >
                <Input placeholder="Specific resource identifier if applicable" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="scheduled_date"
                label="Scheduled Date (Optional)"
              >
                <DatePicker 
                  showTime 
                  placeholder="Select scheduled date and time"
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="implementation_plan"
            label="Implementation Plan (Optional)"
          >
            <TextArea 
              rows={2} 
              placeholder="Step-by-step plan for implementing the change"
            />
          </Form.Item>

          <Form.Item
            name="rollback_plan"
            label="Rollback Plan (Optional)"
          >
            <TextArea 
              rows={2} 
              placeholder="Plan for rolling back if issues occur"
            />
          </Form.Item>

          <Form.Item
            name="proposed_changes"
            label="Proposed Changes (JSON)"
            rules={[
              { required: true, message: 'Please enter proposed changes in JSON format' },
              {
                validator: (_, value) => {
                  if (!value) return Promise.resolve();
                  try {
                    JSON.parse(value);
                    return Promise.resolve();
                  } catch (error) {
                    return Promise.reject(new Error('Invalid JSON format'));
                  }
                }
              }
            ]}
          >
            <TextArea 
              rows={4} 
              placeholder='{"key": "value", "setting": "new_value"}'
            />
          </Form.Item>
        </Form>
      </Modal>

      {/* Detail Modal */}
      <Modal
        title={`Change Request Details - ${selectedChange?.request_id}`}
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={null}
        width={900}
      >
        {selectedChange && (
          <div>
            {/* Workflow Steps */}
            <Card title="Approval Workflow" style={{ marginBottom: '16px' }}>
              <Steps current={getWorkflowSteps(selectedChange).findIndex(step => step.status === 'process')}>
                {getWorkflowSteps(selectedChange).map((step, index) => (
                  <Step key={index} title={step.title} status={step.status} />
                ))}
              </Steps>
            </Card>

            {/* Change Details */}
            <Descriptions title="Change Details" bordered column={2}>
              <Descriptions.Item label="Title" span={2}>
                {selectedChange.title}
              </Descriptions.Item>
              <Descriptions.Item label="Description" span={2}>
                {selectedChange.description}
              </Descriptions.Item>
              <Descriptions.Item label="Change Type">
                <Tag color={changeTypes.find(t => t.value === selectedChange.change_type)?.color}>
                  {changeTypes.find(t => t.value === selectedChange.change_type)?.label}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Priority">
                <Tag color={priorities.find(p => p.value === selectedChange.priority)?.color}>
                  {priorities.find(p => p.value === selectedChange.priority)?.label}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Resource Type">
                {selectedChange.resource_type?.replace('_', ' ').toUpperCase() || 'N/A'}
              </Descriptions.Item>
              <Descriptions.Item label="Resource ID">
                {selectedChange.resource_id || 'N/A'}
              </Descriptions.Item>
              <Descriptions.Item label="Risk Assessment">
                <Tag color={riskLevels.find(r => r.value === selectedChange.risk_assessment)?.color}>
                  {riskLevels.find(r => r.value === selectedChange.risk_assessment)?.label}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Status">
                <Tag color={getStatusColor(selectedChange.status)}>
                  {selectedChange.status.charAt(0).toUpperCase() + selectedChange.status.slice(1)}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Requester">
                {selectedChange.requester_name}
              </Descriptions.Item>
              <Descriptions.Item label="Created">
                {dayjs(selectedChange.created_at).format('MMM DD, YYYY HH:mm')}
              </Descriptions.Item>
              {selectedChange.scheduled_date && (
                <Descriptions.Item label="Scheduled Date">
                  {dayjs(selectedChange.scheduled_date).format('MMM DD, YYYY HH:mm')}
                </Descriptions.Item>
              )}
              {selectedChange.approved_at && (
                <Descriptions.Item label="Approved">
                  {dayjs(selectedChange.approved_at).format('MMM DD, YYYY HH:mm')}
                </Descriptions.Item>
              )}
              {selectedChange.implemented_at && (
                <Descriptions.Item label="Implemented">
                  {dayjs(selectedChange.implemented_at).format('MMM DD, YYYY HH:mm')}
                </Descriptions.Item>
              )}
            </Descriptions>

            {/* Additional Information */}
            {(selectedChange.implementation_plan || selectedChange.rollback_plan) && (
              <>
                <Divider />
                {selectedChange.implementation_plan && (
                  <div style={{ marginBottom: '16px' }}>
                    <Title level={5}>Implementation Plan</Title>
                    <Paragraph>{selectedChange.implementation_plan}</Paragraph>
                  </div>
                )}
                {selectedChange.rollback_plan && (
                  <div>
                    <Title level={5}>Rollback Plan</Title>
                    <Paragraph>{selectedChange.rollback_plan}</Paragraph>
                  </div>
                )}
              </>
            )}

            {/* Actions */}
            <Divider />
            <Space>
              {selectedChange.status === 'approved' && (
                <Button type="primary" icon={<PlayCircleOutlined />}>
                  Implement Change
                </Button>
              )}
              {selectedChange.status === 'implemented' && (
                <Button icon={<RollbackOutlined />}>
                  Rollback
                </Button>
              )}
              <Button onClick={() => setDetailModalVisible(false)}>
                Close
              </Button>
            </Space>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default SplunkACSChanges;
