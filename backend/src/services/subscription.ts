import { logger } from '../utils/logger';

export interface SubscriptionFeatures {
  maxCalls: number;
  maxCampaigns: number;
  maxContacts: number;
  maxUsers: number;
  aiMinutes: number;
  advancedAnalytics: boolean;
  customIntegrations: boolean;
  prioritySupport: boolean;
}

export interface SubscriptionPlan {
  id: string;
  name: string;
  price: number;
  interval: string;
  features: SubscriptionFeatures;
}

export class SubscriptionService {
  private plans: SubscriptionPlan[] = [
    {
      id: 'FREE',
      name: 'Free',
      price: 0,
      interval: 'month',
      features: {
        maxCalls: 100,
        maxCampaigns: 1,
        maxContacts: 100,
        maxUsers: 1,
        aiMinutes: 10,
        advancedAnalytics: false,
        customIntegrations: false,
        prioritySupport: false,
      },
    },
    {
      id: 'STARTER',
      name: 'Starter',
      price: 29,
      interval: 'month',
      features: {
        maxCalls: 1000,
        maxCampaigns: 5,
        maxContacts: 1000,
        maxUsers: 3,
        aiMinutes: 100,
        advancedAnalytics: true,
        customIntegrations: false,
        prioritySupport: false,
      },
    },
    {
      id: 'PROFESSIONAL',
      name: 'Professional',
      price: 99,
      interval: 'month',
      features: {
        maxCalls: 10000,
        maxCampaigns: 50,
        maxContacts: 5000,
        maxUsers: 10,
        aiMinutes: 1000,
        advancedAnalytics: true,
        customIntegrations: true,
        prioritySupport: true,
      },
    },
    {
      id: 'ENTERPRISE',
      name: 'Enterprise',
      price: 299,
      interval: 'month',
      features: {
        maxCalls: -1,
        maxCampaigns: -1,
        maxContacts: -1,
        maxUsers: -1,
        aiMinutes: -1,
        advancedAnalytics: true,
        customIntegrations: true,
        prioritySupport: true,
      },
    },
  ];

  async getPlans(): Promise<SubscriptionPlan[]> {
    return this.plans;
  }

  async getPlan(planId: string): Promise<SubscriptionPlan | null> {
    return this.plans.find(plan => plan.id === planId) || null;
  }

  async validateFeatureAccess(userId: string, feature: string): Promise<boolean> {
    try {
      // Mock validation - in real implementation, check user's subscription
      logger.info('Validating feature access', { userId, feature });
      return true;
    } catch (error) {
      logger.error('Failed to validate feature access', { error, userId, feature });
      return false;
    }
  }

  async checkUsageLimit(userId: string, resource: string): Promise<{ withinLimit: boolean; usage: number; limit: number }> {
    try {
      // Mock usage check - in real implementation, check actual usage
      logger.info('Checking usage limit', { userId, resource });
      return {
        withinLimit: true,
        usage: 100,
        limit: 1000,
      };
    } catch (error) {
      logger.error('Failed to check usage limit', { error, userId, resource });
      return {
        withinLimit: false,
        usage: 0,
        limit: 0,
      };
    }
  }
}