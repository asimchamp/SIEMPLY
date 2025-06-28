import { useState, useEffect } from 'react';
import { 
  Modal, 
  Typography, 
  Descriptions, 
  Spin, 
  Alert, 
  Progress, 
  Tabs, 
  Card, 
  Statistic, 
  Row, 
  Col,
  Divider
} from 'antd';
import {
  DesktopOutlined,
  HddOutlined,
  BarChartOutlined,
  ClockCircleOutlined,
  ApiOutlined
} from '@ant-design/icons';
import { hostService, Host } from '../services/api';

const { Title, Text } = Typography;

interface HostDetailsModalProps {
  visible: boolean;
  host: Host | null;
  onClose: () => void;
}

interface SystemMetrics {
  status: string;
  hostname: string;
  os: {
    name?: string;
    version?: string;
    kernel?: string;
    id?: string;
  };
  cpu: {
    model?: string;
    cores?: number;
    usage_percent?: number;
    load_1min?: number;
    load_5min?: number;
    load_15min?: number;
  };
  memory: {
    total_mb?: number;
    used_mb?: number;
    free_mb?: number;
    usage_percent?: number;
  };
  disk: {
    filesystem?: string;
    total?: string;
    used?: string;
    available?: string;
    usage_percent?: string;
    mount_point?: string;
  };
  uptime: {
    pretty?: string;
    seconds?: number;
  };
  error?: string;
}

const HostDetailsModal: React.FC<HostDetailsModalProps> = ({ visible, host, onClose }) => {
  const [loading, setLoading] = useState<boolean>(false);
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (visible && host) {
      fetchSystemMetrics(host.id);
    } else {
      // Reset state when modal closes
      setMetrics(null);
      setError(null);
    }
  }, [visible, host]);

  const fetchSystemMetrics = async (hostId: number) => {
    try {
      setLoading(true);
      setError(null);
      
      const data = await hostService.getSystemMetrics(hostId);
      setMetrics(data as SystemMetrics);
    } catch (err: any) {
      console.error('Failed to fetch system metrics:', err);
      setError(err.response?.data?.detail || 'Failed to fetch system metrics');
    } finally {
      setLoading(false);
    }
  };

  const renderOsInfo = () => {
    if (!metrics?.os) return <Alert message="No OS information available" type="info" />;
    
    return (
      <Descriptions bordered column={1}>
        <Descriptions.Item label="OS Name">{metrics.os.name || 'Unknown'}</Descriptions.Item>
        <Descriptions.Item label="Version">{metrics.os.version || 'Unknown'}</Descriptions.Item>
        <Descriptions.Item label="Kernel">{metrics.os.kernel || 'Unknown'}</Descriptions.Item>
        <Descriptions.Item label="Distribution">{metrics.os.id || 'Unknown'}</Descriptions.Item>
      </Descriptions>
    );
  };

  const renderCpuInfo = () => {
    if (!metrics?.cpu) return <Alert message="No CPU information available" type="info" />;
    
    return (
      <>
        <Descriptions bordered column={1}>
          <Descriptions.Item label="CPU Model">{metrics.cpu.model || 'Unknown'}</Descriptions.Item>
          <Descriptions.Item label="Cores">{metrics.cpu.cores || 'Unknown'}</Descriptions.Item>
        </Descriptions>
        
        <Divider orientation="left">CPU Usage</Divider>
        
        {metrics.cpu.usage_percent !== undefined && (
          <Progress
            percent={Math.round(metrics.cpu.usage_percent)}
            status={metrics.cpu.usage_percent > 90 ? "exception" : "normal"}
            format={percent => `${percent}%`}
          />
        )}
        
        <Divider orientation="left">Load Average</Divider>
        
        <Row gutter={16}>
          <Col span={8}>
            <Card>
              <Statistic 
                title="1 minute" 
                value={metrics.cpu.load_1min !== undefined ? metrics.cpu.load_1min : 'N/A'} 
                precision={2}
              />
            </Card>
          </Col>
          <Col span={8}>
            <Card>
              <Statistic 
                title="5 minutes" 
                value={metrics.cpu.load_5min !== undefined ? metrics.cpu.load_5min : 'N/A'} 
                precision={2}
              />
            </Card>
          </Col>
          <Col span={8}>
            <Card>
              <Statistic 
                title="15 minutes" 
                value={metrics.cpu.load_15min !== undefined ? metrics.cpu.load_15min : 'N/A'} 
                precision={2}
              />
            </Card>
          </Col>
        </Row>
      </>
    );
  };

  const renderMemoryInfo = () => {
    if (!metrics?.memory) return <Alert message="No memory information available" type="info" />;
    
    const totalGB = metrics.memory.total_mb ? (metrics.memory.total_mb / 1024).toFixed(2) : 'Unknown';
    const usedGB = metrics.memory.used_mb ? (metrics.memory.used_mb / 1024).toFixed(2) : 'Unknown';
    const freeGB = metrics.memory.free_mb ? (metrics.memory.free_mb / 1024).toFixed(2) : 'Unknown';
    
    return (
      <>
        <Descriptions bordered column={1}>
          <Descriptions.Item label="Total Memory">{totalGB} GB</Descriptions.Item>
          <Descriptions.Item label="Used Memory">{usedGB} GB</Descriptions.Item>
          <Descriptions.Item label="Free Memory">{freeGB} GB</Descriptions.Item>
        </Descriptions>
        
        <Divider orientation="left">Memory Usage</Divider>
        
        {metrics.memory.usage_percent !== undefined && (
          <Progress
            percent={Math.round(metrics.memory.usage_percent)}
            status={metrics.memory.usage_percent > 90 ? "exception" : "normal"}
            format={percent => `${percent}%`}
          />
        )}
      </>
    );
  };

  const renderDiskInfo = () => {
    if (!metrics?.disk) return <Alert message="No disk information available" type="info" />;
    
    return (
      <>
        <Descriptions bordered column={1}>
          <Descriptions.Item label="Filesystem">{metrics.disk.filesystem || 'Unknown'}</Descriptions.Item>
          <Descriptions.Item label="Mount Point">{metrics.disk.mount_point || 'Unknown'}</Descriptions.Item>
          <Descriptions.Item label="Total Space">{metrics.disk.total || 'Unknown'}</Descriptions.Item>
          <Descriptions.Item label="Used Space">{metrics.disk.used || 'Unknown'}</Descriptions.Item>
          <Descriptions.Item label="Available Space">{metrics.disk.available || 'Unknown'}</Descriptions.Item>
        </Descriptions>
        
        <Divider orientation="left">Disk Usage</Divider>
        
        {metrics.disk.usage_percent && (
          <Progress
            percent={parseInt(metrics.disk.usage_percent.replace('%', ''))}
            status={parseInt(metrics.disk.usage_percent.replace('%', '')) > 90 ? "exception" : "normal"}
            format={percent => `${percent}%`}
          />
        )}
      </>
    );
  };

  const renderUptimeInfo = () => {
    if (!metrics?.uptime) return <Alert message="No uptime information available" type="info" />;
    
    // Convert seconds to days, hours, minutes
    let uptimeDisplay = 'Unknown';
    if (metrics.uptime.seconds !== undefined) {
      const days = Math.floor(metrics.uptime.seconds / 86400);
      const hours = Math.floor((metrics.uptime.seconds % 86400) / 3600);
      const minutes = Math.floor((metrics.uptime.seconds % 3600) / 60);
      
      uptimeDisplay = `${days} days, ${hours} hours, ${minutes} minutes`;
    } else if (metrics.uptime.pretty) {
      uptimeDisplay = metrics.uptime.pretty;
    }
    
    return (
      <Card>
        <Statistic 
          title="System Uptime" 
          value={uptimeDisplay} 
          prefix={<ClockCircleOutlined />} 
        />
      </Card>
    );
  };

  const renderContent = () => {
    if (loading) {
      return (
        <div style={{ textAlign: 'center', padding: '40px 0' }}>
          <Spin size="large" />
          <p style={{ marginTop: 16 }}>Fetching system metrics...</p>
        </div>
      );
    }
    
    if (error) {
      return (
        <Alert
          message="Error"
          description={error}
          type="error"
          showIcon
        />
      );
    }
    
    if (!metrics) {
      return (
        <Alert
          message="No Data"
          description="No system metrics available"
          type="info"
          showIcon
        />
      );
    }
    
    if (metrics.status === 'offline') {
      return (
        <Alert
          message="Host Offline"
          description={metrics.error || "Could not connect to host to retrieve metrics"}
          type="warning"
          showIcon
        />
      );
    }
    
    // Define tabs items array instead of using TabPane children
    const tabItems = [
      {
        key: 'overview',
        label: <span><DesktopOutlined /> Overview</span>,
        children: (
          <Row gutter={[16, 16]}>
            <Col span={24}>
              <Card title="OS Information">
                {renderOsInfo()}
              </Card>
            </Col>
            <Col span={24}>
              {renderUptimeInfo()}
            </Col>
          </Row>
        )
      },
      {
        key: 'cpu',
        label: <span><BarChartOutlined /> CPU</span>,
        children: (
          <Card title="CPU Information">
            {renderCpuInfo()}
          </Card>
        )
      },
      {
        key: 'memory',
        label: <span><ApiOutlined /> Memory</span>,
        children: (
          <Card title="Memory Information">
            {renderMemoryInfo()}
          </Card>
        )
      },
      {
        key: 'storage',
        label: <span><HddOutlined /> Storage</span>,
        children: (
          <Card title="Storage Information">
            {renderDiskInfo()}
          </Card>
        )
      }
    ];
    
    return (
      <Tabs defaultActiveKey="overview" items={tabItems} />
    );
  };

  return (
    <Modal
      title={
        <Title level={4}>
          <DesktopOutlined /> {host ? `${host.hostname} System Metrics` : 'Host Details'}
        </Title>
      }
      open={visible}
      onCancel={onClose}
      width={800}
      footer={null}
    >
      {renderContent()}
    </Modal>
  );
};

export default HostDetailsModal; 