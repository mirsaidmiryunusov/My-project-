import { PrismaClient, SubscriptionPlan, SubscriptionStatus, PaymentStatus } from '@prisma/client';
import { logger } from '../utils/logger';
import Stripe from 'stripe';

const prisma = new PrismaClient();
const stripe = new Stripe(process.env.STRIPE_SECRET_KEY || 'sk_test_dummy', {
  apiVersion: '2024-06-20',
});

export interface SubscriptionFeatures {
  maxCalls: number;
  maxCampaigns: number;
  maxContacts: number;
  maxUsers: number;
  aiMinutes: number;
  analyticsRetention: number; // days
  prioritySupport: boolean;
  customIntegrations: boolean;
  whiteLabel: boolean;
  apiAccess: boolean;
  webhooks: boolean;
  ssoEnabled: boolean;
  multiTenant: boolean;
  advancedAnalytics: boolean;
  customReports: boolean;
  bulkOperations: boolean;
  realTimeSync: boolean;
  dataExport: boolean;
  customFields: boolean;
  automatedWorkflows: boolean;
}

export const SUBSCRIPTION_PLANS: Record<SubscriptionPlan, {
  name: string;
  price: number; // in cents
  interval: 'month' | 'year';
  features: SubscriptionFeatures;
  stripeProductId?: string;
  stripePriceId?: string;
}> = {
  FREE: {
    name: 'Free',
    price: 0,
    interval: 'month',
    features: {
      maxCalls: 100,
      maxCampaigns: 3,
      maxContacts: 1000,
      maxUsers: 1,
      aiMinutes: 60,
      analyticsRetention: 30,
      prioritySupport: false,
      customIntegrations: false,
      whiteLabel: false,
      apiAccess: false,
      webhooks: false,
      ssoEnabled: false,
      multiTenant: false,
      advancedAnalytics: false,
      customReports: false,
      bulkOperations: false,
      realTimeSync: false,
      dataExport: false,
      customFields: false,
      automatedWorkflows: false,
    },
  },
  STARTER: {
    name: 'Starter',
    price: 2900, // $29/month
    interval: 'month',
    features: {
      maxCalls: 1000,
      maxCampaigns: 10,
      maxContacts: 5000,
      maxUsers: 3,
      aiMinutes: 300,
      analyticsRetention: 90,
      prioritySupport: false,
      customIntegrations: false,
      whiteLabel: false,
      apiAccess: true,
      webhooks: true,
      ssoEnabled: false,
      multiTenant: false,
      advancedAnalytics: false,
      customReports: false,
      bulkOperations: true,
      realTimeSync: true,
      dataExport: true,
      customFields: true,
      automatedWorkflows: false,
    },
  },
  PROFESSIONAL: {
    name: 'Professional',
    price: 9900, // $99/month
    interval: 'month',
    features: {
      maxCalls: 5000,
      maxCampaigns: 50,
      maxContacts: 25000,
      maxUsers: 10,
      aiMinutes: 1500,
      analyticsRetention: 180,
      prioritySupport: true,
      customIntegrations: true,
      whiteLabel: false,
      apiAccess: true,
      webhooks: true,
      ssoEnabled: true,
      multiTenant: false,
      advancedAnalytics: true,
      customReports: true,
      bulkOperations: true,
      realTimeSync: true,
      dataExport: true,
      customFields: true,
      automatedWorkflows: true,
    },
  },
  ENTERPRISE: {
    name: 'Enterprise',
    price: 29900, // $299/month
    interval: 'month',
    features: {
      maxCalls: -1, // unlimited
      maxCampaigns: -1, // unlimited
      maxContacts: -1, // unlimited
      maxUsers: -1, // unlimited
      aiMinutes: -1, // unlimited
      analyticsRetention: 365,
      prioritySupport: true,
      customIntegrations: true,
      whiteLabel: true,
      apiAccess: true,
      webhooks: true,
      ssoEnabled: true,
      multiTenant: true,
      advancedAnalytics: true,
      customReports: true,
      bulkOperations: true,
      realTimeSync: true,
      dataExport: true,
      customFields: true,
      automatedWorkflows: true,
    },
  },
};

export class SubscriptionService {
  async createSubscription(tenantId: string, plan: SubscriptionPlan, paymentMethodId?: string) {
    try {
      const tenant = await prisma.tenant.findUnique({
        where: { id: tenantId },
        include: { subscription: true },
      });

      if (!tenant) {
        throw new Error('Tenant not found');
      }

      // Cancel existing subscription if any
      if (tenant.subscription) {
        await this.cancelSubscription(tenant.subscription.id);
      }

      const planConfig = SUBSCRIPTION_PLANS[plan];
      let stripeSubscriptionId: string | null = null;

      // Create Stripe subscription for paid plans
      if (plan !== 'FREE' && paymentMethodId) {
        const stripeCustomer = await this.getOrCreateStripeCustomer(tenant);
        
        const subscription = await stripe.subscriptions.create({
          customer: stripeCustomer.id,
          items: [{ price: planConfig.stripePriceId }],
          default_payment_method: paymentMethodId,
          expand: ['latest_invoice.payment_intent'],
        });

        stripeSubscriptionId = subscription.id;
      }

      // Create subscription record
      const subscription = await prisma.subscription.create({
        data: {
          tenantId,
          plan,
          status: plan === 'FREE' ? 'ACTIVE' : 'PENDING',
          currentPeriodStart: new Date(),
          currentPeriodEnd: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000), // 30 days
          stripeSubscriptionId,
          features: JSON.stringify(planConfig.features),
        },
      });

      // Update tenant subscription
      await prisma.tenant.update({
        where: { id: tenantId },
        data: { subscriptionId: subscription.id },
      });

      logger.info('Subscription created', { tenantId, plan, subscriptionId: subscription.id });
      return subscription;
    } catch (error) {
      logger.error('Failed to create subscription', { error, tenantId, plan });
      throw error;
    }
  }

  async updateSubscription(subscriptionId: string, plan: SubscriptionPlan) {
    try {
      const subscription = await prisma.subscription.findUnique({
        where: { id: subscriptionId },
        include: { tenant: true },
      });

      if (!subscription) {
        throw new Error('Subscription not found');
      }

      const planConfig = SUBSCRIPTION_PLANS[plan];

      // Update Stripe subscription if exists
      if (subscription.stripeSubscriptionId) {
        await stripe.subscriptions.update(subscription.stripeSubscriptionId, {
          items: [{ 
            id: subscription.stripeSubscriptionId,
            price: planConfig.stripePriceId 
          }],
        });
      }

      // Update subscription record
      const updatedSubscription = await prisma.subscription.update({
        where: { id: subscriptionId },
        data: {
          plan,
          features: JSON.stringify(planConfig.features),
          updatedAt: new Date(),
        },
      });

      logger.info('Subscription updated', { subscriptionId, plan });
      return updatedSubscription;
    } catch (error) {
      logger.error('Failed to update subscription', { error, subscriptionId, plan });
      throw error;
    }
  }

  async cancelSubscription(subscriptionId: string) {
    try {
      const subscription = await prisma.subscription.findUnique({
        where: { id: subscriptionId },
      });

      if (!subscription) {
        throw new Error('Subscription not found');
      }

      // Cancel Stripe subscription if exists
      if (subscription.stripeSubscriptionId) {
        await stripe.subscriptions.cancel(subscription.stripeSubscriptionId);
      }

      // Update subscription status
      await prisma.subscription.update({
        where: { id: subscriptionId },
        data: {
          status: 'CANCELLED',
          cancelledAt: new Date(),
        },
      });

      logger.info('Subscription cancelled', { subscriptionId });
    } catch (error) {
      logger.error('Failed to cancel subscription', { error, subscriptionId });
      throw error;
    }
  }

  async getSubscriptionUsage(tenantId: string) {
    try {
      const tenant = await prisma.tenant.findUnique({
        where: { id: tenantId },
        include: { 
          subscription: true,
          _count: {
            select: {
              users: true,
              campaigns: true,
              customers: true,
            },
          },
        },
      });

      if (!tenant || !tenant.subscription) {
        throw new Error('Subscription not found');
      }

      const features = JSON.parse(tenant.subscription.features) as SubscriptionFeatures;
      
      // Get current period usage
      const currentPeriodStart = tenant.subscription.currentPeriodStart;
      const currentPeriodEnd = tenant.subscription.currentPeriodEnd;

      const [callsCount, aiMinutesUsed] = await Promise.all([
        prisma.call.count({
          where: {
            tenantId,
            createdAt: {
              gte: currentPeriodStart,
              lte: currentPeriodEnd,
            },
          },
        }),
        prisma.call.aggregate({
          where: {
            tenantId,
            createdAt: {
              gte: currentPeriodStart,
              lte: currentPeriodEnd,
            },
          },
          _sum: {
            duration: true,
          },
        }),
      ]);

      const usage = {
        calls: {
          used: callsCount,
          limit: features.maxCalls,
          percentage: features.maxCalls > 0 ? (callsCount / features.maxCalls) * 100 : 0,
        },
        campaigns: {
          used: tenant._count.campaigns,
          limit: features.maxCampaigns,
          percentage: features.maxCampaigns > 0 ? (tenant._count.campaigns / features.maxCampaigns) * 100 : 0,
        },
        contacts: {
          used: tenant._count.customers,
          limit: features.maxContacts,
          percentage: features.maxContacts > 0 ? (tenant._count.customers / features.maxContacts) * 100 : 0,
        },
        users: {
          used: tenant._count.users,
          limit: features.maxUsers,
          percentage: features.maxUsers > 0 ? (tenant._count.users / features.maxUsers) * 100 : 0,
        },
        aiMinutes: {
          used: Math.ceil((aiMinutesUsed._sum.duration || 0) / 60),
          limit: features.aiMinutes,
          percentage: features.aiMinutes > 0 ? (Math.ceil((aiMinutesUsed._sum.duration || 0) / 60) / features.aiMinutes) * 100 : 0,
        },
      };

      return {
        subscription: tenant.subscription,
        features,
        usage,
        periodStart: currentPeriodStart,
        periodEnd: currentPeriodEnd,
      };
    } catch (error) {
      logger.error('Failed to get subscription usage', { error, tenantId });
      throw error;
    }
  }

  async checkFeatureAccess(tenantId: string, feature: keyof SubscriptionFeatures): Promise<boolean> {
    try {
      const tenant = await prisma.tenant.findUnique({
        where: { id: tenantId },
        include: { subscription: true },
      });

      if (!tenant || !tenant.subscription) {
        return false;
      }

      const features = JSON.parse(tenant.subscription.features) as SubscriptionFeatures;
      return features[feature] === true;
    } catch (error) {
      logger.error('Failed to check feature access', { error, tenantId, feature });
      return false;
    }
  }

  async checkUsageLimit(tenantId: string, resource: 'calls' | 'campaigns' | 'contacts' | 'users' | 'aiMinutes'): Promise<boolean> {
    try {
      const usageData = await this.getSubscriptionUsage(tenantId);
      const usage = usageData.usage[resource];
      
      // Unlimited resources (-1) always return true
      if (usage.limit === -1) {
        return true;
      }

      return usage.used < usage.limit;
    } catch (error) {
      logger.error('Failed to check usage limit', { error, tenantId, resource });
      return false;
    }
  }

  async processWebhook(event: Stripe.Event) {
    try {
      switch (event.type) {
        case 'invoice.payment_succeeded':
          await this.handlePaymentSucceeded(event.data.object as Stripe.Invoice);
          break;
        case 'invoice.payment_failed':
          await this.handlePaymentFailed(event.data.object as Stripe.Invoice);
          break;
        case 'customer.subscription.updated':
          await this.handleSubscriptionUpdated(event.data.object as Stripe.Subscription);
          break;
        case 'customer.subscription.deleted':
          await this.handleSubscriptionDeleted(event.data.object as Stripe.Subscription);
          break;
        default:
          logger.info('Unhandled webhook event', { type: event.type });
      }
    } catch (error) {
      logger.error('Failed to process webhook', { error, eventType: event.type });
      throw error;
    }
  }

  private async getOrCreateStripeCustomer(tenant: any) {
    if (tenant.stripeCustomerId) {
      return await stripe.customers.retrieve(tenant.stripeCustomerId);
    }

    const customer = await stripe.customers.create({
      email: tenant.email,
      name: tenant.name,
      metadata: {
        tenantId: tenant.id,
      },
    });

    await prisma.tenant.update({
      where: { id: tenant.id },
      data: { stripeCustomerId: customer.id },
    });

    return customer;
  }

  private async handlePaymentSucceeded(invoice: Stripe.Invoice) {
    const subscription = await prisma.subscription.findFirst({
      where: { stripeSubscriptionId: invoice.subscription as string },
    });

    if (subscription) {
      await prisma.subscription.update({
        where: { id: subscription.id },
        data: { status: 'ACTIVE' },
      });

      // Create payment record
      await prisma.payment.create({
        data: {
          tenantId: subscription.tenantId,
          subscriptionId: subscription.id,
          amount: invoice.amount_paid,
          currency: invoice.currency,
          status: 'COMPLETED',
          stripePaymentIntentId: invoice.payment_intent as string,
          metadata: JSON.stringify({
            invoiceId: invoice.id,
            periodStart: new Date(invoice.period_start * 1000),
            periodEnd: new Date(invoice.period_end * 1000),
          }),
        },
      });
    }
  }

  private async handlePaymentFailed(invoice: Stripe.Invoice) {
    const subscription = await prisma.subscription.findFirst({
      where: { stripeSubscriptionId: invoice.subscription as string },
    });

    if (subscription) {
      await prisma.subscription.update({
        where: { id: subscription.id },
        data: { status: 'PAST_DUE' },
      });

      // Create failed payment record
      await prisma.payment.create({
        data: {
          tenantId: subscription.tenantId,
          subscriptionId: subscription.id,
          amount: invoice.amount_due,
          currency: invoice.currency,
          status: 'FAILED',
          stripePaymentIntentId: invoice.payment_intent as string,
          metadata: JSON.stringify({
            invoiceId: invoice.id,
            failureReason: 'Payment failed',
          }),
        },
      });
    }
  }

  private async handleSubscriptionUpdated(stripeSubscription: Stripe.Subscription) {
    const subscription = await prisma.subscription.findFirst({
      where: { stripeSubscriptionId: stripeSubscription.id },
    });

    if (subscription) {
      await prisma.subscription.update({
        where: { id: subscription.id },
        data: {
          status: stripeSubscription.status === 'active' ? 'ACTIVE' : 'INACTIVE',
          currentPeriodStart: new Date(stripeSubscription.current_period_start * 1000),
          currentPeriodEnd: new Date(stripeSubscription.current_period_end * 1000),
        },
      });
    }
  }

  private async handleSubscriptionDeleted(stripeSubscription: Stripe.Subscription) {
    const subscription = await prisma.subscription.findFirst({
      where: { stripeSubscriptionId: stripeSubscription.id },
    });

    if (subscription) {
      await prisma.subscription.update({
        where: { id: subscription.id },
        data: {
          status: 'CANCELLED',
          cancelledAt: new Date(),
        },
      });
    }
  }
}

export const subscriptionService = new SubscriptionService();