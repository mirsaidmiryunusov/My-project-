/**
 * Error Handling Middleware
 * 
 * Global error handler and 404 handler for the Express application.
 */

import { Request, Response, NextFunction } from 'express';
import { logger } from '../utils/logger';

export interface AppError extends Error {
  statusCode?: number;
  isOperational?: boolean;
}

/**
 * Global error handler middleware
 */
export const errorHandler = (
  error: AppError,
  req: Request,
  res: Response,
  next: NextFunction
): void => {
  const statusCode = error.statusCode || 500;
  const isProduction = process.env.NODE_ENV === 'production';

  // Log error
  logger.error('Error occurred:', {
    message: error.message,
    stack: error.stack,
    statusCode,
    url: req.url,
    method: req.method,
    ip: req.ip,
    userAgent: req.headers['user-agent'],
  });

  // Prepare error response
  const errorResponse: any = {
    success: false,
    message: error.message || 'Internal server error',
    statusCode,
  };

  // Include stack trace in development
  if (!isProduction) {
    errorResponse.stack = error.stack;
    errorResponse.details = {
      url: req.url,
      method: req.method,
      headers: req.headers,
      body: req.body,
      params: req.params,
      query: req.query,
    };
  }

  // Handle specific error types
  if (error.name === 'ValidationError') {
    errorResponse.message = 'Validation failed';
    errorResponse.statusCode = 400;
  } else if (error.name === 'CastError') {
    errorResponse.message = 'Invalid ID format';
    errorResponse.statusCode = 400;
  } else if (error.name === 'MongoError' && (error as any).code === 11000) {
    errorResponse.message = 'Duplicate field value';
    errorResponse.statusCode = 400;
  } else if (error.name === 'JsonWebTokenError') {
    errorResponse.message = 'Invalid token';
    errorResponse.statusCode = 401;
  } else if (error.name === 'TokenExpiredError') {
    errorResponse.message = 'Token expired';
    errorResponse.statusCode = 401;
  }

  res.status(errorResponse.statusCode).json(errorResponse);
};

/**
 * 404 Not Found handler
 */
export const notFoundHandler = (
  req: Request,
  res: Response,
  next: NextFunction
): void => {
  const error: AppError = new Error(`Route ${req.originalUrl} not found`);
  error.statusCode = 404;
  error.isOperational = true;

  next(error);
};

/**
 * Async error wrapper
 */
export const asyncHandler = (fn: Function) => {
  return (req: Request, res: Response, next: NextFunction) => {
    Promise.resolve(fn(req, res, next)).catch(next);
  };
};

/**
 * Create operational error
 */
export const createError = (message: string, statusCode: number = 500): AppError => {
  const error: AppError = new Error(message);
  error.statusCode = statusCode;
  error.isOperational = true;
  return error;
};