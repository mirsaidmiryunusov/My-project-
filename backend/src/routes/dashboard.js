const express = require('express');
const router = express.Router();
const { authenticateToken } = require('../middleware/auth');
const { DatabaseService } = require('../services/database');
const { MetricsService } = require('../services/metrics');

// Get dashboard metrics
router.get('/metrics', authenticateToken, async (req, res) => {
  try {
    const userId = req.user.id;
    const db = DatabaseService.getInstance();
    const metricsService = new MetricsService();

    // Get current metrics
    const metrics = await metricsService.getDashboardMetrics(userId);
    
    // Get additional data from database
    const [
      totalCalls,
      activeCampaigns,
      totalContacts,
      successfulCalls,
      failedCalls,
      pendingCalls
    ] = await Promise.all([
      db.query('SELECT COUNT(*) as count FROM calls WHERE user_id = ?', [userId]),
      db.query('SELECT COUNT(*) as count FROM campaigns WHERE user_id = ? AND status = "active"', [userId]),
      db.query('SELECT COUNT(*) as count FROM contacts WHERE user_id = ?', [userId]),
      db.query('SELECT COUNT(*) as count FROM calls WHERE user_id = ? AND status = "completed"', [userId]),
      db.query('SELECT COUNT(*) as count FROM calls WHERE user_id = ? AND status = "failed"', [userId]),
      db.query('SELECT COUNT(*) as count FROM calls WHERE user_id = ? AND status = "pending"', [userId])
    ]);

    // Calculate conversion rate
    const total = totalCalls[0]?.count || 0;
    const successful = successfulCalls[0]?.count || 0;
    const conversionRate = total > 0 ? (successful / total) * 100 : 0;

    // Calculate average call duration
    const avgDurationResult = await db.query(
      'SELECT AVG(duration) as avgDuration FROM calls WHERE user_id = ? AND duration > 0',
      [userId]
    );
    const avgCallDuration = avgDurationResult[0]?.avgDuration || 0;

    // Calculate monthly growth (mock for now)
    const monthlyGrowth = Math.random() * 20 - 10; // -10% to +10%

    const dashboardMetrics = {
      totalCalls: total,
      activeCampaigns: activeCampaigns[0]?.count || 0,
      totalContacts: totalContacts[0]?.count || 0,
      conversionRate: conversionRate,
      avgCallDuration: Math.round(avgCallDuration),
      successfulCalls: successful,
      failedCalls: failedCalls[0]?.count || 0,
      pendingCalls: pendingCalls[0]?.count || 0,
      totalRevenue: metrics.revenue || 0,
      monthlyGrowth: monthlyGrowth,
    };

    res.json({
      success: true,
      data: dashboardMetrics,
    });
  } catch (error) {
    console.error('Error fetching dashboard metrics:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to fetch dashboard metrics',
      error: error.message,
    });
  }
});

// Get recent calls
router.get('/recent-calls', authenticateToken, async (req, res) => {
  try {
    const userId = req.user.id;
    const limit = parseInt(req.query.limit) || 10;
    const db = DatabaseService.getInstance();

    const recentCalls = await db.query(`
      SELECT 
        c.id,
        c.phone_number as phoneNumber,
        c.status,
        c.duration,
        c.created_at as timestamp,
        c.campaign_id as campaignId,
        c.outcome,
        c.notes,
        COALESCE(cont.first_name, 'Unknown') as firstName,
        COALESCE(cont.last_name, 'Contact') as lastName,
        CONCAT(COALESCE(cont.first_name, 'Unknown'), ' ', COALESCE(cont.last_name, 'Contact')) as customerName
      FROM calls c
      LEFT JOIN contacts cont ON c.contact_id = cont.id
      WHERE c.user_id = ?
      ORDER BY c.created_at DESC
      LIMIT ?
    `, [userId, limit]);

    const formattedCalls = recentCalls.map(call => ({
      id: call.id,
      customerName: call.customerName,
      phoneNumber: call.phoneNumber,
      status: call.status,
      duration: call.duration || 0,
      timestamp: call.timestamp,
      campaignId: call.campaignId,
      outcome: call.outcome,
      notes: call.notes,
    }));

    res.json({
      success: true,
      data: formattedCalls,
    });
  } catch (error) {
    console.error('Error fetching recent calls:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to fetch recent calls',
      error: error.message,
    });
  }
});

// Get dashboard analytics
router.get('/analytics', authenticateToken, async (req, res) => {
  try {
    const userId = req.user.id;
    const timeRange = req.query.timeRange || '7d';
    const db = DatabaseService.getInstance();

    // Calculate date range
    let daysBack = 7;
    switch (timeRange) {
      case '1d': daysBack = 1; break;
      case '7d': daysBack = 7; break;
      case '30d': daysBack = 30; break;
      case '90d': daysBack = 90; break;
      default: daysBack = 7;
    }

    const startDate = new Date();
    startDate.setDate(startDate.getDate() - daysBack);

    // Get call volume data
    const callVolumeData = await db.query(`
      SELECT 
        DATE(created_at) as date,
        COUNT(*) as calls,
        SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful,
        SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
      FROM calls 
      WHERE user_id = ? AND created_at >= ?
      GROUP BY DATE(created_at)
      ORDER BY date
    `, [userId, startDate.toISOString()]);

    // Get conversion trends
    const conversionTrends = callVolumeData.map(item => ({
      date: item.date,
      rate: item.calls > 0 ? (item.successful / item.calls) * 100 : 0,
    }));

    // Get campaign performance
    const campaignPerformance = await db.query(`
      SELECT 
        camp.id as campaignId,
        camp.name,
        COUNT(c.id) as calls,
        SUM(CASE WHEN c.status = 'completed' THEN 1 ELSE 0 END) as conversions,
        SUM(CASE WHEN c.status = 'completed' THEN COALESCE(c.revenue, 0) ELSE 0 END) as revenue
      FROM campaigns camp
      LEFT JOIN calls c ON camp.id = c.campaign_id AND c.created_at >= ?
      WHERE camp.user_id = ?
      GROUP BY camp.id, camp.name
      ORDER BY calls DESC
      LIMIT 10
    `, [startDate.toISOString(), userId]);

    // Get hourly distribution (mock data for now)
    const hourlyDistribution = Array.from({ length: 24 }, (_, hour) => ({
      hour,
      calls: Math.floor(Math.random() * 50) + 10,
      successRate: Math.random() * 40 + 60, // 60-100%
    }));

    // Get geographic data (mock for now)
    const geographicData = [
      { region: 'North America', calls: Math.floor(Math.random() * 1000) + 500, successRate: Math.random() * 20 + 70 },
      { region: 'Europe', calls: Math.floor(Math.random() * 800) + 300, successRate: Math.random() * 20 + 65 },
      { region: 'Asia Pacific', calls: Math.floor(Math.random() * 600) + 200, successRate: Math.random() * 20 + 60 },
      { region: 'Latin America', calls: Math.floor(Math.random() * 400) + 100, successRate: Math.random() * 20 + 55 },
    ];

    const analytics = {
      callVolume: callVolumeData,
      conversionTrends,
      campaignPerformance,
      hourlyDistribution,
      geographicData,
    };

    res.json({
      success: true,
      data: analytics,
    });
  } catch (error) {
    console.error('Error fetching dashboard analytics:', error);
    res.status(500).json({
      success: false,
      message: 'Failed to fetch dashboard analytics',
      error: error.message,
    });
  }
});

module.exports = router;