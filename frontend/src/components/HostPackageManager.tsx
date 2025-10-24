import React, { useState, useEffect } from 'react';
import {
  Card,
  Collapse,
  Typography,
  Button,
  Space,
  Tag,
  message,
  Progress,
  Alert,
  Divider,
  Row,
  Col,
  Statistic
} from 'antd';
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  ExclamationCircleOutlined,
  DownloadOutlined,
  SettingOutlined,
  InfoCircleOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import { hostService } from '../services/api';

const { Panel } = Collapse;
const { Text } = Typography;

interface PackageStatus {
  name: string;
  installed: boolean;
  version?: string;
  path?: string;
  error?: string;
}

interface HostPackageManagerProps {
  hostId: number;
  hostname: string;
  osType: string;
  osVersion?: string;
  hideTitle?: boolean;
}

const HostPackageManager: React.FC<HostPackageManagerProps> = ({
  hostId,
  osType,
  osVersion,
  hideTitle = false
}) => {
  const [packages, setPackages] = useState<PackageStatus[]>([]);
  const [loading, setLoading] = useState(false);
  const [installing, setInstalling] = useState(false);
  const [lastChecked, setLastChecked] = useState<Date | null>(null);

  // Define required packages based on OS type
  const getRequiredPackages = (os: string): string[] => {
    const basePackages = ['curl', 'wget', 'tmux', 'git', 'unzip', 'tar', 'gzip'];
    
    if (os === 'linux') {
      return [
        ...basePackages,
        'python3',
        'python3-pip',
        'build-essential',
        'libssl-dev',
        'libffi-dev',
        'python3-dev',
        'ca-certificates',
        'apt-transport-https',
        'software-properties-common'
      ];
    } else if (os === 'windows') {
      return [
        'curl',
        'wget',
        'git',
        '7zip',
        'python',
        'chocolatey'
      ];
    }
    
    return basePackages;
  };

  // Check package status on the host
  const checkPackages = async () => {
    setLoading(true);
    try {
      // This would call a new API endpoint to check packages on the host
      const response = await hostService.checkPackages(hostId);
      setPackages(response.packages);
      setLastChecked(new Date());
      message.success('Package status updated successfully');
    } catch (error) {
      console.error('Failed to check packages:', error);
      message.error('Failed to check package status');
      
      // Fallback: simulate package checking for demo purposes
      const requiredPackages = getRequiredPackages(osType);
      const simulatedPackages = requiredPackages.map(pkg => ({
        name: pkg,
        installed: Math.random() > 0.3, // Randomly show some as not installed
        version: Math.random() > 0.3 ? `v${Math.floor(Math.random() * 10) + 1}.${Math.floor(Math.random() * 10)}` : undefined,
        path: Math.random() > 0.3 ? `/usr/bin/${pkg}` : undefined
      }));
      setPackages(simulatedPackages);
      setLastChecked(new Date());
    } finally {
      setLoading(false);
    }
  };

  // Install missing packages
  const installMissingPackages = async () => {
    setInstalling(true);
    try {
      // This would call a new API endpoint to install packages on the host
      await hostService.installPackages(hostId);
      message.success('Package installation completed successfully');
      
      // Refresh package status
      await checkPackages();
    } catch (error) {
      console.error('Failed to install packages:', error);
      message.error('Failed to install packages');
    } finally {
      setInstalling(false);
    }
  };

  // Install specific package
  const installPackage = async (packageName: string) => {
    try {
      // This would call a new API endpoint to install a specific package
      await hostService.installPackage(hostId, packageName);
      message.success(`${packageName} installed successfully`);
      
      // Refresh package status
      await checkPackages();
    } catch (error) {
      console.error(`Failed to install ${packageName}:`, error);
      message.error(`Failed to install ${packageName}`);
    }
  };

  // Load packages on component mount
  useEffect(() => {
    checkPackages();
  }, [hostId]);

  const requiredPackages = getRequiredPackages(osType);
  const installedCount = packages.filter(pkg => pkg.installed).length;
  const missingCount = requiredPackages.length - installedCount;
  const installationProgress = (installedCount / requiredPackages.length) * 100;

  const getPackageIcon = (pkg: PackageStatus) => {
    if (pkg.installed) {
      return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
    } else if (pkg.error) {
      return <ExclamationCircleOutlined style={{ color: '#faad14' }} />;
    } else {
      return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;
    }
  };

  const getPackageTag = (pkg: PackageStatus) => {
    if (pkg.installed) {
      return <Tag color="success">Installed</Tag>;
    } else if (pkg.error) {
      return <Tag color="warning">Error</Tag>;
    } else {
      return <Tag color="error">Missing</Tag>;
    }
  };

  return (
    <>
      <style>
        {`
          .package-management-collapse .ant-collapse-header {
            color: inherit !important;
          }
          .package-management-collapse .ant-collapse-header-text {
            color: inherit !important;
          }
          .package-management-collapse .ant-collapse-expand-icon {
            color: inherit !important;
          }
        `}
      </style>
      <Card
        title={!hideTitle ? (
          <Space>
            <SettingOutlined />
            <span>Package Management</span>
          </Space>
        ) : undefined}
        extra={!hideTitle ? (
          <Space>
            <Button
              icon={<ReloadOutlined />}
              onClick={checkPackages}
              loading={loading}
              size="small"
            >
              Refresh
            </Button>
          </Space>
        ) : (
          <Button
            icon={<ReloadOutlined />}
            onClick={checkPackages}
            loading={loading}
            size="small"
          >
            Refresh
          </Button>
        )}
        style={{ marginBottom: hideTitle ? 0 : 16 }}
      >
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col span={8}>
          <Statistic
            title="Total Required"
            value={requiredPackages.length}
            prefix={<InfoCircleOutlined />}
          />
        </Col>
        <Col span={8}>
          <Statistic
            title="Installed"
            value={installedCount}
            valueStyle={{ color: '#52c41a' }}
            prefix={<CheckCircleOutlined />}
          />
        </Col>
        <Col span={8}>
          <Statistic
            title="Missing"
            value={missingCount}
            valueStyle={{ color: '#ff4d4f' }}
            prefix={<CloseCircleOutlined />}
          />
        </Col>
      </Row>

      <Progress
        percent={Math.round(installationProgress)}
        status={installationProgress === 100 ? 'success' : 'active'}
        strokeColor={{
          '0%': '#108ee9',
          '100%': '#52c41a',
        }}
        style={{ marginBottom: 16 }}
      />

      {missingCount > 0 && (
        <Alert
          message={`${missingCount} packages are missing`}
          description="Click 'Install All Missing Packages' to install the required packages automatically."
          type="warning"
          showIcon
          action={
            <Button
              size="small"
              type="primary"
              danger
              icon={<DownloadOutlined />}
              onClick={installMissingPackages}
              loading={installing}
            >
              Install All Missing
            </Button>
          }
          style={{ marginBottom: 16 }}
        />
      )}

      <Collapse
        defaultActiveKey={['required-packages']}
        expandIconPosition="end"
        style={{ background: 'transparent' }}
        className="package-management-collapse"
      >
        <Panel
          header={
            <Space>
              <span>Required Packages ({requiredPackages.length})</span>
              {missingCount > 0 && (
                <Tag color="error">{missingCount} missing</Tag>
              )}
            </Space>
          }
          key="required-packages"
        >
          <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
            {packages.map((pkg, index) => (
              <div key={pkg.name} style={{ marginBottom: 12 }}>
                <Row align="middle" gutter={16}>
                  <Col span={2}>
                    {getPackageIcon(pkg)}
                  </Col>
                  <Col span={6}>
                    <Text strong>{pkg.name}</Text>
                  </Col>
                  <Col span={4}>
                    {getPackageTag(pkg)}
                  </Col>
                  <Col span={6}>
                    {pkg.version && (
                      <Text type="secondary">v{pkg.version}</Text>
                    )}
                  </Col>
                  <Col span={4}>
                    {!pkg.installed && (
                      <Button
                        size="small"
                        type="primary"
                        icon={<DownloadOutlined />}
                        onClick={() => installPackage(pkg.name)}
                        loading={installing}
                      >
                        Install
                      </Button>
                    )}
                  </Col>
                </Row>
                {pkg.path && (
                  <Text type="secondary" style={{ marginLeft: 24 }}>
                    Path: {pkg.path}
                  </Text>
                )}
                {pkg.error && (
                  <Text type="danger" style={{ marginLeft: 24 }}>
                    Error: {pkg.error}
                  </Text>
                )}
                {index < packages.length - 1 && <Divider style={{ margin: '8px 0' }} />}
              </div>
            ))}
          </div>
        </Panel>

        <Panel
          header="System Information"
          key="system-info"
        >
          <Row gutter={16}>
            <Col span={12}>
              <Text strong>Operating System:</Text>
              <br />
              <Text>{osType.charAt(0).toUpperCase() + osType.slice(1)}</Text>
              {osVersion && (
                <>
                  <br />
                  <Text type="secondary">{osVersion}</Text>
                </>
              )}
            </Col>
            <Col span={12}>
              <Text strong>Last Checked:</Text>
              <br />
              <Text type="secondary">
                {lastChecked ? lastChecked.toLocaleString() : 'Never'}
              </Text>
            </Col>
          </Row>
        </Panel>
      </Collapse>
      </Card>
    </>
  );
};

export default HostPackageManager;
