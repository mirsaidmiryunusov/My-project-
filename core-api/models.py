"""
Database Models Module

This module defines comprehensive database models for Project GeminiVoiceConnect,
implementing sophisticated business entities, relationships, and data structures
for multi-tenant SaaS operations, revenue optimization, and AI-driven automation.
"""

from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Dict, Any, Union
from uuid import UUID, uuid4

from sqlmodel import SQLModel, Field, Relationship, Column, JSON, Text
from sqlalchemy import Index, UniqueConstraint, CheckConstraint
from pydantic import validator, EmailStr
import structlog


logger = structlog.get_logger(__name__)


# Enums for type safety and validation
class UserRole(str, Enum):
    """User role enumeration."""
    SUPER_ADMIN = "super_admin"
    TENANT_ADMIN = "tenant_admin"
    MANAGER = "manager"
    AGENT = "agent"
    VIEWER = "viewer"


class TenantStatus(str, Enum):
    """Tenant status enumeration."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    CANCELLED = "cancelled"


class CallStatus(str, Enum):
    """Call status enumeration."""
    INITIATED = "initiated"
    RINGING = "ringing"
    ANSWERED = "answered"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BUSY = "busy"
    NO_ANSWER = "no_answer"
    CANCELLED = "cancelled"


class CallDirection(str, Enum):
    """Call direction enumeration."""
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class CampaignStatus(str, Enum):
    """Campaign status enumeration."""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class LeadStatus(str, Enum):
    """Lead status enumeration."""
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    UNQUALIFIED = "unqualified"
    CONVERTED = "converted"
    LOST = "lost"


class PaymentStatus(str, Enum):
    """Payment status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class IntegrationType(str, Enum):
    """Integration type enumeration."""
    CRM = "crm"
    ECOMMERCE = "ecommerce"
    PAYMENT = "payment"
    COMMUNICATION = "communication"
    ANALYTICS = "analytics"
    CUSTOM = "custom"


# Base Models
class TimestampMixin(SQLModel):
    """Mixin for timestamp fields."""
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class UUIDMixin(SQLModel):
    """Mixin for UUID primary key."""
    id: UUID = Field(default_factory=uuid4, primary_key=True)


# Core Business Models
class Tenant(UUIDMixin, TimestampMixin, table=True):
    """
    Tenant model for multi-tenant SaaS architecture.
    
    Represents individual customer organizations with complete
    isolation and resource management.
    """
    __tablename__ = "tenants"
    
    # Basic Information
    name: str = Field(max_length=255, nullable=False)
    slug: str = Field(max_length=100, nullable=False, unique=True)
    domain: Optional[str] = Field(max_length=255, nullable=True)
    
    # Contact Information
    email: EmailStr = Field(nullable=False)
    phone: Optional[str] = Field(max_length=20, nullable=True)
    address: Optional[str] = Field(max_length=500, nullable=True)
    
    # Status and Configuration
    status: TenantStatus = Field(default=TenantStatus.TRIAL, nullable=False)
    subscription_plan: str = Field(max_length=50, default="starter", nullable=False)
    trial_ends_at: Optional[datetime] = Field(nullable=True)
    
    # Resource Limits
    max_concurrent_calls: int = Field(default=10, nullable=False)
    max_daily_calls: int = Field(default=1000, nullable=False)
    max_sms_per_day: int = Field(default=1000, nullable=False)
    max_users: int = Field(default=5, nullable=False)
    max_modems: int = Field(default=5, nullable=False)
    
    # Business Configuration
    industry: Optional[str] = Field(max_length=100, nullable=True)
    company_size: Optional[str] = Field(max_length=50, nullable=True)
    timezone: str = Field(default="UTC", max_length=50, nullable=False)
    currency: str = Field(default="USD", max_length=3, nullable=False)
    
    # AI Configuration
    gemini_api_key: Optional[str] = Field(nullable=True)
    custom_prompts: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    ai_settings: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Feature Flags
    features_enabled: Dict[str, bool] = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Billing Information
    billing_email: Optional[EmailStr] = Field(nullable=True)
    payment_method_id: Optional[str] = Field(max_length=255, nullable=True)
    
    # Relationships
    users: List["User"] = Relationship(back_populates="tenant")
    campaigns: List["Campaign"] = Relationship(back_populates="tenant")
    calls: List["Call"] = Relationship(back_populates="tenant")
    leads: List["Lead"] = Relationship(back_populates="tenant")
    integrations: List["Integration"] = Relationship(back_populates="tenant")
    
    __table_args__ = (
        Index("idx_tenant_slug", "slug"),
        Index("idx_tenant_status", "status"),
        Index("idx_tenant_domain", "domain"),
    )


class User(UUIDMixin, TimestampMixin, table=True):
    """
    User model for authentication and authorization.
    
    Represents individual users within tenant organizations
    with role-based access control and comprehensive profiles.
    """
    __tablename__ = "users"
    
    # Basic Information
    email: EmailStr = Field(nullable=False, unique=True)
    username: str = Field(max_length=100, nullable=False, unique=True)
    first_name: str = Field(max_length=100, nullable=False)
    last_name: str = Field(max_length=100, nullable=False)
    
    # Authentication
    password_hash: str = Field(nullable=False)
    is_active: bool = Field(default=True, nullable=False)
    is_verified: bool = Field(default=False, nullable=False)
    last_login: Optional[datetime] = Field(nullable=True)
    
    # Authorization
    role: UserRole = Field(default=UserRole.AGENT, nullable=False)
    permissions: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    
    # Profile Information
    phone: Optional[str] = Field(max_length=20, nullable=True)
    avatar_url: Optional[str] = Field(max_length=500, nullable=True)
    timezone: str = Field(default="UTC", max_length=50, nullable=False)
    language: str = Field(default="en", max_length=10, nullable=False)
    
    # Tenant Association
    tenant_id: UUID = Field(foreign_key="tenants.id", nullable=False)
    tenant: Tenant = Relationship(back_populates="users")
    
    # Performance Metrics
    total_calls_handled: int = Field(default=0, nullable=False)
    average_call_duration: Optional[float] = Field(nullable=True)
    customer_satisfaction_score: Optional[float] = Field(nullable=True)
    
    # Settings
    notification_preferences: Dict[str, bool] = Field(default_factory=dict, sa_column=Column(JSON))
    ui_preferences: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    
    __table_args__ = (
        Index("idx_user_email", "email"),
        Index("idx_user_tenant", "tenant_id"),
        Index("idx_user_role", "role"),
        Index("idx_user_active", "is_active"),
    )


class Campaign(UUIDMixin, TimestampMixin, table=True):
    """
    Campaign model for automated calling campaigns.
    
    Represents intelligent calling campaigns with AI-driven
    optimization, scheduling, and performance tracking.
    """
    __tablename__ = "campaigns"
    
    # Basic Information
    name: str = Field(max_length=255, nullable=False)
    description: Optional[str] = Field(sa_column=Column(Text), nullable=True)
    
    # Campaign Configuration
    status: CampaignStatus = Field(default=CampaignStatus.DRAFT, nullable=False)
    campaign_type: str = Field(max_length=50, nullable=False)  # sales, support, survey, etc.
    
    # Scheduling
    start_date: Optional[datetime] = Field(nullable=True)
    end_date: Optional[datetime] = Field(nullable=True)
    schedule_config: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    
    # AI Configuration
    ai_prompt: str = Field(sa_column=Column(Text), nullable=False)
    conversation_goals: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    success_criteria: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Targeting
    target_audience: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    lead_filters: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Performance Metrics
    total_calls_made: int = Field(default=0, nullable=False)
    successful_calls: int = Field(default=0, nullable=False)
    leads_generated: int = Field(default=0, nullable=False)
    conversion_rate: float = Field(default=0.0, nullable=False)
    average_call_duration: float = Field(default=0.0, nullable=False)
    
    # Budget and Limits
    max_calls_per_day: Optional[int] = Field(nullable=True)
    max_total_calls: Optional[int] = Field(nullable=True)
    budget_limit: Optional[Decimal] = Field(max_digits=10, decimal_places=2, nullable=True)
    cost_per_call: Optional[Decimal] = Field(max_digits=6, decimal_places=4, nullable=True)
    
    # Tenant Association
    tenant_id: UUID = Field(foreign_key="tenants.id", nullable=False)
    tenant: Tenant = Relationship(back_populates="campaigns")
    
    # Relationships
    calls: List["Call"] = Relationship(back_populates="campaign")
    leads: List["Lead"] = Relationship(back_populates="campaign")
    
    __table_args__ = (
        Index("idx_campaign_tenant", "tenant_id"),
        Index("idx_campaign_status", "status"),
        Index("idx_campaign_type", "campaign_type"),
        Index("idx_campaign_dates", "start_date", "end_date"),
    )


class Call(UUIDMixin, TimestampMixin, table=True):
    """
    Call model for comprehensive call tracking and analytics.
    
    Represents individual call sessions with detailed metadata,
    conversation analysis, and business intelligence data.
    """
    __tablename__ = "calls"
    
    # Basic Call Information
    phone_number: str = Field(max_length=20, nullable=False)
    direction: CallDirection = Field(nullable=False)
    status: CallStatus = Field(default=CallStatus.INITIATED, nullable=False)
    
    # Timing Information
    initiated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    answered_at: Optional[datetime] = Field(nullable=True)
    ended_at: Optional[datetime] = Field(nullable=True)
    duration_seconds: Optional[int] = Field(nullable=True)
    
    # Technical Details
    modem_id: Optional[str] = Field(max_length=10, nullable=True)
    call_sid: Optional[str] = Field(max_length=100, nullable=True)
    audio_url: Optional[str] = Field(max_length=500, nullable=True)
    
    # Conversation Analysis
    transcript: Optional[str] = Field(sa_column=Column(Text), nullable=True)
    sentiment_score: Optional[float] = Field(nullable=True)
    conversation_summary: Optional[str] = Field(sa_column=Column(Text), nullable=True)
    key_topics: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    
    # Business Intelligence
    lead_qualified: bool = Field(default=False, nullable=False)
    appointment_scheduled: bool = Field(default=False, nullable=False)
    sale_made: bool = Field(default=False, nullable=False)
    sale_amount: Optional[Decimal] = Field(max_digits=10, decimal_places=2, nullable=True)
    
    # Customer Information
    customer_name: Optional[str] = Field(max_length=255, nullable=True)
    customer_email: Optional[EmailStr] = Field(nullable=True)
    customer_company: Optional[str] = Field(max_length=255, nullable=True)
    
    # AI Analysis
    ai_insights: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    action_items: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    follow_up_required: bool = Field(default=False, nullable=False)
    follow_up_date: Optional[datetime] = Field(nullable=True)
    
    # Quality Metrics
    audio_quality_score: Optional[float] = Field(nullable=True)
    conversation_quality_score: Optional[float] = Field(nullable=True)
    customer_satisfaction_score: Optional[float] = Field(nullable=True)
    
    # Associations
    tenant_id: UUID = Field(foreign_key="tenants.id", nullable=False)
    tenant: Tenant = Relationship(back_populates="calls")
    
    campaign_id: Optional[UUID] = Field(foreign_key="campaigns.id", nullable=True)
    campaign: Optional[Campaign] = Relationship(back_populates="calls")
    
    lead_id: Optional[UUID] = Field(foreign_key="leads.id", nullable=True)
    lead: Optional["Lead"] = Relationship(back_populates="calls")
    
    __table_args__ = (
        Index("idx_call_tenant", "tenant_id"),
        Index("idx_call_phone", "phone_number"),
        Index("idx_call_status", "status"),
        Index("idx_call_direction", "direction"),
        Index("idx_call_campaign", "campaign_id"),
        Index("idx_call_initiated", "initiated_at"),
        Index("idx_call_modem", "modem_id"),
    )


class Lead(UUIDMixin, TimestampMixin, table=True):
    """
    Lead model for comprehensive lead management and tracking.
    
    Represents potential customers with detailed profiles,
    interaction history, and AI-driven scoring and insights.
    """
    __tablename__ = "leads"
    
    # Basic Information
    first_name: str = Field(max_length=100, nullable=False)
    last_name: str = Field(max_length=100, nullable=False)
    email: Optional[EmailStr] = Field(nullable=True)
    phone: str = Field(max_length=20, nullable=False)
    
    # Company Information
    company: Optional[str] = Field(max_length=255, nullable=True)
    job_title: Optional[str] = Field(max_length=100, nullable=True)
    industry: Optional[str] = Field(max_length=100, nullable=True)
    company_size: Optional[str] = Field(max_length=50, nullable=True)
    
    # Lead Management
    status: LeadStatus = Field(default=LeadStatus.NEW, nullable=False)
    source: str = Field(max_length=100, nullable=False)  # campaign, website, referral, etc.
    priority: int = Field(default=3, nullable=False)  # 1-5 scale
    
    # AI Scoring
    lead_score: float = Field(default=0.0, nullable=False)
    conversion_probability: Optional[float] = Field(nullable=True)
    lifetime_value_prediction: Optional[Decimal] = Field(max_digits=10, decimal_places=2, nullable=True)
    
    # Interaction History
    last_contacted: Optional[datetime] = Field(nullable=True)
    contact_attempts: int = Field(default=0, nullable=False)
    total_interactions: int = Field(default=0, nullable=False)
    
    # Preferences and Notes
    preferred_contact_time: Optional[str] = Field(max_length=100, nullable=True)
    timezone: Optional[str] = Field(max_length=50, nullable=True)
    language: str = Field(default="en", max_length=10, nullable=False)
    notes: Optional[str] = Field(sa_column=Column(Text), nullable=True)
    
    # Custom Fields
    custom_fields: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    tags: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    
    # Associations
    tenant_id: UUID = Field(foreign_key="tenants.id", nullable=False)
    tenant: Tenant = Relationship(back_populates="leads")
    
    campaign_id: Optional[UUID] = Field(foreign_key="campaigns.id", nullable=True)
    campaign: Optional[Campaign] = Relationship(back_populates="leads")
    
    # Relationships
    calls: List[Call] = Relationship(back_populates="lead")
    
    __table_args__ = (
        Index("idx_lead_tenant", "tenant_id"),
        Index("idx_lead_phone", "phone"),
        Index("idx_lead_email", "email"),
        Index("idx_lead_status", "status"),
        Index("idx_lead_score", "lead_score"),
        Index("idx_lead_campaign", "campaign_id"),
        Index("idx_lead_company", "company"),
    )


class Integration(UUIDMixin, TimestampMixin, table=True):
    """
    Integration model for external service connections.
    
    Represents connections to CRM systems, e-commerce platforms,
    payment processors, and other business applications.
    """
    __tablename__ = "integrations"
    
    # Basic Information
    name: str = Field(max_length=255, nullable=False)
    integration_type: IntegrationType = Field(nullable=False)
    provider: str = Field(max_length=100, nullable=False)  # salesforce, hubspot, shopify, etc.
    
    # Configuration
    is_active: bool = Field(default=True, nullable=False)
    config: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    credentials: Dict[str, str] = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Sync Information
    last_sync: Optional[datetime] = Field(nullable=True)
    sync_frequency: str = Field(default="hourly", max_length=20, nullable=False)
    auto_sync_enabled: bool = Field(default=True, nullable=False)
    
    # Status and Metrics
    status: str = Field(default="connected", max_length=20, nullable=False)
    total_synced_records: int = Field(default=0, nullable=False)
    last_error: Optional[str] = Field(sa_column=Column(Text), nullable=True)
    
    # Tenant Association
    tenant_id: UUID = Field(foreign_key="tenants.id", nullable=False)
    tenant: Tenant = Relationship(back_populates="integrations")
    
    __table_args__ = (
        Index("idx_integration_tenant", "tenant_id"),
        Index("idx_integration_type", "integration_type"),
        Index("idx_integration_provider", "provider"),
        Index("idx_integration_active", "is_active"),
        UniqueConstraint("tenant_id", "provider", name="uq_tenant_provider"),
    )


class Payment(UUIDMixin, TimestampMixin, table=True):
    """
    Payment model for billing and transaction tracking.
    
    Represents payment transactions, subscriptions, and
    billing history for comprehensive financial management.
    """
    __tablename__ = "payments"
    
    # Basic Information
    amount: Decimal = Field(max_digits=10, decimal_places=2, nullable=False)
    currency: str = Field(default="USD", max_length=3, nullable=False)
    status: PaymentStatus = Field(default=PaymentStatus.PENDING, nullable=False)
    
    # Payment Details
    payment_method: str = Field(max_length=50, nullable=False)  # card, bank_transfer, etc.
    payment_processor: str = Field(max_length=50, nullable=False)  # stripe, paypal, etc.
    transaction_id: str = Field(max_length=255, nullable=False, unique=True)
    
    # Billing Information
    billing_period_start: Optional[date] = Field(nullable=True)
    billing_period_end: Optional[date] = Field(nullable=True)
    invoice_number: Optional[str] = Field(max_length=100, nullable=True)
    
    # Processing Information
    processed_at: Optional[datetime] = Field(nullable=True)
    failure_reason: Optional[str] = Field(max_length=500, nullable=True)
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Tenant Association
    tenant_id: UUID = Field(foreign_key="tenants.id", nullable=False)
    
    __table_args__ = (
        Index("idx_payment_tenant", "tenant_id"),
        Index("idx_payment_status", "status"),
        Index("idx_payment_transaction", "transaction_id"),
        Index("idx_payment_processor", "payment_processor"),
        Index("idx_payment_date", "processed_at"),
    )


class AuditLog(UUIDMixin, TimestampMixin, table=True):
    """
    Audit log model for compliance and security tracking.
    
    Represents all system activities for comprehensive
    audit trails and compliance reporting.
    """
    __tablename__ = "audit_logs"
    
    # Event Information
    event_type: str = Field(max_length=100, nullable=False)
    event_description: str = Field(max_length=500, nullable=False)
    
    # Actor Information
    user_id: Optional[UUID] = Field(foreign_key="users.id", nullable=True)
    user_email: Optional[str] = Field(max_length=255, nullable=True)
    ip_address: Optional[str] = Field(max_length=45, nullable=True)
    user_agent: Optional[str] = Field(max_length=500, nullable=True)
    
    # Resource Information
    resource_type: Optional[str] = Field(max_length=100, nullable=True)
    resource_id: Optional[str] = Field(max_length=255, nullable=True)
    
    # Change Information
    old_values: Optional[Dict[str, Any]] = Field(sa_column=Column(JSON), nullable=True)
    new_values: Optional[Dict[str, Any]] = Field(sa_column=Column(JSON), nullable=True)
    
    # Context
    tenant_id: Optional[UUID] = Field(foreign_key="tenants.id", nullable=True)
    session_id: Optional[str] = Field(max_length=255, nullable=True)
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    
    __table_args__ = (
        Index("idx_audit_tenant", "tenant_id"),
        Index("idx_audit_user", "user_id"),
        Index("idx_audit_event", "event_type"),
        Index("idx_audit_resource", "resource_type", "resource_id"),
        Index("idx_audit_timestamp", "created_at"),
    )


# Analytics and Reporting Models
class AnalyticsSnapshot(UUIDMixin, TimestampMixin, table=True):
    """
    Analytics snapshot model for time-series business intelligence.
    
    Stores aggregated metrics and KPIs for historical analysis
    and trend identification.
    """
    __tablename__ = "analytics_snapshots"
    
    # Time Information
    snapshot_date: date = Field(nullable=False)
    snapshot_hour: Optional[int] = Field(nullable=True)  # For hourly snapshots
    
    # Metrics
    total_calls: int = Field(default=0, nullable=False)
    successful_calls: int = Field(default=0, nullable=False)
    total_call_duration: int = Field(default=0, nullable=False)  # in seconds
    average_call_duration: float = Field(default=0.0, nullable=False)
    
    # Lead Metrics
    leads_generated: int = Field(default=0, nullable=False)
    leads_qualified: int = Field(default=0, nullable=False)
    conversion_rate: float = Field(default=0.0, nullable=False)
    
    # Revenue Metrics
    revenue_generated: Decimal = Field(default=0, max_digits=10, decimal_places=2, nullable=False)
    average_deal_size: Decimal = Field(default=0, max_digits=10, decimal_places=2, nullable=False)
    
    # Quality Metrics
    average_sentiment_score: Optional[float] = Field(nullable=True)
    customer_satisfaction_score: Optional[float] = Field(nullable=True)
    
    # Custom Metrics
    custom_metrics: Dict[str, float] = Field(default_factory=dict, sa_column=Column(JSON))
    
    # Tenant Association
    tenant_id: UUID = Field(foreign_key="tenants.id", nullable=False)
    
    __table_args__ = (
        Index("idx_analytics_tenant", "tenant_id"),
        Index("idx_analytics_date", "snapshot_date"),
        Index("idx_analytics_tenant_date", "tenant_id", "snapshot_date"),
        UniqueConstraint("tenant_id", "snapshot_date", "snapshot_hour", name="uq_tenant_snapshot"),
    )


# Validation and Business Logic
@validator('phone', pre=True, always=True)
def validate_phone_number(cls, v):
    """Validate phone number format."""
    if v and not v.startswith('+'):
        # Add basic validation logic
        pass
    return v


@validator('email', pre=True, always=True)
def validate_email_format(cls, v):
    """Validate email format."""
    if v and '@' not in v:
        raise ValueError('Invalid email format')
    return v