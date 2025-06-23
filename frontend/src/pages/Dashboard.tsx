import React from 'react';
import { 
  Typography, 
  Grid, 
  Paper, 
  Box,
  Card,
  CardContent,
  CardHeader
} from '@mui/material';

const Dashboard: React.FC = () => {
  return (
    <div>
      <Box mb={4}>
        <Typography variant="h4" component="h1" gutterBottom>
          Dashboard
        </Typography>
        <Typography variant="subtitle1" color="textSecondary">
          Welcome to SIEMply - SIEM Installation & Management System
        </Typography>
      </Box>
      
      <Grid container spacing={3}>
        {/* Host Summary */}
        <Grid item xs={12} md={6} lg={3}>
          <Card>
            <CardHeader title="Hosts" />
            <CardContent>
              <Typography variant="h3" align="center">
                0
              </Typography>
              <Typography variant="subtitle1" align="center" color="textSecondary">
                Total Hosts
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        {/* Splunk Hosts */}
        <Grid item xs={12} md={6} lg={3}>
          <Card>
            <CardHeader title="Splunk" />
            <CardContent>
              <Typography variant="h3" align="center">
                0
              </Typography>
              <Typography variant="subtitle1" align="center" color="textSecondary">
                Splunk Hosts
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        {/* Cribl Hosts */}
        <Grid item xs={12} md={6} lg={3}>
          <Card>
            <CardHeader title="Cribl" />
            <CardContent>
              <Typography variant="h3" align="center">
                0
              </Typography>
              <Typography variant="subtitle1" align="center" color="textSecondary">
                Cribl Hosts
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        {/* Recent Jobs */}
        <Grid item xs={12} md={6} lg={3}>
          <Card>
            <CardHeader title="Recent Jobs" />
            <CardContent>
              <Typography variant="h3" align="center">
                0
              </Typography>
              <Typography variant="subtitle1" align="center" color="textSecondary">
                Jobs Run
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        {/* Quick Actions */}
        <Grid item xs={12}>
          <Card>
            <CardHeader title="Quick Actions" />
            <CardContent>
              <Typography variant="body1">
                No quick actions available yet. Add hosts to enable installation options.
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </div>
  );
};

export default Dashboard; 