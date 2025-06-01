/**
 * User Routes
 * 
 * User management routes for the GeminiVoiceConnect platform.
 */

import express from 'express';
import { body, param, query } from 'express-validator';
import { UserController } from '../controllers/userController';
import { validateRequest } from '../middleware/validation';
import { requirePermission, requireRole } from '../middleware/auth';

const router = express.Router();
const userController = new UserController();

/**
 * @route   GET /api/users
 * @desc    Get all users with pagination and filtering
 * @access  Private (users:read permission)
 */
router.get(
  '/',
  requirePermission('users:read'),
  [
    query('page').optional().isInt({ min: 1 }).withMessage('Page must be a positive integer'),
    query('limit').optional().isInt({ min: 1, max: 100 }).withMessage('Limit must be between 1 and 100'),
    query('search').optional().isString().withMessage('Search must be a string'),
    query('role').optional().isIn(['ADMIN', 'OPERATOR', 'AGENT', 'VIEWER']).withMessage('Invalid role'),
    query('status').optional().isIn(['active', 'inactive']).withMessage('Invalid status'),
  ],
  validateRequest,
  userController.getUsers.bind(userController)
);

/**
 * @route   GET /api/users/:id
 * @desc    Get user by ID
 * @access  Private (users:read permission)
 */
router.get(
  '/:id',
  requirePermission('users:read'),
  [
    param('id').isString().withMessage('User ID is required'),
  ],
  validateRequest,
  userController.getUserById.bind(userController)
);

/**
 * @route   POST /api/users
 * @desc    Create new user
 * @access  Private (users:write permission)
 */
router.post(
  '/',
  requirePermission('users:write'),
  [
    body('email').isEmail().normalizeEmail().withMessage('Valid email is required'),
    body('password').isLength({ min: 8 }).withMessage('Password must be at least 8 characters'),
    body('name').trim().isLength({ min: 2, max: 50 }).withMessage('Name must be between 2 and 50 characters'),
    body('role').isIn(['ADMIN', 'OPERATOR', 'AGENT', 'VIEWER']).withMessage('Invalid role'),
    body('avatar').optional().isURL().withMessage('Avatar must be a valid URL'),
  ],
  validateRequest,
  userController.createUser.bind(userController)
);

/**
 * @route   PUT /api/users/:id
 * @desc    Update user
 * @access  Private (users:write permission)
 */
router.put(
  '/:id',
  requirePermission('users:write'),
  [
    param('id').isString().withMessage('User ID is required'),
    body('email').optional().isEmail().normalizeEmail().withMessage('Valid email is required'),
    body('name').optional().trim().isLength({ min: 2, max: 50 }).withMessage('Name must be between 2 and 50 characters'),
    body('role').optional().isIn(['ADMIN', 'OPERATOR', 'AGENT', 'VIEWER']).withMessage('Invalid role'),
    body('avatar').optional().isURL().withMessage('Avatar must be a valid URL'),
    body('isActive').optional().isBoolean().withMessage('isActive must be a boolean'),
  ],
  validateRequest,
  userController.updateUser.bind(userController)
);

/**
 * @route   DELETE /api/users/:id
 * @desc    Delete user
 * @access  Private (users:delete permission)
 */
router.delete(
  '/:id',
  requirePermission('users:delete'),
  [
    param('id').isString().withMessage('User ID is required'),
  ],
  validateRequest,
  userController.deleteUser.bind(userController)
);

/**
 * @route   PUT /api/users/:id/permissions
 * @desc    Update user permissions
 * @access  Private (ADMIN role)
 */
router.put(
  '/:id/permissions',
  requireRole('ADMIN'),
  [
    param('id').isString().withMessage('User ID is required'),
    body('permissions').isArray().withMessage('Permissions must be an array'),
    body('permissions.*').isString().withMessage('Each permission must be a string'),
  ],
  validateRequest,
  userController.updateUserPermissions.bind(userController)
);

/**
 * @route   PUT /api/users/:id/password
 * @desc    Reset user password (admin only)
 * @access  Private (ADMIN role)
 */
router.put(
  '/:id/password',
  requireRole('ADMIN'),
  [
    param('id').isString().withMessage('User ID is required'),
    body('password').isLength({ min: 8 }).withMessage('Password must be at least 8 characters'),
  ],
  validateRequest,
  userController.resetUserPassword.bind(userController)
);

/**
 * @route   PUT /api/users/:id/status
 * @desc    Update user status (activate/deactivate)
 * @access  Private (users:write permission)
 */
router.put(
  '/:id/status',
  requirePermission('users:write'),
  [
    param('id').isString().withMessage('User ID is required'),
    body('isActive').isBoolean().withMessage('isActive must be a boolean'),
  ],
  validateRequest,
  userController.updateUserStatus.bind(userController)
);

/**
 * @route   GET /api/users/:id/activity
 * @desc    Get user activity log
 * @access  Private (users:read permission)
 */
router.get(
  '/:id/activity',
  requirePermission('users:read'),
  [
    param('id').isString().withMessage('User ID is required'),
    query('page').optional().isInt({ min: 1 }).withMessage('Page must be a positive integer'),
    query('limit').optional().isInt({ min: 1, max: 100 }).withMessage('Limit must be between 1 and 100'),
  ],
  validateRequest,
  userController.getUserActivity.bind(userController)
);

/**
 * @route   GET /api/users/:id/performance
 * @desc    Get user performance metrics
 * @access  Private (users:read permission)
 */
router.get(
  '/:id/performance',
  requirePermission('users:read'),
  [
    param('id').isString().withMessage('User ID is required'),
    query('period').optional().isIn(['7d', '30d', '90d']).withMessage('Invalid period'),
  ],
  validateRequest,
  userController.getUserPerformance.bind(userController)
);

export default router;