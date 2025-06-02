"""
Modem Management Service Module

This module handles modem management, phone number assignments,
and administrative functions for the AI call center system.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from uuid import UUID

import structlog
from sqlmodel import Session, select
import redis.asyncio as redis

from models import (
    Modem, User, AdminSettings, TemporaryPhoneAssignment,
    ModemStatus, PhoneNumberType, UserRole
)
from config import CoreAPIConfig


logger = structlog.get_logger(__name__)


class ModemManagementService:
    """
    Service for managing modems, phone numbers, and administrative functions.
    
    Handles modem configuration, API key management, and system administration.
    """
    
    def __init__(self, config: CoreAPIConfig, engine, redis_client: redis.Redis):
        self.config = config
        self.engine = engine
        self.redis = redis_client
        
    async def initialize(self):
        """Initialize the service."""
        logger.info("Initializing Modem Management Service")
        await self._initialize_default_settings()
        
    async def cleanup(self):
        """Cleanup resources."""
        logger.info("Cleaning up Modem Management Service")
        
    async def _initialize_default_settings(self):
        """Initialize default admin settings."""
        try:
            with Session(self.engine) as session:
                default_settings = [
                    {
                        "key": "default_gemini_api_key",
                        "value": "",
                        "type": "string",
                        "description": "Default Gemini API key for new modems",
                        "category": "ai_configuration",
                        "is_sensitive": True
                    },
                    {
                        "key": "max_concurrent_calls",
                        "value": "80",
                        "type": "integer",
                        "description": "Maximum concurrent calls across all modems",
                        "category": "system_limits",
                        "is_sensitive": False
                    },
                    {
                        "key": "temporary_assignment_duration",
                        "value": "30",
                        "type": "integer",
                        "description": "Duration in minutes for temporary phone assignments",
                        "category": "system_configuration",
                        "is_sensitive": False
                    },
                    {
                        "key": "sms_verification_timeout",
                        "value": "10",
                        "type": "integer",
                        "description": "SMS verification timeout in minutes",
                        "category": "authentication",
                        "is_sensitive": False
                    }
                ]
                
                for setting_data in default_settings:
                    existing = session.exec(
                        select(AdminSettings).where(
                            AdminSettings.setting_key == setting_data["key"]
                        )
                    ).first()
                    
                    if not existing:
                        setting = AdminSettings(
                            setting_key=setting_data["key"],
                            setting_value=setting_data["value"],
                            setting_type=setting_data["type"],
                            description=setting_data["description"],
                            category=setting_data["category"],
                            is_sensitive=setting_data["is_sensitive"]
                        )
                        session.add(setting)
                
                session.commit()
                logger.info("Default admin settings initialized")
                
        except Exception as e:
            logger.error("Failed to initialize default settings", error=str(e))
            
    async def create_modem(self, modem_data: Dict[str, Any], admin_user_id: str) -> Dict[str, Any]:
        """
        Create a new modem entry.
        
        Args:
            modem_data: Modem configuration data
            admin_user_id: ID of admin user creating the modem
            
        Returns:
            Created modem information
        """
        try:
            with Session(self.engine) as session:
                # Verify admin permissions
                admin_user = session.get(User, admin_user_id)
                if not admin_user or admin_user.role not in [UserRole.SUPER_ADMIN, UserRole.TENANT_ADMIN]:
                    return {
                        "success": False,
                        "error": "Insufficient permissions"
                    }
                
                # Check if modem ID already exists
                existing_modem = session.exec(
                    select(Modem).where(Modem.modem_id == modem_data["modem_id"])
                ).first()
                
                if existing_modem:
                    return {
                        "success": False,
                        "error": "Modem ID already exists"
                    }
                
                # Check if phone number already exists
                existing_phone = session.exec(
                    select(Modem).where(Modem.phone_number == modem_data["phone_number"])
                ).first()
                
                if existing_phone:
                    return {
                        "success": False,
                        "error": "Phone number already exists"
                    }
                
                # Create modem
                modem = Modem(
                    modem_id=modem_data["modem_id"],
                    phone_number=modem_data["phone_number"],
                    phone_number_type=PhoneNumberType(modem_data.get("phone_number_type", "client")),
                    status=ModemStatus.AVAILABLE,
                    is_active=modem_data.get("is_active", True),
                    gemini_api_key=modem_data.get("gemini_api_key"),
                    ai_prompt=modem_data.get("ai_prompt"),
                    device_info=modem_data.get("device_info", {})
                )
                
                session.add(modem)
                session.commit()
                session.refresh(modem)
                
                logger.info("Modem created", 
                           modem_id=modem.modem_id, 
                           phone_number=modem.phone_number,
                           created_by=admin_user_id)
                
                return {
                    "success": True,
                    "modem": {
                        "id": str(modem.id),
                        "modem_id": modem.modem_id,
                        "phone_number": modem.phone_number,
                        "phone_number_type": modem.phone_number_type,
                        "status": modem.status,
                        "is_active": modem.is_active
                    }
                }
                
        except Exception as e:
            logger.error("Modem creation failed", error=str(e))
            return {
                "success": False,
                "error": "Modem creation failed",
                "details": str(e)
            }
            
    async def update_modem(self, modem_id: str, update_data: Dict[str, Any], admin_user_id: str) -> Dict[str, Any]:
        """
        Update modem configuration.
        
        Args:
            modem_id: Modem ID to update
            update_data: Updated configuration data
            admin_user_id: ID of admin user updating the modem
            
        Returns:
            Update result
        """
        try:
            with Session(self.engine) as session:
                # Verify admin permissions
                admin_user = session.get(User, admin_user_id)
                if not admin_user or admin_user.role not in [UserRole.SUPER_ADMIN, UserRole.TENANT_ADMIN]:
                    return {
                        "success": False,
                        "error": "Insufficient permissions"
                    }
                
                modem = session.get(Modem, modem_id)
                if not modem:
                    return {
                        "success": False,
                        "error": "Modem not found"
                    }
                
                # Update allowed fields
                updatable_fields = [
                    "is_active", "gemini_api_key", "ai_prompt", 
                    "device_info", "status"
                ]
                
                for field in updatable_fields:
                    if field in update_data:
                        setattr(modem, field, update_data[field])
                
                modem.updated_at = datetime.utcnow()
                session.commit()
                
                logger.info("Modem updated", 
                           modem_id=modem_id, 
                           updated_by=admin_user_id)
                
                return {
                    "success": True,
                    "message": "Modem updated successfully"
                }
                
        except Exception as e:
            logger.error("Modem update failed", error=str(e))
            return {
                "success": False,
                "error": "Modem update failed",
                "details": str(e)
            }
            
    async def list_modems(self, admin_user_id: str, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        List all modems with optional filtering.
        
        Args:
            admin_user_id: ID of admin user requesting the list
            filters: Optional filters for the query
            
        Returns:
            List of modems
        """
        try:
            with Session(self.engine) as session:
                # Verify admin permissions
                admin_user = session.get(User, admin_user_id)
                if not admin_user or admin_user.role not in [UserRole.SUPER_ADMIN, UserRole.TENANT_ADMIN]:
                    return {
                        "success": False,
                        "error": "Insufficient permissions"
                    }
                
                query = select(Modem)
                
                # Apply filters
                if filters:
                    if "status" in filters:
                        query = query.where(Modem.status == filters["status"])
                    if "phone_number_type" in filters:
                        query = query.where(Modem.phone_number_type == filters["phone_number_type"])
                    if "is_active" in filters:
                        query = query.where(Modem.is_active == filters["is_active"])
                
                modems = session.exec(query).all()
                
                modem_list = []
                for modem in modems:
                    modem_data = {
                        "id": str(modem.id),
                        "modem_id": modem.modem_id,
                        "phone_number": modem.phone_number,
                        "phone_number_type": modem.phone_number_type,
                        "status": modem.status,
                        "is_active": modem.is_active,
                        "assigned_user_id": str(modem.assigned_user_id) if modem.assigned_user_id else None,
                        "assigned_at": modem.assigned_at.isoformat() if modem.assigned_at else None,
                        "last_heartbeat": modem.last_heartbeat.isoformat() if modem.last_heartbeat else None,
                        "signal_strength": modem.signal_strength,
                        "total_calls_handled": modem.total_calls_handled,
                        "total_sms_sent": modem.total_sms_sent,
                        "uptime_percentage": modem.uptime_percentage,
                        "has_gemini_api_key": bool(modem.gemini_api_key)
                    }
                    modem_list.append(modem_data)
                
                return {
                    "success": True,
                    "modems": modem_list,
                    "count": len(modem_list)
                }
                
        except Exception as e:
            logger.error("Failed to list modems", error=str(e))
            return {
                "success": False,
                "error": "Failed to list modems",
                "details": str(e)
            }
            
    async def assign_api_key_to_modem(self, modem_id: str, api_key: str, admin_user_id: str) -> Dict[str, Any]:
        """
        Assign Gemini API key to a specific modem.
        
        Args:
            modem_id: Modem ID
            api_key: Gemini API key
            admin_user_id: ID of admin user
            
        Returns:
            Assignment result
        """
        try:
            with Session(self.engine) as session:
                # Verify admin permissions
                admin_user = session.get(User, admin_user_id)
                if not admin_user or admin_user.role not in [UserRole.SUPER_ADMIN, UserRole.TENANT_ADMIN]:
                    return {
                        "success": False,
                        "error": "Insufficient permissions"
                    }
                
                modem = session.get(Modem, modem_id)
                if not modem:
                    return {
                        "success": False,
                        "error": "Modem not found"
                    }
                
                modem.gemini_api_key = api_key
                modem.updated_at = datetime.utcnow()
                session.commit()
                
                logger.info("API key assigned to modem", 
                           modem_id=modem_id, 
                           assigned_by=admin_user_id)
                
                return {
                    "success": True,
                    "message": "API key assigned successfully"
                }
                
        except Exception as e:
            logger.error("API key assignment failed", error=str(e))
            return {
                "success": False,
                "error": "API key assignment failed",
                "details": str(e)
            }
            
    async def bulk_configure_modems(self, configurations: List[Dict[str, Any]], admin_user_id: str) -> Dict[str, Any]:
        """
        Bulk configure multiple modems.
        
        Args:
            configurations: List of modem configurations
            admin_user_id: ID of admin user
            
        Returns:
            Bulk configuration result
        """
        try:
            with Session(self.engine) as session:
                # Verify admin permissions
                admin_user = session.get(User, admin_user_id)
                if not admin_user or admin_user.role not in [UserRole.SUPER_ADMIN, UserRole.TENANT_ADMIN]:
                    return {
                        "success": False,
                        "error": "Insufficient permissions"
                    }
                
                results = []
                
                for config in configurations:
                    try:
                        modem = session.get(Modem, config["modem_id"])
                        if not modem:
                            results.append({
                                "modem_id": config["modem_id"],
                                "success": False,
                                "error": "Modem not found"
                            })
                            continue
                        
                        # Update configuration
                        if "gemini_api_key" in config:
                            modem.gemini_api_key = config["gemini_api_key"]
                        if "is_active" in config:
                            modem.is_active = config["is_active"]
                        if "ai_prompt" in config:
                            modem.ai_prompt = config["ai_prompt"]
                        
                        modem.updated_at = datetime.utcnow()
                        
                        results.append({
                            "modem_id": config["modem_id"],
                            "success": True,
                            "message": "Configuration updated"
                        })
                        
                    except Exception as e:
                        results.append({
                            "modem_id": config.get("modem_id", "unknown"),
                            "success": False,
                            "error": str(e)
                        })
                
                session.commit()
                
                successful_count = sum(1 for r in results if r["success"])
                
                logger.info("Bulk modem configuration completed", 
                           total=len(configurations), 
                           successful=successful_count,
                           configured_by=admin_user_id)
                
                return {
                    "success": True,
                    "results": results,
                    "total_processed": len(configurations),
                    "successful_updates": successful_count
                }
                
        except Exception as e:
            logger.error("Bulk modem configuration failed", error=str(e))
            return {
                "success": False,
                "error": "Bulk configuration failed",
                "details": str(e)
            }
            
    async def get_modem_statistics(self, admin_user_id: str) -> Dict[str, Any]:
        """
        Get comprehensive modem statistics.
        
        Args:
            admin_user_id: ID of admin user
            
        Returns:
            Modem statistics
        """
        try:
            with Session(self.engine) as session:
                # Verify admin permissions
                admin_user = session.get(User, admin_user_id)
                if not admin_user or admin_user.role not in [UserRole.SUPER_ADMIN, UserRole.TENANT_ADMIN]:
                    return {
                        "success": False,
                        "error": "Insufficient permissions"
                    }
                
                # Get all modems
                modems = session.exec(select(Modem)).all()
                
                # Calculate statistics
                total_modems = len(modems)
                active_modems = sum(1 for m in modems if m.is_active)
                available_modems = sum(1 for m in modems if m.status == ModemStatus.AVAILABLE)
                assigned_modems = sum(1 for m in modems if m.status == ModemStatus.ASSIGNED)
                
                company_numbers = sum(1 for m in modems if m.phone_number_type == PhoneNumberType.COMPANY)
                client_numbers = sum(1 for m in modems if m.phone_number_type == PhoneNumberType.CLIENT)
                
                modems_with_api_keys = sum(1 for m in modems if m.gemini_api_key)
                
                total_calls = sum(m.total_calls_handled for m in modems)
                total_sms = sum(m.total_sms_sent for m in modems)
                
                # Get active temporary assignments
                active_assignments = session.exec(
                    select(TemporaryPhoneAssignment).where(
                        TemporaryPhoneAssignment.is_active == True,
                        TemporaryPhoneAssignment.expires_at > datetime.utcnow()
                    )
                ).all()
                
                statistics = {
                    "total_modems": total_modems,
                    "active_modems": active_modems,
                    "inactive_modems": total_modems - active_modems,
                    "available_modems": available_modems,
                    "assigned_modems": assigned_modems,
                    "company_numbers": company_numbers,
                    "client_numbers": client_numbers,
                    "modems_with_api_keys": modems_with_api_keys,
                    "modems_without_api_keys": total_modems - modems_with_api_keys,
                    "total_calls_handled": total_calls,
                    "total_sms_sent": total_sms,
                    "active_temporary_assignments": len(active_assignments),
                    "average_uptime": sum(m.uptime_percentage for m in modems) / total_modems if total_modems > 0 else 0
                }
                
                return {
                    "success": True,
                    "statistics": statistics
                }
                
        except Exception as e:
            logger.error("Failed to get modem statistics", error=str(e))
            return {
                "success": False,
                "error": "Failed to get statistics",
                "details": str(e)
            }
            
    async def cleanup_expired_assignments(self):
        """Clean up expired temporary assignments."""
        try:
            with Session(self.engine) as session:
                # Find expired assignments
                expired_assignments = session.exec(
                    select(TemporaryPhoneAssignment).where(
                        TemporaryPhoneAssignment.is_active == True,
                        TemporaryPhoneAssignment.expires_at <= datetime.utcnow()
                    )
                ).all()
                
                for assignment in expired_assignments:
                    # Deactivate assignment
                    assignment.is_active = False
                    assignment.call_ended_at = datetime.utcnow()
                    
                    # Free up the modem
                    modem = session.get(Modem, assignment.modem_id)
                    if modem:
                        modem.status = ModemStatus.AVAILABLE
                        modem.assigned_user_id = None
                        modem.assigned_at = None
                        modem.assignment_expires_at = None
                
                session.commit()
                
                if expired_assignments:
                    logger.info("Cleaned up expired assignments", count=len(expired_assignments))
                
        except Exception as e:
            logger.error("Failed to cleanup expired assignments", error=str(e))
            
    async def get_admin_settings(self, admin_user_id: str, category: Optional[str] = None) -> Dict[str, Any]:
        """
        Get admin settings.
        
        Args:
            admin_user_id: ID of admin user
            category: Optional category filter
            
        Returns:
            Admin settings
        """
        try:
            with Session(self.engine) as session:
                # Verify admin permissions
                admin_user = session.get(User, admin_user_id)
                if not admin_user or admin_user.role not in [UserRole.SUPER_ADMIN, UserRole.TENANT_ADMIN]:
                    return {
                        "success": False,
                        "error": "Insufficient permissions"
                    }
                
                query = select(AdminSettings)
                if category:
                    query = query.where(AdminSettings.category == category)
                
                settings = session.exec(query).all()
                
                settings_data = []
                for setting in settings:
                    setting_data = {
                        "id": str(setting.id),
                        "setting_key": setting.setting_key,
                        "setting_value": setting.setting_value if not setting.is_sensitive else "***",
                        "setting_type": setting.setting_type,
                        "description": setting.description,
                        "category": setting.category,
                        "is_sensitive": setting.is_sensitive,
                        "version": setting.version,
                        "updated_at": setting.updated_at.isoformat()
                    }
                    settings_data.append(setting_data)
                
                return {
                    "success": True,
                    "settings": settings_data
                }
                
        except Exception as e:
            logger.error("Failed to get admin settings", error=str(e))
            return {
                "success": False,
                "error": "Failed to get settings",
                "details": str(e)
            }
            
    async def update_admin_setting(self, setting_key: str, new_value: str, admin_user_id: str) -> Dict[str, Any]:
        """
        Update an admin setting.
        
        Args:
            setting_key: Setting key to update
            new_value: New setting value
            admin_user_id: ID of admin user
            
        Returns:
            Update result
        """
        try:
            with Session(self.engine) as session:
                # Verify admin permissions
                admin_user = session.get(User, admin_user_id)
                if not admin_user or admin_user.role not in [UserRole.SUPER_ADMIN, UserRole.TENANT_ADMIN]:
                    return {
                        "success": False,
                        "error": "Insufficient permissions"
                    }
                
                setting = session.exec(
                    select(AdminSettings).where(AdminSettings.setting_key == setting_key)
                ).first()
                
                if not setting:
                    return {
                        "success": False,
                        "error": "Setting not found"
                    }
                
                # Store previous value
                setting.previous_value = setting.setting_value
                setting.setting_value = new_value
                setting.version += 1
                setting.changed_by = admin_user.id
                setting.changed_at = datetime.utcnow()
                setting.updated_at = datetime.utcnow()
                
                session.commit()
                
                logger.info("Admin setting updated", 
                           setting_key=setting_key, 
                           updated_by=admin_user_id)
                
                return {
                    "success": True,
                    "message": "Setting updated successfully"
                }
                
        except Exception as e:
            logger.error("Failed to update admin setting", error=str(e))
            return {
                "success": False,
                "error": "Failed to update setting",
                "details": str(e)
            }