import { useState, useEffect } from 'react';
import { Typography, Card, Spin, Result, Button } from 'antd';
import { CloudDownloadOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import InstallModal from '../components/InstallModal';

const { Title, Text } = Typography;

const NewJob: React.FC = () => {
  const [modalVisible, setModalVisible] = useState<boolean>(true);
  const navigate = useNavigate();

  const handleClose = () => {
    setModalVisible(false);
    // Redirect to jobs page when modal is closed
    navigate('/jobs');
  };

  const handleSuccess = (jobId: string) => {
    // This will be called when a job is successfully created
    console.log('Job created with ID:', jobId);
  };

  return (
    <div className="new-job-container">
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>
          <CloudDownloadOutlined /> New Installation
        </Title>
        <Text>Create a new installation job</Text>
      </div>

      {/* The InstallModal component will be shown automatically */}
      <InstallModal 
        visible={modalVisible}
        onClose={handleClose}
        onSuccess={handleSuccess}
      />

      {/* Show this if the modal is closed but user is still on the page */}
      {!modalVisible && (
        <Card>
          <Result
            status="info"
            title="Installation Wizard Closed"
            subTitle="You can start a new installation or go back to the dashboard"
            extra={[
              <Button 
                type="primary" 
                key="new" 
                onClick={() => setModalVisible(true)}
              >
                Start New Installation
              </Button>,
              <Button 
                key="dashboard" 
                onClick={() => navigate('/dashboard')}
              >
                Back to Dashboard
              </Button>,
            ]}
          />
        </Card>
      )}
    </div>
  );
};

export default NewJob; 