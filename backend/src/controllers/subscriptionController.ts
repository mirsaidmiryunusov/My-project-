import { Request, Response } from 'express';
import { logger } from '../utils/logger';

interface AuthenticatedRequest extends Request {
  user?: {
    id: string;
    tenantId?: string;
  };
}

export class SubscriptionController {
  async getCurrentSubscription(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const userId = req.user?.id;

      if (!userId) {
        res.status(400).json({
          success: false,
          message: 'User ID is required',
        });
        return;
      }

      // Mock subscription data for now
      const mockSubscription = {
        id: 'sub_mock_123',
        plan: 'PROFESSIONAL',
        status: 'active',
        currentPeriodStart: new Date(),
        currentPeriodEnd: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000), // 30 days from now
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
      };

      res.json({
        success: true,
        data: {
          subscription: mockSubscription,
          features: mockSubscription.features,
        },
      });
    } catch (error) {
      logger.error('Failed to get current subscription', { error, userId: req.user?.id });
      res.status(500).json({
        success: false,
        message: 'Failed to get current subscription',
      });
    }
  }

  async getUsage(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const userId = req.user?.id;

      if (!userId) {
        res.status(400).json({
          success: false,
          message: 'User ID is required',
        });
        return;
      }

      // Mock usage data
      const mockUsage = {
        calls: { used: 2450, limit: 10000, percentage: 24.5 },
        campaigns: { used: 12, limit: 50, percentage: 24 },
        contacts: { used: 1250, limit: 5000, percentage: 25 },
        users: { used: 3, limit: 10, percentage: 30 },
        aiMinutes: { used: 340, limit: 1000, percentage: 34 },
      };

      res.json({
        success: true,
        data: mockUsage,
      });
    } catch (error) {
      logger.error('Failed to get subscription usage', { error, userId: req.user?.id });
      res.status(500).json({
        success: false,
        message: 'Failed to get subscription usage',
      });
    }
  }

  async getPlans(req: Request, res: Response): Promise<void> {
    try {
      const plans = [
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
            maxCalls: -1, // unlimited
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

      res.json({
        success: true,
        data: plans,
      });
    } catch (error) {
      logger.error('Failed to get subscription plans', { error });
      res.status(500).json({
        success: false,
        message: 'Failed to get subscription plans',
      });
    }
  }

  async createSubscription(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const userId = req.user?.id;
      const { plan, paymentMethodId } = req.body;

      if (!userId) {
        res.status(400).json({
          success: false,
          message: 'User ID is required',
        });
        return;
      }

      // Mock subscription creation
      const mockSubscription = {
        id: `sub_${Date.now()}`,
        plan,
        status: 'active',
        currentPeriodStart: new Date(),
        currentPeriodEnd: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000),
      };

      res.json({
        success: true,
        data: mockSubscription,
        message: 'Subscription created successfully',
      });
    } catch (error) {
      logger.error('Failed to create subscription', { error, userId: req.user?.id });
      res.status(500).json({
        success: false,
        message: 'Failed to create subscription',
      });
    }
  }

  async updateSubscription(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const userId = req.user?.id;
      const { plan } = req.body;

      if (!userId) {
        res.status(400).json({
          success: false,
          message: 'User ID is required',
        });
        return;
      }

      // Mock subscription update
      const mockSubscription = {
        id: 'sub_mock_123',
        plan,
        status: 'active',
        currentPeriodStart: new Date(),
        currentPeriodEnd: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000),
      };

      res.json({
        success: true,
        data: mockSubscription,
        message: 'Subscription updated successfully',
      });
    } catch (error) {
      logger.error('Failed to update subscription', { error, userId: req.user?.id });
      res.status(500).json({
        success: false,
        message: 'Failed to update subscription',
      });
    }
  }

  async cancelSubscription(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const userId = req.user?.id;

      if (!userId) {
        res.status(400).json({
          success: false,
          message: 'User ID is required',
        });
        return;
      }

      res.json({
        success: true,
        message: 'Subscription cancelled successfully',
      });
    } catch (error) {
      logger.error('Failed to cancel subscription', { error, userId: req.user?.id });
      res.status(500).json({
        success: false,
        message: 'Failed to cancel subscription',
      });
    }
  }

  async createPaymentIntent(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const userId = req.user?.id;
      const { amount, currency = 'usd' } = req.body;

      if (!userId) {
        res.status(400).json({
          success: false,
          message: 'User ID is required',
        });
        return;
      }

      // Mock payment intent
      const mockPaymentIntent = {
        id: `pi_${Date.now()}`,
        client_secret: `pi_${Date.now()}_secret_mock`,
        amount,
        currency,
        status: 'requires_payment_method',
      };

      res.json({
        success: true,
        data: mockPaymentIntent,
      });
    } catch (error) {
      logger.error('Failed to create payment intent', { error, userId: req.user?.id });
      res.status(500).json({
        success: false,
        message: 'Failed to create payment intent',
      });
    }
  }

  async getBillingHistory(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const userId = req.user?.id;

      if (!userId) {
        res.status(400).json({
          success: false,
          message: 'User ID is required',
        });
        return;
      }

      // Mock billing history
      const mockHistory = [
        {
          id: 'inv_001',
          date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000),
          amount: 99,
          status: 'paid',
          description: 'Professional Plan - Monthly',
        },
        {
          id: 'inv_002',
          date: new Date(Date.now() - 60 * 24 * 60 * 60 * 1000),
          amount: 99,
          status: 'paid',
          description: 'Professional Plan - Monthly',
        },
      ];

      res.json({
        success: true,
        data: mockHistory,
      });
    } catch (error) {
      logger.error('Failed to get billing history', { error, userId: req.user?.id });
      res.status(500).json({
        success: false,
        message: 'Failed to get billing history',
      });
    }
  }

  async handleWebhook(req: Request, res: Response): Promise<void> {
    try {
      // Mock webhook handling
      res.json({ received: true });
    } catch (error) {
      logger.error('Failed to handle webhook', { error });
      res.status(400).json({
        success: false,
        message: 'Webhook handling failed',
      });
    }
  }

  async checkFeatureAccess(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const userId = req.user?.id;
      const { feature } = req.params;

      if (!userId) {
        res.status(400).json({
          success: false,
          message: 'User ID is required',
        });
        return;
      }

      // Mock feature access check
      const hasAccess = true; // For demo purposes

      res.json({
        success: true,
        data: { hasAccess, feature },
      });
    } catch (error) {
      logger.error('Failed to check feature access', { error, userId: req.user?.id });
      res.status(500).json({
        success: false,
        message: 'Failed to check feature access',
      });
    }
  }

  async checkUsageLimit(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const userId = req.user?.id;
      const { resource } = req.params;

      if (!userId) {
        res.status(400).json({
          success: false,
          message: 'User ID is required',
        });
        return;
      }

      // Mock usage limit check
      const withinLimit = true; // For demo purposes

      res.json({
        success: true,
        data: { withinLimit, resource },
      });
    } catch (error) {
      logger.error('Failed to check usage limit', { error, userId: req.user?.id });
      res.status(500).json({
        success: false,
        message: 'Failed to check usage limit',
      });
    }
  }
}