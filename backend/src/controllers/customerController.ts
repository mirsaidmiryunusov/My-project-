/**
 * Customer Controller
 * 
 * Handles customer management operations for the GeminiVoiceConnect platform.
 */

import { Response } from 'express';
import { PrismaClient } from '@prisma/client';
import { AuthenticatedRequest } from '../types/auth';
import { logger } from '../utils/logger';

const prisma = new PrismaClient();

export class CustomerController {
  async getCustomers(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { page = 1, limit = 20, search, status } = req.query;
      const skip = (Number(page) - 1) * Number(limit);
      const take = Number(limit);

      const where: any = { tenantId: req.user!.tenantId };
      
      if (search) {
        where.OR = [
          { firstName: { contains: search as string } },
          { lastName: { contains: search as string } },
          { email: { contains: search as string } },
          { phone: { contains: search as string } },
        ];
      }

      if (status) {
        where.isActive = status === 'active';
      }

      const [customers, total] = await Promise.all([
        prisma.customer.findMany({
          where,
          skip,
          take,
          include: { user: true },
          orderBy: { createdAt: 'desc' },
        }),
        prisma.customer.count({ where }),
      ]);

      res.json({
        success: true,
        data: {
          customers,
          pagination: {
            page: Number(page),
            limit: Number(limit),
            total,
            pages: Math.ceil(total / Number(limit)),
          },
        },
      });
    } catch (error) {
      logger.error('Get customers error:', error);
      res.status(500).json({ success: false, message: 'Failed to fetch customers' });
    }
  }

  async getCustomerById(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { id } = req.params;
      
      const customer = await prisma.customer.findFirst({
        where: { id, tenantId: req.user!.tenantId },
        include: { user: true, calls: true },
      });

      if (!customer) {
        res.status(404).json({ success: false, message: 'Customer not found' });
        return;
      }

      res.json({ success: true, data: customer });
    } catch (error) {
      logger.error('Get customer by ID error:', error);
      res.status(500).json({ success: false, message: 'Failed to fetch customer' });
    }
  }

  async createCustomer(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { firstName, lastName, email, phone, address, tags, notes } = req.body;

      const customer = await prisma.customer.create({
        data: {
          firstName,
          lastName,
          email,
          phone,
          address: address ? JSON.stringify(address) : null,
          tags: tags ? tags.join(',') : null,
          notes,
          tenantId: req.user!.tenantId,
          userId: req.user!.id,
          isActive: true,
        },
        include: { user: true },
      });

      res.status(201).json({
        success: true,
        message: 'Customer created successfully',
        data: customer,
      });
    } catch (error) {
      logger.error('Create customer error:', error);
      res.status(500).json({ success: false, message: 'Failed to create customer' });
    }
  }

  async updateCustomer(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { id } = req.params;
      const { firstName, lastName, email, phone, address, tags, notes, isActive } = req.body;

      const customer = await prisma.customer.findFirst({
        where: { id, tenantId: req.user!.tenantId },
      });

      if (!customer) {
        res.status(404).json({ success: false, message: 'Customer not found' });
        return;
      }

      const updateData: any = {};
      if (firstName) updateData.firstName = firstName;
      if (lastName) updateData.lastName = lastName;
      if (email) updateData.email = email;
      if (phone) updateData.phone = phone;
      if (address) updateData.address = JSON.stringify(address);
      if (tags) updateData.tags = tags.join(',');
      if (notes) updateData.notes = notes;
      if (isActive !== undefined) updateData.isActive = isActive;

      const updatedCustomer = await prisma.customer.update({
        where: { id },
        data: updateData,
        include: { user: true },
      });

      res.json({
        success: true,
        message: 'Customer updated successfully',
        data: updatedCustomer,
      });
    } catch (error) {
      logger.error('Update customer error:', error);
      res.status(500).json({ success: false, message: 'Failed to update customer' });
    }
  }

  async deleteCustomer(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { id } = req.params;

      const customer = await prisma.customer.findFirst({
        where: { id, tenantId: req.user!.tenantId },
      });

      if (!customer) {
        res.status(404).json({ success: false, message: 'Customer not found' });
        return;
      }

      await prisma.customer.delete({ where: { id } });

      res.json({ success: true, message: 'Customer deleted successfully' });
    } catch (error) {
      logger.error('Delete customer error:', error);
      res.status(500).json({ success: false, message: 'Failed to delete customer' });
    }
  }

  async getCustomerCalls(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { id } = req.params;
      const { page = 1, limit = 20 } = req.query;

      const customer = await prisma.customer.findFirst({
        where: { id, tenantId: req.user!.tenantId },
      });

      if (!customer) {
        res.status(404).json({ success: false, message: 'Customer not found' });
        return;
      }

      const skip = (Number(page) - 1) * Number(limit);
      const take = Number(limit);

      const [calls, total] = await Promise.all([
        prisma.call.findMany({
          where: { customerId: id },
          skip,
          take,
          include: { user: true, campaign: true },
          orderBy: { createdAt: 'desc' },
        }),
        prisma.call.count({ where: { customerId: id } }),
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
      logger.error('Get customer calls error:', error);
      res.status(500).json({ success: false, message: 'Failed to fetch customer calls' });
    }
  }

  async createCustomerCall(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { id } = req.params;
      const { direction, campaignId } = req.body;

      const customer = await prisma.customer.findFirst({
        where: { id, tenantId: req.user!.tenantId },
      });

      if (!customer) {
        res.status(404).json({ success: false, message: 'Customer not found' });
        return;
      }

      const call = await prisma.call.create({
        data: {
          phoneNumber: customer.phone,
          direction,
          status: 'PENDING',
          tenantId: req.user!.tenantId,
          userId: req.user!.id,
          customerId: id,
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
      logger.error('Create customer call error:', error);
      res.status(500).json({ success: false, message: 'Failed to create call' });
    }
  }

  async getCustomerAnalytics(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { id } = req.params;
      const { period = '30d' } = req.query;

      const customer = await prisma.customer.findFirst({
        where: { id, tenantId: req.user!.tenantId },
      });

      if (!customer) {
        res.status(404).json({ success: false, message: 'Customer not found' });
        return;
      }

      const days = period === '7d' ? 7 : period === '30d' ? 30 : 90;
      const startDate = new Date();
      startDate.setDate(startDate.getDate() - days);

      const calls = await prisma.call.findMany({
        where: {
          customerId: id,
          createdAt: { gte: startDate },
        },
      });

      const completedCalls = calls.filter(c => c.status === 'COMPLETED');
      const successfulCalls = completedCalls.filter(c => 
        c.outcome && ['SALE', 'APPOINTMENT', 'INTERESTED'].includes(c.outcome)
      );

      const analytics = {
        period,
        totalCalls: calls.length,
        completedCalls: completedCalls.length,
        successfulCalls: successfulCalls.length,
        successRate: completedCalls.length > 0 ? (successfulCalls.length / completedCalls.length) * 100 : 0,
        avgCallDuration: completedCalls.reduce((sum, call) => sum + (call.duration || 0), 0) / completedCalls.length || 0,
        lastContact: calls.length > 0 ? calls[0].createdAt : customer.createdAt,
      };

      res.json({ success: true, data: analytics });
    } catch (error) {
      logger.error('Get customer analytics error:', error);
      res.status(500).json({ success: false, message: 'Failed to fetch customer analytics' });
    }
  }

  async importCustomers(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { customers } = req.body;

      const customersData = customers.map((customer: any) => ({
        ...customer,
        tenantId: req.user!.tenantId,
        userId: req.user!.id,
        isActive: true,
      }));

      const result = await prisma.customer.createMany({
        data: customersData,
      });

      res.status(201).json({
        success: true,
        message: `${result.count} customers imported successfully`,
        data: { count: result.count },
      });
    } catch (error) {
      logger.error('Import customers error:', error);
      res.status(500).json({ success: false, message: 'Failed to import customers' });
    }
  }

  async exportCustomers(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { format = 'csv' } = req.query;

      const customers = await prisma.customer.findMany({
        where: { tenantId: req.user!.tenantId },
      });

      res.json({
        success: true,
        message: `Export initiated for ${customers.length} customers in ${format} format`,
        data: {
          exportId: `export_${Date.now()}`,
          format,
          count: customers.length,
        },
      });
    } catch (error) {
      logger.error('Export customers error:', error);
      res.status(500).json({ success: false, message: 'Failed to export customers' });
    }
  }

  async bulkUpdateCustomers(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { customerIds, updates } = req.body;

      const result = await prisma.customer.updateMany({
        where: {
          id: { in: customerIds },
          tenantId: req.user!.tenantId,
        },
        data: updates,
      });

      res.json({
        success: true,
        message: `${result.count} customers updated successfully`,
        data: { count: result.count },
      });
    } catch (error) {
      logger.error('Bulk update customers error:', error);
      res.status(500).json({ success: false, message: 'Failed to bulk update customers' });
    }
  }

  async addCustomerTags(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { id } = req.params;
      const { tags } = req.body;

      const customer = await prisma.customer.findFirst({
        where: { id, tenantId: req.user!.tenantId },
      });

      if (!customer) {
        res.status(404).json({ success: false, message: 'Customer not found' });
        return;
      }

      const existingTags = customer.tags ? customer.tags.split(',') : [];
      const newTags = [...new Set([...existingTags, ...tags])];

      const updatedCustomer = await prisma.customer.update({
        where: { id },
        data: { tags: newTags.join(',') },
      });

      res.json({
        success: true,
        message: 'Tags added successfully',
        data: updatedCustomer,
      });
    } catch (error) {
      logger.error('Add customer tags error:', error);
      res.status(500).json({ success: false, message: 'Failed to add tags' });
    }
  }

  async removeCustomerTags(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { id } = req.params;
      const { tags } = req.body;

      const customer = await prisma.customer.findFirst({
        where: { id, tenantId: req.user!.tenantId },
      });

      if (!customer) {
        res.status(404).json({ success: false, message: 'Customer not found' });
        return;
      }

      const existingTags = customer.tags ? customer.tags.split(',') : [];
      const remainingTags = existingTags.filter(tag => !tags.includes(tag));

      const updatedCustomer = await prisma.customer.update({
        where: { id },
        data: { tags: remainingTags.join(',') },
      });

      res.json({
        success: true,
        message: 'Tags removed successfully',
        data: updatedCustomer,
      });
    } catch (error) {
      logger.error('Remove customer tags error:', error);
      res.status(500).json({ success: false, message: 'Failed to remove tags' });
    }
  }

  async searchCustomers(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { q, page = 1, limit = 20 } = req.query;
      const skip = (Number(page) - 1) * Number(limit);
      const take = Number(limit);

      const where = {
        tenantId: req.user!.tenantId,
        OR: [
          { firstName: { contains: q as string } },
          { lastName: { contains: q as string } },
          { email: { contains: q as string } },
          { phone: { contains: q as string } },
        ],
      };

      const [customers, total] = await Promise.all([
        prisma.customer.findMany({
          where,
          skip,
          take,
          include: { user: true },
          orderBy: { createdAt: 'desc' },
        }),
        prisma.customer.count({ where }),
      ]);

      res.json({
        success: true,
        data: {
          customers,
          pagination: {
            page: Number(page),
            limit: Number(limit),
            total,
            pages: Math.ceil(total / Number(limit)),
          },
        },
      });
    } catch (error) {
      logger.error('Search customers error:', error);
      res.status(500).json({ success: false, message: 'Failed to search customers' });
    }
  }
}