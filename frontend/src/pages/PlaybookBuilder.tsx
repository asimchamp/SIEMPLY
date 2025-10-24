import React, { useState, useEffect } from 'react';
import {
  Card,
  Form,
  Input,
  Button,
  Space,
  Divider,
  Typography,
  Row,
  Col,
  Select,
  Switch,
  InputNumber,
  message,
  Collapse,
  Tag,
  Tooltip,
  Popconfirm,
  Alert,
  theme
} from 'antd';
import {
  PlusOutlined,
  DeleteOutlined,
  SaveOutlined,
  PlayCircleOutlined,
  EyeOutlined,
  CopyOutlined
} from '@ant-design/icons';
import styled from '@emotion/styled';
import { useNavigate, useLocation } from 'react-router-dom';
import { generateYAML, validatePlaybook } from '../utils/yamlGenerator';
import yaml from 'js-yaml';

const { Title, Text } = Typography;
const { Option } = Select;
const { TextArea } = Input;
const { Panel } = Collapse;

const StyledCard = styled(Card)`
  margin-bottom: 16px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
`;

const StyledForm = styled(Form)`
  .ant-form-item-label > label {
    font-weight: 600;
  }
`;

interface Task {
  name: string;
  module: string;
  parameters: Record<string, any>;
  when?: string;
  register?: string;
}

interface Job {
  id: string;
  name: string;
  targets: {
    server_class?: string;
    hosts?: string[];
    exclude_hosts?: string[];
  };
  execution_options: {
    remote_user: string;
    become?: boolean;
    become_user?: string;
    on_failure: 'stop' | 'continue' | 'rollback';
  };
  vars: Record<string, any>;
  tasks: Task[];
}

interface Playbook {
  automation_playbook: Job[];
}

const PlaybookBuilder: React.FC = () => {
  const [form] = Form.useForm();
  const navigate = useNavigate();
  const location = useLocation();
  const [playbookName, setPlaybookName] = useState<string>('');
  const [playbook, setPlaybook] = useState<Playbook>({
    automation_playbook: []
  });
  const [currentJobIndex, setCurrentJobIndex] = useState<number>(-1);
  const [previewVisible, setPreviewVisible] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [editingPlaybookId, setEditingPlaybookId] = useState<string>('');
  const { token } = theme.useToken();

  const parseYAMLToPlaybook = (yamlContent: string): Playbook => {
    try {
      const parsed = yaml.load(yamlContent) as any;
      
      if (!parsed || !parsed.automation_playbook) {
        throw new Error('Invalid playbook structure');
      }

      // Convert the parsed YAML back to our internal format
      const convertedPlaybook: Playbook = {
        automation_playbook: parsed.automation_playbook.map((jobData: any) => {
          const job: Job = {
            id: jobData.job?.id || `job_${Date.now()}`,
            name: jobData.job?.name || jobData.name || 'Unnamed Job',
            targets: {
              server_class: jobData.job?.targets?.server_class || jobData.targets?.server_class,
              hosts: jobData.job?.targets?.hosts || jobData.targets?.hosts || [],
              exclude_hosts: jobData.job?.targets?.exclude_hosts || jobData.targets?.exclude_hosts || []
            },
            execution_options: {
              remote_user: jobData.job?.execution_options?.remote_user || jobData.execution_options?.remote_user || 'root',
              become: jobData.job?.execution_options?.become || jobData.execution_options?.become || false,
              become_user: jobData.job?.execution_options?.become_user || jobData.execution_options?.become_user,
              on_failure: jobData.job?.execution_options?.on_failure || jobData.execution_options?.on_failure || 'stop'
            },
            vars: jobData.job?.vars || jobData.vars || {},
            tasks: []
          };

          // Convert tasks
          const tasks = jobData.job?.tasks || jobData.tasks || [];
          job.tasks = tasks.map((taskData: any) => {
            const task: Task = {
              name: taskData.name || 'Unnamed Task',
              module: taskData.module || 'command',
              parameters: {}
            };

            // Handle different task structures
            if (taskData.command) {
              task.module = 'command';
              if (typeof taskData.command === 'string') {
                task.parameters = { cmd: taskData.command };
              } else if (taskData.command.cmd) {
                task.parameters = { cmd: taskData.command.cmd };
              } else {
                task.parameters = taskData.command;
              }
            } else if (taskData.args) {
              task.parameters = taskData.args;
            }

            if (taskData.when) task.when = taskData.when;
            if (taskData.register) task.register = taskData.register;

            return task;
          });

          return job;
        })
      };

      return convertedPlaybook;
    } catch (error) {
      console.error('Error parsing YAML:', error);
      throw new Error('Failed to parse YAML content');
    }
  };

  // Initialize edit mode if navigating from PlaybookList
  useEffect(() => {
    if (location.state?.editMode && location.state?.playbook) {
      const { playbook: editPlaybook } = location.state;
      setEditMode(true);
      setEditingPlaybookId(editPlaybook.id);
      setPlaybookName(editPlaybook.name.replace('.yml', '').replace('.yaml', ''));
      
      // Parse the YAML content and populate the form
      try {
        const parsedPlaybook = parseYAMLToPlaybook(editPlaybook.content);
        setPlaybook(parsedPlaybook);
      } catch (error) {
        message.error('Failed to parse playbook content');
        console.error('Error parsing playbook:', error);
      }
    }
  }, [location.state]);

  const moduleOptions = [
    { value: 'service', label: 'Service Management' },
    { value: 'git', label: 'Git Operations' },
    { value: 'command', label: 'Command Execution' },
    { value: 'script', label: 'Script Execution' },
    { value: 'package', label: 'Package Management' },
    { value: 'file', label: 'File Operations' },
    { value: 'copy', label: 'File Copy' },
    { value: 'template', label: 'Template Processing' },
    { value: 'debug', label: 'Debug Output' },
    { value: 'reboot', label: 'System Reboot' },
    { value: 'user', label: 'User Management' },
    { value: 'group', label: 'Group Management' }
  ];

  const getModuleParameters = (module: string) => {
    const parameters: Record<string, any> = {};
    
    switch (module) {
      case 'service':
        parameters.name = '';
        parameters.state = 'started';
        parameters.enabled = true;
        break;
      case 'git':
        parameters.repo = '';
        parameters.dest = '';
        parameters.version = '';
        break;
      case 'command':
        parameters.cmd = '';
        break;
      case 'script':
        parameters.path = '';
        break;
      case 'package':
        parameters.name = '';
        parameters.state = 'present';
        break;
      case 'file':
        parameters.path = '';
        parameters.state = 'present';
        break;
      case 'copy':
        parameters.src = '';
        parameters.dest = '';
        break;
      case 'template':
        parameters.src = '';
        parameters.dest = '';
        break;
      case 'debug':
        parameters.msg = '';
        break;
      case 'reboot':
        parameters.reboot_timeout = 600;
        break;
      case 'user':
        parameters.name = '';
        parameters.state = 'present';
        break;
      case 'group':
        parameters.name = '';
        parameters.state = 'present';
        break;
    }
    
    return parameters;
  };

  const addJob = () => {
    const newJob: Job = {
      id: `job_${Date.now()}`,
      name: '',
      targets: {
        server_class: '',
        hosts: [],
        exclude_hosts: []
      },
      execution_options: {
        remote_user: 'root',
        become: false,
        become_user: 'root',
        on_failure: 'stop'
      },
      vars: {},
      tasks: []
    };

    setPlaybook(prev => ({
      automation_playbook: [...prev.automation_playbook, newJob]
    }));
    setCurrentJobIndex(playbook.automation_playbook.length);
  };

  const removeJob = (index: number) => {
    setPlaybook(prev => ({
      automation_playbook: prev.automation_playbook.filter((_, i) => i !== index)
    }));
    if (currentJobIndex === index) {
      setCurrentJobIndex(-1);
    } else if (currentJobIndex > index) {
      setCurrentJobIndex(currentJobIndex - 1);
    }
  };

  const addTask = (jobIndex: number) => {
    const newTask: Task = {
      name: '',
      module: 'command',
      parameters: getModuleParameters('command'),
      when: '',
      register: ''
    };

    setPlaybook(prev => ({
      automation_playbook: prev.automation_playbook.map((job, i) => 
        i === jobIndex 
          ? { ...job, tasks: [...job.tasks, newTask] }
          : job
      )
    }));
  };

  const removeTask = (jobIndex: number, taskIndex: number) => {
    setPlaybook(prev => ({
      automation_playbook: prev.automation_playbook.map((job, i) => 
        i === jobIndex 
          ? { ...job, tasks: job.tasks.filter((_, ti) => ti !== taskIndex) }
          : job
      )
    }));
  };

  const updateJob = (index: number, field: string, value: any) => {
    setPlaybook(prev => ({
      automation_playbook: prev.automation_playbook.map((job, i) => 
        i === index 
          ? { ...job, [field]: value }
          : job
      )
    }));
  };

  const updateTask = (jobIndex: number, taskIndex: number, field: string, value: any) => {
    setPlaybook(prev => ({
      automation_playbook: prev.automation_playbook.map((job, i) => 
        i === jobIndex 
          ? {
              ...job,
              tasks: job.tasks.map((task, ti) => 
                ti === taskIndex 
                  ? { ...task, [field]: value }
                  : task
              )
            }
          : job
      )
    }));
  };

  const updateTaskParameters = (jobIndex: number, taskIndex: number, parameters: Record<string, any>) => {
    setPlaybook(prev => ({
      automation_playbook: prev.automation_playbook.map((job, i) => 
        i === jobIndex 
          ? {
              ...job,
              tasks: job.tasks.map((task, ti) => 
                ti === taskIndex 
                  ? { ...task, parameters }
                  : task
              )
            }
          : job
      )
    }));
  };

  const generateYAMLContent = () => {
    return generateYAML(playbook);
  };

  const savePlaybook = async () => {
    try {
      // Validate playbook before saving
      const validation = validatePlaybook(playbook);
      if (!validation.isValid) {
        message.error('Please fix the following errors:');
        validation.errors.forEach(error => {
          message.error(error);
        });
        return;
      }

      const yamlContent = generateYAMLContent();
      console.log('Sending YAML content:', yamlContent);
      
      // Validate playbook name
      if (!playbookName.trim()) {
        message.error('Please enter a playbook name');
        return;
      }

      // Generate filename from playbook name
      const filename = playbookName.trim().replace(/[^a-zA-Z0-9_-]/g, '_') + '.yml';
      
      let response;
      if (editMode) {
        // Update existing playbook
        const playbookId = editingPlaybookId.split('/').pop() || editingPlaybookId;
        response = await fetch(`/api/playbooks/${encodeURIComponent(playbookId)}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            name: filename,
            content: yamlContent
          })
        });
      } else {
        // Create new playbook
        response = await fetch('/api/playbooks', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            name: filename,
            content: yamlContent
          })
        });
      }

      if (response.ok) {
        const action = editMode ? 'updated' : 'saved';
        message.success(`Playbook ${action} successfully!`);
        // Navigate back to PlaybookList
        navigate('/playbooks');
      } else {
        const errorData = await response.json();
        console.error('Server error:', errorData);
        message.error(`Failed to save playbook: ${errorData.detail || response.statusText}`);
      }
    } catch (error: any) {
      console.error('Error saving playbook:', error);
      const errorMessage = error?.message || 'Unknown error';
      message.error(`Error saving playbook: ${errorMessage}`);
    }
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(generateYAMLContent());
    message.success('YAML copied to clipboard!');
  };

  return (
    <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto' }}>
      <Row gutter={[16, 16]} align="middle" style={{ marginBottom: '24px' }}>
        <Col flex="auto">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <div>
              <Title level={2} style={{ margin: 0 }}>
                {editMode ? 'Edit Playbook' : 'Create New Playbook'}
              </Title>
              <Text type="secondary">
                {editMode ? 'Modify your automation playbook' : 'Build automation playbooks with a visual interface'}
              </Text>
            </div>
          </div>
        </Col>
        <Col>
          <Space>
            <Button 
              icon={<EyeOutlined />} 
              onClick={() => setPreviewVisible(!previewVisible)}
            >
              Preview YAML
            </Button>
            <Button 
              icon={<CopyOutlined />} 
              onClick={copyToClipboard}
            >
              Copy YAML
            </Button>
            <Button 
              type="primary" 
              icon={<SaveOutlined />} 
              onClick={savePlaybook}
            >
              {editMode ? 'Update Playbook' : 'Save Playbook'}
            </Button>
          </Space>
        </Col>
      </Row>

      {previewVisible && (
        <StyledCard title="Generated YAML Preview">
          <pre style={{ 
            backgroundColor: token.colorBgContainer, 
            padding: '16px', 
            borderRadius: '4px',
            overflow: 'auto',
            maxHeight: '400px'
          }}>
            {generateYAMLContent()}
          </pre>
        </StyledCard>
      )}

      <StyledCard title="Playbook Details">
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item 
              label="Playbook Name" 
              required
              help="Enter a meaningful name for your playbook"
            >
              <Input
                placeholder="e.g., Splunk Installation Playbook"
                value={playbookName}
                onChange={(e) => setPlaybookName(e.target.value)}
                style={{ width: '100%' }}
              />
            </Form.Item>
          </Col>
        </Row>
      </StyledCard>

      <StyledCard 
        title="Jobs" 
        extra={
          <Button 
            type="primary" 
            icon={<PlusOutlined />} 
            onClick={addJob}
          >
            Add Job
          </Button>
        }
      >
        {playbook.automation_playbook.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px', color: token.colorTextSecondary }}>
            <Text>No jobs created yet. Click "Add Job" to get started.</Text>
          </div>
        ) : (
          <Collapse 
            activeKey={currentJobIndex >= 0 ? [currentJobIndex] : []}
            onChange={(keys) => setCurrentJobIndex(keys.length > 0 ? Number(keys[0]) : -1)}
          >
            {playbook.automation_playbook.map((job, jobIndex) => (
              <Panel
                key={jobIndex}
                header={
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span>
                      <strong>{job.name || `Job ${jobIndex + 1}`}</strong>
                      <Tag color="blue" style={{ marginLeft: '8px' }}>
                        {job.tasks.length} tasks
                      </Tag>
                    </span>
                    <Popconfirm
                      title="Are you sure you want to delete this job?"
                      onConfirm={() => removeJob(jobIndex)}
                      okText="Yes"
                      cancelText="No"
                    >
                      <Button 
                        type="text" 
                        danger 
                        icon={<DeleteOutlined />}
                        onClick={(e) => e.stopPropagation()}
                      />
                    </Popconfirm>
                  </div>
                }
              >
                <StyledForm layout="vertical">
                  <Row gutter={16}>
                    <Col span={12}>
                      <Form.Item label="Job ID" required>
                        <Input
                          value={job.id}
                          onChange={(e) => updateJob(jobIndex, 'id', e.target.value)}
                          placeholder="e.g., deploy_webapp_prod"
                        />
                      </Form.Item>
                    </Col>
                    <Col span={12}>
                      <Form.Item label="Job Name" required>
                        <Input
                          value={job.name}
                          onChange={(e) => updateJob(jobIndex, 'name', e.target.value)}
                          placeholder="e.g., Deploy web application to production"
                        />
                      </Form.Item>
                    </Col>
                  </Row>

                  <Divider orientation="left">Targets</Divider>
                  <Row gutter={16}>
                    <Col span={8}>
                      <Form.Item label="Server Class">
                        <Input
                          value={job.targets.server_class || ''}
                          onChange={(e) => updateJob(jobIndex, 'targets', {
                            ...job.targets,
                            server_class: e.target.value
                          })}
                          placeholder="e.g., webservers"
                        />
                      </Form.Item>
                    </Col>
                    <Col span={8}>
                      <Form.Item label="Hosts (comma-separated)">
                        <Input
                          value={job.targets.hosts?.join(', ') || ''}
                          onChange={(e) => updateJob(jobIndex, 'targets', {
                            ...job.targets,
                            hosts: e.target.value.split(',').map(h => h.trim()).filter(h => h)
                          })}
                          placeholder="e.g., 100.11.12.34, splunk-hf1"
                        />
                      </Form.Item>
                    </Col>
                    <Col span={8}>
                      <Form.Item label="Exclude Hosts">
                        <Input
                          value={job.targets.exclude_hosts?.join(', ') || ''}
                          onChange={(e) => updateJob(jobIndex, 'targets', {
                            ...job.targets,
                            exclude_hosts: e.target.value.split(',').map(h => h.trim()).filter(h => h)
                          })}
                          placeholder="e.g., test-server"
                        />
                      </Form.Item>
                    </Col>
                  </Row>

                  <Divider orientation="left">Execution Options</Divider>
                  <Row gutter={16}>
                    <Col span={6}>
                      <Form.Item label="Remote User" required>
                        <Input
                          value={job.execution_options.remote_user}
                          onChange={(e) => updateJob(jobIndex, 'execution_options', {
                            ...job.execution_options,
                            remote_user: e.target.value
                          })}
                          placeholder="e.g., root"
                        />
                      </Form.Item>
                    </Col>
                    <Col span={6}>
                      <Form.Item label="Become (sudo)">
                        <Switch
                          checked={job.execution_options.become}
                          onChange={(checked) => updateJob(jobIndex, 'execution_options', {
                            ...job.execution_options,
                            become: checked
                          })}
                        />
                      </Form.Item>
                    </Col>
                    <Col span={6}>
                      <Form.Item label="Become User">
                        <Input
                          value={job.execution_options.become_user || ''}
                          onChange={(e) => updateJob(jobIndex, 'execution_options', {
                            ...job.execution_options,
                            become_user: e.target.value
                          })}
                          placeholder="e.g., root"
                          disabled={!job.execution_options.become}
                        />
                      </Form.Item>
                    </Col>
                    <Col span={6}>
                      <Form.Item label="On Failure">
                        <Select
                          value={job.execution_options.on_failure}
                          onChange={(value) => updateJob(jobIndex, 'execution_options', {
                            ...job.execution_options,
                            on_failure: value
                          })}
                        >
                          <Option value="stop">Stop</Option>
                          <Option value="continue">Continue</Option>
                          <Option value="rollback">Rollback</Option>
                        </Select>
                      </Form.Item>
                    </Col>
                  </Row>

                  <Divider orientation="left">Variables</Divider>
                  <Form.Item label="Variables (JSON format)">
                    <TextArea
                      rows={4}
                      value={JSON.stringify(job.vars, null, 2)}
                      onChange={(e) => {
                        try {
                          const vars = JSON.parse(e.target.value);
                          updateJob(jobIndex, 'vars', vars);
                        } catch (error) {
                          // Invalid JSON, ignore
                        }
                      }}
                      placeholder='{"app_version": "1.5.2", "source_repo": "git@github.com:mycompany/webapp.git"}'
                    />
                  </Form.Item>

                  <Divider orientation="left">
                    Tasks
                    <Button 
                      type="primary" 
                      size="small" 
                      icon={<PlusOutlined />} 
                      onClick={() => addTask(jobIndex)}
                      style={{ marginLeft: '16px' }}
                    >
                      Add Task
                    </Button>
                  </Divider>

                  {job.tasks.map((task, taskIndex) => (
                    <StyledCard 
                      key={taskIndex}
                      size="small"
                      title={`Task ${taskIndex + 1}: ${task.name || 'Unnamed Task'}`}
                      extra={
                        <Popconfirm
                          title="Are you sure you want to delete this task?"
                          onConfirm={() => removeTask(jobIndex, taskIndex)}
                          okText="Yes"
                          cancelText="No"
                        >
                          <Button 
                            type="text" 
                            danger 
                            size="small"
                            icon={<DeleteOutlined />}
                          />
                        </Popconfirm>
                      }
                      style={{ marginBottom: '16px' }}
                    >
                      <Row gutter={16}>
                        <Col span={12}>
                          <Form.Item label="Task Name" required>
                            <Input
                              value={task.name}
                              onChange={(e) => updateTask(jobIndex, taskIndex, 'name', e.target.value)}
                              placeholder="e.g., Stop web server"
                            />
                          </Form.Item>
                        </Col>
                        <Col span={12}>
                          <Form.Item label="Module" required>
                            <Select
                              value={task.module}
                              onChange={(value) => {
                                updateTask(jobIndex, taskIndex, 'module', value);
                                updateTask(jobIndex, taskIndex, 'parameters', getModuleParameters(value));
                              }}
                            >
                              {moduleOptions.map(option => (
                                <Option key={option.value} value={option.value}>
                                  {option.label}
                                </Option>
                              ))}
                            </Select>
                          </Form.Item>
                        </Col>
                      </Row>

                      <Row gutter={16}>
                        <Col span={12}>
                          <Form.Item label="When Condition">
                            <Input
                              value={task.when || ''}
                              onChange={(e) => updateTask(jobIndex, taskIndex, 'when', e.target.value)}
                              placeholder="e.g., system_facts.os_family == 'Debian'"
                            />
                          </Form.Item>
                        </Col>
                        <Col span={12}>
                          <Form.Item label="Register Output">
                            <Input
                              value={task.register || ''}
                              onChange={(e) => updateTask(jobIndex, taskIndex, 'register', e.target.value)}
                              placeholder="e.g., backup_result"
                            />
                          </Form.Item>
                        </Col>
                      </Row>

                      <Form.Item label="Module Parameters">
                        <div style={{ backgroundColor: token.colorFillTertiary, padding: '16px', borderRadius: '4px' }}>
                          {Object.entries(task.parameters).map(([key, value]) => (
                            <Row gutter={16} key={key} style={{ marginBottom: '8px' }}>
                              <Col span={8}>
                                <Text strong>{key}:</Text>
                              </Col>
                              <Col span={16}>
                                {typeof value === 'boolean' ? (
                                  <Switch
                                    checked={value}
                                    onChange={(checked) => {
                                      const newParams = { ...task.parameters, [key]: checked };
                                      updateTaskParameters(jobIndex, taskIndex, newParams);
                                    }}
                                  />
                                ) : typeof value === 'number' ? (
                                  <InputNumber
                                    value={value}
                                    onChange={(val) => {
                                      const newParams = { ...task.parameters, [key]: val };
                                      updateTaskParameters(jobIndex, taskIndex, newParams);
                                    }}
                                    style={{ width: '100%' }}
                                  />
                                ) : (
                                  <Input
                                    value={value}
                                    onChange={(e) => {
                                      const newParams = { ...task.parameters, [key]: e.target.value };
                                      updateTaskParameters(jobIndex, taskIndex, newParams);
                                    }}
                                    placeholder={`Enter ${key}`}
                                  />
                                )}
                              </Col>
                            </Row>
                          ))}
                        </div>
                      </Form.Item>
                    </StyledCard>
                  ))}
                </StyledForm>
              </Panel>
            ))}
          </Collapse>
        )}
      </StyledCard>
    </div>
  );
};

export default PlaybookBuilder; 