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
const apiClient = axios.create({
  baseURL: getApiUrl(),
  headers: {
    'Content-Type': 'application/json',
  },
  // Enable credentials for CORS
  withCredentials: false,
});

// Add request interceptor to update baseURL if it changes
apiClient.interceptors.request.use((config) => {
  config.baseURL = getApiUrl();
  
  // Add authorization header if token exists
  const token = localStorage.getItem('siemply_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  
  return config;
});

// Add response interceptor to handle authentication errors
apiClient.interceptors.response.use(
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

export interface ServerClass {
  id: string;
  name: string;
  description: string;
  host_ids: number[];
  hostnames: string[];
  host_count: number;
  tags: string[];
  is_active: boolean;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface CreateServerClassData {
  name: string;
  description: string;
  host_ids: number[];
  tags?: string[];
  is_active?: boolean;
}

export interface UpdateServerClassData {
  description?: string;
  host_ids?: number[];
  tags?: string[];
  is_active?: boolean;
}

export interface ServerClassConfigContent {
  content: string;
  filename: string;
}

export interface NameValidationResult {
  name: string;
  is_valid: boolean;
}

class ServerClassService {
  private baseUrl = '/api/serverclass';

  /**
   * Get all server classes
   */
  async getAllServerClasses(): Promise<ServerClass[]> {
    try {
      const response = await apiClient.get<ServerClass[]>(this.baseUrl);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch server classes:', error);
      throw error;
    }
  }

  /**
   * Get server class by name
   */
  async getServerClass(name: string): Promise<ServerClass> {
    try {
      const response = await apiClient.get<ServerClass>(`${this.baseUrl}/${name}`);
      return response.data;
    } catch (error) {
      console.error(`Failed to fetch server class '${name}':`, error);
      throw error;
    }
  }

  /**
   * Create a new server class
   */
  async createServerClass(data: CreateServerClassData): Promise<ServerClass> {
    try {
      const response = await apiClient.post<ServerClass>(this.baseUrl, data);
      return response.data;
    } catch (error) {
      console.error('Failed to create server class:', error);
      throw error;
    }
  }

  /**
   * Update server class
   */
  async updateServerClass(name: string, data: UpdateServerClassData): Promise<ServerClass> {
    try {
      const response = await apiClient.put<ServerClass>(`${this.baseUrl}/${name}`, data);
      return response.data;
    } catch (error) {
      console.error(`Failed to update server class '${name}':`, error);
      throw error;
    }
  }

  /**
   * Delete server class
   */
  async deleteServerClass(name: string): Promise<{ message: string }> {
    try {
      const response = await apiClient.delete<{ message: string }>(`${this.baseUrl}/${name}`);
      return response.data;
    } catch (error) {
      console.error(`Failed to delete server class '${name}':`, error);
      throw error;
    }
  }

  /**
   * Get serverclass.conf content
   */
  async getServerClassConfigContent(): Promise<ServerClassConfigContent> {
    try {
      const response = await apiClient.get<ServerClassConfigContent>(`${this.baseUrl}/config/content`);
      return response.data;
    } catch (error) {
      console.error('Failed to fetch serverclass.conf content:', error);
      throw error;
    }
  }

  /**
   * Validate server class name
   */
  async validateServerClassName(name: string): Promise<NameValidationResult> {
    try {
      const response = await apiClient.post<NameValidationResult>(`${this.baseUrl}/validate-name`, null, {
        params: { name }
      });
      return response.data;
    } catch (error) {
      console.error(`Failed to validate server class name '${name}':`, error);
      throw error;
    }
  }

  /**
   * Get server classes by tag
   */
  async getServerClassesByTag(tag: string): Promise<ServerClass[]> {
    try {
      const allServerClasses = await this.getAllServerClasses();
      return allServerClasses.filter(sc => sc.tags.includes(tag));
    } catch (error) {
      console.error(`Failed to fetch server classes by tag '${tag}':`, error);
      throw error;
    }
  }

  /**
   * Get active server classes
   */
  async getActiveServerClasses(): Promise<ServerClass[]> {
    try {
      const allServerClasses = await this.getAllServerClasses();
      return allServerClasses.filter(sc => sc.is_active);
    } catch (error) {
      console.error('Failed to fetch active server classes:', error);
      throw error;
    }
  }

  /**
   * Get server classes containing specific host
   */
  async getServerClassesByHost(hostId: number): Promise<ServerClass[]> {
    try {
      const allServerClasses = await this.getAllServerClasses();
      return allServerClasses.filter(sc => sc.host_ids.includes(hostId));
    } catch (error) {
      console.error(`Failed to fetch server classes for host ${hostId}:`, error);
      throw error;
    }
  }
}

export const serverClassService = new ServerClassService(); 