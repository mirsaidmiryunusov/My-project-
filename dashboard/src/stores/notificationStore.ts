/**
 * Notification Store for Project GeminiVoiceConnect Dashboard
 * 
 * This store manages application notifications, alerts, and user
 * notification preferences using Zustand for state management.
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
  category: 'system' | 'security' | 'performance' | 'business' | 'user';
  priority: 'low' | 'medium' | 'high' | 'critical';
  actions?: Array<{
    label: string;
    action: string;
    variant?: 'primary' | 'secondary' | 'danger';
  }>;
  metadata?: Record<string, any>;
  expiresAt?: string;
  sticky?: boolean;
}

export interface NotificationPreferences {
  email: {
    enabled: boolean;
    categories: string[];
    frequency: 'immediate' | 'hourly' | 'daily';
  };
  push: {
    enabled: boolean;
    categories: string[];
    quietHours: {
      enabled: boolean;
      start: string;
      end: string;
    };
  };
  sms: {
    enabled: boolean;
    categories: string[];
    emergencyOnly: boolean;
  };
  inApp: {
    enabled: boolean;
    autoMarkRead: boolean;
    showToasts: boolean;
  };
}

interface NotificationState {
  notifications: Notification[];
  preferences: NotificationPreferences;
  unreadCount: number;
  isLoading: boolean;
  error: string | null;
}

interface NotificationActions {
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp'>) => void;
  markAsRead: (id: string) => void;
  markAllAsRead: () => void;
  removeNotification: (id: string) => void;
  clearAll: () => void;
  clearExpired: () => void;
  updatePreferences: (preferences: Partial<NotificationPreferences>) => void;
  executeAction: (notificationId: string, actionId: string) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

type NotificationStore = NotificationState & NotificationActions;

const defaultPreferences: NotificationPreferences = {
  email: {
    enabled: true,
    categories: ['system', 'security', 'business'],
    frequency: 'immediate',
  },
  push: {
    enabled: true,
    categories: ['system', 'security', 'performance', 'business'],
    quietHours: {
      enabled: true,
      start: '22:00',
      end: '08:00',
    },
  },
  sms: {
    enabled: false,
    categories: ['security'],
    emergencyOnly: true,
  },
  inApp: {
    enabled: true,
    autoMarkRead: false,
    showToasts: true,
  },
};

const initialNotifications: Notification[] = [
  {
    id: '1',
    type: 'warning',
    title: 'High GPU Usage Alert',
    message: 'GPU usage has exceeded 85% for the last 15 minutes. Consider scaling resources or optimizing workloads.',
    timestamp: new Date(Date.now() - 300000).toISOString(),
    read: false,
    category: 'performance',
    priority: 'high',
    actions: [
      { label: 'View GPU Metrics', action: 'view_gpu_metrics', variant: 'primary' },
      { label: 'Scale Resources', action: 'scale_gpu_resources', variant: 'secondary' },
      { label: 'Dismiss', action: 'dismiss', variant: 'secondary' },
    ],
    metadata: {
      gpuUsage: 87,
      duration: 15,
      threshold: 85,
    },
  },
  {
    id: '2',
    type: 'error',
    title: 'Modem Connection Lost',
    message: 'Modem #47 has lost connection and is not responding to health checks. Automatic failover initiated.',
    timestamp: new Date(Date.now() - 600000).toISOString(),
    read: false,
    category: 'system',
    priority: 'critical',
    actions: [
      { label: 'Restart Modem', action: 'restart_modem', variant: 'primary' },
      { label: 'View Diagnostics', action: 'view_diagnostics', variant: 'secondary' },
      { label: 'Contact Support', action: 'contact_support', variant: 'secondary' },
    ],
    metadata: {
      modemId: '47',
      lastSeen: new Date(Date.now() - 900000).toISOString(),
      failoverActive: true,
    },
    sticky: true,
  },
  {
    id: '3',
    type: 'success',
    title: 'Campaign Completed Successfully',
    message: 'SMS Campaign "Holiday Promotion 2024" completed with 96.2% delivery rate and 18.5% conversion rate.',
    timestamp: new Date(Date.now() - 1800000).toISOString(),
    read: false,
    category: 'business',
    priority: 'medium',
    actions: [
      { label: 'View Report', action: 'view_campaign_report', variant: 'primary' },
      { label: 'Create Similar', action: 'create_similar_campaign', variant: 'secondary' },
    ],
    metadata: {
      campaignId: 'camp_holiday_2024',
      deliveryRate: 96.2,
      conversionRate: 18.5,
      totalSent: 15420,
    },
  },
  {
    id: '4',
    type: 'info',
    title: 'System Maintenance Scheduled',
    message: 'Scheduled maintenance window: Dec 15, 2024 02:00-04:00 UTC. Expected downtime: 30 minutes.',
    timestamp: new Date(Date.now() - 3600000).toISOString(),
    read: true,
    category: 'system',
    priority: 'low',
    actions: [
      { label: 'View Details', action: 'view_maintenance_details', variant: 'primary' },
      { label: 'Set Reminder', action: 'set_reminder', variant: 'secondary' },
    ],
    metadata: {
      maintenanceWindow: {
        start: '2024-12-15T02:00:00Z',
        end: '2024-12-15T04:00:00Z',
        expectedDowntime: 30,
      },
    },
    expiresAt: new Date(Date.now() + 86400000).toISOString(), // Expires in 24 hours
  },
  {
    id: '5',
    type: 'warning',
    title: 'Unusual Call Pattern Detected',
    message: 'AI analytics detected unusual call patterns that may indicate fraudulent activity. Review recommended.',
    timestamp: new Date(Date.now() - 7200000).toISOString(),
    read: false,
    category: 'security',
    priority: 'high',
    actions: [
      { label: 'Review Patterns', action: 'review_call_patterns', variant: 'primary' },
      { label: 'Block Suspicious', action: 'block_suspicious_calls', variant: 'danger' },
      { label: 'False Positive', action: 'mark_false_positive', variant: 'secondary' },
    ],
    metadata: {
      suspiciousCallCount: 47,
      timeWindow: '2 hours',
      confidenceScore: 0.85,
    },
  },
];

export const useNotificationStore = create<NotificationStore>()(
  persist(
    (set, get) => ({
      notifications: initialNotifications,
      preferences: defaultPreferences,
      unreadCount: initialNotifications.filter(n => !n.read).length,
      isLoading: false,
      error: null,

      addNotification: (notification: Omit<Notification, 'id' | 'timestamp'>) => {
        const newNotification: Notification = {
          ...notification,
          id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
          timestamp: new Date().toISOString(),
        };

        const currentNotifications = get().notifications;
        const updatedNotifications = [newNotification, ...currentNotifications];

        // Limit to 100 notifications
        if (updatedNotifications.length > 100) {
          updatedNotifications.splice(100);
        }

        const unreadCount = updatedNotifications.filter(n => !n.read).length;

        set({
          notifications: updatedNotifications,
          unreadCount,
        });

        // Show toast notification if enabled
        const { preferences } = get();
        if (preferences.inApp.showToasts) {
          // This would trigger a toast notification in the UI
          console.log('Toast notification:', newNotification.title);
        }
      },

      markAsRead: (id: string) => {
        const currentNotifications = get().notifications;
        const updatedNotifications = currentNotifications.map(notification =>
          notification.id === id ? { ...notification, read: true } : notification
        );

        const unreadCount = updatedNotifications.filter(n => !n.read).length;

        set({
          notifications: updatedNotifications,
          unreadCount,
        });
      },

      markAllAsRead: () => {
        const currentNotifications = get().notifications;
        const updatedNotifications = currentNotifications.map(notification => ({
          ...notification,
          read: true,
        }));

        set({
          notifications: updatedNotifications,
          unreadCount: 0,
        });
      },

      removeNotification: (id: string) => {
        const currentNotifications = get().notifications;
        const updatedNotifications = currentNotifications.filter(n => n.id !== id);
        const unreadCount = updatedNotifications.filter(n => !n.read).length;

        set({
          notifications: updatedNotifications,
          unreadCount,
        });
      },

      clearAll: () => {
        set({
          notifications: [],
          unreadCount: 0,
        });
      },

      clearExpired: () => {
        const now = new Date();
        const currentNotifications = get().notifications;
        const validNotifications = currentNotifications.filter(notification => {
          if (!notification.expiresAt) return true;
          return new Date(notification.expiresAt) > now;
        });

        const unreadCount = validNotifications.filter(n => !n.read).length;

        set({
          notifications: validNotifications,
          unreadCount,
        });
      },

      updatePreferences: (newPreferences: Partial<NotificationPreferences>) => {
        const currentPreferences = get().preferences;
        const updatedPreferences = {
          ...currentPreferences,
          ...newPreferences,
        };

        set({ preferences: updatedPreferences });
      },

      executeAction: (notificationId: string, actionId: string) => {
        const notification = get().notifications.find(n => n.id === notificationId);
        if (!notification) return;

        const action = notification.actions?.find(a => a.action === actionId);
        if (!action) return;

        // Handle built-in actions
        switch (actionId) {
          case 'dismiss':
            get().removeNotification(notificationId);
            break;
          case 'mark_read':
            get().markAsRead(notificationId);
            break;
          default:
            // Custom action handling would go here
            console.log(`Executing action: ${actionId} for notification: ${notificationId}`);
            // Mark as read after action execution
            get().markAsRead(notificationId);
            break;
        }
      },

      setLoading: (loading: boolean) => {
        set({ isLoading: loading });
      },

      setError: (error: string | null) => {
        set({ error });
      },
    }),
    {
      name: 'notification-storage',
      partialize: (state) => ({
        preferences: state.preferences,
        // Don't persist notifications as they should be fresh on app load
      }),
    }
  )
);

// Auto-clear expired notifications every 5 minutes
setInterval(() => {
  useNotificationStore.getState().clearExpired();
}, 5 * 60 * 1000);

// Utility functions
export const createNotification = (
  type: Notification['type'],
  title: string,
  message: string,
  options?: Partial<Omit<Notification, 'id' | 'timestamp' | 'type' | 'title' | 'message'>>
): Omit<Notification, 'id' | 'timestamp'> => ({
  type,
  title,
  message,
  read: false,
  category: 'system',
  priority: 'medium',
  ...options,
});

export const createSystemAlert = (
  title: string,
  message: string,
  priority: Notification['priority'] = 'medium'
): Omit<Notification, 'id' | 'timestamp'> =>
  createNotification('warning', title, message, {
    category: 'system',
    priority,
  });

export const createSecurityAlert = (
  title: string,
  message: string,
  priority: Notification['priority'] = 'high'
): Omit<Notification, 'id' | 'timestamp'> =>
  createNotification('error', title, message, {
    category: 'security',
    priority,
    sticky: true,
  });

export const createBusinessNotification = (
  title: string,
  message: string,
  type: Notification['type'] = 'info'
): Omit<Notification, 'id' | 'timestamp'> =>
  createNotification(type, title, message, {
    category: 'business',
    priority: 'medium',
  });