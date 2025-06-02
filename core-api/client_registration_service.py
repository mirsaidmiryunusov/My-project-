"""
Client Registration Service Module

This module handles the complete client registration workflow including
SMS verification, temporary phone assignments, and subscription management.
"""

import asyncio
import random
import string
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from uuid import UUID

import structlog
from sqlmodel import Session, select
from passlib.context import CryptContext
import redis.asyncio as redis

from models import (
    ClientRegistration, User, Subscription, Modem, TemporaryPhoneAssignment,
    SMSMessage, ConversationContext, UserRole, SubscriptionStatus,
    ModemStatus, PhoneNumberType, SMSStatus
)
from config import CoreAPIConfig


logger = structlog.get_logger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class ClientRegistrationService:
    """
    Service for handling client registration and onboarding workflow.
    
    Manages the complete registration process from initial signup through
    SMS verification, temporary phone assignment, and subscription setup.
    """
    
    def __init__(self, config: CoreAPIConfig, engine, redis_client: redis.Redis):
        self.config = config
        self.engine = engine
        self.redis = redis_client
        self.sms_service = None  # Will be injected
        
    async def initialize(self):
        """Initialize the service."""
        logger.info("Initializing Client Registration Service")
        
    async def cleanup(self):
        """Cleanup resources."""
        logger.info("Cleaning up Client Registration Service")
        
    def generate_sms_code(self) -> str:
        """Generate a 6-digit SMS verification code."""
        return ''.join(random.choices(string.digits, k=6))
        
    def hash_password(self, password: str) -> str:
        """Hash a password."""
        return pwd_context.hash(password)
        
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)
        
    async def start_registration(self, email: str, password: str, phone_number: str) -> Dict[str, Any]:
        """
        Start the client registration process.
        
        Args:
            email: Client email address
            password: Client password
            phone_number: Client phone number
            
        Returns:
            Registration status and next steps
        """
        try:
            with Session(self.engine) as session:
                # Check if email already exists
                existing_user = session.exec(
                    select(User).where(User.email == email)
                ).first()
                
                if existing_user:
                    return {
                        "success": False,
                        "error": "Email already registered",
                        "code": "EMAIL_EXISTS"
                    }
                
                # Check if phone already exists
                existing_phone = session.exec(
                    select(ClientRegistration).where(
                        ClientRegistration.phone_number == phone_number,
                        ClientRegistration.is_completed == False
                    )
                ).first()
                
                if existing_phone:
                    # Update existing registration
                    registration = existing_phone
                    registration.email = email
                    registration.password_hash = self.hash_password(password)
                    registration.verification_attempts = 0
                else:
                    # Create new registration
                    registration = ClientRegistration(
                        email=email,
                        password_hash=self.hash_password(password),
                        phone_number=phone_number
                    )
                    session.add(registration)
                
                # Generate SMS code
                sms_code = self.generate_sms_code()
                registration.sms_code = sms_code
                registration.sms_code_expires_at = datetime.utcnow() + timedelta(minutes=10)
                
                session.commit()
                session.refresh(registration)
                
                # Send SMS verification code
                await self._send_verification_sms(phone_number, sms_code, registration.id)
                
                logger.info("Registration started", 
                           registration_id=registration.id, 
                           phone_number=phone_number)
                
                return {
                    "success": True,
                    "registration_id": str(registration.id),
                    "message": "SMS verification code sent",
                    "expires_in_minutes": 10
                }
                
        except Exception as e:
            logger.error("Registration start failed", error=str(e))
            return {
                "success": False,
                "error": "Registration failed",
                "details": str(e)
            }
            
    async def verify_sms_code(self, registration_id: str, sms_code: str) -> Dict[str, Any]:
        """
        Verify SMS code and complete registration.
        
        Args:
            registration_id: Registration ID
            sms_code: SMS verification code
            
        Returns:
            Verification result and user credentials
        """
        try:
            with Session(self.engine) as session:
                # Convert string to UUID if needed
                if isinstance(registration_id, str):
                    registration_id = UUID(registration_id)
                
                registration = session.get(ClientRegistration, registration_id)
                
                if not registration:
                    return {
                        "success": False,
                        "error": "Registration not found",
                        "code": "REGISTRATION_NOT_FOUND"
                    }
                
                # Check if already completed
                if registration.is_completed:
                    return {
                        "success": False,
                        "error": "Registration already completed",
                        "code": "ALREADY_COMPLETED"
                    }
                
                # Check attempts
                if registration.verification_attempts >= 3:
                    return {
                        "success": False,
                        "error": "Too many verification attempts",
                        "code": "TOO_MANY_ATTEMPTS"
                    }
                
                # Check expiration
                if registration.sms_code_expires_at < datetime.utcnow():
                    return {
                        "success": False,
                        "error": "SMS code expired",
                        "code": "CODE_EXPIRED"
                    }
                
                # Verify code
                if registration.sms_code != sms_code:
                    registration.verification_attempts += 1
                    session.commit()
                    
                    return {
                        "success": False,
                        "error": "Invalid SMS code",
                        "code": "INVALID_CODE",
                        "attempts_remaining": 3 - registration.verification_attempts
                    }
                
                # Create user account
                user = User(
                    email=registration.email,
                    username=registration.email.split('@')[0],
                    first_name="",
                    last_name="",
                    password_hash=registration.password_hash,
                    phone=registration.phone_number,
                    role=UserRole.AGENT,
                    is_active=True,
                    is_verified=True,
                    tenant_id=self._get_default_tenant_id()
                )
                
                session.add(user)
                session.commit()
                session.refresh(user)
                
                # Complete registration
                registration.is_completed = True
                registration.is_phone_verified = True
                registration.completed_at = datetime.utcnow()
                registration.user_id = user.id
                
                session.commit()
                
                logger.info("Registration completed", 
                           user_id=user.id, 
                           phone_number=registration.phone_number)
                
                return {
                    "success": True,
                    "user_id": str(user.id),
                    "email": user.email,
                    "phone": user.phone,
                    "message": "Registration completed successfully"
                }
                
        except Exception as e:
            logger.error("SMS verification failed", error=str(e))
            return {
                "success": False,
                "error": "Verification failed",
                "details": str(e)
            }
            
    async def assign_temporary_phone(self, user_id: str) -> Dict[str, Any]:
        """
        Assign a temporary company phone number for 30 minutes.
        
        Args:
            user_id: User ID
            
        Returns:
            Temporary phone assignment details
        """
        try:
            with Session(self.engine) as session:
                # Convert string to UUID
                user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
                user = session.get(User, user_uuid)
                if not user:
                    return {
                        "success": False,
                        "error": "User not found"
                    }
                
                # Check if user already has an active assignment
                existing_assignment = session.exec(
                    select(TemporaryPhoneAssignment).where(
                        TemporaryPhoneAssignment.user_id == user_uuid,
                        TemporaryPhoneAssignment.is_active == True,
                        TemporaryPhoneAssignment.expires_at > datetime.utcnow()
                    )
                ).first()
                
                if existing_assignment:
                    return {
                        "success": True,
                        "phone_number": existing_assignment.phone_number,
                        "expires_at": existing_assignment.expires_at.isoformat(),
                        "minutes_remaining": int((existing_assignment.expires_at - datetime.utcnow()).total_seconds() / 60)
                    }
                
                # Find available company modem
                available_modem = session.exec(
                    select(Modem).where(
                        Modem.phone_number_type == PhoneNumberType.COMPANY,
                        Modem.status == ModemStatus.AVAILABLE,
                        Modem.is_active == True
                    )
                ).first()
                
                if not available_modem:
                    return {
                        "success": False,
                        "error": "No available company numbers",
                        "code": "NO_AVAILABLE_NUMBERS"
                    }
                
                # Create temporary assignment
                expires_at = datetime.utcnow() + timedelta(minutes=30)
                assignment = TemporaryPhoneAssignment(
                    user_id=user.id,
                    modem_id=available_modem.id,
                    phone_number=available_modem.phone_number,
                    expires_at=expires_at
                )
                
                # Update modem status
                available_modem.status = ModemStatus.ASSIGNED
                available_modem.assigned_user_id = user.id
                available_modem.assigned_at = datetime.utcnow()
                available_modem.assignment_expires_at = expires_at
                
                session.add(assignment)
                session.commit()
                session.refresh(assignment)
                
                # Schedule cleanup task
                await self._schedule_assignment_cleanup(assignment.id, expires_at)
                
                logger.info("Temporary phone assigned", 
                           user_id=user_id, 
                           phone_number=available_modem.phone_number,
                           expires_at=expires_at)
                
                return {
                    "success": True,
                    "phone_number": available_modem.phone_number,
                    "expires_at": expires_at.isoformat(),
                    "minutes_remaining": 30,
                    "message": "Call this number within 30 minutes to speak with our AI assistant"
                }
                
        except Exception as e:
            logger.error("Temporary phone assignment failed", error=str(e))
            return {
                "success": False,
                "error": "Assignment failed",
                "details": str(e)
            }
            
    async def process_consultation_result(self, user_id: str, consultation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the result of AI consultation and offer subscription.
        
        Args:
            user_id: User ID
            consultation_data: Data from AI consultation
            
        Returns:
            Subscription offer details
        """
        try:
            with Session(self.engine) as session:
                # Update temporary assignment with consultation results
                assignment = session.exec(
                    select(TemporaryPhoneAssignment).where(
                        TemporaryPhoneAssignment.user_id == user_id,
                        TemporaryPhoneAssignment.is_active == True
                    )
                ).first()
                
                if assignment:
                    assignment.conversation_summary = consultation_data.get("summary", "")
                    assignment.client_needs = consultation_data.get("client_needs", [])
                    assignment.recommended_features = consultation_data.get("recommended_features", [])
                    assignment.subscription_offered = True
                    
                    session.commit()
                
                # Create subscription offer
                subscription_offer = {
                    "plan_name": "Monthly AI Assistant",
                    "monthly_price": 99.99,
                    "currency": "USD",
                    "features": consultation_data.get("recommended_features", []),
                    "benefits": [
                        "24/7 AI assistant",
                        "Dedicated phone number",
                        "Custom automation",
                        "Analytics and reporting"
                    ]
                }
                
                logger.info("Consultation processed", 
                           user_id=user_id, 
                           features_count=len(consultation_data.get("recommended_features", [])))
                
                return {
                    "success": True,
                    "subscription_offer": subscription_offer,
                    "consultation_summary": consultation_data.get("summary", ""),
                    "next_step": "subscription_decision"
                }
                
        except Exception as e:
            logger.error("Consultation processing failed", error=str(e))
            return {
                "success": False,
                "error": "Processing failed",
                "details": str(e)
            }
            
    async def create_subscription(self, user_id: str, accepted_features: List[str]) -> Dict[str, Any]:
        """
        Create a monthly subscription for the user.
        
        Args:
            user_id: User ID
            accepted_features: List of accepted features
            
        Returns:
            Subscription creation result
        """
        try:
            with Session(self.engine) as session:
                # Convert string to UUID
                user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
                user = session.get(User, user_uuid)
                if not user:
                    return {
                        "success": False,
                        "error": "User not found"
                    }
                
                # Check if user already has an active subscription
                existing_subscription = session.exec(
                    select(Subscription).where(
                        Subscription.user_id == user_uuid,
                        Subscription.status.in_([SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIAL])
                    )
                ).first()
                
                if existing_subscription:
                    return {
                        "success": False,
                        "error": "User already has an active subscription"
                    }
                
                # Create subscription
                start_date = datetime.utcnow()
                end_date = start_date + timedelta(days=30)
                
                subscription = Subscription(
                    user_id=user.id,
                    plan_name="Monthly AI Assistant",
                    status=SubscriptionStatus.ACTIVE,
                    monthly_price=99.99,
                    currency="USD",
                    start_date=start_date,
                    end_date=end_date,
                    enabled_features=accepted_features,
                    next_payment_date=end_date
                )
                
                session.add(subscription)
                session.commit()
                session.refresh(subscription)
                
                # Update temporary assignment
                assignment = session.exec(
                    select(TemporaryPhoneAssignment).where(
                        TemporaryPhoneAssignment.user_id == user_id,
                        TemporaryPhoneAssignment.is_active == True
                    )
                ).first()
                
                if assignment:
                    assignment.subscription_accepted = True
                    session.commit()
                
                logger.info("Subscription created", 
                           user_id=user_id, 
                           subscription_id=subscription.id,
                           features_count=len(accepted_features))
                
                return {
                    "success": True,
                    "subscription_id": str(subscription.id),
                    "plan_name": subscription.plan_name,
                    "monthly_price": float(subscription.monthly_price),
                    "enabled_features": accepted_features,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "next_step": "select_client_number"
                }
                
        except Exception as e:
            logger.error("Subscription creation failed", error=str(e))
            return {
                "success": False,
                "error": "Subscription creation failed",
                "details": str(e)
            }
            
    async def get_available_client_numbers(self, user_id: str) -> Dict[str, Any]:
        """
        Get list of available client phone numbers.
        
        Args:
            user_id: User ID
            
        Returns:
            List of available client numbers
        """
        try:
            with Session(self.engine) as session:
                # Check if user has active subscription
                subscription = session.exec(
                    select(Subscription).where(
                        Subscription.user_id == user_id,
                        Subscription.status == SubscriptionStatus.ACTIVE
                    )
                ).first()
                
                if not subscription:
                    return {
                        "success": False,
                        "error": "No active subscription found"
                    }
                
                # Get available client numbers
                available_modems = session.exec(
                    select(Modem).where(
                        Modem.phone_number_type == PhoneNumberType.CLIENT,
                        Modem.status == ModemStatus.AVAILABLE,
                        Modem.is_active == True
                    )
                ).all()
                
                client_numbers = [
                    {
                        "modem_id": str(modem.id),
                        "phone_number": modem.phone_number,
                        "signal_strength": modem.signal_strength,
                        "uptime_percentage": modem.uptime_percentage
                    }
                    for modem in available_modems
                ]
                
                return {
                    "success": True,
                    "available_numbers": client_numbers,
                    "count": len(client_numbers)
                }
                
        except Exception as e:
            logger.error("Failed to get available client numbers", error=str(e))
            return {
                "success": False,
                "error": "Failed to get available numbers",
                "details": str(e)
            }
            
    async def assign_client_number(self, user_id: str, modem_id: str) -> Dict[str, Any]:
        """
        Assign a client phone number to the user.
        
        Args:
            user_id: User ID
            modem_id: Selected modem ID
            
        Returns:
            Assignment result
        """
        try:
            with Session(self.engine) as session:
                # Verify subscription
                subscription = session.exec(
                    select(Subscription).where(
                        Subscription.user_id == user_id,
                        Subscription.status == SubscriptionStatus.ACTIVE
                    )
                ).first()
                
                if not subscription:
                    return {
                        "success": False,
                        "error": "No active subscription found"
                    }
                
                # Get modem
                modem = session.get(Modem, modem_id)
                if not modem:
                    return {
                        "success": False,
                        "error": "Modem not found"
                    }
                
                if modem.status != ModemStatus.AVAILABLE:
                    return {
                        "success": False,
                        "error": "Modem not available"
                    }
                
                # Assign modem to user
                modem.status = ModemStatus.ASSIGNED
                modem.assigned_user_id = user_id
                modem.assigned_at = datetime.utcnow()
                
                # Set up AI configuration for the modem
                modem.ai_prompt = self._generate_client_ai_prompt(subscription.enabled_features)
                
                session.commit()
                
                logger.info("Client number assigned", 
                           user_id=user_id, 
                           modem_id=modem_id,
                           phone_number=modem.phone_number)
                
                return {
                    "success": True,
                    "phone_number": modem.phone_number,
                    "modem_id": str(modem.id),
                    "enabled_features": subscription.enabled_features,
                    "message": "Your dedicated phone number has been assigned"
                }
                
        except Exception as e:
            logger.error("Client number assignment failed", error=str(e))
            return {
                "success": False,
                "error": "Assignment failed",
                "details": str(e)
            }
            
    async def _send_verification_sms(self, phone_number: str, sms_code: str, registration_id: UUID):
        """Send SMS verification code."""
        try:
            message_content = f"Your verification code is: {sms_code}. Valid for 10 minutes."
            
            with Session(self.engine) as session:
                sms_message = SMSMessage(
                    phone_number=phone_number,
                    message_content=message_content,
                    message_type="verification",
                    status=SMSStatus.PENDING,
                    registration_id=registration_id
                )
                
                session.add(sms_message)
                session.commit()
                
                # Here you would integrate with actual SMS service
                # For now, we'll just log it
                logger.info("SMS verification code sent", 
                           phone_number=phone_number, 
                           code=sms_code)
                
        except Exception as e:
            logger.error("Failed to send SMS", error=str(e))
            
    def _get_default_tenant_id(self) -> UUID:
        """Get default tenant ID for new users."""
        # This should be configured based on your tenant setup
        # For now, return a placeholder
        from uuid import uuid4
        return uuid4()
        
    async def _schedule_assignment_cleanup(self, assignment_id: UUID, expires_at: datetime):
        """Schedule cleanup of temporary assignment."""
        try:
            # Calculate delay until expiration
            delay = (expires_at - datetime.utcnow()).total_seconds()
            
            # Store cleanup task in Redis
            await self.redis.setex(
                f"cleanup_assignment:{assignment_id}",
                int(delay),
                "pending"
            )
            
            logger.info("Assignment cleanup scheduled", 
                       assignment_id=assignment_id, 
                       expires_at=expires_at)
                       
        except Exception as e:
            logger.error("Failed to schedule cleanup", error=str(e))
            
    def _generate_client_ai_prompt(self, enabled_features: List[str]) -> str:
        """Generate AI prompt based on enabled features."""
        base_prompt = """You are an AI assistant helping a client with their business needs. 
        You have access to the following features based on their subscription:"""
        
        feature_descriptions = {
            "appointment_scheduling": "Schedule and manage appointments",
            "lead_qualification": "Qualify and score leads",
            "customer_support": "Provide customer support",
            "sales_automation": "Automate sales processes",
            "analytics": "Generate reports and analytics"
        }
        
        prompt_parts = [base_prompt]
        for feature in enabled_features:
            if feature in feature_descriptions:
                prompt_parts.append(f"- {feature_descriptions[feature]}")
                
        prompt_parts.append("\nAlways be helpful, professional, and focus on the client's specific needs.")
        
        return "\n".join(prompt_parts)