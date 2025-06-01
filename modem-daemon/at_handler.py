"""
AT Command Handler Module

This module implements comprehensive AT command handling for SIM900 modems,
providing robust communication, error handling, and advanced modem control
functionality for Project GeminiVoiceConnect.
"""

import asyncio
import re
import time
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass

import serial
import structlog

from config import ModemDaemonConfig


logger = structlog.get_logger(__name__)


class ATCommandStatus(str, Enum):
    """AT command execution status."""
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    NO_RESPONSE = "no_response"
    INVALID_RESPONSE = "invalid_response"


class ModemState(str, Enum):
    """Modem operational state."""
    DISCONNECTED = "disconnected"
    INITIALIZING = "initializing"
    READY = "ready"
    CALLING = "calling"
    IN_CALL = "in_call"
    SENDING_SMS = "sending_sms"
    ERROR = "error"
    RESETTING = "resetting"


@dataclass
class ATResponse:
    """
    AT command response container.
    
    Encapsulates the complete response from an AT command
    including status, data, and execution metadata.
    """
    command: str
    status: ATCommandStatus
    response: str
    data: Optional[Dict[str, Any]] = None
    execution_time: float = 0.0
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
    
    @property
    def is_success(self) -> bool:
        """Check if command was successful."""
        return self.status == ATCommandStatus.SUCCESS
    
    @property
    def is_error(self) -> bool:
        """Check if command failed."""
        return self.status == ATCommandStatus.ERROR


class ATCommandHandler:
    """
    Comprehensive AT command handler for SIM900 modems.
    
    Provides robust AT command execution, response parsing,
    error handling, and advanced modem control functionality.
    """
    
    def __init__(self, config: ModemDaemonConfig):
        """
        Initialize AT command handler.
        
        Args:
            config: Modem daemon configuration
        """
        self.config = config
        self.serial_connection: Optional[serial.Serial] = None
        self.state = ModemState.DISCONNECTED
        self.command_queue = asyncio.Queue(maxsize=config.command_queue_size)
        self.response_buffer = []
        self.last_response_time = None
        self.consecutive_errors = 0
        self.initialization_complete = False
        
        # Command patterns and responses
        self.response_patterns = {
            'OK': re.compile(r'^OK$'),
            'ERROR': re.compile(r'^ERROR$'),
            'CME_ERROR': re.compile(r'^\+CME ERROR: (\d+)$'),
            'CMS_ERROR': re.compile(r'^\+CMS ERROR: (\d+)$'),
            'RING': re.compile(r'^RING$'),
            'NO_CARRIER': re.compile(r'^NO CARRIER$'),
            'BUSY': re.compile(r'^BUSY$'),
            'NO_ANSWER': re.compile(r'^NO ANSWER$'),
            'CONNECT': re.compile(r'^CONNECT'),
        }
        
        # Modem information cache
        self.modem_info = {
            'manufacturer': None,
            'model': None,
            'revision': None,
            'imei': None,
            'imsi': None,
            'signal_strength': None,
            'network_status': None,
            'battery_level': None,
            'temperature': None
        }
    
    async def initialize(self) -> bool:
        """
        Initialize modem connection and perform setup.
        
        Returns:
            True if initialization successful
        """
        try:
            logger.info("Initializing modem connection", modem_id=self.config.modem_id)
            
            # Open serial connection
            if not await self._open_serial_connection():
                return False
            
            self.state = ModemState.INITIALIZING
            
            # Perform modem initialization sequence
            if not await self._perform_initialization_sequence():
                return False
            
            # Verify modem functionality
            if not await self._verify_modem_functionality():
                return False
            
            self.state = ModemState.READY
            self.initialization_complete = True
            self.consecutive_errors = 0
            
            logger.info("Modem initialization completed successfully",
                       modem_id=self.config.modem_id,
                       modem_info=self.modem_info)
            
            return True
            
        except Exception as e:
            logger.error("Modem initialization failed",
                        modem_id=self.config.modem_id,
                        error=str(e))
            self.state = ModemState.ERROR
            return False
    
    async def _open_serial_connection(self) -> bool:
        """Open serial connection to modem."""
        try:
            serial_config = self.config.get_serial_config()
            
            self.serial_connection = serial.Serial(**serial_config)
            
            # Wait for connection to stabilize
            await asyncio.sleep(1.0)
            
            # Clear any pending data
            self.serial_connection.reset_input_buffer()
            self.serial_connection.reset_output_buffer()
            
            logger.info("Serial connection opened",
                       device=self.config.modem_device,
                       baudrate=self.config.baudrate)
            
            return True
            
        except Exception as e:
            logger.error("Failed to open serial connection",
                        device=self.config.modem_device,
                        error=str(e))
            return False
    
    async def _perform_initialization_sequence(self) -> bool:
        """Perform complete modem initialization sequence."""
        try:
            # Basic AT command test
            response = await self.send_command("AT", timeout=5.0)
            if not response.is_success:
                logger.error("Basic AT command failed")
                return False
            
            # Disable echo
            response = await self.send_command("ATE0")
            if not response.is_success:
                logger.warning("Failed to disable echo")
            
            # Set error reporting format
            response = await self.send_command("AT+CMEE=2")
            if not response.is_success:
                logger.warning("Failed to set error reporting format")
            
            # Set SMS text mode
            response = await self.send_command("AT+CMGF=1")
            if not response.is_success:
                logger.warning("Failed to set SMS text mode")
            
            # Enable caller ID
            response = await self.send_command("AT+CLIP=1")
            if not response.is_success:
                logger.warning("Failed to enable caller ID")
            
            # Set audio path for voice calls
            response = await self.send_command("AT+CHFA=0")
            if not response.is_success:
                logger.warning("Failed to set audio path")
            
            # Get modem information
            await self._get_modem_information()
            
            # Check network registration
            await self._check_network_registration()
            
            return True
            
        except Exception as e:
            logger.error("Initialization sequence failed", error=str(e))
            return False
    
    async def _verify_modem_functionality(self) -> bool:
        """Verify modem functionality after initialization."""
        try:
            # Check signal strength
            signal_response = await self.send_command("AT+CSQ")
            if signal_response.is_success:
                signal_strength = self._parse_signal_strength(signal_response.response)
                if signal_strength < self.config.signal_strength_threshold:
                    logger.warning("Low signal strength",
                                 signal_strength=signal_strength,
                                 threshold=self.config.signal_strength_threshold)
            
            # Check SIM card status
            sim_response = await self.send_command("AT+CPIN?")
            if not sim_response.is_success or "READY" not in sim_response.response:
                logger.error("SIM card not ready", response=sim_response.response)
                return False
            
            # Check network registration
            network_response = await self.send_command("AT+CREG?")
            if network_response.is_success:
                network_status = self._parse_network_status(network_response.response)
                if network_status not in [1, 5]:  # 1=home, 5=roaming
                    logger.warning("Not registered to network", status=network_status)
            
            return True
            
        except Exception as e:
            logger.error("Modem functionality verification failed", error=str(e))
            return False
    
    async def send_command(self, command: str, timeout: Optional[float] = None,
                          retries: Optional[int] = None) -> ATResponse:
        """
        Send AT command and wait for response.
        
        Args:
            command: AT command to send
            timeout: Command timeout (uses config default if None)
            retries: Number of retries (uses config default if None)
            
        Returns:
            AT command response
        """
        if timeout is None:
            timeout = self.config.at_command_timeout
        if retries is None:
            retries = self.config.at_command_retries
        
        start_time = time.time()
        
        for attempt in range(retries + 1):
            try:
                response = await self._execute_command(command, timeout)
                
                if response.is_success:
                    self.consecutive_errors = 0
                    return response
                
                if attempt < retries:
                    logger.warning("AT command failed, retrying",
                                 command=command,
                                 attempt=attempt + 1,
                                 status=response.status)
                    await asyncio.sleep(0.5)  # Brief delay before retry
                
            except Exception as e:
                logger.error("AT command execution error",
                           command=command,
                           attempt=attempt + 1,
                           error=str(e))
                
                if attempt < retries:
                    await asyncio.sleep(1.0)  # Longer delay on exception
        
        # All retries failed
        self.consecutive_errors += 1
        execution_time = time.time() - start_time
        
        logger.error("AT command failed after all retries",
                    command=command,
                    retries=retries,
                    consecutive_errors=self.consecutive_errors)
        
        return ATResponse(
            command=command,
            status=ATCommandStatus.ERROR,
            response="Failed after all retries",
            execution_time=execution_time
        )
    
    async def _execute_command(self, command: str, timeout: float) -> ATResponse:
        """Execute single AT command."""
        if not self.serial_connection or not self.serial_connection.is_open:
            return ATResponse(
                command=command,
                status=ATCommandStatus.ERROR,
                response="Serial connection not available"
            )
        
        start_time = time.time()
        
        try:
            # Clear input buffer
            self.serial_connection.reset_input_buffer()
            
            # Send command
            command_bytes = f"{command}\r\n".encode('utf-8')
            self.serial_connection.write(command_bytes)
            self.serial_connection.flush()
            
            logger.debug("AT command sent", command=command)
            
            # Read response
            response_lines = []
            end_time = start_time + timeout
            
            while time.time() < end_time:
                if self.serial_connection.in_waiting > 0:
                    line = self.serial_connection.readline().decode('utf-8').strip()
                    
                    if line:
                        response_lines.append(line)
                        logger.debug("AT response line", line=line)
                        
                        # Check for terminal responses
                        if self._is_terminal_response(line):
                            break
                
                await asyncio.sleep(0.01)  # Small delay to prevent busy waiting
            
            execution_time = time.time() - start_time
            response_text = '\n'.join(response_lines)
            
            # Parse response status
            status = self._parse_response_status(response_lines)
            
            # Extract data if available
            data = self._extract_response_data(command, response_lines)
            
            return ATResponse(
                command=command,
                status=status,
                response=response_text,
                data=data,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error("AT command execution exception",
                        command=command,
                        error=str(e))
            
            return ATResponse(
                command=command,
                status=ATCommandStatus.ERROR,
                response=f"Exception: {str(e)}",
                execution_time=execution_time
            )
    
    def _is_terminal_response(self, line: str) -> bool:
        """Check if response line is terminal (ends command)."""
        terminal_responses = ['OK', 'ERROR', 'NO CARRIER', 'BUSY', 'NO ANSWER']
        
        if line in terminal_responses:
            return True
        
        # Check for error codes
        if line.startswith('+CME ERROR:') or line.startswith('+CMS ERROR:'):
            return True
        
        return False
    
    def _parse_response_status(self, response_lines: List[str]) -> ATCommandStatus:
        """Parse response status from response lines."""
        if not response_lines:
            return ATCommandStatus.NO_RESPONSE
        
        last_line = response_lines[-1]
        
        if last_line == 'OK':
            return ATCommandStatus.SUCCESS
        elif last_line == 'ERROR':
            return ATCommandStatus.ERROR
        elif last_line.startswith('+CME ERROR:') or last_line.startswith('+CMS ERROR:'):
            return ATCommandStatus.ERROR
        elif last_line in ['NO CARRIER', 'BUSY', 'NO ANSWER']:
            return ATCommandStatus.ERROR
        
        return ATCommandStatus.INVALID_RESPONSE
    
    def _extract_response_data(self, command: str, response_lines: List[str]) -> Optional[Dict[str, Any]]:
        """Extract structured data from command response."""
        data = {}
        
        # Remove echo and terminal response
        data_lines = [line for line in response_lines 
                     if line != command and not self._is_terminal_response(line)]
        
        if not data_lines:
            return None
        
        # Command-specific parsing
        if command.startswith('AT+CSQ'):
            data.update(self._parse_signal_quality(data_lines))
        elif command.startswith('AT+CREG'):
            data.update(self._parse_network_registration(data_lines))
        elif command.startswith('AT+CPIN'):
            data.update(self._parse_sim_status(data_lines))
        elif command.startswith('AT+CGMI'):
            data['manufacturer'] = data_lines[0] if data_lines else None
        elif command.startswith('AT+CGMM'):
            data['model'] = data_lines[0] if data_lines else None
        elif command.startswith('AT+CGMR'):
            data['revision'] = data_lines[0] if data_lines else None
        elif command.startswith('AT+CGSN'):
            data['imei'] = data_lines[0] if data_lines else None
        
        return data if data else None
    
    def _parse_signal_quality(self, lines: List[str]) -> Dict[str, Any]:
        """Parse signal quality response."""
        data = {}
        for line in lines:
            if line.startswith('+CSQ:'):
                parts = line.replace('+CSQ:', '').strip().split(',')
                if len(parts) >= 2:
                    rssi = int(parts[0])
                    ber = int(parts[1])
                    
                    # Convert RSSI to dBm
                    if rssi == 99:
                        signal_dbm = None
                    else:
                        signal_dbm = -113 + (rssi * 2)
                    
                    data.update({
                        'rssi': rssi,
                        'ber': ber,
                        'signal_dbm': signal_dbm,
                        'signal_strength': rssi
                    })
        return data
    
    def _parse_network_registration(self, lines: List[str]) -> Dict[str, Any]:
        """Parse network registration response."""
        data = {}
        for line in lines:
            if line.startswith('+CREG:'):
                parts = line.replace('+CREG:', '').strip().split(',')
                if len(parts) >= 2:
                    status = int(parts[1])
                    data['network_status'] = status
                    data['registered'] = status in [1, 5]
        return data
    
    def _parse_sim_status(self, lines: List[str]) -> Dict[str, Any]:
        """Parse SIM card status response."""
        data = {}
        for line in lines:
            if line.startswith('+CPIN:'):
                status = line.replace('+CPIN:', '').strip()
                data['sim_status'] = status
                data['sim_ready'] = status == 'READY'
        return data
    
    async def _get_modem_information(self) -> None:
        """Get comprehensive modem information."""
        try:
            # Manufacturer
            response = await self.send_command("AT+CGMI")
            if response.is_success and response.data:
                self.modem_info['manufacturer'] = response.data.get('manufacturer')
            
            # Model
            response = await self.send_command("AT+CGMM")
            if response.is_success and response.data:
                self.modem_info['model'] = response.data.get('model')
            
            # Revision
            response = await self.send_command("AT+CGMR")
            if response.is_success and response.data:
                self.modem_info['revision'] = response.data.get('revision')
            
            # IMEI
            response = await self.send_command("AT+CGSN")
            if response.is_success and response.data:
                self.modem_info['imei'] = response.data.get('imei')
            
        except Exception as e:
            logger.error("Failed to get modem information", error=str(e))
    
    async def _check_network_registration(self) -> None:
        """Check network registration status."""
        try:
            response = await self.send_command("AT+CREG?")
            if response.is_success and response.data:
                self.modem_info.update(response.data)
            
        except Exception as e:
            logger.error("Failed to check network registration", error=str(e))
    
    def _parse_signal_strength(self, response: str) -> int:
        """Parse signal strength from CSQ response."""
        try:
            for line in response.split('\n'):
                if line.startswith('+CSQ:'):
                    rssi = int(line.split(':')[1].split(',')[0].strip())
                    return rssi
        except Exception:
            pass
        return 0
    
    def _parse_network_status(self, response: str) -> int:
        """Parse network registration status."""
        try:
            for line in response.split('\n'):
                if line.startswith('+CREG:'):
                    parts = line.split(':')[1].split(',')
                    if len(parts) >= 2:
                        return int(parts[1].strip())
        except Exception:
            pass
        return 0
    
    async def reset_modem(self) -> bool:
        """Reset modem to recover from errors."""
        try:
            logger.info("Resetting modem", modem_id=self.config.modem_id)
            self.state = ModemState.RESETTING
            
            # Send reset command
            response = await self.send_command("ATZ", timeout=30.0)
            
            if response.is_success:
                # Wait for modem to restart
                await asyncio.sleep(5.0)
                
                # Re-initialize
                if await self.initialize():
                    logger.info("Modem reset successful")
                    return True
            
            logger.error("Modem reset failed")
            self.state = ModemState.ERROR
            return False
            
        except Exception as e:
            logger.error("Modem reset exception", error=str(e))
            self.state = ModemState.ERROR
            return False
    
    async def cleanup(self) -> None:
        """Cleanup resources and close connections."""
        try:
            if self.serial_connection and self.serial_connection.is_open:
                self.serial_connection.close()
            
            self.state = ModemState.DISCONNECTED
            logger.info("AT command handler cleanup completed")
            
        except Exception as e:
            logger.error("AT command handler cleanup error", error=str(e))
    
    def get_modem_status(self) -> Dict[str, Any]:
        """Get current modem status and information."""
        return {
            'modem_id': self.config.modem_id,
            'state': self.state.value,
            'initialized': self.initialization_complete,
            'consecutive_errors': self.consecutive_errors,
            'last_response_time': self.last_response_time.isoformat() if self.last_response_time else None,
            'modem_info': self.modem_info,
            'serial_connected': self.serial_connection.is_open if self.serial_connection else False
        }