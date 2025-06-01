import { Request, Response } from 'express';
import { subscriptionService, SUBSCRIPTION_PLANS } from '../services/subscription';
import { logger } from '../utils/logger';
import { PrismaClient } from '@prisma/client';
import Stripe from 'stripe';

const prisma = new PrismaClient();
const stripe = new Stripe(process.env.STRIPE_SECRET_KEY || 'sk_test_dummy', {
  apiVersion: '2024-06-20',
});

export class SubscriptionController {
  async getCurrentSubscription(req: Request, res: Response) {
    try {
      const tenantId = req.user?.tenantId;
      if (!tenantId) {
        return res.status(400).json({
          success: false,
          message: 'Tenant ID required',
        });
      }

      const tenant = await prisma.tenant.findUnique({
        where: { id: tenantId },
        include: {
          subscription: true,
        },
      });

      if (!tenant) {
        return res.status(404).json({
          success: false,
          message: 'Tenant not found',
        });
      }

      res.json({
        success: true,
        data: {
          subscription: tenant.subscription,
          features: tenant.subscription ? JSON.parse(tenant.subscription.features) : null,
        },
      });
    } catch (error) {
      logger.error('Failed to get current subscription', { error, userId: req.user?.id });
      res.status(500).json({
        success: false,
        message: 'Failed to get subscription',
      });
    }
  }

  async getUsage(req: Request, res: Response) {
    try {
      const tenantId = req.user?.tenantId;
      if (!tenantId) {
        return res.status(400).json({
          success: false,
          message: 'Tenant ID required',
        });
      }

      const usageData = await subscriptionService.getSubscriptionUsage(tenantId);

      res.json({
        success: true,
        data: usageData,
      });
    } catch (error) {
      logger.error('Failed to get subscription usage', { error, userId: req.user?.id });
      res.status(500).json({
        success: false,
        message: 'Failed to get usage data',
      });
    }
  }

  async getPlans(req: Request, res: Response) {
    try {
      const plans = Object.entries(SUBSCRIPTION_PLANS).map(([key, plan]) => ({
        id: key,
        ...plan,
      }));

      res.json({
        success: true,
        data: plans,
      });
    } catch (error) {
      logger.error('Failed to get subscription plans', { error });
      res.status(500).json({
        success: false,
        message: 'Failed to get plans',
      });
    }
  }

  async createSubscription(req: Request, res: Response) {
    try {
      const tenantId = req.user?.tenantId;
      const { plan, paymentMethodId } = req.body;

      if (!tenantId) {
        return res.status(400).json({
          success: false,
          message: 'Tenant ID required',
        });
      }

      const subscription = await subscriptionService.createSubscription(
        tenantId,
        plan,
        paymentMethodId
      );

      res.json({
        success: true,
        data: subscription,
        message: 'Subscription created successfully',
      });
    } catch (error) {
      logger.error('Failed to create subscription', { error, userId: req.user?.id });
      res.status(500).json({
        success: false,
        message: error instanceof Error ? error.message : 'Failed to create subscription',
      });
    }
  }

  async updateSubscription(req: Request, res: Response) {
    try {
      const tenantId = req.user?.tenantId;
      const { plan } = req.body;

      if (!tenantId) {
        return res.status(400).json({
          success: false,
          message: 'Tenant ID required',
        });
      }

      const tenant = await prisma.tenant.findUnique({
        where: { id: tenantId },
        include: { subscription: true },
      });

      if (!tenant?.subscription) {
        return res.status(404).json({
          success: false,
          message: 'Subscription not found',
        });
      }

      const subscription = await subscriptionService.updateSubscription(
        tenant.subscription.id,
        plan
      );

      res.json({
        success: true,
        data: subscription,
        message: 'Subscription updated successfully',
      });
    } catch (error) {
      logger.error('Failed to update subscription', { error, userId: req.user?.id });
      res.status(500).json({
        success: false,
        message: error instanceof Error ? error.message : 'Failed to update subscription',
      });
    }
  }

  async cancelSubscription(req: Request, res: Response) {
    try {
      const tenantId = req.user?.tenantId;

      if (!tenantId) {
        return res.status(400).json({
          success: false,
          message: 'Tenant ID required',
        });
      }

      const tenant = await prisma.tenant.findUnique({
        where: { id: tenantId },
        include: { subscription: true },
      });

      if (!tenant?.subscription) {
        return res.status(404).json({
          success: false,
          message: 'Subscription not found',
        });
      }

      await subscriptionService.cancelSubscription(tenant.subscription.id);

      res.json({
        success: true,
        message: 'Subscription cancelled successfully',
      });
    } catch (error) {
      logger.error('Failed to cancel subscription', { error, userId: req.user?.id });
      res.status(500).json({
        success: false,
        message: error instanceof Error ? error.message : 'Failed to cancel subscription',
      });
    }
  }

  async createPaymentIntent(req: Request, res: Response) {
    try {
      const tenantId = req.user?.tenantId;
      const { plan } = req.body;

      if (!tenantId) {
        return res.status(400).json({
          success: false,
          message: 'Tenant ID required',
        });
      }

      const tenant = await prisma.tenant.findUnique({
        where: { id: tenantId },
      });

      if (!tenant) {
        return res.status(404).json({
          success: false,
          message: 'Tenant not found',
        });
      }

      const planConfig = SUBSCRIPTION_PLANS[plan as keyof typeof SUBSCRIPTION_PLANS];
      if (!planConfig) {
        return res.status(400).json({
          success: false,
          message: 'Invalid plan',
        });
      }

      // Get or create Stripe customer
      let stripeCustomerId = tenant.stripeCustomerId;
      if (!stripeCustomerId) {
        const customer = await stripe.customers.create({
          email: tenant.email,
          name: tenant.name,
          metadata: {
            tenantId: tenant.id,
          },
        });
        stripeCustomerId = customer.id;

        await prisma.tenant.update({
          where: { id: tenantId },
          data: { stripeCustomerId },
        });
      }

      // Create payment intent
      const paymentIntent = await stripe.paymentIntents.create({
        amount: planConfig.price,
        currency: 'usd',
        customer: stripeCustomerId,
        metadata: {
          tenantId,
          plan,
        },
      });

      res.json({
        success: true,
        data: {
          clientSecret: paymentIntent.client_secret,
          amount: planConfig.price,
          currency: 'usd',
        },
      });
    } catch (error) {
      logger.error('Failed to create payment intent', { error, userId: req.user?.id });
      res.status(500).json({
        success: false,
        message: 'Failed to create payment intent',
      });
    }
  }

  async getBillingHistory(req: Request, res: Response) {
    try {
      const tenantId = req.user?.tenantId;

      if (!tenantId) {
        return res.status(400).json({
          success: false,
          message: 'Tenant ID required',
        });
      }

      const payments = await prisma.payment.findMany({
        where: { tenantId },
        orderBy: { createdAt: 'desc' },
        take: 50,
        include: {
          subscription: true,
        },
      });

      res.json({
        success: true,
        data: payments,
      });
    } catch (error) {
      logger.error('Failed to get billing history', { error, userId: req.user?.id });
      res.status(500).json({
        success: false,
        message: 'Failed to get billing history',
      });
    }
  }

  async handleWebhook(req: Request, res: Response) {
    try {
      const sig = req.headers['stripe-signature'] as string;
      const endpointSecret = process.env.STRIPE_WEBHOOK_SECRET;

      if (!endpointSecret) {
        return res.status(400).json({
          success: false,
          message: 'Webhook secret not configured',
        });
      }

      let event: Stripe.Event;

      try {
        event = stripe.webhooks.constructEvent(req.body, sig, endpointSecret);
      } catch (err) {
        logger.error('Webhook signature verification failed', { error: err });
        return res.status(400).json({
          success: false,
          message: 'Webhook signature verification failed',
        });
      }

      await subscriptionService.processWebhook(event);

      res.json({
        success: true,
        message: 'Webhook processed successfully',
      });
    } catch (error) {
      logger.error('Failed to process webhook', { error });
      res.status(500).json({
        success: false,
        message: 'Failed to process webhook',
      });
    }
  }

  async checkFeatureAccess(req: Request, res: Response) {
    try {
      const tenantId = req.user?.tenantId;
      const { feature } = req.params;

      if (!tenantId) {
        return res.status(400).json({
          success: false,
          message: 'Tenant ID required',
        });
      }

      const hasAccess = await subscriptionService.checkFeatureAccess(tenantId, feature as any);

      res.json({
        success: true,
        data: {
          feature,
          hasAccess,
        },
      });
    } catch (error) {
      logger.error('Failed to check feature access', { error, userId: req.user?.id });
      res.status(500).json({
        success: false,
        message: 'Failed to check feature access',
      });
    }
  }

  async checkUsageLimit(req: Request, res: Response) {
    try {
      const tenantId = req.user?.tenantId;
      const { resource } = req.params;

      if (!tenantId) {
        return res.status(400).json({
          success: false,
          message: 'Tenant ID required',
        });
      }

      const withinLimit = await subscriptionService.checkUsageLimit(tenantId, resource as any);

      res.json({
        success: true,
        data: {
          resource,
          withinLimit,
        },
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

export const subscriptionController = new SubscriptionController();