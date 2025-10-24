import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Typography,
  Tag,
  Popconfirm,
  message,
  Modal,
  Descriptions,
  Badge,
  Tooltip,
  Input,
  theme
} from 'antd';
import {
  PlusOutlined,
  DeleteOutlined,
  EyeOutlined,
  PlayCircleOutlined,
  SearchOutlined,
  FileTextOutlined,
  ClockCircleOutlined,
  EditOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import styled from '@emotion/styled';

const { Title, Text } = Typography;
const { Search } = Input;

const StyledCard = styled(Card)`
  margin-bottom: 16px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
`;

interface Playbook {
  id: string;
  name: string;
  content: string;
  created_at: string;
  updated_at: string;
  size: number;
}

const PlaybookList: React.FC = () => {
  const [playbooks, setPlaybooks] = useState<Playbook[]>([]);
  const { token } = theme.useToken();
  const [loading, setLoading] = useState(true);
  const [searchText, setSearchText] = useState('');
  const [previewModalVisible, setPreviewModalVisible] = useState(false);
  const [selectedPlaybook, setSelectedPlaybook] = useState<Playbook | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchPlaybooks();
  }, []);

  const fetchPlaybooks = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/playbooks');
      if (response.ok) {
        const data = await response.json();
        setPlaybooks(data.playbooks || []);
      } else {
        message.error('Failed to fetch playbooks');
      }
    } catch (error) {
      message.error('Error fetching playbooks');
    } finally {
      setLoading(false);
    }
  };

  const deletePlaybook = async (playbookId: string) => {
    try {
      // Extract just the filename from the full path
      const filename = playbookId.split('/').pop() || playbookId;
      const response = await fetch(`/api/playbooks/${encodeURIComponent(filename)}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        message.success('Playbook deleted successfully');
        fetchPlaybooks();
      } else {
        message.error('Failed to delete playbook');
      }
    } catch (error) {
      message.error('Error deleting playbook');
    }
  };

  const executePlaybook = async (playbookId: string) => {
    try {
      console.log('Executing playbook:', playbookId);
      // Extract just the filename from the full path
      const filename = playbookId.split('/').pop() || playbookId;
      
      // Show immediate feedback
      message.loading('Starting playbook execution...', 0);
      
      const response = await fetch(`/api/playbooks/${encodeURIComponent(filename)}/execute`, {
        method: 'POST',
      });

      if (response.ok) {
        const data = await response.json();
        message.destroy(); // Clear the loading message
        message.success(`Playbook execution started successfully! Execution ID: ${data.execution_id}`);
        console.log('Execution response:', data);
        
        // Redirect to executions page to monitor progress
        navigate('/executions', { 
          state: { 
            highlightExecutionId: data.execution_id,
            message: `Playbook "${filename}" execution started successfully`
          } 
        });
      } else {
        const errorData = await response.json();
        console.error('Execution error:', errorData);
        message.destroy(); // Clear the loading message
        message.error(`Failed to execute playbook: ${errorData.detail || response.statusText}`);
      }
    } catch (error: any) {
      console.error('Error executing playbook:', error);
      message.destroy(); // Clear the loading message
      const errorMessage = error?.message || 'Unknown error';
      message.error(`Error executing playbook: ${errorMessage}`);
    }
  };

  const showPreview = (playbook: Playbook) => {
    setSelectedPlaybook(playbook);
    setPreviewModalVisible(true);
  };

  const editPlaybook = (playbook: Playbook) => {
    // Navigate to PlaybookBuilder with edit mode
    navigate('/playbook-builder', { 
      state: { 
        editMode: true, 
        playbook: playbook 
      } 
    });
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleString();
  };

  const filteredPlaybooks = playbooks.filter(playbook =>
    playbook.name.toLowerCase().includes(searchText.toLowerCase()) ||
    playbook.content.toLowerCase().includes(searchText.toLowerCase())
  );

  const columns = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      render: (text: string) => (
        <div>
          <FileTextOutlined style={{ marginRight: '8px', color: '#1890ff' }} />
          <Text strong>{text}</Text>
        </div>
      ),
      sorter: (a: Playbook, b: Playbook) => a.name.localeCompare(b.name),
    },
    {
      title: 'Size',
      dataIndex: 'size',
      key: 'size',
      render: (size: number) => (
        <Tag color="blue">{formatFileSize(size)}</Tag>
      ),
      sorter: (a: Playbook, b: Playbook) => a.size - b.size,
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => (
        <div>
          <ClockCircleOutlined style={{ marginRight: '4px' }} />
          {formatDate(date)}
        </div>
      ),
      sorter: (a: Playbook, b: Playbook) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
    },
    {
      title: 'Updated',
      dataIndex: 'updated_at',
      key: 'updated_at',
      render: (date: string) => (
        <div>
          <ClockCircleOutlined style={{ marginRight: '4px' }} />
          {formatDate(date)}
        </div>
      ),
      sorter: (a: Playbook, b: Playbook) => new Date(a.updated_at).getTime() - new Date(b.updated_at).getTime(),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: Playbook) => (
        <Space size="small">
          <Tooltip title="Preview Playbook">
            <Button
              type="text"
              icon={<EyeOutlined />}
              onClick={() => showPreview(record)}
            />
          </Tooltip>
          <Tooltip title="Edit Playbook">
            <Button
              type="text"
              icon={<EditOutlined />}
              onClick={() => editPlaybook(record)}
            />
          </Tooltip>
          <Tooltip title="Execute Playbook">
            <Button
              type="text"
              icon={<PlayCircleOutlined />}
              onClick={() => executePlaybook(record.id)}
            />
          </Tooltip>
          <Popconfirm
            title="Are you sure you want to delete this playbook?"
            onConfirm={() => deletePlaybook(record.id)}
            okText="Yes"
            cancelText="No"
          >
            <Tooltip title="Delete Playbook">
              <Button
                type="text"
                danger
                icon={<DeleteOutlined />}
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto' }}>
      <StyledCard>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div>
            <Title level={2} style={{ margin: 0 }}>
              Automation Playbooks
            </Title>
            <Text type="secondary">
              Manage and execute your automation playbooks
            </Text>
          </div>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => navigate('/playbook-builder')}
          >
            Create New Playbook
          </Button>
        </div>

        <div style={{ marginBottom: '16px' }}>
          <Search
            placeholder="Search playbooks by name or content..."
            allowClear
            enterButton={<SearchOutlined />}
            size="large"
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ maxWidth: '400px' }}
          />
        </div>

        <Table
          columns={columns}
          dataSource={filteredPlaybooks}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} playbooks`,
          }}
          locale={{
            emptyText: (
              <div style={{ textAlign: 'center', padding: '40px' }}>
                <FileTextOutlined style={{ fontSize: '48px', color: '#d9d9d9', marginBottom: '16px' }} />
                <div>No playbooks found</div>
                <Text type="secondary">Create your first playbook to get started</Text>
              </div>
            ),
          }}
        />
      </StyledCard>

      <Modal
        title={`Playbook Preview: ${selectedPlaybook?.name}`}
        open={previewModalVisible}
        onCancel={() => setPreviewModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setPreviewModalVisible(false)}>
            Close
          </Button>,
          <Button
            key="execute"
            type="primary"
            icon={<PlayCircleOutlined />}
            onClick={() => {
              if (selectedPlaybook) {
                executePlaybook(selectedPlaybook.id);
                setPreviewModalVisible(false);
              }
            }}
          >
            Execute Playbook
          </Button>,
        ]}
        width={800}
      >
        {selectedPlaybook && (
          <div>
            <Descriptions column={2} style={{ marginBottom: '16px' }}>
              <Descriptions.Item label="Name">{selectedPlaybook.name}</Descriptions.Item>
              <Descriptions.Item label="Size">{formatFileSize(selectedPlaybook.size)}</Descriptions.Item>
              <Descriptions.Item label="Created">{formatDate(selectedPlaybook.created_at)}</Descriptions.Item>
              <Descriptions.Item label="Updated">{formatDate(selectedPlaybook.updated_at)}</Descriptions.Item>
            </Descriptions>
            
            <div style={{ marginTop: '16px' }}>
              <Text strong>YAML Content:</Text>
              <pre
                style={{
                  backgroundColor: token.colorBgContainer,
                  color: token.colorText,
                  padding: '16px',
                  borderRadius: '4px',
                  overflow: 'auto',
                  maxHeight: '400px',
                  marginTop: '8px',
                  fontSize: '12px',
                  lineHeight: '1.4',
                  border: `1px solid ${token.colorBorderSecondary}`
                }}
              >
                {selectedPlaybook.content}
              </pre>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default PlaybookList; 