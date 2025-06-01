"""
Tenant Management Module

This module provides comprehensive tenant management functionality for
Project GeminiVoiceConnect's multi-tenant SaaS architecture, implementing
tenant lifecycle management, resource allocation, and billing integration.
"""

import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, List, Optional
from uuid import UUID

from sqlmodel import Session, select, and_, or_
from fastapi import HTTPException, status
import structlog

from config import CoreAPIConfig
from models import (
    Tenant, User, TenantStatus, UserRole, Campaign, Call, Lead, 
    Integration, Payment, AnalyticsSnapshot
)
from database import DatabaseTransaction


logger = structlog.get_logger(__name__)


class TenantManager:
    """
    Comprehensive tenant management system.
    
    Provides tenant lifecycle management, resource allocation,
    usage monitoring, and billing integration for multi-tenant
    SaaS operations.
    """
    
    def __init__(self, config: CoreAPIConfig):
        """
        Initialize tenant manager.
        
        Args:
            config: Core-API configuration
        """
        self.config = config
        self.default_limits = config.default_tenant_limits
    
    def create_tenant(self, tenant_data: Dict[str, Any], session: Session) -> Tenant:
        """
        Create new tenant with default configuration.
        
        Args:
            tenant_data: Tenant creation data
            session: Database session
            
        Returns:
            Created tenant
        """
        try:
            # Validate tenant data
            self._validate_tenant_data(tenant_data)
            
            # Check if slug is unique
            existing_tenant = session.exec(
                select(Tenant).where(Tenant.slug == tenant_data['slug'])
            ).first()
            
            if existing_tenant:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Tenant slug already exists"
                )
            
            # Create tenant with default settings
            tenant = Tenant(
                name=tenant_data['name'],
                slug=tenant_data['slug'],
                email=tenant_data['email'],
                phone=tenant_data.get('phone'),
                address=tenant_data.get('address'),
                domain=tenant_data.get('domain'),
                industry=tenant_data.get('industry'),
                company_size=tenant_data.get('company_size'),
                subscription_plan=tenant_data.get('subscription_plan', 'starter'),
                status=TenantStatus.TRIAL,
                trial_ends_at=datetime.utcnow() + timedelta(days=14),
                **self.default_limits,
                features_enabled=self._get_default_features(
                    tenant_data.get('subscription_plan', 'starter')
                )
            )
            
            with DatabaseTransaction(session) as tx_session:
                tx_session.add(tenant)
                tx_session.flush()  # Get tenant ID
                
                # Create default admin user
                admin_user = self._create_admin_user(tenant, tenant_data, tx_session)
                
                # Initialize tenant resources
                self._initialize_tenant_resources(tenant, tx_session)
                
                logger.info("Tenant created successfully",
                           tenant_id=str(tenant.id),
                           tenant_name=tenant.name,
                           admin_user_id=str(admin_user.id))
            
            return tenant
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to create tenant", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create tenant"
            )
    
    def update_tenant(self, tenant_id: UUID, update_data: Dict[str, Any], 
                     session: Session) -> Tenant:
        """
        Update tenant information and configuration.
        
        Args:
            tenant_id: Tenant ID
            update_data: Update data
            session: Database session
            
        Returns:
            Updated tenant
        """
        try:
            tenant = self._get_tenant_by_id(tenant_id, session)
            
            # Update allowed fields
            allowed_fields = [
                'name', 'email', 'phone', 'address', 'domain', 'industry',
                'company_size', 'timezone', 'currency', 'billing_email',
                'gemini_api_key', 'custom_prompts', 'ai_settings'
            ]
            
            for field, value in update_data.items():
                if field in allowed_fields and hasattr(tenant, field):
                    setattr(tenant, field, value)
            
            tenant.updated_at = datetime.utcnow()
            
            with DatabaseTransaction(session) as tx_session:
                tx_session.add(tenant)
                
                logger.info("Tenant updated successfully",
                           tenant_id=str(tenant_id),
                           updated_fields=list(update_data.keys()))
            
            return tenant
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to update tenant", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update tenant"
            )
    
    def update_tenant_limits(self, tenant_id: UUID, limits: Dict[str, int], 
                           session: Session) -> Tenant:
        """
        Update tenant resource limits.
        
        Args:
            tenant_id: Tenant ID
            limits: New resource limits
            session: Database session
            
        Returns:
            Updated tenant
        """
        try:
            tenant = self._get_tenant_by_id(tenant_id, session)
            
            # Update limits
            limit_fields = [
                'max_concurrent_calls', 'max_daily_calls', 'max_sms_per_day',
                'max_users', 'max_modems'
            ]
            
            for field, value in limits.items():
                if field in limit_fields and hasattr(tenant, field):
                    setattr(tenant, field, value)
            
            tenant.updated_at = datetime.utcnow()
            
            with DatabaseTransaction(session) as tx_session:
                tx_session.add(tenant)
                
                logger.info("Tenant limits updated",
                           tenant_id=str(tenant_id),
                           new_limits=limits)
            
            return tenant
            
        except Exception as e:
            logger.error("Failed to update tenant limits", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update tenant limits"
            )
    
    def update_subscription(self, tenant_id: UUID, plan: str, 
                          session: Session) -> Tenant:
        """
        Update tenant subscription plan.
        
        Args:
            tenant_id: Tenant ID
            plan: New subscription plan
            session: Database session
            
        Returns:
            Updated tenant
        """
        try:
            tenant = self._get_tenant_by_id(tenant_id, session)
            
            # Get plan configuration
            plan_config = self._get_plan_configuration(plan)
            
            # Update subscription
            tenant.subscription_plan = plan
            tenant.status = TenantStatus.ACTIVE
            tenant.trial_ends_at = None
            
            # Update limits based on plan
            for field, value in plan_config['limits'].items():
                setattr(tenant, field, value)
            
            # Update features
            tenant.features_enabled = plan_config['features']
            tenant.updated_at = datetime.utcnow()
            
            with DatabaseTransaction(session) as tx_session:
                tx_session.add(tenant)
                
                logger.info("Tenant subscription updated",
                           tenant_id=str(tenant_id),
                           new_plan=plan)
            
            return tenant
            
        except Exception as e:
            logger.error("Failed to update subscription", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update subscription"
            )
    
    def suspend_tenant(self, tenant_id: UUID, reason: str, session: Session) -> Tenant:
        """
        Suspend tenant account.
        
        Args:
            tenant_id: Tenant ID
            reason: Suspension reason
            session: Database session
            
        Returns:
            Suspended tenant
        """
        try:
            tenant = self._get_tenant_by_id(tenant_id, session)
            
            tenant.status = TenantStatus.SUSPENDED
            tenant.updated_at = datetime.utcnow()
            
            with DatabaseTransaction(session) as tx_session:
                tx_session.add(tenant)
                
                # Deactivate all users
                users = tx_session.exec(
                    select(User).where(User.tenant_id == tenant_id)
                ).all()
                
                for user in users:
                    user.is_active = False
                    tx_session.add(user)
                
                logger.info("Tenant suspended",
                           tenant_id=str(tenant_id),
                           reason=reason)
            
            return tenant
            
        except Exception as e:
            logger.error("Failed to suspend tenant", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to suspend tenant"
            )
    
    def reactivate_tenant(self, tenant_id: UUID, session: Session) -> Tenant:
        """
        Reactivate suspended tenant.
        
        Args:
            tenant_id: Tenant ID
            session: Database session
            
        Returns:
            Reactivated tenant
        """
        try:
            tenant = self._get_tenant_by_id(tenant_id, session)
            
            if tenant.status != TenantStatus.SUSPENDED:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Tenant is not suspended"
                )
            
            tenant.status = TenantStatus.ACTIVE
            tenant.updated_at = datetime.utcnow()
            
            with DatabaseTransaction(session) as tx_session:
                tx_session.add(tenant)
                
                # Reactivate admin users
                admin_users = tx_session.exec(
                    select(User).where(
                        and_(
                            User.tenant_id == tenant_id,
                            User.role == UserRole.TENANT_ADMIN
                        )
                    )
                ).all()
                
                for user in admin_users:
                    user.is_active = True
                    tx_session.add(user)
                
                logger.info("Tenant reactivated", tenant_id=str(tenant_id))
            
            return tenant
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to reactivate tenant", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to reactivate tenant"
            )
    
    def get_tenant_usage(self, tenant_id: UUID, session: Session) -> Dict[str, Any]:
        """
        Get tenant resource usage statistics.
        
        Args:
            tenant_id: Tenant ID
            session: Database session
            
        Returns:
            Usage statistics
        """
        try:
            tenant = self._get_tenant_by_id(tenant_id, session)
            
            # Get current usage
            today = datetime.utcnow().date()
            
            # Call usage
            daily_calls = session.exec(
                select(Call).where(
                    and_(
                        Call.tenant_id == tenant_id,
                        Call.initiated_at >= today
                    )
                )
            ).all()
            
            # SMS usage (would need SMS model)
            # For now, return placeholder
            daily_sms = 0
            
            # User count
            user_count = session.exec(
                select(User).where(User.tenant_id == tenant_id)
            ).count()
            
            # Active campaigns
            active_campaigns = session.exec(
                select(Campaign).where(
                    and_(
                        Campaign.tenant_id == tenant_id,
                        Campaign.status.in_(['running', 'scheduled'])
                    )
                )
            ).count()
            
            usage = {
                'daily_calls': {
                    'used': len(daily_calls),
                    'limit': tenant.max_daily_calls,
                    'percentage': (len(daily_calls) / tenant.max_daily_calls) * 100
                },
                'daily_sms': {
                    'used': daily_sms,
                    'limit': tenant.max_sms_per_day,
                    'percentage': (daily_sms / tenant.max_sms_per_day) * 100
                },
                'users': {
                    'used': user_count,
                    'limit': tenant.max_users,
                    'percentage': (user_count / tenant.max_users) * 100
                },
                'active_campaigns': active_campaigns,
                'subscription_plan': tenant.subscription_plan,
                'status': tenant.status.value
            }
            
            return usage
            
        except Exception as e:
            logger.error("Failed to get tenant usage", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get tenant usage"
            )
    
    def check_usage_limits(self, tenant_id: UUID, resource_type: str, 
                          session: Session) -> bool:
        """
        Check if tenant can use more of a specific resource.
        
        Args:
            tenant_id: Tenant ID
            resource_type: Type of resource to check
            session: Database session
            
        Returns:
            True if usage is within limits
        """
        try:
            usage = self.get_tenant_usage(tenant_id, session)
            
            if resource_type == 'calls':
                return usage['daily_calls']['percentage'] < 100
            elif resource_type == 'sms':
                return usage['daily_sms']['percentage'] < 100
            elif resource_type == 'users':
                return usage['users']['percentage'] < 100
            
            return True
            
        except Exception as e:
            logger.error("Failed to check usage limits", error=str(e))
            return False
    
    def _validate_tenant_data(self, data: Dict[str, Any]) -> None:
        """Validate tenant creation data."""
        required_fields = ['name', 'slug', 'email']
        
        for field in required_fields:
            if field not in data or not data[field]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )
        
        # Validate slug format
        slug = data['slug']
        if not slug.isalnum() or len(slug) < 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Slug must be alphanumeric and at least 3 characters"
            )
    
    def _get_tenant_by_id(self, tenant_id: UUID, session: Session) -> Tenant:
        """Get tenant by ID or raise exception."""
        tenant = session.exec(select(Tenant).where(Tenant.id == tenant_id)).first()
        
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )
        
        return tenant
    
    def _create_admin_user(self, tenant: Tenant, tenant_data: Dict[str, Any], 
                          session: Session) -> User:
        """Create default admin user for tenant."""
        from auth import AuthManager
        
        auth_manager = AuthManager(self.config)
        
        admin_data = tenant_data.get('admin_user', {})
        
        admin_user = User(
            email=admin_data.get('email', tenant.email),
            username=admin_data.get('username', f"{tenant.slug}_admin"),
            first_name=admin_data.get('first_name', 'Admin'),
            last_name=admin_data.get('last_name', 'User'),
            password_hash=auth_manager.hash_password(
                admin_data.get('password', 'changeme123')
            ),
            role=UserRole.TENANT_ADMIN,
            tenant_id=tenant.id,
            is_active=True,
            is_verified=True
        )
        
        session.add(admin_user)
        return admin_user
    
    def _initialize_tenant_resources(self, tenant: Tenant, session: Session) -> None:
        """Initialize default resources for new tenant."""
        # Create default analytics snapshot
        snapshot = AnalyticsSnapshot(
            tenant_id=tenant.id,
            snapshot_date=datetime.utcnow().date()
        )
        session.add(snapshot)
    
    def _get_default_features(self, plan: str) -> Dict[str, bool]:
        """Get default features for subscription plan."""
        features_map = {
            'starter': {
                'healthcare_module': False,
                'legal_module': False,
                'real_estate_module': False,
                'home_services_module': False,
                'advanced_analytics': False,
                'custom_integrations': False,
                'priority_support': False
            },
            'professional': {
                'healthcare_module': True,
                'legal_module': True,
                'real_estate_module': True,
                'home_services_module': True,
                'advanced_analytics': True,
                'custom_integrations': False,
                'priority_support': False
            },
            'enterprise': {
                'healthcare_module': True,
                'legal_module': True,
                'real_estate_module': True,
                'home_services_module': True,
                'advanced_analytics': True,
                'custom_integrations': True,
                'priority_support': True
            }
        }
        
        return features_map.get(plan, features_map['starter'])
    
    def _get_plan_configuration(self, plan: str) -> Dict[str, Any]:
        """Get configuration for subscription plan."""
        plans = {
            'starter': {
                'limits': {
                    'max_concurrent_calls': 10,
                    'max_daily_calls': 1000,
                    'max_sms_per_day': 1000,
                    'max_users': 5,
                    'max_modems': 5
                },
                'features': self._get_default_features('starter')
            },
            'professional': {
                'limits': {
                    'max_concurrent_calls': 50,
                    'max_daily_calls': 5000,
                    'max_sms_per_day': 5000,
                    'max_users': 25,
                    'max_modems': 25
                },
                'features': self._get_default_features('professional')
            },
            'enterprise': {
                'limits': {
                    'max_concurrent_calls': 100,
                    'max_daily_calls': 10000,
                    'max_sms_per_day': 10000,
                    'max_users': 100,
                    'max_modems': 80
                },
                'features': self._get_default_features('enterprise')
            }
        }
        
        return plans.get(plan, plans['starter'])