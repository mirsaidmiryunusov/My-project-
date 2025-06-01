/**
 * Dashboard Routes
 * 
 * Provides real-time dashboard data including analytics, metrics,
 * call statistics, and system monitoring for the GeminiVoiceConnect platform.
 */

import express from 'express';
import { DashboardController } from '../controllers/dashboardController';
import { validateRequest } from '../middleware/validation';
import { query } from 'express-validator';

const router = express.Router();
const dashboardController = new DashboardController();

/**
 * @route   GET /api/dashboard/overview
 * @desc    Get dashboard overview with key metrics
 * @access  Private
 */
router.get('/overview', dashboardController.getOverview.bind(dashboardController));

/**
 * @route   GET /api/dashboard/analytics
 * @desc    Get analytics data for dashboard
 * @access  Private
 */
router.get(
  '/analytics',
  [
    query('period')
      .optional()
      .isIn(['1h', '24h', '7d', '30d', '90d'])
      .withMessage('Invalid period specified'),
    query('metrics')
      .optional()
      .isString()
      .withMessage('Metrics must be a comma-separated string'),
  ],
  validateRequest,
  dashboardController.getAnalytics.bind(dashboardController)
);

/**
 * @route   GET /api/dashboard/calls/live
 * @desc    Get live call data
 * @access  Private
 */
router.get('/calls/live', dashboardController.getLiveCalls.bind(dashboardController));

/**
 * @route   GET /api/dashboard/calls/stats
 * @desc    Get call statistics
 * @access  Private
 */
router.get(
  '/calls/stats',
  [
    query('period')
      .optional()
      .isIn(['1h', '24h', '7d', '30d'])
      .withMessage('Invalid period specified'),
  ],
  validateRequest,
  dashboardController.getCallStats.bind(dashboardController)
);

/**
 * @route   GET /api/dashboard/performance
 * @desc    Get system performance metrics
 * @access  Private
 */
router.get('/performance', dashboardController.getPerformanceMetrics.bind(dashboardController));

/**
 * @route   GET /api/dashboard/predictions
 * @desc    Get AI predictions and forecasts
 * @access  Private
 */
router.get(
  '/predictions',
  [
    query('type')
      .optional()
      .isIn(['revenue', 'churn', 'outcomes', 'sentiment'])
      .withMessage('Invalid prediction type'),
    query('horizon')
      .optional()
      .isIn(['1d', '7d', '30d', '90d'])
      .withMessage('Invalid prediction horizon'),
  ],
  validateRequest,
  dashboardController.getPredictions.bind(dashboardController)
);

/**
 * @route   GET /api/dashboard/revenue
 * @desc    Get revenue analytics and forecasts
 * @access  Private
 */
router.get(
  '/revenue',
  [
    query('period')
      .optional()
      .isIn(['7d', '30d', '90d', '1y'])
      .withMessage('Invalid period specified'),
  ],
  validateRequest,
  dashboardController.getRevenueAnalytics.bind(dashboardController)
);

/**
 * @route   GET /api/dashboard/churn
 * @desc    Get customer churn predictions
 * @access  Private
 */
router.get('/churn', dashboardController.getChurnPredictions.bind(dashboardController));

/**
 * @route   GET /api/dashboard/sentiment
 * @desc    Get sentiment analysis data
 * @access  Private
 */
router.get(
  '/sentiment',
  [
    query('period')
      .optional()
      .isIn(['1h', '24h', '7d', '30d'])
      .withMessage('Invalid period specified'),
  ],
  validateRequest,
  dashboardController.getSentimentAnalysis.bind(dashboardController)
);

/**
 * @route   GET /api/dashboard/agents
 * @desc    Get agent performance data
 * @access  Private
 */
router.get('/agents', dashboardController.getAgentPerformance.bind(dashboardController));

/**
 * @route   GET /api/dashboard/campaigns
 * @desc    Get campaign performance data
 * @access  Private
 */
router.get('/campaigns', dashboardController.getCampaignPerformance.bind(dashboardController));

/**
 * @route   GET /api/dashboard/real-time
 * @desc    Get real-time dashboard data
 * @access  Private
 */
router.get('/real-time', dashboardController.getRealTimeData.bind(dashboardController));

/**
 * @route   GET /api/dashboard/alerts
 * @desc    Get system alerts and notifications
 * @access  Private
 */
router.get('/alerts', dashboardController.getAlerts.bind(dashboardController));

/**
 * @route   GET /api/dashboard/export
 * @desc    Export dashboard data
 * @access  Private
 */
router.get(
  '/export',
  [
    query('format')
      .optional()
      .isIn(['csv', 'xlsx', 'pdf'])
      .withMessage('Invalid export format'),
    query('data')
      .optional()
      .isString()
      .withMessage('Data types must be a comma-separated string'),
  ],
  validateRequest,
  dashboardController.exportData.bind(dashboardController)
);

export default router;