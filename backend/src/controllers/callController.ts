/**
 * Call Controller
 * 
 * Handles call management operations for the GeminiVoiceConnect platform.
 */

import { Response } from 'express';
import { PrismaClient } from '@prisma/client';
import { AuthenticatedRequest } from '../types/auth';
import { logger } from '../utils/logger';

const prisma = new PrismaClient();

export class CallController {
  async getCalls(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { page = 1, limit = 20, status, direction } = req.query;
      const skip = (Number(page) - 1) * Number(limit);
      const take = Number(limit);

      const where: any = { tenantId: req.user!.tenantId };
      if (status) where.status = status;
      if (direction) where.direction = direction;

      const [calls, total] = await Promise.all([
        prisma.call.findMany({
          where,
          skip,
          take,
          include: { customer: true, user: true, campaign: true },
          orderBy: { createdAt: 'desc' },
        }),
        prisma.call.count({ where }),
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
      logger.error('Get calls error:', error);
      res.status(500).json({ success: false, message: 'Failed to fetch calls' });
    }
  }

  async getCallById(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { id } = req.params;
      const call = await prisma.call.findFirst({
        where: { id, tenantId: req.user!.tenantId },
        include: { customer: true, user: true, campaign: true },
      });

      if (!call) {
        res.status(404).json({ success: false, message: 'Call not found' });
        return;
      }

      res.json({ success: true, data: call });
    } catch (error) {
      logger.error('Get call by ID error:', error);
      res.status(500).json({ success: false, message: 'Failed to fetch call' });
    }
  }

  async createCall(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { phoneNumber, direction, customerId, campaignId } = req.body;

      const call = await prisma.call.create({
        data: {
          phoneNumber,
          direction,
          status: 'PENDING',
          tenantId: req.user!.tenantId,
          userId: req.user!.id,
          customerId,
          campaignId,
        },
        include: { customer: true, user: true, campaign: true },
      });

      res.status(201).json({
        success: true,
        message: 'Call created successfully',
        data: call,
      });
    } catch (error) {
      logger.error('Create call error:', error);
      res.status(500).json({ success: false, message: 'Failed to create call' });
    }
  }

  async updateCall(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { id } = req.params;
      const { status, outcome, notes, sentiment, duration } = req.body;

      const call = await prisma.call.findFirst({
        where: { id, tenantId: req.user!.tenantId },
      });

      if (!call) {
        res.status(404).json({ success: false, message: 'Call not found' });
        return;
      }

      const updateData: any = {};
      if (status) updateData.status = status;
      if (outcome) updateData.outcome = outcome;
      if (notes) updateData.notes = notes;
      if (sentiment) updateData.sentiment = sentiment;
      if (duration !== undefined) updateData.duration = duration;

      const updatedCall = await prisma.call.update({
        where: { id },
        data: updateData,
        include: { customer: true, user: true, campaign: true },
      });

      res.json({
        success: true,
        message: 'Call updated successfully',
        data: updatedCall,
      });
    } catch (error) {
      logger.error('Update call error:', error);
      res.status(500).json({ success: false, message: 'Failed to update call' });
    }
  }

  async deleteCall(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { id } = req.params;

      const call = await prisma.call.findFirst({
        where: { id, tenantId: req.user!.tenantId },
      });

      if (!call) {
        res.status(404).json({ success: false, message: 'Call not found' });
        return;
      }

      await prisma.call.delete({ where: { id } });

      res.json({ success: true, message: 'Call deleted successfully' });
    } catch (error) {
      logger.error('Delete call error:', error);
      res.status(500).json({ success: false, message: 'Failed to delete call' });
    }
  }

  async startCall(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { id } = req.params;

      const call = await prisma.call.update({
        where: { id },
        data: {
          status: 'RINGING',
          startedAt: new Date(),
        },
        include: { customer: true, user: true, campaign: true },
      });

      res.json({
        success: true,
        message: 'Call started successfully',
        data: call,
      });
    } catch (error) {
      logger.error('Start call error:', error);
      res.status(500).json({ success: false, message: 'Failed to start call' });
    }
  }

  async endCall(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { id } = req.params;
      const { outcome, notes, sentiment } = req.body;

      const call = await prisma.call.findFirst({
        where: { id, tenantId: req.user!.tenantId },
      });

      if (!call) {
        res.status(404).json({ success: false, message: 'Call not found' });
        return;
      }

      const duration = call.startedAt 
        ? Math.floor((Date.now() - call.startedAt.getTime()) / 1000)
        : null;

      const updatedCall = await prisma.call.update({
        where: { id },
        data: {
          status: 'COMPLETED',
          endedAt: new Date(),
          duration,
          outcome,
          notes,
          sentiment,
        },
        include: { customer: true, user: true, campaign: true },
      });

      res.json({
        success: true,
        message: 'Call ended successfully',
        data: updatedCall,
      });
    } catch (error) {
      logger.error('End call error:', error);
      res.status(500).json({ success: false, message: 'Failed to end call' });
    }
  }

  async getLiveCalls(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const calls = await prisma.call.findMany({
        where: {
          tenantId: req.user!.tenantId,
          status: { in: ['RINGING', 'ANSWERED'] },
        },
        include: { customer: true, user: true, campaign: true },
        orderBy: { startedAt: 'desc' },
      });

      res.json({ success: true, data: calls });
    } catch (error) {
      logger.error('Get live calls error:', error);
      res.status(500).json({ success: false, message: 'Failed to fetch live calls' });
    }
  }

  async getCallStats(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { period = '24h' } = req.query;
      const hours = period === '1h' ? 1 : period === '24h' ? 24 : period === '7d' ? 168 : 720;
      const startDate = new Date(Date.now() - hours * 60 * 60 * 1000);

      const [total, completed, successful] = await Promise.all([
        prisma.call.count({
          where: { tenantId: req.user!.tenantId, createdAt: { gte: startDate } },
        }),
        prisma.call.count({
          where: { tenantId: req.user!.tenantId, status: 'COMPLETED', createdAt: { gte: startDate } },
        }),
        prisma.call.count({
          where: {
            tenantId: req.user!.tenantId,
            status: 'COMPLETED',
            outcome: { in: ['SALE', 'APPOINTMENT', 'INTERESTED'] },
            createdAt: { gte: startDate },
          },
        }),
      ]);

      res.json({
        success: true,
        data: {
          total,
          completed,
          successful,
          successRate: completed > 0 ? (successful / completed) * 100 : 0,
          period,
        },
      });
    } catch (error) {
      logger.error('Get call stats error:', error);
      res.status(500).json({ success: false, message: 'Failed to fetch call stats' });
    }
  }

  async createBulkCalls(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { calls } = req.body;

      const callsData = calls.map((call: any) => ({
        ...call,
        status: 'PENDING',
        tenantId: req.user!.tenantId,
        userId: req.user!.id,
      }));

      const createdCalls = await prisma.call.createMany({
        data: callsData,
      });

      res.status(201).json({
        success: true,
        message: `${createdCalls.count} calls created successfully`,
        data: { count: createdCalls.count },
      });
    } catch (error) {
      logger.error('Create bulk calls error:', error);
      res.status(500).json({ success: false, message: 'Failed to create bulk calls' });
    }
  }

  async getCallRecording(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { id } = req.params;
      
      const call = await prisma.call.findFirst({
        where: { id, tenantId: req.user!.tenantId },
      });

      if (!call) {
        res.status(404).json({ success: false, message: 'Call not found' });
        return;
      }

      res.json({
        success: true,
        data: {
          recording: call.recording || null,
          message: call.recording ? 'Recording available' : 'No recording available',
        },
      });
    } catch (error) {
      logger.error('Get call recording error:', error);
      res.status(500).json({ success: false, message: 'Failed to fetch call recording' });
    }
  }

  async getCallTranscript(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { id } = req.params;
      
      const call = await prisma.call.findFirst({
        where: { id, tenantId: req.user!.tenantId },
      });

      if (!call) {
        res.status(404).json({ success: false, message: 'Call not found' });
        return;
      }

      res.json({
        success: true,
        data: {
          transcript: call.transcript || null,
          message: call.transcript ? 'Transcript available' : 'No transcript available',
        },
      });
    } catch (error) {
      logger.error('Get call transcript error:', error);
      res.status(500).json({ success: false, message: 'Failed to fetch call transcript' });
    }
  }

  async addCallNotes(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { id } = req.params;
      const { notes } = req.body;

      const call = await prisma.call.findFirst({
        where: { id, tenantId: req.user!.tenantId },
      });

      if (!call) {
        res.status(404).json({ success: false, message: 'Call not found' });
        return;
      }

      const updatedCall = await prisma.call.update({
        where: { id },
        data: { notes },
      });

      res.json({
        success: true,
        message: 'Notes added successfully',
        data: updatedCall,
      });
    } catch (error) {
      logger.error('Add call notes error:', error);
      res.status(500).json({ success: false, message: 'Failed to add call notes' });
    }
  }
}