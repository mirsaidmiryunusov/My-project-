"""
Local GSM SMS Service Implementation
Uses local SIM900 GSM modules for SMS sending
"""

import os
import random
import string
import asyncio
import serial
import time
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import structlog
from sqlmodel import Session, select

from database import get_session
from models import SMSMessage, SMSStatus, Modem, ModemStatus, PhoneNumberType

logger = structlog.get_logger(__name__)

class SIM900Module:
    """SIM900 GSM module interface"""
    
    def __init__(self, port: str, baudrate: int = 9600, timeout: int = 10):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_connection = None
        self.is_connected = False
    
    async def connect(self) -> bool:
        """Connect to SIM900 module"""
        try:
            self.serial_connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            
            # Test connection with AT command
            if await self._send_at_command("AT"):
                self.is_connected = True
                logger.info(f"Connected to SIM900 module on {self.port}")
                
                # Initialize module
                await self._initialize_module()
                return True
            else:
                logger.error(f"Failed to connect to SIM900 module on {self.port}")
                return False
                
        except Exception as e:
            logger.error(f"Error connecting to SIM900 module on {self.port}: {str(e)}")
            return False
    
    async def disconnect(self):
        """Disconnect from SIM900 module"""
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
            self.is_connected = False
            logger.info(f"Disconnected from SIM900 module on {self.port}")
    
    async def _initialize_module(self) -> bool:
        """Initialize SIM900 module for SMS"""
        try:
            # Set SMS text mode
            if not await self._send_at_command("AT+CMGF=1"):
                return False
            
            # Set character set to GSM
            if not await self._send_at_command("AT+CSCS=\"GSM\""):
                return False
            
            # Check SIM card status
            if not await self._send_at_command("AT+CPIN?"):
                return False
            
            # Check network registration
            response = await self._send_at_command("AT+CREG?", expect_response=True)
            if not response or "0,1" not in response and "0,5" not in response:
                logger.warning(f"SIM900 module on {self.port} not registered to network")
                return False
            
            # Check signal strength
            response = await self._send_at_command("AT+CSQ", expect_response=True)
            if response:
                logger.info(f"SIM900 module on {self.port} signal strength: {response}")
            
            logger.info(f"SIM900 module on {self.port} initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing SIM900 module on {self.port}: {str(e)}")
            return False
    
    async def _send_at_command(self, command: str, expect_response: bool = False, timeout: int = 10) -> Optional[str]:
        """Send AT command to SIM900 module"""
        try:
            if not self.serial_connection or not self.serial_connection.is_open:
                return None
            
            # Clear input buffer
            self.serial_connection.reset_input_buffer()
            
            # Send command
            self.serial_connection.write(f"{command}\r\n".encode())
            
            # Wait for response
            start_time = time.time()
            response_lines = []
            
            while time.time() - start_time < timeout:
                if self.serial_connection.in_waiting > 0:
                    line = self.serial_connection.readline().decode().strip()
                    if line:
                        response_lines.append(line)
                        
                        # Check for command completion
                        if line == "OK":
                            if expect_response:
                                # Return the response content (excluding command echo and OK)
                                content = [l for l in response_lines if l != command and l != "OK"]
                                return "\n".join(content) if content else "OK"
                            return "OK"
                        elif line == "ERROR" or line.startswith("+CME ERROR") or line.startswith("+CMS ERROR"):
                            logger.error(f"AT command error: {line}")
                            return None
                
                await asyncio.sleep(0.1)
            
            logger.error(f"AT command timeout: {command}")
            return None
            
        except Exception as e:
            logger.error(f"Error sending AT command {command}: {str(e)}")
            return None
    
    async def send_sms(self, phone_number: str, message: str) -> Dict[str, Any]:
        """Send SMS via SIM900 module"""
        try:
            if not self.is_connected:
                return {
                    'success': False,
                    'error': 'Module not connected'
                }
            
            # Clean phone number
            clean_phone = phone_number.replace('+', '').replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
            
            # Start SMS sending
            sms_command = f'AT+CMGS="{clean_phone}"'
            self.serial_connection.write(f"{sms_command}\r\n".encode())
            
            # Wait for prompt (>)
            start_time = time.time()
            while time.time() - start_time < 10:
                if self.serial_connection.in_waiting > 0:
                    response = self.serial_connection.read(self.serial_connection.in_waiting).decode()
                    if '>' in response:
                        break
                await asyncio.sleep(0.1)
            else:
                return {
                    'success': False,
                    'error': 'SMS prompt timeout'
                }
            
            # Send message content
            self.serial_connection.write(f"{message}\x1A".encode())  # \x1A is Ctrl+Z
            
            # Wait for response
            start_time = time.time()
            response_lines = []
            
            while time.time() - start_time < 30:  # SMS can take longer
                if self.serial_connection.in_waiting > 0:
                    line = self.serial_connection.readline().decode().strip()
                    if line:
                        response_lines.append(line)
                        
                        if line == "OK" or "+CMGS:" in line:
                            # Extract message reference if available
                            message_ref = None
                            for resp_line in response_lines:
                                if "+CMGS:" in resp_line:
                                    try:
                                        message_ref = resp_line.split(":")[1].strip()
                                    except:
                                        pass
                            
                            logger.info(f"SMS sent successfully via {self.port} to {phone_number}")
                            return {
                                'success': True,
                                'message_id': message_ref or f"sim900_{int(time.time())}",
                                'provider': f'sim900_{self.port}'
                            }
                        elif line == "ERROR" or "+CME ERROR" in line or "+CMS ERROR" in line:
                            error_msg = line
                            logger.error(f"SMS sending failed via {self.port}: {error_msg}")
                            return {
                                'success': False,
                                'error': f'SMS error: {error_msg}'
                            }
                
                await asyncio.sleep(0.1)
            
            return {
                'success': False,
                'error': 'SMS sending timeout'
            }
            
        except Exception as e:
            logger.error(f"Error sending SMS via {self.port}: {str(e)}")
            return {
                'success': False,
                'error': f'Exception: {str(e)}'
            }
    
    async def check_signal_strength(self) -> Optional[int]:
        """Check signal strength (0-31, 99=unknown)"""
        try:
            response = await self._send_at_command("AT+CSQ", expect_response=True)
            if response and "+CSQ:" in response:
                # Parse response like "+CSQ: 15,99"
                parts = response.split(":")[1].strip().split(",")
                return int(parts[0])
            return None
        except:
            return None
    
    async def get_network_info(self) -> Dict[str, Any]:
        """Get network registration info"""
        try:
            response = await self._send_at_command("AT+CREG?", expect_response=True)
            signal = await self.check_signal_strength()
            
            return {
                'registration': response,
                'signal_strength': signal,
                'connected': self.is_connected
            }
        except Exception as e:
            return {
                'error': str(e),
                'connected': self.is_connected
            }

class LocalGSMSMSService:
    """Local GSM SMS service using SIM900 modules"""
    
    def __init__(self):
        self.modules: Dict[str, SIM900Module] = {}
        self.initialized = False
    
    async def initialize(self):
        """Initialize GSM modules from database"""
        try:
            with Session(get_session().bind) as session:
                # Get all company modems (these are our GSM modules)
                stmt = select(Modem).where(
                    Modem.phone_number_type == PhoneNumberType.COMPANY,
                    Modem.status.in_([ModemStatus.AVAILABLE, ModemStatus.ASSIGNED])
                )
                modems = session.exec(stmt).all()
                
                for modem in modems:
                    # Try to connect to the module
                    # Port mapping: you'll need to configure this based on your setup
                    port = self._get_port_for_modem(modem.modem_id)
                    if port:
                        module = SIM900Module(port)
                        if await module.connect():
                            self.modules[modem.id] = module
                            logger.info(f"Initialized GSM module {modem.modem_id} on {port}")
                        else:
                            logger.error(f"Failed to initialize GSM module {modem.modem_id} on {port}")
                
                self.initialized = True
                logger.info(f"Initialized {len(self.modules)} GSM modules")
                
        except Exception as e:
            logger.error(f"Error initializing GSM modules: {str(e)}")
    
    def _get_port_for_modem(self, modem_id: str) -> Optional[str]:
        """
        Map modem ID to serial port
        Configure this based on your hardware setup
        """
        # Example mapping - adjust based on your setup
        port_mapping = {
            'COMPANY_001': '/dev/ttyUSB0',
            'COMPANY_002': '/dev/ttyUSB1',
            'COMPANY_003': '/dev/ttyUSB2',
            # Add more mappings as needed
        }
        
        # For Windows, use COM ports
        if os.name == 'nt':
            port_mapping = {
                'COMPANY_001': 'COM3',
                'COMPANY_002': 'COM4',
                'COMPANY_003': 'COM5',
            }
        
        return port_mapping.get(modem_id)
    
    def generate_verification_code(self) -> str:
        """Generate 6-digit verification code"""
        return ''.join(random.choices(string.digits, k=6))
    
    async def send_verification_sms(self, phone_number: str) -> Dict[str, Any]:
        """Send verification SMS using local GSM modules"""
        
        if not self.initialized:
            await self.initialize()
        
        if not self.modules:
            # Fallback to development mode if no modules available
            logger.warning("No GSM modules available, using development mode")
            return await self._send_development_sms(phone_number)
        
        # Generate verification code
        verification_code = self.generate_verification_code()
        
        # Create SMS message
        message = f"Ваш код подтверждения для AI Call Center: {verification_code}. Код действителен 10 минут."
        
        # Try to send SMS using available modules
        for modem_id, module in self.modules.items():
            try:
                result = await module.send_sms(phone_number, message)
                
                # Store in database
                with Session(get_session().bind) as session:
                    sms_message = SMSMessage(
                        phone_number=phone_number,
                        message=message,
                        verification_code=verification_code,
                        status=SMSStatus.SENT if result['success'] else SMSStatus.FAILED,
                        provider=result.get('provider', f'sim900_{module.port}'),
                        external_id=result.get('message_id'),
                        expires_at=datetime.utcnow() + timedelta(minutes=10),
                        modem_id=modem_id
                    )
                    session.add(sms_message)
                    session.commit()
                    session.refresh(sms_message)
                
                if result['success']:
                    logger.info(
                        "SMS verification sent via local GSM",
                        phone=phone_number,
                        code=verification_code,
                        modem=modem_id,
                        port=module.port
                    )
                    
                    return {
                        'success': True,
                        'verification_code': verification_code,
                        'message_id': sms_message.id,
                        'provider': result.get('provider'),
                        'modem_id': modem_id
                    }
                else:
                    logger.error(f"Failed to send SMS via module {modem_id}: {result.get('error')}")
                    continue
                    
            except Exception as e:
                logger.error(f"Error with GSM module {modem_id}: {str(e)}")
                continue
        
        # If all modules failed, return error
        return {
            'success': False,
            'error': 'All GSM modules failed to send SMS'
        }
    
    async def _send_development_sms(self, phone_number: str) -> Dict[str, Any]:
        """Development mode SMS simulation"""
        verification_code = self.generate_verification_code()
        message = f"Ваш код подтверждения для AI Call Center: {verification_code}. Код действителен 10 минут."
        
        # Store in database
        with Session(get_session().bind) as session:
            sms_message = SMSMessage(
                phone_number=phone_number,
                message=message,
                verification_code=verification_code,
                status=SMSStatus.SENT,
                provider='development',
                external_id=f"dev_{random.randint(100000, 999999)}",
                expires_at=datetime.utcnow() + timedelta(minutes=10)
            )
            session.add(sms_message)
            session.commit()
            session.refresh(sms_message)
        
        logger.info("Development SMS sent", phone=phone_number, code=verification_code)
        
        return {
            'success': True,
            'verification_code': verification_code,
            'message_id': sms_message.id,
            'provider': 'development'
        }
    
    async def verify_code(self, phone_number: str, code: str) -> Dict[str, Any]:
        """Verify SMS code"""
        
        with Session(get_session().bind) as session:
            # Find the most recent SMS for this phone number
            stmt = select(SMSMessage).where(
                SMSMessage.phone_number == phone_number,
                SMSMessage.verification_code == code,
                SMSMessage.expires_at > datetime.utcnow(),
                SMSMessage.verified_at.is_(None)
            ).order_by(SMSMessage.created_at.desc())
            
            sms_message = session.exec(stmt).first()
            
            if not sms_message:
                return {
                    'success': False,
                    'error': 'Неверный или истекший код подтверждения'
                }
            
            # Mark as verified
            sms_message.verified_at = datetime.utcnow()
            sms_message.status = SMSStatus.DELIVERED
            session.add(sms_message)
            session.commit()
            
            logger.info("SMS code verified", phone=phone_number, code=code)
            
            return {
                'success': True,
                'message': 'Код подтверждения успешно проверен'
            }
    
    async def send_notification_sms(self, phone_number: str, message: str, modem_id: Optional[str] = None) -> Dict[str, Any]:
        """Send notification SMS"""
        
        if not self.initialized:
            await self.initialize()
        
        if not self.modules:
            logger.warning("No GSM modules available for notification SMS")
            return {
                'success': False,
                'error': 'No GSM modules available'
            }
        
        # Use specific modem if provided, otherwise use any available
        modules_to_try = [self.modules[modem_id]] if modem_id and modem_id in self.modules else list(self.modules.values())
        
        for module in modules_to_try:
            try:
                result = await module.send_sms(phone_number, message)
                
                # Store in database
                with Session(get_session().bind) as session:
                    sms_message = SMSMessage(
                        phone_number=phone_number,
                        message=message,
                        status=SMSStatus.SENT if result['success'] else SMSStatus.FAILED,
                        provider=result.get('provider', f'sim900_{module.port}'),
                        external_id=result.get('message_id'),
                        modem_id=modem_id
                    )
                    session.add(sms_message)
                    session.commit()
                
                if result['success']:
                    logger.info(
                        "Notification SMS sent via local GSM",
                        phone=phone_number,
                        modem=modem_id or 'auto',
                        port=module.port
                    )
                    return result
                else:
                    logger.error(f"Failed to send notification SMS: {result.get('error')}")
                    continue
                    
            except Exception as e:
                logger.error(f"Error sending notification SMS: {str(e)}")
                continue
        
        return {
            'success': False,
            'error': 'Failed to send notification SMS via all modules'
        }
    
    async def get_module_status(self) -> List[Dict[str, Any]]:
        """Get status of all GSM modules"""
        status_list = []
        
        for modem_id, module in self.modules.items():
            try:
                network_info = await module.get_network_info()
                status_list.append({
                    'modem_id': modem_id,
                    'port': module.port,
                    'connected': module.is_connected,
                    'network_info': network_info
                })
            except Exception as e:
                status_list.append({
                    'modem_id': modem_id,
                    'port': module.port,
                    'connected': False,
                    'error': str(e)
                })
        
        return status_list
    
    async def cleanup(self):
        """Cleanup and disconnect all modules"""
        for module in self.modules.values():
            await module.disconnect()
        self.modules.clear()
        self.initialized = False

# Global SMS service instance
local_gsm_sms_service = LocalGSMSMSService()

# Convenience functions
async def send_verification_sms(phone_number: str) -> Dict[str, Any]:
    """Send verification SMS via local GSM"""
    return await local_gsm_sms_service.send_verification_sms(phone_number)

async def verify_sms_code(phone_number: str, code: str) -> Dict[str, Any]:
    """Verify SMS code"""
    return await local_gsm_sms_service.verify_code(phone_number, code)

async def send_notification_sms(phone_number: str, message: str, modem_id: Optional[str] = None) -> Dict[str, Any]:
    """Send notification SMS via local GSM"""
    return await local_gsm_sms_service.send_notification_sms(phone_number, message, modem_id)

async def get_gsm_module_status() -> List[Dict[str, Any]]:
    """Get GSM module status"""
    return await local_gsm_sms_service.get_module_status()