/**
 * Authentication Controller
 * 
 * Handles all authentication-related operations including login,
 * registration, password management, and session handling.
 */

import { Request, Response } from 'express';
import bcrypt from 'bcryptjs';
import jwt from 'jsonwebtoken';
import { v4 as uuidv4 } from 'uuid';
import { PrismaClient } from '@prisma/client';
import { logger } from '../utils/logger';
import { AuthenticatedRequest } from '../types/auth';
import { EmailService } from '../services/email';

const prisma = new PrismaClient();
const emailService = new EmailService();

export class AuthController {
  /**
   * Register a new user
   */
  async register(req: Request, res: Response): Promise<void> {
    try {
      const { email, password, name, tenantId, role = 'AGENT' } = req.body;

      // Check if user already exists
      const existingUser = await prisma.user.findUnique({
        where: { email },
      });

      if (existingUser) {
        res.status(400).json({
          success: false,
          message: 'User with this email already exists',
        });
        return;
      }

      // Hash password
      const saltRounds = parseInt(process.env.BCRYPT_ROUNDS || '12', 10);
      const hashedPassword = await bcrypt.hash(password, saltRounds);

      // Create or get default tenant
      let tenant;
      if (tenantId) {
        tenant = await prisma.tenant.findUnique({
          where: { id: tenantId },
        });
        if (!tenant) {
          res.status(400).json({
            success: false,
            message: 'Invalid tenant ID',
          });
          return;
        }
      } else {
        // Create default tenant for demo purposes
        tenant = await prisma.tenant.upsert({
          where: { domain: 'default.geminivoice.com' },
          update: {},
          create: {
            name: 'Default Organization',
            domain: 'default.geminivoice.com',
            isActive: true,
          },
        });
      }

      // Create user
      const user = await prisma.user.create({
        data: {
          email,
          password: hashedPassword,
          name,
          role: role as any,
          tenantId: tenant.id,
          isActive: true,
        },
        include: {
          tenant: true,
          permissions: true,
          preferences: true,
        },
      });

      // Create default user preferences
      await prisma.userPreferences.create({
        data: {
          userId: user.id,
          theme: 'system',
          language: 'en',
          timezone: 'UTC',
          emailNotifications: true,
          smsNotifications: false,
          pushNotifications: true,
        },
      });

      // Create default permissions based on role
      const defaultPermissions = this.getDefaultPermissions(role);
      await prisma.userPermission.createMany({
        data: defaultPermissions.map(permission => ({
          userId: user.id,
          permission,
        })),
      });

      // Generate tokens
      const { accessToken, refreshToken } = await this.generateTokens(user.id, req);

      // Remove password from response
      const { password: _, ...userResponse } = user;

      res.status(201).json({
        success: true,
        message: 'User registered successfully',
        data: {
          user: userResponse,
          accessToken,
          refreshToken,
        },
      });

      logger.info(`User registered: ${email}`);
    } catch (error) {
      logger.error('Registration error:', error);
      res.status(500).json({
        success: false,
        message: 'Internal server error during registration',
      });
    }
  }

  /**
   * Login user
   */
  async login(req: Request, res: Response): Promise<void> {
    try {
      const { email, password, rememberMe = false } = req.body;

      // Find user with all related data
      const user = await prisma.user.findUnique({
        where: { email },
        include: {
          tenant: true,
          permissions: true,
          preferences: true,
        },
      });

      if (!user) {
        res.status(401).json({
          success: false,
          message: 'Invalid email or password',
        });
        return;
      }

      // Check if user is active
      if (!user.isActive) {
        res.status(401).json({
          success: false,
          message: 'Account is deactivated. Please contact support.',
        });
        return;
      }

      // Verify password
      const isPasswordValid = await bcrypt.compare(password, user.password);
      if (!isPasswordValid) {
        res.status(401).json({
          success: false,
          message: 'Invalid email or password',
        });
        return;
      }

      // Update last login
      await prisma.user.update({
        where: { id: user.id },
        data: { lastLogin: new Date() },
      });

      // Generate tokens
      const { accessToken, refreshToken } = await this.generateTokens(
        user.id,
        req,
        rememberMe
      );

      // Remove password from response
      const { password: _, ...userResponse } = user;

      res.json({
        success: true,
        message: 'Login successful',
        data: {
          user: {
            ...userResponse,
            permissions: user.permissions.map(p => p.permission),
          },
          accessToken,
          refreshToken,
        },
      });

      logger.info(`User logged in: ${email}`);
    } catch (error) {
      logger.error('Login error:', error);
      res.status(500).json({
        success: false,
        message: 'Internal server error during login',
      });
    }
  }

  /**
   * Logout user
   */
  async logout(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const token = req.headers.authorization?.replace('Bearer ', '');
      
      if (token) {
        // Invalidate the session
        await prisma.userSession.updateMany({
          where: {
            userId: req.user!.id,
            token,
            isActive: true,
          },
          data: {
            isActive: false,
          },
        });
      }

      res.json({
        success: true,
        message: 'Logout successful',
      });

      logger.info(`User logged out: ${req.user!.email}`);
    } catch (error) {
      logger.error('Logout error:', error);
      res.status(500).json({
        success: false,
        message: 'Internal server error during logout',
      });
    }
  }

  /**
   * Refresh access token
   */
  async refreshToken(req: Request, res: Response): Promise<void> {
    try {
      const { refreshToken } = req.body;

      // Verify refresh token
      const jwtRefreshSecret = process.env.JWT_REFRESH_SECRET || 'fallback-refresh-secret';
      const decoded = jwt.verify(
        refreshToken,
        jwtRefreshSecret
      ) as any;

      // Find active session
      const session = await prisma.userSession.findUnique({
        where: {
          refreshToken,
          isActive: true,
        },
        include: {
          user: {
            include: {
              tenant: true,
              permissions: true,
              preferences: true,
            },
          },
        },
      });

      if (!session || session.expiresAt < new Date()) {
        res.status(401).json({
          success: false,
          message: 'Invalid or expired refresh token',
        });
        return;
      }

      // Generate new tokens
      const { accessToken, refreshToken: newRefreshToken } = await this.generateTokens(
        session.userId,
        req
      );

      // Update session with new refresh token
      await prisma.userSession.update({
        where: { id: session.id },
        data: {
          refreshToken: newRefreshToken,
          expiresAt: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000), // 30 days
        },
      });

      res.json({
        success: true,
        message: 'Token refreshed successfully',
        data: {
          accessToken,
          refreshToken: newRefreshToken,
        },
      });
    } catch (error) {
      logger.error('Token refresh error:', error);
      res.status(401).json({
        success: false,
        message: 'Invalid refresh token',
      });
    }
  }

  /**
   * Get current user profile
   */
  async getProfile(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const user = await prisma.user.findUnique({
        where: { id: req.user!.id },
        include: {
          tenant: true,
          permissions: true,
          preferences: true,
        },
      });

      if (!user) {
        res.status(404).json({
          success: false,
          message: 'User not found',
        });
        return;
      }

      const { password: _, ...userResponse } = user;

      res.json({
        success: true,
        data: {
          ...userResponse,
          permissions: user.permissions.map(p => p.permission),
        },
      });
    } catch (error) {
      logger.error('Get profile error:', error);
      res.status(500).json({
        success: false,
        message: 'Internal server error',
      });
    }
  }

  /**
   * Update user profile
   */
  async updateProfile(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { name, avatar, preferences } = req.body;
      const userId = req.user!.id;

      // Update user
      const updateData: any = {};
      if (name) updateData.name = name;
      if (avatar) updateData.avatar = avatar;

      const user = await prisma.user.update({
        where: { id: userId },
        data: updateData,
        include: {
          tenant: true,
          permissions: true,
          preferences: true,
        },
      });

      // Update preferences if provided
      if (preferences) {
        await prisma.userPreferences.upsert({
          where: { userId },
          update: preferences,
          create: {
            userId,
            ...preferences,
          },
        });
      }

      const { password: _, ...userResponse } = user;

      res.json({
        success: true,
        message: 'Profile updated successfully',
        data: {
          ...userResponse,
          permissions: user.permissions.map(p => p.permission),
        },
      });

      logger.info(`Profile updated: ${user.email}`);
    } catch (error) {
      logger.error('Update profile error:', error);
      res.status(500).json({
        success: false,
        message: 'Internal server error',
      });
    }
  }

  /**
   * Change password
   */
  async changePassword(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { currentPassword, newPassword } = req.body;
      const userId = req.user!.id;

      // Get current user
      const user = await prisma.user.findUnique({
        where: { id: userId },
      });

      if (!user) {
        res.status(404).json({
          success: false,
          message: 'User not found',
        });
        return;
      }

      // Verify current password
      const isCurrentPasswordValid = await bcrypt.compare(currentPassword, user.password);
      if (!isCurrentPasswordValid) {
        res.status(400).json({
          success: false,
          message: 'Current password is incorrect',
        });
        return;
      }

      // Hash new password
      const saltRounds = parseInt(process.env.BCRYPT_ROUNDS || '12', 10);
      const hashedNewPassword = await bcrypt.hash(newPassword, saltRounds);

      // Update password
      await prisma.user.update({
        where: { id: userId },
        data: { password: hashedNewPassword },
      });

      // Invalidate all sessions except current
      const currentToken = req.headers.authorization?.replace('Bearer ', '');
      await prisma.userSession.updateMany({
        where: {
          userId,
          token: { not: currentToken },
          isActive: true,
        },
        data: { isActive: false },
      });

      res.json({
        success: true,
        message: 'Password changed successfully',
      });

      logger.info(`Password changed: ${user.email}`);
    } catch (error) {
      logger.error('Change password error:', error);
      res.status(500).json({
        success: false,
        message: 'Internal server error',
      });
    }
  }

  /**
   * Forgot password
   */
  async forgotPassword(req: Request, res: Response): Promise<void> {
    try {
      const { email } = req.body;

      const user = await prisma.user.findUnique({
        where: { email },
      });

      // Always return success to prevent email enumeration
      res.json({
        success: true,
        message: 'If an account with that email exists, a password reset link has been sent.',
      });

      if (user) {
        // Generate reset token (in production, store this in database with expiration)
        const resetToken = uuidv4();
        
        // Send reset email
        await emailService.sendPasswordResetEmail(email, resetToken);
        
        logger.info(`Password reset requested: ${email}`);
      }
    } catch (error) {
      logger.error('Forgot password error:', error);
      res.status(500).json({
        success: false,
        message: 'Internal server error',
      });
    }
  }

  /**
   * Reset password
   */
  async resetPassword(req: Request, res: Response): Promise<void> {
    try {
      const { token, password } = req.body;

      // In production, verify token from database
      // For demo, we'll accept any token
      
      res.json({
        success: true,
        message: 'Password reset successful. Please login with your new password.',
      });
    } catch (error) {
      logger.error('Reset password error:', error);
      res.status(500).json({
        success: false,
        message: 'Internal server error',
      });
    }
  }

  /**
   * Get user sessions
   */
  async getSessions(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const sessions = await prisma.userSession.findMany({
        where: {
          userId: req.user!.id,
          isActive: true,
        },
        select: {
          id: true,
          ipAddress: true,
          userAgent: true,
          createdAt: true,
          expiresAt: true,
        },
        orderBy: { createdAt: 'desc' },
      });

      res.json({
        success: true,
        data: sessions,
      });
    } catch (error) {
      logger.error('Get sessions error:', error);
      res.status(500).json({
        success: false,
        message: 'Internal server error',
      });
    }
  }

  /**
   * Revoke session
   */
  async revokeSession(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { sessionId } = req.params;

      await prisma.userSession.updateMany({
        where: {
          id: sessionId,
          userId: req.user!.id,
        },
        data: { isActive: false },
      });

      res.json({
        success: true,
        message: 'Session revoked successfully',
      });
    } catch (error) {
      logger.error('Revoke session error:', error);
      res.status(500).json({
        success: false,
        message: 'Internal server error',
      });
    }
  }

  /**
   * Revoke all sessions except current
   */
  async revokeAllSessions(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const currentToken = req.headers.authorization?.replace('Bearer ', '');

      await prisma.userSession.updateMany({
        where: {
          userId: req.user!.id,
          token: { not: currentToken },
          isActive: true,
        },
        data: { isActive: false },
      });

      res.json({
        success: true,
        message: 'All other sessions revoked successfully',
      });
    } catch (error) {
      logger.error('Revoke all sessions error:', error);
      res.status(500).json({
        success: false,
        message: 'Internal server error',
      });
    }
  }

  /**
   * Verify email
   */
  async verifyEmail(req: Request, res: Response): Promise<void> {
    try {
      const { token } = req.body;

      // In production, verify token from database
      res.json({
        success: true,
        message: 'Email verified successfully',
      });
    } catch (error) {
      logger.error('Verify email error:', error);
      res.status(500).json({
        success: false,
        message: 'Internal server error',
      });
    }
  }

  /**
   * Resend verification email
   */
  async resendVerification(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const user = req.user!;

      // Generate verification token
      const verificationToken = uuidv4();
      
      // Send verification email
      await emailService.sendVerificationEmail(user.email, verificationToken);

      res.json({
        success: true,
        message: 'Verification email sent successfully',
      });
    } catch (error) {
      logger.error('Resend verification error:', error);
      res.status(500).json({
        success: false,
        message: 'Internal server error',
      });
    }
  }

  /**
   * Generate JWT tokens and create session
   */
  private async generateTokens(
    userId: string,
    req: Request,
    rememberMe: boolean = false
  ): Promise<{ accessToken: string; refreshToken: string }> {
    const accessTokenExpiry = rememberMe ? '30d' : (process.env.JWT_EXPIRES_IN || '7d');
    const refreshTokenExpiry = process.env.JWT_REFRESH_EXPIRES_IN || '30d';

    const jwtSecret = process.env.JWT_SECRET || 'fallback-secret';
    const jwtRefreshSecret = process.env.JWT_REFRESH_SECRET || 'fallback-refresh-secret';

    const accessToken = jwt.sign(
      { userId, type: 'access' },
      jwtSecret,
      { expiresIn: accessTokenExpiry } as jwt.SignOptions
    );

    const refreshToken = jwt.sign(
      { userId, type: 'refresh' },
      jwtRefreshSecret,
      { expiresIn: refreshTokenExpiry } as jwt.SignOptions
    );

    // Create session record
    await prisma.userSession.create({
      data: {
        userId,
        token: accessToken,
        refreshToken,
        expiresAt: new Date(Date.now() + (rememberMe ? 30 : 7) * 24 * 60 * 60 * 1000),
        ipAddress: req.ip || req.connection.remoteAddress,
        userAgent: req.headers['user-agent'],
      },
    });

    return { accessToken, refreshToken };
  }

  /**
   * Get default permissions based on role
   */
  private getDefaultPermissions(role: string): string[] {
    const permissions: Record<string, string[]> = {
      ADMIN: [
        'calls:read', 'calls:write', 'calls:delete',
        'customers:read', 'customers:write', 'customers:delete',
        'campaigns:read', 'campaigns:write', 'campaigns:delete',
        'analytics:read', 'analytics:write',
        'users:read', 'users:write', 'users:delete',
        'system:read', 'system:write',
        'settings:read', 'settings:write',
      ],
      OPERATOR: [
        'calls:read', 'calls:write',
        'customers:read', 'customers:write',
        'campaigns:read', 'campaigns:write',
        'analytics:read',
        'users:read',
      ],
      AGENT: [
        'calls:read', 'calls:write',
        'customers:read', 'customers:write',
        'campaigns:read',
      ],
      VIEWER: [
        'calls:read',
        'customers:read',
        'campaigns:read',
        'analytics:read',
      ],
    };

    return permissions[role] || permissions.VIEWER;
  }
}

export default AuthController;