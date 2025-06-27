import { useState } from 'react';
import { Card, Typography, Form, Input, Button, message } from 'antd';
import { LockOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../services/authContext';

const { Title, Text } = Typography;

const ChangePassword: React.FC = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { user } = useAuth();

  const handleSubmit = async (values: any) => {
    const { currentPassword, newPassword, confirmPassword } = values;
    
    if (newPassword !== confirmPassword) {
      message.error('New passwords do not match');
      return;
    }
    
    try {
      setLoading(true);
      
      // Call API to change password
      // This is a placeholder - you would need to implement the actual API call
      // using an API service similar to other parts of your application
      await new Promise(resolve => setTimeout(resolve, 1000)); // Simulating API call
      
      message.success('Password changed successfully');
      navigate('/dashboard');
    } catch (error) {
      console.error('Failed to change password:', error);
      message.error('Failed to change password. Please try again.');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="change-password-container">
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>
          <LockOutlined /> Change Password
        </Title>
        <Text>Update your account password</Text>
      </div>
      
      <Card style={{ maxWidth: 500, margin: '0 auto' }}>
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Form.Item
            name="currentPassword"
            label="Current Password"
            rules={[{ required: true, message: 'Please enter your current password' }]}
          >
            <Input.Password placeholder="Enter your current password" />
          </Form.Item>
          
          <Form.Item
            name="newPassword"
            label="New Password"
            rules={[
              { required: true, message: 'Please enter your new password' },
              { min: 8, message: 'Password must be at least 8 characters' }
            ]}
          >
            <Input.Password placeholder="Enter your new password" />
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
            <Input.Password placeholder="Confirm your new password" />
          </Form.Item>
          
          <Form.Item>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <Button onClick={() => navigate(-1)}>
                Cancel
              </Button>
              <Button type="primary" htmlType="submit" loading={loading}>
                Change Password
              </Button>
            </div>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
};

export default ChangePassword; 