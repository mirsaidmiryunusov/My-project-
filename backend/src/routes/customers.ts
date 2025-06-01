/**
 * Customer Routes
 * 
 * Customer management routes for the GeminiVoiceConnect platform.
 */

import express from 'express';
import { body, param, query } from 'express-validator';
import { CustomerController } from '../controllers/customerController';
import { validateRequest } from '../middleware/validation';
import { requirePermission } from '../middleware/auth';

const router = express.Router();
const customerController = new CustomerController();

/**
 * @route   GET /api/customers
 * @desc    Get all customers with pagination and filtering
 * @access  Private (customers:read permission)
 */
router.get(
  '/',
  requirePermission('customers:read'),
  [
    query('page').optional().isInt({ min: 1 }).withMessage('Page must be a positive integer'),
    query('limit').optional().isInt({ min: 1, max: 100 }).withMessage('Limit must be between 1 and 100'),
    query('search').optional().isString().withMessage('Search must be a string'),
    query('status').optional().isIn(['active', 'inactive']).withMessage('Invalid status'),
    query('tags').optional().isString().withMessage('Tags must be a string'),
  ],
  validateRequest,
  customerController.getCustomers.bind(customerController)
);

/**
 * @route   GET /api/customers/:id
 * @desc    Get customer by ID
 * @access  Private (customers:read permission)
 */
router.get(
  '/:id',
  requirePermission('customers:read'),
  [
    param('id').isString().withMessage('Customer ID is required'),
  ],
  validateRequest,
  customerController.getCustomerById.bind(customerController)
);

/**
 * @route   POST /api/customers
 * @desc    Create new customer
 * @access  Private (customers:write permission)
 */
router.post(
  '/',
  requirePermission('customers:write'),
  [
    body('firstName').trim().isLength({ min: 1, max: 50 }).withMessage('First name is required and must be max 50 characters'),
    body('lastName').trim().isLength({ min: 1, max: 50 }).withMessage('Last name is required and must be max 50 characters'),
    body('email').optional().isEmail().normalizeEmail().withMessage('Valid email is required'),
    body('phone').isMobilePhone().withMessage('Valid phone number is required'),
    body('address').optional().isObject().withMessage('Address must be an object'),
    body('tags').optional().isArray().withMessage('Tags must be an array'),
    body('notes').optional().isString().withMessage('Notes must be a string'),
  ],
  validateRequest,
  customerController.createCustomer.bind(customerController)
);

/**
 * @route   PUT /api/customers/:id
 * @desc    Update customer
 * @access  Private (customers:write permission)
 */
router.put(
  '/:id',
  requirePermission('customers:write'),
  [
    param('id').isString().withMessage('Customer ID is required'),
    body('firstName').optional().trim().isLength({ min: 1, max: 50 }).withMessage('First name must be max 50 characters'),
    body('lastName').optional().trim().isLength({ min: 1, max: 50 }).withMessage('Last name must be max 50 characters'),
    body('email').optional().isEmail().normalizeEmail().withMessage('Valid email is required'),
    body('phone').optional().isMobilePhone().withMessage('Valid phone number is required'),
    body('address').optional().isObject().withMessage('Address must be an object'),
    body('tags').optional().isArray().withMessage('Tags must be an array'),
    body('notes').optional().isString().withMessage('Notes must be a string'),
    body('isActive').optional().isBoolean().withMessage('isActive must be a boolean'),
  ],
  validateRequest,
  customerController.updateCustomer.bind(customerController)
);

/**
 * @route   DELETE /api/customers/:id
 * @desc    Delete customer
 * @access  Private (customers:delete permission)
 */
router.delete(
  '/:id',
  requirePermission('customers:delete'),
  [
    param('id').isString().withMessage('Customer ID is required'),
  ],
  validateRequest,
  customerController.deleteCustomer.bind(customerController)
);

/**
 * @route   GET /api/customers/:id/calls
 * @desc    Get customer call history
 * @access  Private (customers:read permission)
 */
router.get(
  '/:id/calls',
  requirePermission('customers:read'),
  [
    param('id').isString().withMessage('Customer ID is required'),
    query('page').optional().isInt({ min: 1 }).withMessage('Page must be a positive integer'),
    query('limit').optional().isInt({ min: 1, max: 100 }).withMessage('Limit must be between 1 and 100'),
  ],
  validateRequest,
  customerController.getCustomerCalls.bind(customerController)
);

/**
 * @route   POST /api/customers/:id/calls
 * @desc    Create call for customer
 * @access  Private (customers:write permission)
 */
router.post(
  '/:id/calls',
  requirePermission('customers:write'),
  [
    param('id').isString().withMessage('Customer ID is required'),
    body('direction').isIn(['INBOUND', 'OUTBOUND']).withMessage('Invalid direction'),
    body('campaignId').optional().isString().withMessage('Campaign ID must be a string'),
  ],
  validateRequest,
  customerController.createCustomerCall.bind(customerController)
);

/**
 * @route   GET /api/customers/:id/analytics
 * @desc    Get customer analytics
 * @access  Private (customers:read permission)
 */
router.get(
  '/:id/analytics',
  requirePermission('customers:read'),
  [
    param('id').isString().withMessage('Customer ID is required'),
    query('period').optional().isIn(['7d', '30d', '90d']).withMessage('Invalid period'),
  ],
  validateRequest,
  customerController.getCustomerAnalytics.bind(customerController)
);

/**
 * @route   POST /api/customers/import
 * @desc    Import customers from CSV/Excel
 * @access  Private (customers:write permission)
 */
router.post(
  '/import',
  requirePermission('customers:write'),
  [
    body('customers').isArray({ min: 1, max: 1000 }).withMessage('Customers must be an array with 1-1000 items'),
    body('customers.*.firstName').trim().isLength({ min: 1, max: 50 }).withMessage('First name is required'),
    body('customers.*.lastName').trim().isLength({ min: 1, max: 50 }).withMessage('Last name is required'),
    body('customers.*.phone').isMobilePhone().withMessage('Valid phone number is required'),
  ],
  validateRequest,
  customerController.importCustomers.bind(customerController)
);

/**
 * @route   GET /api/customers/export
 * @desc    Export customers to CSV/Excel
 * @access  Private (customers:read permission)
 */
router.get(
  '/export',
  requirePermission('customers:read'),
  [
    query('format').optional().isIn(['csv', 'xlsx']).withMessage('Invalid format'),
    query('filters').optional().isString().withMessage('Filters must be a string'),
  ],
  validateRequest,
  customerController.exportCustomers.bind(customerController)
);

/**
 * @route   POST /api/customers/bulk-update
 * @desc    Bulk update customers
 * @access  Private (customers:write permission)
 */
router.post(
  '/bulk-update',
  requirePermission('customers:write'),
  [
    body('customerIds').isArray({ min: 1, max: 100 }).withMessage('Customer IDs must be an array with 1-100 items'),
    body('updates').isObject().withMessage('Updates must be an object'),
  ],
  validateRequest,
  customerController.bulkUpdateCustomers.bind(customerController)
);

/**
 * @route   POST /api/customers/:id/tags
 * @desc    Add tags to customer
 * @access  Private (customers:write permission)
 */
router.post(
  '/:id/tags',
  requirePermission('customers:write'),
  [
    param('id').isString().withMessage('Customer ID is required'),
    body('tags').isArray().withMessage('Tags must be an array'),
    body('tags.*').isString().withMessage('Each tag must be a string'),
  ],
  validateRequest,
  customerController.addCustomerTags.bind(customerController)
);

/**
 * @route   DELETE /api/customers/:id/tags
 * @desc    Remove tags from customer
 * @access  Private (customers:write permission)
 */
router.delete(
  '/:id/tags',
  requirePermission('customers:write'),
  [
    param('id').isString().withMessage('Customer ID is required'),
    body('tags').isArray().withMessage('Tags must be an array'),
    body('tags.*').isString().withMessage('Each tag must be a string'),
  ],
  validateRequest,
  customerController.removeCustomerTags.bind(customerController)
);

/**
 * @route   GET /api/customers/search
 * @desc    Advanced customer search
 * @access  Private (customers:read permission)
 */
router.get(
  '/search',
  requirePermission('customers:read'),
  [
    query('q').isString().isLength({ min: 1 }).withMessage('Search query is required'),
    query('fields').optional().isString().withMessage('Fields must be a string'),
    query('page').optional().isInt({ min: 1 }).withMessage('Page must be a positive integer'),
    query('limit').optional().isInt({ min: 1, max: 100 }).withMessage('Limit must be between 1 and 100'),
  ],
  validateRequest,
  customerController.searchCustomers.bind(customerController)
);

export default router;