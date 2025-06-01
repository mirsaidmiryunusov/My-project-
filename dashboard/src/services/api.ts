import axios, { AxiosInstance, AxiosResponse, AxiosError } from 'axios';

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:3001/api';
const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:3001';

// Types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  firstName: string;
  lastName: string;
  tenantName: string;
}

export interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  role: string;
  tenantId: string;
  permissions: string[];
  preferences?: {
    theme: string;
    language: string;
    timezone: string;
    emailNotifications: boolean;
    smsNotifications: boolean;
    pushNotifications: boolean;
  };
}

export interface AuthResponse {
  user: User;
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
}

export interface DashboardStats {
  totalCalls: number;
  activeCampaigns: number;
  totalContacts: number;
  conversionRate: number;
  callsToday: number;
  callsThisWeek: number;
  callsThisMonth: number;
  avgCallDuration: number;
  successfulCalls: number;
  failedCalls: number;
  pendingCalls: number;
  revenue: {
    today: number;
    thisWeek: number;
    thisMonth: number;
    total: number;
  };
}

export interface Call {
  id: string;
  phoneNumber: string;
  status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED' | 'CANCELLED';
  duration?: number;
  startTime?: string;
  endTime?: string;
  campaignId?: string;
  customerId?: string;
  notes?: string;
  recording?: string;
  transcript?: string;
  sentiment?: 'POSITIVE' | 'NEUTRAL' | 'NEGATIVE';
  outcome?: string;
  createdAt: string;
  updatedAt: string;
}

export interface Campaign {
  id: string;
  name: string;
  description?: string;
  status: 'DRAFT' | 'ACTIVE' | 'PAUSED' | 'COMPLETED' | 'CANCELLED';
  type: 'OUTBOUND' | 'INBOUND';
  script?: string;
  targetAudience?: string;
  startDate?: string;
  endDate?: string;
  totalCalls: number;
  completedCalls: number;
  successfulCalls: number;
  conversionRate: number;
  createdAt: string;
  updatedAt: string;
}

export interface Customer {
  id: string;
  firstName: string;
  lastName: string;
  email?: string;
  phoneNumber: string;
  company?: string;
  status: 'ACTIVE' | 'INACTIVE' | 'BLOCKED';
  tags: string[];
  notes?: string;
  lastContactDate?: string;
  totalCalls: number;
  successfulCalls: number;
  createdAt: string;
  updatedAt: string;
}

export interface Subscription {
  id: string;
  plan: 'FREE' | 'STARTER' | 'PROFESSIONAL' | 'ENTERPRISE';
  status: 'ACTIVE' | 'INACTIVE' | 'PAST_DUE' | 'CANCELLED';
  currentPeriodStart: string;
  currentPeriodEnd: string;
  features: string;
  stripeSubscriptionId?: string;
  cancelledAt?: string;
  createdAt: string;
  updatedAt: string;
}

export interface SubscriptionUsage {
  subscription: Subscription;
  features: any;
  usage: {
    calls: { used: number; limit: number; percentage: number };
    campaigns: { used: number; limit: number; percentage: number };
    contacts: { used: number; limit: number; percentage: number };
    users: { used: number; limit: number; percentage: number };
    aiMinutes: { used: number; limit: number; percentage: number };
  };
  periodStart: string;
  periodEnd: string;
}

// API Client Class
class ApiClient {
  private client: AxiosInstance;
  private token: string | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      (config) => {
        if (this.token) {
          config.headers.Authorization = `Bearer ${this.token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response: AxiosResponse) => response,
      async (error: AxiosError) => {
        if (error.response?.status === 401) {
          // Token expired, try to refresh
          const refreshToken = localStorage.getItem('refreshToken');
          if (refreshToken) {
            try {
              const response = await this.refreshToken(refreshToken);
              this.setToken(response.data.accessToken);
              localStorage.setItem('accessToken', response.data.accessToken);
              
              // Retry the original request
              if (error.config) {
                error.config.headers.Authorization = `Bearer ${response.data.accessToken}`;
                return this.client.request(error.config);
              }
            } catch (refreshError) {
              // Refresh failed, redirect to login
              this.clearAuth();
              window.location.href = '/login';
            }
          } else {
            // No refresh token, redirect to login
            this.clearAuth();
            window.location.href = '/login';
          }
        }
        return Promise.reject(error);
      }
    );

    // Initialize token from localStorage
    const savedToken = localStorage.getItem('accessToken');
    if (savedToken) {
      this.setToken(savedToken);
    }
  }

  setToken(token: string) {
    this.token = token;
  }

  clearAuth() {
    this.token = null;
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('user');
  }

  // Auth endpoints
  async login(credentials: LoginCredentials): Promise<ApiResponse<AuthResponse>> {
    const response = await this.client.post('/auth/login', credentials);
    return response.data;
  }

  async register(data: RegisterData): Promise<ApiResponse<AuthResponse>> {
    const response = await this.client.post('/auth/register', data);
    return response.data;
  }

  async refreshToken(refreshToken: string): Promise<ApiResponse<AuthResponse>> {
    const response = await this.client.post('/auth/refresh', { refreshToken });
    return response.data;
  }

  async logout(): Promise<ApiResponse> {
    const response = await this.client.post('/auth/logout');
    return response.data;
  }

  async forgotPassword(email: string): Promise<ApiResponse> {
    const response = await this.client.post('/auth/forgot-password', { email });
    return response.data;
  }

  async resetPassword(token: string, password: string): Promise<ApiResponse> {
    const response = await this.client.post('/auth/reset-password', { token, password });
    return response.data;
  }

  // Dashboard endpoints
  async getDashboardStats(): Promise<ApiResponse<DashboardStats>> {
    const response = await this.client.get('/dashboard/stats');
    return response.data;
  }

  async getRecentCalls(limit = 10): Promise<ApiResponse<Call[]>> {
    const response = await this.client.get(`/dashboard/recent-calls?limit=${limit}`);
    return response.data;
  }

  async getRecentCampaigns(limit = 5): Promise<ApiResponse<Campaign[]>> {
    const response = await this.client.get(`/dashboard/recent-campaigns?limit=${limit}`);
    return response.data;
  }

  // Calls endpoints
  async getCalls(params?: any): Promise<ApiResponse<{ calls: Call[]; total: number; page: number; limit: number }>> {
    const response = await this.client.get('/calls', { params });
    return response.data;
  }

  async getCall(id: string): Promise<ApiResponse<Call>> {
    const response = await this.client.get(`/calls/${id}`);
    return response.data;
  }

  async createCall(data: Partial<Call>): Promise<ApiResponse<Call>> {
    const response = await this.client.post('/calls', data);
    return response.data;
  }

  async updateCall(id: string, data: Partial<Call>): Promise<ApiResponse<Call>> {
    const response = await this.client.put(`/calls/${id}`, data);
    return response.data;
  }

  async deleteCall(id: string): Promise<ApiResponse> {
    const response = await this.client.delete(`/calls/${id}`);
    return response.data;
  }

  async startCall(id: string): Promise<ApiResponse<Call>> {
    const response = await this.client.post(`/calls/${id}/start`);
    return response.data;
  }

  async endCall(id: string, data?: any): Promise<ApiResponse<Call>> {
    const response = await this.client.post(`/calls/${id}/end`, data);
    return response.data;
  }

  // Campaigns endpoints
  async getCampaigns(params?: any): Promise<ApiResponse<{ campaigns: Campaign[]; total: number; page: number; limit: number }>> {
    const response = await this.client.get('/campaigns', { params });
    return response.data;
  }

  async getCampaign(id: string): Promise<ApiResponse<Campaign>> {
    const response = await this.client.get(`/campaigns/${id}`);
    return response.data;
  }

  async createCampaign(data: Partial<Campaign>): Promise<ApiResponse<Campaign>> {
    const response = await this.client.post('/campaigns', data);
    return response.data;
  }

  async updateCampaign(id: string, data: Partial<Campaign>): Promise<ApiResponse<Campaign>> {
    const response = await this.client.put(`/campaigns/${id}`, data);
    return response.data;
  }

  async deleteCampaign(id: string): Promise<ApiResponse> {
    const response = await this.client.delete(`/campaigns/${id}`);
    return response.data;
  }

  async startCampaign(id: string): Promise<ApiResponse<Campaign>> {
    const response = await this.client.post(`/campaigns/${id}/start`);
    return response.data;
  }

  async pauseCampaign(id: string): Promise<ApiResponse<Campaign>> {
    const response = await this.client.post(`/campaigns/${id}/pause`);
    return response.data;
  }

  async stopCampaign(id: string): Promise<ApiResponse<Campaign>> {
    const response = await this.client.post(`/campaigns/${id}/stop`);
    return response.data;
  }

  // Customers endpoints
  async getCustomers(params?: any): Promise<ApiResponse<{ customers: Customer[]; total: number; page: number; limit: number }>> {
    const response = await this.client.get('/customers', { params });
    return response.data;
  }

  async getCustomer(id: string): Promise<ApiResponse<Customer>> {
    const response = await this.client.get(`/customers/${id}`);
    return response.data;
  }

  async createCustomer(data: Partial<Customer>): Promise<ApiResponse<Customer>> {
    const response = await this.client.post('/customers', data);
    return response.data;
  }

  async updateCustomer(id: string, data: Partial<Customer>): Promise<ApiResponse<Customer>> {
    const response = await this.client.put(`/customers/${id}`, data);
    return response.data;
  }

  async deleteCustomer(id: string): Promise<ApiResponse> {
    const response = await this.client.delete(`/customers/${id}`);
    return response.data;
  }

  async bulkCreateCustomers(customers: Partial<Customer>[]): Promise<ApiResponse<Customer[]>> {
    const response = await this.client.post('/customers/bulk', { customers });
    return response.data;
  }

  async importCustomers(file: File): Promise<ApiResponse> {
    const formData = new FormData();
    formData.append('file', file);
    const response = await this.client.post('/customers/import', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  }

  // Users endpoints
  async getUsers(params?: any): Promise<ApiResponse<{ users: User[]; total: number; page: number; limit: number }>> {
    const response = await this.client.get('/users', { params });
    return response.data;
  }

  async getUser(id: string): Promise<ApiResponse<User>> {
    const response = await this.client.get(`/users/${id}`);
    return response.data;
  }

  async getCurrentUser(): Promise<ApiResponse<User>> {
    const response = await this.client.get('/users/me');
    return response.data;
  }

  async updateUser(id: string, data: Partial<User>): Promise<ApiResponse<User>> {
    const response = await this.client.put(`/users/${id}`, data);
    return response.data;
  }

  async updateProfile(data: Partial<User>): Promise<ApiResponse<User>> {
    const response = await this.client.put('/users/me', data);
    return response.data;
  }

  async changePassword(currentPassword: string, newPassword: string): Promise<ApiResponse> {
    const response = await this.client.post('/users/change-password', {
      currentPassword,
      newPassword,
    });
    return response.data;
  }

  // Dashboard endpoints
  async getDashboardMetrics(): Promise<ApiResponse<any>> {
    const response = await this.client.get('/dashboard/metrics');
    return response.data;
  }

  async getRecentCalls(limit: number = 10): Promise<ApiResponse<any[]>> {
    const response = await this.client.get('/dashboard/recent-calls', { params: { limit } });
    return response.data;
  }

  // Analytics endpoints
  async getAnalytics(timeRange?: string): Promise<ApiResponse<any>> {
    const response = await this.client.get('/analytics', { params: { timeRange } });
    return response.data;
  }

  async getCallAnalytics(params?: any): Promise<ApiResponse<any>> {
    const response = await this.client.get('/analytics/calls', { params });
    return response.data;
  }

  async getCampaignAnalytics(params?: any): Promise<ApiResponse<any>> {
    const response = await this.client.get('/analytics/campaigns', { params });
    return response.data;
  }

  async getPerformanceMetrics(params?: any): Promise<ApiResponse<any>> {
    const response = await this.client.get('/analytics/performance', { params });
    return response.data;
  }

  // Subscription endpoints
  async getCurrentSubscription(): Promise<ApiResponse<{ subscription: Subscription; features: any }>> {
    const response = await this.client.get('/subscription/current');
    return response.data;
  }

  async getSubscriptionUsage(): Promise<ApiResponse<SubscriptionUsage>> {
    const response = await this.client.get('/subscription/usage');
    return response.data;
  }

  async getSubscriptionPlans(): Promise<ApiResponse<any[]>> {
    const response = await this.client.get('/subscription/plans');
    return response.data;
  }

  async createSubscription(plan: string, paymentMethodId?: string): Promise<ApiResponse<Subscription>> {
    const response = await this.client.post('/subscription/create', { plan, paymentMethodId });
    return response.data;
  }

  async updateSubscription(plan: string): Promise<ApiResponse<Subscription>> {
    const response = await this.client.put('/subscription/update', { plan });
    return response.data;
  }

  async cancelSubscription(): Promise<ApiResponse> {
    const response = await this.client.post('/subscription/cancel');
    return response.data;
  }

  async createPaymentIntent(plan: string): Promise<ApiResponse<{ clientSecret: string; amount: number; currency: string }>> {
    const response = await this.client.post('/subscription/payment-intent', { plan });
    return response.data;
  }

  async getBillingHistory(): Promise<ApiResponse<any[]>> {
    const response = await this.client.get('/subscription/billing-history');
    return response.data;
  }

  async checkFeatureAccess(feature: string): Promise<ApiResponse<{ feature: string; hasAccess: boolean }>> {
    const response = await this.client.get(`/subscription/feature/${feature}`);
    return response.data;
  }

  async checkUsageLimit(resource: string): Promise<ApiResponse<{ resource: string; withinLimit: boolean }>> {
    const response = await this.client.get(`/subscription/limit/${resource}`);
    return response.data;
  }
}

// Create and export API client instance
export const apiClient = new ApiClient();

// WebSocket connection helper
export class WebSocketClient {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  connect(token: string) {
    try {
      this.ws = new WebSocket(`${WS_BASE_URL}?token=${token}`);
      
      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.reconnectAttempts = 0;
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.handleMessage(data);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      this.ws.onclose = () => {
        console.log('WebSocket disconnected');
        this.attemptReconnect(token);
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  send(data: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  private attemptReconnect(token: string) {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      setTimeout(() => {
        console.log(`Attempting to reconnect WebSocket (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
        this.connect(token);
      }, this.reconnectDelay * this.reconnectAttempts);
    }
  }

  private handleMessage(data: any) {
    // Emit custom events for different message types
    const event = new CustomEvent('websocket-message', { detail: data });
    window.dispatchEvent(event);

    // Handle specific message types
    switch (data.type) {
      case 'call_update':
        window.dispatchEvent(new CustomEvent('call-update', { detail: data.payload }));
        break;
      case 'campaign_update':
        window.dispatchEvent(new CustomEvent('campaign-update', { detail: data.payload }));
        break;
      case 'metrics_update':
        window.dispatchEvent(new CustomEvent('metrics-update', { detail: data.payload }));
        break;
      default:
        console.log('Unhandled WebSocket message type:', data.type);
    }
  }
}

export const wsClient = new WebSocketClient();