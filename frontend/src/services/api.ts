/**
 * API Service
 * Provides methods for interacting with the SIEMply backend API
 */
import axios from 'axios';
import { storage, getBrowserInfo } from '../utils/storage';

// Get API URL from environment or cross-browser storage with smart detection
const getApiUrl = () => {
  // First check cross-browser storage for user settings
  const settingsJson = storage.getItem('siemply_settings');
  if (settingsJson) {
    try {
      const settings = JSON.parse(settingsJson);
      if (settings.apiUrl) {
        console.log(`Using stored API URL: ${settings.apiUrl} (${getBrowserInfo()})`);
        return settings.apiUrl;
      }
    } catch (e) {
      console.error(`Error parsing settings from storage (${getBrowserInfo()}):`, e);
    }
  }
  
  // Smart detection based on current window location
  const currentHost = window.location.hostname;
  const currentProtocol = window.location.protocol;
  
  // If we're already on the server IP, use it with backend port
  if (currentHost === '192.168.100.44') {
    const detectedUrl = `${currentProtocol}//${currentHost}:5050`;
    console.log(`Smart detection: Using detected API URL: ${detectedUrl} (${getBrowserInfo()})`);
    // Save this detection for future use
    const settings = { apiUrl: detectedUrl };
    storage.setItem('siemply_settings', JSON.stringify(settings));
    return detectedUrl;
  }
  
  // Check environment variable but log what we're using
  const envUrl = import.meta.env.VITE_API_URL;
  if (envUrl) {
    console.log(`Using environment API URL: ${envUrl} (${getBrowserInfo()})`);
    // If it's localhost:8000, override it with the correct server IP
    if (envUrl.includes('localhost:8000')) {
      const correctedUrl = 'http://192.168.100.44:5050';
      console.warn(`Overriding incorrect localhost:8000 with correct server IP: ${correctedUrl} (${getBrowserInfo()})`);
      return correctedUrl;
    }
    return envUrl;
  }
  
  // Final fallback to correct server IP
  const fallbackUrl = 'http://192.168.100.44:5050';
  console.log(`Using fallback API URL: ${fallbackUrl} (${getBrowserInfo()})`);
  return fallbackUrl;
};

// Utility function to manually set API URL (for debugging/fixing issues)
export const setApiUrl = (url: string) => {
  console.log(`Manually setting API URL to: ${url} (${getBrowserInfo()})`);
  const settings = { apiUrl: url };
  storage.setItem('siemply_settings', JSON.stringify(settings));
  api.defaults.baseURL = url;
};

// Utility function to test API connection
export const testApiConnection = async (url?: string): Promise<{success: boolean, url: string, error?: string}> => {
  const testUrl = url || getApiUrl();
  try {
    console.log(`Testing API connection to: ${testUrl} (${getBrowserInfo()})`);
    await axios.get(`${testUrl}/health`, { timeout: 5000 });
    console.log(`API connection test successful: ${testUrl} (${getBrowserInfo()})`);
    return { success: true, url: testUrl };
  } catch (error: any) {
    console.error(`API connection test failed: ${testUrl} (${getBrowserInfo()})`, error);
    return { 
      success: false, 
      url: testUrl, 
      error: error.message || 'Connection failed' 
    };
  }
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
  const token = storage.getItem('siemply_token');
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
      // Clear token from all storage methods and redirect to login
      storage.removeItem('siemply_token');
      console.log(`401 Unauthorized - token cleared (${getBrowserInfo()})`);
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

// SSH service
export const sshService = {
  // Check if SSH key exists
  async checkSSHKey(): Promise<{ exists: boolean; public_key?: string; message: string }> {
    const response = await api.get('/ssh/check-key');
    return response.data;
  },

  // Generate new SSH key
  async generateSSHKey(type: string = 'rsa', bits: number = 4096, password: string = ''): Promise<{ exists: boolean; public_key: string; message: string }> {
    const response = await api.post('/ssh/generate-key', {
      type,
      bits,
      password
    });
    return response.data;
  },

  // Get public key
  async getPublicKey(): Promise<{ exists: boolean; public_key: string; message: string }> {
    const response = await api.get('/ssh/public-key');
    return response.data;
  }
};

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
  },

  // Check packages on a host
  async checkPackages(id: number): Promise<{ packages: any[] }> {
    const response = await api.get(`/hosts/${id}/packages`);
    return response.data;
  },

  // Install all missing packages on a host
  async installPackages(id: number): Promise<{ success: boolean; message: string }> {
    const response = await api.post(`/hosts/${id}/packages/install`);
    return response.data;
  },

  // Install a specific package on a host
  async installPackage(id: number, packageName: string): Promise<{ success: boolean; message: string }> {
    const response = await api.post(`/hosts/${id}/packages/install/${packageName}`);
    return response.data;
  },

  // Check services on a host
  async checkServices(id: number): Promise<{ services: any[] }> {
    const response = await api.get(`/hosts/${id}/services`);
    return response.data;
  },

  // Fix SFTP connectivity issues on a host
  async fixSftp(id: number): Promise<{ success: boolean; message: string }> {
    const response = await api.post(`/hosts/${id}/services/fix-sftp`);
    return response.data;
  },

  // Install syslog-ng service on a host
  async installSyslogNg(id: number): Promise<{ success: boolean; message: string }> {
    const response = await api.post(`/hosts/${id}/services/install-syslog-ng`);
    return response.data;
  },

  // Start syslog-ng service on a host
  async startSyslogNg(id: number): Promise<{ success: boolean; message: string }> {
    const response = await api.post(`/hosts/${id}/services/start-syslog-ng`);
    return response.data;
  },

  // Debug services on a host (detailed output)
  async debugServices(id: number): Promise<any> {
    const response = await api.get(`/hosts/${id}/services/debug`);
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
  async installSplunkUF(targetId: number | string, parameters: Record<string, any>, isDryRun: boolean = false): Promise<Job> {
    console.log("Installing Splunk UF with parameters:", { targetId, parameters, isDryRun });
    
    try {
      // Prepare request body with just the parameters
      const requestBody = {
        ...parameters,
        is_dry_run: isDryRun
      };
      
      // Prepare query parameters for target ID
      const queryParams: any = {};
      
      // Determine if targetId is a host ID (number) or server class name (string)
      if (typeof targetId === 'number') {
        queryParams.host_id = targetId;
      } else {
        queryParams.server_class_name = targetId;
      }
      
      const response = await api.post('/jobs/install/splunk-uf', requestBody, { params: queryParams });
      return response.data;
    } catch (error: any) {
      console.error("Splunk UF installation error details:", error.response?.data);
      throw error;
    }
  },

  // Upgrade Splunk Universal Forwarder
  async upgradeSplunkUF(targetId: number | string, parameters: Record<string, any>, isDryRun: boolean = false): Promise<Job> {
    console.log("Upgrading Splunk UF with parameters:", { targetId, parameters, isDryRun });
    
    try {
      // Prepare request body with just the parameters
      const requestBody = {
        ...parameters,
        is_dry_run: isDryRun
      };
      
      // Prepare query parameters for target ID
      const queryParams: any = {};
      
      // Determine if targetId is a host ID (number) or server class name (string)
      if (typeof targetId === 'number') {
        queryParams.host_id = targetId;
      } else {
        queryParams.server_class_name = targetId;
      }
      
      const response = await api.post('/jobs/upgrade/splunk-uf', requestBody, { params: queryParams });
      return response.data;
    } catch (error: any) {
      console.error("Splunk UF upgrade error details:", error.response?.data);
      throw error;
    }
  },

  // Upgrade Splunk Enterprise
  async upgradeSplunkEnterprise(targetId: number | string, parameters: Record<string, any>, isDryRun: boolean = false): Promise<Job> {
    const params: any = { is_dry_run: isDryRun };
    if (typeof targetId === 'number') {
      params.host_id = targetId;
    } else {
      params.server_class_name = targetId;
    }
    const response = await api.post('/jobs/upgrade/splunk-enterprise', parameters, { params });
    return response.data;
  },

  // Get live logs for a job
  async getLiveLogs(jobId: string): Promise<{ logs: string; status: string; job_type?: string; log_file_path?: string; error?: string; message?: string }> {
    const response = await api.get(`/jobs/live-logs/${jobId}`);
    return response.data;
  },

  // Install Splunk Enterprise
  async installSplunkEnterprise(targetId: number | string, parameters: Record<string, any>, isDryRun: boolean = false): Promise<Job> {
    const params: any = { is_dry_run: isDryRun };
    if (typeof targetId === 'number') {
      params.host_id = targetId;
    } else {
      params.server_class_name = targetId;
    }
    const response = await api.post('/jobs/install/splunk-enterprise', parameters, { params });
    return response.data;
  },

  // Install Cribl Worker
  async installCriblWorker(targetId: number | string, parameters: Record<string, any>, isDryRun: boolean = false): Promise<Job> {
    const params: any = { is_dry_run: isDryRun };
    if (typeof targetId === 'number') {
      params.host_id = targetId;
    } else {
      params.server_class_name = targetId;
    }
    const response = await api.post('/jobs/install/cribl-worker', parameters, { params });
    return response.data;
  },

  // Install Cribl Leader
  async installCriblLeader(targetId: number | string, parameters: Record<string, any>, isDryRun: boolean = false): Promise<Job> {
    const params: any = { is_dry_run: isDryRun };
    if (typeof targetId === 'number') {
      params.host_id = targetId;
    } else {
      params.server_class_name = targetId;
    }
    const response = await api.post('/jobs/install/cribl-leader', parameters, { params });
    return response.data;
  },

  // Install Syslog-NG
  async installSyslog(targetId: number | string, parameters: Record<string, any>, isDryRun: boolean = false): Promise<Job> {
    console.log("Installing Syslog-NG with parameters:", { targetId, parameters, isDryRun });
    
    try {
      const params: any = { is_dry_run: isDryRun };
      if (typeof targetId === 'number') {
        params.host_id = targetId;
      } else {
        params.server_class_name = targetId;
      }
      const response = await api.post('/jobs/install/syslog', parameters, { params });
      return response.data;
    } catch (error: any) {
      console.error("Syslog-NG installation error details:", error.response?.data);
      throw error;
    }
  },

  // Submit custom job (for user commands and scripts)
  async submitCustomJob(targetId: number | string, jobType: string, parameters: Record<string, any>, isDryRun: boolean = false): Promise<Job> {
    const params: any = { job_type: jobType, is_dry_run: isDryRun };
    if (typeof targetId === 'number') {
      params.host_id = targetId;
    } else {
      params.server_class_name = targetId;
    }
    const response = await api.post('/jobs/custom', parameters, { params });
    return response.data;
  },

  // Create custom job (alias for submitCustomJob for consistency)
  async createCustomJob(targetId: number | string, jobType: string, parameters: Record<string, any>, isDryRun: boolean = false): Promise<Job> {
    return this.submitCustomJob(targetId, jobType, parameters, isDryRun);
  },

  // Cancel a job
  async cancelJobByUniqueId(uniqueJobId: string): Promise<{deleted: boolean; job_id: string; status?: string}> {
    const response = await api.delete(`/jobs/by-job-id/${uniqueJobId}`);
    return response.data;
  },
  // Backwards-compatible alias used by older pages
  async cancelJob(jobIdOrUnique: any): Promise<any> {
    if (typeof jobIdOrUnique === 'string') {
      return this.cancelJobByUniqueId(jobIdOrUnique);
    }
    // If a numeric DB id is passed, try to resolve to unique id
    try {
      const job: Job = await this.getJob(jobIdOrUnique);
      return this.cancelJobByUniqueId(job.job_id);
    } catch (e) {
      // As a fallback, call delete by unique id path with the numeric value
      const response = await api.delete(`/jobs/by-job-id/${jobIdOrUnique}`);
      return response.data;
    }
  },

  // Test background job execution
  async testBackgroundJob(): Promise<Job> {
    const response = await api.post('/jobs/test-background');
    return response.data;
  },



  // Cleanup duplicate jobs
  async cleanupDuplicateJobs(): Promise<{success: boolean; message: string; cleaned_count: number}> {
    const response = await api.post('/jobs/cleanup-duplicates');
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
        version: parameters.version, // Don't provide default - version should be selected by user
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
  // Get local settings from cross-browser storage
  getSettings(): AppSettings {
    const settingsJson = storage.getItem('siemply_settings');
    if (!settingsJson) {
      // Return default settings
      return {
        apiUrl: import.meta.env.VITE_API_URL || 'http://192.168.100.44:5050',
        theme: 'dark',
        defaultSplunkVersion: '9.1.1',
        defaultCriblVersion: '3.4.1',
        defaultInstallDir: '/opt'
      };
    }
    
    return JSON.parse(settingsJson);
  },

  // Save settings to cross-browser storage
  saveSettings(settings: AppSettings): void {
    storage.setItem('siemply_settings', JSON.stringify(settings));
    console.log(`Settings saved successfully (${getBrowserInfo()})`);
    
    // Update API baseURL if apiUrl changed
    api.defaults.baseURL = settings.apiUrl;
  }
};

// Export the API instance and services
export default api; 