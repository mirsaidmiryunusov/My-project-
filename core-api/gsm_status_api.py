"""
GSM Module Status API
Provides endpoints to monitor and manage local GSM modules
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
import structlog
from local_gsm_sms_service import get_gsm_module_status, local_gsm_sms_service

logger = structlog.get_logger(__name__)

gsm_status_router = APIRouter(prefix="/api/v1/gsm", tags=["GSM Modules"])

@gsm_status_router.get("/status")
async def get_all_gsm_status() -> Dict[str, Any]:
    """
    Get status of all GSM modules
    
    Returns:
        Status information for all connected GSM modules
    """
    try:
        modules_status = await get_gsm_module_status()
        
        # Calculate summary statistics
        total_modules = len(modules_status)
        connected_modules = sum(1 for m in modules_status if m.get('connected', False))
        
        return {
            "success": True,
            "summary": {
                "total_modules": total_modules,
                "connected_modules": connected_modules,
                "disconnected_modules": total_modules - connected_modules
            },
            "modules": modules_status
        }
        
    except Exception as e:
        logger.error("Error getting GSM status", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@gsm_status_router.post("/initialize")
async def initialize_gsm_modules() -> Dict[str, Any]:
    """
    Initialize or reinitialize GSM modules
    
    Returns:
        Initialization result
    """
    try:
        await local_gsm_sms_service.initialize()
        
        modules_status = await get_gsm_module_status()
        connected_count = sum(1 for m in modules_status if m.get('connected', False))
        
        return {
            "success": True,
            "message": f"Initialized {connected_count} GSM modules",
            "connected_modules": connected_count,
            "modules": modules_status
        }
        
    except Exception as e:
        logger.error("Error initializing GSM modules", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@gsm_status_router.post("/test-sms")
async def test_sms_sending(phone_number: str, message: str = "Test SMS from AI Call Center") -> Dict[str, Any]:
    """
    Test SMS sending via GSM modules
    
    Args:
        phone_number: Target phone number
        message: Test message to send
        
    Returns:
        SMS sending result
    """
    try:
        from local_gsm_sms_service import send_notification_sms
        
        result = await send_notification_sms(phone_number, message)
        
        if result['success']:
            return {
                "success": True,
                "message": "Test SMS sent successfully",
                "details": result
            }
        else:
            return {
                "success": False,
                "message": "Failed to send test SMS",
                "error": result.get('error')
            }
            
    except Exception as e:
        logger.error("Error sending test SMS", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@gsm_status_router.get("/signal-strength")
async def get_signal_strength() -> Dict[str, Any]:
    """
    Get signal strength for all GSM modules
    
    Returns:
        Signal strength information for all modules
    """
    try:
        signal_info = []
        
        for modem_id, module in local_gsm_sms_service.modules.items():
            try:
                signal = await module.check_signal_strength()
                network_info = await module.get_network_info()
                
                signal_info.append({
                    "modem_id": modem_id,
                    "port": module.port,
                    "signal_strength": signal,
                    "signal_quality": _get_signal_quality(signal),
                    "network_info": network_info
                })
                
            except Exception as e:
                signal_info.append({
                    "modem_id": modem_id,
                    "port": module.port,
                    "error": str(e)
                })
        
        return {
            "success": True,
            "modules": signal_info
        }
        
    except Exception as e:
        logger.error("Error getting signal strength", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

def _get_signal_quality(signal_strength: int) -> str:
    """Convert signal strength to quality description"""
    if signal_strength is None or signal_strength == 99:
        return "Unknown"
    elif signal_strength >= 20:
        return "Excellent"
    elif signal_strength >= 15:
        return "Good"
    elif signal_strength >= 10:
        return "Fair"
    elif signal_strength >= 5:
        return "Poor"
    else:
        return "Very Poor"

@gsm_status_router.post("/cleanup")
async def cleanup_gsm_modules() -> Dict[str, Any]:
    """
    Cleanup and disconnect all GSM modules
    
    Returns:
        Cleanup result
    """
    try:
        await local_gsm_sms_service.cleanup()
        
        return {
            "success": True,
            "message": "All GSM modules disconnected and cleaned up"
        }
        
    except Exception as e:
        logger.error("Error cleaning up GSM modules", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@gsm_status_router.get("/health")
async def gsm_health_check() -> Dict[str, Any]:
    """
    Health check for GSM modules
    
    Returns:
        Health status of GSM system
    """
    try:
        modules_status = await get_gsm_module_status()
        
        total_modules = len(modules_status)
        connected_modules = sum(1 for m in modules_status if m.get('connected', False))
        
        # Check if we have at least one working module
        healthy = connected_modules > 0
        
        return {
            "healthy": healthy,
            "total_modules": total_modules,
            "connected_modules": connected_modules,
            "status": "healthy" if healthy else "unhealthy",
            "message": f"{connected_modules}/{total_modules} GSM modules connected"
        }
        
    except Exception as e:
        logger.error("Error in GSM health check", error=str(e))
        return {
            "healthy": False,
            "status": "error",
            "message": str(e)
        }