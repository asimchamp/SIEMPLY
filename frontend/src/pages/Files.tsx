import React, { useState, useEffect, useRef } from 'react';
import {
  Card,
  Button,
  Input,
  Modal,
  message,
  Upload,
  Dropdown,
  Menu,
  Space,
  Typography,
  Breadcrumb,
  Tooltip,
  Popconfirm,
  Spin,
  Empty,
  Divider,
  Row,
  Col,
  Tag,
  Select,
  Form,
  Tabs
} from 'antd';
import {
  UploadOutlined,
  FolderAddOutlined,
  SearchOutlined,
  MoreOutlined,
  DownloadOutlined,
  DeleteOutlined,
  EditOutlined,
  EyeOutlined,
  FileTextOutlined,
  FolderOutlined,
  ArrowLeftOutlined,
  HomeOutlined,
  ReloadOutlined,
  FileImageOutlined,
  FilePdfOutlined,
  FileZipOutlined,
  CodeOutlined,
  PlusOutlined,
  SaveOutlined,
  CloseOutlined,
  UserOutlined,
  ClusterOutlined,
  CloudOutlined,
  DatabaseOutlined,
  ThunderboltOutlined,
  FireOutlined,
  KeyOutlined,
  MonitorOutlined
} from '@ant-design/icons';
import { filesService, FileItem } from '../services/filesService';
import { workflowsService } from '../services/workflowsService';
import dayjs from 'dayjs';
import './Files.css';

const { Title, Text } = Typography;
const { Search } = Input;
const { Option } = Select;
const { TextArea } = Input;

const Files: React.FC = () => {
  const [files, setFiles] = useState<FileItem[]>([]);
  const [clusters, setClusters] = useState<FileItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [currentPath, setCurrentPath] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<FileItem[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  
  // Modal states
  const [createFolderModalVisible, setCreateFolderModalVisible] = useState(false);
  const [createFileModalVisible, setCreateFileModalVisible] = useState(false);
  const [renameModalVisible, setRenameModalVisible] = useState(false);
  const [previewModalVisible, setPreviewModalVisible] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [selectedFile, setSelectedFile] = useState<FileItem | null>(null);
  const [newFolderName, setNewFolderName] = useState('');
  const [newFileName, setNewFileName] = useState('');
  const [newFileContent, setNewFileContent] = useState('');
  const [newFileExtension, setNewFileExtension] = useState('.txt');
  const [fileContent, setFileContent] = useState('');
  const [isEditing, setIsEditing] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  
  // Upload states
  const [uploading, setUploading] = useState(false);
  const uploadRef = useRef<any>(null);

  // Load files on component mount and path change
  useEffect(() => {
    loadFiles();
  }, [currentPath]);

  // Load clusters on component mount
  useEffect(() => {
    loadClusters();
  }, []);

  const loadFiles = async () => {
    try {
      setLoading(true);
      const fileList = await filesService.listFiles(currentPath);
      
      // Separate clusters from user files
      const clusterItems = fileList.filter(item => item.name === 'clusters' && item.is_dir);
      const userItems = fileList.filter(item => item.name !== 'clusters');
      
      setClusters(clusterItems);
      setFiles(userItems);
    } catch (error: any) {
      message.error('Failed to load files: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const loadClusters = async () => {
    try {
      const clusterList = await filesService.listFiles('clusters');
      setClusters(clusterList);
    } catch (error: any) {
      console.error('Failed to load clusters:', error);
    }
  };

  const handleUpload = async (file: File) => {
    try {
      setUploading(true);
      await filesService.uploadFile(file, currentPath);
      message.success('File uploaded successfully');
      loadFiles();
    } catch (error: any) {
      message.error('Failed to upload file: ' + (error.response?.data?.detail || error.message));
    } finally {
      setUploading(false);
    }
  };

  const handleCreateFolder = async () => {
    if (!newFolderName.trim()) {
      message.error('Please enter a folder name');
      return;
    }

    try {
      await filesService.createFolder(newFolderName.trim(), currentPath);
      message.success('Folder created successfully');
      setCreateFolderModalVisible(false);
      setNewFolderName('');
      loadFiles();
    } catch (error: any) {
      message.error('Failed to create folder: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleDelete = async (file: FileItem) => {
    try {
      await filesService.deleteItem(file.path);
      message.success(`${file.is_dir ? 'Folder' : 'File'} deleted successfully`);
      loadFiles();
    } catch (error: any) {
      message.error('Failed to delete item: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleRename = async () => {
    if (!newFileName.trim() || !selectedFile) {
      message.error('Please enter a new name');
      return;
    }

    try {
      await filesService.renameItem(selectedFile.path, newFileName.trim());
      message.success('Item renamed successfully');
      setRenameModalVisible(false);
      setNewFileName('');
      setSelectedFile(null);
      loadFiles();
    } catch (error: any) {
      message.error('Failed to rename item: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleDownload = async (file: FileItem) => {
    try {
      const blob = await filesService.downloadFile(file.path);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = file.name;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      message.success('File downloaded successfully');
    } catch (error: any) {
      message.error('Failed to download file: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleCreateFile = async () => {
    if (!newFileName.trim()) {
      message.error('Please enter a file name');
      return;
    }

    try {
      const fullFileName = newFileName.trim() + newFileExtension;
      await filesService.createFile(fullFileName, newFileContent, currentPath);
      message.success('File created successfully');
      setCreateFileModalVisible(false);
      setNewFileName('');
      setNewFileContent('');
      setNewFileExtension('.txt');
      loadFiles();
    } catch (error: any) {
      message.error('Failed to create file: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handlePreviewFile = async (file: FileItem) => {
    try {
      const content = await filesService.getFileContent(file.path);
      setFileContent(content);
      setSelectedFile(file);
      setPreviewModalVisible(true);
    } catch (error: any) {
      message.error('Failed to load file content: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleEditFile = async (file: FileItem) => {
    try {
      const content = await filesService.getFileContent(file.path);
      setFileContent(content);
      setSelectedFile(file);
      setEditModalVisible(true);
      setIsEditing(true);
      setHasUnsavedChanges(false);
    } catch (error: any) {
      message.error('Failed to load file content: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleSaveFile = async () => {
    if (!selectedFile) return;

    try {
      await filesService.updateFileContent(selectedFile.path, fileContent);
      message.success('File saved successfully');
      setEditModalVisible(false);
      setIsEditing(false);
      setHasUnsavedChanges(false);
      setSelectedFile(null);
      setFileContent('');
    } catch (error: any) {
      message.error('Failed to save file: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleContentChange = (value: string) => {
    setFileContent(value);
    setHasUnsavedChanges(true);
  };

  const handleSearch = async (query: string) => {
    if (!query.trim()) {
      setSearchResults([]);
      setIsSearching(false);
      return;
    }

    try {
      setIsSearching(true);
      const results = await filesService.searchFiles(query, currentPath);
      setSearchResults(results);
    } catch (error: any) {
      message.error('Failed to search files: ' + (error.response?.data?.detail || error.message));
    } finally {
      setIsSearching(false);
    }
  };

  const navigateToFolder = (folder: FileItem) => {
    const newPath = currentPath ? `${currentPath}/${folder.name}` : folder.name;
    setCurrentPath(newPath);
  };

  const navigateToCluster = (cluster: FileItem) => {
    // For clusters, navigate to the clusters/{cluster_name} path
    const clusterPath = `clusters/${cluster.name}`;
    setCurrentPath(clusterPath);
  };

  // Check if current path is inside a cluster
  const isInsideCluster = () => {
    return currentPath.startsWith('clusters/') && currentPath.split('/').length >= 2;
  };

  // Get current cluster name
  const getCurrentClusterName = () => {
    if (isInsideCluster()) {
      return currentPath.split('/')[1];
    }
    return null;
  };

  const navigateBack = () => {
    const pathParts = currentPath.split('/');
    pathParts.pop();
    setCurrentPath(pathParts.join('/'));
  };

  const navigateToRoot = () => {
    setCurrentPath('');
  };

  const getBreadcrumbItems = () => {
    const items = [
      {
        title: (
          <Button 
            type="text" 
            icon={<HomeOutlined />} 
            onClick={navigateToRoot}
            style={{ padding: 0, height: 'auto', color: '#1890ff' }}
          >
            Files
          </Button>
        )
      }
    ];

    if (currentPath) {
      const pathParts = currentPath.split('/');
      let currentPathBuilder = '';
      
      pathParts.forEach((part, index) => {
        currentPathBuilder += (index > 0 ? '/' : '') + part;
        
        // Special handling for cluster paths
        let displayName = part;
        if (currentPath.startsWith('clusters/')) {
          if (index === 1) {
            displayName = 'Clusters';
          } else if (index === 2) {
                      // Component names
          const componentNames: Record<string, string> = {
            'cm': 'Cluster Master',
            'deployer': 'Deployer',
            'sh': 'Search Head',
            'ds': 'Deployment Server',
            'uf': 'Universal Forwarder',
            'hf': 'Heavy Forwarder',
            'lm': 'License Master',
            'mc': 'Monitoring Console'
          };
          displayName = componentNames[part] || part;
          } else if (index === 3) {
            // Config folder names
            displayName = part === 'default' ? 'Default Config' : 'Local Config';
          }
        }
        
        items.push({
          title: (
            <Button 
              type="text" 
              onClick={() => setCurrentPath(currentPathBuilder)}
              style={{ padding: 0, height: 'auto', color: '#1890ff' }}
            >
              {displayName}
            </Button>
          )
        });
      });
    }

    return items;
  };

  const getFileIcon = (file: FileItem) => {
    if (file.is_dir) return <FolderOutlined style={{ fontSize: '24px', color: '#1890ff' }} />;
    
    const extension = file.extension.toLowerCase();
    
    // Text files
    if (['.txt', '.md', '.log'].includes(extension)) return <FileTextOutlined style={{ fontSize: '24px', color: '#52c41a' }} />;
    if (['.py', '.js', '.ts', '.sh', '.bash'].includes(extension)) return <CodeOutlined style={{ fontSize: '24px', color: '#722ed1' }} />;
    if (['.json', '.xml', '.yaml', '.yml'].includes(extension)) return <FileTextOutlined style={{ fontSize: '24px', color: '#fa8c16' }} />;
    if (['.sql'].includes(extension)) return <FileTextOutlined style={{ fontSize: '24px', color: '#13c2c2' }} />;
    
    // Documents
    if (['.pdf'].includes(extension)) return <FilePdfOutlined style={{ fontSize: '24px', color: '#f5222d' }} />;
    if (['.docx', '.doc'].includes(extension)) return <FileTextOutlined style={{ fontSize: '24px', color: '#1890ff' }} />;
    if (['.xlsx', '.xls'].includes(extension)) return <FileTextOutlined style={{ fontSize: '24px', color: '#52c41a' }} />;
    if (['.pptx', '.ppt'].includes(extension)) return <FileTextOutlined style={{ fontSize: '24px', color: '#fa8c16' }} />;
    
    // Images
    if (['.jpg', '.jpeg', '.png', '.gif', '.svg', '.ico'].includes(extension)) return <FileImageOutlined style={{ fontSize: '24px', color: '#eb2f96' }} />;
    
    // Archives
    if (['.zip', '.tar', '.gz', '.tgz', '.rar'].includes(extension)) return <FileZipOutlined style={{ fontSize: '24px', color: '#faad14' }} />;
    
    return <FileTextOutlined style={{ fontSize: '24px', color: '#8c8c8c' }} />;
  };

  const renderClusterView = () => {
    const clusterName = getCurrentClusterName();
    if (!clusterName) return null;

    // Check if we're inside a component folder
    const pathParts = currentPath.split('/');
    if (pathParts.length >= 3) {
      const componentKey = pathParts[2];
      const configFolder = pathParts[3]; // 'default' or 'local'
      
      // We're inside a component folder, show files
      return (
        <div>
          <div style={{ marginBottom: 24 }}>
            <Title level={3} style={{ color: '#ffffff', marginBottom: 8 }}>
              <ClusterOutlined style={{ marginRight: 12, color: '#1890ff' }} />
              Cluster: {clusterName} → {componentKey} → {configFolder}
            </Title>
            <Text style={{ color: '#8c8c8c' }}>
              Configuration files for {componentKey} ({configFolder})
            </Text>
          </div>

          {/* Show files and folders in this component/config folder */}
          {loading ? (
            <div style={{ textAlign: 'center', padding: 50, color: '#ffffff' }}>
              <Spin size="large" />
              <div style={{ marginTop: 16 }}>Loading files...</div>
            </div>
          ) : files.length === 0 ? (
            <Empty
              description="No files in this configuration folder"
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            >
              <Space>
                <Button type="primary" onClick={() => setCreateFileModalVisible(true)}>
                  Create File
                </Button>
                <Button onClick={() => setCreateFolderModalVisible(true)}>
                  Create Folder
                </Button>
              </Space>
            </Empty>
          ) : (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {files.map(renderFileCard)}
            </div>
          )}
        </div>
      );
    }

    // Check if we're inside a component folder (e.g., clusters/prod_3/cm)
    if (pathParts.length === 3) {
      const componentKey = pathParts[2];
      
      // Show default and local folders for this component
      const componentInfo = {
        'cm': { name: 'Cluster Master', icon: <ClusterOutlined />, color: '#52c41a' },
        'deployer': { name: 'Deployer', icon: <CloudOutlined />, color: '#1890ff' },
        'sh': { name: 'Search Head', icon: <SearchOutlined />, color: '#722ed1' },
        'ds': { name: 'Deployment Server', icon: <DatabaseOutlined />, color: '#fa8c16' },
        'uf': { name: 'Universal Forwarder', icon: <ThunderboltOutlined />, color: '#13c2c2' },
        'hf': { name: 'Heavy Forwarder', icon: <FireOutlined />, color: '#eb2f96' },
        'lm': { name: 'License Master', icon: <KeyOutlined />, color: '#722ed1' },
        'mc': { name: 'Monitoring Console', icon: <MonitorOutlined />, color: '#fa8c16' }
      }[componentKey];

      if (componentInfo) {
        return (
          <div>
            <div style={{ marginBottom: 24 }}>
              <Title level={3} style={{ color: '#ffffff', marginBottom: 8 }}>
                <ClusterOutlined style={{ marginRight: 12, color: '#1890ff' }} />
                Cluster: {clusterName} → {componentInfo.name}
              </Title>
              <Text style={{ color: '#8c8c8c' }}>
                Configuration folders for {componentInfo.name}
              </Text>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: 16 }}>
              <Card
                style={{ 
                  backgroundColor: '#2a2a2a', 
                  borderColor: '#404040',
                  cursor: 'pointer'
                }}
                onClick={() => setCurrentPath(`clusters/${clusterName}/${componentKey}/default`)}
              >
                <div style={{ textAlign: 'center' }}>
                  <div style={{ color: '#52c41a', fontSize: 32, marginBottom: 12 }}>
                    <FolderOutlined />
                  </div>
                  <Title level={5} style={{ color: '#ffffff', marginBottom: 8 }}>
                    Default Configuration
                  </Title>
                  <Text style={{ color: '#8c8c8c' }}>
                    Base configuration files
                  </Text>
                </div>
              </Card>

              <Card
                style={{ 
                  backgroundColor: '#2a2a2a', 
                  borderColor: '#404040',
                  cursor: 'pointer'
                }}
                onClick={() => setCurrentPath(`clusters/${clusterName}/${componentKey}/local`)}
              >
                <div style={{ textAlign: 'center' }}>
                  <div style={{ color: '#1890ff', fontSize: 32, marginBottom: 12 }}>
                    <FolderOutlined />
                  </div>
                  <Title level={5} style={{ color: '#ffffff', marginBottom: 8 }}>
                    Local Configuration
                  </Title>
                  <Text style={{ color: '#8c8c8c' }}>
                    Custom configuration files
                  </Text>
                </div>
              </Card>
            </div>
          </div>
        );
      }
    }

    // Show main cluster components view
    const clusterComponents = [
      { key: 'cm', name: 'Cluster Manager', icon: <ClusterOutlined />, color: '#52c41a', description: 'Cluster Master/Manager' },
      { key: 'deployer', name: 'Deployer', icon: <CloudOutlined />, color: '#1890ff', description: 'Search Head Cluster Deployer' },
      { key: 'sh', name: 'Search Head', icon: <SearchOutlined />, color: '#722ed1', description: 'Search Head' },
      { key: 'idx', name: 'Indexer', icon: <DatabaseOutlined />, color: '#13c2c2', description: 'Indexer/Peer Node' },
      { key: 'ds', name: 'Deployment Server', icon: <DatabaseOutlined />, color: '#fa8c16', description: 'Deployment Server' },
      { key: 'uf', name: 'Universal Forwarder', icon: <ThunderboltOutlined />, color: '#13c2c2', description: 'Universal Forwarder' },
      { key: 'hf', name: 'Heavy Forwarder', icon: <FireOutlined />, color: '#eb2f96', description: 'Heavy Forwarder' },
      { key: 'lm', name: 'License Master', icon: <KeyOutlined />, color: '#722ed1', description: 'License Master' },
      { key: 'mc', name: 'Monitoring Console', icon: <MonitorOutlined />, color: '#fa8c16', description: 'Monitoring Console' }
    ];

    return (
      <div>
        <div style={{ marginBottom: 24 }}>
          <Title level={3} style={{ color: '#ffffff', marginBottom: 8 }}>
            <ClusterOutlined style={{ marginRight: 12, color: '#1890ff' }} />
            Cluster: {clusterName}
          </Title>
          <Text style={{ color: '#8c8c8c' }}>
            Splunk cluster configuration structure
          </Text>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: 16 }}>
          {clusterComponents.map((component) => (
            <Card
              key={component.key}
              style={{ 
                backgroundColor: '#2a2a2a', 
                borderColor: '#404040',
                cursor: 'pointer'
              }}
              onClick={() => setCurrentPath(`clusters/${clusterName}/${component.key}`)}
            >
              <div style={{ textAlign: 'center' }}>
                <div style={{ color: component.color, fontSize: 32, marginBottom: 12 }}>
                  {component.icon}
                </div>
                <Title level={5} style={{ color: '#ffffff', marginBottom: 4 }}>
                  {component.name}
                </Title>
                <Text style={{ color: '#8c8c8c', fontSize: 12, marginBottom: 16, display: 'block' }}>
                  {component.description}
                </Text>
                <div style={{ display: 'flex', justifyContent: 'space-around', marginTop: 16 }}>
                  <div style={{ textAlign: 'center' }}>
                    <FolderOutlined style={{ color: '#52c41a', fontSize: 16 }} />
                    <div style={{ color: '#8c8c8c', fontSize: 12, marginTop: 4 }}>default</div>
                  </div>
                  <div style={{ textAlign: 'center' }}>
                    <FolderOutlined style={{ color: '#1890ff', fontSize: 16 }} />
                    <div style={{ color: '#8c8c8c', fontSize: 12, marginTop: 4 }}>local</div>
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>
    );
  };

  const renderFileCard = (file: FileItem) => {
    const menu = (
      <Menu>
        {!file.is_dir && (
          <Menu.Item key="download" icon={<DownloadOutlined />} onClick={() => handleDownload(file)}>
            Download
          </Menu.Item>
        )}
        {filesService.isPreviewable(file) && (
          <Menu.Item key="preview" icon={<EyeOutlined />} onClick={() => handlePreviewFile(file)}>
            Preview
          </Menu.Item>
        )}
        {filesService.isPreviewable(file) && (
          <Menu.Item key="edit" icon={<EditOutlined />} onClick={() => handleEditFile(file)}>
            Edit
          </Menu.Item>
        )}
        <Menu.Item key="rename" icon={<EditOutlined />} onClick={() => {
          setSelectedFile(file);
          setNewFileName(file.name);
          setRenameModalVisible(true);
        }}>
          Rename
        </Menu.Item>
        <Menu.Divider />
        <Menu.Item key="delete" icon={<DeleteOutlined />} danger onClick={() => handleDelete(file)}>
          Delete
        </Menu.Item>
      </Menu>
    );

    return (
      <Card
        key={file.path}
        hoverable
        style={{ 
          width: 200, 
          margin: 8,
          cursor: file.is_dir ? 'pointer' : 'default',
          backgroundColor: '#1f1f1f',
          borderColor: '#303030'
        }}
        onClick={() => file.is_dir && navigateToFolder(file)}
        bodyStyle={{ padding: 12, textAlign: 'center' }}
      >
        <div style={{ marginBottom: 8 }}>
          {getFileIcon(file)}
        </div>
        <div style={{ 
          fontSize: '12px', 
          fontWeight: 'bold',
          marginBottom: 4,
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
          color: '#ffffff'
        }}>
          {file.name}
        </div>
        <div style={{ fontSize: '11px', color: '#a6a6a6', marginBottom: 8 }}>
          {file.is_dir ? 'Folder' : filesService.formatFileSize(file.size)}
        </div>
        <div style={{ fontSize: '10px', color: '#8c8c8c' }}>
          {dayjs(file.modified_time).format('MMM D, YYYY')}
        </div>
        <div style={{ position: 'absolute', top: 8, right: 8 }}>
          <Dropdown overlay={menu} trigger={['click']}>
            <Button 
              type="text" 
              icon={<MoreOutlined />} 
              size="small"
              onClick={(e) => e.stopPropagation()}
            />
          </Dropdown>
        </div>
      </Card>
    );
  };

  const displayFiles = searchQuery ? searchResults : files;

  // Create cluster structure function
  const createClusterStructure = async (clusterName: string) => {
    try {
      const result = await workflowsService.createCluster(clusterName);
      message.success(`Cluster "${clusterName}" structure created successfully!`);
      console.log('Cluster creation result:', result);
      
      // Refresh the clusters list to show the newly created cluster
      await loadClusters();
    } catch (error: any) {
      console.error('Failed to create cluster structure:', error);
      message.error(`Failed to create cluster structure: ${error.response?.data?.detail || error.message}`);
    }
  };

  return (
    <div className="files-page" style={{ 
      padding: 24, 
      backgroundColor: '#141414', 
      minHeight: '100vh',
      color: '#ffffff'
    }}>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <Title level={2} style={{ margin: 0, color: '#ffffff' }}>
          <FileTextOutlined style={{ marginRight: 12, color: '#1890ff' }} />
          Files
        </Title>
        <Text style={{ color: '#8c8c8c' }}>Manage your files and folders</Text>
      </div>

      {/* Breadcrumb */}
      <Card style={{ marginBottom: 16, backgroundColor: '#1f1f1f', borderColor: '#303030' }}>
        <Breadcrumb items={getBreadcrumbItems()} />
      </Card>

      {/* Toolbar */}
      <Card style={{ marginBottom: 16, backgroundColor: '#1f1f1f', borderColor: '#303030' }}>
        <Row gutter={16} align="middle">
          <Col>
            <Space>
              <Upload
                ref={uploadRef}
                beforeUpload={(file) => {
                  handleUpload(file);
                  return false;
                }}
                showUploadList={false}
                disabled={uploading}
              >
                <Button 
                  type="primary" 
                  icon={<UploadOutlined />} 
                  loading={uploading}
                >
                  Upload File
                </Button>
              </Upload>
              
              <Button 
                icon={<FolderAddOutlined />} 
                onClick={() => setCreateFolderModalVisible(true)}
              >
                New Folder
              </Button>
              
              <Button 
                icon={<PlusOutlined />} 
                onClick={() => setCreateFileModalVisible(true)}
              >
                New File
              </Button>
              
              {currentPath && (
                <Button 
                  icon={<ArrowLeftOutlined />} 
                  onClick={navigateBack}
                >
                  Back
                </Button>
              )}
              
              <Button 
                icon={<ReloadOutlined />} 
                onClick={loadFiles}
                loading={loading}
              >
                Refresh
              </Button>
            </Space>
          </Col>
          
          <Col flex="auto">
            <Search
              placeholder="Search files and folders..."
              allowClear
              enterButton={<SearchOutlined />}
              size="large"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onSearch={handleSearch}
              loading={isSearching}
            />
          </Col>
        </Row>
      </Card>

      {/* Main Content Area */}
      {isInsideCluster() ? (
        // Show cluster view when inside a cluster
        <Card style={{ backgroundColor: '#1f1f1f', borderColor: '#303030' }}>
          {renderClusterView()}
        </Card>
      ) : (
        // Show tabs when not inside a cluster
        <Card style={{ backgroundColor: '#1f1f1f', borderColor: '#303030' }}>
          <Tabs
            defaultActiveKey="user"
            items={[
              {
                key: 'user',
                label: (
                  <span>
                    <UserOutlined />
                    User Files
                  </span>
                ),
                children: (
                  <div>
                    {loading ? (
                      <div style={{ textAlign: 'center', padding: 50, color: '#ffffff' }}>
                        <Spin size="large" />
                        <div style={{ marginTop: 16 }}>Loading files...</div>
                      </div>
                    ) : displayFiles.length === 0 ? (
                      <Empty
                        description={
                          searchQuery 
                            ? "No files found matching your search"
                            : "No files in this folder"
                        }
                        image={Empty.PRESENTED_IMAGE_SIMPLE}
                      >
                        {!searchQuery && (
                          <Space>
                            <Button type="primary" onClick={() => setCreateFolderModalVisible(true)}>
                              Create Folder
                            </Button>
                            <Button onClick={() => uploadRef.current?.click()}>
                              Upload File
                            </Button>
                          </Space>
                        )}
                      </Empty>
                    ) : (
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                        {displayFiles.map(renderFileCard)}
                      </div>
                    )}
                  </div>
                )
              },
            {
              key: 'clustering',
              label: (
                <span>
                  <ClusterOutlined />
                  Clustering
                </span>
              ),
              children: (
                <div>
                  <div style={{ marginBottom: 16 }}>
                    <Title level={5} style={{ color: '#ffffff', marginBottom: 16 }}>
                      Splunk Clustering Configuration
                    </Title>
                    <Text style={{ color: '#8c8c8c', display: 'block', marginBottom: 16 }}>
                      Manage enhanced cluster configurations for production-ready Splunk environments. Each cluster includes comprehensive component configurations, SSL/TLS support, security hardening, and auto-generated documentation. The enhanced cluster manager creates 11 component types with default and local configuration folders.
                    </Text>
                    
                    <Space style={{ marginBottom: 16 }}>
                      <Button 
                        type="primary" 
                        icon={<PlusOutlined />}
                        onClick={() => {
                          Modal.confirm({
                            title: 'Create New Cluster',
                            content: (
                              <div>
                                <p style={{ color: '#ffffff', marginBottom: 16 }}>
                                  Enter a name for your new Splunk cluster. This will create the necessary folder structure.
                                </p>
                                <Input
                                  placeholder="Enter cluster name (e.g., production-cluster)"
                                  id="cluster-name-input"
                                  style={{ marginTop: 8 }}
                                />
                              </div>
                            ),
                            onOk: () => {
                              const clusterName = (document.getElementById('cluster-name-input') as HTMLInputElement)?.value;
                              if (clusterName && clusterName.trim()) {
                                createClusterStructure(clusterName.trim());
                              }
                            },
                            okText: 'Create Cluster',
                            cancelText: 'Cancel'
                          });
                        }}
                      >
                        Create New Cluster
                      </Button>
                      <Button 
                        icon={<ReloadOutlined />}
                        onClick={loadClusters}
                      >
                        Refresh Clusters
                      </Button>
                    </Space>
                  </div>
                  
                  {/* Display existing clusters */}
                  {clusters.length > 0 ? (
                    <div>
                      <Title level={5} style={{ color: '#ffffff', marginBottom: 16 }}>
                        Existing Clusters
                      </Title>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                        {clusters.map((cluster) => (
                          <Card
                            key={cluster.name}
                            style={{ 
                              width: 200, 
                              backgroundColor: '#2a2a2a', 
                              borderColor: '#404040',
                              cursor: 'pointer'
                            }}
                            onClick={() => navigateToCluster(cluster)}
                          >
                            <div style={{ textAlign: 'center' }}>
                              <ClusterOutlined style={{ fontSize: 24, color: '#1890ff', marginBottom: 8 }} />
                              <div style={{ color: '#ffffff', fontWeight: 'bold' }}>{cluster.name}</div>
                              <div style={{ color: '#8c8c8c', fontSize: 12 }}>Cluster Configuration</div>
                            </div>
                          </Card>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div style={{ 
                      backgroundColor: '#262626', 
                      padding: 16, 
                      borderRadius: 6,
                      border: '1px solid #404040'
                    }}>
                      <Text style={{ color: '#8c8c8c', fontSize: '12px' }}>
                        <strong>Note:</strong> Enhanced clustering configuration is created by the production-ready cluster manager when you use the Build page. 
                        Each cluster includes 11 component types with comprehensive configurations, SSL/TLS support, and auto-generated documentation.
                        The structure below shows the enhanced component layout:
                      </Text>
                      <div style={{ 
                        marginTop: 12, 
                        padding: 12, 
                        backgroundColor: '#1f1f1f', 
                        borderRadius: 4,
                        fontFamily: 'monospace',
                        fontSize: '11px',
                        color: '#8c8c8c'
                      }}>
                        cluster-name/
                        <br />
                        ├── cm/                 # Cluster Manager
                        <br />
                        │   ├── default/       # Default configurations
                        <br />
                        │   └── local/         # Custom configurations
                        <br />
                        ├── deployer/           # Search Head Cluster Deployer
                        <br />
                        │   ├── default/
                        <br />
                        │   └── local/
                        <br />
                        ├── sh/                 # Search Head
                        <br />
                        │   ├── default/
                        <br />
                        │   └── local/
                        <br />
                        ├── idx/                # Indexer/Peer Node
                        <br />
                        │   ├── default/
                        <br />
                        │   └── local/
                        <br />
                        ├── ds/                 # Deployment Server
                        <br />
                        │   ├── default/
                        <br />
                        │   └── local/
                        <br />
                        ├── uf/                 # Universal Forwarder
                        <br />
                        │   ├── default/
                        <br />
                        │   └── local/
                        <br />
                        ├── hf/                 # Heavy Forwarder
                        <br />
                        │   ├── default/
                        <br />
                        │   └── local/
                        <br />
                        ├── lm/                 # License Master
                        <br />
                        │   ├── default/
                        <br />
                        │   └── local/
                        <br />
                        ├── mc/                 # Monitoring Console
                        <br />
                        │   ├── default/
                        <br />
                        │   └── local/
                        <br />
                        └── documentation/      # Auto-generated guides
                        <br />
                            ├── README.md
                        <br />
                            ├── DEPLOYMENT_GUIDE.md
                        <br />
                            └── TROUBLESHOOTING.md
                      </div>
                    </div>
                  )}
                </div>
              )
            }
          ]}
        />
      </Card>
      )}

      {/* Create Folder Modal */}
      <Modal
        title="Create New Folder"
        open={createFolderModalVisible}
        onOk={handleCreateFolder}
        onCancel={() => {
          setCreateFolderModalVisible(false);
          setNewFolderName('');
        }}
        okText="Create"
        cancelText="Cancel"
      >
        <Input
          placeholder="Enter folder name"
          value={newFolderName}
          onChange={(e) => setNewFolderName(e.target.value)}
          onPressEnter={handleCreateFolder}
          autoFocus
        />
      </Modal>

      {/* Create File Modal */}
      <Modal
        title="Create New File"
        open={createFileModalVisible}
        onOk={handleCreateFile}
        onCancel={() => {
          setCreateFileModalVisible(false);
          setNewFileName('');
          setNewFileContent('');
          setNewFileExtension('.txt');
        }}
        okText="Create"
        cancelText="Cancel"
        width={800}
      >
        <Form layout="vertical">
          <Form.Item label="File Name">
            <Input
              placeholder="Enter file name (without extension)"
              value={newFileName}
              onChange={(e) => setNewFileName(e.target.value)}
              autoFocus
            />
          </Form.Item>
          <Form.Item label="File Type">
            <Select
              value={newFileExtension}
              onChange={setNewFileExtension}
              style={{ width: '100%' }}
            >
              <Option value=".txt">Text File (.txt)</Option>
              <Option value=".md">Markdown (.md)</Option>
              <Option value=".py">Python (.py)</Option>
              <Option value=".js">JavaScript (.js)</Option>
              <Option value=".ts">TypeScript (.ts)</Option>
              <Option value=".json">JSON (.json)</Option>
              <Option value=".yaml">YAML (.yaml)</Option>
              <Option value=".yml">YAML (.yml)</Option>
              <Option value=".sh">Shell Script (.sh)</Option>
              <Option value=".bash">Bash Script (.bash)</Option>
              <Option value=".sql">SQL (.sql)</Option>
              <Option value=".html">HTML (.html)</Option>
              <Option value=".css">CSS (.css)</Option>
              <Option value=".conf">Config (.conf)</Option>
              <Option value=".ini">INI (.ini)</Option>
              <Option value=".cfg">Config (.cfg)</Option>
            </Select>
          </Form.Item>
          <Form.Item label="File Content">
            <TextArea
              placeholder="Enter file content..."
              value={newFileContent}
              onChange={(e) => setNewFileContent(e.target.value)}
              rows={15}
              style={{ fontFamily: 'monospace' }}
            />
          </Form.Item>
        </Form>
      </Modal>

      {/* Rename Modal */}
      <Modal
        title="Rename Item"
        open={renameModalVisible}
        onOk={handleRename}
        onCancel={() => {
          setRenameModalVisible(false);
          setNewFileName('');
          setSelectedFile(null);
        }}
        okText="Rename"
        cancelText="Cancel"
      >
        <Input
          placeholder="Enter new name"
          value={newFileName}
          onChange={(e) => setNewFileName(e.target.value)}
          onPressEnter={handleRename}
          autoFocus
        />
      </Modal>

      {/* Preview Modal */}
      <Modal
        title={`Preview: ${selectedFile?.name}`}
        open={previewModalVisible}
        onCancel={() => {
          setPreviewModalVisible(false);
          setSelectedFile(null);
        }}
        footer={[
          <Button key="edit" icon={<EditOutlined />} onClick={() => {
            setPreviewModalVisible(false);
            handleEditFile(selectedFile!);
          }}>
            Edit
          </Button>,
          <Button key="download" icon={<DownloadOutlined />} onClick={() => selectedFile && handleDownload(selectedFile)}>
            Download
          </Button>,
          <Button key="close" onClick={() => {
            setPreviewModalVisible(false);
            setSelectedFile(null);
          }}>
            Close
          </Button>
        ]}
        width={800}
      >
        {selectedFile && (
          <div>
            <div style={{ marginBottom: 16 }}>
              <Tag color="blue">{selectedFile.extension}</Tag>
              <Tag color="green">{filesService.formatFileSize(selectedFile.size)}</Tag>
              <Tag color="orange">Modified: {dayjs(selectedFile.modified_time).format('MMM D, YYYY HH:mm')}</Tag>
            </div>
            <div style={{ 
              backgroundColor: '#262626', 
              padding: 16, 
              borderRadius: 4,
              maxHeight: 400,
              overflow: 'auto',
              fontFamily: 'monospace',
              fontSize: '12px',
              whiteSpace: 'pre-wrap',
              color: '#ffffff',
              border: '1px solid #404040'
            }}>
              {fileContent}
            </div>
          </div>
        )}
      </Modal>

      {/* Edit File Modal */}
      <Modal
        title={`Edit: ${selectedFile?.name}`}
        open={editModalVisible}
        onOk={handleSaveFile}
        onCancel={() => {
          if (hasUnsavedChanges) {
            Modal.confirm({
              title: 'Unsaved Changes',
              content: 'You have unsaved changes. Are you sure you want to close without saving?',
              onOk: () => {
                setEditModalVisible(false);
                setIsEditing(false);
                setHasUnsavedChanges(false);
                setSelectedFile(null);
                setFileContent('');
              }
            });
          } else {
            setEditModalVisible(false);
            setIsEditing(false);
            setSelectedFile(null);
            setFileContent('');
          }
        }}
        okText="Save"
        cancelText="Cancel"
        width={1000}
        okButtonProps={{ icon: <SaveOutlined /> }}
      >
        {selectedFile && (
          <div>
            <div style={{ marginBottom: 16 }}>
              <Tag color="blue">{selectedFile.extension}</Tag>
              <Tag color="green">{filesService.formatFileSize(selectedFile.size)}</Tag>
              <Tag color="orange">Modified: {dayjs(selectedFile.modified_time).format('MMM D, YYYY HH:mm')}</Tag>
              {hasUnsavedChanges && <Tag color="red">Unsaved Changes</Tag>}
            </div>
            <TextArea
              value={fileContent}
              onChange={(e) => handleContentChange(e.target.value)}
              rows={25}
              style={{ 
                fontFamily: 'monospace',
                fontSize: '12px',
                backgroundColor: '#262626',
                borderColor: '#404040',
                color: '#ffffff'
              }}
              placeholder="File content..."
            />
          </div>
        )}
      </Modal>
    </div>
  );
};

export default Files; 