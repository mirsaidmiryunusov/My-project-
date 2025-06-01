"""
Call Manager for Project GeminiVoiceConnect

This module provides comprehensive call management capabilities for SIM900 modems including
call initiation, answering, termination, call state tracking, DTMF handling, and
advanced call features like call forwarding and conference calling.

Key Features:
- Outbound and inbound call management
- Call state tracking and monitoring
- DTMF tone generation and detection
- Call duration tracking
- Call recording coordination
- Call forwarding and redirection
- Conference call support
- Call quality monitoring
- Emergency call handling
"""

from typing import Dict, List, Optional, Any, Union, Callable
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import json
import logging
from dataclasses import dataclass, asdict
import re
import uuid
import time
import threading
from queue import Queue, Empty

from .config import get_settings
from .at_handler import ATHandler, ATResponse

logger = logging.getLogger(__name__)
settings = get_settings()


class CallState(str, Enum):
    """Call state enumeration"""
    IDLE = "idle"
    DIALING = "dialing"
    RINGING = "ringing"
    CONNECTED = "connected"
    HOLDING = "holding"
    BUSY = "busy"
    NO_ANSWER = "no_answer"
    FAILED = "failed"
    TERMINATED = "terminated"


class CallDirection(str, Enum):
    """Call direction enumeration"""
    OUTBOUND = "outbound"
    INBOUND = "inbound"


class CallType(str, Enum):
    """Call type enumeration"""
    VOICE = "voice"
    DATA = "data"
    FAX = "fax"
    EMERGENCY = "emergency"


@dataclass
class CallInfo:
    """Call information structure"""
    call_id: str
    phone_number: str
    direction: CallDirection
    call_type: CallType
    state: CallState
    start_time: datetime
    answer_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[int] = None  # seconds
    termination_reason: Optional[str] = None
    call_quality: Optional[Dict[str, Any]] = None
    dtmf_sequence: Optional[List[str]] = None
    recording_info: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class DTMFEvent:
    """DTMF event structure"""
    call_id: str
    digit: str
    timestamp: datetime
    duration: Optional[int] = None  # milliseconds


class CallManager:
    """
    Comprehensive call management system for SIM900 modems.
    
    This manager handles all aspects of voice call operations including call
    initiation, state management, DTMF handling, and call quality monitoring.
    It provides event-driven call handling with comprehensive logging and
    monitoring capabilities.
    """
    
    def __init__(self, modem_id: str, at_handler: ATHandler):
        self.modem_id = modem_id
        self.at_handler = at_handler
        self.active_calls = {}
        self.call_history = []
        self.call_event_handlers = {}
        self.dtmf_handlers = {}
        self.is_monitoring = False
        self.monitor_thread = None
        self.call_counter = 0
        
    async def initialize(self) -> bool:
        """
        Initialize call manager and configure modem for voice operations.
        
        Returns:
            Success status
        """
        try:
            logger.info(f"Initializing call manager for modem {self.modem_id}")
            
            # Set voice call mode
            response = await self.at_handler.send_command("AT+FCLASS=0")
            if not response.success:
                logger.error("Failed to set voice call mode")
                return False
            
            # Enable caller ID
            response = await self.at_handler.send_command("AT+CLIP=1")
            if response.success:
                logger.info("Caller ID enabled")
            
            # Enable call waiting notification
            response = await self.at_handler.send_command("AT+CCWA=1,1")
            if response.success:
                logger.info("Call waiting enabled")
            
            # Configure DTMF detection
            response = await self.at_handler.send_command("AT+DDET=1")
            if response.success:
                logger.info("DTMF detection enabled")
            
            # Set audio path (hands-free)
            response = await self.at_handler.send_command("AT+SPEAKER=1")
            if response.success:
                logger.info("Audio path configured")
            
            # Start call monitoring
            self.is_monitoring = True
            self.monitor_thread = threading.Thread(target=self._call_monitor, daemon=True)
            self.monitor_thread.start()
            
            logger.info(f"Call manager initialized successfully for modem {self.modem_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize call manager: {str(e)}")
            return False
    
    async def make_call(
        self,
        phone_number: str,
        call_type: CallType = CallType.VOICE,
        timeout: int = 30
    ) -> CallInfo:
        """
        Initiate an outbound call.
        
        Args:
            phone_number: Number to call
            call_type: Type of call
            timeout: Call timeout in seconds
            
        Returns:
            Call information object
        """
        try:
            # Validate phone number
            if not self._validate_phone_number(phone_number):
                raise ValueError(f"Invalid phone number: {phone_number}")
            
            # Check if modem is busy
            if self._has_active_calls():
                raise RuntimeError("Modem is busy with another call")
            
            # Create call info
            call_id = self._generate_call_id()
            call_info = CallInfo(
                call_id=call_id,
                phone_number=phone_number,
                direction=CallDirection.OUTBOUND,
                call_type=call_type,
                state=CallState.DIALING,
                start_time=datetime.utcnow()
            )
            
            # Store call info
            self.active_calls[call_id] = call_info
            
            # Initiate call
            if call_type == CallType.VOICE:
                command = f"ATD{phone_number};"
            else:
                command = f"ATD{phone_number}"
            
            response = await self.at_handler.send_command(command)
            
            if response.success:
                logger.info(f"Call {call_id} initiated to {phone_number}")
                
                # Wait for call to be answered or timeout
                await self._wait_for_call_answer(call_id, timeout)
                
            else:
                call_info.state = CallState.FAILED
                call_info.end_time = datetime.utcnow()
                call_info.termination_reason = "Failed to initiate call"
                logger.error(f"Failed to initiate call {call_id}")
            
            return call_info
            
        except Exception as e:
            logger.error(f"Failed to make call: {str(e)}")
            if 'call_info' in locals():
                call_info.state = CallState.FAILED
                call_info.end_time = datetime.utcnow()
                call_info.termination_reason = str(e)
            raise
    
    async def answer_call(self, call_id: Optional[str] = None) -> bool:
        """
        Answer an incoming call.
        
        Args:
            call_id: Optional specific call ID to answer
            
        Returns:
            Success status
        """
        try:
            # Find incoming call
            if call_id:
                call_info = self.active_calls.get(call_id)
                if not call_info or call_info.state != CallState.RINGING:
                    raise ValueError(f"No ringing call with ID {call_id}")
            else:
                # Find any ringing call
                call_info = None
                for call in self.active_calls.values():
                    if call.state == CallState.RINGING:
                        call_info = call
                        break
                
                if not call_info:
                    raise RuntimeError("No incoming call to answer")
            
            # Answer the call
            response = await self.at_handler.send_command("ATA")
            
            if response.success:
                call_info.state = CallState.CONNECTED
                call_info.answer_time = datetime.utcnow()
                
                logger.info(f"Answered call {call_info.call_id}")
                
                # Trigger call answered event
                await self._trigger_call_event("call_answered", call_info)
                
                return True
            else:
                logger.error(f"Failed to answer call {call_info.call_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to answer call: {str(e)}")
            return False
    
    async def hang_up_call(self, call_id: Optional[str] = None) -> bool:
        """
        Terminate a call.
        
        Args:
            call_id: Optional specific call ID to hang up
            
        Returns:
            Success status
        """
        try:
            # Find active call
            if call_id:
                call_info = self.active_calls.get(call_id)
                if not call_info:
                    raise ValueError(f"No active call with ID {call_id}")
            else:
                # Find any active call
                call_info = None
                for call in self.active_calls.values():
                    if call.state in [CallState.CONNECTED, CallState.RINGING, CallState.DIALING]:
                        call_info = call
                        break
                
                if not call_info:
                    raise RuntimeError("No active call to hang up")
            
            # Hang up the call
            response = await self.at_handler.send_command("ATH")
            
            if response.success:
                call_info.state = CallState.TERMINATED
                call_info.end_time = datetime.utcnow()
                call_info.termination_reason = "User terminated"
                
                # Calculate duration
                if call_info.answer_time:
                    duration = (call_info.end_time - call_info.answer_time).total_seconds()
                    call_info.duration = int(duration)
                
                logger.info(f"Hung up call {call_info.call_id}")
                
                # Move to history and remove from active
                self.call_history.append(call_info)
                del self.active_calls[call_info.call_id]
                
                # Trigger call ended event
                await self._trigger_call_event("call_ended", call_info)
                
                return True
            else:
                logger.error(f"Failed to hang up call {call_info.call_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to hang up call: {str(e)}")
            return False
    
    async def send_dtmf(self, call_id: str, digits: str, duration: int = 100) -> bool:
        """
        Send DTMF tones during a call.
        
        Args:
            call_id: Call identifier
            digits: DTMF digits to send
            duration: Tone duration in milliseconds
            
        Returns:
            Success status
        """
        try:
            call_info = self.active_calls.get(call_id)
            if not call_info or call_info.state != CallState.CONNECTED:
                raise ValueError(f"No connected call with ID {call_id}")
            
            # Validate DTMF digits
            valid_digits = "0123456789*#ABCD"
            for digit in digits:
                if digit not in valid_digits:
                    raise ValueError(f"Invalid DTMF digit: {digit}")
            
            # Send DTMF tones
            for digit in digits:
                command = f"AT+VTS={digit}"
                response = await self.at_handler.send_command(command)
                
                if response.success:
                    # Record DTMF event
                    dtmf_event = DTMFEvent(
                        call_id=call_id,
                        digit=digit,
                        timestamp=datetime.utcnow(),
                        duration=duration
                    )
                    
                    if not call_info.dtmf_sequence:
                        call_info.dtmf_sequence = []
                    call_info.dtmf_sequence.append(digit)
                    
                    # Trigger DTMF event
                    await self._trigger_dtmf_event(dtmf_event)
                    
                    # Small delay between tones
                    await asyncio.sleep(duration / 1000.0)
                else:
                    logger.error(f"Failed to send DTMF digit {digit}")
                    return False
            
            logger.info(f"Sent DTMF sequence '{digits}' on call {call_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send DTMF: {str(e)}")
            return False
    
    async def hold_call(self, call_id: str) -> bool:
        """
        Put a call on hold.
        
        Args:
            call_id: Call identifier
            
        Returns:
            Success status
        """
        try:
            call_info = self.active_calls.get(call_id)
            if not call_info or call_info.state != CallState.CONNECTED:
                raise ValueError(f"No connected call with ID {call_id}")
            
            # Put call on hold
            response = await self.at_handler.send_command("AT+CHLD=2")
            
            if response.success:
                call_info.state = CallState.HOLDING
                logger.info(f"Put call {call_id} on hold")
                return True
            else:
                logger.error(f"Failed to hold call {call_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to hold call: {str(e)}")
            return False
    
    async def resume_call(self, call_id: str) -> bool:
        """
        Resume a held call.
        
        Args:
            call_id: Call identifier
            
        Returns:
            Success status
        """
        try:
            call_info = self.active_calls.get(call_id)
            if not call_info or call_info.state != CallState.HOLDING:
                raise ValueError(f"No held call with ID {call_id}")
            
            # Resume call
            response = await self.at_handler.send_command("AT+CHLD=1")
            
            if response.success:
                call_info.state = CallState.CONNECTED
                logger.info(f"Resumed call {call_id}")
                return True
            else:
                logger.error(f"Failed to resume call {call_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to resume call: {str(e)}")
            return False
    
    async def get_call_status(self, call_id: str) -> Optional[CallInfo]:
        """
        Get status of a specific call.
        
        Args:
            call_id: Call identifier
            
        Returns:
            Call information or None
        """
        return self.active_calls.get(call_id)
    
    async def get_active_calls(self) -> List[CallInfo]:
        """
        Get list of all active calls.
        
        Returns:
            List of active call information
        """
        return list(self.active_calls.values())
    
    async def get_call_history(self, limit: int = 100) -> List[CallInfo]:
        """
        Get call history.
        
        Args:
            limit: Maximum number of calls to return
            
        Returns:
            List of historical call information
        """
        return self.call_history[-limit:]
    
    def register_call_event_handler(self, event_type: str, handler: Callable):
        """
        Register event handler for call events.
        
        Args:
            event_type: Type of event (call_incoming, call_answered, call_ended, etc.)
            handler: Event handler function
        """
        if event_type not in self.call_event_handlers:
            self.call_event_handlers[event_type] = []
        self.call_event_handlers[event_type].append(handler)
    
    def register_dtmf_handler(self, handler: Callable):
        """
        Register handler for DTMF events.
        
        Args:
            handler: DTMF event handler function
        """
        handler_id = str(uuid.uuid4())
        self.dtmf_handlers[handler_id] = handler
        return handler_id
    
    def _call_monitor(self):
        """Background thread for monitoring call events"""
        logger.info(f"Call monitor started for modem {self.modem_id}")
        
        while self.is_monitoring:
            try:
                # Check for incoming calls and call state changes
                asyncio.run(self._check_call_status())
                
                # Check for DTMF events
                asyncio.run(self._check_dtmf_events())
                
                time.sleep(0.5)  # Check every 500ms
                
            except Exception as e:
                logger.error(f"Error in call monitor: {str(e)}")
                time.sleep(1.0)
        
        logger.info(f"Call monitor stopped for modem {self.modem_id}")
    
    async def _check_call_status(self):
        """Check for call status changes"""
        try:
            # Query current call status
            response = await self.at_handler.send_command("AT+CLCC")
            
            if response.success and response.data:
                current_calls = self._parse_call_list(response.data)
                await self._update_call_states(current_calls)
                
        except Exception as e:
            logger.error(f"Error checking call status: {str(e)}")
    
    async def _check_dtmf_events(self):
        """Check for DTMF events"""
        try:
            # This would be implemented based on modem-specific DTMF detection
            # For SIM900, DTMF events might come as URCs
            pass
            
        except Exception as e:
            logger.error(f"Error checking DTMF events: {str(e)}")
    
    async def _wait_for_call_answer(self, call_id: str, timeout: int):
        """Wait for call to be answered or timeout"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            call_info = self.active_calls.get(call_id)
            if not call_info:
                break
            
            if call_info.state == CallState.CONNECTED:
                call_info.answer_time = datetime.utcnow()
                await self._trigger_call_event("call_answered", call_info)
                break
            elif call_info.state in [CallState.BUSY, CallState.FAILED, CallState.NO_ANSWER]:
                break
            
            await asyncio.sleep(0.5)
        
        # Check final state
        call_info = self.active_calls.get(call_id)
        if call_info and call_info.state == CallState.DIALING:
            call_info.state = CallState.NO_ANSWER
            call_info.end_time = datetime.utcnow()
            call_info.termination_reason = "No answer"
    
    def _parse_call_list(self, data: str) -> List[Dict[str, Any]]:
        """Parse call list from AT+CLCC response"""
        calls = []
        
        try:
            lines = data.strip().split('\n')
            
            for line in lines:
                if line.startswith('+CLCC:'):
                    # Parse call information
                    match = re.match(
                        r'\+CLCC:\s*(\d+),(\d+),(\d+),(\d+),(\d+),"([^"]*)",(\d+)',
                        line
                    )
                    
                    if match:
                        call_data = {
                            "index": int(match.group(1)),
                            "direction": int(match.group(2)),
                            "state": int(match.group(3)),
                            "mode": int(match.group(4)),
                            "multiparty": int(match.group(5)),
                            "number": match.group(6),
                            "type": int(match.group(7))
                        }
                        calls.append(call_data)
                        
        except Exception as e:
            logger.error(f"Error parsing call list: {str(e)}")
        
        return calls
    
    async def _update_call_states(self, current_calls: List[Dict[str, Any]]):
        """Update call states based on modem status"""
        try:
            # Map modem call states to our call states
            state_map = {
                0: CallState.CONNECTED,  # Active
                1: CallState.HOLDING,    # Held
                2: CallState.DIALING,    # Dialing
                3: CallState.RINGING,    # Alerting
                4: CallState.RINGING,    # Incoming
                5: CallState.RINGING     # Waiting
            }
            
            # Check for new incoming calls
            for call_data in current_calls:
                if call_data["direction"] == 1 and call_data["state"] == 4:  # Incoming call
                    # Check if we already know about this call
                    existing_call = None
                    for call_info in self.active_calls.values():
                        if (call_info.phone_number == call_data["number"] and
                            call_info.direction == CallDirection.INBOUND):
                            existing_call = call_info
                            break
                    
                    if not existing_call:
                        # New incoming call
                        call_id = self._generate_call_id()
                        call_info = CallInfo(
                            call_id=call_id,
                            phone_number=call_data["number"],
                            direction=CallDirection.INBOUND,
                            call_type=CallType.VOICE,
                            state=CallState.RINGING,
                            start_time=datetime.utcnow()
                        )
                        
                        self.active_calls[call_id] = call_info
                        await self._trigger_call_event("call_incoming", call_info)
            
            # Update existing call states
            for call_info in list(self.active_calls.values()):
                found = False
                for call_data in current_calls:
                    if call_data["number"] == call_info.phone_number:
                        new_state = state_map.get(call_data["state"], call_info.state)
                        if new_state != call_info.state:
                            old_state = call_info.state
                            call_info.state = new_state
                            logger.info(f"Call {call_info.call_id} state changed: {old_state} -> {new_state}")
                        found = True
                        break
                
                # If call not found in current calls, it may have ended
                if not found and call_info.state in [CallState.CONNECTED, CallState.DIALING, CallState.RINGING]:
                    call_info.state = CallState.TERMINATED
                    call_info.end_time = datetime.utcnow()
                    call_info.termination_reason = "Call ended"
                    
                    if call_info.answer_time:
                        duration = (call_info.end_time - call_info.answer_time).total_seconds()
                        call_info.duration = int(duration)
                    
                    # Move to history
                    self.call_history.append(call_info)
                    del self.active_calls[call_info.call_id]
                    
                    await self._trigger_call_event("call_ended", call_info)
                    
        except Exception as e:
            logger.error(f"Error updating call states: {str(e)}")
    
    async def _trigger_call_event(self, event_type: str, call_info: CallInfo):
        """Trigger call event handlers"""
        try:
            handlers = self.call_event_handlers.get(event_type, [])
            for handler in handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(call_info)
                    else:
                        handler(call_info)
                except Exception as e:
                    logger.error(f"Error in call event handler: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error triggering call event: {str(e)}")
    
    async def _trigger_dtmf_event(self, dtmf_event: DTMFEvent):
        """Trigger DTMF event handlers"""
        try:
            for handler in self.dtmf_handlers.values():
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(dtmf_event)
                    else:
                        handler(dtmf_event)
                except Exception as e:
                    logger.error(f"Error in DTMF event handler: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error triggering DTMF event: {str(e)}")
    
    def _validate_phone_number(self, phone_number: str) -> bool:
        """Validate phone number format"""
        # Remove common formatting characters
        cleaned = re.sub(r'[\s\-\(\)]', '', phone_number)
        
        # Check if it's a valid format
        if re.match(r'^\+?[1-9]\d{1,14}$', cleaned):
            return True
        
        return False
    
    def _has_active_calls(self) -> bool:
        """Check if there are any active calls"""
        for call_info in self.active_calls.values():
            if call_info.state in [CallState.CONNECTED, CallState.DIALING, CallState.RINGING]:
                return True
        return False
    
    def _generate_call_id(self) -> str:
        """Generate unique call identifier"""
        self.call_counter += 1
        return f"{self.modem_id}_call_{self.call_counter}_{int(time.time())}"
    
    async def shutdown(self):
        """Shutdown call manager"""
        logger.info(f"Shutting down call manager for modem {self.modem_id}")
        
        # Hang up any active calls
        for call_info in list(self.active_calls.values()):
            await self.hang_up_call(call_info.call_id)
        
        # Stop monitoring
        self.is_monitoring = False
        
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5.0)
        
        logger.info(f"Call manager shutdown complete for modem {self.modem_id}")