/**
 * Analytics Service
 * 
 * Provides analytics data processing and calculations for dashboard metrics.
 */

import { PrismaClient } from '@prisma/client';
import { logger } from '../utils/logger';

const prisma = new PrismaClient();

export class AnalyticsService {
  /**
   * Get analytics data for specified period
   */
  async getAnalytics(tenantId: string, period: string, metrics?: string): Promise<any> {
    try {
      const { startDate, endDate } = this.getPeriodDates(period);
      const requestedMetrics = metrics ? metrics.split(',') : ['calls', 'revenue', 'success_rate'];

      const analyticsData: any = {
        period,
        startDate,
        endDate,
        metrics: {},
      };

      // Get call analytics
      if (requestedMetrics.includes('calls')) {
        analyticsData.metrics.calls = await this.getCallAnalytics(tenantId, startDate, endDate);
      }

      // Get revenue analytics
      if (requestedMetrics.includes('revenue')) {
        analyticsData.metrics.revenue = await this.getRevenueAnalytics(tenantId, startDate, endDate);
      }

      // Get success rate analytics
      if (requestedMetrics.includes('success_rate')) {
        analyticsData.metrics.successRate = await this.getSuccessRateAnalytics(tenantId, startDate, endDate);
      }

      // Get customer analytics
      if (requestedMetrics.includes('customers')) {
        analyticsData.metrics.customers = await this.getCustomerAnalytics(tenantId, startDate, endDate);
      }

      // Get agent performance
      if (requestedMetrics.includes('agents')) {
        analyticsData.metrics.agents = await this.getAgentAnalytics(tenantId, startDate, endDate);
      }

      return analyticsData;
    } catch (error) {
      logger.error('Analytics service error:', error);
      throw error;
    }
  }

  /**
   * Get call statistics for specified period
   */
  async getCallStatistics(tenantId: string, period: string): Promise<any> {
    try {
      const { startDate, endDate } = this.getPeriodDates(period);

      const [
        totalCalls,
        completedCalls,
        successfulCalls,
        avgDuration,
        callsByStatus,
        callsByOutcome,
        hourlyDistribution
      ] = await Promise.all([
        // Total calls
        prisma.call.count({
          where: {
            tenantId,
            createdAt: { gte: startDate, lte: endDate },
          },
        }),

        // Completed calls
        prisma.call.count({
          where: {
            tenantId,
            status: 'COMPLETED',
            createdAt: { gte: startDate, lte: endDate },
          },
        }),

        // Successful calls
        prisma.call.count({
          where: {
            tenantId,
            status: 'COMPLETED',
            outcome: { in: ['SALE', 'APPOINTMENT', 'INTERESTED'] },
            createdAt: { gte: startDate, lte: endDate },
          },
        }),

        // Average duration
        prisma.call.aggregate({
          where: {
            tenantId,
            status: 'COMPLETED',
            duration: { not: null },
            createdAt: { gte: startDate, lte: endDate },
          },
          _avg: { duration: true },
        }),

        // Calls by status
        prisma.call.groupBy({
          by: ['status'],
          where: {
            tenantId,
            createdAt: { gte: startDate, lte: endDate },
          },
          _count: { status: true },
        }),

        // Calls by outcome
        prisma.call.groupBy({
          by: ['outcome'],
          where: {
            tenantId,
            status: 'COMPLETED',
            outcome: { not: null },
            createdAt: { gte: startDate, lte: endDate },
          },
          _count: { outcome: true },
        }),

        // Hourly distribution
        this.getHourlyCallDistribution(tenantId, startDate, endDate),
      ]);

      const successRate = completedCalls > 0 ? (successfulCalls / completedCalls) * 100 : 0;
      const completionRate = totalCalls > 0 ? (completedCalls / totalCalls) * 100 : 0;

      return {
        summary: {
          totalCalls,
          completedCalls,
          successfulCalls,
          successRate: Math.round(successRate * 100) / 100,
          completionRate: Math.round(completionRate * 100) / 100,
          avgDuration: Math.round(avgDuration._avg.duration || 0),
        },
        distribution: {
          byStatus: callsByStatus.map(item => ({
            status: item.status,
            count: item._count.status,
            percentage: Math.round((item._count.status / totalCalls) * 100 * 100) / 100,
          })),
          byOutcome: callsByOutcome.map(item => ({
            outcome: item.outcome,
            count: item._count.outcome,
            percentage: Math.round((item._count.outcome / completedCalls) * 100 * 100) / 100,
          })),
          byHour: hourlyDistribution,
        },
      };
    } catch (error) {
      logger.error('Call statistics error:', error);
      throw error;
    }
  }

  /**
   * Get sentiment analysis data
   */
  async getSentimentAnalysis(tenantId: string, period: string): Promise<any> {
    try {
      const { startDate, endDate } = this.getPeriodDates(period);

      const sentimentData = await prisma.call.groupBy({
        by: ['sentiment'],
        where: {
          tenantId,
          sentiment: { not: null },
          createdAt: { gte: startDate, lte: endDate },
        },
        _count: { sentiment: true },
      });

      const totalCalls = sentimentData.reduce((sum, item) => sum + item._count.sentiment, 0);

      const sentimentDistribution = sentimentData.map(item => ({
        sentiment: item.sentiment,
        count: item._count.sentiment,
        percentage: Math.round((item._count.sentiment / totalCalls) * 100 * 100) / 100,
      }));

      // Generate sentiment trend over time
      const sentimentTrend = await this.getSentimentTrend(tenantId, startDate, endDate);

      return {
        distribution: sentimentDistribution,
        trend: sentimentTrend,
        summary: {
          totalAnalyzed: totalCalls,
          positiveRate: sentimentDistribution.find(s => s.sentiment === 'POSITIVE')?.percentage || 0,
          negativeRate: sentimentDistribution.find(s => s.sentiment === 'NEGATIVE')?.percentage || 0,
          neutralRate: sentimentDistribution.find(s => s.sentiment === 'NEUTRAL')?.percentage || 0,
        },
      };
    } catch (error) {
      logger.error('Sentiment analysis error:', error);
      throw error;
    }
  }

  /**
   * Get call analytics for period
   */
  private async getCallAnalytics(tenantId: string, startDate: Date, endDate: Date): Promise<any> {
    const callData = await prisma.call.findMany({
      where: {
        tenantId,
        createdAt: { gte: startDate, lte: endDate },
      },
      select: {
        createdAt: true,
        status: true,
        duration: true,
        direction: true,
      },
    });

    // Group by day
    const dailyData = this.groupByDay(callData, startDate, endDate);

    return {
      total: callData.length,
      dailyData,
      byDirection: {
        inbound: callData.filter(c => c.direction === 'INBOUND').length,
        outbound: callData.filter(c => c.direction === 'OUTBOUND').length,
      },
    };
  }

  /**
   * Get revenue analytics for period
   */
  private async getRevenueAnalytics(tenantId: string, startDate: Date, endDate: Date): Promise<any> {
    // Mock revenue calculation based on successful calls
    const successfulCalls = await prisma.call.findMany({
      where: {
        tenantId,
        status: 'COMPLETED',
        outcome: { in: ['SALE', 'APPOINTMENT'] },
        createdAt: { gte: startDate, lte: endDate },
      },
      select: {
        createdAt: true,
        outcome: true,
      },
    });

    const avgDealValue = 250; // Mock average deal value
    const totalRevenue = successfulCalls.length * avgDealValue;

    // Group by day
    const dailyRevenue = this.groupByDay(successfulCalls, startDate, endDate, (items) => 
      items.length * avgDealValue
    );

    return {
      total: totalRevenue,
      avgDealValue,
      dailyData: dailyRevenue,
      forecast: totalRevenue * 1.15, // 15% growth forecast
    };
  }

  /**
   * Get success rate analytics
   */
  private async getSuccessRateAnalytics(tenantId: string, startDate: Date, endDate: Date): Promise<any> {
    const calls = await prisma.call.findMany({
      where: {
        tenantId,
        status: 'COMPLETED',
        createdAt: { gte: startDate, lte: endDate },
      },
      select: {
        createdAt: true,
        outcome: true,
      },
    });

    const successfulCalls = calls.filter(c => 
      c.outcome && ['SALE', 'APPOINTMENT', 'INTERESTED'].includes(c.outcome)
    );

    const successRate = calls.length > 0 ? (successfulCalls.length / calls.length) * 100 : 0;

    // Daily success rate
    const dailySuccessRate = this.groupByDay(calls, startDate, endDate, (items) => {
      const successful = items.filter(c => 
        c.outcome && ['SALE', 'APPOINTMENT', 'INTERESTED'].includes(c.outcome)
      );
      return items.length > 0 ? (successful.length / items.length) * 100 : 0;
    });

    return {
      overall: Math.round(successRate * 100) / 100,
      dailyData: dailySuccessRate,
      trend: this.calculateTrend(dailySuccessRate),
    };
  }

  /**
   * Get customer analytics
   */
  private async getCustomerAnalytics(tenantId: string, startDate: Date, endDate: Date): Promise<any> {
    const [newCustomers, totalCustomers, activeCustomers] = await Promise.all([
      prisma.customer.count({
        where: {
          tenantId,
          createdAt: { gte: startDate, lte: endDate },
        },
      }),
      prisma.customer.count({
        where: { tenantId, isActive: true },
      }),
      prisma.customer.count({
        where: {
          tenantId,
          isActive: true,
          calls: {
            some: {
              createdAt: { gte: startDate, lte: endDate },
            },
          },
        },
      }),
    ]);

    return {
      new: newCustomers,
      total: totalCustomers,
      active: activeCustomers,
      engagementRate: totalCustomers > 0 ? (activeCustomers / totalCustomers) * 100 : 0,
    };
  }

  /**
   * Get agent analytics
   */
  private async getAgentAnalytics(tenantId: string, startDate: Date, endDate: Date): Promise<any> {
    const agentPerformance = await prisma.user.findMany({
      where: {
        tenantId,
        role: { in: ['AGENT', 'OPERATOR'] },
        isActive: true,
      },
      include: {
        calls: {
          where: {
            createdAt: { gte: startDate, lte: endDate },
          },
        },
      },
    });

    const agentStats = agentPerformance.map(agent => {
      const calls = agent.calls;
      const completedCalls = calls.filter(c => c.status === 'COMPLETED');
      const successfulCalls = completedCalls.filter(c => 
        c.outcome && ['SALE', 'APPOINTMENT', 'INTERESTED'].includes(c.outcome)
      );

      return {
        agentId: agent.id,
        name: agent.name,
        totalCalls: calls.length,
        completedCalls: completedCalls.length,
        successfulCalls: successfulCalls.length,
        successRate: completedCalls.length > 0 ? (successfulCalls.length / completedCalls.length) * 100 : 0,
      };
    });

    return {
      agents: agentStats,
      summary: {
        totalAgents: agentStats.length,
        avgSuccessRate: agentStats.reduce((sum, a) => sum + a.successRate, 0) / agentStats.length || 0,
        topPerformer: agentStats.reduce((top, current) => 
          current.successRate > top.successRate ? current : top, agentStats[0]
        ),
      },
    };
  }

  /**
   * Get hourly call distribution
   */
  private async getHourlyCallDistribution(tenantId: string, startDate: Date, endDate: Date): Promise<any[]> {
    const calls = await prisma.call.findMany({
      where: {
        tenantId,
        createdAt: { gte: startDate, lte: endDate },
      },
      select: {
        createdAt: true,
      },
    });

    const hourlyData = Array.from({ length: 24 }, (_, hour) => ({
      hour,
      count: 0,
    }));

    calls.forEach(call => {
      const hour = call.createdAt.getHours();
      hourlyData[hour].count++;
    });

    return hourlyData;
  }

  /**
   * Get sentiment trend over time
   */
  private async getSentimentTrend(tenantId: string, startDate: Date, endDate: Date): Promise<any[]> {
    const calls = await prisma.call.findMany({
      where: {
        tenantId,
        sentiment: { not: null },
        createdAt: { gte: startDate, lte: endDate },
      },
      select: {
        createdAt: true,
        sentiment: true,
      },
    });

    return this.groupByDay(calls, startDate, endDate, (items) => {
      const sentiments = { POSITIVE: 0, NEGATIVE: 0, NEUTRAL: 0 };
      items.forEach(item => {
        if (item.sentiment) {
          sentiments[item.sentiment as keyof typeof sentiments]++;
        }
      });
      
      const total = items.length;
      return {
        positive: total > 0 ? (sentiments.POSITIVE / total) * 100 : 0,
        negative: total > 0 ? (sentiments.NEGATIVE / total) * 100 : 0,
        neutral: total > 0 ? (sentiments.NEUTRAL / total) * 100 : 0,
      };
    });
  }

  /**
   * Group data by day
   */
  private groupByDay(data: any[], startDate: Date, endDate: Date, aggregator?: (items: any[]) => any): any[] {
    const days = Math.ceil((endDate.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24));
    const result = [];

    for (let i = 0; i < days; i++) {
      const date = new Date(startDate);
      date.setDate(date.getDate() + i);
      
      const dayData = data.filter(item => {
        const itemDate = new Date(item.createdAt);
        return itemDate.toDateString() === date.toDateString();
      });

      result.push({
        date: date.toISOString().split('T')[0],
        value: aggregator ? aggregator(dayData) : dayData.length,
      });
    }

    return result;
  }

  /**
   * Calculate trend from daily data
   */
  private calculateTrend(dailyData: any[]): string {
    if (dailyData.length < 2) return 'stable';
    
    const recent = dailyData.slice(-3).reduce((sum, d) => sum + d.value, 0) / 3;
    const previous = dailyData.slice(-6, -3).reduce((sum, d) => sum + d.value, 0) / 3;
    
    if (recent > previous * 1.05) return 'increasing';
    if (recent < previous * 0.95) return 'decreasing';
    return 'stable';
  }

  /**
   * Get period dates based on period string
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
      case '90d':
        startDate.setDate(startDate.getDate() - 90);
        break;
      default:
        startDate.setDate(startDate.getDate() - 7);
    }

    return { startDate, endDate };
  }
}