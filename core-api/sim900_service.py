"""
SIM900 GSM Module Service - Specialized for SIM900 modules.

This service provides optimized communication with SIM900 GSM modules
for SMS sending and voice call management.
"""

import asyncio
import serial
import serial.tools.list_ports
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from uuid import UUID, uuid4
import structlog
from sqlmodel import Session, select
from database import get_db_manager
from models import Modem, ModemStatus, SMSMessage, SMSStatus

logger = structlog.get_logger(__name__)


class SIM900Service:
    """Service for managing SIM900 GSM modules."""
    
    def __init__(self):
        self.db_manager = get_db_manager()
        self.engine = self.db_manager.engine
        self.connected_modules = {}  # port -> connection
        self.module_info_cache = {}  # port -> module_info
        
        # SIM900 specific settings
        self.sim900_baudrates = [9600, 19200, 38400, 57600, 115200]
        self.default_baudrate = 9600  # SIM900 default
        self.command_timeout = 10
        self.sms_timeout = 30
    
    async def scan_for_sim900_modules(self) -> Dict[str, Any]:
        """
        Scan for SIM900 GSM modules specifically.
        Returns actual hardware found, not simulated data.
        """
        try:
            found_modules = []
            
            # Scan all available serial ports
            ports = serial.tools.list_ports.comports()
            
            for port in ports:
                try:
                    # Try to identify SIM900 module
                    module_info = await self._identify_sim900_module(port.device)
                    if module_info:
                        found_modules.append({
                            "port": port.device,
                            "description": port.description,
                            "manufacturer": port.manufacturer,
                            "vid": port.vid,
                            "pid": port.pid,
                            "serial_number": port.serial_number,
                            "module_info": module_info,
                            "module_type": "SIM900"
                        })
                        
                except Exception as e:
                    logger.debug("Failed to check port for SIM900", port=port.device, error=str(e))
                    continue
            
            logger.info("SIM900 module scan completed", found_count=len(found_modules))
            
            return {
                "success": True,
                "modules_found": len(found_modules),
                "modules": found_modules,
                "message": f"Found {len(found_modules)} SIM900 modules" if found_modules else "No SIM900 modules detected"
            }
            
        except Exception as e:
            logger.error("SIM900 module scan failed", error=str(e))
            return {
                "success": False,
                "error": "Failed to scan for SIM900 modules",
                "modules_found": 0,
                "modules": []
            }
    
    async def _identify_sim900_module(self, port: str) -> Optional[Dict[str, str]]:
        """
        Try to identify if a serial port has a SIM900 module.
        Tests multiple baudrates and SIM900-specific commands.
        """
        for baudrate in self.sim900_baudrates:
            try:
                ser = serial.Serial(
                    port=port,
                    baudrate=baudrate,
                    timeout=2,
                    write_timeout=2,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE
                )
                
                try:
                    # Clear any pending data
                    ser.flushInput()
                    ser.flushOutput()
                    time.sleep(0.1)
                    
                    # Send AT command
                    ser.write(b'AT\r\n')
                    time.sleep(0.5)
                    response = ser.read_all().decode('utf-8', errors='ignore').strip()
                    
                    if 'OK' in response:
                        # Get module information
                        module_info = {"baudrate": baudrate}
                        
                        # Get manufacturer (should be SIMCOM for SIM900)
                        ser.write(b'AT+CGMI\r\n')
                        time.sleep(0.5)
                        manufacturer_response = ser.read_all().decode('utf-8', errors='ignore').strip()
                        if 'SIMCOM' in manufacturer_response.upper():
                            module_info['manufacturer'] = 'SIMCOM'
                        
                        # Get model (should contain SIM900)
                        ser.write(b'AT+CGMM\r\n')
                        time.sleep(0.5)
                        model_response = ser.read_all().decode('utf-8', errors='ignore').strip()
                        if 'SIM900' in model_response.upper():
                            module_info['model'] = 'SIM900'
                            module_info['is_sim900'] = True
                        
                        # Get IMEI
                        ser.write(b'AT+CGSN\r\n')
                        time.sleep(0.5)
                        imei_response = ser.read_all().decode('utf-8', errors='ignore').strip()
                        lines = imei_response.split('\n')
                        for line in lines:
                            line = line.strip()
                            if len(line) == 15 and line.isdigit():
                                module_info['imei'] = line
                                break
                        
                        # Get SIM card status
                        ser.write(b'AT+CPIN?\r\n')
                        time.sleep(0.5)
                        sim_response = ser.read_all().decode('utf-8', errors='ignore').strip()
                        if 'READY' in sim_response:
                            module_info['sim_status'] = 'READY'
                        elif 'SIM PIN' in sim_response:
                            module_info['sim_status'] = 'SIM PIN'
                        else:
                            module_info['sim_status'] = 'NOT_READY'
                        
                        # Get signal strength
                        ser.write(b'AT+CSQ\r\n')
                        time.sleep(0.5)
                        signal_response = ser.read_all().decode('utf-8', errors='ignore').strip()
                        if '+CSQ:' in signal_response:
                            try:
                                signal_part = signal_response.split('+CSQ:')[1].split(',')[0].strip()
                                signal_strength = int(signal_part)
                                module_info['signal_strength'] = signal_strength
                                module_info['signal_quality'] = self._get_signal_quality(signal_strength)
                            except:
                                module_info['signal_strength'] = 'Unknown'
                        
                        # Get network registration
                        ser.write(b'AT+CREG?\r\n')
                        time.sleep(0.5)
                        network_response = ser.read_all().decode('utf-8', errors='ignore').strip()
                        if '+CREG:' in network_response:
                            if ',1' in network_response or ',5' in network_response:
                                module_info['network_status'] = 'REGISTERED'
                            else:
                                module_info['network_status'] = 'NOT_REGISTERED'
                        
                        # If we found SIM900, cache the info and return
                        if module_info.get('is_sim900', False):
                            self.module_info_cache[port] = module_info
                            logger.info("SIM900 module identified", port=port, baudrate=baudrate)
                            return module_info
                        
                finally:
                    ser.close()
                    
            except Exception as e:
                logger.debug("Failed to test SIM900 on port", port=port, baudrate=baudrate, error=str(e))
                continue
        
        return None
    
    def _get_signal_quality(self, signal_strength: int) -> str:
        """Convert signal strength to quality description."""
        if signal_strength == 99:
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
    
    async def add_sim900_module(self, port: str, phone_number: str, api_key: str) -> Dict[str, Any]:
        """
        Add a SIM900 module to the system.
        Only works with actual SIM900 hardware.
        """
        try:
            # First verify the module exists and is SIM900
            module_info = await self._identify_sim900_module(port)
            if not module_info:
                return {
                    "success": False,
                    "error": f"No SIM900 module found on port {port}"
                }
            
            if not module_info.get('is_sim900', False):
                return {
                    "success": False,
                    "error": f"Module on port {port} is not a SIM900"
                }
            
            # Check if SIM card is ready
            if module_info.get('sim_status') != 'READY':
                return {
                    "success": False,
                    "error": f"SIM card not ready on port {port}. Status: {module_info.get('sim_status', 'Unknown')}"
                }
            
            # Check network registration
            if module_info.get('network_status') != 'REGISTERED':
                return {
                    "success": False,
                    "error": f"SIM900 not registered to network on port {port}"
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
                        "error": f"SIM900 module on port {port} already exists in system"
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
                    manufacturer=module_info.get('manufacturer', 'SIMCOM'),
                    model=module_info.get('model', 'SIM900'),
                    signal_strength=str(module_info.get('signal_strength', 'Unknown')),
                    last_seen=datetime.utcnow(),
                    baudrate=module_info.get('baudrate', 9600)
                )
                
                session.add(modem)
                session.commit()
                session.refresh(modem)
                
                logger.info("SIM900 module added successfully", 
                           modem_id=modem.id, 
                           phone_number=phone_number, 
                           port=port,
                           baudrate=module_info.get('baudrate'))
                
                return {
                    "success": True,
                    "modem_id": str(modem.id),
                    "phone_number": phone_number,
                    "port": port,
                    "module_info": module_info,
                    "message": "SIM900 module added successfully"
                }
                
        except Exception as e:
            logger.error("Failed to add SIM900 module", error=str(e), port=port)
            return {
                "success": False,
                "error": "Failed to add SIM900 module"
            }
    
    async def send_sms_via_sim900(self, modem_id: UUID, phone_number: str, message: str) -> Dict[str, Any]:
        """
        Send SMS using SIM900 module with optimized commands.
        """
        try:
            with Session(self.engine) as session:
                modem = session.get(Modem, modem_id)
                if not modem:
                    return {
                        "success": False,
                        "error": "SIM900 module not found"
                    }
                
                if modem.status != ModemStatus.AVAILABLE:
                    return {
                        "success": False,
                        "error": f"SIM900 module not available. Status: {modem.status}"
                    }
                
                # Send SMS using SIM900 optimized method
                result = await self._send_sms_sim900_optimized(modem, phone_number, message)
                
                # Create SMS record
                sms_message = SMSMessage(
                    modem_id=modem_id,
                    phone_number=phone_number,
                    message_content=message,
                    message_type="outbound",
                    status=SMSStatus.SENT if result["success"] else SMSStatus.FAILED,
                    error_message=result.get("error") if not result["success"] else None,
                    sent_at=datetime.utcnow() if result["success"] else None
                )
                
                session.add(sms_message)
                session.commit()
                
                return result
                
        except Exception as e:
            logger.error("Failed to send SMS via SIM900", error=str(e), modem_id=modem_id)
            return {
                "success": False,
                "error": "Failed to send SMS"
            }
    
    async def _send_sms_sim900_optimized(self, modem: Modem, phone_number: str, message: str) -> Dict[str, Any]:
        """
        Send SMS using SIM900 with optimized AT commands.
        """
        try:
            # Get baudrate from modem or use default
            baudrate = getattr(modem, 'baudrate', self.default_baudrate)
            
            # Create serial connection
            ser = serial.Serial(
                port=modem.port,
                baudrate=baudrate,
                timeout=self.command_timeout,
                write_timeout=self.command_timeout,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            
            try:
                # Clear buffers
                ser.flushInput()
                ser.flushOutput()
                time.sleep(0.1)
                
                # Test connection
                ser.write(b'AT\r\n')
                time.sleep(0.5)
                response = ser.read_all().decode('utf-8', errors='ignore')
                if 'OK' not in response:
                    return {
                        "success": False,
                        "error": "SIM900 not responding to AT commands"
                    }
                
                # Set SMS text mode
                ser.write(b'AT+CMGF=1\r\n')
                time.sleep(0.5)
                response = ser.read_all().decode('utf-8', errors='ignore')
                if 'OK' not in response:
                    return {
                        "success": False,
                        "error": "Failed to set SMS text mode"
                    }
                
                # Set SMS character set to GSM
                ser.write(b'AT+CSCS="GSM"\r\n')
                time.sleep(0.5)
                response = ser.read_all().decode('utf-8', errors='ignore')
                
                # Send SMS command
                sms_cmd = f'AT+CMGS="{phone_number}"\r\n'
                ser.write(sms_cmd.encode())
                time.sleep(1)
                
                # Wait for prompt
                response = ser.read_all().decode('utf-8', errors='ignore')
                if '>' not in response:
                    return {
                        "success": False,
                        "error": "SMS prompt not received from SIM900"
                    }
                
                # Send message and Ctrl+Z
                message_with_end = f'{message}\x1A'
                ser.write(message_with_end.encode('utf-8', errors='ignore'))
                
                # Wait for response (SIM900 can take up to 30 seconds)
                start_time = time.time()
                response = ""
                while time.time() - start_time < self.sms_timeout:
                    if ser.in_waiting > 0:
                        new_data = ser.read_all().decode('utf-8', errors='ignore')
                        response += new_data
                        
                        if 'OK' in response:
                            logger.info("SMS sent successfully via SIM900", 
                                       phone_number=phone_number, 
                                       modem_id=modem.id)
                            return {
                                "success": True,
                                "message": "SMS sent successfully via SIM900"
                            }
                        elif 'ERROR' in response:
                            logger.error("SMS sending failed on SIM900", 
                                        response=response, 
                                        phone_number=phone_number)
                            return {
                                "success": False,
                                "error": f"SIM900 SMS error: {response}"
                            }
                    
                    await asyncio.sleep(0.1)
                
                return {
                    "success": False,
                    "error": "SMS sending timeout on SIM900"
                }
                
            finally:
                ser.close()
                
        except Exception as e:
            logger.error("SIM900 SMS sending failed", error=str(e))
            return {
                "success": False,
                "error": f"SIM900 communication failed: {str(e)}"
            }
    
    async def get_sim900_status(self, modem_id: UUID) -> Dict[str, Any]:
        """Get real-time status of a SIM900 module."""
        try:
            with Session(self.engine) as session:
                modem = session.get(Modem, modem_id)
                if not modem:
                    return {
                        "success": False,
                        "error": "SIM900 module not found"
                    }
                
                # Get real-time status from SIM900
                hardware_status = await self._get_sim900_hardware_status(modem)
                
                return {
                    "success": True,
                    "modem_id": str(modem.id),
                    "phone_number": modem.phone_number,
                    "status": modem.status,
                    "port": modem.port,
                    "model": "SIM900",
                    "hardware_status": hardware_status,
                    "last_seen": modem.last_seen.isoformat() if modem.last_seen else None
                }
                
        except Exception as e:
            logger.error("Failed to get SIM900 status", error=str(e), modem_id=modem_id)
            return {
                "success": False,
                "error": "Failed to get SIM900 status"
            }
    
    async def _get_sim900_hardware_status(self, modem: Modem) -> Dict[str, Any]:
        """Get real-time SIM900 hardware status."""
        try:
            # Use cached info if available and recent
            cached_info = self.module_info_cache.get(modem.port)
            if cached_info:
                cache_time = cached_info.get('last_check')
                if cache_time and (datetime.utcnow() - cache_time).seconds < 60:
                    return cached_info
            
            # Get fresh status from SIM900
            module_info = await self._identify_sim900_module(modem.port)
            if module_info:
                module_info['last_check'] = datetime.utcnow()
                self.module_info_cache[modem.port] = module_info
                
                return {
                    "connected": True,
                    "sim_status": module_info.get('sim_status', 'Unknown'),
                    "signal_strength": module_info.get('signal_strength', 'Unknown'),
                    "signal_quality": module_info.get('signal_quality', 'Unknown'),
                    "network_status": module_info.get('network_status', 'Unknown'),
                    "baudrate": module_info.get('baudrate', 9600),
                    "last_check": datetime.utcnow().isoformat()
                }
            else:
                return {
                    "connected": False,
                    "error": "Cannot communicate with SIM900 module",
                    "last_check": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            return {
                "connected": False,
                "error": str(e),
                "last_check": datetime.utcnow().isoformat()
            }


# Dependency injection
def get_sim900_service() -> SIM900Service:
    """Get SIM900 service instance."""
    return SIM900Service()