/**
 * API Service
 * Provides methods for interacting with the SIEMply backend API
 */
import axios from 'axios';

// Get API URL from environment or localStorage
const getApiUrl = () => {
  // First check localStorage for user settings
  const settingsJson = localStorage.getItem('siemply_settings');
  if (settingsJson) {
    try {
      const settings = JSON.parse(settingsJson);
      if (settings.apiUrl) {
        return settings.apiUrl;
      }
    } catch (e) {
      console.error('Error parsing settings from localStorage:', e);
    }
  }
  
  // Fall back to environment variable
  return import.meta.env.VITE_API_URL || 'http://localhost:5050';
};

// Create axios instance with base URL and default headers
const api = axios.create({
  baseURL: getApiUrl(),
  headers: {
    'Content-Type': 'application/json',
  },
  // Enable credentials for CORS
  withCredentials: false,
});

// Add request interceptor to update baseURL if it changes
api.interceptors.request.use((config) => {
  config.baseURL = getApiUrl();
  
  // Add authorization header if token exists
  const token = localStorage.getItem('siemply_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  
  return config;
});

// Add response interceptor to handle authentication errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle 401 Unauthorized errors
    if (error.response && error.response.status === 401) {
      // Clear token and redirect to login
      localStorage.removeItem('siemply_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Host types
export interface Host {
  id: number;
  hostname: string;
  ip_address: string;
  port: number;
  username: string;
  roles: string[];
  os_type: string;
  os_version?: string;
  status: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
}

export interface CreateHostData {
  hostname: string;
  ip_address: string;
  port: number;
  username: string;
  password?: string;
  ssh_key_path?: string;
  roles?: string[];
  os_type?: string;
  os_version?: string;
}

export interface UpdateHostData {
  hostname?: string;
  ip_address?: string;
  port?: number;
  username?: string;
  password?: string;
  ssh_key_path?: string;
  roles?: string[];
  os_type?: string;
  os_version?: string;
  status?: string;
  is_active?: boolean;
}

// Job types
export interface Job {
  id: number;
  job_id: string;
  host_id: number;
  job_type: string;
  status: string;
  is_dry_run: boolean;
  parameters?: Record<string, any>;
  stdout?: string;
  stderr?: string;
  return_code?: number;
  result?: Record<string, any>;
  created_at: string;
  started_at?: string;
  completed_at?: string;
}

export interface CreateJobData {
  host_id: number;
  job_type: string;
  is_dry_run?: boolean;
  parameters?: Record<string, any>;
}

// Host service
export const hostService = {
  // Get all hosts
  async getAllHosts(): Promise<Host[]> {
    const response = await api.get('/hosts');
    return response.data;
  },

  // Get hosts with filters
  async getHosts(filters?: { role?: string; status?: string }): Promise<Host[]> {
    const params = new URLSearchParams();
    if (filters?.role) params.append('role', filters.role);
    if (filters?.status) params.append('status', filters.status);
    
    const response = await api.get('/hosts', { params });
    return response.data;
  },

  // Get a single host by ID
  async getHost(id: number): Promise<Host> {
    const response = await api.get(`/hosts/${id}`);
    return response.data;
  },

  // Create a new host
  async createHost(data: CreateHostData): Promise<Host> {
    const response = await api.post('/hosts', data);
    return response.data;
  },

  // Update a host
  async updateHost(id: number, data: UpdateHostData): Promise<Host> {
    const response = await api.patch(`/hosts/${id}`, data);
    return response.data;
  },

  // Delete a host
  async deleteHost(id: number): Promise<void> {
    await api.delete(`/hosts/${id}`);
  },

  // Test connection to a host
  async testConnection(id: number): Promise<Record<string, any>> {
    const response = await api.post(`/hosts/${id}/test-connection`);
    return response.data;
  },

  // Add a role to a host
  async addRole(id: number, role: string): Promise<Host> {
    const response = await api.post(`/hosts/${id}/roles/${role}`);
    return response.data;
  },

  // Remove a role from a host
  async removeRole(id: number, role: string): Promise<Host> {
    const response = await api.delete(`/hosts/${id}/roles/${role}`);
    return response.data;
  }
};

// Job service
export const jobService = {
  // Get all jobs
  async getAllJobs(): Promise<Job[]> {
    const response = await api.get('/jobs');
    return response.data;
  },

  // Get jobs with filters
  async getJobs(filters?: { host_id?: number; job_type?: string; status?: string }): Promise<Job[]> {
    const params = new URLSearchParams();
    if (filters?.host_id) params.append('host_id', filters.host_id.toString());
    if (filters?.job_type) params.append('job_type', filters.job_type);
    if (filters?.status) params.append('status', filters.status);
    
    const response = await api.get('/jobs', { params });
    return response.data;
  },

  // Get a single job by ID
  async getJob(id: number): Promise<Job> {
    const response = await api.get(`/jobs/${id}`);
    return response.data;
  },

  // Get a job by unique job ID
  async getJobByUniqueId(jobId: string): Promise<Job> {
    const response = await api.get(`/jobs/by-job-id/${jobId}`);
    return response.data;
  },

  // Install Splunk Universal Forwarder
  async installSplunkUF(hostId: number, parameters: Record<string, any>, isDryRun: boolean = false): Promise<Job> {
    const response = await api.post('/jobs/install/splunk-uf', { 
      host_id: hostId, 
      parameters, 
      is_dry_run: isDryRun 
    });
    return response.data;
  },

  // Install Splunk Enterprise
  async installSplunkEnterprise(hostId: number, parameters: Record<string, any>, isDryRun: boolean = false): Promise<Job> {
    const response = await api.post('/jobs/install/splunk-enterprise', { 
      host_id: hostId, 
      parameters, 
      is_dry_run: isDryRun 
    });
    return response.data;
  },

  // Install Cribl Worker
  async installCriblWorker(hostId: number, parameters: Record<string, any>, isDryRun: boolean = false): Promise<Job> {
    const response = await api.post('/jobs/install/cribl-worker', { 
      host_id: hostId, 
      parameters, 
      is_dry_run: isDryRun 
    });
    return response.data;
  },

  // Install Cribl Leader
  async installCriblLeader(hostId: number, parameters: Record<string, any>, isDryRun: boolean = false): Promise<Job> {
    const response = await api.post('/jobs/install/cribl-leader', { 
      host_id: hostId, 
      parameters, 
      is_dry_run: isDryRun 
    });
    return response.data;
  },

  // Cancel a job
  async cancelJob(id: number): Promise<Job> {
    const response = await api.post(`/jobs/${id}/cancel`);
    return response.data;
  }
};

// Settings service
export interface AppSettings {
  apiUrl: string;
  theme: 'light' | 'dark';
  sshKeyPath?: string;
  defaultSplunkVersion: string;
  defaultCriblVersion: string;
  defaultInstallDir: string;
}

export const settingsService = {
  // Get local settings from localStorage
  getSettings(): AppSettings {
    const settingsJson = localStorage.getItem('siemply_settings');
    if (!settingsJson) {
      // Return default settings
      return {
        apiUrl: import.meta.env.VITE_API_URL || 'http://localhost:5050',
        theme: 'dark',
        defaultSplunkVersion: '9.1.1',
        defaultCriblVersion: '3.4.1',
        defaultInstallDir: '/opt'
      };
    }
    
    return JSON.parse(settingsJson);
  },

  // Save settings to localStorage
  saveSettings(settings: AppSettings): void {
    localStorage.setItem('siemply_settings', JSON.stringify(settings));
    
    // Update API baseURL if apiUrl changed
    api.defaults.baseURL = settings.apiUrl;
  }
};

// Export the API instance and services
export default api; 