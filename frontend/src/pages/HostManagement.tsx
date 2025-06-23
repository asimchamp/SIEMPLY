import React from 'react';
import { Typography, Box } from '@mui/material';

const HostManagement: React.FC = () => {
  return (
    <div>
      <Box mb={4}>
        <Typography variant="h4" component="h1" gutterBottom>
          Host Management
        </Typography>
        <Typography variant="subtitle1" color="textSecondary">
          Add, edit, and manage your Splunk and Cribl hosts
        </Typography>
      </Box>
      
      {/* Host management content goes here */}
      <Typography>Host management functionality will be implemented in Phase 2</Typography>
    </div>
  );
};

export default HostManagement; 