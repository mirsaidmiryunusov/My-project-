import { Router } from 'express';
import { subscriptionController } from '../controllers/subscriptionController';
import { authenticateToken, requirePermission } from '../middleware/auth';
import { validateRequest } from '../middleware/validation';
import { body, param } from 'express-validator';

const router = Router();

// Get current subscription
router.get(
  '/current',
  authenticateToken,
  subscriptionController.getCurrentSubscription
);

// Get subscription usage
router.get(
  '/usage',
  authenticateToken,
  subscriptionController.getUsage
);

// Get available plans
router.get(
  '/plans',
  subscriptionController.getPlans
);

// Create subscription
router.post(
  '/create',
  authenticateToken,
  requirePermission('subscription:manage'),
  validateRequest([
    body('plan').isIn(['FREE', 'STARTER', 'PROFESSIONAL', 'ENTERPRISE']),
    body('paymentMethodId').optional().isString(),
  ]),
  subscriptionController.createSubscription
);

// Update subscription
router.put(
  '/update',
  authenticateToken,
  requirePermission('subscription:manage'),
  validateRequest([
    body('plan').isIn(['FREE', 'STARTER', 'PROFESSIONAL', 'ENTERPRISE']),
  ]),
  subscriptionController.updateSubscription
);

// Cancel subscription
router.post(
  '/cancel',
  authenticateToken,
  requirePermission('subscription:manage'),
  subscriptionController.cancelSubscription
);

// Create payment intent
router.post(
  '/payment-intent',
  authenticateToken,
  requirePermission('subscription:manage'),
  validateRequest([
    body('plan').isIn(['STARTER', 'PROFESSIONAL', 'ENTERPRISE']),
  ]),
  subscriptionController.createPaymentIntent
);

// Get billing history
router.get(
  '/billing-history',
  authenticateToken,
  subscriptionController.getBillingHistory
);

// Stripe webhook
router.post(
  '/webhook',
  subscriptionController.handleWebhook
);

// Check feature access
router.get(
  '/feature/:feature',
  authenticateToken,
  validateRequest([
    param('feature').isString(),
  ]),
  subscriptionController.checkFeatureAccess
);

// Check usage limit
router.get(
  '/limit/:resource',
  authenticateToken,
  validateRequest([
    param('resource').isIn(['calls', 'campaigns', 'contacts', 'users', 'aiMinutes']),
  ]),
  subscriptionController.checkUsageLimit
);

export default router;