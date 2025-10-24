import api from './api';

export interface ClusterInfo {
  cluster_name: string;
  created_at: string;
  components: string[];
  config_folders: string[];
  total_folders: number;
  folder_structure?: Record<string, any>;
}

export interface DeploymentResult {
  node_id: string;
  node_type: string;
  status: 'success' | 'error' | 'skipped';
  message: string;
  job_id?: string;
}

export interface DeploymentResponse {
  success: boolean;
  cluster_name: string;
  total_nodes: number;
  total_connections: number;
  deployment_results: DeploymentResult[];
}

export interface BuildComponent {
  type: string;
  hostId?: number;
  host?: any;
  packageId?: number;
  package?: any;
  isConfigured: boolean;
}

export interface BuildSaveRequest {
  cluster_name: string;
  components: BuildComponent[];
}

export interface BuildSaveResponse {
  success: boolean;
  message: string;
  updated_files?: string[];
  host_mapping?: Record<string, string>;
  errors?: string[];
}

export const workflowsService = {
  // Create a new cluster
  async createCluster(clusterName: string): Promise<ClusterInfo> {
    const response = await api.post('/workflows/clusters', {
      cluster_name: clusterName
    });
    return response.data;
  },

  // List all clusters
  async listClusters(): Promise<ClusterInfo[]> {
    const response = await api.get('/workflows/clusters');
    return response.data;
  },

  // Get cluster information
  async getClusterInfo(clusterName: string): Promise<ClusterInfo> {
    const response = await api.get(`/workflows/clusters/${clusterName}`);
    return response.data;
  },

  // Delete a cluster
  async deleteCluster(clusterName: string): Promise<{ success: boolean; message: string }> {
    const response = await api.delete(`/workflows/clusters/${clusterName}`);
    return response.data;
  },

  // Save build configuration
  async saveBuildConfiguration(buildData: BuildSaveRequest): Promise<BuildSaveResponse> {
    const response = await api.post('/workflows/builds/save', buildData);
    return response.data;
  },

  // Deploy environment
  async deployEnvironment(deploymentData: {
    nodes: any[];
    connections: any[];
    cluster_name?: string;
  }): Promise<DeploymentResponse> {
    const response = await api.post('/workflows/deploy', deploymentData);
    return response.data;
  },

  // Health check
  async healthCheck(): Promise<{ status: string; service: string; cluster_manager: string }> {
    const response = await api.get('/workflows/health');
    return response.data;
  }
};
