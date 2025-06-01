/**
 * User Controller
 * 
 * Handles user management operations for the GeminiVoiceConnect platform.
 */

import { Response } from 'express';
import { PrismaClient } from '@prisma/client';
import bcrypt from 'bcryptjs';
import { AuthenticatedRequest } from '../types/auth';
import { logger } from '../utils/logger';

const prisma = new PrismaClient();

export class UserController {
  /**
   * Get all users with pagination and filtering
   */
  async getUsers(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const {
        page = 1,
        limit = 20,
        search,
        role,
        status
      } = req.query;

      const skip = (Number(page) - 1) * Number(limit);
      const take = Number(limit);

      // Build where clause
      const where: any = {
        tenantId: req.user!.tenantId,
      };

      if (search) {
        where.OR = [
          { name: { contains: search as string } },
          { email: { contains: search as string } },
        ];
      }

      if (role) {
        where.role = role;
      }

      if (status) {
        where.isActive = status === 'active';
      }

      const [users, total] = await Promise.all([
        prisma.user.findMany({
          where,
          skip,
          take,
          include: {
            tenant: true,
            permissions: true,
            preferences: true,
          },
          orderBy: { createdAt: 'desc' },
        }),
        prisma.user.count({ where }),
      ]);

      // Remove passwords from response
      const usersResponse = users.map(user => {
        const { password, ...userWithoutPassword } = user;
        return {
          ...userWithoutPassword,
          permissions: user.permissions.map(p => p.permission),
        };
      });

      res.json({
        success: true,
        data: {
          users: usersResponse,
          pagination: {
            page: Number(page),
            limit: Number(limit),
            total,
            pages: Math.ceil(total / Number(limit)),
          },
        },
      });
    } catch (error) {
      logger.error('Get users error:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to fetch users',
      });
    }
  }

  /**
   * Get user by ID
   */
  async getUserById(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { id } = req.params;

      const user = await prisma.user.findFirst({
        where: {
          id,
          tenantId: req.user!.tenantId,
        },
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

      const { password, ...userResponse } = user;

      res.json({
        success: true,
        data: {
          ...userResponse,
          permissions: user.permissions.map(p => p.permission),
        },
      });
    } catch (error) {
      logger.error('Get user by ID error:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to fetch user',
      });
    }
  }

  /**
   * Create new user
   */
  async createUser(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { email, password, name, role, avatar } = req.body;

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

      // Create user
      const user = await prisma.user.create({
        data: {
          email,
          password: hashedPassword,
          name,
          role,
          tenantId: req.user!.tenantId,
          avatar,
          isActive: true,
        },
        include: {
          tenant: true,
          permissions: true,
          preferences: true,
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

      // Create default preferences
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

      const { password: _, ...userResponse } = user;

      res.status(201).json({
        success: true,
        message: 'User created successfully',
        data: userResponse,
      });

      logger.info(`User created: ${email} by ${req.user!.email}`);
    } catch (error) {
      logger.error('Create user error:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to create user',
      });
    }
  }

  /**
   * Update user
   */
  async updateUser(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { id } = req.params;
      const { email, name, role, avatar, isActive } = req.body;

      // Check if user exists and belongs to tenant
      const existingUser = await prisma.user.findFirst({
        where: {
          id,
          tenantId: req.user!.tenantId,
        },
      });

      if (!existingUser) {
        res.status(404).json({
          success: false,
          message: 'User not found',
        });
        return;
      }

      // Check if email is already taken by another user
      if (email && email !== existingUser.email) {
        const emailExists = await prisma.user.findUnique({
          where: { email },
        });

        if (emailExists) {
          res.status(400).json({
            success: false,
            message: 'Email is already taken',
          });
          return;
        }
      }

      // Update user
      const updateData: any = {};
      if (email) updateData.email = email;
      if (name) updateData.name = name;
      if (role) updateData.role = role;
      if (avatar !== undefined) updateData.avatar = avatar;
      if (isActive !== undefined) updateData.isActive = isActive;

      const user = await prisma.user.update({
        where: { id },
        data: updateData,
        include: {
          tenant: true,
          permissions: true,
          preferences: true,
        },
      });

      const { password, ...userResponse } = user;

      res.json({
        success: true,
        message: 'User updated successfully',
        data: {
          ...userResponse,
          permissions: user.permissions.map(p => p.permission),
        },
      });

      logger.info(`User updated: ${user.email} by ${req.user!.email}`);
    } catch (error) {
      logger.error('Update user error:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to update user',
      });
    }
  }

  /**
   * Delete user
   */
  async deleteUser(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { id } = req.params;

      // Check if user exists and belongs to tenant
      const user = await prisma.user.findFirst({
        where: {
          id,
          tenantId: req.user!.tenantId,
        },
      });

      if (!user) {
        res.status(404).json({
          success: false,
          message: 'User not found',
        });
        return;
      }

      // Prevent self-deletion
      if (user.id === req.user!.id) {
        res.status(400).json({
          success: false,
          message: 'Cannot delete your own account',
        });
        return;
      }

      // Delete user (cascade will handle related records)
      await prisma.user.delete({
        where: { id },
      });

      res.json({
        success: true,
        message: 'User deleted successfully',
      });

      logger.info(`User deleted: ${user.email} by ${req.user!.email}`);
    } catch (error) {
      logger.error('Delete user error:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to delete user',
      });
    }
  }

  /**
   * Update user permissions
   */
  async updateUserPermissions(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { id } = req.params;
      const { permissions } = req.body;

      // Check if user exists and belongs to tenant
      const user = await prisma.user.findFirst({
        where: {
          id,
          tenantId: req.user!.tenantId,
        },
      });

      if (!user) {
        res.status(404).json({
          success: false,
          message: 'User not found',
        });
        return;
      }

      // Delete existing permissions
      await prisma.userPermission.deleteMany({
        where: { userId: id },
      });

      // Create new permissions
      if (permissions.length > 0) {
        await prisma.userPermission.createMany({
          data: permissions.map((permission: string) => ({
            userId: id,
            permission,
          })),
        });
      }

      res.json({
        success: true,
        message: 'User permissions updated successfully',
      });

      logger.info(`User permissions updated: ${user.email} by ${req.user!.email}`);
    } catch (error) {
      logger.error('Update user permissions error:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to update user permissions',
      });
    }
  }

  /**
   * Reset user password (admin only)
   */
  async resetUserPassword(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { id } = req.params;
      const { password } = req.body;

      // Check if user exists and belongs to tenant
      const user = await prisma.user.findFirst({
        where: {
          id,
          tenantId: req.user!.tenantId,
        },
      });

      if (!user) {
        res.status(404).json({
          success: false,
          message: 'User not found',
        });
        return;
      }

      // Hash new password
      const saltRounds = parseInt(process.env.BCRYPT_ROUNDS || '12', 10);
      const hashedPassword = await bcrypt.hash(password, saltRounds);

      // Update password
      await prisma.user.update({
        where: { id },
        data: { password: hashedPassword },
      });

      // Invalidate all user sessions
      await prisma.userSession.updateMany({
        where: { userId: id },
        data: { isActive: false },
      });

      res.json({
        success: true,
        message: 'Password reset successfully',
      });

      logger.info(`Password reset for user: ${user.email} by ${req.user!.email}`);
    } catch (error) {
      logger.error('Reset user password error:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to reset password',
      });
    }
  }

  /**
   * Update user status
   */
  async updateUserStatus(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { id } = req.params;
      const { isActive } = req.body;

      // Check if user exists and belongs to tenant
      const user = await prisma.user.findFirst({
        where: {
          id,
          tenantId: req.user!.tenantId,
        },
      });

      if (!user) {
        res.status(404).json({
          success: false,
          message: 'User not found',
        });
        return;
      }

      // Prevent self-deactivation
      if (user.id === req.user!.id && !isActive) {
        res.status(400).json({
          success: false,
          message: 'Cannot deactivate your own account',
        });
        return;
      }

      // Update status
      await prisma.user.update({
        where: { id },
        data: { isActive },
      });

      // If deactivating, invalidate all sessions
      if (!isActive) {
        await prisma.userSession.updateMany({
          where: { userId: id },
          data: { isActive: false },
        });
      }

      res.json({
        success: true,
        message: `User ${isActive ? 'activated' : 'deactivated'} successfully`,
      });

      logger.info(`User ${isActive ? 'activated' : 'deactivated'}: ${user.email} by ${req.user!.email}`);
    } catch (error) {
      logger.error('Update user status error:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to update user status',
      });
    }
  }

  /**
   * Get user activity log
   */
  async getUserActivity(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { id } = req.params;
      const { page = 1, limit = 20 } = req.query;

      // Check if user exists and belongs to tenant
      const user = await prisma.user.findFirst({
        where: {
          id,
          tenantId: req.user!.tenantId,
        },
      });

      if (!user) {
        res.status(404).json({
          success: false,
          message: 'User not found',
        });
        return;
      }

      const skip = (Number(page) - 1) * Number(limit);
      const take = Number(limit);

      // Get user's recent calls as activity
      const [calls, total] = await Promise.all([
        prisma.call.findMany({
          where: { userId: id },
          include: {
            customer: true,
            campaign: true,
          },
          orderBy: { createdAt: 'desc' },
          skip,
          take,
        }),
        prisma.call.count({ where: { userId: id } }),
      ]);

      const activity = calls.map(call => ({
        id: call.id,
        type: 'call',
        action: `${call.direction} call ${call.status}`,
        details: {
          phoneNumber: call.phoneNumber,
          duration: call.duration,
          outcome: call.outcome,
          customer: call.customer ? `${call.customer.firstName} ${call.customer.lastName}` : null,
          campaign: call.campaign?.name,
        },
        timestamp: call.createdAt,
      }));

      res.json({
        success: true,
        data: {
          activity,
          pagination: {
            page: Number(page),
            limit: Number(limit),
            total,
            pages: Math.ceil(total / Number(limit)),
          },
        },
      });
    } catch (error) {
      logger.error('Get user activity error:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to fetch user activity',
      });
    }
  }

  /**
   * Get user performance metrics
   */
  async getUserPerformance(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { id } = req.params;
      const { period = '30d' } = req.query;

      // Check if user exists and belongs to tenant
      const user = await prisma.user.findFirst({
        where: {
          id,
          tenantId: req.user!.tenantId,
        },
      });

      if (!user) {
        res.status(404).json({
          success: false,
          message: 'User not found',
        });
        return;
      }

      const days = this.getPeriodDays(period as string);
      const startDate = new Date();
      startDate.setDate(startDate.getDate() - days);

      const calls = await prisma.call.findMany({
        where: {
          userId: id,
          createdAt: { gte: startDate },
        },
      });

      const completedCalls = calls.filter(c => c.status === 'COMPLETED');
      const successfulCalls = completedCalls.filter(c => 
        c.outcome && ['SALE', 'APPOINTMENT', 'INTERESTED'].includes(c.outcome)
      );

      const totalDuration = completedCalls.reduce((sum, call) => sum + (call.duration || 0), 0);
      const avgDuration = completedCalls.length > 0 ? totalDuration / completedCalls.length : 0;

      const performance = {
        period,
        totalCalls: calls.length,
        completedCalls: completedCalls.length,
        successfulCalls: successfulCalls.length,
        successRate: completedCalls.length > 0 ? (successfulCalls.length / completedCalls.length) * 100 : 0,
        avgCallDuration: Math.round(avgDuration),
        totalTalkTime: totalDuration,
        callsPerDay: calls.length / days,
      };

      res.json({
        success: true,
        data: performance,
      });
    } catch (error) {
      logger.error('Get user performance error:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to fetch user performance',
      });
    }
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

  /**
   * Get number of days from period string
   */
  private getPeriodDays(period: string): number {
    switch (period) {
      case '7d': return 7;
      case '30d': return 30;
      case '90d': return 90;
      default: return 30;
    }
  }
}