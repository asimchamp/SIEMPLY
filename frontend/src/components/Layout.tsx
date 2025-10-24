import React, { ReactNode, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { 
  Layout as AntLayout, 
  Menu, 
  Typography, 
  Divider,
  Switch,
  Button,
  Avatar,
  Dropdown
} from 'antd';
import {
  DashboardOutlined,
  DesktopOutlined,
  HistoryOutlined,
  SettingOutlined,
  MenuUnfoldOutlined,
  MenuFoldOutlined,
  UserOutlined,
  LogoutOutlined,
  LockOutlined,
  AppstoreOutlined,
  PlusOutlined,
  CloudDownloadOutlined,
  DatabaseOutlined,
  BookOutlined,
  FileTextOutlined,
  PlayCircleOutlined,
  CodeOutlined,
  BarChartOutlined,
  CloudOutlined,
  SecurityScanOutlined,
  EditOutlined,
  NodeIndexOutlined
} from '@ant-design/icons';
import { useAuth } from '../services/authContext';
import type { MenuProps } from 'antd';

const { Header, Sider, Content } = AntLayout;
const { Title, Text } = Typography;

// Props interface
interface LayoutProps {
  children: ReactNode;
  darkMode: boolean;
  toggleDarkMode: () => void;
}

const AppLayout: React.FC<LayoutProps> = ({ children, darkMode, toggleDarkMode }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);
  const { user, logout } = useAuth();

  const handleLogout = () => {
    logout();
  };

  // Define menu items with submenu for Jobs and Database
  const menuItems: MenuProps['items'] = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: 'Dashboard',
    },
    {
      key: '/hosts',
      icon: <DesktopOutlined />,
      label: 'Host Management',
    },
    {
      key: 'jobs',
      icon: <AppstoreOutlined />,
      label: 'Jobs',
      children: [
        {
          key: '/jobs/new',
          icon: <CloudDownloadOutlined />,
          label: 'New Job',
        },
        {
          key: '/jobs',
          icon: <HistoryOutlined />,
          label: 'Job History',
        },
      ],
    },
    {
      key: '/build',
      icon: <NodeIndexOutlined />,
      label: 'Build',
    },

    {
      key: 'playbooks',
      icon: <PlayCircleOutlined />,
      label: 'Playbooks',
      children: [
        {
          key: '/playbooks',
          icon: <FileTextOutlined />,
          label: 'Playbook List',
        },
        {
          key: '/playbook-builder',
          icon: <CodeOutlined />,
          label: 'Playbook Builder',
        },
      ],
    },
    {
      key: '/executions',
      icon: <BarChartOutlined />,
      label: 'Executions',
    },
    {
      key: 'splunk-acs',
      icon: <CloudOutlined />,
      label: 'Splunk ACS',
      children: [
        {
          key: '/splunk-acs/dashboard',
          icon: <DashboardOutlined />,
          label: 'ACS Dashboard',
        },
        {
          key: '/splunk-acs/configs',
          icon: <SettingOutlined />,
          label: 'Configurations',
        },
        {
          key: '/splunk-acs/ip-allow-lists',
          icon: <SecurityScanOutlined />,
          label: 'IP Allow Lists',
        },
        {
          key: '/splunk-acs/changes',
          icon: <EditOutlined />,
          label: 'Change Requests',
        },
      ],
    },
    {
      key: 'database',
      icon: <DatabaseOutlined />,
      label: 'Database',
      children: [
        {
          key: '/database/packages',
          icon: <AppstoreOutlined />,
          label: 'Software Package Database',
        },
        {
          key: '/database/users',
          icon: <UserOutlined />,
          label: 'Users',
        },
        {
          key: '/database/files',
          icon: <FileTextOutlined />,
          label: 'Files',
        },
      ],
    },
    {
      key: '/settings',
      icon: <SettingOutlined />,
      label: 'Settings',
    },
  ];

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key);
  };

  const userMenuItems = [
    {
      key: 'profile',
      label: 'Profile',
      icon: <UserOutlined />,
    },
    {
      key: 'change-password',
      label: 'Change Password',
      icon: <LockOutlined />,
      onClick: () => navigate('/change-password'),
    },
    {
      key: 'logout',
      label: 'Logout',
      icon: <LogoutOutlined />,
      onClick: handleLogout,
    },
  ];

  // Determine which keys should be open based on current path
  const getOpenKeys = () => {
    if (location.pathname.startsWith('/jobs')) {
      return ['jobs'];
    }
    if (location.pathname.startsWith('/database')) {
      return ['database'];
    }
    if (location.pathname.startsWith('/playbooks') || location.pathname.startsWith('/playbook-builder')) {
      return ['playbooks'];
    }
    if (location.pathname.startsWith('/splunk-acs')) {
      return ['splunk-acs'];
    }
    return [];
  };

  return (
    <AntLayout style={{ minHeight: '100vh' }}>
      <Sider 
        collapsible
        collapsed={collapsed}
        onCollapse={(value) => setCollapsed(value)}
        theme={darkMode ? 'dark' : 'light'}
        style={{ 
          overflow: 'auto',
          height: '100vh',
          position: 'fixed',
          left: 0,
          top: 0,
          bottom: 0,
        }}
      >
        <div style={{ 
          height: 32, 
          margin: 16, 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: collapsed ? 'center' : 'flex-start'
        }}>
          <Title level={4} style={{ margin: 0, color: darkMode ? 'white' : undefined }}>
            <span style={{ color: '#1890ff' }}>SIEM</span>
            {!collapsed && 'ply'}
          </Title>
        </div>
        
        <Menu
          theme={darkMode ? 'dark' : 'light'}
          mode="inline"
          selectedKeys={[location.pathname]}
          defaultOpenKeys={getOpenKeys()}
          items={menuItems}
          onClick={handleMenuClick}
        />

        <Divider />
        
        {!collapsed && (
          <div style={{ padding: '0 16px', marginBottom: 8 }}>
            <Text type="secondary">Theme:</Text>
            <div style={{ display: 'flex', alignItems: 'center', marginTop: 8 }}>
              <Text style={{ color: darkMode ? 'white' : undefined }}>Light</Text>
              <Switch 
                checked={darkMode} 
                onChange={toggleDarkMode} 
                style={{ margin: '0 8px' }} 
              />
              <Text style={{ color: darkMode ? 'white' : undefined }}>Dark</Text>
            </div>
          </div>
        )}
      </Sider>

      <AntLayout style={{ marginLeft: collapsed ? 80 : 200 }}>
        <Header style={{ 
          padding: '0 16px', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between',
          position: 'sticky',
          top: 0,
          zIndex: 1,
          width: '100%',
          background: darkMode ? '#141414' : '#fff',
          boxShadow: '0 1px 4px rgba(0,21,41,.08)'
        }}>
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
          />

          <div style={{ display: 'flex', alignItems: 'center' }}>
            {!collapsed && (
              <Text style={{ 
                marginRight: 16, 
                color: darkMode ? 'white' : undefined 
              }}>
                SIEM Installation & Management
              </Text>
            )}
            
            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
              <Button type="text" style={{ height: 48, marginLeft: 8 }}>
                <Avatar icon={<UserOutlined />} style={{ marginRight: 8 }} />
                {user?.username}
              </Button>
            </Dropdown>
          </div>
        </Header>

        <Content style={{ 
          margin: '24px 16px', 
          padding: 24, 
          background: darkMode ? '#141414' : '#fff',
          borderRadius: 4,
          minHeight: 280
        }}>
          {children}
        </Content>
      </AntLayout>
    </AntLayout>
  );
};

export default AppLayout; 