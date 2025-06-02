"""
Client API Module

This module provides API endpoints for client registration, authentication,
and subscription management functionality.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, EmailStr
from sqlmodel import Session

from database import get_session
from auth import get_current_user, create_access_token
from client_registration_service import ClientRegistrationService
from models import User


logger = structlog.get_logger(__name__)

# Create router
client_router = APIRouter(prefix="/api/v1/client", tags=["Client Management"])


# Pydantic models for request/response
class ClientRegistrationRequest(BaseModel):
    email: EmailStr
    password: str
    phone_number: str


class ClientRegistrationResponse(BaseModel):
    success: bool
    registration_id: Optional[str] = None
    message: str
    expires_in_minutes: Optional[int] = None
    error: Optional[str] = None


class SMSVerificationRequest(BaseModel):
    registration_id: str
    sms_code: str


class SMSVerificationResponse(BaseModel):
    success: bool
    user_id: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    message: str
    error: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    success: bool
    access_token: Optional[str] = None
    token_type: Optional[str] = None
    user_id: Optional[str] = None
    email: Optional[str] = None
    message: str
    error: Optional[str] = None


class TemporaryPhoneResponse(BaseModel):
    success: bool
    phone_number: Optional[str] = None
    expires_at: Optional[str] = None
    minutes_remaining: Optional[int] = None
    message: str
    error: Optional[str] = None


class ConsultationResultRequest(BaseModel):
    summary: str
    client_needs: List[str]
    recommended_features: List[str]


class SubscriptionOfferResponse(BaseModel):
    success: bool
    subscription_offer: Optional[Dict[str, Any]] = None
    consultation_summary: Optional[str] = None
    next_step: Optional[str] = None
    error: Optional[str] = None


class CreateSubscriptionRequest(BaseModel):
    accepted_features: List[str]


class SubscriptionResponse(BaseModel):
    success: bool
    subscription_id: Optional[str] = None
    plan_name: Optional[str] = None
    monthly_price: Optional[float] = None
    enabled_features: Optional[List[str]] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    next_step: Optional[str] = None
    error: Optional[str] = None


class AvailableNumbersResponse(BaseModel):
    success: bool
    available_numbers: Optional[List[Dict[str, Any]]] = None
    count: Optional[int] = None
    error: Optional[str] = None


class AssignNumberRequest(BaseModel):
    modem_id: str


class AssignNumberResponse(BaseModel):
    success: bool
    phone_number: Optional[str] = None
    modem_id: Optional[str] = None
    enabled_features: Optional[List[str]] = None
    message: str
    error: Optional[str] = None


# Dependency to get client registration service
async def get_client_registration_service() -> ClientRegistrationService:
    """Get client registration service instance."""
    # This would be injected from the main app state
    from main import app_state
    return app_state.get('client_registration_service')


@client_router.post("/register", response_model=ClientRegistrationResponse)
async def register_client(
    request: ClientRegistrationRequest,
    background_tasks: BackgroundTasks,
    service: ClientRegistrationService = Depends(get_client_registration_service)
):
    """
    Start client registration process.
    
    Initiates the registration workflow by creating a registration record
    and sending SMS verification code to the provided phone number.
    """
    try:
        result = await service.start_registration(
            email=request.email,
            password=request.password,
            phone_number=request.phone_number
        )
        
        if result["success"]:
            return ClientRegistrationResponse(
                success=True,
                registration_id=result["registration_id"],
                message=result["message"],
                expires_in_minutes=result["expires_in_minutes"]
            )
        else:
            return ClientRegistrationResponse(
                success=False,
                message=result["error"],
                error=result["error"]
            )
            
    except Exception as e:
        logger.error("Client registration failed", error=str(e))
        raise HTTPException(status_code=500, detail="Registration failed")


@client_router.post("/verify-sms", response_model=SMSVerificationResponse)
async def verify_sms_code(
    request: SMSVerificationRequest,
    service: ClientRegistrationService = Depends(get_client_registration_service)
):
    """
    Verify SMS code and complete registration.
    
    Validates the SMS verification code and creates the user account
    if the code is correct and not expired.
    """
    try:
        result = await service.verify_sms_code(
            registration_id=request.registration_id,
            sms_code=request.sms_code
        )
        
        if result["success"]:
            return SMSVerificationResponse(
                success=True,
                user_id=result["user_id"],
                email=result["email"],
                phone=result["phone"],
                message=result["message"]
            )
        else:
            return SMSVerificationResponse(
                success=False,
                message=result["error"],
                error=result["error"]
            )
            
    except Exception as e:
        logger.error("SMS verification failed", error=str(e))
        raise HTTPException(status_code=500, detail="Verification failed")


@client_router.post("/login", response_model=LoginResponse)
async def login_client(
    request: LoginRequest,
    service: ClientRegistrationService = Depends(get_client_registration_service),
    session: Session = Depends(get_session)
):
    """
    Authenticate client and return access token.
    
    Validates email and password, then returns JWT access token
    for authenticated sessions.
    """
    try:
        # Find user by email
        from sqlmodel import select
        from models import User
        
        user = session.exec(
            select(User).where(User.email == request.email)
        ).first()
        
        if not user:
            return LoginResponse(
                success=False,
                message="Invalid email or password",
                error="INVALID_CREDENTIALS"
            )
        
        # Verify password
        if not service.verify_password(request.password, user.password_hash):
            return LoginResponse(
                success=False,
                message="Invalid email or password",
                error="INVALID_CREDENTIALS"
            )
        
        if not user.is_active:
            return LoginResponse(
                success=False,
                message="Account is deactivated",
                error="ACCOUNT_DEACTIVATED"
            )
        
        # Create access token
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email}
        )
        
        # Update last login
        user.last_login = datetime.utcnow()
        session.commit()
        
        logger.info("Client logged in", user_id=user.id, email=user.email)
        
        return LoginResponse(
            success=True,
            access_token=access_token,
            token_type="bearer",
            user_id=str(user.id),
            email=user.email,
            message="Login successful"
        )
        
    except Exception as e:
        logger.error("Client login failed", error=str(e))
        raise HTTPException(status_code=500, detail="Login failed")


@client_router.post("/request-temporary-phone", response_model=TemporaryPhoneResponse)
async def request_temporary_phone(
    current_user: User = Depends(get_current_user),
    service: ClientRegistrationService = Depends(get_client_registration_service)
):
    """
    Request a temporary company phone number for consultation.
    
    Assigns a company phone number to the authenticated user for 30 minutes
    to speak with the AI assistant about their business needs.
    """
    try:
        result = await service.assign_temporary_phone(str(current_user.id))
        
        if result["success"]:
            return TemporaryPhoneResponse(
                success=True,
                phone_number=result["phone_number"],
                expires_at=result["expires_at"],
                minutes_remaining=result["minutes_remaining"],
                message=result["message"]
            )
        else:
            return TemporaryPhoneResponse(
                success=False,
                message=result["error"],
                error=result["error"]
            )
            
    except Exception as e:
        logger.error("Temporary phone request failed", error=str(e))
        raise HTTPException(status_code=500, detail="Request failed")


@client_router.post("/consultation-result", response_model=SubscriptionOfferResponse)
async def submit_consultation_result(
    request: ConsultationResultRequest,
    current_user: User = Depends(get_current_user),
    service: ClientRegistrationService = Depends(get_client_registration_service)
):
    """
    Submit consultation results and receive subscription offer.
    
    Processes the AI consultation results and generates a personalized
    subscription offer based on the client's identified needs.
    """
    try:
        consultation_data = {
            "summary": request.summary,
            "client_needs": request.client_needs,
            "recommended_features": request.recommended_features
        }
        
        result = await service.process_consultation_result(
            str(current_user.id),
            consultation_data
        )
        
        if result["success"]:
            return SubscriptionOfferResponse(
                success=True,
                subscription_offer=result["subscription_offer"],
                consultation_summary=result["consultation_summary"],
                next_step=result["next_step"]
            )
        else:
            return SubscriptionOfferResponse(
                success=False,
                error=result["error"]
            )
            
    except Exception as e:
        logger.error("Consultation result processing failed", error=str(e))
        raise HTTPException(status_code=500, detail="Processing failed")


@client_router.post("/create-subscription", response_model=SubscriptionResponse)
async def create_subscription(
    request: CreateSubscriptionRequest,
    current_user: User = Depends(get_current_user),
    service: ClientRegistrationService = Depends(get_client_registration_service)
):
    """
    Create a monthly subscription for the client.
    
    Creates an active subscription with the selected features
    and enables the client to choose a dedicated phone number.
    """
    try:
        result = await service.create_subscription(
            str(current_user.id),
            request.accepted_features
        )
        
        if result["success"]:
            return SubscriptionResponse(
                success=True,
                subscription_id=result["subscription_id"],
                plan_name=result["plan_name"],
                monthly_price=result["monthly_price"],
                enabled_features=result["enabled_features"],
                start_date=result["start_date"],
                end_date=result["end_date"],
                next_step=result["next_step"],
                message="Subscription created successfully"
            )
        else:
            return SubscriptionResponse(
                success=False,
                message=result["error"],
                error=result["error"]
            )
            
    except Exception as e:
        logger.error("Subscription creation failed", error=str(e))
        raise HTTPException(status_code=500, detail="Subscription creation failed")


@client_router.get("/available-numbers", response_model=AvailableNumbersResponse)
async def get_available_numbers(
    current_user: User = Depends(get_current_user),
    service: ClientRegistrationService = Depends(get_client_registration_service)
):
    """
    Get list of available client phone numbers.
    
    Returns available phone numbers that can be assigned to clients
    with active subscriptions.
    """
    try:
        result = await service.get_available_client_numbers(str(current_user.id))
        
        if result["success"]:
            return AvailableNumbersResponse(
                success=True,
                available_numbers=result["available_numbers"],
                count=result["count"]
            )
        else:
            return AvailableNumbersResponse(
                success=False,
                error=result["error"]
            )
            
    except Exception as e:
        logger.error("Failed to get available numbers", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get available numbers")


@client_router.post("/assign-number", response_model=AssignNumberResponse)
async def assign_client_number(
    request: AssignNumberRequest,
    current_user: User = Depends(get_current_user),
    service: ClientRegistrationService = Depends(get_client_registration_service)
):
    """
    Assign a client phone number to the user.
    
    Assigns the selected phone number to the user's account,
    making it their dedicated number for AI assistance.
    """
    try:
        result = await service.assign_client_number(
            str(current_user.id),
            request.modem_id
        )
        
        if result["success"]:
            return AssignNumberResponse(
                success=True,
                phone_number=result["phone_number"],
                modem_id=result["modem_id"],
                enabled_features=result["enabled_features"],
                message=result["message"]
            )
        else:
            return AssignNumberResponse(
                success=False,
                message=result["error"],
                error=result["error"]
            )
            
    except Exception as e:
        logger.error("Number assignment failed", error=str(e))
        raise HTTPException(status_code=500, detail="Assignment failed")


@client_router.get("/profile")
async def get_client_profile(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Get client profile information.
    
    Returns the current user's profile including subscription status
    and assigned phone numbers.
    """
    try:
        from sqlmodel import select
        from models import Subscription, Modem
        
        # Get active subscription
        subscription = session.exec(
            select(Subscription).where(
                Subscription.user_id == current_user.id,
                Subscription.status == "active"
            )
        ).first()
        
        # Get assigned modems
        assigned_modems = session.exec(
            select(Modem).where(
                Modem.assigned_user_id == current_user.id
            )
        ).all()
        
        profile_data = {
            "user_id": str(current_user.id),
            "email": current_user.email,
            "phone": current_user.phone,
            "first_name": current_user.first_name,
            "last_name": current_user.last_name,
            "is_verified": current_user.is_verified,
            "subscription": None,
            "assigned_numbers": []
        }
        
        if subscription:
            profile_data["subscription"] = {
                "id": str(subscription.id),
                "plan_name": subscription.plan_name,
                "status": subscription.status,
                "monthly_price": float(subscription.monthly_price),
                "enabled_features": subscription.enabled_features,
                "start_date": subscription.start_date.isoformat(),
                "end_date": subscription.end_date.isoformat(),
                "next_payment_date": subscription.next_payment_date.isoformat() if subscription.next_payment_date else None
            }
        
        for modem in assigned_modems:
            profile_data["assigned_numbers"].append({
                "modem_id": str(modem.id),
                "phone_number": modem.phone_number,
                "phone_number_type": modem.phone_number_type,
                "assigned_at": modem.assigned_at.isoformat() if modem.assigned_at else None
            })
        
        return {
            "success": True,
            "profile": profile_data
        }
        
    except Exception as e:
        logger.error("Failed to get client profile", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get profile")