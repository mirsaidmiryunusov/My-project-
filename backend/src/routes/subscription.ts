import express from 'express';
import { SubscriptionController } from '../controllers/subscriptionController';

const router = express.Router();
const subscriptionController = new SubscriptionController();

// Get current subscription
router.get('/current', subscriptionController.getCurrentSubscription.bind(subscriptionController));

// Get subscription usage
router.get('/usage', subscriptionController.getUsage.bind(subscriptionController));

// Get available plans
router.get('/plans', subscriptionController.getPlans.bind(subscriptionController));

// Create subscription
router.post('/create', subscriptionController.createSubscription.bind(subscriptionController));

// Update subscription
router.put('/update', subscriptionController.updateSubscription.bind(subscriptionController));

// Cancel subscription
router.delete('/cancel', subscriptionController.cancelSubscription.bind(subscriptionController));

// Create payment intent
router.post('/payment-intent', subscriptionController.createPaymentIntent.bind(subscriptionController));

// Get billing history
router.get('/billing-history', subscriptionController.getBillingHistory.bind(subscriptionController));

// Webhook endpoint
router.post('/webhook', subscriptionController.handleWebhook.bind(subscriptionController));

// Check feature access
router.get('/feature/:feature', subscriptionController.checkFeatureAccess.bind(subscriptionController));

// Check usage limit
router.get('/usage-limit/:resource', subscriptionController.checkUsageLimit.bind(subscriptionController));

export default router;