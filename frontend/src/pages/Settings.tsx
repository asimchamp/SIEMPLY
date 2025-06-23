import React from 'react';
import { Typography, Box } from '@mui/material';

const Settings: React.FC = () => {
  return (
    <div>
      <Box mb={4}>
        <Typography variant="h4" component="h1" gutterBottom>
          Settings
        </Typography>
        <Typography variant="subtitle1" color="textSecondary">
          Configure application settings and defaults
        </Typography>
      </Box>
      
      {/* Settings content goes here */}
      <Typography>Settings functionality will be implemented in Phase 3</Typography>
    </div>
  );
};

export default Settings; 