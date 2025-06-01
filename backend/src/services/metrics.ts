/**
 * Metrics Service
 * 
 * System performance monitoring and metrics collection service.
 */

import { PrismaClient } from '@prisma/client';
import { logger } from '../utils/logger';
import os from 'os';

const prisma = new PrismaClient();

export class MetricsService {
  private metricsInterval: NodeJS.Timeout | null = null;
  private isRunning = false;

  /**
   * Start metrics collection
   */
  async start(): Promise<void> {
    if (this.isRunning) {
      logger.warn('Metrics service is already running');
      return;
    }

    this.isRunning = true;
    logger.info('Starting metrics collection service');

    // Collect metrics every 30 seconds
    this.metricsInterval = setInterval(() => {
      this.collectSystemMetrics();
    }, 30000);

    // Collect initial metrics
    await this.collectSystemMetrics();
  }

  /**
   * Stop metrics collection
   */
  async stop(): Promise<void> {
    if (!this.isRunning) {
      return;
    }

    this.isRunning = false;
    
    if (this.metricsInterval) {
      clearInterval(this.metricsInterval);
      this.metricsInterval = null;
    }

    logger.info('Metrics collection service stopped');
  }

  /**
   * Get current system metrics
   */
  async getSystemMetrics(): Promise<any> {
    try {
      const [cpuUsage, memoryUsage, diskUsage] = await Promise.all([
        this.getCPUUsage(),
        this.getMemoryUsage(),
        this.getDiskUsage(),
      ]);

      const networkStats = this.getNetworkStats();
      const processStats = this.getProcessStats();

      return {
        timestamp: new Date().toISOString(),
        system: {
          cpu: cpuUsage,
          memory: memoryUsage,
          disk: diskUsage,
          network: networkStats,
          uptime: os.uptime(),
          loadAverage: os.loadavg(),
        },
        process: processStats,
        application: await this.getApplicationMetrics(),
      };
    } catch (error) {
      logger.error('Failed to get system metrics:', error);
      throw error;
    }
  }

  /**
   * Get application-specific metrics
   */
  async getApplicationMetrics(): Promise<any> {
    try {
      const now = new Date();
      const last24h = new Date(now.getTime() - 24 * 60 * 60 * 1000);

      const [
        totalCalls,
        activeCalls,
        totalUsers,
        activeUsers,
        totalCustomers,
        callsLast24h
      ] = await Promise.all([
        prisma.call.count(),
        prisma.call.count({
          where: { status: { in: ['RINGING', 'ANSWERED'] } }
        }),
        prisma.user.count({ where: { isActive: true } }),
        prisma.user.count({
          where: {
            isActive: true,
            lastLogin: { gte: new Date(now.getTime() - 15 * 60 * 1000) } // Last 15 minutes
          }
        }),
        prisma.customer.count({ where: { isActive: true } }),
        prisma.call.count({
          where: { createdAt: { gte: last24h } }
        })
      ]);

      // Database performance metrics
      const dbMetrics = await this.getDatabaseMetrics();

      return {
        calls: {
          total: totalCalls,
          active: activeCalls,
          last24h: callsLast24h,
          rate: callsLast24h / 24, // Calls per hour
        },
        users: {
          total: totalUsers,
          active: activeUsers,
          utilization: totalUsers > 0 ? (activeUsers / totalUsers) * 100 : 0,
        },
        customers: {
          total: totalCustomers,
        },
        database: dbMetrics,
        performance: {
          responseTime: await this.getAverageResponseTime(),
          throughput: await this.getThroughput(),
          errorRate: await this.getErrorRate(),
        },
      };
    } catch (error) {
      logger.error('Failed to get application metrics:', error);
      throw error;
    }
  }

  /**
   * Collect and store system metrics
   */
  private async collectSystemMetrics(): Promise<void> {
    try {
      const metrics = await this.getSystemMetrics();
      
      // Store key metrics in database
      const metricsToStore = [
        { metric: 'cpu_usage', value: metrics.system.cpu.usage },
        { metric: 'memory_usage', value: metrics.system.memory.usage },
        { metric: 'disk_usage', value: metrics.system.disk.usage },
        { metric: 'active_calls', value: metrics.application.calls.active },
        { metric: 'active_users', value: metrics.application.users.active },
        { metric: 'response_time', value: metrics.application.performance.responseTime },
      ];

      await prisma.systemMetrics.createMany({
        data: metricsToStore.map(m => ({
          metric: m.metric,
          value: m.value,
          timestamp: new Date(),
        })),
      });

      logger.debug('System metrics collected and stored');
    } catch (error) {
      logger.error('Failed to collect system metrics:', error);
    }
  }

  /**
   * Get CPU usage percentage
   */
  private async getCPUUsage(): Promise<any> {
    return new Promise((resolve) => {
      const startUsage = process.cpuUsage();
      const startTime = process.hrtime();

      setTimeout(() => {
        const endUsage = process.cpuUsage(startUsage);
        const endTime = process.hrtime(startTime);

        const totalTime = endTime[0] * 1000000 + endTime[1] / 1000; // microseconds
        const totalUsage = endUsage.user + endUsage.system;
        const usage = (totalUsage / totalTime) * 100;

        resolve({
          usage: Math.round(usage * 100) / 100,
          user: Math.round((endUsage.user / totalTime) * 100 * 100) / 100,
          system: Math.round((endUsage.system / totalTime) * 100 * 100) / 100,
          cores: os.cpus().length,
        });
      }, 100);
    });
  }

  /**
   * Get memory usage information
   */
  private getMemoryUsage(): any {
    const totalMemory = os.totalmem();
    const freeMemory = os.freemem();
    const usedMemory = totalMemory - freeMemory;
    const processMemory = process.memoryUsage();

    return {
      total: totalMemory,
      used: usedMemory,
      free: freeMemory,
      usage: (usedMemory / totalMemory) * 100,
      process: {
        rss: processMemory.rss,
        heapTotal: processMemory.heapTotal,
        heapUsed: processMemory.heapUsed,
        external: processMemory.external,
        arrayBuffers: processMemory.arrayBuffers,
      },
    };
  }

  /**
   * Get disk usage information (mock implementation)
   */
  private getDiskUsage(): any {
    // In a real implementation, you would use a library like 'node-disk-info'
    // For demo purposes, we'll return mock data
    return {
      total: 100 * 1024 * 1024 * 1024, // 100GB
      used: 45 * 1024 * 1024 * 1024,  // 45GB
      free: 55 * 1024 * 1024 * 1024,  // 55GB
      usage: 45,
    };
  }

  /**
   * Get network statistics (mock implementation)
   */
  private getNetworkStats(): any {
    // In a real implementation, you would collect actual network stats
    return {
      bytesReceived: Math.floor(Math.random() * 1000000),
      bytesSent: Math.floor(Math.random() * 1000000),
      packetsReceived: Math.floor(Math.random() * 10000),
      packetsSent: Math.floor(Math.random() * 10000),
      errors: Math.floor(Math.random() * 10),
    };
  }

  /**
   * Get process statistics
   */
  private getProcessStats(): any {
    return {
      pid: process.pid,
      uptime: process.uptime(),
      version: process.version,
      platform: process.platform,
      arch: process.arch,
      nodeVersion: process.versions.node,
      v8Version: process.versions.v8,
    };
  }

  /**
   * Get database performance metrics
   */
  private async getDatabaseMetrics(): Promise<any> {
    try {
      const startTime = Date.now();
      
      // Simple query to test database performance
      await prisma.user.count();
      
      const queryTime = Date.now() - startTime;

      // Get connection pool info (if available)
      const connectionInfo = {
        // These would be actual connection pool metrics in a real implementation
        activeConnections: Math.floor(Math.random() * 10) + 1,
        idleConnections: Math.floor(Math.random() * 5) + 1,
        totalConnections: 10,
      };

      return {
        queryTime,
        connections: connectionInfo,
        status: 'connected',
      };
    } catch (error) {
      return {
        queryTime: -1,
        connections: null,
        status: 'error',
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  /**
   * Get average response time (mock implementation)
   */
  private async getAverageResponseTime(): Promise<number> {
    // In a real implementation, you would track actual response times
    return Math.floor(Math.random() * 100) + 50; // 50-150ms
  }

  /**
   * Get throughput (requests per second)
   */
  private async getThroughput(): Promise<number> {
    // In a real implementation, you would track actual throughput
    return Math.floor(Math.random() * 50) + 10; // 10-60 RPS
  }

  /**
   * Get error rate percentage
   */
  private async getErrorRate(): Promise<number> {
    // In a real implementation, you would track actual error rates
    return Math.random() * 5; // 0-5% error rate
  }

  /**
   * Get historical metrics
   */
  async getHistoricalMetrics(metric: string, period: string): Promise<any[]> {
    try {
      const { startDate, endDate } = this.getPeriodDates(period);

      const metrics = await prisma.systemMetrics.findMany({
        where: {
          metric,
          timestamp: {
            gte: startDate,
            lte: endDate,
          },
        },
        orderBy: { timestamp: 'asc' },
      });

      return metrics.map(m => ({
        timestamp: m.timestamp,
        value: m.value,
        metadata: m.metadata,
      }));
    } catch (error) {
      logger.error('Failed to get historical metrics:', error);
      throw error;
    }
  }

  /**
   * Get period dates
   */
  private getPeriodDates(period: string): { startDate: Date; endDate: Date } {
    const endDate = new Date();
    const startDate = new Date();

    switch (period) {
      case '1h':
        startDate.setHours(startDate.getHours() - 1);
        break;
      case '24h':
        startDate.setDate(startDate.getDate() - 1);
        break;
      case '7d':
        startDate.setDate(startDate.getDate() - 7);
        break;
      case '30d':
        startDate.setDate(startDate.getDate() - 30);
        break;
      default:
        startDate.setDate(startDate.getDate() - 1);
    }

    return { startDate, endDate };
  }
}