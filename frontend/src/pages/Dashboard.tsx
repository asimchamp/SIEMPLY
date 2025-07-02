import { useState, useEffect } from 'react';
import { Card, Typography, Row, Col, Statistic, Button, Table, Tag, Spin, Alert, Drawer, Descriptions, Tabs, Collapse, Badge, Space, Tooltip } from 'antd';
import { 
  DatabaseOutlined, 
  CheckCircleOutlined, 
  WarningOutlined, 
  HistoryOutlined,
  FileSearchOutlined
} from '@ant-design/icons';
import { Link } from 'react-router-dom';
import { hostService, jobService, Host, Job } from '../services/api';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';

// Extend dayjs with plugins
dayjs.extend(relativeTime);

const { Title, Text } = Typography;
const { Panel } = Collapse;

const Dashboard: React.FC = () => {
  const [hosts, setHosts] = useState<Host[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [drawerVisible, setDrawerVisible] = useState<boolean>(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        // Fetch hosts and recent jobs
        const hostsData = await hostService.getAllHosts();
        const jobsData = await jobService.getAllJobs(); // Use getAllJobs instead of getJobs to get all jobs with full details
        
        setHosts(hostsData);
        setJobs(jobsData.slice(0, 5)); // Get 5 most recent jobs
        setError(null);
      } catch (err) {
        console.error('Error fetching dashboard data:', err);
        setError('Failed to fetch dashboard data. Please check your connection to the API server.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // Calculate statistics - Fixed to check for roles starting with Splunk* or Cribl* (case-insensitive)
  const activeHosts = hosts.filter(host => host.is_active).length;
  const splunkHosts = hosts.filter(host => 
    host.roles.some(role => role.toLowerCase().startsWith('splunk'))
  ).length;
  const criblHosts = hosts.filter(host => 
    host.roles.some(role => role.toLowerCase().startsWith('cribl'))
  ).length;
  
  const recentJobs = jobs.sort((a, b) => 
    new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  ).slice(0, 5);

  // Enhanced status color logic matching Job History
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

  // Enhanced status text logic matching Job History
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

  // Get host name by ID
  const getHostName = (hostId: number) => {
    const host = hosts.find(h => h.id === hostId);
    return host ? host.hostname : `Host ID: ${hostId}`;
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
                {getHostName(selectedJob.host_id)}
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

  // Legacy status color function for backward compatibility
  const statusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'success':
      case 'completed':
        return 'success';
      case 'running':
      case 'in_progress':
        return 'processing';
      case 'failed':
      case 'error':
        return 'error';
      default:
        return 'default';
    }
  };

  // Host table columns
  const hostColumns = [
    {
      title: 'Hostname',
      dataIndex: 'hostname',
      key: 'hostname',
      render: (text: string, record: Host) => <Link to={`/hosts/${record.id}`}>{text}</Link>,
    },
    {
      title: 'IP Address',
      dataIndex: 'ip_address',
      key: 'ip_address',
    },
    {
      title: 'Roles',
      dataIndex: 'roles',
      key: 'roles',
      render: (roles: string[]) => (
        <>
          {roles.map(role => {
            let color = role.toLowerCase().startsWith('splunk') ? 'green' : 
                       role.toLowerCase().startsWith('cribl') ? 'blue' : 'default';
            return <Tag color={color} key={role}>{role.toUpperCase()}</Tag>;
          })}
        </>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={statusColor(status)}>{status.toUpperCase()}</Tag>
      ),
    },
  ];

  // Job table columns - Updated to use enhanced status logic and show job details in drawer
  const jobColumns = [
    {
      title: 'Job Type',
      dataIndex: 'job_type',
      key: 'job_type',
      render: (text: string) => text.replace(/_/g, ' ').toUpperCase(),
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
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: unknown, record: Job) => (
        <Space size="small">
          <Button 
            type="link" 
            size="small"
            icon={<FileSearchOutlined />}
            onClick={() => showJobDetails(record)}
          >
            View Details
          </Button>
        </Space>
      ),
    },
  ];

  if (loading) {
    return <div style={{ textAlign: 'center', padding: '50px' }}><Spin size="large" /></div>;
  }

  if (error) {
    return <Alert message="Error" description={error} type="error" showIcon />;
  }

  return (
    <div className="dashboard-container">
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>Dashboard</Title>
        <Text>Overview of your SIEMply system status</Text>
      </div>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <Card>
            <Statistic 
              title="Total Hosts" 
              value={hosts.length} 
              prefix={<DatabaseOutlined />} 
            />
            <div style={{ marginTop: 8 }}>
              <Text type="secondary">{activeHosts} active hosts</Text>
            </div>
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic 
              title="Splunk Hosts" 
              value={splunkHosts} 
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic 
              title="Cribl Hosts" 
              value={criblHosts} 
              valueStyle={{ color: '#0050b3' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col span={12}>
          <Card 
            title={<><DatabaseOutlined /> Recent Hosts</>}
            extra={<Link to="/hosts">View All</Link>}
            style={{ marginBottom: 24 }}
          >
            <Table 
              dataSource={hosts.slice(0, 5)} 
              columns={hostColumns} 
              rowKey="id" 
              pagination={false} 
              size="small"
            />
          </Card>
        </Col>
        <Col span={12}>
          <Card 
            title={<><HistoryOutlined /> Recent Jobs</>}
            extra={<Link to="/jobs">View All</Link>}
            style={{ marginBottom: 24 }}
          >
            <Table 
              dataSource={recentJobs} 
              columns={jobColumns} 
              rowKey="id" 
              pagination={false} 
              size="small"
            />
          </Card>
        </Col>
      </Row>

      <Row>
        <Col span={24}>
          <Card title="Quick Actions">
            <Button type="primary" style={{ marginRight: 8 }}>
              <Link to="/hosts/new">Add New Host</Link>
            </Button>
            <Button style={{ marginRight: 8 }}>
              <Link to="/jobs/new">Run Installation</Link>
            </Button>
            <Button>
              <Link to="/settings">Configure Settings</Link>
            </Button>
          </Card>
        </Col>
      </Row>

      {/* Job Details Drawer */}
      <Drawer
        title={
          <span>
            <FileSearchOutlined /> Job Details
            {selectedJob && (
              <Tag 
                color={getStatusColor(selectedJob.status, selectedJob)}
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
    </div>
  );
};

export default Dashboard; 