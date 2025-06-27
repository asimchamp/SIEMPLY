import { useState } from 'react';
import { Form, Input, Button, Typography, Card, message, Divider, Alert } from 'antd';
import { UserOutlined, LockOutlined, LoginOutlined } from '@ant-design/icons';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../services/authContext';

const { Title, Text } = Typography;

interface LoginFormData {
  username: string;
  password: string;
}

const Login: React.FC = () => {
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const { login } = useAuth();

  // Handle login form submission
  const handleSubmit = async (values: LoginFormData) => {
    try {
      setLoading(true);
      setError(null);

      // Use the login function from authContext
      await login(values.username, values.password);
      
      message.success('Login successful');
      // Redirection is handled in the authContext
    } catch (error: any) {
      console.error('Login error:', error);
      setError(error.response?.data?.detail || 'Login failed. Please check your credentials.');
      message.error('Login failed. Please check your credentials.');
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