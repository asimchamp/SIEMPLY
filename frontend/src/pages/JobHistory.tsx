import { useState, useEffect } from 'react';
import { 
  Card, 
  Typography, 
  Table, 
  Tag, 
  Button, 
  Space, 
  Drawer,
  Spin,
  Alert,
  Descriptions,
  Tabs,
  Collapse,
  Badge,
  DatePicker,
  Select,
  Form,
  Row,
  Col,
  Tooltip,
  message
} from 'antd';
import { 
  HistoryOutlined, 
  FileSearchOutlined, 
  ExclamationCircleOutlined,
  ReloadOutlined,
  FilterOutlined,
  ClockCircleOutlined
} from '@ant-design/icons';
import { hostService, jobService, Host, Job } from '../services/api';
import type { ColumnType } from 'antd/es/table';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';

// Extend dayjs with plugins
dayjs.extend(relativeTime);

const { Title, Text, Paragraph } = Typography;
const { TabPane } = Tabs;
const { Panel } = Collapse;
const { Option } = Select;
const { RangePicker } = DatePicker;

const JobHistory: React.FC = () => {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [hosts, setHosts] = useState<Map<number, Host>>(new Map());
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [drawerVisible, setDrawerVisible] = useState<boolean>(false);
  const [filters, setFilters] = useState({
    status: '',
    job_type: '',
    host_id: null as number | null,
    date_range: null as [dayjs.Dayjs, dayjs.Dayjs] | null
  });

  // Load jobs on component mount
  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      
      // Fetch all jobs
      const jobsData = await jobService.getAllJobs();
      setJobs(jobsData);
      
      // Fetch all hosts to populate host data in jobs
      const hostsData = await hostService.getAllHosts();
      const hostsMap = new Map<number, Host>();
      hostsData.forEach(host => hostsMap.set(host.id, host));
      setHosts(hostsMap);
      
      setError(null);
    } catch (err) {
      console.error('Error fetching job data:', err);
      setError('Failed to fetch job data. Please check your connection to the API server.');
    } finally {
      setLoading(false);
    }
  };

  // Apply filters to jobs
  const applyFilters = async () => {
    try {
      setLoading(true);
      
      const filterParams = {
        ...(filters.status && { status: filters.status }),
        ...(filters.job_type && { job_type: filters.job_type }),
        ...(filters.host_id && { host_id: filters.host_id })
      };
      
      // Apply date range filter on client side after fetching
      let jobsData = await jobService.getJobs(filterParams);
      
      if (filters.date_range) {
        const [startDate, endDate] = filters.date_range;
        
        jobsData = jobsData.filter(job => {
          const jobDate = dayjs(job.created_at);
          return jobDate.isAfter(startDate) && jobDate.isBefore(endDate);
        });
      }
      
      setJobs(jobsData);
    } catch (error) {
      console.error('Error applying filters:', error);
      setError('Failed to apply filters');
    } finally {
      setLoading(false);
    }
  };

  // Reset all filters
  const resetFilters = () => {
    setFilters({
      status: '',
      job_type: '',
      host_id: null,
      date_range: null
    });
    fetchData();
  };

  // Helper function to get status color
  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
      case 'success':
        return 'success';
      case 'running':
      case 'in_progress':
        return 'processing';
      case 'failed':
      case 'error':
        return 'error';
      case 'cancelled':
        return 'warning';
      default:
        return 'default';
    }
  };

  // Show job details in drawer
  const showJobDetails = (job: Job) => {
    setSelectedJob(job);
    setDrawerVisible(true);
  };

  // Close job details drawer
  const closeDrawer = () => {
    setDrawerVisible(false);
  };

  // Table columns
  const columns: ColumnType<Job>[] = [
    {
      title: 'Job ID',
      dataIndex: 'job_id',
      key: 'job_id',
      render: (text: string) => <Text code>{text}</Text>,
    },
    {
      title: 'Type',
      dataIndex: 'job_type',
      key: 'job_type',
      render: (text: string) => text.replace(/_/g, ' ').toUpperCase(),
      filters: [
        { text: 'Install Splunk UF', value: 'install_splunk_uf' },
        { text: 'Install Splunk Enterprise', value: 'install_splunk_enterprise' },
        { text: 'Install Cribl Leader', value: 'install_cribl_leader' },
        { text: 'Install Cribl Worker', value: 'install_cribl_worker' },
      ],
      onFilter: (value: any, record: Job) => record.job_type === value,
    },
    {
      title: 'Host',
      dataIndex: 'host_id',
      key: 'host_id',
      render: (host_id: number) => {
        const host = hosts.get(host_id);
        return host ? host.hostname : `Host ID: ${host_id}`;
      },
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={getStatusColor(status)}>
          {status.toUpperCase()}
        </Tag>
      ),
      filters: [
        { text: 'Completed', value: 'completed' },
        { text: 'Running', value: 'running' },
        { text: 'Failed', value: 'failed' },
        { text: 'Cancelled', value: 'cancelled' },
        { text: 'Pending', value: 'pending' },
      ],
      onFilter: (value: any, record: Job) => record.status === value,
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => (
        <Tooltip title={new Date(date).toLocaleString()}>
          {dayjs(date).fromNow()}
        </Tooltip>
      ),
      sorter: (a: Job, b: Job) => 
        new Date(a.created_at).getTime() - new Date(b.created_at).getTime(),
      defaultSortOrder: 'descend',
    },
    {
      title: 'Duration',
      key: 'duration',
      render: (_, record: Job) => {
        if (!record.started_at) return <Text type="secondary">Not started</Text>;
        
        const start = new Date(record.started_at).getTime();
        const end = record.completed_at
          ? new Date(record.completed_at).getTime()
          : new Date().getTime();
        
        const durationMs = end - start;
        const seconds = Math.floor(durationMs / 1000);
        
        if (seconds < 60) return `${seconds} sec`;
        if (seconds < 3600) return `${Math.floor(seconds / 60)} min ${seconds % 60} sec`;
        return `${Math.floor(seconds / 3600)} hr ${Math.floor((seconds % 3600) / 60)} min`;
      },
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: Job) => (
        <Space size="small">
          <Button 
            size="small"
            icon={<FileSearchOutlined />}
            onClick={() => showJobDetails(record)}
          >
            Details
          </Button>
          {(record.status === 'running' || record.status === 'pending') && (
            <Button
              size="small"
              danger
              onClick={() => cancelJob(record.id)}
            >
              Cancel
            </Button>
          )}
        </Space>
      ),
    },
  ];

  // Cancel job
  const cancelJob = async (jobId: number) => {
    try {
      await jobService.cancelJob(jobId);
      message.success('Job cancelled successfully');
      fetchData();
    } catch (error) {
      console.error('Failed to cancel job:', error);
      message.error('Failed to cancel job');
    }
  };

  // Handle filter changes
  const handleFilterChange = (key: string, value: any) => {
    setFilters({
      ...filters,
      [key]: value
    });
  };

  // Job output content for drawer
  const jobOutputContent = () => {
    if (!selectedJob) return null;
    
    return (
      <div className="job-output">
        <Tabs defaultActiveKey="details">
          <TabPane tab="Details" key="details">
            <Descriptions bordered column={1}>
              <Descriptions.Item label="Job ID">{selectedJob.job_id}</Descriptions.Item>
              <Descriptions.Item label="Type">{selectedJob.job_type.replace(/_/g, ' ')}</Descriptions.Item>
              <Descriptions.Item label="Host">
                {hosts.get(selectedJob.host_id)?.hostname || `Host ID: ${selectedJob.host_id}`}
              </Descriptions.Item>
              <Descriptions.Item label="Status">
                <Tag color={getStatusColor(selectedJob.status)}>{selectedJob.status.toUpperCase()}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Dry Run">
                {selectedJob.is_dry_run ? 'Yes' : 'No'}
              </Descriptions.Item>
              <Descriptions.Item label="Created">
                {new Date(selectedJob.created_at).toLocaleString()}
              </Descriptions.Item>
              {selectedJob.started_at && (
                <Descriptions.Item label="Started">
                  {new Date(selectedJob.started_at).toLocaleString()}
                </Descriptions.Item>
              )}
              {selectedJob.completed_at && (
                <Descriptions.Item label="Completed">
                  {new Date(selectedJob.completed_at).toLocaleString()}
                </Descriptions.Item>
              )}
              {selectedJob.return_code !== undefined && (
                <Descriptions.Item label="Return Code">
                  <Tag color={selectedJob.return_code === 0 ? 'green' : 'red'}>
                    {selectedJob.return_code}
                  </Tag>
                </Descriptions.Item>
              )}
            </Descriptions>
            
            {selectedJob.parameters && (
              <Collapse style={{ marginTop: 16 }}>
                <Panel header="Parameters" key="1">
                  <pre>{JSON.stringify(selectedJob.parameters, null, 2)}</pre>
                </Panel>
              </Collapse>
            )}
          </TabPane>
          
          <TabPane tab="Output" key="output">
            <Collapse defaultActiveKey={['stdout']} style={{ marginBottom: 16 }}>
              <Panel 
                header={
                  <span>
                    <Badge status="success" /> Standard Output
                  </span>
                } 
                key="stdout"
              >
                <pre style={{ maxHeight: 400, overflow: 'auto' }}>
                  {selectedJob.stdout || 'No standard output available'}
                </pre>
              </Panel>
              <Panel 
                header={
                  <span>
                    <Badge status="error" /> Standard Error
                  </span>
                } 
                key="stderr"
              >
                <pre style={{ maxHeight: 400, overflow: 'auto' }}>
                  {selectedJob.stderr || 'No standard error output available'}
                </pre>
              </Panel>
            </Collapse>
            
            {selectedJob.result && (
              <Collapse>
                <Panel header="Result" key="result">
                  <pre>{JSON.stringify(selectedJob.result, null, 2)}</pre>
                </Panel>
              </Collapse>
            )}
          </TabPane>
        </Tabs>
      </div>
    );
  };

  if (loading && jobs.length === 0) {
    return <div style={{ textAlign: 'center', padding: 50 }}><Spin size="large" /></div>;
  }

  if (error && jobs.length === 0) {
    return <Alert message="Error" description={error} type="error" showIcon />;
  }

  return (
    <div className="job-history-container">
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>
          <HistoryOutlined /> Job History
        </Title>
        <Text>View history of jobs and their results</Text>
      </div>

      {/* Filters */}
      <Card style={{ marginBottom: 16 }}>
        <Form layout="horizontal">
          <Row gutter={16}>
            <Col span={6}>
              <Form.Item label="Status">
                <Select
                  placeholder="Filter by status"
                  value={filters.status || undefined}
                  onChange={(value) => handleFilterChange('status', value)}
                  allowClear
                  style={{ width: '100%' }}
                >
                  <Option value="completed">Completed</Option>
                  <Option value="running">Running</Option>
                  <Option value="failed">Failed</Option>
                  <Option value="cancelled">Cancelled</Option>
                  <Option value="pending">Pending</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item label="Job Type">
                <Select
                  placeholder="Filter by job type"
                  value={filters.job_type || undefined}
                  onChange={(value) => handleFilterChange('job_type', value)}
                  allowClear
                  style={{ width: '100%' }}
                >
                  <Option value="install_splunk_uf">Install Splunk UF</Option>
                  <Option value="install_splunk_enterprise">Install Splunk Enterprise</Option>
                  <Option value="install_cribl_leader">Install Cribl Leader</Option>
                  <Option value="install_cribl_worker">Install Cribl Worker</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item label="Host">
                <Select
                  placeholder="Filter by host"
                  value={filters.host_id || undefined}
                  onChange={(value) => handleFilterChange('host_id', value)}
                  allowClear
                  style={{ width: '100%' }}
                >
                  {Array.from(hosts.values()).map(host => (
                    <Option key={host.id} value={host.id}>{host.hostname}</Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item label="Date Range">
                <RangePicker
                  onChange={(dates) => handleFilterChange('date_range', dates)}
                  value={filters.date_range}
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
          </Row>
          <Row>
            <Col span={24} style={{ textAlign: 'right' }}>
              <Button 
                type="primary"
                icon={<FilterOutlined />}
                onClick={applyFilters}
                style={{ marginRight: 8 }}
              >
                Apply Filters
              </Button>
              <Button
                onClick={resetFilters}
              >
                Reset
              </Button>
            </Col>
          </Row>
        </Form>
      </Card>

      <Card>
        <div style={{ marginBottom: 16, textAlign: 'right' }}>
          <Button 
            icon={<ReloadOutlined />}
            onClick={fetchData}
          >
            Refresh
          </Button>
        </div>

        <Table
          dataSource={jobs}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
        />
      </Card>

      {/* Job Details Drawer */}
      <Drawer
        title={
          <span>
            <FileSearchOutlined /> Job Details
            {selectedJob && (
              <Tag 
                color={getStatusColor(selectedJob.status)}
                style={{ marginLeft: 8 }}
              >
                {selectedJob.status.toUpperCase()}
              </Tag>
            )}
          </span>
        }
        width={700}
        placement="right"
        onClose={closeDrawer}
        open={drawerVisible}
      >
        {jobOutputContent()}
      </Drawer>
    </div>
  );
};

export default JobHistory;