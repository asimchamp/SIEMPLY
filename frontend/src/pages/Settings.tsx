import { useState, useEffect } from 'react';
import {
  Card,
  Typography,
  Form,
  Input,
  Button,
  Select,
  Switch,
  Divider,
  message,
  Alert,
  Row,
  Col,
  Space,
  InputNumber
} from 'antd';
import {
  SettingOutlined,
  SaveOutlined,
  ApiOutlined,
  KeyOutlined,
  UserOutlined
} from '@ant-design/icons';
import { settingsService, AppSettings } from '../services/api';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;

const Settings: React.FC = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState<boolean>(false);
  const [settings, setSettings] = useState<AppSettings>(settingsService.getSettings());

  // Load settings on mount
  useEffect(() => {
    try {
      const currentSettings = settingsService.getSettings();
      setSettings(currentSettings);
      form.setFieldsValue(currentSettings);
    } catch (error) {
      console.error('Failed to load settings:', error);
      message.error('Failed to load settings');
    }
  }, [form]);

  // Save settings
  const handleSave = async (values: AppSettings) => {
    try {
      setLoading(true);
      settingsService.saveSettings({
        ...settings,
        ...values
      });
      message.success('Settings saved successfully');
      setSettings({
        ...settings,
        ...values
      });
    } catch (error) {
      console.error('Failed to save settings:', error);
      message.error('Failed to save settings');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="settings-container">
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>
          <SettingOutlined /> Settings
        </Title>
        <Text>Configure application settings</Text>
      </div>

      <Card>
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSave}
          initialValues={settings}
        >
          <Divider orientation="left">API Configuration</Divider>
          <Row gutter={16}>
            <Col span={18}>
              <Form.Item
                name="apiUrl"
                label="API URL"
                rules={[
                  { required: true, message: 'Please enter API URL' },
                  { type: 'url', message: 'Please enter a valid URL' }
                ]}
                tooltip="The URL of the SIEMply API server"
              >
                <Input 
                  prefix={<ApiOutlined />}
                  placeholder="http://localhost:5050"
                />
              </Form.Item>
            </Col>
          </Row>

          <Divider orientation="left">Default Versions</Divider>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="defaultSplunkVersion"
                label="Default Splunk Version"
                rules={[{ required: true, message: 'Please enter default Splunk version' }]}
              >
                <Select placeholder="Select Splunk version">
                  <Option value="9.1.1">9.1.1</Option>
                  <Option value="9.0.5">9.0.5</Option>
                  <Option value="8.2.9">8.2.9</Option>
                  <Option value="8.1.5">8.1.5</Option>
                  <Option value="7.3.9">7.3.9</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="defaultCriblVersion"
                label="Default Cribl Version"
                rules={[{ required: true, message: 'Please enter default Cribl version' }]}
              >
                <Select placeholder="Select Cribl version">
                  <Option value="3.4.1">3.4.1</Option>
                  <Option value="3.3.0">3.3.0</Option>
                  <Option value="3.0.5">3.0.5</Option>
                  <Option value="2.4.5">2.4.5</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
          
          <Form.Item
            name="defaultInstallDir"
            label="Default Installation Directory"
            rules={[{ required: true, message: 'Please enter default installation directory' }]}
          >
            <Input placeholder="/opt" />
          </Form.Item>

          <Divider orientation="left">SSH Configuration</Divider>
          <Form.Item
            name="sshKeyPath"
            label="Default SSH Key Path"
            tooltip="Path to the default SSH private key for connecting to hosts"
          >
            <Input 
              prefix={<KeyOutlined />}
              placeholder="/path/to/id_rsa"
            />
          </Form.Item>

          <Divider orientation="left">UI Settings</Divider>
          <Form.Item
            name="theme"
            label="Theme"
            tooltip="Select light or dark theme for the UI"
          >
            <Select placeholder="Select theme">
              <Option value="light">Light</Option>
              <Option value="dark">Dark</Option>
            </Select>
          </Form.Item>

          <Form.Item>
            <Space>
              <Button 
                type="primary" 
                htmlType="submit"
                icon={<SaveOutlined />}
                loading={loading}
              >
                Save Settings
              </Button>
              <Button 
                onClick={() => form.resetFields()}
              >
                Reset
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>

      <Card style={{ marginTop: 16 }}>
        <Alert
          message="Local Storage"
          description="Settings are stored in your browser's local storage. Clearing browser data will reset these settings."
          type="info"
          showIcon
        />
      </Card>
    </div>
  );
};

export default Settings; 