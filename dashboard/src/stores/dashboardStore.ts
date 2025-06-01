import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { apiClient, wsClient } from '../services/api';

// Types
interface DashboardMetrics {
  totalCalls: number;
  activeCampaigns: number;
  totalContacts: number;
  conversionRate: number;
  avgCallDuration: number;
  successfulCalls: number;
  failedCalls: number;
  pendingCalls: number;
  totalRevenue: number;
  monthlyGrowth: number;
}

interface CallData {
  id: string;
  customerName: string;
  phoneNumber: string;
  status: 'completed' | 'failed' | 'in-progress' | 'scheduled';
  duration: number;
  timestamp: string;
  campaignId?: string;
  outcome?: string;
  notes?: string;
  recording?: string;
}

interface CampaignData {
  id: string;
  name: string;
  status: 'active' | 'paused' | 'completed' | 'draft';
  totalCalls: number;
  successfulCalls: number;
  conversionRate: number;
  startDate: string;
  endDate?: string;
  targetAudience: string;
  script?: string;
  budget?: number;
  spent?: number;
}

interface ContactData {
  id: string;
  firstName: string;
  lastName: string;
  email: string;
  phoneNumber: string;
  status: 'active' | 'inactive' | 'do-not-call';
  tags: string[];
  lastContact?: string;
  notes?: string;
  customFields?: Record<string, any>;
}

interface AnalyticsData {
  callVolume: Array<{ date: string; calls: number; successful: number; failed: number }>;
  conversionTrends: Array<{ date: string; rate: number }>;
  campaignPerformance: Array<{ campaignId: string; name: string; calls: number; conversions: number; revenue: number }>;
  hourlyDistribution: Array<{ hour: number; calls: number; successRate: number }>;
  geographicData: Array<{ region: string; calls: number; successRate: number }>;
}

interface DashboardState {
  // Data
  metrics: DashboardMetrics | null;
  recentCalls: CallData[];
  campaigns: CampaignData[];
  contacts: ContactData[];
  analytics: AnalyticsData | null;
  
  // UI State
  loading: boolean;
  error: string | null;
  lastUpdated: string | null;
  
  // Real-time updates
  isConnected: boolean;
  liveMetrics: Partial<DashboardMetrics>;
}

interface DashboardActions {
  // Data fetching
  fetchDashboardData: () => Promise<void>;
  fetchMetrics: () => Promise<void>;
  fetchRecentCalls: (limit?: number) => Promise<void>;
  fetchCampaigns: () => Promise<void>;
  fetchContacts: (page?: number, limit?: number) => Promise<void>;
  fetchAnalytics: (timeRange?: string) => Promise<void>;
  
  // Real-time updates
  connectRealTime: () => void;
  disconnectRealTime: () => void;
  updateLiveMetrics: (metrics: Partial<DashboardMetrics>) => void;
  
  // Actions
  createCampaign: (campaign: Partial<CampaignData>) => Promise<boolean>;
  updateCampaign: (id: string, updates: Partial<CampaignData>) => Promise<boolean>;
  deleteCampaign: (id: string) => Promise<boolean>;
  
  createContact: (contact: Partial<ContactData>) => Promise<boolean>;
  updateContact: (id: string, updates: Partial<ContactData>) => Promise<boolean>;
  deleteContact: (id: string) => Promise<boolean>;
  
  // Utility
  clearError: () => void;
  setLoading: (loading: boolean) => void;
  refreshData: () => Promise<void>;
}

type DashboardStore = DashboardState & DashboardActions;

const initialState: DashboardState = {
  metrics: null,
  recentCalls: [],
  campaigns: [],
  contacts: [],
  analytics: null,
  loading: false,
  error: null,
  lastUpdated: null,
  isConnected: false,
  liveMetrics: {},
};

export const useDashboardStore = create<DashboardStore>()(
  persist(
    (set, get) => ({
      ...initialState,

      fetchDashboardData: async () => {
        set({ loading: true, error: null });
        
        try {
          await Promise.all([
            get().fetchMetrics(),
            get().fetchRecentCalls(10),
            get().fetchCampaigns(),
            get().fetchAnalytics('7d'),
          ]);
          
          set({ 
            loading: false, 
            lastUpdated: new Date().toISOString(),
          });
        } catch (error) {
          set({
            loading: false,
            error: error instanceof Error ? error.message : 'Failed to fetch dashboard data',
          });
        }
      },

      fetchMetrics: async () => {
        try {
          const response = await apiClient.client.get('/dashboard/overview');
          
          if (response.data.success && response.data.data) {
            set({ metrics: response.data.data });
          } else {
            throw new Error(response.data.message || 'Failed to fetch metrics');
          }
        } catch (error) {
          console.error('Failed to fetch metrics:', error);
          throw error;
        }
      },

      fetchRecentCalls: async (limit = 10) => {
        try {
          const response = await apiClient.getRecentCalls(limit);
          
          if (response.success && response.data) {
            set({ recentCalls: response.data });
          } else {
            throw new Error(response.message || 'Failed to fetch recent calls');
          }
        } catch (error) {
          console.error('Failed to fetch recent calls:', error);
          throw error;
        }
      },

      fetchCampaigns: async () => {
        try {
          const response = await apiClient.getCampaigns();
          
          if (response.success && response.data) {
            set({ campaigns: response.data });
          } else {
            throw new Error(response.message || 'Failed to fetch campaigns');
          }
        } catch (error) {
          console.error('Failed to fetch campaigns:', error);
          throw error;
        }
      },

      fetchContacts: async (page = 1, limit = 50) => {
        try {
          const response = await apiClient.getContacts(page, limit);
          
          if (response.success && response.data) {
            set({ contacts: response.data });
          } else {
            throw new Error(response.message || 'Failed to fetch contacts');
          }
        } catch (error) {
          console.error('Failed to fetch contacts:', error);
          throw error;
        }
      },

      fetchAnalytics: async (timeRange = '7d') => {
        try {
          const response = await apiClient.getAnalytics(timeRange);
          
          if (response.success && response.data) {
            set({ analytics: response.data });
          } else {
            throw new Error(response.message || 'Failed to fetch analytics');
          }
        } catch (error) {
          console.error('Failed to fetch analytics:', error);
          throw error;
        }
      },

      connectRealTime: () => {
        if (!get().isConnected) {
          wsClient.on('metrics-update', (data: Partial<DashboardMetrics>) => {
            get().updateLiveMetrics(data);
          });
          
          wsClient.on('call-update', (callData: CallData) => {
            const { recentCalls } = get();
            const updatedCalls = [callData, ...recentCalls.slice(0, 9)];
            set({ recentCalls: updatedCalls });
          });
          
          wsClient.on('campaign-update', (campaignData: CampaignData) => {
            const { campaigns } = get();
            const updatedCampaigns = campaigns.map(c => 
              c.id === campaignData.id ? campaignData : c
            );
            set({ campaigns: updatedCampaigns });
          });
          
          set({ isConnected: true });
        }
      },

      disconnectRealTime: () => {
        wsClient.off('metrics-update');
        wsClient.off('call-update');
        wsClient.off('campaign-update');
        set({ isConnected: false });
      },

      updateLiveMetrics: (newMetrics: Partial<DashboardMetrics>) => {
        const { liveMetrics } = get();
        set({ 
          liveMetrics: { ...liveMetrics, ...newMetrics },
        });
      },

      createCampaign: async (campaign: Partial<CampaignData>) => {
        set({ loading: true, error: null });
        
        try {
          const response = await apiClient.createCampaign(campaign);
          
          if (response.success && response.data) {
            const { campaigns } = get();
            set({ 
              campaigns: [...campaigns, response.data],
              loading: false,
            });
            return true;
          } else {
            set({
              loading: false,
              error: response.message || 'Failed to create campaign',
            });
            return false;
          }
        } catch (error) {
          set({
            loading: false,
            error: error instanceof Error ? error.message : 'Failed to create campaign',
          });
          return false;
        }
      },

      updateCampaign: async (id: string, updates: Partial<CampaignData>) => {
        set({ loading: true, error: null });
        
        try {
          const response = await apiClient.updateCampaign(id, updates);
          
          if (response.success && response.data) {
            const { campaigns } = get();
            const updatedCampaigns = campaigns.map(c => 
              c.id === id ? response.data : c
            );
            set({ 
              campaigns: updatedCampaigns,
              loading: false,
            });
            return true;
          } else {
            set({
              loading: false,
              error: response.message || 'Failed to update campaign',
            });
            return false;
          }
        } catch (error) {
          set({
            loading: false,
            error: error instanceof Error ? error.message : 'Failed to update campaign',
          });
          return false;
        }
      },

      deleteCampaign: async (id: string) => {
        set({ loading: true, error: null });
        
        try {
          const response = await apiClient.deleteCampaign(id);
          
          if (response.success) {
            const { campaigns } = get();
            const updatedCampaigns = campaigns.filter(c => c.id !== id);
            set({ 
              campaigns: updatedCampaigns,
              loading: false,
            });
            return true;
          } else {
            set({
              loading: false,
              error: response.message || 'Failed to delete campaign',
            });
            return false;
          }
        } catch (error) {
          set({
            loading: false,
            error: error instanceof Error ? error.message : 'Failed to delete campaign',
          });
          return false;
        }
      },

      createContact: async (contact: Partial<ContactData>) => {
        set({ loading: true, error: null });
        
        try {
          const response = await apiClient.createContact(contact);
          
          if (response.success && response.data) {
            const { contacts } = get();
            set({ 
              contacts: [...contacts, response.data],
              loading: false,
            });
            return true;
          } else {
            set({
              loading: false,
              error: response.message || 'Failed to create contact',
            });
            return false;
          }
        } catch (error) {
          set({
            loading: false,
            error: error instanceof Error ? error.message : 'Failed to create contact',
          });
          return false;
        }
      },

      updateContact: async (id: string, updates: Partial<ContactData>) => {
        set({ loading: true, error: null });
        
        try {
          const response = await apiClient.updateContact(id, updates);
          
          if (response.success && response.data) {
            const { contacts } = get();
            const updatedContacts = contacts.map(c => 
              c.id === id ? response.data : c
            );
            set({ 
              contacts: updatedContacts,
              loading: false,
            });
            return true;
          } else {
            set({
              loading: false,
              error: response.message || 'Failed to update contact',
            });
            return false;
          }
        } catch (error) {
          set({
            loading: false,
            error: error instanceof Error ? error.message : 'Failed to update contact',
          });
          return false;
        }
      },

      deleteContact: async (id: string) => {
        set({ loading: true, error: null });
        
        try {
          const response = await apiClient.deleteContact(id);
          
          if (response.success) {
            const { contacts } = get();
            const updatedContacts = contacts.filter(c => c.id !== id);
            set({ 
              contacts: updatedContacts,
              loading: false,
            });
            return true;
          } else {
            set({
              loading: false,
              error: response.message || 'Failed to delete contact',
            });
            return false;
          }
        } catch (error) {
          set({
            loading: false,
            error: error instanceof Error ? error.message : 'Failed to delete contact',
          });
          return false;
        }
      },

      refreshData: async () => {
        await get().fetchDashboardData();
      },

      clearError: () => {
        set({ error: null });
      },

      setLoading: (loading: boolean) => {
        set({ loading });
      },
    }),
    {
      name: 'dashboard-storage',
      partialize: (state) => ({
        metrics: state.metrics,
        lastUpdated: state.lastUpdated,
        // Don't persist real-time data
      }),
    }
  )
);

// Helper functions
export const formatMetricValue = (value: number, type: 'currency' | 'percentage' | 'number' | 'duration') => {
  switch (type) {
    case 'currency':
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
      }).format(value);
    case 'percentage':
      return `${value.toFixed(1)}%`;
    case 'duration':
      const minutes = Math.floor(value / 60);
      const seconds = value % 60;
      return `${minutes}:${seconds.toString().padStart(2, '0')}`;
    default:
      return value.toLocaleString();
  }
};

export const getStatusColor = (status: string) => {
  switch (status.toLowerCase()) {
    case 'active':
    case 'completed':
    case 'successful':
      return 'green';
    case 'paused':
    case 'pending':
    case 'in-progress':
      return 'yellow';
    case 'failed':
    case 'inactive':
      return 'red';
    case 'draft':
      return 'gray';
    default:
      return 'blue';
  }
};

export const calculateTrend = (current: number, previous: number) => {
  if (previous === 0) return 0;
  return ((current - previous) / previous) * 100;
};