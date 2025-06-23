import { useState, useEffect } from 'react';
import { Card, Typography, Row, Col, Statistic, Button, Table, Tag, Spin, Alert } from 'antd';
import { 
  DatabaseOutlined, 
  CheckCircleOutlined, 
  WarningOutlined, 
  HistoryOutlined 
} from '@ant-design/icons';
import { Link } from 'react-router-dom';
import { hostService, jobService, Host, Job } from '../services/api';

const { Title, Text } = Typography;

const Dashboard: React.FC = () => {
  const [hosts, setHosts] = useState<Host[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        // Fetch hosts and recent jobs
        const hostsData = await hostService.getAllHosts();
        const jobsData = await jobService.getJobs();
        
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

  // Calculate statistics
  const activeHosts = hosts.filter(host => host.is_active).length;
  const splunkHosts = hosts.filter(host => host.roles.includes('splunk')).length;
  const criblHosts = hosts.filter(host => host.roles.includes('cribl')).length;
  
  const recentJobs = jobs.sort((a, b) => 
    new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  ).slice(0, 5);

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
            let color = role === 'splunk' ? 'green' : role === 'cribl' ? 'blue' : 'default';
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

  // Job table columns
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
      render: (status: string) => (
        <Tag color={statusColor(status)}>{status.toUpperCase()}</Tag>
      ),
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => new Date(date).toLocaleString(),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: unknown, record: Job) => (
        <Link to={`/jobs/${record.id}`}>
          <Button type="link" size="small">View Details</Button>
        </Link>
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
    </div>
  );
};

export default Dashboard; 