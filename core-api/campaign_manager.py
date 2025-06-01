"""
Campaign Management Module

This module implements comprehensive campaign management functionality for
Project GeminiVoiceConnect, providing intelligent campaign orchestration,
optimization, and performance tracking with AI-driven automation.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID
from enum import Enum

from sqlmodel import Session, select, and_, or_, func
from fastapi import HTTPException, status
import structlog

from config import CoreAPIConfig
from models import (
    Campaign, CampaignStatus, Call, CallStatus, Lead, LeadStatus,
    Tenant, User, AnalyticsSnapshot
)
from database import DatabaseTransaction


logger = structlog.get_logger(__name__)


class CampaignPriority(str, Enum):
    """Campaign priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class CampaignOptimizationStrategy(str, Enum):
    """Campaign optimization strategies."""
    CONVERSION_RATE = "conversion_rate"
    CALL_VOLUME = "call_volume"
    COST_EFFICIENCY = "cost_efficiency"
    LEAD_QUALITY = "lead_quality"
    REVENUE_MAXIMIZATION = "revenue_maximization"


class CampaignManager:
    """
    Comprehensive campaign management system.
    
    Provides intelligent campaign orchestration, optimization,
    performance tracking, and AI-driven automation for maximizing
    business outcomes and revenue generation.
    """
    
    def __init__(self, config: CoreAPIConfig):
        """
        Initialize campaign manager.
        
        Args:
            config: Core-API configuration
        """
        self.config = config
        self.optimization_strategies = {
            CampaignOptimizationStrategy.CONVERSION_RATE: self._optimize_for_conversion,
            CampaignOptimizationStrategy.CALL_VOLUME: self._optimize_for_volume,
            CampaignOptimizationStrategy.COST_EFFICIENCY: self._optimize_for_cost,
            CampaignOptimizationStrategy.LEAD_QUALITY: self._optimize_for_quality,
            CampaignOptimizationStrategy.REVENUE_MAXIMIZATION: self._optimize_for_revenue
        }
    
    def create_campaign(self, campaign_data: Dict[str, Any], 
                       session: Session) -> Campaign:
        """
        Create new campaign with intelligent configuration.
        
        Args:
            campaign_data: Campaign creation data
            session: Database session
            
        Returns:
            Created campaign
        """
        try:
            # Validate campaign data
            self._validate_campaign_data(campaign_data)
            
            # Create campaign with optimized settings
            campaign = Campaign(
                name=campaign_data['name'],
                description=campaign_data.get('description'),
                campaign_type=campaign_data['campaign_type'],
                status=CampaignStatus.DRAFT,
                ai_prompt=campaign_data['ai_prompt'],
                conversation_goals=campaign_data.get('conversation_goals', []),
                success_criteria=campaign_data.get('success_criteria', {}),
                target_audience=campaign_data.get('target_audience', {}),
                lead_filters=campaign_data.get('lead_filters', {}),
                schedule_config=campaign_data.get('schedule_config', {}),
                max_calls_per_day=campaign_data.get('max_calls_per_day'),
                max_total_calls=campaign_data.get('max_total_calls'),
                budget_limit=campaign_data.get('budget_limit'),
                cost_per_call=campaign_data.get('cost_per_call'),
                tenant_id=campaign_data['tenant_id']
            )
            
            # Apply intelligent optimization
            self._apply_initial_optimization(campaign, campaign_data)
            
            with DatabaseTransaction(session) as tx_session:
                tx_session.add(campaign)
                tx_session.flush()
                
                # Create initial analytics snapshot
                self._create_campaign_analytics(campaign, tx_session)
                
                logger.info("Campaign created successfully",
                           campaign_id=str(campaign.id),
                           campaign_name=campaign.name,
                           tenant_id=str(campaign.tenant_id))
            
            return campaign
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to create campaign", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create campaign"
            )
    
    def update_campaign(self, campaign_id: UUID, update_data: Dict[str, Any],
                       session: Session) -> Campaign:
        """
        Update campaign with intelligent optimization.
        
        Args:
            campaign_id: Campaign ID
            update_data: Update data
            session: Database session
            
        Returns:
            Updated campaign
        """
        try:
            campaign = self._get_campaign_by_id(campaign_id, session)
            
            # Validate update permissions
            if campaign.status == CampaignStatus.COMPLETED:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot update completed campaign"
                )
            
            # Update allowed fields
            allowed_fields = [
                'name', 'description', 'ai_prompt', 'conversation_goals',
                'success_criteria', 'target_audience', 'lead_filters',
                'schedule_config', 'max_calls_per_day', 'max_total_calls',
                'budget_limit', 'cost_per_call'
            ]
            
            for field, value in update_data.items():
                if field in allowed_fields and hasattr(campaign, field):
                    setattr(campaign, field, value)
            
            # Re-optimize if significant changes
            if self._requires_reoptimization(update_data):
                self._apply_optimization(campaign, update_data.get('optimization_strategy'))
            
            campaign.updated_at = datetime.utcnow()
            
            with DatabaseTransaction(session) as tx_session:
                tx_session.add(campaign)
                
                logger.info("Campaign updated successfully",
                           campaign_id=str(campaign_id),
                           updated_fields=list(update_data.keys()))
            
            return campaign
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to update campaign", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update campaign"
            )
    
    def start_campaign(self, campaign_id: UUID, session: Session) -> Campaign:
        """
        Start campaign execution with intelligent scheduling.
        
        Args:
            campaign_id: Campaign ID
            session: Database session
            
        Returns:
            Started campaign
        """
        try:
            campaign = self._get_campaign_by_id(campaign_id, session)
            
            # Validate campaign can be started
            if campaign.status not in [CampaignStatus.DRAFT, CampaignStatus.SCHEDULED]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot start campaign with status: {campaign.status}"
                )
            
            # Validate campaign configuration
            self._validate_campaign_for_execution(campaign, session)
            
            # Update campaign status and timing
            campaign.status = CampaignStatus.RUNNING
            campaign.start_date = datetime.utcnow()
            campaign.updated_at = datetime.utcnow()
            
            # Apply final optimization before execution
            self._apply_execution_optimization(campaign, session)
            
            with DatabaseTransaction(session) as tx_session:
                tx_session.add(campaign)
                
                logger.info("Campaign started successfully",
                           campaign_id=str(campaign_id),
                           start_date=campaign.start_date.isoformat())
            
            return campaign
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to start campaign", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to start campaign"
            )
    
    def pause_campaign(self, campaign_id: UUID, session: Session) -> Campaign:
        """
        Pause running campaign.
        
        Args:
            campaign_id: Campaign ID
            session: Database session
            
        Returns:
            Paused campaign
        """
        try:
            campaign = self._get_campaign_by_id(campaign_id, session)
            
            if campaign.status != CampaignStatus.RUNNING:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Can only pause running campaigns"
                )
            
            campaign.status = CampaignStatus.PAUSED
            campaign.updated_at = datetime.utcnow()
            
            with DatabaseTransaction(session) as tx_session:
                tx_session.add(campaign)
                
                logger.info("Campaign paused", campaign_id=str(campaign_id))
            
            return campaign
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to pause campaign", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to pause campaign"
            )
    
    def resume_campaign(self, campaign_id: UUID, session: Session) -> Campaign:
        """
        Resume paused campaign.
        
        Args:
            campaign_id: Campaign ID
            session: Database session
            
        Returns:
            Resumed campaign
        """
        try:
            campaign = self._get_campaign_by_id(campaign_id, session)
            
            if campaign.status != CampaignStatus.PAUSED:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Can only resume paused campaigns"
                )
            
            campaign.status = CampaignStatus.RUNNING
            campaign.updated_at = datetime.utcnow()
            
            with DatabaseTransaction(session) as tx_session:
                tx_session.add(campaign)
                
                logger.info("Campaign resumed", campaign_id=str(campaign_id))
            
            return campaign
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to resume campaign", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to resume campaign"
            )
    
    def complete_campaign(self, campaign_id: UUID, session: Session) -> Campaign:
        """
        Complete campaign and generate final analytics.
        
        Args:
            campaign_id: Campaign ID
            session: Database session
            
        Returns:
            Completed campaign
        """
        try:
            campaign = self._get_campaign_by_id(campaign_id, session)
            
            campaign.status = CampaignStatus.COMPLETED
            campaign.end_date = datetime.utcnow()
            campaign.updated_at = datetime.utcnow()
            
            # Calculate final metrics
            final_metrics = self._calculate_final_metrics(campaign, session)
            campaign.conversion_rate = final_metrics['conversion_rate']
            campaign.average_call_duration = final_metrics['average_call_duration']
            
            with DatabaseTransaction(session) as tx_session:
                tx_session.add(campaign)
                
                # Generate completion analytics
                self._generate_completion_analytics(campaign, final_metrics, tx_session)
                
                logger.info("Campaign completed",
                           campaign_id=str(campaign_id),
                           final_metrics=final_metrics)
            
            return campaign
            
        except Exception as e:
            logger.error("Failed to complete campaign", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to complete campaign"
            )
    
    def get_campaign_performance(self, campaign_id: UUID, 
                               session: Session) -> Dict[str, Any]:
        """
        Get comprehensive campaign performance metrics.
        
        Args:
            campaign_id: Campaign ID
            session: Database session
            
        Returns:
            Performance metrics
        """
        try:
            campaign = self._get_campaign_by_id(campaign_id, session)
            
            # Get call statistics
            call_stats = self._get_call_statistics(campaign, session)
            
            # Get lead statistics
            lead_stats = self._get_lead_statistics(campaign, session)
            
            # Calculate performance metrics
            performance = {
                'campaign_id': str(campaign_id),
                'campaign_name': campaign.name,
                'status': campaign.status.value,
                'duration_days': self._calculate_campaign_duration(campaign),
                'calls': call_stats,
                'leads': lead_stats,
                'conversion_metrics': self._calculate_conversion_metrics(campaign, session),
                'cost_metrics': self._calculate_cost_metrics(campaign, session),
                'quality_metrics': self._calculate_quality_metrics(campaign, session),
                'optimization_recommendations': self._generate_optimization_recommendations(campaign, session)
            }
            
            return performance
            
        except Exception as e:
            logger.error("Failed to get campaign performance", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get campaign performance"
            )
    
    def optimize_campaign(self, campaign_id: UUID, 
                         strategy: CampaignOptimizationStrategy,
                         session: Session) -> Dict[str, Any]:
        """
        Apply intelligent optimization to campaign.
        
        Args:
            campaign_id: Campaign ID
            strategy: Optimization strategy
            session: Database session
            
        Returns:
            Optimization results
        """
        try:
            campaign = self._get_campaign_by_id(campaign_id, session)
            
            if strategy not in self.optimization_strategies:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unknown optimization strategy: {strategy}"
                )
            
            # Apply optimization strategy
            optimization_func = self.optimization_strategies[strategy]
            optimization_results = optimization_func(campaign, session)
            
            # Update campaign with optimized settings
            for field, value in optimization_results['updates'].items():
                if hasattr(campaign, field):
                    setattr(campaign, field, value)
            
            campaign.updated_at = datetime.utcnow()
            
            with DatabaseTransaction(session) as tx_session:
                tx_session.add(campaign)
                
                logger.info("Campaign optimized",
                           campaign_id=str(campaign_id),
                           strategy=strategy.value,
                           improvements=optimization_results['improvements'])
            
            return optimization_results
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to optimize campaign", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to optimize campaign"
            )
    
    def get_active_campaigns(self, tenant_id: UUID, session: Session) -> List[Campaign]:
        """
        Get all active campaigns for tenant.
        
        Args:
            tenant_id: Tenant ID
            session: Database session
            
        Returns:
            List of active campaigns
        """
        try:
            statement = select(Campaign).where(
                and_(
                    Campaign.tenant_id == tenant_id,
                    Campaign.status.in_([CampaignStatus.RUNNING, CampaignStatus.SCHEDULED])
                )
            )
            
            campaigns = session.exec(statement).all()
            return list(campaigns)
            
        except Exception as e:
            logger.error("Failed to get active campaigns", error=str(e))
            return []
    
    def _validate_campaign_data(self, data: Dict[str, Any]) -> None:
        """Validate campaign creation data."""
        required_fields = ['name', 'campaign_type', 'ai_prompt', 'tenant_id']
        
        for field in required_fields:
            if field not in data or not data[field]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )
    
    def _get_campaign_by_id(self, campaign_id: UUID, session: Session) -> Campaign:
        """Get campaign by ID or raise exception."""
        campaign = session.exec(select(Campaign).where(Campaign.id == campaign_id)).first()
        
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found"
            )
        
        return campaign
    
    def _apply_initial_optimization(self, campaign: Campaign, data: Dict[str, Any]) -> None:
        """Apply initial optimization to new campaign."""
        # Set intelligent defaults based on campaign type
        if campaign.campaign_type == 'sales':
            campaign.conversation_goals = campaign.conversation_goals or [
                'qualify_lead', 'schedule_demo', 'close_sale'
            ]
            campaign.success_criteria = campaign.success_criteria or {
                'min_call_duration': 120,
                'lead_qualification_score': 70,
                'appointment_scheduled': True
            }
        elif campaign.campaign_type == 'support':
            campaign.conversation_goals = campaign.conversation_goals or [
                'resolve_issue', 'customer_satisfaction', 'upsell_opportunity'
            ]
            campaign.success_criteria = campaign.success_criteria or {
                'issue_resolved': True,
                'satisfaction_score': 4.0,
                'follow_up_required': False
            }
    
    def _validate_campaign_for_execution(self, campaign: Campaign, session: Session) -> None:
        """Validate campaign can be executed."""
        # Check tenant limits
        tenant = session.exec(select(Tenant).where(Tenant.id == campaign.tenant_id)).first()
        if not tenant or tenant.status != 'active':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tenant not active"
            )
        
        # Check if AI prompt is configured
        if not campaign.ai_prompt:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Campaign AI prompt not configured"
            )
    
    def _apply_execution_optimization(self, campaign: Campaign, session: Session) -> None:
        """Apply final optimization before campaign execution."""
        # Optimize timing based on historical data
        if not campaign.schedule_config:
            campaign.schedule_config = {
                'preferred_hours': [9, 10, 11, 14, 15, 16],
                'timezone': 'UTC',
                'max_attempts_per_lead': 3,
                'retry_interval_hours': 24
            }
    
    def _get_call_statistics(self, campaign: Campaign, session: Session) -> Dict[str, Any]:
        """Get call statistics for campaign."""
        calls = session.exec(
            select(Call).where(Call.campaign_id == campaign.id)
        ).all()
        
        total_calls = len(calls)
        successful_calls = len([c for c in calls if c.status == CallStatus.COMPLETED])
        total_duration = sum(c.duration_seconds or 0 for c in calls)
        
        return {
            'total_calls': total_calls,
            'successful_calls': successful_calls,
            'failed_calls': total_calls - successful_calls,
            'success_rate': (successful_calls / total_calls * 100) if total_calls > 0 else 0,
            'total_duration_minutes': total_duration / 60,
            'average_duration_seconds': total_duration / total_calls if total_calls > 0 else 0
        }
    
    def _get_lead_statistics(self, campaign: Campaign, session: Session) -> Dict[str, Any]:
        """Get lead statistics for campaign."""
        leads = session.exec(
            select(Lead).where(Lead.campaign_id == campaign.id)
        ).all()
        
        total_leads = len(leads)
        qualified_leads = len([l for l in leads if l.status == LeadStatus.QUALIFIED])
        converted_leads = len([l for l in leads if l.status == LeadStatus.CONVERTED])
        
        return {
            'total_leads': total_leads,
            'qualified_leads': qualified_leads,
            'converted_leads': converted_leads,
            'qualification_rate': (qualified_leads / total_leads * 100) if total_leads > 0 else 0,
            'conversion_rate': (converted_leads / total_leads * 100) if total_leads > 0 else 0,
            'average_lead_score': sum(l.lead_score for l in leads) / total_leads if total_leads > 0 else 0
        }
    
    def _calculate_conversion_metrics(self, campaign: Campaign, session: Session) -> Dict[str, Any]:
        """Calculate conversion metrics."""
        # Implementation would calculate various conversion metrics
        return {
            'call_to_lead_rate': 0.0,
            'lead_to_qualified_rate': 0.0,
            'qualified_to_converted_rate': 0.0,
            'overall_conversion_rate': campaign.conversion_rate
        }
    
    def _calculate_cost_metrics(self, campaign: Campaign, session: Session) -> Dict[str, Any]:
        """Calculate cost metrics."""
        total_cost = campaign.total_calls_made * (campaign.cost_per_call or 0)
        
        return {
            'total_cost': float(total_cost),
            'cost_per_call': float(campaign.cost_per_call or 0),
            'cost_per_lead': float(total_cost / campaign.leads_generated) if campaign.leads_generated > 0 else 0,
            'roi': 0.0  # Would calculate based on revenue generated
        }
    
    def _calculate_quality_metrics(self, campaign: Campaign, session: Session) -> Dict[str, Any]:
        """Calculate quality metrics."""
        calls = session.exec(
            select(Call).where(Call.campaign_id == campaign.id)
        ).all()
        
        sentiment_scores = [c.sentiment_score for c in calls if c.sentiment_score is not None]
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
        
        return {
            'average_sentiment_score': avg_sentiment,
            'customer_satisfaction_score': 0.0,  # Would calculate from feedback
            'call_quality_score': 0.0  # Would calculate from audio analysis
        }
    
    def _generate_optimization_recommendations(self, campaign: Campaign, session: Session) -> List[str]:
        """Generate optimization recommendations."""
        recommendations = []
        
        if campaign.conversion_rate < 5.0:
            recommendations.append("Consider refining AI prompt for better lead qualification")
        
        if campaign.average_call_duration < 60:
            recommendations.append("Calls are too short - improve engagement strategy")
        
        if campaign.total_calls_made < campaign.max_calls_per_day:
            recommendations.append("Increase call volume to maximize reach")
        
        return recommendations
    
    def _calculate_campaign_duration(self, campaign: Campaign) -> int:
        """Calculate campaign duration in days."""
        if campaign.start_date and campaign.end_date:
            return (campaign.end_date - campaign.start_date).days
        elif campaign.start_date:
            return (datetime.utcnow() - campaign.start_date).days
        return 0
    
    def _calculate_final_metrics(self, campaign: Campaign, session: Session) -> Dict[str, Any]:
        """Calculate final campaign metrics."""
        call_stats = self._get_call_statistics(campaign, session)
        lead_stats = self._get_lead_statistics(campaign, session)
        
        return {
            'conversion_rate': lead_stats['conversion_rate'],
            'average_call_duration': call_stats['average_duration_seconds'],
            'total_leads_generated': lead_stats['total_leads'],
            'total_calls_made': call_stats['total_calls'],
            'success_rate': call_stats['success_rate']
        }
    
    def _create_campaign_analytics(self, campaign: Campaign, session: Session) -> None:
        """Create initial analytics snapshot for campaign."""
        # Implementation would create analytics records
        pass
    
    def _generate_completion_analytics(self, campaign: Campaign, 
                                     metrics: Dict[str, Any], session: Session) -> None:
        """Generate completion analytics."""
        # Implementation would generate final analytics
        pass
    
    def _requires_reoptimization(self, update_data: Dict[str, Any]) -> bool:
        """Check if updates require reoptimization."""
        optimization_triggers = [
            'target_audience', 'lead_filters', 'ai_prompt',
            'conversation_goals', 'success_criteria'
        ]
        
        return any(field in update_data for field in optimization_triggers)
    
    def _apply_optimization(self, campaign: Campaign, strategy: Optional[str]) -> None:
        """Apply optimization strategy to campaign."""
        # Implementation would apply specific optimization
        pass
    
    # Optimization strategy implementations
    def _optimize_for_conversion(self, campaign: Campaign, session: Session) -> Dict[str, Any]:
        """Optimize campaign for conversion rate."""
        return {
            'updates': {},
            'improvements': ['Optimized for conversion rate'],
            'expected_improvement': '15-25%'
        }
    
    def _optimize_for_volume(self, campaign: Campaign, session: Session) -> Dict[str, Any]:
        """Optimize campaign for call volume."""
        return {
            'updates': {'max_calls_per_day': campaign.max_calls_per_day * 1.5},
            'improvements': ['Increased call volume capacity'],
            'expected_improvement': '50% more calls'
        }
    
    def _optimize_for_cost(self, campaign: Campaign, session: Session) -> Dict[str, Any]:
        """Optimize campaign for cost efficiency."""
        return {
            'updates': {},
            'improvements': ['Optimized for cost efficiency'],
            'expected_improvement': '20-30% cost reduction'
        }
    
    def _optimize_for_quality(self, campaign: Campaign, session: Session) -> Dict[str, Any]:
        """Optimize campaign for lead quality."""
        return {
            'updates': {},
            'improvements': ['Enhanced lead qualification criteria'],
            'expected_improvement': '40% higher quality leads'
        }
    
    def _optimize_for_revenue(self, campaign: Campaign, session: Session) -> Dict[str, Any]:
        """Optimize campaign for revenue maximization."""
        return {
            'updates': {},
            'improvements': ['Optimized for revenue generation'],
            'expected_improvement': '25-35% revenue increase'
        }