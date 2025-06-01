/**
 * Analytics Controller
 * 
 * Handles analytics and reporting operations for the GeminiVoiceConnect platform.
 */

import { Response } from 'express';
import { AuthenticatedRequest } from '../types/auth';
import { AnalyticsService } from '../services/analytics';
import { logger } from '../utils/logger';

const analyticsService = new AnalyticsService();

export class AnalyticsController {
  async getOverview(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { period = '7d' } = req.query;
      const tenantId = req.user!.tenantId;

      const analytics = await analyticsService.getAnalytics(tenantId, period as string);

      res.json({
        success: true,
        data: analytics,
      });
    } catch (error) {
      logger.error('Get analytics overview error:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to fetch analytics overview',
      });
    }
  }

  async getCallAnalytics(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { period = '7d', groupBy = 'day', metrics } = req.query;
      const tenantId = req.user!.tenantId;

      const callStats = await analyticsService.getCallStatistics(tenantId, period as string);

      res.json({
        success: true,
        data: callStats,
      });
    } catch (error) {
      logger.error('Get call analytics error:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to fetch call analytics',
      });
    }
  }

  async getRevenueAnalytics(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { period = '30d', breakdown = 'daily' } = req.query;
      const tenantId = req.user!.tenantId;

      // Mock revenue analytics for demo
      const revenueData = {
        period,
        breakdown,
        totalRevenue: 125000,
        growth: 15.5,
        forecast: 145000,
        dailyData: this.generateMockRevenueData(period as string),
      };

      res.json({
        success: true,
        data: revenueData,
      });
    } catch (error) {
      logger.error('Get revenue analytics error:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to fetch revenue analytics',
      });
    }
  }

  async getPerformanceAnalytics(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { period = '30d', type = 'overall' } = req.query;
      const tenantId = req.user!.tenantId;

      const analytics = await analyticsService.getAnalytics(tenantId, period as string, 'agents,calls,success_rate');

      res.json({
        success: true,
        data: analytics,
      });
    } catch (error) {
      logger.error('Get performance analytics error:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to fetch performance analytics',
      });
    }
  }

  async getSentimentAnalytics(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { period = '7d', breakdown = 'daily' } = req.query;
      const tenantId = req.user!.tenantId;

      const sentimentData = await analyticsService.getSentimentAnalysis(tenantId, period as string);

      res.json({
        success: true,
        data: sentimentData,
      });
    } catch (error) {
      logger.error('Get sentiment analytics error:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to fetch sentiment analytics',
      });
    }
  }

  async getTrendAnalytics(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { metric, period = '30d', comparison = 'previous_period' } = req.query;
      const tenantId = req.user!.tenantId;

      // Mock trend data for demo
      const trendData = {
        metric,
        period,
        comparison,
        currentValue: 85.5,
        previousValue: 78.2,
        change: 7.3,
        trend: 'increasing',
        data: this.generateMockTrendData(period as string),
      };

      res.json({
        success: true,
        data: trendData,
      });
    } catch (error) {
      logger.error('Get trend analytics error:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to fetch trend analytics',
      });
    }
  }

  async getAgentAnalytics(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { period = '30d', sortBy = 'success_rate', order = 'desc' } = req.query;
      const tenantId = req.user!.tenantId;

      const analytics = await analyticsService.getAnalytics(tenantId, period as string, 'agents');

      res.json({
        success: true,
        data: analytics.metrics.agents || { agents: [], summary: {} },
      });
    } catch (error) {
      logger.error('Get agent analytics error:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to fetch agent analytics',
      });
    }
  }

  async getCampaignAnalytics(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { period = '30d', status } = req.query;
      const tenantId = req.user!.tenantId;

      // Mock campaign analytics for demo
      const campaignData = {
        period,
        campaigns: [
          {
            id: '1',
            name: 'Q4 Sales Campaign',
            status: 'ACTIVE',
            totalCalls: 1250,
            successRate: 23.5,
            revenue: 45000,
          },
          {
            id: '2',
            name: 'Holiday Promotion',
            status: 'COMPLETED',
            totalCalls: 890,
            successRate: 28.1,
            revenue: 32000,
          },
        ],
        summary: {
          totalCampaigns: 2,
          activeCampaigns: 1,
          avgSuccessRate: 25.8,
          totalRevenue: 77000,
        },
      };

      res.json({
        success: true,
        data: campaignData,
      });
    } catch (error) {
      logger.error('Get campaign analytics error:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to fetch campaign analytics',
      });
    }
  }

  async getCustomerAnalytics(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { period = '30d', segment } = req.query;
      const tenantId = req.user!.tenantId;

      const analytics = await analyticsService.getAnalytics(tenantId, period as string, 'customers');

      res.json({
        success: true,
        data: analytics.metrics.customers || { new: 0, total: 0, active: 0, engagementRate: 0 },
      });
    } catch (error) {
      logger.error('Get customer analytics error:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to fetch customer analytics',
      });
    }
  }

  async getForecastAnalytics(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { metric, horizon = '30d', confidence = 0.85 } = req.query;

      // Mock forecast data for demo
      const forecastData = {
        metric,
        horizon,
        confidence: Number(confidence),
        forecast: this.generateMockForecastData(metric as string, horizon as string),
        accuracy: 87.5,
        lastUpdated: new Date().toISOString(),
      };

      res.json({
        success: true,
        data: forecastData,
      });
    } catch (error) {
      logger.error('Get forecast analytics error:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to fetch forecast analytics',
      });
    }
  }

  async getAvailableReports(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const reports = [
        {
          id: 'call-summary',
          name: 'Call Summary Report',
          description: 'Comprehensive overview of call activities',
          category: 'calls',
        },
        {
          id: 'agent-performance',
          name: 'Agent Performance Report',
          description: 'Individual agent metrics and performance',
          category: 'performance',
        },
        {
          id: 'revenue-analysis',
          name: 'Revenue Analysis Report',
          description: 'Revenue trends and forecasts',
          category: 'revenue',
        },
        {
          id: 'customer-insights',
          name: 'Customer Insights Report',
          description: 'Customer behavior and engagement analysis',
          category: 'customers',
        },
      ];

      res.json({
        success: true,
        data: reports,
      });
    } catch (error) {
      logger.error('Get available reports error:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to fetch available reports',
      });
    }
  }

  async generateCustomReport(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { reportType, parameters } = req.body;

      // Mock report generation for demo
      const report = {
        id: `report_${Date.now()}`,
        type: reportType,
        parameters,
        status: 'generating',
        estimatedTime: '2-3 minutes',
        createdAt: new Date().toISOString(),
      };

      res.status(202).json({
        success: true,
        message: 'Report generation started',
        data: report,
      });
    } catch (error) {
      logger.error('Generate custom report error:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to generate custom report',
      });
    }
  }

  async exportAnalytics(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const { type, format = 'csv', period = '30d' } = req.query;

      // Mock export for demo
      const exportData = {
        exportId: `export_${Date.now()}`,
        type,
        format,
        period,
        status: 'processing',
        estimatedSize: '2.5 MB',
        estimatedTime: '30 seconds',
      };

      res.json({
        success: true,
        message: 'Export initiated',
        data: exportData,
      });
    } catch (error) {
      logger.error('Export analytics error:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to export analytics',
      });
    }
  }

  async getRealTimeAnalytics(req: AuthenticatedRequest, res: Response): Promise<void> {
    try {
      const tenantId = req.user!.tenantId;

      // Mock real-time data for demo
      const realTimeData = {
        timestamp: new Date().toISOString(),
        activeCalls: Math.floor(Math.random() * 20) + 5,
        callsPerMinute: Math.floor(Math.random() * 10) + 2,
        avgWaitTime: Math.floor(Math.random() * 60) + 15,
        successRate: Math.random() * 30 + 60,
        onlineAgents: Math.floor(Math.random() * 15) + 5,
        queuedCalls: Math.floor(Math.random() * 10),
      };

      res.json({
        success: true,
        data: realTimeData,
      });
    } catch (error) {
      logger.error('Get real-time analytics error:', error);
      res.status(500).json({
        success: false,
        message: 'Failed to fetch real-time analytics',
      });
    }
  }

  private generateMockRevenueData(period: string): any[] {
    const days = period === '7d' ? 7 : period === '30d' ? 30 : 90;
    const data = [];

    for (let i = days - 1; i >= 0; i--) {
      const date = new Date();
      date.setDate(date.getDate() - i);
      
      const baseRevenue = 1000 + Math.random() * 2000;
      const seasonality = Math.sin((date.getDay() / 7) * Math.PI) * 500;
      const revenue = Math.max(0, baseRevenue + seasonality);

      data.push({
        date: date.toISOString().split('T')[0],
        revenue: Math.round(revenue),
        calls: Math.floor(revenue / 250),
      });
    }

    return data;
  }

  private generateMockTrendData(period: string): any[] {
    const days = period === '7d' ? 7 : period === '30d' ? 30 : 90;
    const data = [];

    for (let i = days - 1; i >= 0; i--) {
      const date = new Date();
      date.setDate(date.getDate() - i);
      
      const baseValue = 75 + Math.random() * 20;
      const trend = (days - i) / days * 10; // Upward trend
      const noise = (Math.random() - 0.5) * 10;
      const value = Math.max(0, Math.min(100, baseValue + trend + noise));

      data.push({
        date: date.toISOString().split('T')[0],
        value: Math.round(value * 100) / 100,
      });
    }

    return data;
  }

  private generateMockForecastData(metric: string, horizon: string): any[] {
    const days = horizon === '7d' ? 7 : horizon === '30d' ? 30 : 90;
    const data = [];

    for (let i = 1; i <= days; i++) {
      const date = new Date();
      date.setDate(date.getDate() + i);
      
      let baseValue = 1000;
      if (metric === 'revenue') baseValue = 2000;
      else if (metric === 'churn') baseValue = 5;

      const trend = i / days * 0.15; // 15% growth over period
      const seasonality = Math.sin((i / 7) * Math.PI) * 0.1;
      const randomness = (Math.random() - 0.5) * 0.2;
      
      const value = baseValue * (1 + trend + seasonality + randomness);
      const confidence = Math.max(0.5, 0.95 - (i / days) * 0.3); // Decreasing confidence

      data.push({
        date: date.toISOString().split('T')[0],
        value: Math.round(value),
        confidence: Math.round(confidence * 100) / 100,
        range: {
          min: Math.round(value * 0.8),
          max: Math.round(value * 1.2),
        },
      });
    }

    return data;
  }
}