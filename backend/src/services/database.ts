/**
 * Database Service
 * 
 * Manages database connections and initialization for the application.
 */

import { PrismaClient } from '@prisma/client';
import { logger } from '../utils/logger';

export class DatabaseService {
  private prisma: PrismaClient;

  constructor() {
    this.prisma = new PrismaClient({
      log: [
        {
          emit: 'event',
          level: 'query',
        },
        {
          emit: 'event',
          level: 'error',
        },
        {
          emit: 'event',
          level: 'info',
        },
        {
          emit: 'event',
          level: 'warn',
        },
      ],
    });

    // Database event logging disabled due to TypeScript compatibility issues
    // Will be re-enabled with proper typing in future updates
  }

  /**
   * Initialize database connection and run migrations
   */
  async initialize(): Promise<void> {
    try {
      // Test database connection
      await this.prisma.$connect();
      logger.info('Database connected successfully');

      // Run any pending migrations in production
      if (process.env.NODE_ENV === 'production') {
        // Note: In production, migrations should be run separately
        // This is just for demo purposes
        logger.info('Database migrations would run here in production');
      }

      // Seed database with initial data if needed
      await this.seedInitialData();

    } catch (error) {
      logger.error('Database initialization failed:', error);
      throw error;
    }
  }

  /**
   * Disconnect from database
   */
  async disconnect(): Promise<void> {
    try {
      await this.prisma.$disconnect();
      logger.info('Database disconnected successfully');
    } catch (error) {
      logger.error('Database disconnection failed:', error);
      throw error;
    }
  }

  /**
   * Get Prisma client instance
   */
  getClient(): PrismaClient {
    return this.prisma;
  }

  /**
   * Seed initial data for demo purposes
   */
  private async seedInitialData(): Promise<void> {
    try {
      // Check if we already have data
      const userCount = await this.prisma.user.count();
      if (userCount > 0) {
        logger.info('Database already contains data, skipping seed');
        return;
      }

      logger.info('Seeding initial data...');

      // Create default tenant
      const defaultTenant = await this.prisma.tenant.create({
        data: {
          name: 'GeminiVoice Demo Organization',
          domain: 'demo.geminivoice.com',
          isActive: true,
          settings: JSON.stringify({
            timezone: 'UTC',
            currency: 'USD',
            features: ['calls', 'sms', 'analytics', 'ai'],
          }),
        },
      });

      // Create demo admin user
      const bcrypt = require('bcryptjs');
      const hashedPassword = await bcrypt.hash('demo123', 12);

      const adminUser = await this.prisma.user.create({
        data: {
          email: 'admin@geminivoice.com',
          password: hashedPassword,
          name: 'Demo Administrator',
          role: 'ADMIN',
          tenantId: defaultTenant.id,
          isActive: true,
          avatar: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=32&h=32&fit=crop&crop=face',
        },
      });

      // Create admin permissions
      const adminPermissions = [
        'calls:read', 'calls:write', 'calls:delete',
        'customers:read', 'customers:write', 'customers:delete',
        'campaigns:read', 'campaigns:write', 'campaigns:delete',
        'analytics:read', 'analytics:write',
        'users:read', 'users:write', 'users:delete',
        'system:read', 'system:write',
        'settings:read', 'settings:write',
      ];

      await this.prisma.userPermission.createMany({
        data: adminPermissions.map(permission => ({
          userId: adminUser.id,
          permission,
        })),
      });

      // Create admin preferences
      await this.prisma.userPreferences.create({
        data: {
          userId: adminUser.id,
          theme: 'system',
          language: 'en',
          timezone: 'UTC',
          emailNotifications: true,
          smsNotifications: false,
          pushNotifications: true,
        },
      });

      // Create demo customers
      const customers = [
        {
          firstName: 'John',
          lastName: 'Smith',
          email: 'john.smith@example.com',
          phone: '+1234567890',
          tenantId: defaultTenant.id,
        },
        {
          firstName: 'Sarah',
          lastName: 'Johnson',
          email: 'sarah.johnson@example.com',
          phone: '+1234567891',
          tenantId: defaultTenant.id,
        },
        {
          firstName: 'Michael',
          lastName: 'Brown',
          email: 'michael.brown@example.com',
          phone: '+1234567892',
          tenantId: defaultTenant.id,
        },
        {
          firstName: 'Emily',
          lastName: 'Davis',
          email: 'emily.davis@example.com',
          phone: '+1234567893',
          tenantId: defaultTenant.id,
        },
        {
          firstName: 'David',
          lastName: 'Wilson',
          email: 'david.wilson@example.com',
          phone: '+1234567894',
          tenantId: defaultTenant.id,
        },
      ];

      await this.prisma.customer.createMany({
        data: customers,
      });

      // Create demo campaign
      const campaign = await this.prisma.campaign.create({
        data: {
          name: 'Q4 Sales Campaign',
          description: 'End of year sales push for existing customers',
          type: 'OUTBOUND',
          status: 'ACTIVE',
          tenantId: defaultTenant.id,
          userId: adminUser.id,
          startDate: new Date(),
          endDate: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000), // 30 days from now
          settings: JSON.stringify({
            maxCallsPerDay: 100,
            callWindow: { start: '09:00', end: '17:00' },
            timezone: 'UTC',
          }),
        },
      });

      // Create demo calls
      const callStatuses = ['COMPLETED', 'COMPLETED', 'COMPLETED', 'NO_ANSWER', 'BUSY'];
      const callOutcomes = ['SALE', 'APPOINTMENT', 'NOT_INTERESTED', null, null];
      const callSentiments = ['POSITIVE', 'POSITIVE', 'NEGATIVE', 'NEUTRAL', 'NEUTRAL'];

      const demoCustomers = await this.prisma.customer.findMany({
        where: { tenantId: defaultTenant.id },
        take: 5,
      });

      for (let i = 0; i < 20; i++) {
        const customer = demoCustomers[i % demoCustomers.length];
        const statusIndex = i % callStatuses.length;
        const callDate = new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000); // Random date in last 7 days

        await this.prisma.call.create({
          data: {
            tenantId: defaultTenant.id,
            userId: adminUser.id,
            customerId: customer.id,
            campaignId: campaign.id,
            phoneNumber: customer.phone,
            direction: 'OUTBOUND',
            status: callStatuses[statusIndex] as any,
            duration: callStatuses[statusIndex] === 'COMPLETED' ? Math.floor(Math.random() * 600) + 60 : null,
            outcome: callOutcomes[statusIndex],
            sentiment: callSentiments[statusIndex],
            notes: callStatuses[statusIndex] === 'COMPLETED' ? 'Call completed successfully' : 'Customer not available',
            startedAt: callDate,
            endedAt: callStatuses[statusIndex] === 'COMPLETED' ? new Date(callDate.getTime() + Math.random() * 600000) : null,
            createdAt: callDate,
          },
        });
      }

      // Create analytics data
      const analyticsData = [];
      for (let i = 0; i < 30; i++) {
        const date = new Date();
        date.setDate(date.getDate() - i);

        analyticsData.push(
          {
            tenantId: defaultTenant.id,
            date,
            metric: 'calls_total',
            value: Math.floor(Math.random() * 50) + 20,
          },
          {
            tenantId: defaultTenant.id,
            date,
            metric: 'calls_successful',
            value: Math.floor(Math.random() * 30) + 10,
          },
          {
            tenantId: defaultTenant.id,
            date,
            metric: 'revenue',
            value: Math.floor(Math.random() * 5000) + 1000,
          }
        );
      }

      await this.prisma.analytics.createMany({
        data: analyticsData,
      });

      logger.info('Initial data seeded successfully');
    } catch (error) {
      logger.error('Failed to seed initial data:', error);
      // Don't throw error, as this is not critical for app startup
    }
  }
}