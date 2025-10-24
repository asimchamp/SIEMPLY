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
  message,
  notification,
  theme
} from 'antd';
import { 
  HistoryOutlined, 
  FileSearchOutlined, 
  ExclamationCircleOutlined,
  ReloadOutlined,
  FilterOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  EyeOutlined
} from '@ant-design/icons';
import { hostService, jobService, Host, Job } from '../services/api';
import type { ColumnType } from 'antd/es/table';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import { useSearchParams } from 'react-router-dom';

// Extend dayjs with plugins
dayjs.extend(relativeTime);

const { Title, Text } = Typography;
const { Panel } = Collapse;
const { Option } = Select;
const { RangePicker } = DatePicker;

const JobHistory: React.FC = () => {
  const { token } = theme.useToken();
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
  const [searchParams, setSearchParams] = useSearchParams();
  const [pollingInterval, setPollingInterval] = useState<NodeJS.Timeout | null>(null);
  const [previousJobs, setPreviousJobs] = useState<Job[]>([]);
  const [liveLogsVisible, setLiveLogsVisible] = useState<boolean>(false);
  const [liveLogsJob, setLiveLogsJob] = useState<Job | null>(null);
  const [liveLogs, setLiveLogs] = useState<string>('');
  const [liveLogsLoading, setLiveLogsLoading] = useState<boolean>(false);
  const [liveLogsPollingInterval, setLiveLogsPollingInterval] = useState<NodeJS.Timeout | null>(null);

  // Load jobs on component mount
  useEffect(() => {
    fetchData();
  }, []);

  // Handle URL parameters for job highlighting
  useEffect(() => {
    const jobId = searchParams.get('job_id');
    if (jobId && jobs.length > 0) {
      const job = jobs.find(j => j.job_id === jobId);
      if (job) {
        setSelectedJob(job);
        setDrawerVisible(true);
        // Clear the URL parameter after opening the drawer
        setSearchParams({});
      }
    }
  }, [jobs, searchParams, setSearchParams]);

  // Set up polling for running jobs and track status changes
  useEffect(() => {
    const runningJobs = jobs.filter(job => 
      job.status === 'running' || job.status === 'pending'
    );

    if (runningJobs.length > 0) {
      // Poll every 5 seconds for running jobs
      const interval = setInterval(() => {
        fetchData();
      }, 5000);
      setPollingInterval(interval);

      return () => {
        if (interval) {
          clearInterval(interval);
        }
      };
    } else {
      // Clear polling if no running jobs
      if (pollingInterval) {
        clearInterval(pollingInterval);
        setPollingInterval(null);
      }
    }
  }, [jobs]);

  // Check for job status changes and show notifications
  useEffect(() => {
    if (previousJobs.length > 0 && jobs.length > 0) {
      jobs.forEach(currentJob => {
        const previousJob = previousJobs.find(pj => pj.id === currentJob.id);
        if (previousJob && previousJob.status !== currentJob.status) {
          // Job status changed, show notification
          const host = hosts.get(currentJob.host_id);
          const hostname = host ? host.hostname : `Host ${currentJob.host_id}`;
          
          if (currentJob.status === 'completed') {
            notification.success({
              message: 'Job Completed',
              description: `${currentJob.job_type.replace(/_/g, ' ')} on ${hostname} has completed successfully.`,
              duration: 5,
              icon: <CheckCircleOutlined style={{ color: '#52c41a' }} />
            });
          } else if (currentJob.status === 'failed') {
            notification.error({
              message: 'Job Failed',
              description: `${currentJob.job_type.replace(/_/g, ' ')} on ${hostname} has failed.`,
              duration: 8,
              icon: <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />
            });
          }
        }
      });
    }
    
    // Update previous jobs for next comparison
    setPreviousJobs(jobs);
  }, [jobs, hosts]);

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
  const getStatusColor = (status: string, job?: Job) => {
    // Check if job was skipped (completed but with skipped result)
    if (status.toLowerCase() === 'completed' && job?.result?.actual_status === 'skipped') {
      return 'cyan'; // Different color for skipped jobs
    }
    
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

  // Helper function to get status display text
  const getStatusText = (status: string, job?: Job) => {
    // Check if job was skipped (completed but with skipped result)
    if (status.toLowerCase() === 'completed' && job?.result?.actual_status === 'skipped') {
      return 'SKIPPED';
    }
    
    return status.toUpperCase();
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
      render: (text: string) => {
        const jobTypeMap: Record<string, string> = {
          'splunk_cm_install': 'Install Splunk CM',
          'splunk_cm_upgrade': 'Upgrade Splunk CM',
          'splunk_deployer_install': 'Install Splunk Deployer',
          'splunk_deployer_upgrade': 'Upgrade Splunk Deployer',
          'splunk_license_master_install': 'Install Splunk License Master',
          'splunk_license_master_upgrade': 'Upgrade Splunk License Master',
          'splunk_monitoring_console_install': 'Install Splunk Monitoring Console',
          'splunk_monitoring_console_upgrade': 'Upgrade Splunk Monitoring Console',
          'splunk_deployment_server_install': 'Install Splunk Deployment Server',
          'splunk_deployment_server_upgrade': 'Upgrade Splunk Deployment Server',
          'splunk_search_head_install': 'Install Splunk Search Head',
          'splunk_search_head_upgrade': 'Upgrade Splunk Search Head',
          'splunk_indexer_install': 'Install Splunk Indexer',
          'splunk_indexer_upgrade': 'Upgrade Splunk Indexer',
          'splunk_hf_install': 'Install Splunk HF',
          'splunk_hf_upgrade': 'Upgrade Splunk HF',
          'splunk_uf_install': 'Install Splunk UF',
          'splunk_uf_upgrade': 'Upgrade Splunk UF',
          'splunk_enterprise_install': 'Install Splunk Enterprise',
          'splunk_enterprise_upgrade': 'Upgrade Splunk Enterprise',
          'cribl_leader_install': 'Install Cribl Leader',
          'cribl_worker_install': 'Install Cribl Worker',
          'custom_command': 'Custom Command',
          'bash_script': 'Bash Script'
        };
        return jobTypeMap[text] || text.replace(/_/g, ' ').toUpperCase();
      },
      filters: [
        { text: 'Install Splunk CM', value: 'splunk_cm_install' },
        { text: 'Install Splunk Deployer', value: 'splunk_deployer_install' },
        { text: 'Install Splunk License Master', value: 'splunk_license_master_install' },
        { text: 'Install Splunk Monitoring Console', value: 'splunk_monitoring_console_install' },
        { text: 'Install Splunk Deployment Server', value: 'splunk_deployment_server_install' },
        { text: 'Install Splunk Search Head', value: 'splunk_search_head_install' },
        { text: 'Install Splunk Indexer', value: 'splunk_indexer_install' },
        { text: 'Install Splunk HF', value: 'splunk_hf_install' },
        { text: 'Install Splunk UF', value: 'splunk_uf_install' },
        { text: 'Install Splunk Enterprise', value: 'splunk_enterprise_install' },
        { text: 'Install Cribl Leader', value: 'cribl_leader_install' },
        { text: 'Install Cribl Worker', value: 'cribl_worker_install' },
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
      render: (status: string, record: Job) => (
        <Tag color={getStatusColor(status, record)}>
          {getStatusText(status, record)}
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
          {(record.job_type.includes('splunk') && record.job_type.includes('install')) && (
            <Tooltip title="View Live Logs">
              <Button 
                size="small"
                icon={<EyeOutlined />}
                onClick={() => showLiveLogs(record)}
              />
            </Tooltip>
          )}
          {(record.status === 'running' || record.status === 'pending') && (
            <Button
              size="small"
              danger
              onClick={() => cancelJob(record.job_id)}
            >
              Cancel
            </Button>
          )}
        </Space>
      ),
    },
  ];

  // Cancel job
  const cancelJob = async (uniqueJobId: string) => {
    try {
      await jobService.cancelJobByUniqueId(uniqueJobId);
      message.success('Job cancelled successfully');
      fetchData();
    } catch (error) {
      console.error('Failed to cancel job:', error);
      message.error('Failed to cancel job');
    }
  };

  // Show live logs
  const showLiveLogs = (job: Job) => {
    setLiveLogsJob(job);
    setLiveLogsVisible(true);
    setLiveLogs('');
    fetchLiveLogs(job.job_id);
  };

  // Fetch live logs
  const fetchLiveLogs = async (jobId: string) => {
    try {
      setLiveLogsLoading(true);
      // First try to get logs from the job's stdout field
      const jobData = jobs.find(j => j.job_id === jobId);
      if (jobData && jobData.stdout) {
        setLiveLogs(jobData.stdout);
      } else {
        // Fallback to live logs endpoint for running jobs
        const response = await jobService.getLiveLogs(jobId);
        setLiveLogs(response.logs || '');
        if (response.error) {
          console.warn(`Live logs unavailable: ${response.error}`);
        }
      }
    } catch (error) {
      console.error('Failed to fetch live logs:', error);
      // For completed jobs, try to show the job stdout as fallback
      const jobData = jobs.find(j => j.job_id === jobId);
      if (jobData && jobData.stdout) {
        setLiveLogs(jobData.stdout);
      } else {
        message.error('Failed to fetch logs');
      }
    } finally {
      setLiveLogsLoading(false);
    }
  };

  // Close live logs modal
  const closeLiveLogs = () => {
    setLiveLogsVisible(false);
    setLiveLogsJob(null);
    setLiveLogs('');
    if (liveLogsPollingInterval) {
      clearInterval(liveLogsPollingInterval);
      setLiveLogsPollingInterval(null);
    }
  };

  // Set up live logs polling
  useEffect(() => {
    if (liveLogsVisible && liveLogsJob) {
      if (liveLogsJob.status === 'running' || liveLogsJob.status === 'pending') {
        // Poll for running jobs
        const interval = setInterval(() => {
          fetchLiveLogs(liveLogsJob.job_id);
        }, 3000); // Poll every 3 seconds
        setLiveLogsPollingInterval(interval);
        
        return () => {
          if (interval) {
            clearInterval(interval);
          }
        };
      } else {
        // For completed jobs, just refresh once to get latest data
        fetchLiveLogs(liveLogsJob.job_id);
      }
    }
  }, [liveLogsVisible, liveLogsJob]);

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
    
    // Define tabs items for the Tabs component
    const tabItems = [
      {
        key: "details",
        label: "Details",
        children: (
          <>
            <Descriptions bordered column={1}>
              <Descriptions.Item label="Job ID">{selectedJob.job_id}</Descriptions.Item>
              <Descriptions.Item label="Type">{selectedJob.job_type.replace(/_/g, ' ')}</Descriptions.Item>
              <Descriptions.Item label="Host">
                {hosts.get(selectedJob.host_id)?.hostname || `Host ID: ${selectedJob.host_id}`}
              </Descriptions.Item>
              <Descriptions.Item label="Status">
                <Tag color={getStatusColor(selectedJob.status, selectedJob)}>
                  {getStatusText(selectedJob.status, selectedJob)}
                </Tag>
                {selectedJob.result?.status_note && (
                  <div style={{ marginTop: 8, fontSize: '12px', color: '#666' }}>
                    {selectedJob.result.status_note}
                  </div>
                )}
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
          </>
        )
      },
      {
        key: "output",
        label: "Output",
        children: (
          <>
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
          </>
        )
      }
    ];
    
    return (
      <div className="job-output">
        <Tabs defaultActiveKey="details" items={tabItems} />
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
        {pollingInterval && (
          <div style={{ marginTop: 8 }}>
            <Tag color="processing" icon={<ClockCircleOutlined />}>
              Auto-refreshing for running jobs
            </Tag>
          </div>
        )}
      </div>

      {/* Filters */}
      <Card style={{ marginBottom: 16 }}>
        <Form layout="horizontal">
          <Row gutter={16}>
            <Col span={6}>
              <Form.Item label="Status">
                <Select
                  placeholder="Filter by status"
                  value={filters.status}
                  onChange={(value) => handleFilterChange('status', value)}
                  allowClear
                >
                  <Option value="pending">Pending</Option>
                  <Option value="running">Running</Option>
                  <Option value="completed">Completed</Option>
                  <Option value="failed">Failed</Option>
                  <Option value="cancelled">Cancelled</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item label="Job Type">
                <Select
                  placeholder="Filter by job type"
                  value={filters.job_type}
                  onChange={(value) => handleFilterChange('job_type', value)}
                  allowClear
                >
                  <Option value="splunk_cm_install">Install Splunk CM</Option>
                  <Option value="splunk_deployer_install">Install Splunk Deployer</Option>
                  <Option value="splunk_license_master_install">Install Splunk License Master</Option>
                  <Option value="splunk_monitoring_console_install">Install Splunk Monitoring Console</Option>
                  <Option value="splunk_deployment_server_install">Install Splunk Deployment Server</Option>
                  <Option value="splunk_search_head_install">Install Splunk Search Head</Option>
                  <Option value="splunk_indexer_install">Install Splunk Indexer</Option>
                  <Option value="splunk_hf_install">Install Splunk HF</Option>
                  <Option value="splunk_uf_install">Install Splunk UF</Option>
                  <Option value="splunk_enterprise_install">Install Splunk Enterprise</Option>
                  <Option value="cribl_leader_install">Install Cribl Leader</Option>
                  <Option value="cribl_worker_install">Install Cribl Worker</Option>
                  <Option value="custom_command">Custom Command</Option>
                  <Option value="bash_script">Bash Script</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item label="Host">
                <Select
                  placeholder="Filter by host"
                  value={filters.host_id}
                  onChange={(value) => handleFilterChange('host_id', value)}
                  allowClear
                  showSearch
                  optionFilterProp="children"
                >
                  {Array.from(hosts.values()).map(host => (
                    <Option key={host.id} value={host.id}>
                      {host.hostname} ({host.ip_address})
                    </Option>
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
            loading={loading}
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
                {getStatusText(selectedJob.status, selectedJob)}
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

      {/* Live Logs Modal */}
      <Drawer
        title={
          <span>
            <EyeOutlined /> Live Logs
            {liveLogsJob && (
              <Tag 
                color={getStatusColor(liveLogsJob.status)}
                style={{ marginLeft: 8 }}
              >
                {getStatusText(liveLogsJob.status, liveLogsJob)}
              </Tag>
            )}
          </span>
        }
        width={800}
        placement="right"
        onClose={closeLiveLogs}
        open={liveLogsVisible}
        extra={
          <Space>
            {liveLogsLoading && <Spin size="small" />}
            <Button 
              size="small" 
              onClick={() => liveLogsJob && fetchLiveLogs(liveLogsJob.job_id)}
              icon={<ReloadOutlined />}
            >
              Refresh
            </Button>
          </Space>
        }
      >
        <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
          {liveLogsJob && (
            <div style={{ marginBottom: 16 }}>
              <Descriptions size="small" column={2}>
                <Descriptions.Item label="Job ID">{liveLogsJob.job_id}</Descriptions.Item>
                <Descriptions.Item label="Type">{liveLogsJob.job_type.replace(/_/g, ' ')}</Descriptions.Item>
                <Descriptions.Item label="Host">
                  {hosts.get(liveLogsJob.host_id)?.hostname || `Host ID: ${liveLogsJob.host_id}`}
                </Descriptions.Item>
                <Descriptions.Item label="Status">
                  <Tag color={getStatusColor(liveLogsJob.status)}>
                    {getStatusText(liveLogsJob.status, liveLogsJob)}
                  </Tag>
                </Descriptions.Item>
              </Descriptions>
            </div>
          )}
          
          <div style={{ flex: 1, overflow: 'hidden' }}>
              <Card 
              title="Runner Logs" 
              size="small"
              style={{ height: '100%' }}
              bodyStyle={{ height: 'calc(100% - 50px)', overflow: 'auto' }}
            >
              {liveLogs ? (
                <div style={{ marginBottom: '16px' }}>
                  <Text strong style={{ color: '#52c41a' }}>STDOUT:</Text>
                  <pre style={{
                    backgroundColor: token.colorBgContainer,
                    color: token.colorText,
                    padding: '8px',
                    borderRadius: '4px',
                    fontSize: '12px',
                    maxHeight: '400px',
                    overflow: 'auto',
                    marginTop: '4px',
                    whiteSpace: 'pre-wrap',
                    wordWrap: 'break-word',
                    fontFamily: 'monospace',
                    border: `1px solid ${token.colorBorderSecondary}`
                  }}>
                    {liveLogs}
                  </pre>
                </div>
              ) : (
                <Text type="secondary">
                  {liveLogsLoading ? 'Loading logs...' : 'No logs available'}
                </Text>
              )}
            </Card>
          </div>
        </div>
      </Drawer>
    </div>
  );
};

export default JobHistory;