/**
 * Campaign Controller
 * 
 * Handles campaign management operations for the GeminiVoiceConnect platform.
 */

import { Response } from 'express';
import { PrismaClient } from '@prisma/client';
import { AuthenticatedRequest } from '../types/auth';
import { logger } from '../utils/logger';

const prisma = new PrismaClient();

export class CampaignController {
  async getCampaigns(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { page = 1, limit = 20, status, type, search } = req.query;
      const skip = (Number(page) - 1) * Number(limit);
      const take = Number(limit);

      const where: any = { tenantId: req.user!.tenantId };
      
      if (status) where.status = status;
      if (type) where.type = type;
      if (search) {
        where.OR = [
          { name: { contains: search as string } },
          { description: { contains: search as string } },
        ];
      }

      const [campaigns, total] = await Promise.all([
        prisma.campaign.findMany({
          where,
          skip,
          take,
          include: { user: true, customers: true, calls: true },
          orderBy: { createdAt: 'desc' },
        }),
        prisma.campaign.count({ where }),
      ]);

      res.json({
        success: true,
        data: {
          campaigns,
          pagination: {
            page: Number(page),
            limit: Number(limit),
            total,
            pages: Math.ceil(total / Number(limit)),
          },
        },
      });
    } catch (error) {
      logger.error('Get campaigns error:', error);
      res.status(500).json({ success: false, message: 'Failed to fetch campaigns' });
    }
  }

  async getCampaignById(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { id } = req.params;
      
      const campaign = await prisma.campaign.findFirst({
        where: { id, tenantId: req.user!.tenantId },
        include: { 
          user: true, 
          customers: { include: { customer: true } }, 
          calls: true 
        },
      });

      if (!campaign) {
        res.status(404).json({ success: false, message: 'Campaign not found' });
        return;
      }

      res.json({ success: true, data: campaign });
    } catch (error) {
      logger.error('Get campaign by ID error:', error);
      res.status(500).json({ success: false, message: 'Failed to fetch campaign' });
    }
  }

  async createCampaign(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { name, description, type, startDate, endDate, settings } = req.body;

      const campaign = await prisma.campaign.create({
        data: {
          name,
          description,
          type,
          status: 'DRAFT',
          startDate: startDate ? new Date(startDate) : null,
          endDate: endDate ? new Date(endDate) : null,
          settings: settings ? JSON.stringify(settings) : null,
          tenantId: req.user!.tenantId,
          userId: req.user!.id,
        },
        include: { user: true },
      });

      res.status(201).json({
        success: true,
        message: 'Campaign created successfully',
        data: campaign,
      });
    } catch (error) {
      logger.error('Create campaign error:', error);
      res.status(500).json({ success: false, message: 'Failed to create campaign' });
    }
  }

  async updateCampaign(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { id } = req.params;
      const { name, description, type, status, startDate, endDate, settings } = req.body;

      const campaign = await prisma.campaign.findFirst({
        where: { id, tenantId: req.user!.tenantId },
      });

      if (!campaign) {
        res.status(404).json({ success: false, message: 'Campaign not found' });
        return;
      }

      const updateData: any = {};
      if (name) updateData.name = name;
      if (description) updateData.description = description;
      if (type) updateData.type = type;
      if (status) updateData.status = status;
      if (startDate) updateData.startDate = new Date(startDate);
      if (endDate) updateData.endDate = new Date(endDate);
      if (settings) updateData.settings = JSON.stringify(settings);

      const updatedCampaign = await prisma.campaign.update({
        where: { id },
        data: updateData,
        include: { user: true },
      });

      res.json({
        success: true,
        message: 'Campaign updated successfully',
        data: updatedCampaign,
      });
    } catch (error) {
      logger.error('Update campaign error:', error);
      res.status(500).json({ success: false, message: 'Failed to update campaign' });
    }
  }

  async deleteCampaign(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { id } = req.params;

      const campaign = await prisma.campaign.findFirst({
        where: { id, tenantId: req.user!.tenantId },
      });

      if (!campaign) {
        res.status(404).json({ success: false, message: 'Campaign not found' });
        return;
      }

      await prisma.campaign.delete({ where: { id } });

      res.json({ success: true, message: 'Campaign deleted successfully' });
    } catch (error) {
      logger.error('Delete campaign error:', error);
      res.status(500).json({ success: false, message: 'Failed to delete campaign' });
    }
  }

  async startCampaign(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { id } = req.params;

      const campaign = await prisma.campaign.update({
        where: { id },
        data: { status: 'ACTIVE' },
      });

      res.json({
        success: true,
        message: 'Campaign started successfully',
        data: campaign,
      });
    } catch (error) {
      logger.error('Start campaign error:', error);
      res.status(500).json({ success: false, message: 'Failed to start campaign' });
    }
  }

  async pauseCampaign(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { id } = req.params;

      const campaign = await prisma.campaign.update({
        where: { id },
        data: { status: 'PAUSED' },
      });

      res.json({
        success: true,
        message: 'Campaign paused successfully',
        data: campaign,
      });
    } catch (error) {
      logger.error('Pause campaign error:', error);
      res.status(500).json({ success: false, message: 'Failed to pause campaign' });
    }
  }

  async resumeCampaign(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { id } = req.params;

      const campaign = await prisma.campaign.update({
        where: { id },
        data: { status: 'ACTIVE' },
      });

      res.json({
        success: true,
        message: 'Campaign resumed successfully',
        data: campaign,
      });
    } catch (error) {
      logger.error('Resume campaign error:', error);
      res.status(500).json({ success: false, message: 'Failed to resume campaign' });
    }
  }

  async completeCampaign(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { id } = req.params;

      const campaign = await prisma.campaign.update({
        where: { id },
        data: { status: 'COMPLETED' },
      });

      res.json({
        success: true,
        message: 'Campaign completed successfully',
        data: campaign,
      });
    } catch (error) {
      logger.error('Complete campaign error:', error);
      res.status(500).json({ success: false, message: 'Failed to complete campaign' });
    }
  }

  async getCampaignCustomers(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { id } = req.params;
      const { page = 1, limit = 20 } = req.query;

      const campaign = await prisma.campaign.findFirst({
        where: { id, tenantId: req.user!.tenantId },
      });

      if (!campaign) {
        res.status(404).json({ success: false, message: 'Campaign not found' });
        return;
      }

      const skip = (Number(page) - 1) * Number(limit);
      const take = Number(limit);

      const [campaignCustomers, total] = await Promise.all([
        prisma.campaignCustomer.findMany({
          where: { campaignId: id },
          skip,
          take,
          include: { customer: true },
          orderBy: { priority: 'desc' },
        }),
        prisma.campaignCustomer.count({ where: { campaignId: id } }),
      ]);

      res.json({
        success: true,
        data: {
          customers: campaignCustomers,
          pagination: {
            page: Number(page),
            limit: Number(limit),
            total,
            pages: Math.ceil(total / Number(limit)),
          },
        },
      });
    } catch (error) {
      logger.error('Get campaign customers error:', error);
      res.status(500).json({ success: false, message: 'Failed to fetch campaign customers' });
    }
  }

  async addCustomersToCampaign(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { id } = req.params;
      const { customerIds, priority = 1 } = req.body;

      const campaign = await prisma.campaign.findFirst({
        where: { id, tenantId: req.user!.tenantId },
      });

      if (!campaign) {
        res.status(404).json({ success: false, message: 'Campaign not found' });
        return;
      }

      const campaignCustomersData = customerIds.map((customerId: string) => ({
        campaignId: id,
        customerId,
        priority,
        status: 'pending',
      }));

      const result = await prisma.campaignCustomer.createMany({
        data: campaignCustomersData,
        skipDuplicates: true,
      });

      res.json({
        success: true,
        message: `${result.count} customers added to campaign`,
        data: { count: result.count },
      });
    } catch (error) {
      logger.error('Add customers to campaign error:', error);
      res.status(500).json({ success: false, message: 'Failed to add customers to campaign' });
    }
  }

  async removeCustomersFromCampaign(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { id } = req.params;
      const { customerIds } = req.body;

      const campaign = await prisma.campaign.findFirst({
        where: { id, tenantId: req.user!.tenantId },
      });

      if (!campaign) {
        res.status(404).json({ success: false, message: 'Campaign not found' });
        return;
      }

      const result = await prisma.campaignCustomer.deleteMany({
        where: {
          campaignId: id,
          customerId: { in: customerIds },
        },
      });

      res.json({
        success: true,
        message: `${result.count} customers removed from campaign`,
        data: { count: result.count },
      });
    } catch (error) {
      logger.error('Remove customers from campaign error:', error);
      res.status(500).json({ success: false, message: 'Failed to remove customers from campaign' });
    }
  }

  async getCampaignCalls(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { id } = req.params;
      const { page = 1, limit = 20 } = req.query;

      const campaign = await prisma.campaign.findFirst({
        where: { id, tenantId: req.user!.tenantId },
      });

      if (!campaign) {
        res.status(404).json({ success: false, message: 'Campaign not found' });
        return;
      }

      const skip = (Number(page) - 1) * Number(limit);
      const take = Number(limit);

      const [calls, total] = await Promise.all([
        prisma.call.findMany({
          where: { campaignId: id },
          skip,
          take,
          include: { customer: true, user: true },
          orderBy: { createdAt: 'desc' },
        }),
        prisma.call.count({ where: { campaignId: id } }),
      ]);

      res.json({
        success: true,
        data: {
          calls,
          pagination: {
            page: Number(page),
            limit: Number(limit),
            total,
            pages: Math.ceil(total / Number(limit)),
          },
        },
      });
    } catch (error) {
      logger.error('Get campaign calls error:', error);
      res.status(500).json({ success: false, message: 'Failed to fetch campaign calls' });
    }
  }

  async getCampaignAnalytics(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { id } = req.params;

      const campaign = await prisma.campaign.findFirst({
        where: { id, tenantId: req.user!.tenantId },
        include: { calls: true, customers: true },
      });

      if (!campaign) {
        res.status(404).json({ success: false, message: 'Campaign not found' });
        return;
      }

      const calls = campaign.calls;
      const completedCalls = calls.filter(c => c.status === 'COMPLETED');
      const successfulCalls = completedCalls.filter(c => 
        c.outcome && ['SALE', 'APPOINTMENT', 'INTERESTED'].includes(c.outcome)
      );

      const analytics = {
        totalCustomers: campaign.customers.length,
        totalCalls: calls.length,
        completedCalls: completedCalls.length,
        successfulCalls: successfulCalls.length,
        successRate: completedCalls.length > 0 ? (successfulCalls.length / completedCalls.length) * 100 : 0,
        contactRate: campaign.customers.length > 0 ? (calls.length / campaign.customers.length) * 100 : 0,
        avgCallDuration: completedCalls.reduce((sum, call) => sum + (call.duration || 0), 0) / completedCalls.length || 0,
      };

      res.json({ success: true, data: analytics });
    } catch (error) {
      logger.error('Get campaign analytics error:', error);
      res.status(500).json({ success: false, message: 'Failed to fetch campaign analytics' });
    }
  }

  async getCampaignPerformance(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { id } = req.params;

      const campaign = await prisma.campaign.findFirst({
        where: { id, tenantId: req.user!.tenantId },
        include: { calls: true, customers: true },
      });

      if (!campaign) {
        res.status(404).json({ success: false, message: 'Campaign not found' });
        return;
      }

      const calls = campaign.calls;
      const dailyStats = this.calculateDailyStats(calls);

      const performance = {
        overview: {
          status: campaign.status,
          duration: campaign.startDate && campaign.endDate 
            ? Math.ceil((campaign.endDate.getTime() - campaign.startDate.getTime()) / (1000 * 60 * 60 * 24))
            : null,
          progress: campaign.customers.length > 0 ? (calls.length / campaign.customers.length) * 100 : 0,
        },
        dailyStats,
        trends: {
          callVolume: 'increasing',
          successRate: 'stable',
          efficiency: 'improving',
        },
      };

      res.json({ success: true, data: performance });
    } catch (error) {
      logger.error('Get campaign performance error:', error);
      res.status(500).json({ success: false, message: 'Failed to fetch campaign performance' });
    }
  }

  async cloneCampaign(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { id } = req.params;
      const { name } = req.body;

      const originalCampaign = await prisma.campaign.findFirst({
        where: { id, tenantId: req.user!.tenantId },
        include: { customers: true },
      });

      if (!originalCampaign) {
        res.status(404).json({ success: false, message: 'Campaign not found' });
        return;
      }

      const clonedCampaign = await prisma.campaign.create({
        data: {
          name,
          description: originalCampaign.description,
          type: originalCampaign.type,
          status: 'DRAFT',
          settings: originalCampaign.settings,
          tenantId: req.user!.tenantId,
          userId: req.user!.id,
        },
      });

      // Clone customer associations
      if (originalCampaign.customers.length > 0) {
        const customerData = originalCampaign.customers.map(cc => ({
          campaignId: clonedCampaign.id,
          customerId: cc.customerId,
          priority: cc.priority,
          status: 'pending',
        }));

        await prisma.campaignCustomer.createMany({
          data: customerData,
        });
      }

      res.status(201).json({
        success: true,
        message: 'Campaign cloned successfully',
        data: clonedCampaign,
      });
    } catch (error) {
      logger.error('Clone campaign error:', error);
      res.status(500).json({ success: false, message: 'Failed to clone campaign' });
    }
  }

  private calculateDailyStats(calls: any[]): any[] {
    const dailyStats: Record<string, any> = {};

    calls.forEach(call => {
      const date = call.createdAt.toISOString().split('T')[0];
      if (!dailyStats[date]) {
        dailyStats[date] = {
          date,
          totalCalls: 0,
          completedCalls: 0,
          successfulCalls: 0,
        };
      }

      dailyStats[date].totalCalls++;
      if (call.status === 'COMPLETED') {
        dailyStats[date].completedCalls++;
        if (call.outcome && ['SALE', 'APPOINTMENT', 'INTERESTED'].includes(call.outcome)) {
          dailyStats[date].successfulCalls++;
        }
      }
    });

    return Object.values(dailyStats).map((stats: any) => ({
      ...stats,
      successRate: stats.completedCalls > 0 ? (stats.successfulCalls / stats.completedCalls) * 100 : 0,
    }));
  }
}