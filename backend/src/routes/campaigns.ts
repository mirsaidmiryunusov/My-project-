/**
 * Campaign Routes
 * 
 * Campaign management routes for the GeminiVoiceConnect platform.
 */

import express from 'express';
import { body, param, query } from 'express-validator';
import { CampaignController } from '../controllers/campaignController';
import { validateRequest } from '../middleware/validation';
import { requirePermission } from '../middleware/auth';

const router = express.Router();
const campaignController = new CampaignController();

/**
 * @route   GET /api/campaigns
 * @desc    Get all campaigns with pagination and filtering
 * @access  Private (campaigns:read permission)
 */
router.get(
  '/',
  requirePermission('campaigns:read'),
  [
    query('page').optional().isInt({ min: 1 }).withMessage('Page must be a positive integer'),
    query('limit').optional().isInt({ min: 1, max: 100 }).withMessage('Limit must be between 1 and 100'),
    query('status').optional().isIn(['DRAFT', 'ACTIVE', 'PAUSED', 'COMPLETED', 'CANCELLED']).withMessage('Invalid status'),
    query('type').optional().isIn(['OUTBOUND', 'INBOUND', 'MIXED']).withMessage('Invalid type'),
    query('search').optional().isString().withMessage('Search must be a string'),
  ],
  validateRequest,
  campaignController.getCampaigns.bind(campaignController)
);

/**
 * @route   GET /api/campaigns/:id
 * @desc    Get campaign by ID
 * @access  Private (campaigns:read permission)
 */
router.get(
  '/:id',
  requirePermission('campaigns:read'),
  [
    param('id').isString().withMessage('Campaign ID is required'),
  ],
  validateRequest,
  campaignController.getCampaignById.bind(campaignController)
);

/**
 * @route   POST /api/campaigns
 * @desc    Create new campaign
 * @access  Private (campaigns:write permission)
 */
router.post(
  '/',
  requirePermission('campaigns:write'),
  [
    body('name').trim().isLength({ min: 1, max: 100 }).withMessage('Name is required and must be max 100 characters'),
    body('description').optional().isString().withMessage('Description must be a string'),
    body('type').isIn(['OUTBOUND', 'INBOUND', 'MIXED']).withMessage('Invalid type'),
    body('startDate').optional().isISO8601().withMessage('Start date must be a valid ISO date'),
    body('endDate').optional().isISO8601().withMessage('End date must be a valid ISO date'),
    body('settings').optional().isObject().withMessage('Settings must be an object'),
  ],
  validateRequest,
  campaignController.createCampaign.bind(campaignController)
);

/**
 * @route   PUT /api/campaigns/:id
 * @desc    Update campaign
 * @access  Private (campaigns:write permission)
 */
router.put(
  '/:id',
  requirePermission('campaigns:write'),
  [
    param('id').isString().withMessage('Campaign ID is required'),
    body('name').optional().trim().isLength({ min: 1, max: 100 }).withMessage('Name must be max 100 characters'),
    body('description').optional().isString().withMessage('Description must be a string'),
    body('type').optional().isIn(['OUTBOUND', 'INBOUND', 'MIXED']).withMessage('Invalid type'),
    body('status').optional().isIn(['DRAFT', 'ACTIVE', 'PAUSED', 'COMPLETED', 'CANCELLED']).withMessage('Invalid status'),
    body('startDate').optional().isISO8601().withMessage('Start date must be a valid ISO date'),
    body('endDate').optional().isISO8601().withMessage('End date must be a valid ISO date'),
    body('settings').optional().isObject().withMessage('Settings must be an object'),
  ],
  validateRequest,
  campaignController.updateCampaign.bind(campaignController)
);

/**
 * @route   DELETE /api/campaigns/:id
 * @desc    Delete campaign
 * @access  Private (campaigns:delete permission)
 */
router.delete(
  '/:id',
  requirePermission('campaigns:delete'),
  [
    param('id').isString().withMessage('Campaign ID is required'),
  ],
  validateRequest,
  campaignController.deleteCampaign.bind(campaignController)
);

/**
 * @route   POST /api/campaigns/:id/start
 * @desc    Start campaign
 * @access  Private (campaigns:write permission)
 */
router.post(
  '/:id/start',
  requirePermission('campaigns:write'),
  [
    param('id').isString().withMessage('Campaign ID is required'),
  ],
  validateRequest,
  campaignController.startCampaign.bind(campaignController)
);

/**
 * @route   POST /api/campaigns/:id/pause
 * @desc    Pause campaign
 * @access  Private (campaigns:write permission)
 */
router.post(
  '/:id/pause',
  requirePermission('campaigns:write'),
  [
    param('id').isString().withMessage('Campaign ID is required'),
  ],
  validateRequest,
  campaignController.pauseCampaign.bind(campaignController)
);

/**
 * @route   POST /api/campaigns/:id/resume
 * @desc    Resume campaign
 * @access  Private (campaigns:write permission)
 */
router.post(
  '/:id/resume',
  requirePermission('campaigns:write'),
  [
    param('id').isString().withMessage('Campaign ID is required'),
  ],
  validateRequest,
  campaignController.resumeCampaign.bind(campaignController)
);

/**
 * @route   POST /api/campaigns/:id/complete
 * @desc    Complete campaign
 * @access  Private (campaigns:write permission)
 */
router.post(
  '/:id/complete',
  requirePermission('campaigns:write'),
  [
    param('id').isString().withMessage('Campaign ID is required'),
  ],
  validateRequest,
  campaignController.completeCampaign.bind(campaignController)
);

/**
 * @route   GET /api/campaigns/:id/customers
 * @desc    Get campaign customers
 * @access  Private (campaigns:read permission)
 */
router.get(
  '/:id/customers',
  requirePermission('campaigns:read'),
  [
    param('id').isString().withMessage('Campaign ID is required'),
    query('page').optional().isInt({ min: 1 }).withMessage('Page must be a positive integer'),
    query('limit').optional().isInt({ min: 1, max: 100 }).withMessage('Limit must be between 1 and 100'),
    query('status').optional().isString().withMessage('Status must be a string'),
  ],
  validateRequest,
  campaignController.getCampaignCustomers.bind(campaignController)
);

/**
 * @route   POST /api/campaigns/:id/customers
 * @desc    Add customers to campaign
 * @access  Private (campaigns:write permission)
 */
router.post(
  '/:id/customers',
  requirePermission('campaigns:write'),
  [
    param('id').isString().withMessage('Campaign ID is required'),
    body('customerIds').isArray({ min: 1, max: 1000 }).withMessage('Customer IDs must be an array with 1-1000 items'),
    body('customerIds.*').isString().withMessage('Each customer ID must be a string'),
    body('priority').optional().isInt({ min: 1, max: 10 }).withMessage('Priority must be between 1 and 10'),
  ],
  validateRequest,
  campaignController.addCustomersToCampaign.bind(campaignController)
);

/**
 * @route   DELETE /api/campaigns/:id/customers
 * @desc    Remove customers from campaign
 * @access  Private (campaigns:write permission)
 */
router.delete(
  '/:id/customers',
  requirePermission('campaigns:write'),
  [
    param('id').isString().withMessage('Campaign ID is required'),
    body('customerIds').isArray({ min: 1, max: 1000 }).withMessage('Customer IDs must be an array with 1-1000 items'),
    body('customerIds.*').isString().withMessage('Each customer ID must be a string'),
  ],
  validateRequest,
  campaignController.removeCustomersFromCampaign.bind(campaignController)
);

/**
 * @route   GET /api/campaigns/:id/calls
 * @desc    Get campaign calls
 * @access  Private (campaigns:read permission)
 */
router.get(
  '/:id/calls',
  requirePermission('campaigns:read'),
  [
    param('id').isString().withMessage('Campaign ID is required'),
    query('page').optional().isInt({ min: 1 }).withMessage('Page must be a positive integer'),
    query('limit').optional().isInt({ min: 1, max: 100 }).withMessage('Limit must be between 1 and 100'),
    query('status').optional().isString().withMessage('Status must be a string'),
  ],
  validateRequest,
  campaignController.getCampaignCalls.bind(campaignController)
);

/**
 * @route   GET /api/campaigns/:id/analytics
 * @desc    Get campaign analytics
 * @access  Private (campaigns:read permission)
 */
router.get(
  '/:id/analytics',
  requirePermission('campaigns:read'),
  [
    param('id').isString().withMessage('Campaign ID is required'),
    query('period').optional().isIn(['7d', '30d', '90d']).withMessage('Invalid period'),
  ],
  validateRequest,
  campaignController.getCampaignAnalytics.bind(campaignController)
);

/**
 * @route   GET /api/campaigns/:id/performance
 * @desc    Get campaign performance metrics
 * @access  Private (campaigns:read permission)
 */
router.get(
  '/:id/performance',
  requirePermission('campaigns:read'),
  [
    param('id').isString().withMessage('Campaign ID is required'),
  ],
  validateRequest,
  campaignController.getCampaignPerformance.bind(campaignController)
);

/**
 * @route   POST /api/campaigns/:id/clone
 * @desc    Clone campaign
 * @access  Private (campaigns:write permission)
 */
router.post(
  '/:id/clone',
  requirePermission('campaigns:write'),
  [
    param('id').isString().withMessage('Campaign ID is required'),
    body('name').trim().isLength({ min: 1, max: 100 }).withMessage('Name is required and must be max 100 characters'),
  ],
  validateRequest,
  campaignController.cloneCampaign.bind(campaignController)
);

export default router;