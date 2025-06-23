import React from 'react';
import { Typography, Box } from '@mui/material';

const JobHistory: React.FC = () => {
  return (
    <div>
      <Box mb={4}>
        <Typography variant="h4" component="h1" gutterBottom>
          Job History
        </Typography>
        <Typography variant="subtitle1" color="textSecondary">
          View the history of installation and configuration jobs
        </Typography>
      </Box>
      
      {/* Job history content goes here */}
      <Typography>Job history functionality will be implemented in Phase 2</Typography>
    </div>
  );
};

export default JobHistory;