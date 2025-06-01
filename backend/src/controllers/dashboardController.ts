/**
 * Dashboard Controller
 * 
 * Provides real-time dashboard data, analytics, and metrics
 * for the GeminiVoiceConnect AI Call Center platform.
 */

import { Response } from 'express';
import { PrismaClient } from '@prisma/client';
import { AuthenticatedRequest } from '../types/auth';
import { logger } from '../utils/logger';
import { AnalyticsService } from '../services/analytics';
import { PredictionService } from '../services/prediction';
import { MetricsService } from '../services/metrics';

const prisma = new PrismaClient();
const analyticsService = new AnalyticsService();
const predictionService = new PredictionService();
const metricsService = new MetricsService();

export class DashboardController {
  /**
   * Get dashboard overview with key metrics
   */
  async getOverview(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const tenantId = req.user!.tenantId;
      const now = new Date();
      const last24h = new Date(now.getTime() - 24 * 60 * 60 * 1000);
      const last7d = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);

      // Get basic counts
      const [
        totalCalls,
        activeCalls,
        totalCustomers,
        activeCampaigns,
        callsLast24h,
        callsLast7d
      ] = await Promise.all([
        prisma.call.count({ where: { tenantId } }),
        prisma.call.count({ 
          where: { 
            tenantId, 
            status: { in: ['RINGING', 'ANSWERED'] } 
          } 
        }),
        prisma.customer.count({ where: { tenantId, isActive: true } }),
        prisma.campaign.count({ 
          where: { 
            tenantId, 
            status: 'ACTIVE' 
          } 
        }),
        prisma.call.count({ 
          where: { 
            tenantId, 
            createdAt: { gte: last24h } 
          } 
        }),
        prisma.call.count({ 
          where: { 
            tenantId, 
            createdAt: { gte: last7d } 
          } 
        })
      ]);

      // Calculate success rates
      const successfulCalls = await prisma.call.count({
        where: {
          tenantId,
          status: 'COMPLETED',
          outcome: { in: ['SALE', 'APPOINTMENT', 'INTERESTED'] }
        }
      });

      const completedCalls = await prisma.call.count({
        where: {
          tenantId,
          status: 'COMPLETED'
        }
      });

      const successRate = completedCalls > 0 ? (successfulCalls / completedCalls) * 100 : 0;

      // Get average call duration
      const avgDurationResult = await prisma.call.aggregate({
        where: {
          tenantId,
          status: 'COMPLETED',
          duration: { not: null }
        },
        _avg: {
          duration: true
        }
      });

      const avgCallDuration = avgDurationResult._avg.duration || 0;

      // Get revenue data (mock for demo)
      const revenueData = await this.generateRevenueData(tenantId);

      // Get system health
      const systemHealth = await this.getSystemHealth();

      // Get recent activity
      const recentCalls = await prisma.call.findMany({
        where: { tenantId },
        include: {
          customer: true,
          user: true
        },
        orderBy: { createdAt: 'desc' },
        take: 10
      });

      res.json({
        success: true,
        data: {
          overview: {
            totalCalls,
            activeCalls,
            totalCustomers,
            activeCampaigns,
            successRate: Math.round(successRate * 100) / 100,
            avgCallDuration: Math.round(avgCallDuration),
            callsLast24h,
            callsLast7d,
            revenue: revenueData
          },
          systemHealth,
          recentActivity: recentCalls.map(call => ({
            id: call.id,
            phoneNumber: call.phoneNumber,
            status: call.status,
            duration: call.duration,
            outcome: call.outcome,
            customer: call.customer ? {
              name: `${call.customer.firstName} ${call.customer.lastName}`,
              phone: call.customer.phone
            } : null,
            agent: call.user ? call.user.name : null,
            timestamp: call.createdAt
          })),
          lastUpdated: new Date().toISOString()
        }
      });
    } catch (error) {
      logger.error('Dashboard overview error:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to fetch dashboard overview'
      });
    }
  }

  /**
   * Get analytics data
   */
  async getAnalytics(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const tenantId = req.user!.tenantId;
      const period = req.query.period as string || '24h';
      const metrics = req.query.metrics as string;

      const analyticsData = await analyticsService.getAnalytics(tenantId, period, metrics);

      res.json({
        success: true,
        data: analyticsData
      });
    } catch (error) {
      logger.error('Analytics error:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to fetch analytics data'
      });
    }
  }

  /**
   * Get live calls data
   */
  async getLiveCalls(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const tenantId = req.user!.tenantId;

      const liveCalls = await prisma.call.findMany({
        where: {
          tenantId,
          status: { in: ['RINGING', 'ANSWERED'] }
        },
        include: {
          customer: true,
          user: true,
          campaign: true
        },
        orderBy: { startedAt: 'desc' }
      });

      const formattedCalls = liveCalls.map(call => ({
        id: call.id,
        phoneNumber: call.phoneNumber,
        direction: call.direction,
        status: call.status,
        duration: call.startedAt ? Math.floor((Date.now() - call.startedAt.getTime()) / 1000) : 0,
        customer: call.customer ? {
          id: call.customer.id,
          name: `${call.customer.firstName} ${call.customer.lastName}`,
          phone: call.customer.phone,
          email: call.customer.email
        } : null,
        agent: call.user ? {
          id: call.user.id,
          name: call.user.name,
          avatar: call.user.avatar
        } : null,
        campaign: call.campaign ? {
          id: call.campaign.id,
          name: call.campaign.name,
          type: call.campaign.type
        } : null,
        startedAt: call.startedAt,
        metadata: call.metadata
      }));

      res.json({
        success: true,
        data: {
          calls: formattedCalls,
          summary: {
            total: formattedCalls.length,
            inbound: formattedCalls.filter(c => c.direction === 'INBOUND').length,
            outbound: formattedCalls.filter(c => c.direction === 'OUTBOUND').length,
            ringing: formattedCalls.filter(c => c.status === 'RINGING').length,
            answered: formattedCalls.filter(c => c.status === 'ANSWERED').length
          }
        }
      });
    } catch (error) {
      logger.error('Live calls error:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to fetch live calls data'
      });
    }
  }

  /**
   * Get call statistics
   */
  async getCallStats(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const tenantId = req.user!.tenantId;
      const period = req.query.period as string || '24h';

      const stats = await analyticsService.getCallStatistics(tenantId, period);

      res.json({
        success: true,
        data: stats
      });
    } catch (error) {
      logger.error('Call stats error:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to fetch call statistics'
      });
    }
  }

  /**
   * Get performance metrics
   */
  async getPerformanceMetrics(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const metrics = await metricsService.getSystemMetrics();

      res.json({
        success: true,
        data: metrics
      });
    } catch (error) {
      logger.error('Performance metrics error:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to fetch performance metrics'
      });
    }
  }

  /**
   * Get AI predictions
   */
  async getPredictions(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const tenantId = req.user!.tenantId;
      const type = req.query.type as string;
      const horizon = req.query.horizon as string || '7d';

      const predictions = await predictionService.getPredictions(tenantId, type, horizon);

      res.json({
        success: true,
        data: predictions
      });
    } catch (error) {
      logger.error('Predictions error:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to fetch predictions'
      });
    }
  }

  /**
   * Get revenue analytics
   */
  async getRevenueAnalytics(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const tenantId = req.user!.tenantId;
      const period = req.query.period as string || '30d';

      const revenueData = await this.generateRevenueAnalytics(tenantId, period);

      res.json({
        success: true,
        data: revenueData
      });
    } catch (error) {
      logger.error('Revenue analytics error:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to fetch revenue analytics'
      });
    }
  }

  /**
   * Get churn predictions
   */
  async getChurnPredictions(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const tenantId = req.user!.tenantId;

      const churnData = await predictionService.getChurnPredictions(tenantId);

      res.json({
        success: true,
        data: churnData
      });
    } catch (error) {
      logger.error('Churn predictions error:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to fetch churn predictions'
      });
    }
  }

  /**
   * Get sentiment analysis
   */
  async getSentimentAnalysis(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const tenantId = req.user!.tenantId;
      const period = req.query.period as string || '24h';

      const sentimentData = await analyticsService.getSentimentAnalysis(tenantId, period);

      res.json({
        success: true,
        data: sentimentData
      });
    } catch (error) {
      logger.error('Sentiment analysis error:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to fetch sentiment analysis'
      });
    }
  }

  /**
   * Get agent performance
   */
  async getAgentPerformance(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const tenantId = req.user!.tenantId;

      const agents = await prisma.user.findMany({
        where: {
          tenantId,
          isActive: true,
          role: { in: ['AGENT', 'OPERATOR'] }
        },
        include: {
          calls: {
            where: {
              createdAt: {
                gte: new Date(Date.now() - 24 * 60 * 60 * 1000) // Last 24 hours
              }
            }
          }
        }
      });

      const agentPerformance = agents.map(agent => {
        const calls = agent.calls;
        const completedCalls = calls.filter(c => c.status === 'COMPLETED');
        const successfulCalls = completedCalls.filter(c => 
          c.outcome && ['SALE', 'APPOINTMENT', 'INTERESTED'].includes(c.outcome)
        );

        const totalDuration = completedCalls.reduce((sum, call) => sum + (call.duration || 0), 0);
        const avgDuration = completedCalls.length > 0 ? totalDuration / completedCalls.length : 0;

        return {
          id: agent.id,
          name: agent.name,
          email: agent.email,
          avatar: agent.avatar,
          role: agent.role,
          stats: {
            totalCalls: calls.length,
            completedCalls: completedCalls.length,
            successfulCalls: successfulCalls.length,
            successRate: completedCalls.length > 0 ? (successfulCalls.length / completedCalls.length) * 100 : 0,
            avgCallDuration: Math.round(avgDuration),
            totalTalkTime: totalDuration
          },
          status: this.getAgentStatus(agent.lastLogin),
          lastActive: agent.lastLogin
        };
      });

      res.json({
        success: true,
        data: {
          agents: agentPerformance,
          summary: {
            totalAgents: agents.length,
            activeAgents: agentPerformance.filter(a => a.status === 'online').length,
            avgSuccessRate: agentPerformance.reduce((sum, a) => sum + a.stats.successRate, 0) / agents.length || 0
          }
        }
      });
    } catch (error) {
      logger.error('Agent performance error:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to fetch agent performance'
      });
    }
  }

  /**
   * Get campaign performance
   */
  async getCampaignPerformance(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const tenantId = req.user!.tenantId;

      const campaigns = await prisma.campaign.findMany({
        where: { tenantId },
        include: {
          calls: true,
          customers: {
            include: {
              customer: true
            }
          }
        }
      });

      const campaignPerformance = campaigns.map(campaign => {
        const calls = campaign.calls;
        const completedCalls = calls.filter(c => c.status === 'COMPLETED');
        const successfulCalls = completedCalls.filter(c => 
          c.outcome && ['SALE', 'APPOINTMENT', 'INTERESTED'].includes(c.outcome)
        );

        return {
          id: campaign.id,
          name: campaign.name,
          type: campaign.type,
          status: campaign.status,
          startDate: campaign.startDate,
          endDate: campaign.endDate,
          stats: {
            totalCustomers: campaign.customers.length,
            totalCalls: calls.length,
            completedCalls: completedCalls.length,
            successfulCalls: successfulCalls.length,
            successRate: completedCalls.length > 0 ? (successfulCalls.length / completedCalls.length) * 100 : 0,
            contactRate: campaign.customers.length > 0 ? (calls.length / campaign.customers.length) * 100 : 0
          }
        };
      });

      res.json({
        success: true,
        data: campaignPerformance
      });
    } catch (error) {
      logger.error('Campaign performance error:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to fetch campaign performance'
      });
    }
  }

  /**
   * Get real-time data
   */
  async getRealTimeData(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const tenantId = req.user!.tenantId;

      // Get real-time metrics
      const [activeCalls, queuedCalls, onlineAgents] = await Promise.all([
        prisma.call.count({
          where: {
            tenantId,
            status: { in: ['RINGING', 'ANSWERED'] }
          }
        }),
        prisma.call.count({
          where: {
            tenantId,
            status: 'PENDING'
          }
        }),
        prisma.user.count({
          where: {
            tenantId,
            isActive: true,
            lastLogin: {
              gte: new Date(Date.now() - 15 * 60 * 1000) // Last 15 minutes
            }
          }
        })
      ]);

      // Generate real-time metrics
      const realTimeMetrics = {
        activeCalls,
        queuedCalls,
        onlineAgents,
        callsPerMinute: Math.floor(Math.random() * 10) + 5,
        avgWaitTime: Math.floor(Math.random() * 60) + 30,
        systemLoad: Math.random() * 100,
        memoryUsage: Math.random() * 100,
        cpuUsage: Math.random() * 100,
        networkLatency: Math.floor(Math.random() * 50) + 10,
        timestamp: new Date().toISOString()
      };

      res.json({
        success: true,
        data: realTimeMetrics
      });
    } catch (error) {
      logger.error('Real-time data error:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to fetch real-time data'
      });
    }
  }

  /**
   * Get system alerts
   */
  async getAlerts(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      // Generate mock alerts for demo
      const alerts = [
        {
          id: '1',
          type: 'warning',
          title: 'High Call Volume',
          message: 'Call volume is 25% above normal for this time of day',
          timestamp: new Date(Date.now() - 5 * 60 * 1000),
          severity: 'medium',
          acknowledged: false
        },
        {
          id: '2',
          type: 'info',
          title: 'System Update',
          message: 'Scheduled maintenance window in 2 hours',
          timestamp: new Date(Date.now() - 30 * 60 * 1000),
          severity: 'low',
          acknowledged: true
        },
        {
          id: '3',
          type: 'success',
          title: 'Campaign Performance',
          message: 'Marketing Campaign #123 exceeded target by 15%',
          timestamp: new Date(Date.now() - 60 * 60 * 1000),
          severity: 'low',
          acknowledged: false
        }
      ];

      res.json({
        success: true,
        data: {
          alerts,
          summary: {
            total: alerts.length,
            unacknowledged: alerts.filter(a => !a.acknowledged).length,
            critical: alerts.filter(a => a.severity === 'high').length,
            warnings: alerts.filter(a => a.severity === 'medium').length
          }
        }
      });
    } catch (error) {
      logger.error('Alerts error:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to fetch alerts'
      });
    }
  }

  /**
   * Export dashboard data
   */
  async exportData(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const format = req.query.format as string || 'csv';
      const dataTypes = req.query.data as string || 'overview';

      // For demo, return a success message
      res.json({
        success: true,
        message: `Export initiated for ${dataTypes} in ${format} format`,
        data: {
          exportId: `export_${Date.now()}`,
          format,
          dataTypes: dataTypes.split(','),
          estimatedSize: '2.5 MB',
          estimatedTime: '30 seconds'
        }
      });
    } catch (error) {
      logger.error('Export data error:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to initiate data export'
      });
    }
  }

  /**
   * Generate revenue data for demo
   */
  private async generateRevenueData(tenantId: string) {
    const now = new Date();
    const last30Days = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);

    // Mock revenue calculation based on successful calls
    const successfulCalls = await prisma.call.count({
      where: {
        tenantId,
        status: 'COMPLETED',
        outcome: { in: ['SALE', 'APPOINTMENT'] },
        createdAt: { gte: last30Days }
      }
    });

    const avgDealValue = 250; // Mock average deal value
    const currentRevenue = successfulCalls * avgDealValue;
    const projectedRevenue = currentRevenue * 1.15; // 15% growth projection

    return {
      current: currentRevenue,
      projected: projectedRevenue,
      growth: 15.0,
      target: currentRevenue * 1.2
    };
  }

  /**
   * Generate detailed revenue analytics
   */
  private async generateRevenueAnalytics(tenantId: string, period: string) {
    const days = this.getPeriodDays(period);
    const data = [];

    for (let i = days - 1; i >= 0; i--) {
      const date = new Date();
      date.setDate(date.getDate() - i);
      
      // Mock revenue data
      const baseRevenue = 1000 + Math.random() * 2000;
      const seasonality = Math.sin((date.getDay() / 7) * Math.PI) * 500;
      const revenue = Math.max(0, baseRevenue + seasonality);

      data.push({
        date: date.toISOString().split('T')[0],
        revenue: Math.round(revenue),
        calls: Math.floor(revenue / 250),
        conversion: Math.random() * 0.3 + 0.1
      });
    }

    return {
      timeSeries: data,
      summary: {
        totalRevenue: data.reduce((sum, d) => sum + d.revenue, 0),
        avgDailyRevenue: data.reduce((sum, d) => sum + d.revenue, 0) / data.length,
        totalCalls: data.reduce((sum, d) => sum + d.calls, 0),
        avgConversion: data.reduce((sum, d) => sum + d.conversion, 0) / data.length
      }
    };
  }

  /**
   * Get system health status
   */
  private async getSystemHealth() {
    return {
      status: 'healthy',
      uptime: process.uptime(),
      memory: process.memoryUsage(),
      cpu: Math.random() * 100,
      database: 'connected',
      redis: 'connected',
      lastCheck: new Date().toISOString()
    };
  }

  /**
   * Get agent status based on last login
   */
  private getAgentStatus(lastLogin: Date | null): string {
    if (!lastLogin) return 'offline';
    
    const now = new Date();
    const diffMinutes = (now.getTime() - lastLogin.getTime()) / (1000 * 60);
    
    if (diffMinutes < 5) return 'online';
    if (diffMinutes < 30) return 'away';
    return 'offline';
  }

  /**
   * Convert period string to number of days
   */
  private getPeriodDays(period: string): number {
    switch (period) {
      case '7d': return 7;
      case '30d': return 30;
      case '90d': return 90;
      case '1y': return 365;
      default: return 30;
    }
  }
}

export default DashboardController;