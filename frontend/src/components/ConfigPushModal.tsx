import React, { useState, useEffect } from 'react';
import { 
  Modal, 
  Form, 
  Select, 
  Button, 
  Upload, 
  message, 
  Divider, 
  Space, 
  Alert, 
  Typography,
  Input
} from 'antd';
import { 
  InboxOutlined,
  FileTextOutlined,
  CloudUploadOutlined
} from '@ant-design/icons';
import { RcFile } from 'antd/lib/upload';
import { hostService, Host } from '../services/api';
import api from '../services/api';

const { Option } = Select;
const { Dragger } = Upload;

interface ConfigPushModalProps {
  visible: boolean;
  onClose: () => void;
}

const ConfigPushModal: React.FC<ConfigPushModalProps> = ({ visible, onClose }) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [hosts, setHosts] = useState<Host[]>([]);
  const [selectedProduct, setSelectedProduct] = useState<'splunk' | 'cribl'>('splunk');
  const [fileList, setFileList] = useState<RcFile[]>([]);
  const [targetDir, setTargetDir] = useState<string>('');
  const [uploadResults, setUploadResults] = useState<any[] | null>(null);

  // Set default target directory based on selected product
  useEffect(() => {
    if (selectedProduct === 'splunk') {
      setTargetDir('/opt/splunk/etc/system/local');
    } else {
      setTargetDir('/opt/cribl/local');
    }
  }, [selectedProduct]);

  // Load hosts when the modal becomes visible
  useEffect(() => {
    if (visible) {
      fetchHosts();
      resetForm();
    }
  }, [visible]);

  // Fetch hosts with Splunk or Cribl roles
  const fetchHosts = async () => {
    try {
      const allHosts = await hostService.getAllHosts();
      
      // Filter hosts with either Splunk or Cribl roles
      const filteredHosts = allHosts.filter(host => {
        const hasRole = (role: string) => host.roles.includes(role);
        return hasRole('splunk_uf') || 
               hasRole('splunk_indexer') || 
               hasRole('splunk_search_head') ||
               hasRole('cribl_leader') || 
               hasRole('cribl_worker');
      });
      
      setHosts(filteredHosts);
    } catch (error) {
      console.error('Failed to fetch hosts:', error);
      message.error('Failed to load host data');
    }
  };

  // Reset form state
  const resetForm = () => {
    form.resetFields();
    setFileList([]);
    setUploadResults(null);
    setSelectedProduct('splunk');
    setTargetDir('/opt/splunk/etc/system/local');
  };

  // Handle file changes in upload component
  const handleFileChange = (info: any) => {
    const newFileList = [...info.fileList].map(file => file.originFileObj);
    setFileList(newFileList);
  };

  // Handle product selection change
  const handleProductChange = (value: 'splunk' | 'cribl') => {
    setSelectedProduct(value);
    
    // Update target directory based on product
    if (value === 'splunk') {
      setTargetDir('/opt/splunk/etc/system/local');
    } else {
      setTargetDir('/opt/cribl/local');
    }
  };

  // Filter hosts based on selected product
  const getFilteredHosts = () => {
    if (!hosts) return [];
    
    return hosts.filter(host => {
      if (selectedProduct === 'splunk') {
        return host.roles.some(role => role.includes('splunk'));
      } else {
        return host.roles.some(role => role.includes('cribl'));
      }
    });
  };

  // Submit form and upload files
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      
      if (fileList.length === 0) {
        message.error('Please select at least one configuration file to upload');
        return;
      }
      
      setLoading(true);
      
      // Create form data for file upload
      const formData = new FormData();
      fileList.forEach(file => {
        formData.append('files', file);
      });
      
      // Add target directory as query parameter
      formData.append('target_dir', values.targetDir);
      
      // Call API endpoint based on product type
      const endpoint = `/configs/push/${selectedProduct}/${values.hostId}`;
      const response = await api.post(endpoint, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      // Show results
      setUploadResults(response.data.results);
      
      message.success('Configuration files uploaded successfully');
    } catch (error) {
      console.error('Failed to upload config files:', error);
      message.error('Failed to upload configuration files');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      title="Push Configuration Files"
      open={visible}
      onCancel={onClose}
      width={700}
      footer={null}
    >
      <Form
        form={form}
        layout="vertical"
        initialValues={{
          product: "splunk",
          targetDir: targetDir
        }}
      >
        <Form.Item
          name="product"
          label="Product"
          rules={[{ required: true, message: 'Please select a product' }]}
        >
          <Select 
            onChange={(value) => handleProductChange(value as 'splunk' | 'cribl')}
            value={selectedProduct}
          >
            <Option value="splunk">Splunk</Option>
            <Option value="cribl">Cribl</Option>
          </Select>
        </Form.Item>
        
        <Form.Item
          name="hostId"
          label="Target Host"
          rules={[{ required: true, message: 'Please select a host' }]}
        >
          <Select
            placeholder="Select host for configuration push"
            showSearch
            optionFilterProp="children"
          >
            {getFilteredHosts().map(host => (
              <Option key={host.id} value={host.id}>
                {host.hostname} ({host.ip_address})
              </Option>
            ))}
          </Select>
        </Form.Item>
        
        <Form.Item
          name="targetDir"
          label="Target Directory"
          rules={[{ required: true, message: 'Please specify target directory' }]}
        >
          <Input 
            value={targetDir}
            onChange={(e) => setTargetDir(e.target.value)}
          />
        </Form.Item>
        
        <Form.Item
          name="files"
          label="Configuration Files"
        >
          <Dragger
            name="files"
            multiple={true}
            beforeUpload={() => false}
            onChange={handleFileChange}
            fileList={fileList as any}
          >
            <p className="ant-upload-drag-icon">
              <InboxOutlined />
            </p>
            <p className="ant-upload-text">Click or drag file to this area to upload</p>
            <p className="ant-upload-hint">
              {selectedProduct === 'splunk' 
                ? 'Upload .conf files for Splunk configuration' 
                : 'Upload .yml files for Cribl configuration'}
            </p>
          </Dragger>
        </Form.Item>

        <Form.Item>
          <div style={{ textAlign: 'right' }}>
            <Space>
              <Button onClick={onClose}>
                Cancel
              </Button>
              <Button
                type="primary"
                icon={<CloudUploadOutlined />}
                loading={loading}
                onClick={handleSubmit}
              >
                Upload Configuration
              </Button>
            </Space>
          </div>
        </Form.Item>
      </Form>
      
      {uploadResults && (
        <>
          <Divider>Upload Results</Divider>
          
          {uploadResults.map((result, index) => (
            <Alert
              key={index}
              message={result.filename}
              description={result.message}
              type={result.status === 'success' ? 'success' : result.status === 'warning' ? 'warning' : 'error'}
              showIcon
              style={{ marginBottom: 8 }}
              icon={<FileTextOutlined />}
            />
          ))}
        </>
      )}
    </Modal>
  );
};

export default ConfigPushModal; 