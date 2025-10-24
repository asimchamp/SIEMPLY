/**
 * Splunk ACS API Service
 * Handles all communication with the ACS backend endpoints
 */
import api from '../../services/api';

// Types
export interface SplunkCloudConfig {
  id: number;
  name: string;
  stack_id: string;
  region: string;
  environment: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface IPAllowList {
  id: number;
  name: string;
  description?: string;
  ip_ranges: string[];
  created_at: string;
  updated_at: string;
}

export interface ChangeRequest {
  id: number;
  request_id: string;
  title: string;
  description: string;
  change_type: 'configuration' | 'emergency' | 'scheduled';
  priority: 'low' | 'medium' | 'high' | 'critical';
  status: 'draft' | 'pending' | 'approved' | 'implementing' | 'implemented' | 'rejected' | 'failed';
  resource_type?: string;
  resource_id?: string;
  requester_id: number;
  requester_name: string;
  created_at: string;
  updated_at: string;
  approved_at?: string;
  implemented_at?: string;
  scheduled_date?: string;
  risk_assessment: 'low' | 'medium' | 'high';
  implementation_plan?: string;
  rollback_plan?: string;
  proposed_changes?: any;
}

export interface ACSStats {
  totalConfigs: number;
  activeConfigs: number;
  pendingChanges: number;
  totalChanges: number;
  lastSync: string;
}

export interface HealthStatus {
  status: string;
  timestamp: string;
  version: string;
  services: Record<string, string>;
  alerts_count: number;
}

// API Service Class
class SplunkACSApiService {

  private async makeRequest<T>(endpoint: string, options: any = {}): Promise<T> {
    const url = `/splunk-acs${endpoint}`;
    
    console.log(`ACS API Request: ${options.method || 'GET'} ${url}`, {
      data: options.data,
      options
    });
    
    try {
      const response = await api.request({
        url,
        method: options.method || 'GET',
        data: options.data,
        ...options
      });
      
      console.log(`ACS API Response: ${url}`, response.data);
      return response.data;
    } catch (error: any) {
      console.error(`ACS API Error: ${url}`, {
        status: error.response?.status,
        data: error.response?.data,
        message: error.message
      });
      
      if (error.response?.status === 401) {
        throw new Error('Authentication required. Please log in.');
      }
      if (error.response?.status === 403) {
        throw new Error('Access denied. Insufficient permissions.');
      }
      if (error.response?.status === 404) {
        throw new Error('Resource not found.');
      }
      
      throw new Error(error.response?.data?.detail || error.message || 'API request failed');
    }
  }

  // Configuration Management
  async getConfigurations(): Promise<SplunkCloudConfig[]> {
    return this.makeRequest<SplunkCloudConfig[]>('/config');
  }

  async getConfiguration(id: number): Promise<SplunkCloudConfig> {
    return this.makeRequest<SplunkCloudConfig>(`/config/${id}`);
  }

  async createConfiguration(config: Partial<SplunkCloudConfig>): Promise<SplunkCloudConfig> {
    return this.makeRequest<SplunkCloudConfig>('/config', {
      method: 'POST',
      data: config
    });
  }

  async updateConfiguration(id: number, config: Partial<SplunkCloudConfig>): Promise<SplunkCloudConfig> {
    return this.makeRequest<SplunkCloudConfig>(`/config/${id}`, {
      method: 'PUT',
      data: config
    });
  }

  async deleteConfiguration(id: number): Promise<void> {
    return this.makeRequest<void>(`/config/${id}`, {
      method: 'DELETE'
    });
  }

  // IP Allow Lists
  async getIPAllowLists(configId: number): Promise<IPAllowList[]> {
    return this.makeRequest<IPAllowList[]>(`/config/${configId}/ip-allow-lists`);
  }

  async createIPAllowList(configId: number, allowList: Partial<IPAllowList>): Promise<IPAllowList> {
    return this.makeRequest<IPAllowList>(`/config/${configId}/ip-allow-lists`, {
      method: 'POST',
      data: allowList
    });
  }

  async updateIPAllowList(configId: number, listId: number, allowList: Partial<IPAllowList>): Promise<IPAllowList> {
    return this.makeRequest<IPAllowList>(`/config/${configId}/ip-allow-lists/${listId}`, {
      method: 'PUT',
      data: allowList
    });
  }

  async deleteIPAllowList(configId: number, listId: number): Promise<void> {
    return this.makeRequest<void>(`/config/${configId}/ip-allow-lists/${listId}`, {
      method: 'DELETE'
    });
  }

  // Change Requests
  async getChangeRequests(filters?: {
    status?: string;
    priority?: string;
    change_type?: string;
  }): Promise<ChangeRequest[]> {
    const params = new URLSearchParams();
    if (filters?.status) params.append('status', filters.status);
    if (filters?.priority) params.append('priority', filters.priority);
    if (filters?.change_type) params.append('change_type', filters.change_type);
    
    const queryString = params.toString();
    const endpoint = queryString ? `/change-requests?${queryString}` : '/change-requests';
    
    return this.makeRequest<ChangeRequest[]>(endpoint);
  }

  async getChangeRequest(requestId: string): Promise<ChangeRequest> {
    return this.makeRequest<ChangeRequest>(`/change-requests/${requestId}`);
  }

  async createChangeRequest(changeRequest: Partial<ChangeRequest>): Promise<ChangeRequest> {
    return this.makeRequest<ChangeRequest>('/change-requests', {
      method: 'POST',
      data: changeRequest
    });
  }

  async updateChangeRequest(requestId: string, changeRequest: Partial<ChangeRequest>): Promise<ChangeRequest> {
    return this.makeRequest<ChangeRequest>(`/change-requests/${requestId}`, {
      method: 'PUT',
      data: changeRequest
    });
  }

  async approveChangeRequest(requestId: string, approverId: number, comments?: string): Promise<void> {
    return this.makeRequest<void>(`/change-requests/${requestId}/approve`, {
      method: 'POST',
      data: { approver_id: approverId, comments }
    });
  }

  async rejectChangeRequest(requestId: string, rejectorId: number, reason: string): Promise<void> {
    return this.makeRequest<void>(`/change-requests/${requestId}/reject`, {
      method: 'POST',
      data: { rejector_id: rejectorId, reason }
    });
  }

  async implementChangeRequest(requestId: string): Promise<void> {
    return this.makeRequest<void>(`/change-requests/${requestId}/implement`, {
      method: 'POST'
    });
  }

  // Health & Monitoring
  async getHealthStatus(): Promise<HealthStatus> {
    return this.makeRequest<HealthStatus>('/health');
  }

  async getMetrics(): Promise<any> {
    return this.makeRequest<any>('/metrics');
  }

  // Dashboard Statistics
  async getDashboardStats(): Promise<ACSStats> {
    try {
      // Get real data from multiple endpoints
      const [configs, changes, health] = await Promise.all([
        this.getConfigurations(),
        this.getChangeRequests(),
        this.getHealthStatus()
      ]);

      const pendingChanges = changes.filter(cr => cr.status === 'pending').length;
      const totalChanges = changes.length;
      const activeConfigs = configs.filter(c => c.is_active).length;

      return {
        totalConfigs: configs.length,
        activeConfigs,
        pendingChanges,
        totalChanges,
        lastSync: new Date().toISOString()
      };
    } catch (error) {
      console.error('Failed to get dashboard stats:', error);
      // Return default stats if API fails
      return {
        totalConfigs: 0,
        activeConfigs: 0,
        pendingChanges: 0,
        totalChanges: 0,
        lastSync: 'Never'
      };
    }
  }
}

// Export singleton instance
export const acsApiService = new SplunkACSApiService();
