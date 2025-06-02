"""
Admin API Module

This module provides API endpoints for administrative functions including
modem management, API key configuration, and system settings.
"""

from typing import Dict, Any, List, Optional
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from sqlmodel import Session

from database import get_session
from auth import get_current_user, require_admin_role
from modem_management_service import ModemManagementService
from gsm_module_service import GSMModuleService
from sim900_service import SIM900Service
from models import User, UserRole


logger = structlog.get_logger(__name__)

# Create router
admin_router = APIRouter(prefix="/api/v1/admin", tags=["Administration"])


# Pydantic models for request/response
class CreateModemRequest(BaseModel):
    modem_id: str
    phone_number: str
    phone_number_type: str = "client"  # client, company, temporary
    is_active: bool = True
    gemini_api_key: Optional[str] = None
    ai_prompt: Optional[str] = None
    device_info: Optional[Dict[str, Any]] = None


class UpdateModemRequest(BaseModel):
    is_active: Optional[bool] = None
    gemini_api_key: Optional[str] = None
    ai_prompt: Optional[str] = None
    device_info: Optional[Dict[str, Any]] = None
    status: Optional[str] = None


class ModemResponse(BaseModel):
    success: bool
    modem: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    error: Optional[str] = None


class ModemListResponse(BaseModel):
    success: bool
    modems: Optional[List[Dict[str, Any]]] = None
    count: Optional[int] = None
    error: Optional[str] = None


class AssignAPIKeyRequest(BaseModel):
    api_key: str


class BulkConfigurationRequest(BaseModel):
    configurations: List[Dict[str, Any]]


class BulkConfigurationResponse(BaseModel):
    success: bool
    results: Optional[List[Dict[str, Any]]] = None
    total_processed: Optional[int] = None
    successful_updates: Optional[int] = None
    error: Optional[str] = None


class StatisticsResponse(BaseModel):
    success: bool
    statistics: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class AdminSettingsResponse(BaseModel):
    success: bool
    settings: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None


class UpdateSettingRequest(BaseModel):
    new_value: str


class GenericResponse(BaseModel):
    success: bool
    message: str
    error: Optional[str] = None


# Dependency to get modem management service
async def get_modem_management_service() -> ModemManagementService:
    """Get modem management service instance."""
    from main import app_state
    return app_state.get('modem_management_service')


@admin_router.post("/modems", response_model=ModemResponse)
async def create_modem(
    request: CreateModemRequest,
    current_user: User = Depends(require_admin_role),
    service: ModemManagementService = Depends(get_modem_management_service)
):
    """
    Create a new modem entry.
    
    Creates a new modem with the specified configuration including
    phone number, type, and optional AI settings.
    """
    try:
        modem_data = {
            "modem_id": request.modem_id,
            "phone_number": request.phone_number,
            "phone_number_type": request.phone_number_type,
            "is_active": request.is_active,
            "gemini_api_key": request.gemini_api_key,
            "ai_prompt": request.ai_prompt,
            "device_info": request.device_info or {}
        }
        
        result = await service.create_modem(modem_data, str(current_user.id))
        
        if result["success"]:
            return ModemResponse(
                success=True,
                modem=result["modem"],
                message="Modem created successfully"
            )
        else:
            return ModemResponse(
                success=False,
                error=result["error"]
            )
            
    except Exception as e:
        logger.error("Modem creation failed", error=str(e))
        raise HTTPException(status_code=500, detail="Modem creation failed")


@admin_router.get("/modems", response_model=ModemListResponse)
async def list_modems(
    status: Optional[str] = Query(None, description="Filter by status"),
    phone_number_type: Optional[str] = Query(None, description="Filter by phone number type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(require_admin_role),
    service: ModemManagementService = Depends(get_modem_management_service)
):
    """
    List all modems with optional filtering.
    
    Returns a list of all modems in the system with their current
    status, assignments, and configuration details.
    """
    try:
        filters = {}
        if status:
            filters["status"] = status
        if phone_number_type:
            filters["phone_number_type"] = phone_number_type
        if is_active is not None:
            filters["is_active"] = is_active
        
        result = await service.list_modems(str(current_user.id), filters)
        
        if result["success"]:
            return ModemListResponse(
                success=True,
                modems=result["modems"],
                count=result["count"]
            )
        else:
            return ModemListResponse(
                success=False,
                error=result["error"]
            )
            
    except Exception as e:
        logger.error("Failed to list modems", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to list modems")


@admin_router.put("/modems/{modem_id}", response_model=GenericResponse)
async def update_modem(
    modem_id: str,
    request: UpdateModemRequest,
    current_user: User = Depends(require_admin_role),
    service: ModemManagementService = Depends(get_modem_management_service)
):
    """
    Update modem configuration.
    
    Updates the specified modem's configuration including
    status, API keys, and AI prompts.
    """
    try:
        update_data = {}
        if request.is_active is not None:
            update_data["is_active"] = request.is_active
        if request.gemini_api_key is not None:
            update_data["gemini_api_key"] = request.gemini_api_key
        if request.ai_prompt is not None:
            update_data["ai_prompt"] = request.ai_prompt
        if request.device_info is not None:
            update_data["device_info"] = request.device_info
        if request.status is not None:
            update_data["status"] = request.status
        
        result = await service.update_modem(modem_id, update_data, str(current_user.id))
        
        if result["success"]:
            return GenericResponse(
                success=True,
                message="Modem updated successfully"
            )
        else:
            return GenericResponse(
                success=False,
                message=result["error"],
                error=result["error"]
            )
            
    except Exception as e:
        logger.error("Modem update failed", error=str(e))
        raise HTTPException(status_code=500, detail="Modem update failed")


@admin_router.post("/modems/{modem_id}/assign-api-key", response_model=GenericResponse)
async def assign_api_key_to_modem(
    modem_id: str,
    request: AssignAPIKeyRequest,
    current_user: User = Depends(require_admin_role),
    service: ModemManagementService = Depends(get_modem_management_service)
):
    """
    Assign Gemini API key to a specific modem.
    
    Assigns or updates the Gemini API key for the specified modem,
    enabling AI functionality for that phone number.
    """
    try:
        result = await service.assign_api_key_to_modem(
            modem_id, 
            request.api_key, 
            str(current_user.id)
        )
        
        if result["success"]:
            return GenericResponse(
                success=True,
                message="API key assigned successfully"
            )
        else:
            return GenericResponse(
                success=False,
                message=result["error"],
                error=result["error"]
            )
            
    except Exception as e:
        logger.error("API key assignment failed", error=str(e))
        raise HTTPException(status_code=500, detail="API key assignment failed")


@admin_router.post("/modems/bulk-configure", response_model=BulkConfigurationResponse)
async def bulk_configure_modems(
    request: BulkConfigurationRequest,
    current_user: User = Depends(require_admin_role),
    service: ModemManagementService = Depends(get_modem_management_service)
):
    """
    Bulk configure multiple modems.
    
    Applies configuration changes to multiple modems simultaneously,
    useful for mass updates of API keys or settings.
    """
    try:
        result = await service.bulk_configure_modems(
            request.configurations,
            str(current_user.id)
        )
        
        if result["success"]:
            return BulkConfigurationResponse(
                success=True,
                results=result["results"],
                total_processed=result["total_processed"],
                successful_updates=result["successful_updates"]
            )
        else:
            return BulkConfigurationResponse(
                success=False,
                error=result["error"]
            )
            
    except Exception as e:
        logger.error("Bulk configuration failed", error=str(e))
        raise HTTPException(status_code=500, detail="Bulk configuration failed")


@admin_router.get("/statistics", response_model=StatisticsResponse)
async def get_modem_statistics(
    current_user: User = Depends(require_admin_role),
    service: ModemManagementService = Depends(get_modem_management_service)
):
    """
    Get comprehensive modem statistics.
    
    Returns detailed statistics about modem usage, availability,
    and system performance metrics.
    """
    try:
        result = await service.get_modem_statistics(str(current_user.id))
        
        if result["success"]:
            return StatisticsResponse(
                success=True,
                statistics=result["statistics"]
            )
        else:
            return StatisticsResponse(
                success=False,
                error=result["error"]
            )
            
    except Exception as e:
        logger.error("Failed to get statistics", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get statistics")


@admin_router.get("/settings", response_model=AdminSettingsResponse)
async def get_admin_settings(
    category: Optional[str] = Query(None, description="Filter by category"),
    current_user: User = Depends(require_admin_role),
    service: ModemManagementService = Depends(get_modem_management_service)
):
    """
    Get admin settings.
    
    Returns system configuration settings with optional
    filtering by category.
    """
    try:
        result = await service.get_admin_settings(str(current_user.id), category)
        
        if result["success"]:
            return AdminSettingsResponse(
                success=True,
                settings=result["settings"]
            )
        else:
            return AdminSettingsResponse(
                success=False,
                error=result["error"]
            )
            
    except Exception as e:
        logger.error("Failed to get admin settings", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get admin settings")


@admin_router.put("/settings/{setting_key}", response_model=GenericResponse)
async def update_admin_setting(
    setting_key: str,
    request: UpdateSettingRequest,
    current_user: User = Depends(require_admin_role),
    service: ModemManagementService = Depends(get_modem_management_service)
):
    """
    Update an admin setting.
    
    Updates the specified system setting with a new value,
    maintaining version history for audit purposes.
    """
    try:
        result = await service.update_admin_setting(
            setting_key,
            request.new_value,
            str(current_user.id)
        )
        
        if result["success"]:
            return GenericResponse(
                success=True,
                message="Setting updated successfully"
            )
        else:
            return GenericResponse(
                success=False,
                message=result["error"],
                error=result["error"]
            )
            
    except Exception as e:
        logger.error("Failed to update admin setting", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update setting")


@admin_router.post("/cleanup-expired-assignments", response_model=GenericResponse)
async def cleanup_expired_assignments(
    current_user: User = Depends(require_admin_role),
    service: ModemManagementService = Depends(get_modem_management_service)
):
    """
    Manually trigger cleanup of expired temporary assignments.
    
    Forces cleanup of expired temporary phone assignments,
    freeing up company numbers for new clients.
    """
    try:
        await service.cleanup_expired_assignments()
        
        return GenericResponse(
            success=True,
            message="Expired assignments cleaned up successfully"
        )
        
    except Exception as e:
        logger.error("Failed to cleanup expired assignments", error=str(e))
        raise HTTPException(status_code=500, detail="Cleanup failed")


@admin_router.get("/dashboard-data")
async def get_admin_dashboard_data(
    current_user: User = Depends(require_admin_role),
    service: ModemManagementService = Depends(get_modem_management_service),
    session: Session = Depends(get_session)
):
    """
    Get comprehensive dashboard data for admin interface.
    
    Returns all necessary data for the admin dashboard including
    statistics, recent activity, and system status.
    """
    try:
        from sqlmodel import select, func
        from models import (
            ClientRegistration, Subscription, TemporaryPhoneAssignment,
            SMSMessage, Call
        )
        from datetime import datetime, timedelta
        
        # Get modem statistics
        modem_stats_result = await service.get_modem_statistics(str(current_user.id))
        modem_stats = modem_stats_result.get("statistics", {}) if modem_stats_result["success"] else {}
        
        # Get registration statistics
        today = datetime.utcnow().date()
        week_ago = today - timedelta(days=7)
        
        registrations_today = session.exec(
            select(func.count(ClientRegistration.id)).where(
                func.date(ClientRegistration.created_at) == today
            )
        ).one()
        
        registrations_week = session.exec(
            select(func.count(ClientRegistration.id)).where(
                func.date(ClientRegistration.created_at) >= week_ago
            )
        ).one()
        
        # Get subscription statistics
        active_subscriptions = session.exec(
            select(func.count(Subscription.id)).where(
                Subscription.status == "active"
            )
        ).one()
        
        # Get recent activity
        recent_registrations = session.exec(
            select(ClientRegistration).where(
                ClientRegistration.created_at >= datetime.utcnow() - timedelta(hours=24)
            ).order_by(ClientRegistration.created_at.desc()).limit(10)
        ).all()
        
        recent_assignments = session.exec(
            select(TemporaryPhoneAssignment).where(
                TemporaryPhoneAssignment.created_at >= datetime.utcnow() - timedelta(hours=24)
            ).order_by(TemporaryPhoneAssignment.created_at.desc()).limit(10)
        ).all()
        
        dashboard_data = {
            "modem_statistics": modem_stats,
            "registration_statistics": {
                "registrations_today": registrations_today,
                "registrations_this_week": registrations_week,
                "active_subscriptions": active_subscriptions
            },
            "recent_activity": {
                "recent_registrations": [
                    {
                        "id": str(reg.id),
                        "email": reg.email,
                        "phone_number": reg.phone_number,
                        "is_completed": reg.is_completed,
                        "created_at": reg.created_at.isoformat()
                    }
                    for reg in recent_registrations
                ],
                "recent_assignments": [
                    {
                        "id": str(assign.id),
                        "phone_number": assign.phone_number,
                        "user_id": str(assign.user_id),
                        "expires_at": assign.expires_at.isoformat(),
                        "is_active": assign.is_active,
                        "created_at": assign.created_at.isoformat()
                    }
                    for assign in recent_assignments
                ]
            },
            "system_status": {
                "timestamp": datetime.utcnow().isoformat(),
                "healthy": True
            }
        }
        
        return {
            "success": True,
            "dashboard_data": dashboard_data
        }
        
    except Exception as e:
        logger.error("Failed to get dashboard data", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get dashboard data")


# GSM Module Management Endpoints

@admin_router.get("/gsm-modules/scan")
async def scan_gsm_modules(current_user: User = Depends(require_admin_role)):
    """Scan for connected SIM900 GSM modules."""
    try:
        # Use SIM900 service for hardware detection
        sim900_service = SIM900Service()
        result = await sim900_service.scan_for_sim900_modules()
        
        logger.info("SIM900 module scan completed", 
                   admin_id=current_user.id, 
                   modules_found=result.get("modules_found", 0))
        return result
        
    except Exception as e:
        logger.error("Failed to scan SIM900 modules", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to scan SIM900 modules")


class AddGSMModuleRequest(BaseModel):
    port: str
    phone_number: str
    api_key: str


@admin_router.post("/gsm-modules/add")
async def add_gsm_module(
    request: AddGSMModuleRequest,
    current_user: User = Depends(require_admin_role)
):
    """Add a new SIM900 GSM module to the system."""
    try:
        # Use SIM900 service for hardware verification and addition
        sim900_service = SIM900Service()
        result = await sim900_service.add_sim900_module(
            port=request.port,
            phone_number=request.phone_number,
            api_key=request.api_key
        )
        
        if result["success"]:
            logger.info("SIM900 module added successfully", 
                       admin_id=current_user.id, 
                       port=request.port, 
                       phone_number=request.phone_number)
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to add GSM module", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to add GSM module")


@admin_router.delete("/gsm-modules/{modem_id}")
async def remove_gsm_module(
    modem_id: UUID,
    current_user: User = Depends(require_admin_role)
):
    """Remove a GSM module from the system."""
    try:
        gsm_service = GSMModuleService()
        result = await gsm_service.remove_gsm_module(modem_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to remove GSM module", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to remove GSM module")


@admin_router.get("/gsm-modules/{modem_id}/status")
async def get_gsm_module_status(
    modem_id: UUID,
    current_user: User = Depends(require_admin_role)
):
    """Get real-time status of a SIM900 GSM module."""
    try:
        # Use SIM900 service for hardware status check
        sim900_service = SIM900Service()
        result = await sim900_service.get_sim900_status(modem_id)
        
        if result["success"]:
            logger.info("SIM900 module status retrieved", 
                       admin_id=current_user.id, 
                       modem_id=modem_id)
            return result
        else:
            raise HTTPException(status_code=404, detail=result["error"])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get GSM module status", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get module status")


@admin_router.get("/gsm-modules/count")
async def get_available_modules_count(current_user: User = Depends(require_admin_role)):
    """Get count of available GSM modules."""
    try:
        gsm_service = GSMModuleService()
        count = await gsm_service.get_available_modules_count()
        
        return {
            "success": True,
            "available_modules": count,
            "message": f"{count} GSM modules available" if count > 0 else "No GSM modules available"
        }
        
    except Exception as e:
        logger.error("Failed to get available modules count", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get modules count")