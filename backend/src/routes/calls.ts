/**
 * Call Routes
 * 
 * Call management and monitoring routes for the GeminiVoiceConnect platform.
 */

import express from 'express';
import { body, param, query } from 'express-validator';
import { CallController } from '../controllers/callController';
import { validateRequest } from '../middleware/validation';
import { requirePermission } from '../middleware/auth';

const router = express.Router();
const callController = new CallController();

/**
 * @route   GET /api/calls
 * @desc    Get all calls with pagination and filtering
 * @access  Private (calls:read permission)
 */
router.get(
  '/',
  requirePermission('calls:read'),
  [
    query('page').optional().isInt({ min: 1 }).withMessage('Page must be a positive integer'),
    query('limit').optional().isInt({ min: 1, max: 100 }).withMessage('Limit must be between 1 and 100'),
    query('status').optional().isIn(['PENDING', 'RINGING', 'ANSWERED', 'BUSY', 'NO_ANSWER', 'FAILED', 'COMPLETED']).withMessage('Invalid status'),
    query('direction').optional().isIn(['INBOUND', 'OUTBOUND']).withMessage('Invalid direction'),
    query('outcome').optional().isString().withMessage('Outcome must be a string'),
    query('startDate').optional().isISO8601().withMessage('Start date must be a valid ISO date'),
    query('endDate').optional().isISO8601().withMessage('End date must be a valid ISO date'),
    query('search').optional().isString().withMessage('Search must be a string'),
  ],
  validateRequest,
  callController.getCalls.bind(callController)
);

/**
 * @route   GET /api/calls/:id
 * @desc    Get call by ID
 * @access  Private (calls:read permission)
 */
router.get(
  '/:id',
  requirePermission('calls:read'),
  [
    param('id').isString().withMessage('Call ID is required'),
  ],
  validateRequest,
  callController.getCallById.bind(callController)
);

/**
 * @route   POST /api/calls
 * @desc    Create new call
 * @access  Private (calls:write permission)
 */
router.post(
  '/',
  requirePermission('calls:write'),
  [
    body('phoneNumber').isMobilePhone('any').withMessage('Valid phone number is required'),
    body('direction').isIn(['INBOUND', 'OUTBOUND']).withMessage('Invalid direction'),
    body('customerId').optional().isString().withMessage('Customer ID must be a string'),
    body('campaignId').optional().isString().withMessage('Campaign ID must be a string'),
  ],
  validateRequest,
  callController.createCall.bind(callController)
);

/**
 * @route   PUT /api/calls/:id
 * @desc    Update call
 * @access  Private (calls:write permission)
 */
router.put(
  '/:id',
  requirePermission('calls:write'),
  [
    param('id').isString().withMessage('Call ID is required'),
    body('status').optional().isIn(['PENDING', 'RINGING', 'ANSWERED', 'BUSY', 'NO_ANSWER', 'FAILED', 'COMPLETED']).withMessage('Invalid status'),
    body('outcome').optional().isString().withMessage('Outcome must be a string'),
    body('notes').optional().isString().withMessage('Notes must be a string'),
    body('sentiment').optional().isIn(['POSITIVE', 'NEGATIVE', 'NEUTRAL']).withMessage('Invalid sentiment'),
    body('duration').optional().isInt({ min: 0 }).withMessage('Duration must be a positive integer'),
  ],
  validateRequest,
  callController.updateCall.bind(callController)
);

/**
 * @route   DELETE /api/calls/:id
 * @desc    Delete call
 * @access  Private (calls:delete permission)
 */
router.delete(
  '/:id',
  requirePermission('calls:delete'),
  [
    param('id').isString().withMessage('Call ID is required'),
  ],
  validateRequest,
  callController.deleteCall.bind(callController)
);

/**
 * @route   POST /api/calls/:id/start
 * @desc    Start a call
 * @access  Private (calls:write permission)
 */
router.post(
  '/:id/start',
  requirePermission('calls:write'),
  [
    param('id').isString().withMessage('Call ID is required'),
  ],
  validateRequest,
  callController.startCall.bind(callController)
);

/**
 * @route   POST /api/calls/:id/end
 * @desc    End a call
 * @access  Private (calls:write permission)
 */
router.post(
  '/:id/end',
  requirePermission('calls:write'),
  [
    param('id').isString().withMessage('Call ID is required'),
    body('outcome').optional().isString().withMessage('Outcome must be a string'),
    body('notes').optional().isString().withMessage('Notes must be a string'),
    body('sentiment').optional().isIn(['POSITIVE', 'NEGATIVE', 'NEUTRAL']).withMessage('Invalid sentiment'),
  ],
  validateRequest,
  callController.endCall.bind(callController)
);

/**
 * @route   GET /api/calls/live
 * @desc    Get live/active calls
 * @access  Private (calls:read permission)
 */
router.get(
  '/live',
  requirePermission('calls:read'),
  callController.getLiveCalls.bind(callController)
);

/**
 * @route   GET /api/calls/stats
 * @desc    Get call statistics
 * @access  Private (calls:read permission)
 */
router.get(
  '/stats',
  requirePermission('calls:read'),
  [
    query('period').optional().isIn(['1h', '24h', '7d', '30d']).withMessage('Invalid period'),
    query('groupBy').optional().isIn(['hour', 'day', 'week', 'month']).withMessage('Invalid groupBy'),
  ],
  validateRequest,
  callController.getCallStats.bind(callController)
);

/**
 * @route   POST /api/calls/bulk
 * @desc    Create multiple calls (bulk operation)
 * @access  Private (calls:write permission)
 */
router.post(
  '/bulk',
  requirePermission('calls:write'),
  [
    body('calls').isArray({ min: 1, max: 100 }).withMessage('Calls must be an array with 1-100 items'),
    body('calls.*.phoneNumber').isMobilePhone('any').withMessage('Valid phone number is required'),
    body('calls.*.direction').isIn(['INBOUND', 'OUTBOUND']).withMessage('Invalid direction'),
    body('calls.*.customerId').optional().isString().withMessage('Customer ID must be a string'),
    body('calls.*.campaignId').optional().isString().withMessage('Campaign ID must be a string'),
  ],
  validateRequest,
  callController.createBulkCalls.bind(callController)
);

/**
 * @route   GET /api/calls/:id/recording
 * @desc    Get call recording
 * @access  Private (calls:read permission)
 */
router.get(
  '/:id/recording',
  requirePermission('calls:read'),
  [
    param('id').isString().withMessage('Call ID is required'),
  ],
  validateRequest,
  callController.getCallRecording.bind(callController)
);

/**
 * @route   GET /api/calls/:id/transcript
 * @desc    Get call transcript
 * @access  Private (calls:read permission)
 */
router.get(
  '/:id/transcript',
  requirePermission('calls:read'),
  [
    param('id').isString().withMessage('Call ID is required'),
  ],
  validateRequest,
  callController.getCallTranscript.bind(callController)
);

/**
 * @route   POST /api/calls/:id/notes
 * @desc    Add notes to call
 * @access  Private (calls:write permission)
 */
router.post(
  '/:id/notes',
  requirePermission('calls:write'),
  [
    param('id').isString().withMessage('Call ID is required'),
    body('notes').isString().isLength({ min: 1, max: 1000 }).withMessage('Notes must be between 1 and 1000 characters'),
  ],
  validateRequest,
  callController.addCallNotes.bind(callController)
);

export default router;