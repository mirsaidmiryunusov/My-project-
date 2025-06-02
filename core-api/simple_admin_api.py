"""
Simple Admin API for Development

This module provides simple admin endpoints without authentication for development.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID

import structlog
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlmodel import Session, select

from database import get_session
from models import Modem, User, SMSMessage, Call

logger = structlog.get_logger(__name__)

# Create router
simple_admin_router = APIRouter(prefix="/api/v1/simple-admin", tags=["Simple Admin"])

# Pydantic models
class SimpleModemResponse(BaseModel):
    id: str
    modem_id: str
    phone_number: str
    phone_number_type: str
    status: str
    gemini_api_key: Optional[str] = None
    assigned_user_id: Optional[str] = None

class SimpleModemUpdateRequest(BaseModel):
    gemini_api_key: Optional[str] = None
    status: Optional[str] = None

class SimpleStatsResponse(BaseModel):
    total_users: int
    total_modems: int
    active_modems: int
    available_modems: int
    busy_modems: int
    total_calls: int
    total_sms: int

@simple_admin_router.get("/modems", response_model=List[SimpleModemResponse])
async def get_modems(session: Session = Depends(get_session)):
    """Get all modems"""
    try:
        statement = select(Modem)
        modems = session.exec(statement).all()
        
        return [
            SimpleModemResponse(
                id=str(modem.id),
                modem_id=modem.modem_id,
                phone_number=modem.phone_number,
                phone_number_type=modem.phone_number_type,
                status=modem.status,
                gemini_api_key=modem.gemini_api_key,
                assigned_user_id=str(modem.assigned_user_id) if modem.assigned_user_id else None
            )
            for modem in modems
        ]
    except Exception as e:
        logger.error("Failed to get modems", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get modems")

@simple_admin_router.put("/modems/{modem_id}")
async def update_modem(
    modem_id: str,
    update_data: SimpleModemUpdateRequest,
    session: Session = Depends(get_session)
):
    """Update modem"""
    try:
        modem = session.exec(
            select(Modem).where(Modem.id == UUID(modem_id))
        ).first()
        
        if not modem:
            raise HTTPException(status_code=404, detail="Modem not found")
        
        if update_data.gemini_api_key is not None:
            modem.gemini_api_key = update_data.gemini_api_key
        
        if update_data.status is not None:
            modem.status = update_data.status
        
        modem.updated_at = datetime.utcnow()
        
        session.add(modem)
        session.commit()
        session.refresh(modem)
        
        return {"success": True, "message": "Modem updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update modem", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to update modem")

@simple_admin_router.get("/stats", response_model=SimpleStatsResponse)
async def get_stats(session: Session = Depends(get_session)):
    """Get simple stats"""
    try:
        total_users = len(session.exec(select(User)).all())
        
        modems = session.exec(select(Modem)).all()
        total_modems = len(modems)
        active_modems = len([m for m in modems if m.status != "INACTIVE"])
        available_modems = len([m for m in modems if m.status == "AVAILABLE"])
        busy_modems = len([m for m in modems if m.status == "BUSY"])
        
        total_calls = len(session.exec(select(Call)).all())
        total_sms = len(session.exec(select(SMSMessage)).all())
        
        return SimpleStatsResponse(
            total_users=total_users,
            total_modems=total_modems,
            active_modems=active_modems,
            available_modems=available_modems,
            busy_modems=busy_modems,
            total_calls=total_calls,
            total_sms=total_sms
        )
        
    except Exception as e:
        logger.error("Failed to get stats", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get stats")