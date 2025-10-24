import { useState, useEffect } from 'react';
import { Form, Input, Button, Typography, Card, message, Divider, Alert, Space, Tooltip } from 'antd';
import { UserOutlined, LockOutlined, LoginOutlined, ApiOutlined, ReloadOutlined, ToolOutlined } from '@ant-design/icons';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../services/authContext';
import { testApiConnection, setApiUrl } from '../services/api';
import { getBrowserInfo } from '../utils/storage';

const { Title, Text } = Typography;

interface LoginFormData {
  username: string;
  password: string;
}

const Login: React.FC = () => {
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<{
    status: 'unknown' | 'testing' | 'success' | 'failed';
    url?: string;
    error?: string;
  }>({ status: 'unknown' });
  const navigate = useNavigate();
  const { login } = useAuth();

  // Test API connection on component mount
  useEffect(() => {
    testConnection();
  }, []);

  // Test API connection
  const testConnection = async () => {
    setConnectionStatus({ status: 'testing' });
    const result = await testApiConnection();
    setConnectionStatus({
      status: result.success ? 'success' : 'failed',
      url: result.url,
      error: result.error
    });
  };

  // Fix API URL by setting it to the correct server IP
  const fixApiUrl = () => {
    setApiUrl('http://192.168.100.44:5050');
    message.success('API URL fixed! Testing connection...');
    setTimeout(() => {
      testConnection();
      // Reload the page to ensure all components use the new URL
      window.location.reload();
    }, 500);
  };

  // Handle login form submission
  const handleSubmit = async (values: LoginFormData) => {
    try {
      setLoading(true);
      setError(null);

      // Test connection first if it failed
      if (connectionStatus.status === 'failed') {
        message.error('Cannot connect to server. Please check connection or fix API URL.');
        return;
      }

      // Use the login function from authContext
      await login(values.username, values.password);
      
      message.success('Login successful');
      // Redirection is handled in the authContext
    } catch (error: any) {
      console.error(`Login error (${getBrowserInfo()}):`, error);
      
      // Enhanced error handling for network vs authentication errors
      if (error.code === 'ERR_NETWORK' || error.message === 'Network Error') {
        setError(`Network Error: Cannot connect to server. Please check your connection or try fixing the API URL. (${getBrowserInfo()})`);
        message.error('Network Error: Cannot connect to server');
        setConnectionStatus({ status: 'failed', error: 'Network connection failed' });
      } else {
        setError(error.response?.data?.detail || 'Login failed. Please check your credentials.');
        message.error('Login failed. Please check your credentials.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ 
      display: 'flex', 
      justifyContent: 'center', 
      alignItems: 'center', 
      minHeight: '100vh',
      background: '#f0f2f5'
    }}>
      <Card 
        style={{ width: 400, boxShadow: '0 4px 8px rgba(0, 0, 0, 0.1)' }}
        title={
          <div style={{ textAlign: 'center' }}>
            <Title level={2} style={{ marginBottom: 0 }}>
              <span style={{ color: '#1890ff' }}>SIEM</span>ply
            </Title>
            <Text type="secondary">SIEM Installation & Management System</Text>
          </div>
        }
      >
        {/* Connection Status */}
        {connectionStatus.status !== 'unknown' && (
          <Alert
            message={`Backend Connection (${getBrowserInfo()})`}
            description={
              <div>
                <div>Status: {connectionStatus.status === 'testing' ? 'Testing...' : 
                              connectionStatus.status === 'success' ? 'Connected' : 'Failed'}</div>
                <div>URL: {connectionStatus.url}</div>
                {connectionStatus.error && <div>Error: {connectionStatus.error}</div>}
                {connectionStatus.status === 'failed' && (
                  <Space style={{ marginTop: 8 }}>
                    <Button 
                      size="small" 
                      icon={<ReloadOutlined />} 
                      onClick={testConnection}
                    >
                      Test Connection
                    </Button>
                    <Button 
                      size="small" 
                      icon={<ToolOutlined />} 
                      onClick={fixApiUrl}
                      type="primary"
                    >
                      Fix API URL
                    </Button>
                  </Space>
                )}
              </div>
            }
            type={connectionStatus.status === 'success' ? 'success' : 
                  connectionStatus.status === 'testing' ? 'info' : 'warning'}
            showIcon
            style={{ marginBottom: 16 }}
          />
        )}

        {error && (
          <Alert 
            message="Login Error" 
            description={error} 
            type="error" 
            showIcon 
            style={{ marginBottom: 16 }} 
          />
        )}

        <Form
          name="login"
          initialValues={{ remember: true }}
          onFinish={handleSubmit}
          layout="vertical"
        >
          <Form.Item
            name="username"
            rules={[{ required: true, message: 'Please enter your username' }]}
          >
            <Input 
              prefix={<UserOutlined />} 
              placeholder="Username" 
              size="large" 
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[{ required: true, message: 'Please enter your password' }]}
          >
            <Input.Password 
              prefix={<LockOutlined />} 
              placeholder="Password" 
              size="large" 
            />
          </Form.Item>

          <Form.Item>
            <Button 
              type="primary" 
              htmlType="submit" 
              loading={loading}
              icon={<LoginOutlined />}
              size="large"
              block
            >
              Log in
            </Button>
          </Form.Item>
        </Form>
        
        <Divider plain>Don't have an account?</Divider>
        
        <Button 
          type="link" 
          block
          onClick={() => navigate('/register')}
        >
          Register now
        </Button>
      </Card>
    </div>
  );
};

export default Login; 