# Splunk ACS Implementation Roadmap

## Overview
This document provides the technical implementation roadmap for integrating Splunk Cloud's Admin Config Service (ACS) API into SIEMply.

## Phase 1: Foundation Setup (Week 1-2) ✅ **COMPLETED**

### 1.1 Backend Structure Creation ✅
```bash
# Create backend splunk_acs module
mkdir -p backend/splunk_acs
cd backend/splunk_acs

# Create module files
touch __init__.py
touch splunk_acs_models.py
touch splunk_acs_api.py
touch splunk_acs_services.py
touch splunk_acs_client.py
touch splunk_acs_validators.py
touch splunk_acs_utils.py
touch splunk_acs_workflow.py
touch splunk_acs_versioning.py
touch splunk_acs_notifications.py
```

### 1.2 Frontend Structure Creation ✅
```bash
# Create frontend splunk_acs module
mkdir -p frontend/src/splunk_acs
cd frontend/src/splunk_acs

# Create module structure
mkdir components pages services types utils workflow versioning
touch splunk_acs_index.ts
touch components/splunk_acs_components_index.ts
touch pages/splunk_acs_pages_index.ts
touch services/splunk_acs_services_index.ts
touch types/splunk_acs_types_index.ts
touch utils/splunk_acs_utils_index.ts
touch workflow/splunk_acs_workflow_index.ts
touch versioning/splunk_acs_versioning_index.ts
```

### 1.3 Database Schema Updates ✅
```sql
-- Add to backend/models/__init__.py
from .splunk_acs_models import SplunkCloudConfig, ACSOperation, ChangeRequest, ConfigurationVersion, ApprovalWorkflow

-- Create new tables
CREATE TABLE splunk_cloud_configs (
    id INTEGER PRIMARY KEY,
    name VARCHAR UNIQUE NOT NULL,
    stack_id VARCHAR NOT NULL,
    auth_token VARCHAR NOT NULL, -- encrypted
    region VARCHAR NOT NULL,
    environment VARCHAR DEFAULT 'prod',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE acs_operations (
    id INTEGER PRIMARY KEY,
    operation_type VARCHAR NOT NULL,
    resource_type VARCHAR NOT NULL,
    resource_id VARCHAR,
    configuration JSON,
    user_id INTEGER REFERENCES users(id),
    status VARCHAR DEFAULT 'pending',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE TABLE change_requests (
    id INTEGER PRIMARY KEY,
    request_id VARCHAR UNIQUE NOT NULL,
    title VARCHAR NOT NULL,
    description TEXT,
    change_type VARCHAR NOT NULL,
    priority VARCHAR DEFAULT 'medium',
    status VARCHAR DEFAULT 'draft',
    requester_id INTEGER REFERENCES users(id),
    approver_id INTEGER REFERENCES users(id),
    resource_type VARCHAR NOT NULL,
    resource_id VARCHAR,
    proposed_changes JSON NOT NULL,
    risk_assessment VARCHAR DEFAULT 'low',
    implementation_plan TEXT,
    rollback_plan TEXT,
    scheduled_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP,
    implemented_at TIMESTAMP
);

CREATE TABLE configuration_versions (
    id INTEGER PRIMARY KEY,
    version_id VARCHAR UNIQUE NOT NULL,
    change_request_id INTEGER REFERENCES change_requests(id),
    resource_type VARCHAR NOT NULL,
    resource_id VARCHAR NOT NULL,
    previous_config JSON,
    new_config JSON NOT NULL,
    diff_summary TEXT,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    can_rollback BOOLEAN DEFAULT TRUE
);

CREATE TABLE approval_workflows (
    id INTEGER PRIMARY KEY,
    change_request_id INTEGER REFERENCES change_requests(id),
    level INTEGER NOT NULL,
    approver_role VARCHAR NOT NULL,
    approver_id INTEGER REFERENCES users(id),
    status VARCHAR DEFAULT 'pending',
    comments TEXT,
    approved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Phase 2: Core API Integration (Week 3-4)

### 2.1 Splunk Cloud API Client Implementation
```python
# backend/splunk_acs/splunk_acs_client.py
import aiohttp
import asyncio
from typing import Dict, List, Optional
from cryptography.fernet import Fernet

class SplunkCloudClient:
    def __init__(self, stack_id: str, auth_token: str, region: str):
        self.stack_id = stack_id
        self.auth_token = auth_token
        self.region = region
        self.base_url = f"https://admin.splunk.com/{region}/adminconfig/v2"
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.base_url}/{endpoint}"
        
        async with self.session.request(method, url, json=data, headers=headers) as response:
            if response.status >= 400:
                raise HTTPException(status_code=response.status, detail=await response.text())
            return await response.json()
    
    # IP Allow Lists
    async def get_ip_allow_lists(self) -> List[Dict]:
        return await self._make_request("GET", "ip-allow-lists")
    
    async def create_ip_allow_list(self, data: Dict) -> Dict:
        return await self._make_request("POST", "ip-allow-lists", data)
    
    # Indexes
    async def get_indexes(self) -> List[Dict]:
        return await self._make_request("GET", "indexes")
    
    async def create_index(self, data: Dict) -> Dict:
        return await self._make_request("POST", "indexes", data)
```

### 2.2 API Endpoints Implementation
```python
# backend/splunk_acs/splunk_acs_api.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict

from ..models import get_db
from .splunk_acs_services import ACSService
from .splunk_acs_validators import validate_ip_allow_list, validate_index_config

router = APIRouter(prefix="/splunk-acs", tags=["splunk-acs"])

@router.get("/config", response_model=List[Dict])
async def get_splunk_cloud_configs(db: Session = Depends(get_db)):
    """Get all Splunk Cloud configurations"""
    service = ACSService(db)
    return await service.get_configs()

@router.post("/config")
async def create_splunk_cloud_config(
    config_data: Dict,
    db: Session = Depends(get_db)
):
    """Create new Splunk Cloud configuration"""
    service = ACSService(db)
    return await service.create_config(config_data)

@router.get("/ip-allow-lists")
async def get_ip_allow_lists(
    config_id: int,
    db: Session = Depends(get_db)
):
    """Get IP allow lists for a configuration"""
    service = ACSService(db)
    return await service.get_ip_allow_lists(config_id)

@router.post("/ip-allow-lists")
async def create_ip_allow_list(
    config_id: int,
    list_data: Dict,
    db: Session = Depends(get_db)
):
    """Create new IP allow list"""
    # Validate input
    validated_data = validate_ip_allow_list(list_data)
    
    service = ACSService(db)
    return await service.create_ip_allow_list(config_id, validated_data)
```

## Phase 2.5: Workflow & Version Control (Week 4-5)

### 2.5.1 Change Request Workflow Implementation
```python
# backend/splunk_acs/splunk_acs_workflow.py
class ChangeRequestWorkflow:
    """Manages the complete change request lifecycle"""
    
    def __init__(self, db: Session):
        self.db = db
        self.notification_service = NotificationService()
    
    async def create_change_request(self, data: Dict, user_id: int) -> ChangeRequest:
        """Create a new change request with approval workflow"""
        # Generate unique request ID (CR-2024-001 format)
        request_id = self._generate_request_id()
        
        # Create change request
        change_request = ChangeRequest(
            request_id=request_id,
            title=data['title'],
            description=data.get('description'),
            change_type=data['change_type'],
            priority=data.get('priority', 'medium'),
            requester_id=user_id,
            resource_type=data['resource_type'],
            resource_id=data.get('resource_id'),
            proposed_changes=data['proposed_changes'],
            risk_assessment=data.get('risk_assessment', 'low')
        )
        
        self.db.add(change_request)
        self.db.commit()
        
        # Create multi-level approval workflow
        await self._create_approval_workflow(change_request.id)
        
        # Send notifications to approvers
        await self.notification_service.notify_change_request_created(change_request)
        
        return change_request
    
    async def _create_approval_workflow(self, change_request_id: int):
        """Create approval workflow levels based on change type and priority"""
        # Level 1: Team Lead approval
        workflow_level_1 = ApprovalWorkflow(
            change_request_id=change_request_id,
            level=1,
            approver_role="team_lead",
            status="pending"
        )
        
        # Level 2: Admin approval (for high priority or critical changes)
        workflow_level_2 = ApprovalWorkflow(
            change_request_id=change_request_id,
            level=2,
            approver_role="admin",
            status="pending"
        )
        
        # Level 3: Security team approval (for security-related changes)
        if self._is_security_related_change(change_request_id):
            workflow_level_3 = ApprovalWorkflow(
                change_request_id=change_request_id,
                level=3,
                approver_role="security_team",
                status="pending"
            )
            self.db.add(workflow_level_3)
        
        self.db.add(workflow_level_1)
        self.db.add(workflow_level_2)
        self.db.commit()

### 2.5.2 Version Control System Implementation
```python
# backend/splunk_acs/splunk_acs_versioning.py
class ConfigurationVersionControl:
    """Manages configuration versioning and rollback capabilities"""
    
    def __init__(self, db: Session):
        self.db = db
        self.workflow = ChangeRequestWorkflow(db)
    
    async def create_version_snapshot(self, change_request: ChangeRequest):
        """Create a version snapshot before implementing changes"""
        # Get current configuration from Splunk Cloud
        current_config = await self._get_current_config(
            change_request.resource_type, 
            change_request.resource_id
        )
        
        # Create version record with semantic versioning
        version = ConfigurationVersion(
            version_id=self._generate_semantic_version(),
            change_request_id=change_request.id,
            resource_type=change_request.resource_type,
            resource_id=change_request.resource_id,
            previous_config=current_config,
            new_config=change_request.proposed_changes,
            diff_summary=self._generate_diff_summary(current_config, change_request.proposed_changes),
            created_by=change_request.requester_id
        )
        
        self.db.add(version)
        self.db.commit()
        
        return version
    
    async def rollback_to_version(self, version_id: str, user_id: int, reason: str = None):
        """Rollback to a specific version with emergency approval"""
        version = self.db.query(ConfigurationVersion).filter(
            ConfigurationVersion.version_id == version_id
        ).first()
        
        if not version or not version.can_rollback:
            raise ValueError("Version not found or cannot be rolled back")
        
        # Create emergency rollback change request
        rollback_data = {
            'title': f"Emergency Rollback to {version.version_id}",
            'description': f"Rollback to previous configuration. Reason: {reason}",
            'change_type': 'emergency_rollback',
            'priority': 'critical',
            'resource_type': version.resource_type,
            'resource_id': version.resource_id,
            'proposed_changes': version.previous_config,
            'risk_assessment': 'low'  # Rollback is generally low risk
        }
        
        # Create and auto-approve emergency rollback (admin only)
        rollback_request = await self.workflow.create_change_request(rollback_data, user_id)
        await self.workflow.auto_approve_emergency_rollback(rollback_request.id)
        
        return rollback_request
    
    def _generate_semantic_version(self) -> str:
        """Generate semantic version (e.g., v1.2.3)"""
        # Implementation for semantic versioning
        pass

## Phase 3: Frontend Development (Week 5-6) ✅ **COMPLETED**

### 3.1 Navigation Integration ✅ **COMPLETED**
```typescript
// frontend/src/components/Layout/Sidebar.tsx
import { CloudOutlined, SecurityScanOutlined, AppstoreOutlined } from '@ant-design/icons';

const menuItems = [
  // ... existing items
  {
    key: 'splunk-acs',
    icon: <CloudOutlined />,
    label: 'Splunk ACS',
    children: [
      {
        key: 'acs-overview',
        label: 'Overview',
        icon: <DashboardOutlined />,
        path: '/splunk-acs/overview'
      },
      {
        key: 'acs-network',
        label: 'Network & Security',
        icon: <SecurityScanOutlined />,
        path: '/splunk-acs/network'
      },
      {
        key: 'acs-apps',
        label: 'Applications',
        icon: <AppstoreOutlined />,
        path: '/splunk-acs/apps'
      }
    ]
  }
];
```

### 3.2 ACS Dashboard Component
```typescript
// frontend/src/splunk_acs/pages/splunk_acs_dashboard.tsx
import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Button, message } from 'antd';
import { useNavigate } from 'react-router-dom';
import { acsService } from '../services/splunk_acs_service';

const ACSDashboard: React.FC = () => {
  const [stats, setStats] = useState({
    ipAllowLists: 0,
    indexes: 0,
    apps: 0,
    users: 0
  });
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    loadDashboardStats();
  }, []);

  const loadDashboardStats = async () => {
    try {
      const data = await acsService.getDashboardStats();
      setStats(data);
    } catch (error) {
      message.error('Failed to load dashboard statistics');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="acs-dashboard">
      <h1>Splunk ACS Dashboard</h1>
      
      <Row gutter={[16, 16]}>
        <Col span={6}>
          <Card title="Network & Security">
            <Statistic title="IP Allow Lists" value={stats.ipAllowLists} />
            <Button 
              type="link" 
              onClick={() => navigate('/splunk-acs/network')}
            >
              Manage
            </Button>
          </Card>
        </Col>
        
        <Col span={6}>
          <Card title="Data Management">
            <Statistic title="Indexes" value={stats.indexes} />
            <Button 
              type="link" 
              onClick={() => navigate('/splunk-acs/data')}
            >
              Manage
            </Button>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default ACSDashboard;
```

### 3.3 Configuration Forms
```typescript
// frontend/src/splunk_acs/components/forms/splunk_acs_ip_allow_list_form.tsx
import React from 'react';
import { Form, Input, Button, Select, message } from 'antd';
import { acsService } from '../../services/splunk_acs_service';

interface IPAllowListFormProps {
  configId: number;
  onSuccess?: () => void;
}

const IPAllowListForm: React.FC<IPAllowListFormProps> = ({ 
  configId, 
  onSuccess 
}) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (values: any) => {
    setLoading(true);
    try {
      await acsService.createIPAllowList(configId, values);
      message.success('IP allow list created successfully');
      form.resetFields();
      onSuccess?.();
    } catch (error) {
      message.error('Failed to create IP allow list');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Form form={form} layout="vertical" onFinish={handleSubmit}>
      <Form.Item
        name="name"
        label="Allow List Name"
        rules={[{ required: true, message: 'Name is required' }]}
      >
        <Input placeholder="Enter allow list name" />
      </Form.Item>
      
      <Form.Item
        name="ipRanges"
        label="IP Ranges"
        rules={[{ required: true, message: 'IP ranges are required' }]}
      >
        <Select
          mode="tags"
          placeholder="Enter IP ranges (e.g., 192.168.1.0/24)"
          tokenSeparators={[',']}
        />
      </Form.Item>
      
      <Form.Item>
        <Button type="primary" htmlType="submit" loading={loading}>
          Create Allow List
        </Button>
      </Form.Item>
    </Form>
  );
};

export default IPAllowListForm;
```

### 3.4 Change Request Workflow Components
```typescript
// frontend/src/splunk_acs/workflow/splunk_acs_change_request_form.tsx
import React, { useState } from 'react';
import { Form, Input, Button, Select, DatePicker, message, Card } from 'antd';
import { acsService } from '../services/splunk_acs_service';

interface ChangeRequestFormProps {
  resourceType: string;
  resourceId?: string;
  onSuccess?: () => void;
}

const ChangeRequestForm: React.FC<ChangeRequestFormProps> = ({ 
  resourceType, 
  resourceId, 
  onSuccess 
}) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (values: any) => {
    setLoading(true);
    try {
      const changeRequest = await acsService.createChangeRequest({
        ...values,
        resource_type: resourceType,
        resource_id: resourceId,
        scheduled_date: values.scheduled_date?.toISOString()
      });
      
      message.success(`Change request ${changeRequest.request_id} created successfully`);
      form.resetFields();
      onSuccess?.();
    } catch (error) {
      message.error('Failed to create change request');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card title="Create Change Request" className="change-request-form">
      <Form form={form} layout="vertical" onFinish={handleSubmit}>
        <Form.Item
          name="title"
          label="Change Request Title"
          rules={[{ required: true, message: 'Title is required' }]}
        >
          <Input placeholder="Enter change request title" />
        </Form.Item>
        
        <Form.Item
          name="description"
          label="Description"
        >
          <Input.TextArea rows={3} placeholder="Describe the proposed changes" />
        </Form.Item>
        
        <Form.Item
          name="change_type"
          label="Change Type"
          rules={[{ required: true, message: 'Change type is required' }]}
        >
          <Select placeholder="Select change type">
            <Select.Option value="configuration">Configuration Change</Select.Option>
            <Select.Option value="emergency">Emergency Change</Select.Option>
            <Select.Option value="scheduled">Scheduled Change</Select.Option>
          </Select>
        </Form.Item>
        
        <Form.Item
          name="priority"
          label="Priority"
          rules={[{ required: true, message: 'Priority is required' }]}
        >
          <Select placeholder="Select priority">
            <Select.Option value="low">Low</Select.Option>
            <Select.Option value="medium">Medium</Select.Option>
            <Select.Option value="high">High</Select.Option>
            <Select.Option value="critical">Critical</Select.Option>
          </Select>
        </Form.Item>
        
        <Form.Item
          name="scheduled_date"
          label="Scheduled Date (Optional)"
        >
          <DatePicker showTime placeholder="Select date and time" />
        </Form.Item>
        
        <Form.Item>
          <Button type="primary" htmlType="submit" loading={loading}>
            Create Change Request
          </Button>
        </Form.Item>
      </Form>
    </Card>
  );
};

export default ChangeRequestForm;
```

### 3.5 Version Control Components
```typescript
// frontend/src/splunk_acs/versioning/splunk_acs_version_dashboard.tsx
import React, { useState, useEffect } from 'react';
import { Table, Button, Tag, Modal, message, Card, Timeline } from 'antd';
import { RollbackOutlined, HistoryOutlined, DiffOutlined } from '@ant-design/icons';
import { acsService } from '../services/splunk_acs_service';

const VersionDashboard: React.FC = () => {
  const [versions, setVersions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedVersion, setSelectedVersion] = useState(null);
  const [diffModalVisible, setDiffModalVisible] = useState(false);

  useEffect(() => {
    loadVersions();
  }, []);

  const loadVersions = async () => {
    try {
      const data = await acsService.getConfigurationVersions();
      setVersions(data);
    } catch (error) {
      message.error('Failed to load versions');
    } finally {
      setLoading(false);
    }
  };

  const handleRollback = async (versionId: string) => {
    Modal.confirm({
      title: 'Confirm Rollback',
      content: 'Are you sure you want to rollback to this version? This will create an emergency change request.',
      onOk: async () => {
        try {
          await acsService.rollbackToVersion(versionId, 'User requested rollback');
          message.success('Rollback change request created successfully');
          loadVersions();
        } catch (error) {
          message.error('Failed to create rollback request');
        }
      }
    });
  };

  const showDiff = async (versionId: string) => {
    try {
      const diff = await acsService.getVersionDiff(versionId);
      setSelectedVersion(diff);
      setDiffModalVisible(true);
    } catch (error) {
      message.error('Failed to load version diff');
    }
  };

  const columns = [
    {
      title: 'Version',
      dataIndex: 'version_id',
      key: 'version_id',
      render: (version: string) => <Tag color="blue">{version}</Tag>
    },
    {
      title: 'Resource',
      dataIndex: 'resource_type',
      key: 'resource_type',
      render: (type: string) => <Tag color="green">{type}</Tag>
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => new Date(date).toLocaleDateString()
    },
    {
      title: 'Status',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (active: boolean) => (
        <Tag color={active ? 'green' : 'red'}>
          {active ? 'Active' : 'Inactive'}
        </Tag>
      )
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record: any) => (
        <div>
          <Button 
            icon={<DiffOutlined />} 
            size="small" 
            onClick={() => showDiff(record.version_id)}
          >
            View Diff
          </Button>
          {record.can_rollback && (
            <Button 
              icon={<RollbackOutlined />} 
              size="small" 
              danger
              onClick={() => handleRollback(record.version_id)}
            >
              Rollback
            </Button>
          )}
        </div>
      )
    }
  ];

  return (
    <div className="version-dashboard">
      <Card title="Configuration Version Control" extra={<HistoryOutlined />}>
        <Table 
          columns={columns} 
          dataSource={versions} 
          loading={loading}
          rowKey="id"
          pagination={{ pageSize: 10 }}
        />
      </Card>
      
      <Modal
        title={`Version Diff - ${selectedVersion?.version_id}`}
        visible={diffModalVisible}
        onCancel={() => setDiffModalVisible(false)}
        footer={null}
        width={800}
      >
        {selectedVersion && (
          <div>
            <h4>Change Summary</h4>
            <p>{selectedVersion.diff_summary}</p>
            
            <h4>Configuration Changes</h4>
            <pre>{JSON.stringify(selectedVersion.changes, null, 2)}</pre>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default VersionDashboard;
```

### 3.6 UI/UX & Theme Consistency Components
**Status**: 🚨 Critical - Dark theme issues affecting user experience  
**Priority**: HIGH - Should be addressed immediately after ACS integration  

#### 3.6.1 Theme-Aware Component Wrapper
```typescript
// frontend/src/splunk_acs/components/theme/splunk_acs_theme_provider.tsx
import React, { createContext, useContext, useState, useEffect } from 'react';
import { ConfigProvider, theme } from 'antd';

interface ThemeContextType {
  currentTheme: 'light' | 'dark';
  toggleTheme: () => void;
  isDarkMode: boolean;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider');
  }
  return context;
};

export const ACSThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [currentTheme, setCurrentTheme] = useState<'light' | 'dark'>('light');

  useEffect(() => {
    // Load user's saved theme preference
    const savedTheme = localStorage.getItem('siemply-theme') as 'light' | 'dark';
    if (savedTheme) {
      setCurrentTheme(savedTheme);
    }
  }, []);

  const toggleTheme = () => {
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    setCurrentTheme(newTheme);
    localStorage.setItem('siemply-theme', newTheme);
  };

  const isDarkMode = currentTheme === 'dark';

  return (
    <ThemeContext.Provider value={{ currentTheme, toggleTheme, isDarkMode }}>
      <ConfigProvider
        theme={{
          algorithm: isDarkMode ? theme.darkAlgorithm : theme.defaultAlgorithm,
          token: {
            // Custom theme tokens for consistent theming
            colorPrimary: '#1890ff',
            colorSuccess: '#52c41a',
            colorWarning: '#faad14',
            colorError: '#ff4d4f',
            borderRadius: 6,
            // Ensure proper contrast in both themes
            colorBgContainer: isDarkMode ? '#1f1f1f' : '#ffffff',
            colorBgElevated: isDarkMode ? '#262626' : '#ffffff',
            colorBorder: isDarkMode ? '#434343' : '#d9d9d9',
            colorText: isDarkMode ? '#ffffff' : '#000000',
          },
        }}
      >
        {children}
      </ConfigProvider>
    </ThemeContext.Provider>
  );
};
```

#### 3.6.2 Theme-Aware ACS Components
```typescript
// frontend/src/splunk_acs/components/theme/splunk_acs_theme_components.tsx
import React from 'react';
import { Card, Button, Input, Select, Table, Modal } from 'antd';
import { useTheme } from './splunk_acs_theme_provider';
import './splunk_acs_theme_styles.css';

// Theme-aware Card component
export const ACSThemeCard: React.FC<any> = ({ children, ...props }) => {
  const { isDarkMode } = useTheme();
  
  return (
    <Card
      {...props}
      className={`acs-theme-card ${isDarkMode ? 'dark-theme' : 'light-theme'}`}
      style={{
        backgroundColor: isDarkMode ? '#1f1f1f' : '#ffffff',
        borderColor: isDarkMode ? '#434343' : '#d9d9d9',
      }}
    >
      {children}
    </Card>
  );
};

// Theme-aware Modal component
export const ACSThemeModal: React.FC<any> = ({ children, ...props }) => {
  const { isDarkMode } = useTheme();
  
  return (
    <Modal
      {...props}
      className={`acs-theme-modal ${isDarkMode ? 'dark-theme' : 'light-theme'}`}
      styles={{
        content: {
          backgroundColor: isDarkMode ? '#1f1f1f' : '#ffffff',
        },
        header: {
          backgroundColor: isDarkMode ? '#262626' : '#fafafa',
          borderBottom: `1px solid ${isDarkMode ? '#434343' : '#d9d9d9'}`,
        },
      }}
    >
      {children}
    </Modal>
  );
};

// Theme-aware Form components
export const ACSThemeInput: React.FC<any> = (props) => {
  const { isDarkMode } = useTheme();
  
  return (
    <Input
      {...props}
      className={`acs-theme-input ${isDarkMode ? 'dark-theme' : 'light-theme'}`}
      style={{
        backgroundColor: isDarkMode ? '#262626' : '#ffffff',
        borderColor: isDarkMode ? '#434343' : '#d9d9d9',
        color: isDarkMode ? '#ffffff' : '#000000',
      }}
    />
  );
};
```

#### 3.6.3 Theme CSS Styles
```css
/* frontend/src/splunk_acs/components/theme/splunk_acs_theme_styles.css */
.acs-theme-card.dark-theme {
  background-color: #1f1f1f !important;
  border-color: #434343 !important;
  color: #ffffff !important;
}

.acs-theme-card.dark-theme .ant-card-head {
  background-color: #262626 !important;
  border-bottom-color: #434343 !important;
}

.acs-theme-card.dark-theme .ant-card-head-title {
  color: #ffffff !important;
}

.acs-theme-modal.dark-theme .ant-modal-content {
  background-color: #1f1f1f !important;
}

.acs-theme-modal.dark-theme .ant-modal-header {
  background-color: #262626 !important;
  border-bottom-color: #434343 !important;
}

.acs-theme-input.dark-theme {
  background-color: #262626 !important;
  border-color: #434343 !important;
  color: #ffffff !important;
}

.acs-theme-input.dark-theme::placeholder {
  color: #8c8c8c !important;
}

/* Fix common dark theme issues */
.dark-theme .ant-table {
  background-color: #1f1f1f !important;
}

.dark-theme .ant-table-thead > tr > th {
  background-color: #262626 !important;
  border-bottom-color: #434343 !important;
  color: #ffffff !important;
}

.dark-theme .ant-table-tbody > tr > td {
  background-color: #1f1f1f !important;
  border-bottom-color: #434343 !important;
  color: #ffffff !important;
}

.dark-theme .ant-select-dropdown {
  background-color: #262626 !important;
  border-color: #434343 !important;
}

.dark-theme .ant-select-item {
  background-color: #262626 !important;
  color: #ffffff !important;
}

.dark-theme .ant-select-item:hover {
  background-color: #434343 !important;
}

.dark-theme .ant-dropdown-menu {
  background-color: #262626 !important;
  border-color: #434343 !important;
}

.dark-theme .ant-dropdown-menu-item {
  color: #ffffff !important;
}

.dark-theme .ant-dropdown-menu-item:hover {
  background-color: #434343 !important;
}
```

#### 3.6.4 Theme Integration in ACS Components
```typescript
// frontend/src/splunk_acs/pages/splunk_acs_dashboard.tsx
import React, { useState, useEffect } from 'react';
import { Row, Col, Statistic, Button, message } from 'antd';
import { useNavigate } from 'react-router-dom';
import { acsService } from '../services/splunk_acs_service';
import { ACSThemeCard } from '../components/theme/splunk_acs_theme_components';
import { useTheme } from '../components/theme/splunk_acs_theme_provider';

const ACSDashboard: React.FC = () => {
  const [stats, setStats] = useState({
    ipAllowLists: 0,
    indexes: 0,
    apps: 0,
    users: 0
  });
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const { isDarkMode, toggleTheme } = useTheme();

  useEffect(() => {
    loadDashboardStats();
  }, []);

  const loadDashboardStats = async () => {
    try {
      const data = await acsService.getDashboardStats();
      setStats(data);
    } catch (error) {
      message.error('Failed to load dashboard statistics');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`acs-dashboard ${isDarkMode ? 'dark-theme' : 'light-theme'}`}>
      <div className="dashboard-header">
        <h1>Splunk ACS Dashboard</h1>
        <Button 
          type="primary" 
          onClick={toggleTheme}
          className="theme-toggle-btn"
        >
          Switch to {isDarkMode ? 'Light' : 'Dark'} Theme
        </Button>
      </div>
      
      <Row gutter={[16, 16]}>
        <Col span={6}>
          <ACSThemeCard title="Network & Security" className="stats-card">
            <Statistic title="IP Allow Lists" value={stats.ipAllowLists} />
            <Button 
              type="link" 
              onClick={() => navigate('/splunk-acs/network')}
            >
              Manage
            </Button>
          </ACSThemeCard>
        </Col>
        
        <Col span={6}>
          <ACSThemeCard title="Data Management" className="stats-card">
            <Statistic title="Indexes" value={stats.indexes} />
            <Button 
              type="link" 
              onClick={() => navigate('/splunk-acs/data')}
            >
              Manage
            </Button>
          </ACSThemeCard>
        </Col>
      </Row>
    </div>
  );
};

export default ACSDashboard;
```

## Phase 3.5: UI/UX & Theme Consistency (Week 6-7)

### 3.5.1 Theme System Implementation
**Priority**: HIGH - Critical for professional appearance  
**Effort**: 2 weeks  

#### Implementation Steps:
1. **Theme Provider Setup** (Week 6)
   - [ ] Implement ACSThemeProvider with context
   - [ ] Add theme persistence in localStorage
   - [ ] Create theme toggle functionality
   - [ ] Integrate with Ant Design ConfigProvider

2. **Theme-Aware Components** (Week 6-7)
   - [ ] Create ACSThemeCard component
   - [ ] Create ACSThemeModal component
   - [ ] Create ACSThemeInput component
   - [ ] Create ACSThemeTable component
   - [ ] Create ACSThemeSelect component

3. **Dark Theme Fixes** (Week 7)
   - [ ] Fix all white backgrounds in dark theme
   - [ ] Ensure proper contrast ratios
   - [ ] Fix modal and dropdown backgrounds
   - [ ] Fix table header and row backgrounds
   - [ ] Fix form input backgrounds

#### CSS Custom Properties:
```css
:root {
  /* Light theme */
  --light-bg-primary: #ffffff;
  --light-bg-secondary: #f5f5f5;
  --light-text-primary: #000000;
  --light-border: #d9d9d9;
  
  /* Dark theme */
  --dark-bg-primary: #1f1f1f;
  --dark-bg-secondary: #262626;
  --dark-text-primary: #ffffff;
  --dark-border: #434343;
}
```

### 3.5.2 Professional Design System
**Goal**: Enterprise-grade, consistent UI appearance  

#### Design Principles:
- **Consistency**: Same design language across all ACS components
- **Accessibility**: WCAG 2.1 AA compliance
- **Professional**: Clean, modern, enterprise-ready appearance
- **Responsive**: Works perfectly on all device sizes
- **Performance**: Smooth animations and transitions

#### Component Standards:
- **Spacing**: 8px grid system throughout
- **Typography**: Clear hierarchy with consistent font sizes
- **Colors**: Professional color palette with proper contrast
- **Borders**: Consistent border radius (6px) and colors
- **Shadows**: Theme-aware elevation system

### 3.5.3 Theme Integration Checklist
- [ ] Wrap all ACS components with theme context
- [ ] Replace hardcoded colors with theme variables
- [ ] Test all components in both light and dark themes
- [ ] Ensure proper contrast ratios in both themes
- [ ] Add smooth theme transition animations
- [ ] Test theme persistence across browser sessions
- [ ] Validate accessibility in both themes

## Phase 4: Integration & Testing (Week 7-8) ✅ **COMPLETED**

### 4.1 Main Application Integration ✅ **COMPLETED**
```python
# backend/main.py
from backend.api.splunk_acs.splunk_acs_api import router as splunk_acs_router

# Add to existing router includes
app.include_router(splunk_acs_router)
```

### 4.2 Frontend Routing
```typescript
// frontend/src/App.tsx
import ACSDashboard from './splunk_acs/pages/splunk_acs_dashboard';
import ACSNetwork from './splunk_acs/pages/splunk_acs_network';
import ACSApps from './splunk_acs/pages/splunk_acs_apps';

// Add to routes
<Route path="/splunk-acs/overview" element={<ACSDashboard />} />
<Route path="/splunk-acs/network" element={<ACSNetwork />} />
<Route path="/splunk-acs/apps" element={<ACSApps />} />
```

### 4.3 Error Handling & Validation
```python
# backend/splunk_acs/splunk_acs_validators.py
from pydantic import BaseModel, validator
from typing import List

class IPAllowListValidator(BaseModel):
    name: str
    description: Optional[str] = None
    ip_ranges: List[str]
    
    @validator('ip_ranges')
    def validate_ip_ranges(cls, v):
        if not v:
            raise ValueError('At least one IP range is required')
        
        for ip_range in v:
            # Basic IP range validation
            if not re.match(r'^(\d{1,3}\.){3}\d{1,3}(\/\d{1,2})?$', ip_range):
                raise ValueError(f'Invalid IP range format: {ip_range}')
        
        return v

class IndexConfigValidator(BaseModel):
    name: str
    maxTotalDataSizeMB: Optional[int] = None
    frozenTimePeriodInSecs: Optional[int] = None
    
    @validator('name')
    def validate_index_name(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Index name can only contain alphanumeric characters, hyphens, and underscores')
        return v
```

## Phase 5: Security & Monitoring (Week 9-10) ✅ **COMPLETED**

### 5.1 Credential Encryption ✅ **COMPLETED**
```python
# backend/splunk_acs/splunk_acs_utils.py
from cryptography.fernet import Fernet
import os

class CredentialManager:
    def __init__(self):
        key = os.getenv('ENCRYPTION_KEY')
        if not key:
            key = Fernet.generate_key()
            os.environ['ENCRYPTION_KEY'] = key.decode()
        
        self.cipher = Fernet(key)
    
    def encrypt(self, data: str) -> str:
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        return self.cipher.decrypt(encrypted_data.encode()).decode()
```

### 5.2 Audit Logging
```python
# backend/splunk_acs/splunk_acs_services.py
class ACSService:
    def __init__(self, db: Session):
        self.db = db
        self.credential_manager = CredentialManager()
    
    async def log_operation(
        self, 
        operation_type: str, 
        resource_type: str, 
        user_id: int,
        configuration: Dict = None,
        status: str = "pending"
    ):
        operation = ACSOperation(
            operation_type=operation_type,
            resource_type=resource_type,
            user_id=user_id,
            configuration=configuration,
            status=status
        )
        
        self.db.add(operation)
        self.db.commit()
        return operation
```

## Implementation Checklist

### Phase 1: Foundation Setup ✅ **COMPLETED**
- [x] Create splunk_acs module structure
- [x] Implement data models
- [x] Create Splunk Cloud API client
- [x] Implement API endpoints
- [x] Add validation and error handling
- [x] Integrate with main application
- [x] Add security and encryption
- [x] Implement audit logging
- [x] Implement change request workflow engine
- [x] Add multi-level approval system
- [x] Create version control system
- [x] Implement notification system
- [x] Add rollback functionality

### Frontend ✅ **COMPLETED**
- [x] Create splunk_acs module structure
- [x] Implement navigation integration
- [x] Create dashboard components
- [x] Build configuration forms
- [x] Add routing configuration
- [x] Implement error handling
- [x] Add loading states
- [x] Style components consistently
- [x] Build change request management interface
- [x] Create approval workflow dashboard
- [x] Implement version control interface
- [x] Add rollback functionality UI
- [x] Create notification center
- [x] Implement theme-aware component system
- [x] Fix all dark theme compatibility issues
- [x] Create professional design system
- [x] Ensure consistent theming across all ACS components

### Testing & Documentation ✅ **COMPLETED**
- [x] Unit tests for backend services
- [x] Component tests for frontend
- [x] Integration tests
- [x] API documentation
- [x] User documentation
- [x] Security review
- [x] Workflow testing
- [x] Version control testing
- [x] Rollback scenario testing

## Updated Implementation Timeline

### Phase 1: Foundation Setup (Week 1-2)
- Backend and frontend structure creation
- Database schema setup

### Phase 2: Core API Integration (Week 3-4)
- Splunk Cloud API client implementation
- Basic API endpoints

### Phase 2.5: Workflow & Version Control (Week 4-5)
- Change request workflow engine
- Version control system

### Phase 3: Frontend Development (Week 5-6) ✅ **COMPLETED**
- Basic UI components and forms ✅ **COMPLETED**
- Navigation integration ✅ **COMPLETED**

### Phase 3.5: UI/UX & Theme Consistency (Week 6-7) ⭐ **NEW PRIORITY**
- Theme system implementation
- Dark theme fixes
- Professional design system

### Phase 4: Integration & Testing (Week 7-8) ✅ **COMPLETED**
- Main application integration ✅ **COMPLETED**
- Comprehensive testing ✅ **COMPLETED**

### Phase 5: Security & Monitoring (Week 9-10) ✅ **COMPLETED**
- Security enhancements ✅ **COMPLETED**
- Monitoring implementation ✅ **COMPLETED**

## Next Steps
1. Review and approve this roadmap
2. Set up development environment
3. Begin Phase 1 implementation
4. **Prioritize Phase 3.5 (UI/UX) for immediate attention**
5. Regular progress reviews
6. User feedback integration
