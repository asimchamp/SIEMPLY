import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Typography, 
  Table, 
  Button, 
  Modal, 
  Form, 
  Input, 
  Switch, 
  Tag, 
  message, 
  Popconfirm,
  Space,
  Tooltip,
  Row,
  Col,
  Badge,
  Avatar,
  Select
} from 'antd';
import { 
  UserOutlined, 
  PlusOutlined, 
  EditOutlined, 
  DeleteOutlined, 
  SyncOutlined,
  LockOutlined,
  UnlockOutlined,
  CrownOutlined,
  KeyOutlined
} from '@ant-design/icons';
import { ColumnType } from 'antd/es/table';
import dayjs from 'dayjs';
import { userService, User, CreateUserData, UpdateUserData, ChangePasswordData } from '../services/api';

const { Title, Text } = Typography;
const { Password } = Input;
const { Option } = Select;

const Users: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [modalVisible, setModalVisible] = useState<boolean>(false);
  const [passwordModalVisible, setPasswordModalVisible] = useState<boolean>(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [changingPasswordUser, setChangingPasswordUser] = useState<User | null>(null);
  const [form] = Form.useForm();
  const [passwordForm] = Form.useForm();

  // Load users on component mount
  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const usersData = await userService.getAllUsers();
      setUsers(usersData);
      setError(null);
    } catch (err) {
      console.error('Error fetching users:', err);
      setError('Failed to fetch user data. Please check your connection to the API server.');
    } finally {
      setLoading(false);
    }
  };

  // Show create modal
  const showCreateModal = () => {
    setEditingUser(null);
    form.resetFields();
    setModalVisible(true);
  };

  // Show edit modal
  const showEditModal = (user: User) => {
    setEditingUser(user);
    form.setFieldsValue({
      username: user.username,
      email: user.email,
      full_name: user.full_name,
      is_active: user.is_active,
      role: user.role
    });
    setModalVisible(true);
  };

  // Show password change modal
  const showPasswordModal = (user: User) => {
    setChangingPasswordUser(user);
    passwordForm.resetFields();
    setPasswordModalVisible(true);
  };

  // Handle create/update user
  const handleSubmit = async (values: any) => {
    try {
      if (editingUser) {
        // Update user
        const updateData: UpdateUserData = {
          email: values.email,
          full_name: values.full_name,
          is_active: values.is_active,
          role: values.role
        };
        await userService.updateUser(editingUser.id, updateData);
        message.success('User updated successfully');
      } else {
        // Create user
        const createData: CreateUserData = {
          username: values.username,
          email: values.email,
          full_name: values.full_name,
          password: values.password,
          is_active: values.is_active,
          role: values.role
        };
        await userService.createUser(createData);
        message.success('User created successfully');
      }
      
      setModalVisible(false);
      fetchUsers();
    } catch (err: any) {
      console.error('Error saving user:', err);
      message.error(err.response?.data?.detail || 'Failed to save user');
    }
  };

  // Handle password change
  const handlePasswordChange = async (values: any) => {
    try {
      if (changingPasswordUser) {
        const passwordData: ChangePasswordData = {
          password: values.password
        };
        await userService.changePassword(changingPasswordUser.id, passwordData);
        message.success('Password changed successfully');
        setPasswordModalVisible(false);
      }
    } catch (err: any) {
      console.error('Error changing password:', err);
      message.error(err.response?.data?.detail || 'Failed to change password');
    }
  };

  // Handle delete
  const handleDelete = async (id: number) => {
    try {
      await userService.deleteUser(id);
      message.success('User deleted successfully');
      fetchUsers();
    } catch (err: any) {
      console.error('Error deleting user:', err);
      message.error(err.response?.data?.detail || 'Failed to delete user');
    }
  };

  // Handle toggle active status
  const handleToggleActive = async (id: number, is_active: boolean) => {
    try {
      await userService.toggleActiveStatus(id);
      message.success(`User ${!is_active ? 'activated' : 'deactivated'} successfully`);
      fetchUsers();
    } catch (err: any) {
      console.error('Error toggling user status:', err);
      message.error(err.response?.data?.detail || 'Failed to update user status');
    }
  };

  // Table columns
  const columns: ColumnType<User>[] = [
    {
      title: 'User',
      key: 'user',
      render: (_, record: User) => (
        <Space>
          <Avatar icon={<UserOutlined />} />
          <div>
            <div>
              <strong>{record.full_name}</strong>
              {record.role === 'admin' && (
                <Tooltip title="Administrator">
                  <CrownOutlined style={{ color: '#faad14', marginLeft: 8 }} />
                </Tooltip>
              )}
            </div>
            <Text type="secondary" style={{ fontSize: '12px' }}>
              @{record.username}
            </Text>
          </div>
        </Space>
      ),
    },
    {
      title: 'Email',
      dataIndex: 'email',
      key: 'email',
    },
    {
      title: 'Status',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (is_active: boolean) => (
        <Tag color={is_active ? 'success' : 'error'}>
          {is_active ? 'Active' : 'Inactive'}
        </Tag>
      ),
    },
    {
      title: 'Role',
      dataIndex: 'role',
      key: 'role',
      render: (role: string) => (
        <Tag color={role === 'admin' ? 'gold' : 'blue'}>
          {role === 'admin' ? 'Administrator' : 'User'}
        </Tag>
      ),
    },
    {
      title: 'Last Login',
      dataIndex: 'last_login',
      key: 'last_login',
      render: (date: string) => date ? dayjs(date).format('YYYY-MM-DD HH:mm') : 'Never',
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => dayjs(date).format('YYYY-MM-DD'),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record: User) => (
        <Space>
          <Tooltip title="Edit user">
            <Button
              type="text"
              icon={<EditOutlined />}
              size="small"
              onClick={() => showEditModal(record)}
            />
          </Tooltip>
          <Tooltip title="Change password">
            <Button
              type="text"
              icon={<KeyOutlined />}
              size="small"
              onClick={() => showPasswordModal(record)}
            />
          </Tooltip>
          <Tooltip title={record.is_active ? 'Deactivate user' : 'Activate user'}>
            <Button
              type="text"
              icon={record.is_active ? <LockOutlined /> : <UnlockOutlined />}
              size="small"
              onClick={() => handleToggleActive(record.id, record.is_active)}
            />
          </Tooltip>
          {record.username !== 'admin' && (
            <Popconfirm
              title="Are you sure you want to delete this user?"
              onConfirm={() => handleDelete(record.id)}
              okText="Yes"
              cancelText="No"
            >
              <Tooltip title="Delete user">
                <Button
                  type="text"
                  icon={<DeleteOutlined />}
                  size="small"
                  danger
                />
              </Tooltip>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div className="users-container">
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>
          <UserOutlined /> User Management
        </Title>
        <Text>Manage system users and their permissions</Text>
      </div>

      <Card>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
          <Title level={4}>
            <UserOutlined /> Users
            <Badge count={users.length} showZero style={{ marginLeft: 8 }} />
          </Title>
          <Space>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={showCreateModal}
            >
              Add User
            </Button>
            <Button
              icon={<SyncOutlined spin={loading} />}
              onClick={fetchUsers}
              disabled={loading}
            >
              Refresh
            </Button>
          </Space>
        </div>

        {error && (
          <div style={{ marginBottom: 16 }}>
            <Text type="danger">{error}</Text>
          </div>
        )}

        <Table
          dataSource={users}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
        />
      </Card>

      {/* User Form Modal */}
      <Modal
        title={
          <Title level={4}>
            <UserOutlined /> {editingUser ? 'Edit User' : 'Add New User'}
          </Title>
        }
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={[
          <Button key="cancel" onClick={() => setModalVisible(false)}>
            Cancel
          </Button>,
          <Button key="submit" type="primary" onClick={() => form.submit()}>
            {editingUser ? 'Update' : 'Create'}
          </Button>
        ]}
        width={600}
        destroyOnClose={true}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="username"
                label="Username"
                rules={[
                  { required: true, message: 'Please enter username' },
                  { min: 3, message: 'Username must be at least 3 characters' }
                ]}
              >
                <Input 
                  placeholder="Enter username" 
                  disabled={!!editingUser} // Disable username editing
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="email"
                label="Email"
                rules={[
                  { required: true, message: 'Please enter email' },
                  { type: 'email', message: 'Please enter a valid email' }
                ]}
              >
                <Input placeholder="Enter email address" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="full_name"
            label="Full Name"
            rules={[{ required: true, message: 'Please enter full name' }]}
          >
            <Input placeholder="Enter full name" />
          </Form.Item>

          {!editingUser && (
            <Form.Item
              name="password"
              label="Password"
              rules={[
                { required: true, message: 'Please enter password' },
                { min: 6, message: 'Password must be at least 6 characters' }
              ]}
            >
              <Password placeholder="Enter password" />
            </Form.Item>
          )}

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="is_active"
                label="Active"
                valuePropName="checked"
                initialValue={true}
              >
                <Switch />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="role"
                label="Role"
                initialValue="user"
              >
                <Select>
                  <Option value="user">User</Option>
                  <Option value="admin">Administrator</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>

      {/* Password Change Modal */}
      <Modal
        title={
          <Title level={4}>
            <KeyOutlined /> Change Password
          </Title>
        }
        open={passwordModalVisible}
        onCancel={() => setPasswordModalVisible(false)}
        footer={[
          <Button key="cancel" onClick={() => setPasswordModalVisible(false)}>
            Cancel
          </Button>,
          <Button key="submit" type="primary" onClick={() => passwordForm.submit()}>
            Change Password
          </Button>
        ]}
        width={400}
        destroyOnClose={true}
      >
        <Form
          form={passwordForm}
          layout="vertical"
          onFinish={handlePasswordChange}
        >
          <div style={{ marginBottom: 16 }}>
            <Text>
              Changing password for: <strong>{changingPasswordUser?.full_name}</strong>
            </Text>
          </div>
          
          <Form.Item
            name="password"
            label="New Password"
            rules={[
              { required: true, message: 'Please enter new password' },
              { min: 6, message: 'Password must be at least 6 characters' }
            ]}
          >
            <Password placeholder="Enter new password" />
          </Form.Item>

          <Form.Item
            name="confirmPassword"
            label="Confirm Password"
            dependencies={['password']}
            rules={[
              { required: true, message: 'Please confirm the password' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('password') === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error('Passwords do not match'));
                },
              }),
            ]}
          >
            <Password placeholder="Confirm new password" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Users; 