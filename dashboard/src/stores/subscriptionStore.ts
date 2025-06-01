import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { apiClient, Subscription, SubscriptionUsage } from '../services/api';

interface SubscriptionState {
  // State
  subscription: Subscription | null;
  usage: SubscriptionUsage | null;
  plans: any[];
  billingHistory: any[];
  loading: boolean;
  error: string | null;

  // Actions
  fetchCurrentSubscription: () => Promise<void>;
  fetchUsage: () => Promise<void>;
  fetchPlans: () => Promise<void>;
  fetchBillingHistory: () => Promise<void>;
  createSubscription: (plan: string, paymentMethodId?: string) => Promise<boolean>;
  updateSubscription: (plan: string) => Promise<boolean>;
  cancelSubscription: () => Promise<boolean>;
  createPaymentIntent: (plan: string) => Promise<{ clientSecret: string; amount: number; currency: string } | null>;
  checkFeatureAccess: (feature: string) => Promise<boolean>;
  checkUsageLimit: (resource: string) => Promise<boolean>;
  clearError: () => void;
  reset: () => void;
}

export const useSubscriptionStore = create<SubscriptionState>()(
  persist(
    (set, get) => ({
      // Initial state
      subscription: null,
      usage: null,
      plans: [],
      billingHistory: [],
      loading: false,
      error: null,

      // Actions
      fetchCurrentSubscription: async () => {
        set({ loading: true, error: null });
        try {
          const response = await apiClient.getCurrentSubscription();
          if (response.success && response.data) {
            set({ 
              subscription: response.data.subscription,
              loading: false 
            });
          } else {
            set({ 
              error: response.message || 'Failed to fetch subscription',
              loading: false 
            });
          }
        } catch (error) {
          set({ 
            error: error instanceof Error ? error.message : 'Failed to fetch subscription',
            loading: false 
          });
        }
      },

      fetchUsage: async () => {
        set({ loading: true, error: null });
        try {
          const response = await apiClient.getSubscriptionUsage();
          if (response.success && response.data) {
            set({ 
              usage: response.data,
              subscription: response.data.subscription,
              loading: false 
            });
          } else {
            set({ 
              error: response.message || 'Failed to fetch usage data',
              loading: false 
            });
          }
        } catch (error) {
          set({ 
            error: error instanceof Error ? error.message : 'Failed to fetch usage data',
            loading: false 
          });
        }
      },

      fetchPlans: async () => {
        set({ loading: true, error: null });
        try {
          const response = await apiClient.getSubscriptionPlans();
          if (response.success && response.data) {
            set({ 
              plans: response.data,
              loading: false 
            });
          } else {
            set({ 
              error: response.message || 'Failed to fetch plans',
              loading: false 
            });
          }
        } catch (error) {
          set({ 
            error: error instanceof Error ? error.message : 'Failed to fetch plans',
            loading: false 
          });
        }
      },

      fetchBillingHistory: async () => {
        set({ loading: true, error: null });
        try {
          const response = await apiClient.getBillingHistory();
          if (response.success && response.data) {
            set({ 
              billingHistory: response.data,
              loading: false 
            });
          } else {
            set({ 
              error: response.message || 'Failed to fetch billing history',
              loading: false 
            });
          }
        } catch (error) {
          set({ 
            error: error instanceof Error ? error.message : 'Failed to fetch billing history',
            loading: false 
          });
        }
      },

      createSubscription: async (plan: string, paymentMethodId?: string) => {
        set({ loading: true, error: null });
        try {
          const response = await apiClient.createSubscription(plan, paymentMethodId);
          if (response.success && response.data) {
            set({ 
              subscription: response.data,
              loading: false 
            });
            // Refresh usage data
            await get().fetchUsage();
            return true;
          } else {
            set({ 
              error: response.message || 'Failed to create subscription',
              loading: false 
            });
            return false;
          }
        } catch (error) {
          set({ 
            error: error instanceof Error ? error.message : 'Failed to create subscription',
            loading: false 
          });
          return false;
        }
      },

      updateSubscription: async (plan: string) => {
        set({ loading: true, error: null });
        try {
          const response = await apiClient.updateSubscription(plan);
          if (response.success && response.data) {
            set({ 
              subscription: response.data,
              loading: false 
            });
            // Refresh usage data
            await get().fetchUsage();
            return true;
          } else {
            set({ 
              error: response.message || 'Failed to update subscription',
              loading: false 
            });
            return false;
          }
        } catch (error) {
          set({ 
            error: error instanceof Error ? error.message : 'Failed to update subscription',
            loading: false 
          });
          return false;
        }
      },

      cancelSubscription: async () => {
        set({ loading: true, error: null });
        try {
          const response = await apiClient.cancelSubscription();
          if (response.success) {
            // Refresh subscription data
            await get().fetchCurrentSubscription();
            await get().fetchUsage();
            set({ loading: false });
            return true;
          } else {
            set({ 
              error: response.message || 'Failed to cancel subscription',
              loading: false 
            });
            return false;
          }
        } catch (error) {
          set({ 
            error: error instanceof Error ? error.message : 'Failed to cancel subscription',
            loading: false 
          });
          return false;
        }
      },

      createPaymentIntent: async (plan: string) => {
        set({ loading: true, error: null });
        try {
          const response = await apiClient.createPaymentIntent(plan);
          if (response.success && response.data) {
            set({ loading: false });
            return response.data;
          } else {
            set({ 
              error: response.message || 'Failed to create payment intent',
              loading: false 
            });
            return null;
          }
        } catch (error) {
          set({ 
            error: error instanceof Error ? error.message : 'Failed to create payment intent',
            loading: false 
          });
          return null;
        }
      },

      checkFeatureAccess: async (feature: string) => {
        try {
          const response = await apiClient.checkFeatureAccess(feature);
          if (response.success && response.data) {
            return response.data.hasAccess;
          }
          return false;
        } catch (error) {
          console.error('Failed to check feature access:', error);
          return false;
        }
      },

      checkUsageLimit: async (resource: string) => {
        try {
          const response = await apiClient.checkUsageLimit(resource);
          if (response.success && response.data) {
            return response.data.withinLimit;
          }
          return false;
        } catch (error) {
          console.error('Failed to check usage limit:', error);
          return false;
        }
      },

      clearError: () => {
        set({ error: null });
      },

      reset: () => {
        set({
          subscription: null,
          usage: null,
          plans: [],
          billingHistory: [],
          loading: false,
          error: null,
        });
      },
    }),
    {
      name: 'subscription-store',
      partialize: (state) => ({
        subscription: state.subscription,
        usage: state.usage,
        plans: state.plans,
      }),
    }
  )
);

// Helper functions for subscription features
export const getSubscriptionFeatures = (subscription: Subscription | null) => {
  if (!subscription) return null;
  try {
    return JSON.parse(subscription.features);
  } catch {
    return null;
  }
};

export const hasFeatureAccess = (subscription: Subscription | null, feature: string) => {
  const features = getSubscriptionFeatures(subscription);
  return features?.[feature] === true;
};

export const getUsagePercentage = (used: number, limit: number) => {
  if (limit === -1) return 0; // Unlimited
  if (limit === 0) return 100;
  return Math.min((used / limit) * 100, 100);
};

export const isUsageLimitReached = (used: number, limit: number) => {
  if (limit === -1) return false; // Unlimited
  return used >= limit;
};

export const formatUsageDisplay = (used: number, limit: number) => {
  if (limit === -1) return `${used.toLocaleString()} / Unlimited`;
  return `${used.toLocaleString()} / ${limit.toLocaleString()}`;
};

export const getPlanDisplayName = (plan: string) => {
  const planNames: Record<string, string> = {
    FREE: 'Free',
    STARTER: 'Starter',
    PROFESSIONAL: 'Professional',
    ENTERPRISE: 'Enterprise',
  };
  return planNames[plan] || plan;
};

export const getPlanColor = (plan: string) => {
  const planColors: Record<string, string> = {
    FREE: 'gray',
    STARTER: 'blue',
    PROFESSIONAL: 'purple',
    ENTERPRISE: 'gold',
  };
  return planColors[plan] || 'gray';
};

export const formatPrice = (priceInCents: number) => {
  return `$${(priceInCents / 100).toFixed(2)}`;
};

export const getSubscriptionStatusColor = (status: string) => {
  const statusColors: Record<string, string> = {
    ACTIVE: 'green',
    INACTIVE: 'gray',
    PAST_DUE: 'orange',
    CANCELLED: 'red',
  };
  return statusColors[status] || 'gray';
};

export const getSubscriptionStatusText = (status: string) => {
  const statusTexts: Record<string, string> = {
    ACTIVE: 'Active',
    INACTIVE: 'Inactive',
    PAST_DUE: 'Past Due',
    CANCELLED: 'Cancelled',
  };
  return statusTexts[status] || status;
};