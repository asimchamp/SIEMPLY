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

// Package types
export interface DownloadEntry {
  architecture: string;
  download_url: string;
  file_size?: number;
  checksum?: string;
  os_compatibility?: string[];
}

export interface SoftwarePackage {
  id: number;
  name: string;
  package_type: string;
  version: string;
  description?: string;
  vendor: string;
  downloads: DownloadEntry[];
  // Legacy fields for backward compatibility
  download_url?: string;
  file_size?: number;
  checksum?: string;
  architecture: string;
  os_compatibility: string[];
  install_command?: string;
  default_install_dir: string;
  default_user: string;
  default_group: string;
  default_ports?: Record<string, any>;
  min_requirements?: Record<string, any>;
  installation_notes?: string;
  status: string;
  is_default: boolean;
  release_date?: string;
  support_end_date?: string;
  created_at: string;
  updated_at: string;
}

export interface CreatePackageData {
  name: string;
  package_type: string;
  version: string;
  description?: string;
  vendor?: string;
  downloads?: DownloadEntry[];
  install_command?: string;
  default_install_dir?: string;
  default_user?: string;
  default_group?: string;
  default_ports?: Record<string, any>;
  min_requirements?: Record<string, any>;
  installation_notes?: string;
  status?: string;
  is_default?: boolean;
  release_date?: string;
  support_end_date?: string;
}

export interface UpdatePackageData {
  name?: string;
  description?: string;
  vendor?: string;
  downloads?: DownloadEntry[];
  install_command?: string;
  default_install_dir?: string;
  default_user?: string;
  default_group?: string;
  default_ports?: Record<string, any>;
  min_requirements?: Record<string, any>;
  installation_notes?: string;
  status?: string;
  is_default?: boolean;
  release_date?: string;
  support_end_date?: string;
}

// User types
export interface User {
  id: number;
  username: string;
  email: string;
  full_name?: string;
  role: string; // "admin" or "user"
  is_active: boolean;
  created_at: string;
  updated_at?: string;
  last_login?: string;
}

export interface CreateUserData {
  username: string;
  email: string;
  password: string;
  full_name?: string;
  role?: string;
  is_active?: boolean;
}

export interface UpdateUserData {
  email?: string;
  full_name?: string;
  role?: string;
  is_active?: boolean;
}

export interface ChangePasswordData {
  password: string;
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

  // Get system metrics for a host
  async getSystemMetrics(id: number): Promise<Record<string, any>> {
    const response = await api.get(`/hosts/${id}/system-metrics`);
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
    console.log("Installing Splunk UF with parameters:", { hostId, parameters, isDryRun });
    
    try {
      const response = await api.post('/jobs/install/splunk-uf', parameters, {
        params: {
        host_id: hostId, 
        is_dry_run: isDryRun 
        }
      });
      return response.data;
    } catch (error: any) {
      console.error("Splunk UF installation error details:", error.response?.data);
      throw error;
    }
  },

  // Install Splunk Enterprise
  async installSplunkEnterprise(hostId: number, parameters: Record<string, any>, isDryRun: boolean = false): Promise<Job> {
    const response = await api.post('/jobs/install/splunk-enterprise', parameters, {
      params: {
      host_id: hostId, 
      is_dry_run: isDryRun 
      }
    });
    return response.data;
  },

  // Install Cribl Worker
  async installCriblWorker(hostId: number, parameters: Record<string, any>, isDryRun: boolean = false): Promise<Job> {
    const response = await api.post('/jobs/install/cribl-worker', parameters, {
      params: {
      host_id: hostId, 
      is_dry_run: isDryRun 
      }
    });
    return response.data;
  },

  // Install Cribl Leader
  async installCriblLeader(hostId: number, parameters: Record<string, any>, isDryRun: boolean = false): Promise<Job> {
    const response = await api.post('/jobs/install/cribl-leader', parameters, {
      params: {
      host_id: hostId, 
      is_dry_run: isDryRun 
      }
    });
    return response.data;
  },

  // Submit custom job (for user commands and scripts)
  async submitCustomJob(hostId: number, jobType: string, parameters: Record<string, any>, isDryRun: boolean = false): Promise<Job> {
    const response = await api.post('/jobs/custom', parameters, {
      params: {
      host_id: hostId,
      job_type: jobType,
      is_dry_run: isDryRun 
      }
    });
    return response.data;
  },

  // Cancel a job
  async cancelJob(id: number): Promise<Job> {
    const response = await api.post(`/jobs/${id}/cancel`);
    return response.data;
  }
};

// Package service
export const packageService = {
  // Get all packages
  async getAllPackages(): Promise<SoftwarePackage[]> {
    const response = await api.get('/packages');
    return response.data;
  },

  // Get packages with filters
  async getPackages(filters?: { package_type?: string; status?: string; vendor?: string }): Promise<SoftwarePackage[]> {
    const params = new URLSearchParams();
    if (filters?.package_type) params.append('package_type', filters.package_type);
    if (filters?.status) params.append('status', filters.status);
    if (filters?.vendor) params.append('vendor', filters.vendor);
    
    const response = await api.get('/packages', { params });
    return response.data;
  },

  // Get a single package by ID
  async getPackage(id: number): Promise<SoftwarePackage> {
    const response = await api.get(`/packages/${id}`);
    return response.data;
  },

  // Create a new package
  async createPackage(data: CreatePackageData): Promise<SoftwarePackage> {
    const response = await api.post('/packages', data);
    return response.data;
  },

  // Update a package
  async updatePackage(id: number, data: UpdatePackageData): Promise<SoftwarePackage> {
    const response = await api.put(`/packages/${id}`, data);
    return response.data;
  },

  // Delete a package
  async deletePackage(id: number): Promise<{ message: string }> {
    const response = await api.delete(`/packages/${id}`);
    return response.data;
  },

  // Get available package types
  async getAvailableTypes(): Promise<string[]> {
    const response = await api.get('/packages/types/available');
    return response.data;
  },

  // Get available package statuses
  async getAvailableStatuses(): Promise<string[]> {
    const response = await api.get('/packages/status/available');
    return response.data;
  },

  // Set package as default for its type
  async setDefaultPackage(id: number): Promise<SoftwarePackage> {
    const response = await api.post(`/packages/${id}/set-default`);
    return response.data;
  },

  // Get default packages by type
  async getDefaultPackages(): Promise<SoftwarePackage[]> {
    const response = await api.get('/packages/defaults/by-type');
    return response.data;
  },

  // Bulk import packages
  async bulkImportPackages(packages: CreatePackageData[]): Promise<SoftwarePackage[]> {
    const response = await api.post('/packages/bulk-import', packages);
    return response.data;
  }
};

// User service
export const userService = {
  // Get all users
  async getAllUsers(): Promise<User[]> {
    const response = await api.get('/users');
    return response.data;
  },

  // Get a single user by ID
  async getUser(id: number): Promise<User> {
    const response = await api.get(`/users/${id}`);
    return response.data;
  },

  // Create a new user
  async createUser(data: CreateUserData): Promise<User> {
    const response = await api.post('/users', data);
    return response.data;
  },

  // Update a user
  async updateUser(id: number, data: UpdateUserData): Promise<User> {
    const response = await api.put(`/users/${id}`, data);
    return response.data;
  },

  // Delete a user
  async deleteUser(id: number): Promise<void> {
    await api.delete(`/users/${id}`);
  },

  // Change user password
  async changePassword(id: number, data: ChangePasswordData): Promise<{ message: string }> {
    const response = await api.post(`/users/${id}/change-password`, data);
    return response.data;
  },

  // Toggle user active status
  async toggleActiveStatus(id: number): Promise<User> {
    const response = await api.post(`/users/${id}/toggle-active`);
    return response.data;
  }
};

// Splunk service
export const splunkService = {
  // Install Splunk Universal Forwarder directly (no job)
  async installSplunkUF(hostId: number, parameters: {
    version: string;
    install_dir?: string;
    admin_password: string;
    user?: string;
    group?: string;
    deployment_server?: string;
    deployment_app?: string;
    is_dry_run?: boolean;
  }): Promise<Record<string, any>> {
    console.log("Direct Splunk UF installation with parameters:", { hostId, parameters });
    
    try {
      // Ensure required parameters are set with defaults if not provided
      const finalParams = {
        version: parameters.version || '9.4.3',
        install_dir: parameters.install_dir || '/opt',
        admin_password: parameters.admin_password || 'changeme',
        user: parameters.user || 'splunk',
        group: parameters.group || 'splunk',
        deployment_server: parameters.deployment_server,
        deployment_app: parameters.deployment_app,
        is_dry_run: parameters.is_dry_run || false
      };
      
      // Validate required parameters before sending
      if (!finalParams.version) {
        throw new Error("Splunk version is required");
      }
      
      if (!finalParams.admin_password) {
        throw new Error("Admin password is required");
      }
      
      console.log("Sending Splunk UF installation request with parameters:", finalParams);
      
      const response = await api.post(`/splunk/${hostId}/install-uf`, finalParams);
      return response.data;
    } catch (error: any) {
      console.error("Direct Splunk UF installation error details:", error.response?.data);
      
      // Format error message for better display
      let errorMessage = "Failed to install Splunk Universal Forwarder";
      
      if (error.response?.data?.detail) {
        if (Array.isArray(error.response.data.detail)) {
          errorMessage = error.response.data.detail.map((err: any) => err.msg || String(err)).join(", ");
        } else {
          errorMessage = error.response.data.detail;
        }
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      // Rethrow with better error message
      const enhancedError = new Error(errorMessage);
      enhancedError.name = error.name || "SplunkInstallError";
      throw enhancedError;
    }
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