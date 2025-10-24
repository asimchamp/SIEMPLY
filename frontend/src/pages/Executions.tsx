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
  Select,
  DatePicker,
  Row,
  Col,
  Statistic,
  Progress,
  Timeline,
  Divider,
  Alert,
  Tabs,
  Collapse,
  Empty,
  Spin,
  theme
} from 'antd';
import {
  PlayCircleOutlined,
  StopOutlined,
  DeleteOutlined,
  EyeOutlined,
  ReloadOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ExclamationCircleOutlined,
  LoadingOutlined,
  FileTextOutlined,
  BarChartOutlined,
  HistoryOutlined,
  SearchOutlined,
  FilterOutlined,
  DownloadOutlined
} from '@ant-design/icons';
import styled from '@emotion/styled';
import dayjs from 'dayjs';
import { useLocation } from 'react-router-dom';

const { Title, Text } = Typography;
const { Search } = Input;
const { Option } = Select;
const { RangePicker } = DatePicker;
const { TabPane } = Tabs;
const { Panel } = Collapse;

const StyledCard = styled(Card)`
  margin-bottom: 16px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
`;

const StatsCard = styled(Card)`
  text-align: center;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  
  .ant-statistic-title {
    color: #666;
    font-size: 14px;
  }
  
  .ant-statistic-content {
    font-size: 24px;
    font-weight: 600;
  }
`;

// Add CSS for highlighted row
const StyledTable = styled.div`
  .highlighted-row {
    background-color: #e6f7ff !important;
    border-left: 4px solid #1890ff !important;
  }
  
  .highlighted-row:hover {
    background-color: #bae7ff !important;
  }
`;

interface Execution {
  id: number;
  execution_id: string;
  playbook_id: string;
  playbook_name: string;
  status: string;
  started_at: string;
  completed_at?: string;
  duration?: number;
  total_jobs: number;
  completed_jobs: number;
  failed_jobs: number;
  error_message?: string;
  created_by?: string;
  job_executions: JobExecution[];
}

interface JobExecution {
  id: number;
  job_id: string;
  job_name: string;
  status: string;
  started_at?: string;
  completed_at?: string;
  duration?: number;
  target_hosts?: string[];
  completed_hosts: number;
  failed_hosts: number;
  error_message?: string;
  task_executions: TaskExecution[];
}

interface TaskExecution {
  id: number;
  task_name: string;
  module: string;
  status: string;
  started_at?: string;
  completed_at?: string;
  duration?: number;
  host?: string;
  stdout?: string;
  stderr?: string;
  return_code?: number;
  changed: boolean;
  error_message?: string;
}

interface ExecutionStats {
  total_executions: number;
  successful_executions: number;
  failed_executions: number;
  running_executions: number;
  average_duration?: number;
  recent_executions: Execution[];
}

const Executions: React.FC = () => {
  const [executions, setExecutions] = useState<Execution[]>([]);
  const { token } = theme.useToken();
  const [stats, setStats] = useState<ExecutionStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [statsLoading, setStatsLoading] = useState(true);
  const [searchText, setSearchText] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs] | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [total, setTotal] = useState(0);
  const [selectedExecution, setSelectedExecution] = useState<Execution | null>(null);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [logModalVisible, setLogModalVisible] = useState(false);
  const [executionLog, setExecutionLog] = useState<any>(null);
  const [logLoading, setLogLoading] = useState(false);
  const [realTimeExecutions, setRealTimeExecutions] = useState<Set<string>>(new Set());
  const [pollingInterval, setPollingInterval] = useState<NodeJS.Timeout | null>(null);
  const [highlightExecutionId, setHighlightExecutionId] = useState<string | null>(null);
  const [welcomeMessage, setWelcomeMessage] = useState<string | null>(null);
  
  const location = useLocation();

  // Handle navigation state from playbook execution
  useEffect(() => {
    if (location.state) {
      const { highlightExecutionId: highlightId, message: welcomeMsg } = location.state as any;
      if (highlightId) {
        setHighlightExecutionId(highlightId);
        // Clear the state to prevent re-highlighting on refresh
        window.history.replaceState({}, document.title);
      }
      if (welcomeMsg) {
        setWelcomeMessage(welcomeMsg);
        message.success(welcomeMsg);
        // Clear the state to prevent re-showing on refresh
        window.history.replaceState({}, document.title);
      }
    }
  }, [location.state]);

  useEffect(() => {
    fetchExecutions();
    fetchStats();
  }, [currentPage, pageSize, searchText, statusFilter, dateRange]);

  // Real-time polling for running executions
  useEffect(() => {
    // Start polling for running executions
    const startPolling = () => {
      const interval = setInterval(() => {
        const runningExecutions = executions.filter(exec => 
          exec.status === 'running' || exec.status === 'queued'
        );
        
        if (runningExecutions.length > 0) {
          setRealTimeExecutions(new Set(runningExecutions.map(exec => exec.execution_id)));
          fetchExecutions(); // Refresh data for running executions
        } else {
          setRealTimeExecutions(new Set());
        }
      }, 2000); // Poll every 2 seconds
      
      setPollingInterval(interval);
    };

    startPolling();

    // Cleanup on unmount
    return () => {
      if (pollingInterval) {
        clearInterval(pollingInterval);
      }
    };
  }, [executions]);

  const fetchExecutions = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        page: currentPage.toString(),
        page_size: pageSize.toString(),
      });

      if (searchText) {
        params.append('playbook_name', searchText);
      }
      if (statusFilter) {
        params.append('status_filter', statusFilter);
      }
      if (dateRange) {
        params.append('date_from', dateRange[0].toISOString());
        params.append('date_to', dateRange[1].toISOString());
      }

      const response = await fetch(`/api/executions?${params}`);
      if (response.ok) {
        const data = await response.json();
        setExecutions(data.executions || []);
        setTotal(data.total || 0);
      } else {
        message.error('Failed to fetch executions');
      }
    } catch (error) {
      message.error('Error fetching executions');
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      setStatsLoading(true);
      const response = await fetch('/api/executions/stats');
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      } else {
        message.error('Failed to fetch execution stats');
      }
    } catch (error) {
      message.error('Error fetching execution stats');
    } finally {
      setStatsLoading(false);
    }
  };

  const cancelExecution = async (executionId: string) => {
    try {
      const response = await fetch(`/api/executions/${executionId}/cancel`, {
        method: 'POST',
      });

      if (response.ok) {
        message.success('Execution cancelled successfully');
        fetchExecutions();
        fetchStats();
      } else {
        message.error('Failed to cancel execution');
      }
    } catch (error) {
      message.error('Error cancelling execution');
    }
  };

  const deleteExecution = async (executionId: string) => {
    try {
      const response = await fetch(`/api/executions/${executionId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        message.success('Execution deleted successfully');
        fetchExecutions();
        fetchStats();
      } else {
        message.error('Failed to delete execution');
      }
    } catch (error) {
      message.error('Error deleting execution');
    }
  };

  const fetchExecutionLog = async (executionId: string) => {
    try {
      setLogLoading(true);
      const response = await fetch(`/api/executions/${executionId}/log`);
      if (response.ok) {
        const data = await response.json();
        setExecutionLog(data);
      } else {
        message.error('Failed to fetch execution log');
      }
    } catch (error) {
      message.error('Error fetching execution log');
    } finally {
      setLogLoading(false);
    }
  };

  const showExecutionDetail = (execution: Execution) => {
    setSelectedExecution(execution);
    setDetailModalVisible(true);
  };

  const showExecutionLog = async (execution: Execution) => {
    setSelectedExecution(execution);
    setLogModalVisible(true);
    await fetchExecutionLog(execution.execution_id);
    
    // Start real-time log updates for running executions
    if (execution.status === 'running' || execution.status === 'queued') {
      const logInterval = setInterval(async () => {
        await fetchExecutionLog(execution.execution_id);
      }, 3000); // Update logs every 3 seconds
      
      // Store interval for cleanup
      setPollingInterval(logInterval);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'running':
        return 'processing';
      case 'queued':
        return 'warning';
      case 'failed':
        return 'error';
      case 'cancelled':
        return 'default';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleOutlined />;
      case 'running':
        return <LoadingOutlined />;
      case 'queued':
        return <ClockCircleOutlined />;
      case 'failed':
        return <CloseCircleOutlined />;
      case 'cancelled':
        return <StopOutlined />;
      default:
        return <ExclamationCircleOutlined />;
    }
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return '-';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
      return `${hours}h ${minutes}m ${secs}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`;
    } else {
      return `${secs}s`;
    }
  };

  const formatDate = (dateString: string) => {
    return dayjs(dateString).format('YYYY-MM-DD HH:mm:ss');
  };

  const columns = [
    {
      title: 'Execution ID',
      dataIndex: 'execution_id',
      key: 'execution_id',
      render: (text: string) => (
        <Text code style={{ fontSize: '12px' }}>
          {text.substring(0, 12)}...
        </Text>
      ),
      width: 120,
    },
    {
      title: 'Playbook',
      dataIndex: 'playbook_name',
      key: 'playbook_name',
      render: (text: string) => (
        <div>
          <FileTextOutlined style={{ marginRight: '8px', color: '#1890ff' }} />
          <Text strong>{text}</Text>
        </div>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string, record: Execution) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Badge
            status={getStatusColor(status) as any}
            text={
              <Tag color={getStatusColor(status)} icon={getStatusIcon(status)}>
                {status.toUpperCase()}
              </Tag>
            }
          />
          {realTimeExecutions.has(record.execution_id) && (
            <Badge status="processing" text="Live" />
          )}
        </div>
      ),
      width: 140,
    },
    {
      title: 'Progress',
      key: 'progress',
      render: (_, record: Execution) => {
        const total = record.total_jobs;
        const completed = record.completed_jobs;
        const failed = record.failed_jobs;
        const percentage = total > 0 ? Math.round((completed / total) * 100) : 0;
        
        return (
          <div>
            <Progress
              percent={percentage}
              status={record.status === 'failed' ? 'exception' : 'active'}
              format={() => `${completed}/${total} jobs`}
            />
            {failed > 0 && (
              <Text type="danger" style={{ fontSize: '12px' }}>
                {failed} failed
              </Text>
            )}
          </div>
        );
      },
      width: 150,
    },
    {
      title: 'Duration',
      key: 'duration',
      render: (_, record: Execution) => {
        if (record.status === 'running' || record.status === 'queued') {
          return <Text type="secondary">Running...</Text>;
        }
        return <Text>{formatDuration(record.duration)}</Text>;
      },
      width: 100,
    },
    {
      title: 'Started',
      dataIndex: 'started_at',
      key: 'started_at',
      render: (date: string) => (
        <div>
          <ClockCircleOutlined style={{ marginRight: '4px' }} />
          {formatDate(date)}
        </div>
      ),
      width: 160,
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record: Execution) => (
        <Space size="small">
          <Tooltip title="View Details">
            <Button
              type="text"
              icon={<EyeOutlined />}
              onClick={() => showExecutionDetail(record)}
            />
          </Tooltip>
          <Tooltip title="View Log">
            <Button
              type="text"
              icon={<FileTextOutlined />}
              onClick={() => showExecutionLog(record)}
            />
          </Tooltip>
          {(record.status === 'queued' || record.status === 'running') && (
            <Tooltip title="Cancel Execution">
              <Popconfirm
                title="Are you sure you want to cancel this execution?"
                onConfirm={() => cancelExecution(record.execution_id)}
                okText="Yes"
                cancelText="No"
              >
                <Button
                  type="text"
                  danger
                  icon={<StopOutlined />}
                />
              </Popconfirm>
            </Tooltip>
          )}
          <Popconfirm
            title="Are you sure you want to delete this execution?"
            onConfirm={() => deleteExecution(record.execution_id)}
            okText="Yes"
            cancelText="No"
          >
            <Tooltip title="Delete Execution">
              <Button
                type="text"
                danger
                icon={<DeleteOutlined />}
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
      width: 120,
    },
  ];

  return (
    <div style={{ padding: '24px', maxWidth: '1400px', margin: '0 auto' }}>
      {/* Header */}
      <Row gutter={[16, 16]} align="middle" style={{ marginBottom: '24px' }}>
        <Col flex="auto">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <div>
              <Title level={2} style={{ margin: 0 }}>
                Playbook Executions
              </Title>
              <Text type="secondary">
                Monitor and manage your playbook execution history
              </Text>
            </div>
          </div>
        </Col>
        <Col>
          <Space>
            <Button
              icon={<ReloadOutlined />}
              onClick={() => {
                fetchExecutions();
                fetchStats();
              }}
            >
              Refresh
            </Button>
          </Space>
        </Col>
      </Row>

      {/* Statistics Cards */}
      {!statsLoading && stats && (
        <Row gutter={16} style={{ marginBottom: '24px' }}>
          <Col span={6}>
            <StatsCard>
              <Statistic
                title="Total Executions"
                value={stats.total_executions}
                prefix={<HistoryOutlined />}
              />
            </StatsCard>
          </Col>
          <Col span={6}>
            <StatsCard>
              <Statistic
                title="Successful"
                value={stats.successful_executions}
                valueStyle={{ color: '#52c41a' }}
                prefix={<CheckCircleOutlined />}
              />
            </StatsCard>
          </Col>
          <Col span={6}>
            <StatsCard>
              <Statistic
                title="Failed"
                value={stats.failed_executions}
                valueStyle={{ color: '#ff4d4f' }}
                prefix={<CloseCircleOutlined />}
              />
            </StatsCard>
          </Col>
          <Col span={6}>
            <StatsCard>
              <Statistic
                title="Running"
                value={stats.running_executions}
                valueStyle={{ color: '#1890ff' }}
                prefix={<LoadingOutlined />}
              />
            </StatsCard>
          </Col>
        </Row>
      )}

      {/* Filters */}
      <StyledCard>
        <Row gutter={16} align="middle" style={{ marginBottom: '16px' }}>
          <Col span={8}>
            <Search
              placeholder="Search by playbook name..."
              allowClear
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              prefix={<SearchOutlined />}
            />
          </Col>
          <Col span={4}>
            <Select
              placeholder="Status"
              allowClear
              value={statusFilter}
              onChange={setStatusFilter}
              style={{ width: '100%' }}
            >
              <Option value="queued">Queued</Option>
              <Option value="running">Running</Option>
              <Option value="completed">Completed</Option>
              <Option value="failed">Failed</Option>
              <Option value="cancelled">Cancelled</Option>
            </Select>
          </Col>
          <Col span={8}>
            <RangePicker
              placeholder={['Start Date', 'End Date']}
              value={dateRange}
              onChange={(dates) => setDateRange(dates as any)}
              style={{ width: '100%' }}
            />
          </Col>
          <Col span={4}>
            <Button
              icon={<FilterOutlined />}
              onClick={() => {
                setSearchText('');
                setStatusFilter('');
                setDateRange(null);
              }}
            >
              Clear
            </Button>
          </Col>
        </Row>

        {/* Welcome Message */}
        {welcomeMessage && (
          <Alert
            message="Playbook Execution Started"
            description={welcomeMessage}
            type="success"
            showIcon
            closable
            onClose={() => setWelcomeMessage(null)}
            style={{ marginBottom: 16 }}
          />
        )}

        {/* Executions Table */}
        <StyledTable>
          <Table
            columns={columns}
            dataSource={executions}
            rowKey="execution_id"
            loading={loading}
            rowClassName={(record) => 
              record.execution_id === highlightExecutionId ? 'highlighted-row' : ''
            }
            pagination={{
              current: currentPage,
              pageSize: pageSize,
              total: total,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} executions`,
              onChange: (page, size) => {
                setCurrentPage(page);
                setPageSize(size || 20);
              },
            }}
            locale={{
              emptyText: (
                <Empty
                  image={Empty.PRESENTED_IMAGE_SIMPLE}
                  description="No executions found"
                />
              ),
            }}
          />
        </StyledTable>
      </StyledCard>

      {/* Enhanced Execution Detail Modal */}
      <Modal
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <FileTextOutlined style={{ color: '#1890ff' }} />
            <span>Execution Details: {selectedExecution?.playbook_name}</span>
            {realTimeExecutions.has(selectedExecution?.execution_id || '') && (
              <Badge status="processing" text="Live" />
            )}
          </div>
        }
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={null}
        width={1000}
        style={{ top: 20 }}
      >
        {selectedExecution && (
          <div>
            {/* Execution Overview */}
            <Card size="small" style={{ marginBottom: '16px' }}>
              <Row gutter={16}>
                <Col span={6}>
                  <Statistic
                    title="Status"
                    value={selectedExecution.status.toUpperCase()}
                    valueStyle={{ 
                      color: getStatusColor(selectedExecution.status) === 'success' ? '#52c41a' :
                              getStatusColor(selectedExecution.status) === 'error' ? '#ff4d4f' :
                              getStatusColor(selectedExecution.status) === 'processing' ? '#1890ff' : '#666'
                    }}
                    prefix={getStatusIcon(selectedExecution.status)}
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="Duration"
                    value={formatDuration(selectedExecution.duration)}
                    prefix={<ClockCircleOutlined />}
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="Jobs Progress"
                    value={`${selectedExecution.completed_jobs}/${selectedExecution.total_jobs}`}
                    suffix={selectedExecution.failed_jobs > 0 ? ` (${selectedExecution.failed_jobs} failed)` : ''}
                    valueStyle={{ color: selectedExecution.failed_jobs > 0 ? '#ff4d4f' : '#52c41a' }}
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="Execution ID"
                    value={selectedExecution.execution_id.substring(0, 12) + '...'}
                    valueStyle={{ fontSize: '14px' }}
                  />
                </Col>
              </Row>
            </Card>

            {/* Progress Bar */}
            <Card size="small" style={{ marginBottom: '16px' }}>
              <div style={{ marginBottom: '8px' }}>
                <Text strong>Overall Progress</Text>
              </div>
              <Progress
                percent={selectedExecution.total_jobs > 0 ? Math.round((selectedExecution.completed_jobs / selectedExecution.total_jobs) * 100) : 0}
                status={selectedExecution.status === 'failed' ? 'exception' : 'active'}
                strokeColor={{
                  '0%': '#108ee9',
                  '100%': '#87d068',
                }}
              />
              <div style={{ marginTop: '8px', display: 'flex', justifyContent: 'space-between' }}>
                <Text type="secondary">Started: {formatDate(selectedExecution.started_at)}</Text>
                {selectedExecution.completed_at && (
                  <Text type="secondary">Completed: {formatDate(selectedExecution.completed_at)}</Text>
                )}
              </div>
            </Card>

            {/* Error Message */}
            {selectedExecution.error_message && (
              <Alert
                message="Execution Error"
                description={selectedExecution.error_message}
                type="error"
                showIcon
                style={{ marginBottom: '16px' }}
              />
            )}

            {/* Enhanced Job Executions */}
            {selectedExecution.job_executions && selectedExecution.job_executions.length > 0 && (
              <div>
                <Title level={4} style={{ marginBottom: '16px' }}>
                  <HistoryOutlined style={{ marginRight: '8px' }} />
                  Job Executions
                </Title>
                <Collapse defaultActiveKey={selectedExecution.job_executions.map(job => job.job_id)}>
                  {selectedExecution.job_executions.map((job) => (
                    <Panel
                      key={job.job_id}
                      header={
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <Badge
                              status={getStatusColor(job.status) as any}
                              dot
                            />
                            <Text strong>{job.job_name}</Text>
                            <Tag color="blue">{job.job_id}</Tag>
                          </div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                            <Text type="secondary" style={{ fontSize: '12px' }}>
                              {formatDuration(job.duration)}
                            </Text>
                            <Badge
                              status={getStatusColor(job.status) as any}
                              text={job.status.toUpperCase()}
                            />
                          </div>
                        </div>
                      }
                    >
                      {/* Job Details */}
                      <Row gutter={16} style={{ marginBottom: '16px' }}>
                        <Col span={12}>
                          <Card size="small" title="Job Information">
                            <Descriptions column={1} size="small">
                              <Descriptions.Item label="Job ID">
                                <Text code>{job.job_id}</Text>
                              </Descriptions.Item>
                              <Descriptions.Item label="Started At">
                                {job.started_at ? formatDate(job.started_at) : '-'}
                              </Descriptions.Item>
                              <Descriptions.Item label="Completed At">
                                {job.completed_at ? formatDate(job.completed_at) : '-'}
                              </Descriptions.Item>
                              <Descriptions.Item label="Duration">
                                {formatDuration(job.duration)}
                              </Descriptions.Item>
                            </Descriptions>
                          </Card>
                        </Col>
                        <Col span={12}>
                          <Card size="small" title="Target Information">
                            <Descriptions column={1} size="small">
                              <Descriptions.Item label="Target Hosts">
                                {job.target_hosts && job.target_hosts.length > 0 ? (
                                  <div>
                                    {job.target_hosts.map((host, index) => (
                                      <Tag key={index} color="green" style={{ marginBottom: '4px' }}>
                                        {host}
                                      </Tag>
                                    ))}
                                  </div>
                                ) : '-'}
                              </Descriptions.Item>
                              <Descriptions.Item label="Host Progress">
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                  <Text type="success">{job.completed_hosts} completed</Text>
                                  {job.failed_hosts > 0 && (
                                    <Text type="danger">{job.failed_hosts} failed</Text>
                                  )}
                                </div>
                              </Descriptions.Item>
                            </Descriptions>
                          </Card>
                        </Col>
                      </Row>

                      {/* Job Progress */}
                      <Card size="small" title="Job Progress" style={{ marginBottom: '16px' }}>
                        <Progress
                          percent={job.target_hosts && job.target_hosts.length > 0 ? 
                            Math.round(((job.completed_hosts + job.failed_hosts) / job.target_hosts.length) * 100) : 0}
                          status={job.status === 'failed' ? 'exception' : 'active'}
                          format={() => `${job.completed_hosts + job.failed_hosts}/${job.target_hosts?.length || 0} hosts`}
                        />
                      </Card>

                      {/* Task Executions */}
                      {job.task_executions && job.task_executions.length > 0 && (
                        <Card size="small" title="Task Executions">
                          <Table
                            dataSource={job.task_executions}
                            rowKey="id"
                            size="small"
                            pagination={false}
                            columns={[
                              {
                                title: 'Task',
                                dataIndex: 'task_name',
                                key: 'task_name',
                                render: (text: string) => <Text strong>{text}</Text>,
                              },
                              {
                                title: 'Module',
                                dataIndex: 'module',
                                key: 'module',
                                render: (text: string) => <Tag color="blue">{text}</Tag>,
                              },
                              {
                                title: 'Host',
                                dataIndex: 'host',
                                key: 'host',
                                render: (text: string) => <Tag color="green">{text}</Tag>,
                              },
                              {
                                title: 'Status',
                                dataIndex: 'status',
                                key: 'status',
                                render: (status: string) => (
                                  <Badge
                                    status={getStatusColor(status) as any}
                                    text={status.toUpperCase()}
                                  />
                                ),
                              },
                              {
                                title: 'Duration',
                                key: 'duration',
                                render: (_, record: TaskExecution) => formatDuration(record.duration),
                              },
                              {
                                title: 'Return Code',
                                dataIndex: 'return_code',
                                key: 'return_code',
                                render: (code: number) => code !== undefined ? (
                                  <Tag color={code === 0 ? 'success' : 'error'}>{code}</Tag>
                                ) : '-',
                              },
                            ]}
                          />
                        </Card>
                      )}

                      {/* Job Error */}
                      {job.error_message && (
                        <Alert
                          message="Job Error"
                          description={job.error_message}
                          type="error"
                          showIcon
                          style={{ marginTop: '16px' }}
                        />
                      )}
                    </Panel>
                  ))}
                </Collapse>
              </div>
            )}
          </div>
        )}
      </Modal>

      {/* Enhanced Execution Log Modal */}
      <Modal
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <FileTextOutlined style={{ color: '#1890ff' }} />
            <span>Execution Log: {selectedExecution?.playbook_name}</span>
            {realTimeExecutions.has(selectedExecution?.execution_id || '') && (
              <Badge status="processing" text="Live" />
            )}
          </div>
        }
        open={logModalVisible}
        onCancel={() => {
          setLogModalVisible(false);
          // Clear polling interval when modal is closed
          if (pollingInterval) {
            clearInterval(pollingInterval);
            setPollingInterval(null);
          }
        }}
        footer={null}
        width={1200}
        style={{ top: 20 }}
      >
        {logLoading ? (
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <Spin size="large" />
            <div style={{ marginTop: '16px' }}>Loading execution log...</div>
          </div>
        ) : executionLog ? (
          <Tabs defaultActiveKey="1">
            <TabPane tab="Overview" key="1">
              <Descriptions column={2} bordered>
                <Descriptions.Item label="Execution ID">
                  <Text code>{executionLog.execution.id}</Text>
                </Descriptions.Item>
                <Descriptions.Item label="Status">
                  <Badge
                    status={getStatusColor(executionLog.execution.status) as any}
                    text={executionLog.execution.status.toUpperCase()}
                  />
                </Descriptions.Item>
                <Descriptions.Item label="Started At">
                  {formatDate(executionLog.execution.started_at)}
                </Descriptions.Item>
                <Descriptions.Item label="Completed At">
                  {executionLog.execution.completed_at ? formatDate(executionLog.execution.completed_at) : '-'}
                </Descriptions.Item>
                <Descriptions.Item label="Duration">
                  {formatDuration(executionLog.execution.duration)}
                </Descriptions.Item>
              </Descriptions>
            </TabPane>
            <TabPane tab="Jobs" key="2">
              <Timeline>
                {executionLog.jobs.map((job: any) => (
                  <Timeline.Item
                    key={job.id}
                    color={getStatusColor(job.status)}
                    dot={getStatusIcon(job.status)}
                  >
                    <div>
                      <Text strong>{job.name}</Text>
                      <br />
                      <Text type="secondary">ID: {job.id}</Text>
                      <br />
                      <Text>Status: {job.status}</Text>
                      {job.duration && (
                        <>
                          <br />
                          <Text>Duration: {formatDuration(job.duration)}</Text>
                        </>
                      )}
                      {job.error_message && (
                        <>
                          <br />
                          <Text type="danger">Error: {job.error_message}</Text>
                        </>
                      )}
                    </div>
                  </Timeline.Item>
                ))}
              </Timeline>
            </TabPane>
            <TabPane tab="Tasks" key="3">
              <div style={{ marginBottom: '16px' }}>
                <Text strong>Task Execution Details</Text>
                <Text type="secondary" style={{ marginLeft: '8px' }}>
                  Showing {executionLog.tasks.length} tasks
                </Text>
              </div>
              <Collapse defaultActiveKey={executionLog.tasks.map((task: any, index: number) => index)}>
                {executionLog.tasks.map((task: any, index: number) => (
                  <Panel
                    key={index}
                    header={
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <Badge
                            status={getStatusColor(task.status) as any}
                            dot
                          />
                          <Text strong>{task.task_name}</Text>
                          <Tag color="blue">{task.module}</Tag>
                          <Tag color="green">{task.host}</Tag>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                          <Text type="secondary" style={{ fontSize: '12px' }}>
                            {formatDuration(task.duration)}
                          </Text>
                          {task.return_code !== undefined && (
                            <Tag color={task.return_code === 0 ? 'success' : 'error'}>
                              Exit: {task.return_code}
                            </Tag>
                          )}
                          <Badge
                            status={getStatusColor(task.status) as any}
                            text={task.status.toUpperCase()}
                          />
                        </div>
                      </div>
                    }
                  >
                    <Row gutter={16}>
                      <Col span={12}>
                        <Card size="small" title="Task Information">
                          <Descriptions column={1} size="small">
                            <Descriptions.Item label="Task Name">
                              <Text strong>{task.task_name}</Text>
                            </Descriptions.Item>
                            <Descriptions.Item label="Module">
                              <Tag color="blue">{task.module}</Tag>
                            </Descriptions.Item>
                            <Descriptions.Item label="Host">
                              <Tag color="green">{task.host}</Tag>
                            </Descriptions.Item>
                            <Descriptions.Item label="Status">
                              <Badge
                                status={getStatusColor(task.status) as any}
                                text={task.status.toUpperCase()}
                              />
                            </Descriptions.Item>
                            <Descriptions.Item label="Started At">
                              {task.started_at ? formatDate(task.started_at) : '-'}
                            </Descriptions.Item>
                            <Descriptions.Item label="Completed At">
                              {task.completed_at ? formatDate(task.completed_at) : '-'}
                            </Descriptions.Item>
                            <Descriptions.Item label="Duration">
                              {formatDuration(task.duration)}
                            </Descriptions.Item>
                            <Descriptions.Item label="Return Code">
                              {task.return_code !== undefined ? (
                                <Tag color={task.return_code === 0 ? 'success' : 'error'}>
                                  {task.return_code}
                                </Tag>
                              ) : '-'}
                            </Descriptions.Item>
                          </Descriptions>
                        </Card>
                      </Col>
                      <Col span={12}>
                        <Card size="small" title="Task Output">
                          {task.stdout && (
                            <div style={{ marginBottom: '16px' }}>
                              <Text strong style={{ color: '#52c41a' }}>STDOUT:</Text>
                              <pre style={{
                                backgroundColor: token.colorBgContainer,
                                color: token.colorText,
                                padding: '8px',
                                borderRadius: '4px',
                                fontSize: '12px',
                                maxHeight: '200px',
                                overflow: 'auto',
                                marginTop: '4px',
                                border: `1px solid ${token.colorBorderSecondary}`
                              }}>
                                {task.stdout}
                              </pre>
                            </div>
                          )}
                          {task.stderr && (
                            <div>
                              <Text strong style={{ color: '#ff4d4f' }}>STDERR:</Text>
                              <pre style={{
                                backgroundColor: token.colorErrorBg,
                                color: token.colorErrorText,
                                padding: '8px',
                                borderRadius: '4px',
                                fontSize: '12px',
                                maxHeight: '200px',
                                overflow: 'auto',
                                marginTop: '4px',
                                border: `1px solid ${token.colorErrorBorder}`
                              }}>
                                {task.stderr}
                              </pre>
                            </div>
                          )}
                          {!task.stdout && !task.stderr && (
                            <Text type="secondary">No output available</Text>
                          )}
                        </Card>
                      </Col>
                    </Row>
                    
                    {task.error_message && (
                      <Alert
                        message="Task Error"
                        description={task.error_message}
                        type="error"
                        showIcon
                        style={{ marginTop: '16px' }}
                      />
                    )}
                  </Panel>
                ))}
              </Collapse>
            </TabPane>
          </Tabs>
        ) : (
          <Empty description="No log data available" />
        )}
      </Modal>
    </div>
  );
};

export default Executions; 