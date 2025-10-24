import { useState } from 'react';
import { Form, Input, Button, Typography, Card, message, Divider, Alert } from 'antd';
import { UserOutlined, LockOutlined, MailOutlined, UserAddOutlined } from '@ant-design/icons';
import { useNavigate, Link } from 'react-router-dom';
import api from '../services/api';

const { Title, Text } = Typography;

interface RegisterFormData {
  username: string;
  email: string;
  password: string;
  confirmPassword: string;
  full_name?: string;
}

const Register: React.FC = () => {
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const [form] = Form.useForm();

  // Handle registration form submission
  const handleSubmit = async (values: RegisterFormData) => {
    try {
      setLoading(true);
      setError(null);

      if (values.password !== values.confirmPassword) {
        setError('Passwords do not match');
        return;
      }

      // Register user
      const userData = {
        username: values.username,
        email: values.email,
        password: values.password,
        full_name: values.full_name
      };

      await api.post('/auth/register', userData);

      message.success('Registration successful! You can now log in.');
      navigate('/login');
    } catch (error: any) {
      console.error('Registration error:', error);
      setError(error.response?.data?.detail || 'Registration failed. Please try again.');
      message.error('Registration failed. Please try again.');
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
              Register for <span style={{ color: '#1890ff' }}>SIEM</span>ply
            </Title>
            <Text type="secondary">Create your account</Text>
          </div>
        }
      >
        {error && (
          <Alert 
            message="Registration Error" 
            description={error} 
            type="error" 
            showIcon 
            style={{ marginBottom: 16 }} 
          />
        )}

        <Form
          form={form}
          name="register"
          onFinish={handleSubmit}
          layout="vertical"
          scrollToFirstError
        >
          <Form.Item
            name="username"
            rules={[
              { required: true, message: 'Please enter a username' },
              { min: 3, message: 'Username must be at least 3 characters' }
            ]}
          >
            <Input 
              prefix={<UserOutlined />} 
              placeholder="Username" 
              size="large" 
            />
          </Form.Item>

          <Form.Item
            name="email"
            rules={[
              { required: true, message: 'Please enter your email' },
              { type: 'email', message: 'Please enter a valid email' }
            ]}
          >
            <Input 
              prefix={<MailOutlined />} 
              placeholder="Email" 
              size="large" 
            />
          </Form.Item>

          <Form.Item
            name="full_name"
          >
            <Input 
              prefix={<UserOutlined />} 
              placeholder="Full Name (optional)" 
              size="large" 
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[
              { required: true, message: 'Please enter a password' },
              { min: 8, message: 'Password must be at least 8 characters' }
            ]}
          >
            <Input.Password 
              prefix={<LockOutlined />} 
              placeholder="Password" 
              size="large" 
            />
          </Form.Item>

          <Form.Item
            name="confirmPassword"
            rules={[
              { required: true, message: 'Please confirm your password' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('password') === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error('The two passwords do not match'));
                },
              }),
            ]}
          >
            <Input.Password 
              prefix={<LockOutlined />} 
              placeholder="Confirm Password" 
              size="large" 
            />
          </Form.Item>

          <Form.Item>
            <Button 
              type="primary" 
              htmlType="submit" 
              loading={loading}
              icon={<UserAddOutlined />}
              size="large"
              block
            >
              Register
            </Button>
          </Form.Item>
        </Form>
        
        <Divider plain>Already have an account?</Divider>
        
        <Button 
          type="link" 
          block
          onClick={() => navigate('/login')}
        >
          Log in
        </Button>
      </Card>
    </div>
  );
};

export default Register; 