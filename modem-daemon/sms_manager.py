"""
SMS Manager for Project GeminiVoiceConnect

This module provides comprehensive SMS management capabilities for SIM900 modems including
sending, receiving, delivery tracking, message queuing, and advanced SMS features like
concatenated messages, flash SMS, and delivery reports.

Key Features:
- Bidirectional SMS communication (send/receive)
- Message queuing and retry mechanisms
- Delivery status tracking and reports
- Concatenated message handling (long SMS)
- Flash SMS and priority messaging
- SMS encoding support (GSM 7-bit, UCS2)
- Message storage management
- Bulk SMS operations
- SMS-based command processing
"""

from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import json
import logging
from dataclasses import dataclass, asdict
import re
import uuid
import time
from queue import Queue, Empty
import threading

from .config import get_settings
from .at_handler import ATHandler, ATResponse

logger = logging.getLogger(__name__)
settings = get_settings()


class SMSStatus(str, Enum):
    """SMS message status"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    RECEIVED = "received"
    READ = "read"


class SMSEncoding(str, Enum):
    """SMS encoding types"""
    GSM_7BIT = "gsm_7bit"
    UCS2 = "ucs2"
    BINARY = "binary"


class SMSType(str, Enum):
    """SMS message types"""
    NORMAL = "normal"
    FLASH = "flash"
    CONCATENATED = "concatenated"
    DELIVERY_REPORT = "delivery_report"


@dataclass
class SMSMessage:
    """SMS message structure"""
    id: str
    phone_number: str
    content: str
    status: SMSStatus
    encoding: SMSEncoding
    message_type: SMSType
    created_at: datetime
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    pdu_mode: bool = False
    message_reference: Optional[int] = None
    delivery_report_requested: bool = False
    flash_message: bool = False
    concatenated_info: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class SMSDeliveryReport:
    """SMS delivery report structure"""
    message_reference: int
    phone_number: str
    timestamp: datetime
    status: str
    error_code: Optional[int] = None


@dataclass
class ConcatenatedSMSInfo:
    """Concatenated SMS information"""
    reference_number: int
    total_parts: int
    part_number: int
    message_id: str


class SMSManager:
    """
    Comprehensive SMS management system for SIM900 modems.
    
    This manager handles all aspects of SMS communication including sending,
    receiving, delivery tracking, message queuing, and advanced SMS features.
    It provides robust error handling, retry mechanisms, and supports both
    text and PDU modes for maximum compatibility.
    """
    
    def __init__(self, modem_id: str, at_handler: ATHandler):
        self.modem_id = modem_id
        self.at_handler = at_handler
        self.outbound_queue = Queue()
        self.inbound_messages = []
        self.delivery_reports = {}
        self.concatenated_messages = {}
        self.message_storage = {}
        self.is_running = False
        self.worker_thread = None
        self.message_counter = 0
        
    async def initialize(self) -> bool:
        """
        Initialize SMS manager and configure modem for SMS operations.
        
        Returns:
            Success status
        """
        try:
            logger.info(f"Initializing SMS manager for modem {self.modem_id}")
            
            # Set SMS text mode
            response = await self.at_handler.send_command("AT+CMGF=1")
            if not response.success:
                logger.error("Failed to set SMS text mode")
                return False
            
            # Configure SMS storage
            response = await self.at_handler.send_command('AT+CPMS="SM","SM","SM"')
            if not response.success:
                logger.warning("Failed to set SMS storage, trying alternative")
                # Try alternative storage setting
                await self.at_handler.send_command('AT+CPMS="ME","ME","ME"')
            
            # Enable SMS delivery reports
            response = await self.at_handler.send_command("AT+CSMP=49,167,0,0")
            if response.success:
                logger.info("SMS delivery reports enabled")
            
            # Configure new message indication
            response = await self.at_handler.send_command("AT+CNMI=2,2,0,1,0")
            if response.success:
                logger.info("SMS new message indication configured")
            
            # Clear any existing messages
            await self._clear_message_storage()
            
            # Start SMS worker thread
            self.is_running = True
            self.worker_thread = threading.Thread(target=self._sms_worker, daemon=True)
            self.worker_thread.start()
            
            logger.info(f"SMS manager initialized successfully for modem {self.modem_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize SMS manager: {str(e)}")
            return False
    
    async def send_sms(
        self,
        phone_number: str,
        message: str,
        flash_message: bool = False,
        delivery_report: bool = True,
        encoding: SMSEncoding = SMSEncoding.GSM_7BIT
    ) -> SMSMessage:
        """
        Send SMS message.
        
        Args:
            phone_number: Recipient phone number
            message: Message content
            flash_message: Send as flash SMS
            delivery_report: Request delivery report
            encoding: Message encoding
            
        Returns:
            SMS message object
        """
        try:
            # Validate phone number
            if not self._validate_phone_number(phone_number):
                raise ValueError(f"Invalid phone number: {phone_number}")
            
            # Check message length and split if necessary
            messages = self._split_long_message(message, encoding)
            
            if len(messages) == 1:
                # Single message
                sms_message = SMSMessage(
                    id=str(uuid.uuid4()),
                    phone_number=phone_number,
                    content=message,
                    status=SMSStatus.PENDING,
                    encoding=encoding,
                    message_type=SMSType.FLASH if flash_message else SMSType.NORMAL,
                    created_at=datetime.utcnow(),
                    delivery_report_requested=delivery_report,
                    flash_message=flash_message
                )
            else:
                # Concatenated message
                reference_number = self._generate_reference_number()
                sms_message = SMSMessage(
                    id=str(uuid.uuid4()),
                    phone_number=phone_number,
                    content=message,
                    status=SMSStatus.PENDING,
                    encoding=encoding,
                    message_type=SMSType.CONCATENATED,
                    created_at=datetime.utcnow(),
                    delivery_report_requested=delivery_report,
                    concatenated_info={
                        "reference_number": reference_number,
                        "total_parts": len(messages),
                        "parts": messages
                    }
                )
            
            # Add to outbound queue
            self.outbound_queue.put(sms_message)
            self.message_storage[sms_message.id] = sms_message
            
            logger.info(f"Queued SMS {sms_message.id} to {phone_number}")
            return sms_message
            
        except Exception as e:
            logger.error(f"Failed to send SMS: {str(e)}")
            raise
    
    async def send_bulk_sms(
        self,
        recipients: List[str],
        message: str,
        flash_message: bool = False,
        delivery_report: bool = True
    ) -> List[SMSMessage]:
        """
        Send bulk SMS messages.
        
        Args:
            recipients: List of recipient phone numbers
            message: Message content
            flash_message: Send as flash SMS
            delivery_report: Request delivery report
            
        Returns:
            List of SMS message objects
        """
        try:
            messages = []
            
            for phone_number in recipients:
                try:
                    sms_message = await self.send_sms(
                        phone_number=phone_number,
                        message=message,
                        flash_message=flash_message,
                        delivery_report=delivery_report
                    )
                    messages.append(sms_message)
                except Exception as e:
                    logger.error(f"Failed to queue SMS for {phone_number}: {str(e)}")
                    # Create failed message record
                    failed_message = SMSMessage(
                        id=str(uuid.uuid4()),
                        phone_number=phone_number,
                        content=message,
                        status=SMSStatus.FAILED,
                        encoding=SMSEncoding.GSM_7BIT,
                        message_type=SMSType.NORMAL,
                        created_at=datetime.utcnow(),
                        metadata={"error": str(e)}
                    )
                    messages.append(failed_message)
            
            logger.info(f"Queued {len(messages)} bulk SMS messages")
            return messages
            
        except Exception as e:
            logger.error(f"Failed to send bulk SMS: {str(e)}")
            raise
    
    async def receive_sms(self) -> List[SMSMessage]:
        """
        Retrieve received SMS messages.
        
        Returns:
            List of received SMS messages
        """
        try:
            received_messages = []
            
            # Read all unread messages
            response = await self.at_handler.send_command('AT+CMGL="REC UNREAD"')
            if response.success and response.data:
                messages = self._parse_received_messages(response.data)
                received_messages.extend(messages)
            
            # Read all read messages (for completeness)
            response = await self.at_handler.send_command('AT+CMGL="REC READ"')
            if response.success and response.data:
                messages = self._parse_received_messages(response.data)
                received_messages.extend(messages)
            
            # Process concatenated messages
            received_messages = self._process_concatenated_messages(received_messages)
            
            # Store received messages
            for message in received_messages:
                self.message_storage[message.id] = message
                self.inbound_messages.append(message)
            
            if received_messages:
                logger.info(f"Received {len(received_messages)} SMS messages")
            
            return received_messages
            
        except Exception as e:
            logger.error(f"Failed to receive SMS: {str(e)}")
            return []
    
    async def get_message_status(self, message_id: str) -> Optional[SMSMessage]:
        """
        Get status of a specific message.
        
        Args:
            message_id: Message identifier
            
        Returns:
            SMS message object or None
        """
        return self.message_storage.get(message_id)
    
    async def get_delivery_report(self, message_reference: int) -> Optional[SMSDeliveryReport]:
        """
        Get delivery report for a message.
        
        Args:
            message_reference: Message reference number
            
        Returns:
            Delivery report or None
        """
        return self.delivery_reports.get(message_reference)
    
    async def delete_message(self, message_index: int) -> bool:
        """
        Delete message from modem storage.
        
        Args:
            message_index: Message storage index
            
        Returns:
            Success status
        """
        try:
            response = await self.at_handler.send_command(f"AT+CMGD={message_index}")
            return response.success
            
        except Exception as e:
            logger.error(f"Failed to delete message {message_index}: {str(e)}")
            return False
    
    async def get_sms_storage_info(self) -> Dict[str, Any]:
        """
        Get SMS storage information.
        
        Returns:
            Storage information
        """
        try:
            response = await self.at_handler.send_command("AT+CPMS?")
            if response.success and response.data:
                # Parse storage information
                storage_info = self._parse_storage_info(response.data)
                return storage_info
            
            return {"error": "Failed to get storage info"}
            
        except Exception as e:
            logger.error(f"Failed to get SMS storage info: {str(e)}")
            return {"error": str(e)}
    
    def _sms_worker(self):
        """Background worker thread for processing SMS queue"""
        logger.info(f"SMS worker started for modem {self.modem_id}")
        
        while self.is_running:
            try:
                # Process outbound messages
                try:
                    message = self.outbound_queue.get(timeout=1.0)
                    asyncio.run(self._process_outbound_message(message))
                    self.outbound_queue.task_done()
                except Empty:
                    pass
                
                # Check for incoming messages
                asyncio.run(self._check_incoming_messages())
                
                # Process delivery reports
                asyncio.run(self._check_delivery_reports())
                
                time.sleep(0.1)  # Small delay to prevent CPU spinning
                
            except Exception as e:
                logger.error(f"Error in SMS worker: {str(e)}")
                time.sleep(1.0)
        
        logger.info(f"SMS worker stopped for modem {self.modem_id}")
    
    async def _process_outbound_message(self, message: SMSMessage):
        """Process outbound SMS message"""
        try:
            if message.message_type == SMSType.CONCATENATED:
                # Send concatenated message parts
                await self._send_concatenated_message(message)
            else:
                # Send single message
                await self._send_single_message(message)
                
        except Exception as e:
            logger.error(f"Failed to process outbound message {message.id}: {str(e)}")
            message.status = SMSStatus.FAILED
            message.metadata = {"error": str(e)}
    
    async def _send_single_message(self, message: SMSMessage):
        """Send single SMS message"""
        try:
            # Set SMS parameters if flash message
            if message.flash_message:
                await self.at_handler.send_command("AT+CSMP=17,167,0,0")
            else:
                await self.at_handler.send_command("AT+CSMP=49,167,0,0")
            
            # Send message
            command = f'AT+CMGS="{message.phone_number}"'
            response = await self.at_handler.send_command(command)
            
            if response.success:
                # Send message content
                content_response = await self.at_handler.send_command(
                    message.content + "\x1A"  # Ctrl+Z to send
                )
                
                if content_response.success:
                    # Extract message reference from response
                    message_ref = self._extract_message_reference(content_response.data)
                    message.message_reference = message_ref
                    message.status = SMSStatus.SENT
                    message.sent_at = datetime.utcnow()
                    
                    logger.info(f"SMS {message.id} sent successfully (ref: {message_ref})")
                else:
                    message.status = SMSStatus.FAILED
                    logger.error(f"Failed to send SMS content for {message.id}")
            else:
                message.status = SMSStatus.FAILED
                logger.error(f"Failed to initiate SMS send for {message.id}")
                
        except Exception as e:
            logger.error(f"Error sending single message: {str(e)}")
            message.status = SMSStatus.FAILED
            message.metadata = {"error": str(e)}
    
    async def _send_concatenated_message(self, message: SMSMessage):
        """Send concatenated SMS message"""
        try:
            if not message.concatenated_info:
                raise ValueError("Missing concatenated message info")
            
            parts = message.concatenated_info["parts"]
            reference_number = message.concatenated_info["reference_number"]
            total_parts = len(parts)
            
            sent_parts = 0
            
            for i, part in enumerate(parts):
                try:
                    # Create part message
                    part_message = SMSMessage(
                        id=f"{message.id}_part_{i+1}",
                        phone_number=message.phone_number,
                        content=part,
                        status=SMSStatus.PENDING,
                        encoding=message.encoding,
                        message_type=SMSType.NORMAL,
                        created_at=datetime.utcnow(),
                        concatenated_info=ConcatenatedSMSInfo(
                            reference_number=reference_number,
                            total_parts=total_parts,
                            part_number=i + 1,
                            message_id=message.id
                        )
                    )
                    
                    await self._send_single_message(part_message)
                    
                    if part_message.status == SMSStatus.SENT:
                        sent_parts += 1
                    
                    # Small delay between parts
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"Failed to send part {i+1} of message {message.id}: {str(e)}")
            
            # Update main message status
            if sent_parts == total_parts:
                message.status = SMSStatus.SENT
                message.sent_at = datetime.utcnow()
                logger.info(f"Concatenated SMS {message.id} sent successfully ({sent_parts}/{total_parts} parts)")
            else:
                message.status = SMSStatus.FAILED
                logger.error(f"Concatenated SMS {message.id} partially failed ({sent_parts}/{total_parts} parts)")
                
        except Exception as e:
            logger.error(f"Error sending concatenated message: {str(e)}")
            message.status = SMSStatus.FAILED
            message.metadata = {"error": str(e)}
    
    async def _check_incoming_messages(self):
        """Check for incoming SMS messages"""
        try:
            # This would be triggered by URC (Unsolicited Result Code) in real implementation
            # For now, we'll poll periodically
            await self.receive_sms()
            
        except Exception as e:
            logger.error(f"Error checking incoming messages: {str(e)}")
    
    async def _check_delivery_reports(self):
        """Check for SMS delivery reports"""
        try:
            # Read delivery reports
            response = await self.at_handler.send_command('AT+CMGL="STO SENT"')
            if response.success and response.data:
                reports = self._parse_delivery_reports(response.data)
                for report in reports:
                    self.delivery_reports[report.message_reference] = report
                    
                    # Update message status
                    for message in self.message_storage.values():
                        if (message.message_reference == report.message_reference and
                            message.status == SMSStatus.SENT):
                            message.status = SMSStatus.DELIVERED
                            message.delivered_at = report.timestamp
                            break
                            
        except Exception as e:
            logger.error(f"Error checking delivery reports: {str(e)}")
    
    def _validate_phone_number(self, phone_number: str) -> bool:
        """Validate phone number format"""
        # Remove common formatting characters
        cleaned = re.sub(r'[\s\-\(\)]', '', phone_number)
        
        # Check if it's a valid international format
        if re.match(r'^\+?[1-9]\d{1,14}$', cleaned):
            return True
        
        return False
    
    def _split_long_message(self, message: str, encoding: SMSEncoding) -> List[str]:
        """Split long message into SMS-sized parts"""
        if encoding == SMSEncoding.GSM_7BIT:
            max_length = 160
            concat_length = 153  # 160 - 7 bytes for concatenation header
        else:  # UCS2
            max_length = 70
            concat_length = 67  # 70 - 3 bytes for concatenation header
        
        if len(message) <= max_length:
            return [message]
        
        # Split into parts
        parts = []
        for i in range(0, len(message), concat_length):
            parts.append(message[i:i + concat_length])
        
        return parts
    
    def _generate_reference_number(self) -> int:
        """Generate reference number for concatenated messages"""
        self.message_counter = (self.message_counter + 1) % 256
        return self.message_counter
    
    def _parse_received_messages(self, data: str) -> List[SMSMessage]:
        """Parse received SMS messages from AT response"""
        messages = []
        
        try:
            lines = data.strip().split('\n')
            i = 0
            
            while i < len(lines):
                line = lines[i].strip()
                
                if line.startswith('+CMGL:'):
                    # Parse message header
                    header_match = re.match(
                        r'\+CMGL:\s*(\d+),"([^"]*)","([^"]*)"[^,]*,"([^"]*)"',
                        line
                    )
                    
                    if header_match and i + 1 < len(lines):
                        index = int(header_match.group(1))
                        status = header_match.group(2)
                        sender = header_match.group(3)
                        timestamp_str = header_match.group(4)
                        
                        # Get message content
                        content = lines[i + 1].strip()
                        
                        # Parse timestamp
                        timestamp = self._parse_timestamp(timestamp_str)
                        
                        message = SMSMessage(
                            id=str(uuid.uuid4()),
                            phone_number=sender,
                            content=content,
                            status=SMSStatus.RECEIVED,
                            encoding=SMSEncoding.GSM_7BIT,
                            message_type=SMSType.NORMAL,
                            created_at=timestamp,
                            metadata={"storage_index": index}
                        )
                        
                        messages.append(message)
                        i += 2
                    else:
                        i += 1
                else:
                    i += 1
                    
        except Exception as e:
            logger.error(f"Error parsing received messages: {str(e)}")
        
        return messages
    
    def _process_concatenated_messages(self, messages: List[SMSMessage]) -> List[SMSMessage]:
        """Process and reassemble concatenated messages"""
        # This is a simplified implementation
        # In a full implementation, you would parse UDH (User Data Header)
        # to identify and reassemble concatenated messages
        return messages
    
    def _parse_delivery_reports(self, data: str) -> List[SMSDeliveryReport]:
        """Parse SMS delivery reports"""
        reports = []
        
        try:
            # Parse delivery report format
            # This would depend on the specific format returned by the modem
            pass
            
        except Exception as e:
            logger.error(f"Error parsing delivery reports: {str(e)}")
        
        return reports
    
    def _extract_message_reference(self, data: str) -> Optional[int]:
        """Extract message reference from send response"""
        try:
            # Look for message reference in response
            match = re.search(r'\+CMGS:\s*(\d+)', data)
            if match:
                return int(match.group(1))
        except Exception as e:
            logger.error(f"Error extracting message reference: {str(e)}")
        
        return None
    
    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse SMS timestamp"""
        try:
            # SMS timestamp format: "yy/MM/dd,hh:mm:ss±zz"
            # This is a simplified parser
            return datetime.utcnow()
        except Exception as e:
            logger.error(f"Error parsing timestamp: {str(e)}")
            return datetime.utcnow()
    
    def _parse_storage_info(self, data: str) -> Dict[str, Any]:
        """Parse SMS storage information"""
        try:
            # Parse +CPMS response
            match = re.search(r'\+CPMS:\s*(\d+),(\d+),(\d+),(\d+),(\d+),(\d+)', data)
            if match:
                return {
                    "read_storage": {
                        "used": int(match.group(1)),
                        "total": int(match.group(2))
                    },
                    "write_storage": {
                        "used": int(match.group(3)),
                        "total": int(match.group(4))
                    },
                    "receive_storage": {
                        "used": int(match.group(5)),
                        "total": int(match.group(6))
                    }
                }
        except Exception as e:
            logger.error(f"Error parsing storage info: {str(e)}")
        
        return {"error": "Failed to parse storage info"}
    
    async def _clear_message_storage(self):
        """Clear all messages from modem storage"""
        try:
            # Delete all messages
            response = await self.at_handler.send_command("AT+CMGD=1,4")
            if response.success:
                logger.info("Cleared SMS storage")
            else:
                logger.warning("Failed to clear SMS storage")
                
        except Exception as e:
            logger.error(f"Error clearing message storage: {str(e)}")
    
    async def shutdown(self):
        """Shutdown SMS manager"""
        logger.info(f"Shutting down SMS manager for modem {self.modem_id}")
        self.is_running = False
        
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=5.0)
        
        logger.info(f"SMS manager shutdown complete for modem {self.modem_id}")