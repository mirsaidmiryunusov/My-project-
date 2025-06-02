"""
GSM Module Service - Real hardware management for SMS and voice calls.

This service manages actual GSM modules connected to the system.
NO SIMULATION - only real hardware detection and management.
"""

import asyncio
import serial
import serial.tools.list_ports
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from uuid import UUID, uuid4
import structlog
from sqlmodel import Session, select
from database import get_db_manager
from models import Modem, ModemStatus, SMSMessage, SMSStatus

logger = structlog.get_logger(__name__)


class GSMModuleService:
    """Service for managing real GSM modules - NO SIMULATION."""
    
    def __init__(self):
        self.db_manager = get_db_manager()
        self.engine = self.db_manager.engine
        self.connected_modules = {}  # port -> module_info
        self.module_connections = {}  # modem_id -> serial_connection
    
    async def scan_for_gsm_modules(self) -> Dict[str, Any]:
        """
        Scan for real GSM modules connected via USB/Serial.
        Returns actual hardware found, not simulated data.
        """
        try:
            found_modules = []
            
            # Scan all available serial ports
            ports = serial.tools.list_ports.comports()
            
            for port in ports:
                try:
                    # Try to connect and identify GSM module
                    module_info = await self._identify_gsm_module(port.device)
                    if module_info:
                        found_modules.append({
                            "port": port.device,
                            "description": port.description,
                            "manufacturer": port.manufacturer,
                            "vid": port.vid,
                            "pid": port.pid,
                            "serial_number": port.serial_number,
                            "module_info": module_info
                        })
                        
                except Exception as e:
                    logger.debug("Failed to check port", port=port.device, error=str(e))
                    continue
            
            logger.info("GSM module scan completed", found_count=len(found_modules))
            
            return {
                "success": True,
                "modules_found": len(found_modules),
                "modules": found_modules,
                "message": f"Found {len(found_modules)} GSM modules" if found_modules else "No GSM modules detected"
            }
            
        except Exception as e:
            logger.error("GSM module scan failed", error=str(e))
            return {
                "success": False,
                "error": "Failed to scan for GSM modules",
                "modules_found": 0,
                "modules": []
            }
    
    async def _identify_gsm_module(self, port: str) -> Optional[Dict[str, str]]:
        """
        Try to identify if a serial port has a GSM module.
        Returns module information if found, None otherwise.
        """
        try:
            # Try to open serial connection
            ser = serial.Serial(
                port=port,
                baudrate=115200,
                timeout=2,
                write_timeout=2
            )
            
            try:
                # Send AT command to check if it's a GSM module
                ser.write(b'AT\r\n')
                response = ser.readline().decode('utf-8', errors='ignore').strip()
                
                if 'OK' in response:
                    # Get module information
                    module_info = {}
                    
                    # Get manufacturer
                    ser.write(b'AT+CGMI\r\n')
                    manufacturer = ser.readline().decode('utf-8', errors='ignore').strip()
                    if manufacturer and manufacturer != 'OK':
                        module_info['manufacturer'] = manufacturer
                    
                    # Get model
                    ser.write(b'AT+CGMM\r\n')
                    model = ser.readline().decode('utf-8', errors='ignore').strip()
                    if model and model != 'OK':
                        module_info['model'] = model
                    
                    # Get IMEI
                    ser.write(b'AT+CGSN\r\n')
                    imei = ser.readline().decode('utf-8', errors='ignore').strip()
                    if imei and imei != 'OK' and len(imei) >= 15:
                        module_info['imei'] = imei
                    
                    # Get SIM card status
                    ser.write(b'AT+CPIN?\r\n')
                    sim_status = ser.readline().decode('utf-8', errors='ignore').strip()
                    module_info['sim_status'] = sim_status
                    
                    # Get signal strength
                    ser.write(b'AT+CSQ\r\n')
                    signal = ser.readline().decode('utf-8', errors='ignore').strip()
                    module_info['signal_strength'] = signal
                    
                    return module_info
                    
            finally:
                ser.close()
                
        except Exception as e:
            logger.debug("Failed to identify GSM module", port=port, error=str(e))
            
        return None
    
    async def add_gsm_module(self, port: str, phone_number: str, api_key: str) -> Dict[str, Any]:
        """
        Add a real GSM module to the system.
        Only works with actual hardware - no simulation.
        """
        try:
            # First verify the module exists and is accessible
            module_info = await self._identify_gsm_module(port)
            if not module_info:
                return {
                    "success": False,
                    "error": f"No GSM module found on port {port}"
                }
            
            # Check if SIM card is ready
            if 'READY' not in module_info.get('sim_status', ''):
                return {
                    "success": False,
                    "error": f"SIM card not ready on port {port}. Status: {module_info.get('sim_status', 'Unknown')}"
                }
            
            with Session(self.engine) as session:
                # Check if module already exists
                existing_modem = session.exec(
                    select(Modem).where(
                        Modem.port == port
                    )
                ).first()
                
                if existing_modem:
                    return {
                        "success": False,
                        "error": f"GSM module on port {port} already exists in system"
                    }
                
                # Check if phone number already exists
                existing_phone = session.exec(
                    select(Modem).where(
                        Modem.phone_number == phone_number
                    )
                ).first()
                
                if existing_phone:
                    return {
                        "success": False,
                        "error": f"Phone number {phone_number} already assigned to another module"
                    }
                
                # Create new modem record
                modem = Modem(
                    phone_number=phone_number,
                    status=ModemStatus.AVAILABLE,
                    api_key=api_key,
                    port=port,
                    imei=module_info.get('imei'),
                    manufacturer=module_info.get('manufacturer'),
                    model=module_info.get('model'),
                    signal_strength=module_info.get('signal_strength'),
                    last_seen=datetime.utcnow()
                )
                
                session.add(modem)
                session.commit()
                session.refresh(modem)
                
                logger.info("GSM module added successfully", 
                           modem_id=modem.id, 
                           phone_number=phone_number, 
                           port=port)
                
                return {
                    "success": True,
                    "modem_id": str(modem.id),
                    "phone_number": phone_number,
                    "port": port,
                    "module_info": module_info,
                    "message": "GSM module added successfully"
                }
                
        except Exception as e:
            logger.error("Failed to add GSM module", error=str(e), port=port)
            return {
                "success": False,
                "error": "Failed to add GSM module"
            }
    
    async def remove_gsm_module(self, modem_id: UUID) -> Dict[str, Any]:
        """Remove a GSM module from the system."""
        try:
            with Session(self.engine) as session:
                modem = session.get(Modem, modem_id)
                if not modem:
                    return {
                        "success": False,
                        "error": "GSM module not found"
                    }
                
                # Close any active connections
                if modem_id in self.module_connections:
                    try:
                        self.module_connections[modem_id].close()
                        del self.module_connections[modem_id]
                    except:
                        pass
                
                # Remove from database
                session.delete(modem)
                session.commit()
                
                logger.info("GSM module removed", modem_id=modem_id)
                
                return {
                    "success": True,
                    "message": "GSM module removed successfully"
                }
                
        except Exception as e:
            logger.error("Failed to remove GSM module", error=str(e), modem_id=modem_id)
            return {
                "success": False,
                "error": "Failed to remove GSM module"
            }
    
    async def send_sms(self, modem_id: UUID, phone_number: str, message: str) -> Dict[str, Any]:
        """
        Send SMS using real GSM module.
        Returns error if no modules are available - NO SIMULATION.
        """
        try:
            with Session(self.engine) as session:
                modem = session.get(Modem, modem_id)
                if not modem:
                    return {
                        "success": False,
                        "error": "GSM module not found"
                    }
                
                if modem.status != ModemStatus.AVAILABLE:
                    return {
                        "success": False,
                        "error": f"GSM module not available. Status: {modem.status}"
                    }
                
                # Try to send SMS using real hardware
                result = await self._send_sms_via_hardware(modem, phone_number, message)
                
                # Create SMS record
                sms_message = SMSMessage(
                    modem_id=modem_id,
                    phone_number=phone_number,
                    message=message,
                    status=SMSStatus.SENT if result["success"] else SMSStatus.FAILED,
                    error_message=result.get("error") if not result["success"] else None
                )
                
                session.add(sms_message)
                session.commit()
                
                return result
                
        except Exception as e:
            logger.error("Failed to send SMS", error=str(e), modem_id=modem_id)
            return {
                "success": False,
                "error": "Failed to send SMS"
            }
    
    async def _send_sms_via_hardware(self, modem: Modem, phone_number: str, message: str) -> Dict[str, Any]:
        """
        Send SMS using actual GSM hardware.
        NO SIMULATION - only real hardware communication.
        """
        try:
            # Get or create serial connection
            if modem.id not in self.module_connections:
                try:
                    ser = serial.Serial(
                        port=modem.port,
                        baudrate=115200,
                        timeout=10,
                        write_timeout=10
                    )
                    self.module_connections[modem.id] = ser
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"Cannot connect to GSM module on {modem.port}: {str(e)}"
                    }
            
            ser = self.module_connections[modem.id]
            
            # Set SMS text mode
            ser.write(b'AT+CMGF=1\r\n')
            response = ser.readline().decode('utf-8', errors='ignore').strip()
            if 'OK' not in response:
                return {
                    "success": False,
                    "error": "Failed to set SMS text mode"
                }
            
            # Send SMS command
            sms_cmd = f'AT+CMGS="{phone_number}"\r\n'
            ser.write(sms_cmd.encode())
            
            # Wait for prompt
            response = ser.readline().decode('utf-8', errors='ignore').strip()
            if '>' not in response:
                return {
                    "success": False,
                    "error": "SMS prompt not received"
                }
            
            # Send message and Ctrl+Z
            ser.write(f'{message}\x1A'.encode())
            
            # Wait for response (can take up to 30 seconds)
            response = ""
            for _ in range(30):  # 30 second timeout
                try:
                    line = ser.readline().decode('utf-8', errors='ignore').strip()
                    response += line + " "
                    if 'OK' in line or 'ERROR' in line:
                        break
                except:
                    break
                await asyncio.sleep(1)
            
            if 'OK' in response:
                logger.info("SMS sent successfully", phone_number=phone_number, modem_id=modem.id)
                return {
                    "success": True,
                    "message": "SMS sent successfully"
                }
            else:
                logger.error("SMS sending failed", response=response, phone_number=phone_number)
                return {
                    "success": False,
                    "error": f"SMS sending failed: {response}"
                }
                
        except Exception as e:
            logger.error("Hardware SMS sending failed", error=str(e))
            return {
                "success": False,
                "error": f"Hardware communication failed: {str(e)}"
            }
    
    async def get_module_status(self, modem_id: UUID) -> Dict[str, Any]:
        """Get real-time status of a GSM module."""
        try:
            with Session(self.engine) as session:
                modem = session.get(Modem, modem_id)
                if not modem:
                    return {
                        "success": False,
                        "error": "GSM module not found"
                    }
                
                # Try to get real-time status from hardware
                hardware_status = await self._get_hardware_status(modem)
                
                return {
                    "success": True,
                    "modem_id": str(modem.id),
                    "phone_number": modem.phone_number,
                    "status": modem.status,
                    "port": modem.port,
                    "hardware_status": hardware_status,
                    "last_seen": modem.last_seen.isoformat() if modem.last_seen else None
                }
                
        except Exception as e:
            logger.error("Failed to get module status", error=str(e), modem_id=modem_id)
            return {
                "success": False,
                "error": "Failed to get module status"
            }
    
    async def _get_hardware_status(self, modem: Modem) -> Dict[str, Any]:
        """Get real-time hardware status - NO SIMULATION."""
        try:
            # Try to get current module info
            module_info = await self._identify_gsm_module(modem.port)
            if module_info:
                return {
                    "connected": True,
                    "sim_status": module_info.get('sim_status', 'Unknown'),
                    "signal_strength": module_info.get('signal_strength', 'Unknown'),
                    "last_check": datetime.utcnow().isoformat()
                }
            else:
                return {
                    "connected": False,
                    "error": "Cannot communicate with GSM module",
                    "last_check": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            return {
                "connected": False,
                "error": str(e),
                "last_check": datetime.utcnow().isoformat()
            }
    
    async def get_available_modules_count(self) -> int:
        """
        Get count of available GSM modules.
        Returns 0 if no real modules are connected - NO SIMULATION.
        """
        try:
            with Session(self.engine) as session:
                count = session.exec(
                    select(Modem).where(
                        Modem.status == ModemStatus.AVAILABLE
                    )
                ).all()
                
                # Verify each module is actually available by checking hardware
                available_count = 0
                for modem in count:
                    hardware_status = await self._get_hardware_status(modem)
                    if hardware_status.get("connected", False):
                        available_count += 1
                
                return available_count
                
        except Exception as e:
            logger.error("Failed to get available modules count", error=str(e))
            return 0


# Dependency injection
def get_gsm_module_service() -> GSMModuleService:
    """Get GSM module service instance."""
    return GSMModuleService()