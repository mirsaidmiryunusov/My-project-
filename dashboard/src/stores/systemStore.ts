/**
 * System Store for Project GeminiVoiceConnect Dashboard
 * 
 * This store manages system status, health monitoring, and real-time
 * system metrics using Zustand for state management.
 */

import { create } from 'zustand';

export interface ModemStatus {
  id: string;
  status: 'online' | 'offline' | 'error' | 'maintenance';
  signalStrength: number;
  carrier: string;
  lastSeen: string;
  activeCalls: number;
  totalCalls: number;
  errorCount: number;
  temperature?: number;
  location?: string;
}

export interface SystemMetrics {
  timestamp: string;
  cpuUsage: number;
  memoryUsage: number;
  gpuUsage: number;
  diskUsage: number;
  networkIn: number;
  networkOut: number;
  activeCalls: number;
  smsQueue: number;
  errorRate: number;
}

export interface SystemStatus {
  overallHealth: 'healthy' | 'warning' | 'critical';
  modemsOnline: number;
  totalModems: number;
  gpuUsage: number;
  cpuUsage: number;
  memoryUsage: number;
  activeCalls: number;
  smsQueue: number;
  onlineAgents: number;
  todayRevenue: number;
  errorRate: number;
  uptime: string;
  lastUpdated: string;
}

export interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
  category: 'system' | 'security' | 'performance' | 'business';
  priority: 'low' | 'medium' | 'high' | 'critical';
  actions?: Array<{
    label: string;
    action: string;
  }>;
}

interface SystemState {
  systemStatus: SystemStatus;
  modems: ModemStatus[];
  metrics: SystemMetrics[];
  notifications: Notification[];
  isLoading: boolean;
  error: string | null;
  lastRefresh: string | null;
}

interface SystemActions {
  refreshSystemStatus: () => Promise<void>;
  refreshModemStatus: () => Promise<void>;
  addMetric: (metric: SystemMetrics) => void;
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp'>) => void;
  markNotificationRead: (id: string) => void;
  clearNotifications: () => void;
  setError: (error: string | null) => void;
  setLoading: (loading: boolean) => void;
}

type SystemStore = SystemState & SystemActions;

const initialSystemStatus: SystemStatus = {
  overallHealth: 'healthy',
  modemsOnline: 78,
  totalModems: 80,
  gpuUsage: 45,
  cpuUsage: 32,
  memoryUsage: 68,
  activeCalls: 23,
  smsQueue: 156,
  onlineAgents: 12,
  todayRevenue: 15420,
  errorRate: 0.02,
  uptime: '15d 8h 32m',
  lastUpdated: new Date().toISOString(),
};

const generateMockModems = (): ModemStatus[] => {
  return Array.from({ length: 80 }, (_, i) => ({
    id: `modem_${i + 1}`,
    status: Math.random() > 0.05 ? 'online' : Math.random() > 0.5 ? 'offline' : 'error',
    signalStrength: Math.floor(Math.random() * 100),
    carrier: ['Verizon', 'AT&T', 'T-Mobile', 'Sprint'][Math.floor(Math.random() * 4)],
    lastSeen: new Date(Date.now() - Math.random() * 3600000).toISOString(),
    activeCalls: Math.floor(Math.random() * 3),
    totalCalls: Math.floor(Math.random() * 1000),
    errorCount: Math.floor(Math.random() * 10),
    temperature: 35 + Math.random() * 20,
    location: `Rack ${Math.floor(i / 10) + 1}, Slot ${(i % 10) + 1}`,
  }));
};

const generateMockNotifications = (): Notification[] => {
  const notifications: Notification[] = [
    {
      id: '1',
      type: 'warning',
      title: 'High GPU Usage Detected',
      message: 'GPU usage has exceeded 80% for the last 10 minutes. Consider scaling resources.',
      timestamp: new Date(Date.now() - 300000).toISOString(),
      read: false,
      category: 'performance',
      priority: 'medium',
      actions: [
        { label: 'View Details', action: 'view_gpu_metrics' },
        { label: 'Scale Resources', action: 'scale_gpu' },
      ],
    },
    {
      id: '2',
      type: 'error',
      title: 'Modem Offline',
      message: 'Modem #47 has gone offline and is not responding to health checks.',
      timestamp: new Date(Date.now() - 600000).toISOString(),
      read: false,
      category: 'system',
      priority: 'high',
      actions: [
        { label: 'Restart Modem', action: 'restart_modem_47' },
        { label: 'View Logs', action: 'view_modem_logs_47' },
      ],
    },
    {
      id: '3',
      type: 'success',
      title: 'Campaign Completed',
      message: 'SMS Campaign "Summer Promotion" has completed successfully with 94% delivery rate.',
      timestamp: new Date(Date.now() - 900000).toISOString(),
      read: true,
      category: 'business',
      priority: 'low',
    },
    {
      id: '4',
      type: 'info',
      title: 'System Update Available',
      message: 'A new system update (v2.1.3) is available with performance improvements.',
      timestamp: new Date(Date.now() - 1800000).toISOString(),
      read: false,
      category: 'system',
      priority: 'low',
      actions: [
        { label: 'View Changelog', action: 'view_changelog' },
        { label: 'Schedule Update', action: 'schedule_update' },
      ],
    },
  ];

  return notifications;
};

export const useSystemStore = create<SystemStore>((set, get) => ({
  systemStatus: initialSystemStatus,
  modems: generateMockModems(),
  metrics: [],
  notifications: generateMockNotifications(),
  isLoading: false,
  error: null,
  lastRefresh: null,

  refreshSystemStatus: async () => {
    set({ isLoading: true, error: null });
    
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Generate updated status with some randomization
      const currentStatus = get().systemStatus;
      const updatedStatus: SystemStatus = {
        ...currentStatus,
        modemsOnline: Math.max(75, Math.min(80, currentStatus.modemsOnline + Math.floor(Math.random() * 6) - 3)),
        gpuUsage: Math.max(0, Math.min(100, currentStatus.gpuUsage + Math.floor(Math.random() * 20) - 10)),
        cpuUsage: Math.max(0, Math.min(100, currentStatus.cpuUsage + Math.floor(Math.random() * 20) - 10)),
        memoryUsage: Math.max(0, Math.min(100, currentStatus.memoryUsage + Math.floor(Math.random() * 10) - 5)),
        activeCalls: Math.max(0, currentStatus.activeCalls + Math.floor(Math.random() * 10) - 5),
        smsQueue: Math.max(0, currentStatus.smsQueue + Math.floor(Math.random() * 100) - 50),
        todayRevenue: currentStatus.todayRevenue + Math.floor(Math.random() * 1000),
        lastUpdated: new Date().toISOString(),
      };

      // Update overall health based on metrics
      if (updatedStatus.gpuUsage > 90 || updatedStatus.cpuUsage > 90 || updatedStatus.modemsOnline < 70) {
        updatedStatus.overallHealth = 'critical';
      } else if (updatedStatus.gpuUsage > 80 || updatedStatus.cpuUsage > 80 || updatedStatus.modemsOnline < 75) {
        updatedStatus.overallHealth = 'warning';
      } else {
        updatedStatus.overallHealth = 'healthy';
      }

      set({
        systemStatus: updatedStatus,
        isLoading: false,
        lastRefresh: new Date().toISOString(),
      });

      // Add new metric
      const newMetric: SystemMetrics = {
        timestamp: new Date().toISOString(),
        cpuUsage: updatedStatus.cpuUsage,
        memoryUsage: updatedStatus.memoryUsage,
        gpuUsage: updatedStatus.gpuUsage,
        diskUsage: Math.floor(Math.random() * 100),
        networkIn: Math.floor(Math.random() * 1000),
        networkOut: Math.floor(Math.random() * 1000),
        activeCalls: updatedStatus.activeCalls,
        smsQueue: updatedStatus.smsQueue,
        errorRate: Math.random() * 0.1,
      };

      get().addMetric(newMetric);

    } catch (error) {
      set({
        isLoading: false,
        error: error instanceof Error ? error.message : 'Failed to refresh system status',
      });
    }
  },

  refreshModemStatus: async () => {
    set({ isLoading: true });
    
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 800));
      
      // Update some modems randomly
      const currentModems = get().modems;
      const updatedModems = currentModems.map(modem => {
        if (Math.random() < 0.1) { // 10% chance to update each modem
          return {
            ...modem,
            signalStrength: Math.max(0, Math.min(100, modem.signalStrength + Math.floor(Math.random() * 20) - 10)),
            lastSeen: new Date().toISOString(),
            activeCalls: Math.max(0, Math.min(3, modem.activeCalls + Math.floor(Math.random() * 3) - 1)),
            temperature: Math.max(20, Math.min(70, (modem.temperature || 40) + Math.random() * 4 - 2)),
          };
        }
        return modem;
      });

      set({
        modems: updatedModems,
        isLoading: false,
      });

    } catch (error) {
      set({
        isLoading: false,
        error: error instanceof Error ? error.message : 'Failed to refresh modem status',
      });
    }
  },

  addMetric: (metric: SystemMetrics) => {
    const currentMetrics = get().metrics;
    const updatedMetrics = [...currentMetrics, metric];
    
    // Keep only last 100 metrics
    if (updatedMetrics.length > 100) {
      updatedMetrics.splice(0, updatedMetrics.length - 100);
    }
    
    set({ metrics: updatedMetrics });
  },

  addNotification: (notification: Omit<Notification, 'id' | 'timestamp'>) => {
    const newNotification: Notification = {
      ...notification,
      id: Date.now().toString(),
      timestamp: new Date().toISOString(),
    };

    const currentNotifications = get().notifications;
    set({
      notifications: [newNotification, ...currentNotifications],
    });
  },

  markNotificationRead: (id: string) => {
    const currentNotifications = get().notifications;
    const updatedNotifications = currentNotifications.map(notification =>
      notification.id === id ? { ...notification, read: true } : notification
    );
    
    set({ notifications: updatedNotifications });
  },

  clearNotifications: () => {
    set({ notifications: [] });
  },

  setError: (error: string | null) => {
    set({ error });
  },

  setLoading: (loading: boolean) => {
    set({ isLoading: loading });
  },
}));

// Auto-refresh system status every 30 seconds
setInterval(() => {
  useSystemStore.getState().refreshSystemStatus();
}, 30000);