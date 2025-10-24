import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Typography, 
  Button, 
  Space, 
  Alert, 
  Divider, 
  Row, 
  Col,
  Input,
  message,
  Tooltip,
  Tag,
  Collapse,
  Steps,
  Result
} from 'antd';
import { 
  KeyOutlined, 
  CopyOutlined, 
  PlusOutlined, 
  CheckCircleOutlined,
  InfoCircleOutlined,
  FileTextOutlined,
  CodeOutlined,
  SafetyOutlined
} from '@ant-design/icons';
import { sshService } from '../services/api';

const { Title, Text, Paragraph } = Typography;
const { Panel } = Collapse;
const { Step } = Steps;

interface SSHKeyManagerProps {
  hideTitle?: boolean;
}

const SSHKeyManager: React.FC<SSHKeyManagerProps> = ({ hideTitle = false }) => {
  const [publicKey, setPublicKey] = useState<string>('');
  const [keyExists, setKeyExists] = useState<boolean>(false);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [isChecking, setIsChecking] = useState<boolean>(true);

  useEffect(() => {
    checkSSHKey();
  }, []);

  const checkSSHKey = async () => {
    try {
      setIsChecking(true);
      const data = await sshService.checkSSHKey();
      setKeyExists(data.exists);
      if (data.exists && data.public_key) {
        setPublicKey(data.public_key);
      }
    } catch (error) {
      console.error('Error checking SSH key:', error);
      message.error('Failed to check SSH key status');
      setKeyExists(false);
    } finally {
      setIsChecking(false);
    }
  };

  const generateSSHKey = async () => {
    try {
      setIsGenerating(true);
      const data = await sshService.generateSSHKey('rsa', 4096, '');
      setPublicKey(data.public_key);
      setKeyExists(true);
      message.success('SSH key generated successfully!');
    } catch (error) {
      console.error('Error generating SSH key:', error);
      message.error('Failed to generate SSH key. Please try again.');
    } finally {
      setIsGenerating(false);
    }
  };

  const copyPublicKey = async () => {
    try {
      await navigator.clipboard.writeText(publicKey);
      message.success('Public key copied to clipboard!');
    } catch (error) {
      console.error('Failed to copy to clipboard:', error);
      message.error('Failed to copy to clipboard. Please copy manually.');
    }
  };

  const downloadPublicKey = () => {
    const blob = new Blob([publicKey], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'id_rsa.pub';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    message.success('Public key downloaded!');
  };

  if (isChecking) {
    return (
      <Card>
        <div style={{ textAlign: 'center', padding: '20px' }}>
          <Text>Checking SSH key status...</Text>
        </div>
      </Card>
    );
  }

  return (
    <div>
      {!hideTitle && (
        <div style={{ marginBottom: 24 }}>
          <Title level={4}>
            <KeyOutlined /> SSH Key Management
          </Title>
          <Text type="secondary">
            Manage SSH keys for secure host connections
          </Text>
        </div>
      )}

      {!keyExists ? (
        <Card>
          <Result
            icon={<KeyOutlined style={{ color: '#faad14' }} />}
            title="SSH Key Not Found"
            subTitle="No SSH key pair detected. Generate a new key to enable secure host connections."
            extra={
              <Button 
                type="primary" 
                icon={<PlusOutlined />}
                size="large"
                onClick={generateSSHKey}
                loading={isGenerating}
              >
                Generate SSH Key
              </Button>
            }
          />
          <Divider />
          <Alert
            message="SSH Key Generation"
            description="This will create a new RSA key pair (4096 bits) without a passphrase for automated deployments."
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />
        </Card>
      ) : (
        <Card>
          <Result
            icon={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
            title="SSH Key Available"
            subTitle="Your SSH key pair is ready for use."
            status="success"
          />
          
          <Divider />
          
          <Row gutter={16}>
            <Col span={24}>
              <Title level={5}>
                <FileTextOutlined /> Public Key (id_rsa.pub)
              </Title>
              <Input.TextArea
                value={publicKey}
                rows={6}
                readOnly
                style={{ 
                  fontFamily: 'monospace',
                  fontSize: '12px'
                }}
              />
            </Col>
          </Row>
          
          <Divider />
          
          <Row gutter={16}>
            <Col span={12}>
              <Space direction="vertical" style={{ width: '100%' }}>
                <Button 
                  type="primary" 
                  icon={<CopyOutlined />}
                  onClick={copyPublicKey}
                  block
                >
                  Copy Public Key
                </Button>
                <Button 
                  icon={<FileTextOutlined />}
                  onClick={downloadPublicKey}
                  block
                >
                  Download Public Key
                </Button>
              </Space>
            </Col>
            <Col span={12}>
              <Space direction="vertical" style={{ width: '100%' }}>
                <Button 
                  icon={<PlusOutlined />}
                  onClick={generateSSHKey}
                  loading={isGenerating}
                  block
                >
                  Regenerate Key
                </Button>
                <Button 
                  icon={<KeyOutlined />}
                  onClick={checkSSHKey}
                  block
                >
                  Refresh Status
                </Button>
              </Space>
            </Col>
          </Row>
        </Card>
      )}

      <Divider />

      <Card title={
        <span>
          <SafetyOutlined /> SSH Key Configuration Instructions
        </span>
      }>
        <Collapse defaultActiveKey={['target-host']} ghost>
          <Panel 
            header={
              <span>
                <CodeOutlined /> Target Host Configuration
              </span>
            } 
            key="target-host"
          >
            <Steps direction="vertical" size="small">
              <Step 
                title="Login as root" 
                description="Access the target host with root privileges"
                icon={<CodeOutlined />}
              />
              <Step 
                title="Create SSH directory" 
                description="mkdir -p /root/.ssh"
                icon={<CodeOutlined />}
              />
              <Step 
                title="Create authorized_keys file" 
                description="touch /root/.ssh/authorized_keys"
                icon={<CodeOutlined />}
              />
              <Step 
                title="Paste public key" 
                description="Copy the public key above and paste it into /root/.ssh/authorized_keys"
                icon={<KeyOutlined />}
              />
              <Step 
                title="Set permissions" 
                description="chmod 700 /root/.ssh && chmod 600 /root/.ssh/authorized_keys"
                icon={<SafetyOutlined />}
              />
            </Steps>
            
            <Divider />
            
            <Alert
              message="Security Note"
              description="Ensure proper file permissions are set to prevent unauthorized access. The .ssh directory should be 700 and authorized_keys should be 600."
              type="warning"
              showIcon
              style={{ marginBottom: 16 }}
            />
            
            <Text type="secondary">
              After completing these steps, you should be able to connect to the target host using SSH key authentication without entering a password.
            </Text>
          </Panel>
          
          <Panel 
            header={
              <span>
                <InfoCircleOutlined /> Additional Information
              </span>
            } 
            key="additional-info"
          >
            <Row gutter={16}>
              <Col span={12}>
                <Title level={5}>Key Details</Title>
                <ul>
                  <li><Text strong>Type:</Text> RSA</li>
                  <li><Text strong>Bits:</Text> 4096</li>
                  <li><Text strong>Passphrase:</Text> None (for automation)</li>
                  <li><Text strong>Location:</Text> ~/.ssh/id_rsa (private)</li>
                  <li><Text strong>Location:</Text> ~/.ssh/id_rsa.pub (public)</li>
                </ul>
              </Col>
              <Col span={12}>
                <Title level={5}>Best Practices</Title>
                <ul>
                  <li>Keep private key secure and never share</li>
                  <li>Use different keys for different environments</li>
                  <li>Regularly rotate keys for security</li>
                  <li>Monitor authorized_keys for unauthorized entries</li>
                  <li>Consider using SSH agents for key management</li>
                </ul>
              </Col>
            </Row>
          </Panel>
        </Collapse>
      </Card>
    </div>
  );
};

export default SSHKeyManager;
