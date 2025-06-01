/**
 * Analytics Routes
 * 
 * Analytics and reporting routes for the GeminiVoiceConnect platform.
 */

import express from 'express';
import { query } from 'express-validator';
import { AnalyticsController } from '../controllers/analyticsController';
import { validateRequest } from '../middleware/validation';
import { requirePermission } from '../middleware/auth';

const router = express.Router();
const analyticsController = new AnalyticsController();

/**
 * @route   GET /api/analytics/overview
 * @desc    Get analytics overview
 * @access  Private (analytics:read permission)
 */
router.get(
  '/overview',
  requirePermission('analytics:read'),
  [
    query('period').optional().isIn(['1h', '24h', '7d', '30d', '90d']).withMessage('Invalid period'),
  ],
  validateRequest,
  analyticsController.getOverview.bind(analyticsController)
);

/**
 * @route   GET /api/analytics/calls
 * @desc    Get call analytics
 * @access  Private (analytics:read permission)
 */
router.get(
  '/calls',
  requirePermission('analytics:read'),
  [
    query('period').optional().isIn(['1h', '24h', '7d', '30d', '90d']).withMessage('Invalid period'),
    query('groupBy').optional().isIn(['hour', 'day', 'week', 'month']).withMessage('Invalid groupBy'),
    query('metrics').optional().isString().withMessage('Metrics must be a string'),
  ],
  validateRequest,
  analyticsController.getCallAnalytics.bind(analyticsController)
);

/**
 * @route   GET /api/analytics/revenue
 * @desc    Get revenue analytics
 * @access  Private (analytics:read permission)
 */
router.get(
  '/revenue',
  requirePermission('analytics:read'),
  [
    query('period').optional().isIn(['7d', '30d', '90d', '1y']).withMessage('Invalid period'),
    query('breakdown').optional().isIn(['daily', 'weekly', 'monthly']).withMessage('Invalid breakdown'),
  ],
  validateRequest,
  analyticsController.getRevenueAnalytics.bind(analyticsController)
);

/**
 * @route   GET /api/analytics/performance
 * @desc    Get performance analytics
 * @access  Private (analytics:read permission)
 */
router.get(
  '/performance',
  requirePermission('analytics:read'),
  [
    query('period').optional().isIn(['7d', '30d', '90d']).withMessage('Invalid period'),
    query('type').optional().isIn(['agents', 'campaigns', 'overall']).withMessage('Invalid type'),
  ],
  validateRequest,
  analyticsController.getPerformanceAnalytics.bind(analyticsController)
);

/**
 * @route   GET /api/analytics/sentiment
 * @desc    Get sentiment analytics
 * @access  Private (analytics:read permission)
 */
router.get(
  '/sentiment',
  requirePermission('analytics:read'),
  [
    query('period').optional().isIn(['1h', '24h', '7d', '30d']).withMessage('Invalid period'),
    query('breakdown').optional().isIn(['hourly', 'daily']).withMessage('Invalid breakdown'),
  ],
  validateRequest,
  analyticsController.getSentimentAnalytics.bind(analyticsController)
);

/**
 * @route   GET /api/analytics/trends
 * @desc    Get trend analytics
 * @access  Private (analytics:read permission)
 */
router.get(
  '/trends',
  requirePermission('analytics:read'),
  [
    query('metric').isIn(['calls', 'revenue', 'success_rate', 'sentiment']).withMessage('Invalid metric'),
    query('period').optional().isIn(['7d', '30d', '90d']).withMessage('Invalid period'),
    query('comparison').optional().isIn(['previous_period', 'previous_year']).withMessage('Invalid comparison'),
  ],
  validateRequest,
  analyticsController.getTrendAnalytics.bind(analyticsController)
);

/**
 * @route   GET /api/analytics/agents
 * @desc    Get agent analytics
 * @access  Private (analytics:read permission)
 */
router.get(
  '/agents',
  requirePermission('analytics:read'),
  [
    query('period').optional().isIn(['7d', '30d', '90d']).withMessage('Invalid period'),
    query('sortBy').optional().isIn(['calls', 'success_rate', 'revenue', 'duration']).withMessage('Invalid sortBy'),
    query('order').optional().isIn(['asc', 'desc']).withMessage('Invalid order'),
  ],
  validateRequest,
  analyticsController.getAgentAnalytics.bind(analyticsController)
);

/**
 * @route   GET /api/analytics/campaigns
 * @desc    Get campaign analytics
 * @access  Private (analytics:read permission)
 */
router.get(
  '/campaigns',
  requirePermission('analytics:read'),
  [
    query('period').optional().isIn(['7d', '30d', '90d']).withMessage('Invalid period'),
    query('status').optional().isIn(['ACTIVE', 'COMPLETED', 'PAUSED']).withMessage('Invalid status'),
  ],
  validateRequest,
  analyticsController.getCampaignAnalytics.bind(analyticsController)
);

/**
 * @route   GET /api/analytics/customers
 * @desc    Get customer analytics
 * @access  Private (analytics:read permission)
 */
router.get(
  '/customers',
  requirePermission('analytics:read'),
  [
    query('period').optional().isIn(['7d', '30d', '90d']).withMessage('Invalid period'),
    query('segment').optional().isString().withMessage('Segment must be a string'),
  ],
  validateRequest,
  analyticsController.getCustomerAnalytics.bind(analyticsController)
);

/**
 * @route   GET /api/analytics/forecasts
 * @desc    Get forecast analytics
 * @access  Private (analytics:read permission)
 */
router.get(
  '/forecasts',
  requirePermission('analytics:read'),
  [
    query('metric').isIn(['calls', 'revenue', 'churn']).withMessage('Invalid metric'),
    query('horizon').optional().isIn(['7d', '30d', '90d']).withMessage('Invalid horizon'),
    query('confidence').optional().isFloat({ min: 0.5, max: 0.99 }).withMessage('Confidence must be between 0.5 and 0.99'),
  ],
  validateRequest,
  analyticsController.getForecastAnalytics.bind(analyticsController)
);

/**
 * @route   GET /api/analytics/reports
 * @desc    Get available reports
 * @access  Private (analytics:read permission)
 */
router.get(
  '/reports',
  requirePermission('analytics:read'),
  analyticsController.getAvailableReports.bind(analyticsController)
);

/**
 * @route   POST /api/analytics/reports
 * @desc    Generate custom report
 * @access  Private (analytics:read permission)
 */
router.post(
  '/reports',
  requirePermission('analytics:read'),
  analyticsController.generateCustomReport.bind(analyticsController)
);

/**
 * @route   GET /api/analytics/export
 * @desc    Export analytics data
 * @access  Private (analytics:read permission)
 */
router.get(
  '/export',
  requirePermission('analytics:read'),
  [
    query('type').isIn(['calls', 'revenue', 'performance', 'sentiment']).withMessage('Invalid type'),
    query('format').optional().isIn(['csv', 'xlsx', 'pdf']).withMessage('Invalid format'),
    query('period').optional().isIn(['7d', '30d', '90d']).withMessage('Invalid period'),
  ],
  validateRequest,
  analyticsController.exportAnalytics.bind(analyticsController)
);

/**
 * @route   GET /api/analytics/real-time
 * @desc    Get real-time analytics
 * @access  Private (analytics:read permission)
 */
router.get(
  '/real-time',
  requirePermission('analytics:read'),
  analyticsController.getRealTimeAnalytics.bind(analyticsController)
);

export default router;