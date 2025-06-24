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
  LogoutOutlined
} from '@ant-design/icons';
import { useAuth } from '../services/authContext';

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

  const menuItems = [
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
      key: '/jobs',
      icon: <HistoryOutlined />,
      label: 'Job History',
    },
    {
      key: '/settings',
      icon: <SettingOutlined />,
      label: 'Settings',
    },
  ];

  const handleMenuClick = (path: string) => {
    navigate(path);
  };

  const userMenuItems = [
    {
      key: 'profile',
      label: 'Profile',
      icon: <UserOutlined />,
    },
    {
      key: 'logout',
      label: 'Logout',
      icon: <LogoutOutlined />,
      onClick: handleLogout,
    },
  ];

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
          items={menuItems}
          onClick={({ key }) => handleMenuClick(key)}
        />

        <Divider />
        
        {!collapsed && (
          <div style={{ padding: '0 16px', marginBottom: 8 }}>
            <Text type="secondary">Theme:</Text>
            <div style={{ display: 'flex', alignItems: 'center', marginTop: 8 }}>
              <Text>Light</Text>
              <Switch 
                checked={darkMode} 
                onChange={toggleDarkMode} 
                style={{ margin: '0 8px' }} 
              />
              <Text>Dark</Text>
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
              <Text style={{ marginRight: 16 }}>
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