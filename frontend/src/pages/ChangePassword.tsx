import { useState } from 'react';
import { Form, Input, Button, Card, message, Typography, Alert } from 'antd';
import { LockOutlined, SaveOutlined } from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import api from '../services/api';

const { Title, Text } = Typography;

interface ChangePasswordFormData {
  currentPassword: string;
  newPassword: string;
  confirmPassword: string;
}

interface LocationState {
  firstLogin?: boolean;
}

const ChangePassword: React.FC = () => {
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const location = useLocation();
  const { firstLogin } = (location.state as LocationState) || {};
  
  const handleSubmit = async (values: ChangePasswordFormData) => {
    try {
      setLoading(true);
      setError(null);
      
      if (values.newPassword !== values.confirmPassword) {
        setError('New passwords do not match');
        return;
      }
      
      await api.post('/auth/change-password', {
        current_password: values.currentPassword,
        new_password: values.newPassword
      });
      
      message.success('Password changed successfully');
      
      // If it's first login, redirect to dashboard
      if (firstLogin) {
        navigate('/dashboard');
      } else {
        navigate('/settings');
      }
    } catch (error: any) {
      console.error('Password change error:', error);
      setError(error.response?.data?.detail || 'Failed to change password');
      message.error('Failed to change password');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div style={{ maxWidth: 600, margin: '0 auto', padding: '24px' }}>
      <Card
        title={
          <Title level={3}>
            {firstLogin ? 'Set New Password' : 'Change Password'}
          </Title>
        }
      >
        {firstLogin && (
          <Alert
            message="Security Notice"
            description="You are using the default password. Please set a new password to continue."
            type="warning"
            showIcon
            style={{ marginBottom: 24 }}
          />
        )}
        
        {error && (
          <Alert
            message="Error"
            description={error}
            type="error"
            showIcon
            style={{ marginBottom: 24 }}
          />
        )}
        
        <Form
          name="change-password"
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Form.Item
            name="currentPassword"
            label="Current Password"
            rules={[{ required: true, message: 'Please enter your current password' }]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="Current Password"
            />
          </Form.Item>
          
          <Form.Item
            name="newPassword"
            label="New Password"
            rules={[
              { required: true, message: 'Please enter a new password' },
              { min: 8, message: 'Password must be at least 8 characters' }
            ]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="New Password"
            />
          </Form.Item>
          
          <Form.Item
            name="confirmPassword"
            label="Confirm New Password"
            rules={[
              { required: true, message: 'Please confirm your new password' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('newPassword') === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error('The two passwords do not match'));
                },
              }),
            ]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="Confirm New Password"
            />
          </Form.Item>
          
          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              icon={<SaveOutlined />}
              block
            >
              {firstLogin ? 'Set New Password' : 'Change Password'}
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
};

export default ChangePassword; 