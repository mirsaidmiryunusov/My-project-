"""
Analytics Engine for Project GeminiVoiceConnect

This module provides comprehensive business intelligence and analytics capabilities for the
AI Call Center Agent system. It implements real-time analytics processing, predictive
modeling, customer behavior analysis, and revenue optimization insights.

Key Features:
- Real-time call analytics and performance metrics
- Customer behavior analysis and segmentation
- Revenue optimization and forecasting
- Predictive churn analysis and retention insights
- Campaign performance analytics
- Agent performance monitoring (AI agents)
- Custom dashboard metrics and KPIs
- Advanced reporting and data visualization
"""

from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import json
import logging
from dataclasses import dataclass, asdict
import statistics
from collections import defaultdict, Counter
import numpy as np
from scipy import stats
import pandas as pd

from sqlmodel import Session, select, func, and_, or_
from fastapi import HTTPException, status

from .config import get_settings
from .database import get_session
from .models import (
    Tenant, CallLog, Customer, Lead, Order, Campaign,
    AgentPerformance, CustomerSegment, AnalyticsReport
)

logger = logging.getLogger(__name__)
settings = get_settings()


class MetricType(str, Enum):
    """Types of analytics metrics"""
    CALL_VOLUME = "call_volume"
    CALL_DURATION = "call_duration"
    CONVERSION_RATE = "conversion_rate"
    CUSTOMER_SATISFACTION = "customer_satisfaction"
    REVENUE = "revenue"
    CHURN_RATE = "churn_rate"
    RESPONSE_TIME = "response_time"
    RESOLUTION_RATE = "resolution_rate"


class TimeGranularity(str, Enum):
    """Time granularity for analytics"""
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"


class SegmentCriteria(str, Enum):
    """Customer segmentation criteria"""
    VALUE = "value"
    FREQUENCY = "frequency"
    RECENCY = "recency"
    BEHAVIOR = "behavior"
    DEMOGRAPHICS = "demographics"
    ENGAGEMENT = "engagement"


@dataclass
class AnalyticsMetric:
    """Analytics metric data structure"""
    name: str
    value: float
    unit: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class TrendAnalysis:
    """Trend analysis result"""
    metric: str
    trend_direction: str  # "up", "down", "stable"
    trend_strength: float  # 0-1
    percentage_change: float
    period_comparison: str
    confidence_level: float


@dataclass
class CustomerInsight:
    """Customer behavior insight"""
    customer_id: str
    segment: str
    lifetime_value: float
    churn_probability: float
    next_best_action: str
    engagement_score: float
    satisfaction_score: float


@dataclass
class RevenueAnalysis:
    """Revenue analysis result"""
    total_revenue: float
    revenue_growth: float
    average_order_value: float
    conversion_rate: float
    revenue_by_source: Dict[str, float]
    revenue_forecast: Dict[str, float]


class AnalyticsEngine:
    """
    Comprehensive analytics engine providing business intelligence and insights.
    
    This engine processes call data, customer interactions, and business metrics to
    generate actionable insights for optimizing call center operations and revenue.
    It includes real-time analytics, predictive modeling, and advanced reporting
    capabilities.
    """
    
    def __init__(self):
        self.cache = {}
        self.cache_ttl = timedelta(minutes=5)
        
    async def get_real_time_metrics(
        self,
        tenant_id: str,
        metric_types: List[MetricType],
        time_range: Optional[timedelta] = None
    ) -> List[AnalyticsMetric]:
        """
        Get real-time analytics metrics for a tenant.
        
        Args:
            tenant_id: Tenant identifier
            metric_types: List of metrics to retrieve
            time_range: Time range for metrics (default: last hour)
            
        Returns:
            List of analytics metrics
        """
        if time_range is None:
            time_range = timedelta(hours=1)
        
        start_time = datetime.utcnow() - time_range
        metrics = []
        
        try:
            with get_session() as session:
                for metric_type in metric_types:
                    metric_value = await self._calculate_metric(
                        session, tenant_id, metric_type, start_time
                    )
                    
                    metrics.append(AnalyticsMetric(
                        name=metric_type.value,
                        value=metric_value,
                        unit=self._get_metric_unit(metric_type),
                        timestamp=datetime.utcnow()
                    ))
                
                logger.info(f"Generated {len(metrics)} real-time metrics for tenant {tenant_id}")
                return metrics
                
        except Exception as e:
            logger.error(f"Failed to get real-time metrics: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve real-time metrics"
            )
    
    async def analyze_call_performance(
        self,
        tenant_id: str,
        time_period: timedelta = timedelta(days=30)
    ) -> Dict[str, Any]:
        """
        Analyze call performance metrics and trends.
        
        Args:
            tenant_id: Tenant identifier
            time_period: Analysis time period
            
        Returns:
            Call performance analysis
        """
        try:
            start_time = datetime.utcnow() - time_period
            
            with get_session() as session:
                # Get call logs for the period
                call_logs = session.exec(
                    select(CallLog).where(
                        and_(
                            CallLog.tenant_id == tenant_id,
                            CallLog.start_time >= start_time
                        )
                    )
                ).all()
                
                if not call_logs:
                    return {
                        "total_calls": 0,
                        "average_duration": 0,
                        "success_rate": 0,
                        "trends": []
                    }
                
                # Calculate basic metrics
                total_calls = len(call_logs)
                successful_calls = len([call for call in call_logs if call.status == "completed"])
                total_duration = sum([call.duration or 0 for call in call_logs])
                
                # Calculate performance metrics
                success_rate = (successful_calls / total_calls) * 100 if total_calls > 0 else 0
                average_duration = total_duration / total_calls if total_calls > 0 else 0
                
                # Analyze trends
                daily_metrics = self._group_calls_by_day(call_logs)
                trends = self._calculate_trends(daily_metrics)
                
                # Calculate response time metrics
                response_times = [call.response_time for call in call_logs if call.response_time]
                avg_response_time = statistics.mean(response_times) if response_times else 0
                
                # Calculate resolution metrics
                resolved_calls = len([call for call in call_logs if call.resolution_status == "resolved"])
                resolution_rate = (resolved_calls / total_calls) * 100 if total_calls > 0 else 0
                
                analysis = {
                    "total_calls": total_calls,
                    "successful_calls": successful_calls,
                    "success_rate": success_rate,
                    "average_duration": average_duration,
                    "average_response_time": avg_response_time,
                    "resolution_rate": resolution_rate,
                    "trends": trends,
                    "daily_breakdown": daily_metrics,
                    "peak_hours": self._identify_peak_hours(call_logs),
                    "call_types": self._analyze_call_types(call_logs)
                }
                
                logger.info(f"Analyzed call performance for tenant {tenant_id}: {total_calls} calls")
                return analysis
                
        except Exception as e:
            logger.error(f"Failed to analyze call performance: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to analyze call performance"
            )
    
    async def analyze_customer_behavior(
        self,
        tenant_id: str,
        customer_id: Optional[str] = None
    ) -> Union[CustomerInsight, List[CustomerInsight]]:
        """
        Analyze customer behavior and generate insights.
        
        Args:
            tenant_id: Tenant identifier
            customer_id: Optional specific customer ID
            
        Returns:
            Customer insights (single or list)
        """
        try:
            with get_session() as session:
                if customer_id:
                    # Analyze specific customer
                    customer = session.get(Customer, customer_id)
                    if not customer or customer.tenant_id != tenant_id:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail="Customer not found"
                        )
                    
                    insight = await self._analyze_single_customer(session, customer)
                    return insight
                else:
                    # Analyze all customers for tenant
                    customers = session.exec(
                        select(Customer).where(Customer.tenant_id == tenant_id)
                    ).all()
                    
                    insights = []
                    for customer in customers:
                        insight = await self._analyze_single_customer(session, customer)
                        insights.append(insight)
                    
                    logger.info(f"Analyzed {len(insights)} customers for tenant {tenant_id}")
                    return insights
                    
        except Exception as e:
            logger.error(f"Failed to analyze customer behavior: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to analyze customer behavior"
            )
    
    async def generate_revenue_analysis(
        self,
        tenant_id: str,
        time_period: timedelta = timedelta(days=30)
    ) -> RevenueAnalysis:
        """
        Generate comprehensive revenue analysis.
        
        Args:
            tenant_id: Tenant identifier
            time_period: Analysis time period
            
        Returns:
            Revenue analysis results
        """
        try:
            start_time = datetime.utcnow() - time_period
            
            with get_session() as session:
                # Get orders for the period
                orders = session.exec(
                    select(Order).where(
                        and_(
                            Order.tenant_id == tenant_id,
                            Order.created_at >= start_time,
                            Order.status == "completed"
                        )
                    )
                ).all()
                
                if not orders:
                    return RevenueAnalysis(
                        total_revenue=0.0,
                        revenue_growth=0.0,
                        average_order_value=0.0,
                        conversion_rate=0.0,
                        revenue_by_source={},
                        revenue_forecast={}
                    )
                
                # Calculate revenue metrics
                total_revenue = sum([order.total_amount for order in orders])
                average_order_value = total_revenue / len(orders)
                
                # Calculate revenue growth
                previous_period_start = start_time - time_period
                previous_orders = session.exec(
                    select(Order).where(
                        and_(
                            Order.tenant_id == tenant_id,
                            Order.created_at >= previous_period_start,
                            Order.created_at < start_time,
                            Order.status == "completed"
                        )
                    )
                ).all()
                
                previous_revenue = sum([order.total_amount for order in previous_orders])
                revenue_growth = ((total_revenue - previous_revenue) / previous_revenue * 100) if previous_revenue > 0 else 0
                
                # Calculate conversion rate
                total_leads = session.exec(
                    select(func.count(Lead.id)).where(
                        and_(
                            Lead.tenant_id == tenant_id,
                            Lead.created_at >= start_time
                        )
                    )
                ).first()
                
                conversion_rate = (len(orders) / total_leads * 100) if total_leads > 0 else 0
                
                # Revenue by source
                revenue_by_source = defaultdict(float)
                for order in orders:
                    source = order.source or "unknown"
                    revenue_by_source[source] += order.total_amount
                
                # Generate revenue forecast
                revenue_forecast = self._generate_revenue_forecast(orders)
                
                analysis = RevenueAnalysis(
                    total_revenue=total_revenue,
                    revenue_growth=revenue_growth,
                    average_order_value=average_order_value,
                    conversion_rate=conversion_rate,
                    revenue_by_source=dict(revenue_by_source),
                    revenue_forecast=revenue_forecast
                )
                
                logger.info(f"Generated revenue analysis for tenant {tenant_id}: ${total_revenue:.2f}")
                return analysis
                
        except Exception as e:
            logger.error(f"Failed to generate revenue analysis: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate revenue analysis"
            )
    
    async def predict_customer_churn(
        self,
        tenant_id: str,
        prediction_horizon: timedelta = timedelta(days=30)
    ) -> List[Dict[str, Any]]:
        """
        Predict customer churn using behavioral analysis.
        
        Args:
            tenant_id: Tenant identifier
            prediction_horizon: Prediction time horizon
            
        Returns:
            List of churn predictions
        """
        try:
            with get_session() as session:
                customers = session.exec(
                    select(Customer).where(Customer.tenant_id == tenant_id)
                ).all()
                
                predictions = []
                
                for customer in customers:
                    # Calculate churn probability based on various factors
                    churn_score = await self._calculate_churn_score(session, customer)
                    
                    # Get customer engagement metrics
                    engagement_score = await self._calculate_engagement_score(session, customer)
                    
                    # Get recent interaction patterns
                    recent_interactions = await self._get_recent_interactions(session, customer.id)
                    
                    prediction = {
                        "customer_id": customer.id,
                        "customer_name": f"{customer.first_name} {customer.last_name}",
                        "churn_probability": churn_score,
                        "risk_level": self._get_risk_level(churn_score),
                        "engagement_score": engagement_score,
                        "last_interaction": recent_interactions.get("last_interaction"),
                        "interaction_frequency": recent_interactions.get("frequency"),
                        "recommended_actions": self._get_retention_recommendations(churn_score, engagement_score)
                    }
                    
                    predictions.append(prediction)
                
                # Sort by churn probability (highest risk first)
                predictions.sort(key=lambda x: x["churn_probability"], reverse=True)
                
                logger.info(f"Generated churn predictions for {len(predictions)} customers")
                return predictions
                
        except Exception as e:
            logger.error(f"Failed to predict customer churn: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to predict customer churn"
            )
    
    async def segment_customers(
        self,
        tenant_id: str,
        criteria: List[SegmentCriteria]
    ) -> Dict[str, List[str]]:
        """
        Segment customers based on specified criteria.
        
        Args:
            tenant_id: Tenant identifier
            criteria: Segmentation criteria
            
        Returns:
            Customer segments
        """
        try:
            with get_session() as session:
                customers = session.exec(
                    select(Customer).where(Customer.tenant_id == tenant_id)
                ).all()
                
                segments = defaultdict(list)
                
                for customer in customers:
                    customer_segments = []
                    
                    for criterion in criteria:
                        segment = await self._apply_segmentation_criterion(
                            session, customer, criterion
                        )
                        customer_segments.append(segment)
                    
                    # Combine segments
                    combined_segment = "_".join(customer_segments)
                    segments[combined_segment].append(customer.id)
                
                logger.info(f"Segmented {len(customers)} customers into {len(segments)} segments")
                return dict(segments)
                
        except Exception as e:
            logger.error(f"Failed to segment customers: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to segment customers"
            )
    
    async def generate_campaign_analytics(
        self,
        tenant_id: str,
        campaign_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate campaign performance analytics.
        
        Args:
            tenant_id: Tenant identifier
            campaign_id: Optional specific campaign ID
            
        Returns:
            Campaign analytics
        """
        try:
            with get_session() as session:
                if campaign_id:
                    campaigns = [session.get(Campaign, campaign_id)]
                    if not campaigns[0] or campaigns[0].tenant_id != tenant_id:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail="Campaign not found"
                        )
                else:
                    campaigns = session.exec(
                        select(Campaign).where(Campaign.tenant_id == tenant_id)
                    ).all()
                
                analytics = {}
                
                for campaign in campaigns:
                    if not campaign:
                        continue
                        
                    # Get campaign calls
                    campaign_calls = session.exec(
                        select(CallLog).where(CallLog.campaign_id == campaign.id)
                    ).all()
                    
                    # Calculate campaign metrics
                    total_calls = len(campaign_calls)
                    successful_calls = len([call for call in campaign_calls if call.status == "completed"])
                    
                    # Get campaign leads
                    campaign_leads = session.exec(
                        select(Lead).where(Lead.campaign_id == campaign.id)
                    ).all()
                    
                    # Get campaign orders
                    campaign_orders = session.exec(
                        select(Order).where(Order.campaign_id == campaign.id)
                    ).all()
                    
                    campaign_analytics = {
                        "campaign_id": campaign.id,
                        "campaign_name": campaign.name,
                        "total_calls": total_calls,
                        "successful_calls": successful_calls,
                        "success_rate": (successful_calls / total_calls * 100) if total_calls > 0 else 0,
                        "total_leads": len(campaign_leads),
                        "qualified_leads": len([lead for lead in campaign_leads if lead.status == "qualified"]),
                        "total_orders": len(campaign_orders),
                        "total_revenue": sum([order.total_amount for order in campaign_orders]),
                        "conversion_rate": (len(campaign_orders) / len(campaign_leads) * 100) if campaign_leads else 0,
                        "cost_per_lead": campaign.budget / len(campaign_leads) if campaign_leads and campaign.budget else 0,
                        "roi": self._calculate_campaign_roi(campaign, campaign_orders)
                    }
                    
                    analytics[campaign.id] = campaign_analytics
                
                logger.info(f"Generated analytics for {len(analytics)} campaigns")
                return analytics
                
        except Exception as e:
            logger.error(f"Failed to generate campaign analytics: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate campaign analytics"
            )
    
    async def _calculate_metric(
        self,
        session: Session,
        tenant_id: str,
        metric_type: MetricType,
        start_time: datetime
    ) -> float:
        """Calculate specific metric value"""
        if metric_type == MetricType.CALL_VOLUME:
            result = session.exec(
                select(func.count(CallLog.id)).where(
                    and_(
                        CallLog.tenant_id == tenant_id,
                        CallLog.start_time >= start_time
                    )
                )
            ).first()
            return float(result or 0)
        
        elif metric_type == MetricType.CALL_DURATION:
            result = session.exec(
                select(func.avg(CallLog.duration)).where(
                    and_(
                        CallLog.tenant_id == tenant_id,
                        CallLog.start_time >= start_time,
                        CallLog.duration.isnot(None)
                    )
                )
            ).first()
            return float(result or 0)
        
        elif metric_type == MetricType.CONVERSION_RATE:
            total_leads = session.exec(
                select(func.count(Lead.id)).where(
                    and_(
                        Lead.tenant_id == tenant_id,
                        Lead.created_at >= start_time
                    )
                )
            ).first()
            
            converted_leads = session.exec(
                select(func.count(Lead.id)).where(
                    and_(
                        Lead.tenant_id == tenant_id,
                        Lead.created_at >= start_time,
                        Lead.status == "converted"
                    )
                )
            ).first()
            
            return (converted_leads / total_leads * 100) if total_leads > 0 else 0
        
        # Add more metric calculations as needed
        return 0.0
    
    def _get_metric_unit(self, metric_type: MetricType) -> str:
        """Get unit for metric type"""
        units = {
            MetricType.CALL_VOLUME: "calls",
            MetricType.CALL_DURATION: "seconds",
            MetricType.CONVERSION_RATE: "percentage",
            MetricType.CUSTOMER_SATISFACTION: "score",
            MetricType.REVENUE: "currency",
            MetricType.CHURN_RATE: "percentage",
            MetricType.RESPONSE_TIME: "seconds",
            MetricType.RESOLUTION_RATE: "percentage"
        }
        return units.get(metric_type, "units")
    
    def _group_calls_by_day(self, call_logs: List[CallLog]) -> Dict[str, Dict[str, Any]]:
        """Group calls by day for trend analysis"""
        daily_metrics = defaultdict(lambda: {"calls": 0, "duration": 0, "successful": 0})
        
        for call in call_logs:
            day_key = call.start_time.strftime("%Y-%m-%d")
            daily_metrics[day_key]["calls"] += 1
            daily_metrics[day_key]["duration"] += call.duration or 0
            if call.status == "completed":
                daily_metrics[day_key]["successful"] += 1
        
        return dict(daily_metrics)
    
    def _calculate_trends(self, daily_metrics: Dict[str, Dict[str, Any]]) -> List[TrendAnalysis]:
        """Calculate trends from daily metrics"""
        trends = []
        
        if len(daily_metrics) < 2:
            return trends
        
        # Sort by date
        sorted_days = sorted(daily_metrics.keys())
        
        # Calculate call volume trend
        call_volumes = [daily_metrics[day]["calls"] for day in sorted_days]
        if len(call_volumes) >= 2:
            trend = self._calculate_trend_direction(call_volumes)
            trends.append(trend)
        
        return trends
    
    def _calculate_trend_direction(self, values: List[float]) -> TrendAnalysis:
        """Calculate trend direction and strength"""
        if len(values) < 2:
            return TrendAnalysis(
                metric="calls",
                trend_direction="stable",
                trend_strength=0.0,
                percentage_change=0.0,
                period_comparison="insufficient_data",
                confidence_level=0.0
            )
        
        # Calculate linear regression
        x = list(range(len(values)))
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, values)
        
        # Determine trend direction
        if slope > 0.1:
            direction = "up"
        elif slope < -0.1:
            direction = "down"
        else:
            direction = "stable"
        
        # Calculate percentage change
        percentage_change = ((values[-1] - values[0]) / values[0] * 100) if values[0] != 0 else 0
        
        return TrendAnalysis(
            metric="calls",
            trend_direction=direction,
            trend_strength=abs(r_value),
            percentage_change=percentage_change,
            period_comparison=f"{len(values)}_days",
            confidence_level=1 - p_value if p_value < 1 else 0
        )
    
    def _identify_peak_hours(self, call_logs: List[CallLog]) -> Dict[str, int]:
        """Identify peak calling hours"""
        hourly_counts = defaultdict(int)
        
        for call in call_logs:
            hour = call.start_time.hour
            hourly_counts[hour] += 1
        
        return dict(hourly_counts)
    
    def _analyze_call_types(self, call_logs: List[CallLog]) -> Dict[str, int]:
        """Analyze distribution of call types"""
        call_types = defaultdict(int)
        
        for call in call_logs:
            call_type = call.call_type or "unknown"
            call_types[call_type] += 1
        
        return dict(call_types)
    
    async def _analyze_single_customer(self, session: Session, customer: Customer) -> CustomerInsight:
        """Analyze a single customer's behavior"""
        # Calculate lifetime value
        orders = session.exec(
            select(Order).where(Order.customer_id == customer.id)
        ).all()
        lifetime_value = sum([order.total_amount for order in orders])
        
        # Calculate churn probability
        churn_probability = await self._calculate_churn_score(session, customer)
        
        # Calculate engagement score
        engagement_score = await self._calculate_engagement_score(session, customer)
        
        # Determine customer segment
        segment = await self._determine_customer_segment(session, customer)
        
        # Generate next best action
        next_best_action = self._generate_next_best_action(
            churn_probability, engagement_score, lifetime_value
        )
        
        return CustomerInsight(
            customer_id=customer.id,
            segment=segment,
            lifetime_value=lifetime_value,
            churn_probability=churn_probability,
            next_best_action=next_best_action,
            engagement_score=engagement_score,
            satisfaction_score=customer.satisfaction_score or 0.0
        )
    
    async def _calculate_churn_score(self, session: Session, customer: Customer) -> float:
        """Calculate customer churn probability"""
        # Get recent interactions
        recent_calls = session.exec(
            select(CallLog).where(
                and_(
                    CallLog.customer_id == customer.id,
                    CallLog.start_time >= datetime.utcnow() - timedelta(days=30)
                )
            )
        ).all()
        
        # Calculate factors
        days_since_last_interaction = (datetime.utcnow() - customer.last_interaction).days if customer.last_interaction else 365
        interaction_frequency = len(recent_calls)
        satisfaction_score = customer.satisfaction_score or 0.0
        
        # Simple churn scoring algorithm
        churn_score = 0.0
        
        # Days since last interaction (higher = more likely to churn)
        if days_since_last_interaction > 60:
            churn_score += 0.4
        elif days_since_last_interaction > 30:
            churn_score += 0.2
        
        # Interaction frequency (lower = more likely to churn)
        if interaction_frequency == 0:
            churn_score += 0.3
        elif interaction_frequency < 3:
            churn_score += 0.1
        
        # Satisfaction score (lower = more likely to churn)
        if satisfaction_score < 3.0:
            churn_score += 0.3
        elif satisfaction_score < 4.0:
            churn_score += 0.1
        
        return min(churn_score, 1.0)
    
    async def _calculate_engagement_score(self, session: Session, customer: Customer) -> float:
        """Calculate customer engagement score"""
        # Get interaction history
        calls = session.exec(
            select(CallLog).where(CallLog.customer_id == customer.id)
        ).all()
        
        orders = session.exec(
            select(Order).where(Order.customer_id == customer.id)
        ).all()
        
        # Calculate engagement factors
        total_interactions = len(calls)
        recent_interactions = len([call for call in calls if call.start_time >= datetime.utcnow() - timedelta(days=30)])
        total_orders = len(orders)
        
        # Simple engagement scoring
        engagement_score = 0.0
        
        if total_interactions > 10:
            engagement_score += 0.3
        elif total_interactions > 5:
            engagement_score += 0.2
        elif total_interactions > 0:
            engagement_score += 0.1
        
        if recent_interactions > 3:
            engagement_score += 0.3
        elif recent_interactions > 1:
            engagement_score += 0.2
        elif recent_interactions > 0:
            engagement_score += 0.1
        
        if total_orders > 5:
            engagement_score += 0.4
        elif total_orders > 1:
            engagement_score += 0.2
        elif total_orders > 0:
            engagement_score += 0.1
        
        return min(engagement_score, 1.0)
    
    async def _get_recent_interactions(self, session: Session, customer_id: str) -> Dict[str, Any]:
        """Get recent customer interactions"""
        recent_calls = session.exec(
            select(CallLog).where(
                and_(
                    CallLog.customer_id == customer_id,
                    CallLog.start_time >= datetime.utcnow() - timedelta(days=30)
                )
            ).order_by(CallLog.start_time.desc())
        ).all()
        
        return {
            "last_interaction": recent_calls[0].start_time if recent_calls else None,
            "frequency": len(recent_calls)
        }
    
    def _get_risk_level(self, churn_score: float) -> str:
        """Determine risk level from churn score"""
        if churn_score >= 0.7:
            return "high"
        elif churn_score >= 0.4:
            return "medium"
        else:
            return "low"
    
    def _get_retention_recommendations(self, churn_score: float, engagement_score: float) -> List[str]:
        """Generate retention recommendations"""
        recommendations = []
        
        if churn_score >= 0.7:
            recommendations.append("Immediate personal outreach required")
            recommendations.append("Offer special discount or incentive")
            recommendations.append("Schedule retention call")
        elif churn_score >= 0.4:
            recommendations.append("Send re-engagement campaign")
            recommendations.append("Offer product recommendations")
        
        if engagement_score < 0.3:
            recommendations.append("Increase touchpoint frequency")
            recommendations.append("Provide value-added content")
        
        return recommendations
    
    async def _apply_segmentation_criterion(
        self,
        session: Session,
        customer: Customer,
        criterion: SegmentCriteria
    ) -> str:
        """Apply segmentation criterion to customer"""
        if criterion == SegmentCriteria.VALUE:
            orders = session.exec(
                select(Order).where(Order.customer_id == customer.id)
            ).all()
            total_value = sum([order.total_amount for order in orders])
            
            if total_value >= 10000:
                return "high_value"
            elif total_value >= 1000:
                return "medium_value"
            else:
                return "low_value"
        
        elif criterion == SegmentCriteria.FREQUENCY:
            calls = session.exec(
                select(CallLog).where(CallLog.customer_id == customer.id)
            ).all()
            
            if len(calls) >= 20:
                return "high_frequency"
            elif len(calls) >= 5:
                return "medium_frequency"
            else:
                return "low_frequency"
        
        elif criterion == SegmentCriteria.RECENCY:
            if customer.last_interaction:
                days_since = (datetime.utcnow() - customer.last_interaction).days
                if days_since <= 7:
                    return "recent"
                elif days_since <= 30:
                    return "moderate"
                else:
                    return "dormant"
            else:
                return "dormant"
        
        return "unknown"
    
    async def _determine_customer_segment(self, session: Session, customer: Customer) -> str:
        """Determine overall customer segment"""
        value_segment = await self._apply_segmentation_criterion(session, customer, SegmentCriteria.VALUE)
        frequency_segment = await self._apply_segmentation_criterion(session, customer, SegmentCriteria.FREQUENCY)
        recency_segment = await self._apply_segmentation_criterion(session, customer, SegmentCriteria.RECENCY)
        
        # Combine segments into overall classification
        if value_segment == "high_value" and frequency_segment == "high_frequency":
            return "vip"
        elif value_segment == "high_value":
            return "high_value"
        elif frequency_segment == "high_frequency":
            return "frequent"
        elif recency_segment == "recent":
            return "active"
        else:
            return "standard"
    
    def _generate_next_best_action(
        self,
        churn_probability: float,
        engagement_score: float,
        lifetime_value: float
    ) -> str:
        """Generate next best action for customer"""
        if churn_probability >= 0.7:
            return "retention_call"
        elif churn_probability >= 0.4:
            return "re_engagement_campaign"
        elif engagement_score >= 0.7 and lifetime_value >= 1000:
            return "upsell_opportunity"
        elif engagement_score < 0.3:
            return "nurture_campaign"
        else:
            return "maintain_relationship"
    
    def _generate_revenue_forecast(self, orders: List[Order]) -> Dict[str, float]:
        """Generate revenue forecast based on historical data"""
        if len(orders) < 3:
            return {"next_month": 0.0, "next_quarter": 0.0}
        
        # Group orders by month
        monthly_revenue = defaultdict(float)
        for order in orders:
            month_key = order.created_at.strftime("%Y-%m")
            monthly_revenue[month_key] += order.total_amount
        
        # Calculate average monthly revenue
        revenues = list(monthly_revenue.values())
        avg_monthly_revenue = statistics.mean(revenues)
        
        # Simple forecast (could be enhanced with more sophisticated models)
        return {
            "next_month": avg_monthly_revenue,
            "next_quarter": avg_monthly_revenue * 3
        }
    
    def _calculate_campaign_roi(self, campaign: Campaign, orders: List[Order]) -> float:
        """Calculate campaign ROI"""
        total_revenue = sum([order.total_amount for order in orders])
        campaign_cost = campaign.budget or 0
        
        if campaign_cost == 0:
            return 0.0
        
        return ((total_revenue - campaign_cost) / campaign_cost) * 100


# Global analytics engine instance
analytics_engine = AnalyticsEngine()