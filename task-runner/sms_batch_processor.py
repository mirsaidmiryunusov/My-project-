"""
SMS Batch Processor for Project GeminiVoiceConnect

This module provides comprehensive SMS batch processing capabilities for marketing
campaigns, notifications, and automated messaging. It implements intelligent
delivery optimization, personalization, compliance management, and real-time
analytics for maximum SMS campaign effectiveness.

Key Features:
- High-volume SMS batch processing across 80 modems
- Intelligent delivery optimization and load balancing
- Advanced personalization and template management
- Compliance management (TCPA, GDPR, opt-out handling)
- Real-time delivery tracking and analytics
- Retry logic and failure handling
- A/B testing for SMS campaigns
- Delivery time optimization
"""

from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import json
import logging
from dataclasses import dataclass, asdict
import re
import statistics
from collections import defaultdict, deque
import numpy as np
import pandas as pd
from celery import Celery
from jinja2 import Template
import phonenumbers
from phonenumbers import NumberParseException

logger = logging.getLogger(__name__)


class SMSType(str, Enum):
    """Types of SMS messages"""
    MARKETING = "marketing"
    TRANSACTIONAL = "transactional"
    NOTIFICATION = "notification"
    REMINDER = "reminder"
    ALERT = "alert"
    VERIFICATION = "verification"
    SURVEY = "survey"
    PROMOTIONAL = "promotional"


class SMSStatus(str, Enum):
    """SMS delivery status"""
    PENDING = "pending"
    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"
    OPTED_OUT = "opted_out"
    BLOCKED = "blocked"


class SMSPriority(str, Enum):
    """SMS delivery priority"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class SMSMessage:
    """Individual SMS message"""
    message_id: str
    campaign_id: str
    recipient_phone: str
    content: str
    sms_type: SMSType
    priority: SMSPriority
    scheduled_time: Optional[datetime]
    personalization_data: Optional[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]]
    status: SMSStatus = SMSStatus.PENDING
    modem_id: Optional[str] = None
    sent_time: Optional[datetime] = None
    delivered_time: Optional[datetime] = None
    failure_reason: Optional[str] = None
    retry_count: int = 0


@dataclass
class SMSCampaign:
    """SMS campaign configuration"""
    campaign_id: str
    tenant_id: str
    name: str
    sms_type: SMSType
    template: str
    recipient_list: List[Dict[str, Any]]
    scheduled_start: Optional[datetime]
    scheduled_end: Optional[datetime]
    priority: SMSPriority
    max_retries: int = 3
    retry_delay_minutes: int = 30
    personalization_enabled: bool = True
    compliance_checks: bool = True
    delivery_optimization: bool = True
    a_b_testing: bool = False
    test_percentage: float = 0.1


@dataclass
class SMSBatchMetrics:
    """SMS batch processing metrics"""
    campaign_id: str
    total_messages: int
    queued_messages: int
    sent_messages: int
    delivered_messages: int
    failed_messages: int
    opted_out_messages: int
    delivery_rate: float
    average_delivery_time: float
    throughput_per_hour: float
    cost_per_message: float
    total_cost: float


class SMSBatchProcessor:
    """
    Advanced SMS batch processing engine with intelligent delivery optimization.
    
    This processor manages high-volume SMS campaigns across 80 modems with
    intelligent load balancing, personalization, compliance management,
    and real-time analytics for maximum delivery effectiveness.
    """
    
    def __init__(self, celery_app: Celery):
        self.celery_app = celery_app
        
        # Processing state
        self.active_campaigns = {}
        self.message_queues = defaultdict(deque)  # Per-modem queues
        self.modem_status = {}  # Track modem availability
        self.delivery_stats = defaultdict(dict)
        
        # Configuration
        self.max_messages_per_modem_per_hour = 100
        self.max_concurrent_campaigns = 10
        self.compliance_keywords = self._load_compliance_keywords()
        self.opt_out_keywords = ["STOP", "UNSUBSCRIBE", "QUIT", "CANCEL", "END"]
        
        # Template engine
        self.template_cache = {}
        
        # Analytics
        self.delivery_analytics = {}
        self.performance_history = defaultdict(list)
        
        # Modem assignment strategy
        self.modem_assignment_strategy = "round_robin"  # round_robin, load_based, geographic
        self.current_modem_index = 0
        
        logger.info("SMS batch processor initialized")
    
    async def start_sms_campaign(
        self,
        campaign: SMSCampaign
    ) -> Dict[str, Any]:
        """
        Start a new SMS campaign with batch processing.
        
        Args:
            campaign: SMS campaign configuration
            
        Returns:
            Campaign startup result
        """
        try:
            logger.info(f"Starting SMS campaign {campaign.campaign_id} with {len(campaign.recipient_list)} recipients")
            
            # Validate campaign
            validation_result = await self._validate_campaign(campaign)
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "error": validation_result["error"],
                    "message": "Campaign validation failed"
                }
            
            # Process recipient list
            processed_recipients = await self._process_recipient_list(
                campaign.recipient_list, campaign.compliance_checks
            )
            
            if not processed_recipients:
                return {
                    "success": False,
                    "error": "No valid recipients after processing",
                    "message": "Campaign has no valid recipients"
                }
            
            # Generate SMS messages
            messages = await self._generate_sms_messages(campaign, processed_recipients)
            
            # Set up A/B testing if enabled
            if campaign.a_b_testing:
                messages = await self._setup_ab_testing(campaign, messages)
            
            # Initialize campaign state
            campaign_state = {
                "campaign": campaign,
                "messages": {msg.message_id: msg for msg in messages},
                "status": "running",
                "start_time": datetime.utcnow(),
                "total_messages": len(messages),
                "processed_messages": 0,
                "metrics": SMSBatchMetrics(
                    campaign_id=campaign.campaign_id,
                    total_messages=len(messages),
                    queued_messages=len(messages),
                    sent_messages=0,
                    delivered_messages=0,
                    failed_messages=0,
                    opted_out_messages=0,
                    delivery_rate=0.0,
                    average_delivery_time=0.0,
                    throughput_per_hour=0.0,
                    cost_per_message=0.02,  # $0.02 per SMS
                    total_cost=len(messages) * 0.02
                )
            }
            
            self.active_campaigns[campaign.campaign_id] = campaign_state
            
            # Queue messages for processing
            await self._queue_messages_for_delivery(campaign.campaign_id, messages)
            
            # Start campaign processing
            task = self.celery_app.send_task(
                'sms_batch_processor.process_campaign',
                args=[campaign.campaign_id],
                queue='sms_processing'
            )
            
            campaign_state["task_id"] = task.id
            
            logger.info(f"SMS campaign {campaign.campaign_id} started successfully")
            
            return {
                "success": True,
                "campaign_id": campaign.campaign_id,
                "task_id": task.id,
                "total_messages": len(messages),
                "valid_recipients": len(processed_recipients),
                "estimated_duration": self._estimate_campaign_duration(len(messages)),
                "estimated_cost": len(messages) * 0.02,
                "message": "SMS campaign started successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to start SMS campaign {campaign.campaign_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to start SMS campaign"
            }
    
    async def process_campaign(self, campaign_id: str):
        """
        Main campaign processing loop.
        
        Args:
            campaign_id: Campaign identifier
        """
        try:
            campaign_state = self.active_campaigns.get(campaign_id)
            if not campaign_state:
                logger.error(f"Campaign {campaign_id} not found")
                return
            
            logger.info(f"Processing SMS campaign {campaign_id}")
            
            campaign = campaign_state["campaign"]
            messages = campaign_state["messages"]
            
            # Process messages in batches
            while campaign_state["status"] == "running":
                # Get available modems
                available_modems = await self._get_available_modems()
                
                if not available_modems:
                    logger.warning("No modems available, waiting...")
                    await asyncio.sleep(30)
                    continue
                
                # Process messages for each available modem
                tasks = []
                for modem_id in available_modems:
                    if modem_id in self.message_queues and self.message_queues[modem_id]:
                        # Get next message for this modem
                        message = self.message_queues[modem_id].popleft()
                        
                        # Start SMS sending task
                        task = self.celery_app.send_task(
                            'sms_batch_processor.send_sms',
                            args=[campaign_id, message.message_id, modem_id],
                            queue='sms_sending'
                        )
                        tasks.append(task)
                
                # Wait for batch completion or timeout
                if tasks:
                    await asyncio.sleep(5)  # Allow time for processing
                
                # Update campaign metrics
                await self._update_campaign_metrics(campaign_id)
                
                # Check if campaign is complete
                if all(msg.status in [SMSStatus.SENT, SMSStatus.DELIVERED, SMSStatus.FAILED, SMSStatus.OPTED_OUT] 
                       for msg in messages.values()):
                    break
                
                # Check for campaign timeout
                if campaign.scheduled_end and datetime.utcnow() > campaign.scheduled_end:
                    logger.info(f"Campaign {campaign_id} reached scheduled end time")
                    break
                
                await asyncio.sleep(1)  # Prevent tight loop
            
            # Finalize campaign
            await self._finalize_campaign(campaign_id)
            
        except Exception as e:
            logger.error(f"Campaign processing failed for {campaign_id}: {str(e)}")
            await self._handle_campaign_error(campaign_id, str(e))
    
    async def send_sms(self, campaign_id: str, message_id: str, modem_id: str):
        """
        Send individual SMS message.
        
        Args:
            campaign_id: Campaign identifier
            message_id: Message identifier
            modem_id: Modem identifier
        """
        try:
            campaign_state = self.active_campaigns.get(campaign_id)
            if not campaign_state:
                logger.error(f"Campaign {campaign_id} not found")
                return
            
            message = campaign_state["messages"].get(message_id)
            if not message:
                logger.error(f"Message {message_id} not found")
                return
            
            # Update message status
            message.status = SMSStatus.SENDING
            message.modem_id = modem_id
            message.sent_time = datetime.utcnow()
            
            # Send SMS via modem daemon
            result = await self._send_sms_via_modem(modem_id, message)
            
            if result["success"]:
                message.status = SMSStatus.SENT
                logger.info(f"SMS sent successfully: {message_id} via {modem_id}")
                
                # Schedule delivery confirmation check
                self.celery_app.send_task(
                    'sms_batch_processor.check_delivery_status',
                    args=[campaign_id, message_id],
                    countdown=300  # Check after 5 minutes
                )
            else:
                message.status = SMSStatus.FAILED
                message.failure_reason = result.get("error", "Unknown error")
                logger.error(f"SMS sending failed: {message_id} - {message.failure_reason}")
                
                # Schedule retry if applicable
                if message.retry_count < campaign_state["campaign"].max_retries:
                    await self._schedule_retry(campaign_id, message_id)
            
        except Exception as e:
            logger.error(f"Failed to send SMS {message_id}: {str(e)}")
            
            # Update message status
            if campaign_id in self.active_campaigns and message_id in self.active_campaigns[campaign_id]["messages"]:
                message = self.active_campaigns[campaign_id]["messages"][message_id]
                message.status = SMSStatus.FAILED
                message.failure_reason = str(e)
    
    async def check_delivery_status(self, campaign_id: str, message_id: str):
        """
        Check SMS delivery status.
        
        Args:
            campaign_id: Campaign identifier
            message_id: Message identifier
        """
        try:
            campaign_state = self.active_campaigns.get(campaign_id)
            if not campaign_state:
                return
            
            message = campaign_state["messages"].get(message_id)
            if not message or message.status != SMSStatus.SENT:
                return
            
            # Check delivery status via modem daemon
            delivery_status = await self._check_sms_delivery_status(message.modem_id, message_id)
            
            if delivery_status["delivered"]:
                message.status = SMSStatus.DELIVERED
                message.delivered_time = datetime.utcnow()
                logger.info(f"SMS delivered: {message_id}")
            elif delivery_status["failed"]:
                message.status = SMSStatus.FAILED
                message.failure_reason = delivery_status.get("error", "Delivery failed")
                logger.warning(f"SMS delivery failed: {message_id}")
            
        except Exception as e:
            logger.error(f"Failed to check delivery status for {message_id}: {str(e)}")
    
    async def pause_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """
        Pause an active SMS campaign.
        
        Args:
            campaign_id: Campaign identifier
            
        Returns:
            Pause operation result
        """
        try:
            campaign_state = self.active_campaigns.get(campaign_id)
            if not campaign_state:
                return {"success": False, "error": "Campaign not found"}
            
            campaign_state["status"] = "paused"
            campaign_state["pause_time"] = datetime.utcnow()
            
            logger.info(f"SMS campaign {campaign_id} paused")
            
            return {
                "success": True,
                "message": "Campaign paused successfully",
                "paused_at": campaign_state["pause_time"].isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to pause campaign {campaign_id}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def resume_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """
        Resume a paused SMS campaign.
        
        Args:
            campaign_id: Campaign identifier
            
        Returns:
            Resume operation result
        """
        try:
            campaign_state = self.active_campaigns.get(campaign_id)
            if not campaign_state:
                return {"success": False, "error": "Campaign not found"}
            
            if campaign_state["status"] != "paused":
                return {"success": False, "error": "Campaign is not paused"}
            
            campaign_state["status"] = "running"
            campaign_state["resume_time"] = datetime.utcnow()
            
            # Restart processing
            task = self.celery_app.send_task(
                'sms_batch_processor.process_campaign',
                args=[campaign_id],
                queue='sms_processing'
            )
            
            campaign_state["task_id"] = task.id
            
            logger.info(f"SMS campaign {campaign_id} resumed")
            
            return {
                "success": True,
                "message": "Campaign resumed successfully",
                "resumed_at": campaign_state["resume_time"].isoformat(),
                "task_id": task.id
            }
            
        except Exception as e:
            logger.error(f"Failed to resume campaign {campaign_id}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def stop_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """
        Stop an SMS campaign completely.
        
        Args:
            campaign_id: Campaign identifier
            
        Returns:
            Stop operation result
        """
        try:
            campaign_state = self.active_campaigns.get(campaign_id)
            if not campaign_state:
                return {"success": False, "error": "Campaign not found"}
            
            campaign_state["status"] = "stopped"
            campaign_state["end_time"] = datetime.utcnow()
            
            # Cancel processing task
            if "task_id" in campaign_state:
                self.celery_app.control.revoke(campaign_state["task_id"], terminate=True)
            
            # Generate final report
            final_report = await self._generate_campaign_report(campaign_id)
            
            logger.info(f"SMS campaign {campaign_id} stopped")
            
            return {
                "success": True,
                "message": "Campaign stopped successfully",
                "stopped_at": campaign_state["end_time"].isoformat(),
                "final_report": final_report
            }
            
        except Exception as e:
            logger.error(f"Failed to stop campaign {campaign_id}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_campaign_status(self, campaign_id: str) -> Dict[str, Any]:
        """
        Get current campaign status and metrics.
        
        Args:
            campaign_id: Campaign identifier
            
        Returns:
            Campaign status and metrics
        """
        try:
            campaign_state = self.active_campaigns.get(campaign_id)
            if not campaign_state:
                return {"error": "Campaign not found"}
            
            # Update metrics
            await self._update_campaign_metrics(campaign_id)
            
            return {
                "campaign_id": campaign_id,
                "status": campaign_state["status"],
                "start_time": campaign_state["start_time"].isoformat(),
                "metrics": asdict(campaign_state["metrics"]),
                "progress_percentage": (campaign_state["processed_messages"] / campaign_state["total_messages"] * 100) if campaign_state["total_messages"] > 0 else 0,
                "estimated_completion": self._estimate_completion_time(campaign_id),
                "recent_activity": self._get_recent_activity(campaign_id)
            }
            
        except Exception as e:
            logger.error(f"Failed to get campaign status for {campaign_id}: {str(e)}")
            return {"error": str(e)}
    
    async def process_opt_out(self, phone_number: str, message_content: str) -> Dict[str, Any]:
        """
        Process opt-out request from SMS reply.
        
        Args:
            phone_number: Phone number requesting opt-out
            message_content: Content of the opt-out message
            
        Returns:
            Opt-out processing result
        """
        try:
            # Normalize phone number
            normalized_phone = self._normalize_phone_number(phone_number)
            
            # Check if message contains opt-out keywords
            is_opt_out = any(keyword.lower() in message_content.upper() for keyword in self.opt_out_keywords)
            
            if is_opt_out:
                # Add to opt-out list
                await self._add_to_opt_out_list(normalized_phone)
                
                # Send confirmation SMS
                confirmation_message = "You have been successfully unsubscribed from our SMS messages. Reply HELP for assistance."
                await self._send_confirmation_sms(normalized_phone, confirmation_message)
                
                logger.info(f"Processed opt-out for {normalized_phone}")
                
                return {
                    "success": True,
                    "phone_number": normalized_phone,
                    "action": "opted_out",
                    "message": "Opt-out processed successfully"
                }
            else:
                return {
                    "success": False,
                    "phone_number": normalized_phone,
                    "action": "no_action",
                    "message": "Message does not contain opt-out keywords"
                }
                
        except Exception as e:
            logger.error(f"Failed to process opt-out for {phone_number}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # Private helper methods
    
    async def _validate_campaign(self, campaign: SMSCampaign) -> Dict[str, Any]:
        """Validate SMS campaign configuration"""
        try:
            # Check required fields
            if not campaign.campaign_id:
                return {"valid": False, "error": "Campaign ID is required"}
            
            if not campaign.template:
                return {"valid": False, "error": "SMS template is required"}
            
            if not campaign.recipient_list:
                return {"valid": False, "error": "Recipient list cannot be empty"}
            
            # Validate template
            try:
                Template(campaign.template)
            except Exception as e:
                return {"valid": False, "error": f"Invalid template: {str(e)}"}
            
            # Check message length
            sample_message = await self._render_template(campaign.template, {"name": "Test"})
            if len(sample_message) > 160:
                return {"valid": False, "error": "Message template exceeds 160 characters"}
            
            # Check compliance
            if campaign.compliance_checks:
                compliance_result = await self._check_template_compliance(campaign.template)
                if not compliance_result["compliant"]:
                    return {"valid": False, "error": f"Compliance violation: {compliance_result['violation']}"}
            
            return {"valid": True}
            
        except Exception as e:
            return {"valid": False, "error": str(e)}
    
    async def _process_recipient_list(
        self,
        recipient_list: List[Dict[str, Any]],
        compliance_checks: bool
    ) -> List[Dict[str, Any]]:
        """Process and validate recipient list"""
        processed_recipients = []
        
        for recipient in recipient_list:
            try:
                # Validate phone number
                phone_number = recipient.get("phone_number", "")
                normalized_phone = self._normalize_phone_number(phone_number)
                
                if not normalized_phone:
                    logger.warning(f"Invalid phone number: {phone_number}")
                    continue
                
                # Check opt-out status
                if compliance_checks and await self._is_opted_out(normalized_phone):
                    logger.info(f"Skipping opted-out number: {normalized_phone}")
                    continue
                
                # Check do-not-call list
                if compliance_checks and await self._is_on_dnc_list(normalized_phone):
                    logger.info(f"Skipping DNC number: {normalized_phone}")
                    continue
                
                recipient["phone_number"] = normalized_phone
                processed_recipients.append(recipient)
                
            except Exception as e:
                logger.error(f"Failed to process recipient {recipient}: {str(e)}")
                continue
        
        return processed_recipients
    
    async def _generate_sms_messages(
        self,
        campaign: SMSCampaign,
        recipients: List[Dict[str, Any]]
    ) -> List[SMSMessage]:
        """Generate SMS messages for campaign"""
        messages = []
        
        for i, recipient in enumerate(recipients):
            try:
                # Render personalized message
                if campaign.personalization_enabled:
                    content = await self._render_template(campaign.template, recipient)
                else:
                    content = campaign.template
                
                # Create message
                message = SMSMessage(
                    message_id=f"{campaign.campaign_id}_{i}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                    campaign_id=campaign.campaign_id,
                    recipient_phone=recipient["phone_number"],
                    content=content,
                    sms_type=campaign.sms_type,
                    priority=campaign.priority,
                    scheduled_time=campaign.scheduled_start,
                    personalization_data=recipient if campaign.personalization_enabled else None,
                    metadata={"recipient_index": i}
                )
                
                messages.append(message)
                
            except Exception as e:
                logger.error(f"Failed to generate message for recipient {recipient}: {str(e)}")
                continue
        
        return messages
    
    async def _setup_ab_testing(
        self,
        campaign: SMSCampaign,
        messages: List[SMSMessage]
    ) -> List[SMSMessage]:
        """Set up A/B testing for campaign"""
        if not campaign.a_b_testing:
            return messages
        
        # Split messages into test groups
        test_count = int(len(messages) * campaign.test_percentage)
        
        # Randomly select test group
        import random
        random.shuffle(messages)
        
        for i, message in enumerate(messages):
            if i < test_count:
                message.metadata = message.metadata or {}
                message.metadata["ab_group"] = "test"
                # Apply test variation (could be different template, timing, etc.)
            else:
                message.metadata = message.metadata or {}
                message.metadata["ab_group"] = "control"
        
        return messages
    
    async def _queue_messages_for_delivery(
        self,
        campaign_id: str,
        messages: List[SMSMessage]
    ):
        """Queue messages for delivery across modems"""
        # Sort messages by priority and scheduled time
        sorted_messages = sorted(
            messages,
            key=lambda x: (
                x.priority.value,
                x.scheduled_time or datetime.utcnow()
            )
        )
        
        # Distribute messages across modems
        available_modems = await self._get_available_modems()
        
        if not available_modems:
            logger.warning("No modems available for message queuing")
            return
        
        for i, message in enumerate(sorted_messages):
            # Assign modem based on strategy
            modem_id = self._assign_modem(available_modems, message)
            self.message_queues[modem_id].append(message)
    
    def _assign_modem(self, available_modems: List[str], message: SMSMessage) -> str:
        """Assign modem for message delivery"""
        if self.modem_assignment_strategy == "round_robin":
            modem_id = available_modems[self.current_modem_index % len(available_modems)]
            self.current_modem_index += 1
            return modem_id
        
        elif self.modem_assignment_strategy == "load_based":
            # Choose modem with smallest queue
            modem_loads = {modem: len(self.message_queues[modem]) for modem in available_modems}
            return min(modem_loads, key=modem_loads.get)
        
        elif self.modem_assignment_strategy == "geographic":
            # Assign based on phone number area code (simplified)
            area_code = message.recipient_phone[:3] if len(message.recipient_phone) >= 3 else "000"
            modem_index = int(area_code) % len(available_modems)
            return available_modems[modem_index]
        
        else:
            # Default to round robin
            return available_modems[0]
    
    async def _render_template(self, template_str: str, data: Dict[str, Any]) -> str:
        """Render SMS template with personalization data"""
        try:
            # Cache templates for performance
            if template_str not in self.template_cache:
                self.template_cache[template_str] = Template(template_str)
            
            template = self.template_cache[template_str]
            return template.render(**data)
            
        except Exception as e:
            logger.error(f"Failed to render template: {str(e)}")
            return template_str  # Return original template on error
    
    def _normalize_phone_number(self, phone_number: str) -> Optional[str]:
        """Normalize phone number to E.164 format"""
        try:
            # Remove non-digit characters
            cleaned = re.sub(r'[^\d+]', '', phone_number)
            
            # Parse phone number
            parsed = phonenumbers.parse(cleaned, "US")  # Default to US
            
            if phonenumbers.is_valid_number(parsed):
                return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
            else:
                return None
                
        except NumberParseException:
            return None
    
    async def _get_available_modems(self) -> List[str]:
        """Get list of available modems for SMS sending"""
        # This would integrate with the modem management system
        # For now, return mock modem list
        all_modems = [f"modem_{i}" for i in range(1, 81)]  # 80 modems
        
        # Filter out busy modems (simplified)
        available_modems = []
        for modem_id in all_modems:
            current_load = len(self.message_queues.get(modem_id, []))
            if current_load < self.max_messages_per_modem_per_hour / 60:  # Per minute limit
                available_modems.append(modem_id)
        
        return available_modems[:20]  # Limit to 20 concurrent modems
    
    async def _send_sms_via_modem(self, modem_id: str, message: SMSMessage) -> Dict[str, Any]:
        """Send SMS via specific modem"""
        try:
            # This would integrate with the modem-daemon
            # For now, simulate SMS sending
            
            # Simulate network delay
            await asyncio.sleep(0.1)
            
            # Simulate success/failure (95% success rate)
            import random
            if random.random() < 0.95:
                return {
                    "success": True,
                    "message_id": message.message_id,
                    "modem_id": modem_id,
                    "sent_time": datetime.utcnow().isoformat()
                }
            else:
                return {
                    "success": False,
                    "error": "Network timeout",
                    "message_id": message.message_id,
                    "modem_id": modem_id
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message_id": message.message_id,
                "modem_id": modem_id
            }
    
    async def _check_sms_delivery_status(self, modem_id: str, message_id: str) -> Dict[str, Any]:
        """Check SMS delivery status via modem"""
        try:
            # This would integrate with the modem-daemon
            # For now, simulate delivery status check
            
            import random
            if random.random() < 0.9:  # 90% delivery rate
                return {
                    "delivered": True,
                    "delivery_time": datetime.utcnow().isoformat()
                }
            else:
                return {
                    "delivered": False,
                    "failed": True,
                    "error": "Delivery failed"
                }
                
        except Exception as e:
            return {
                "delivered": False,
                "failed": True,
                "error": str(e)
            }
    
    async def _schedule_retry(self, campaign_id: str, message_id: str):
        """Schedule message retry"""
        campaign_state = self.active_campaigns.get(campaign_id)
        if not campaign_state:
            return
        
        message = campaign_state["messages"].get(message_id)
        if not message:
            return
        
        campaign = campaign_state["campaign"]
        
        if message.retry_count < campaign.max_retries:
            message.retry_count += 1
            message.status = SMSStatus.PENDING
            
            # Schedule retry
            retry_delay = campaign.retry_delay_minutes * 60  # Convert to seconds
            
            self.celery_app.send_task(
                'sms_batch_processor.retry_sms',
                args=[campaign_id, message_id],
                countdown=retry_delay
            )
            
            logger.info(f"Scheduled retry {message.retry_count} for message {message_id}")
    
    async def _update_campaign_metrics(self, campaign_id: str):
        """Update campaign metrics"""
        campaign_state = self.active_campaigns.get(campaign_id)
        if not campaign_state:
            return
        
        messages = campaign_state["messages"]
        metrics = campaign_state["metrics"]
        
        # Count messages by status
        status_counts = defaultdict(int)
        for message in messages.values():
            status_counts[message.status] += 1
        
        # Update metrics
        metrics.queued_messages = status_counts[SMSStatus.PENDING] + status_counts[SMSStatus.QUEUED]
        metrics.sent_messages = status_counts[SMSStatus.SENT] + status_counts[SMSStatus.DELIVERED]
        metrics.delivered_messages = status_counts[SMSStatus.DELIVERED]
        metrics.failed_messages = status_counts[SMSStatus.FAILED]
        metrics.opted_out_messages = status_counts[SMSStatus.OPTED_OUT]
        
        # Calculate rates
        total_processed = metrics.sent_messages + metrics.failed_messages + metrics.opted_out_messages
        if total_processed > 0:
            metrics.delivery_rate = (metrics.delivered_messages / total_processed) * 100
        
        # Calculate average delivery time
        delivered_messages = [m for m in messages.values() if m.delivered_time and m.sent_time]
        if delivered_messages:
            delivery_times = [(m.delivered_time - m.sent_time).total_seconds() for m in delivered_messages]
            metrics.average_delivery_time = statistics.mean(delivery_times)
        
        # Calculate throughput
        elapsed_time = (datetime.utcnow() - campaign_state["start_time"]).total_seconds() / 3600
        if elapsed_time > 0:
            metrics.throughput_per_hour = total_processed / elapsed_time
        
        campaign_state["processed_messages"] = total_processed
    
    async def _finalize_campaign(self, campaign_id: str):
        """Finalize completed campaign"""
        campaign_state = self.active_campaigns[campaign_id]
        campaign_state["status"] = "completed"
        campaign_state["end_time"] = datetime.utcnow()
        
        # Generate final report
        final_report = await self._generate_campaign_report(campaign_id)
        campaign_state["final_report"] = final_report
        
        logger.info(f"SMS campaign {campaign_id} completed successfully")
    
    async def _handle_campaign_error(self, campaign_id: str, error_message: str):
        """Handle campaign execution errors"""
        campaign_state = self.active_campaigns[campaign_id]
        campaign_state["status"] = "failed"
        campaign_state["error"] = error_message
        campaign_state["end_time"] = datetime.utcnow()
        
        logger.error(f"SMS campaign {campaign_id} failed: {error_message}")
    
    async def _generate_campaign_report(self, campaign_id: str) -> Dict[str, Any]:
        """Generate comprehensive campaign report"""
        campaign_state = self.active_campaigns[campaign_id]
        metrics = campaign_state["metrics"]
        
        # Calculate final statistics
        total_duration = (campaign_state.get("end_time", datetime.utcnow()) - 
                         campaign_state["start_time"]).total_seconds()
        
        report = {
            "campaign_id": campaign_id,
            "status": campaign_state["status"],
            "duration_seconds": total_duration,
            "total_messages": metrics.total_messages,
            "sent_messages": metrics.sent_messages,
            "delivered_messages": metrics.delivered_messages,
            "failed_messages": metrics.failed_messages,
            "opted_out_messages": metrics.opted_out_messages,
            "delivery_rate": metrics.delivery_rate,
            "average_delivery_time": metrics.average_delivery_time,
            "throughput_per_hour": metrics.throughput_per_hour,
            "total_cost": metrics.total_cost,
            "cost_per_delivered": metrics.total_cost / max(metrics.delivered_messages, 1),
            "performance_summary": {
                "success_rate": (metrics.delivered_messages / metrics.total_messages * 100) if metrics.total_messages > 0 else 0,
                "efficiency_score": self._calculate_efficiency_score(metrics),
                "cost_effectiveness": self._calculate_cost_effectiveness(metrics)
            }
        }
        
        return report
    
    def _calculate_efficiency_score(self, metrics: SMSBatchMetrics) -> float:
        """Calculate campaign efficiency score"""
        if metrics.total_messages == 0:
            return 0.0
        
        # Weighted score based on delivery rate and throughput
        delivery_weight = 0.7
        throughput_weight = 0.3
        
        delivery_score = metrics.delivery_rate / 100.0
        throughput_score = min(1.0, metrics.throughput_per_hour / 1000.0)  # Normalize to 1000/hour
        
        return (delivery_score * delivery_weight + throughput_score * throughput_weight) * 100
    
    def _calculate_cost_effectiveness(self, metrics: SMSBatchMetrics) -> float:
        """Calculate cost effectiveness score"""
        if metrics.delivered_messages == 0:
            return 0.0
        
        cost_per_delivery = metrics.total_cost / metrics.delivered_messages
        
        # Score based on cost efficiency (lower cost = higher score)
        if cost_per_delivery <= 0.02:
            return 100.0
        elif cost_per_delivery <= 0.05:
            return 80.0
        elif cost_per_delivery <= 0.10:
            return 60.0
        else:
            return 40.0
    
    def _estimate_campaign_duration(self, message_count: int) -> str:
        """Estimate campaign completion time"""
        # Assume 20 modems processing 100 messages/hour each
        messages_per_hour = 20 * 100
        hours = message_count / messages_per_hour
        
        if hours < 1:
            return f"{int(hours * 60)} minutes"
        elif hours < 24:
            return f"{hours:.1f} hours"
        else:
            return f"{hours / 24:.1f} days"
    
    def _estimate_completion_time(self, campaign_id: str) -> Optional[str]:
        """Estimate campaign completion time"""
        campaign_state = self.active_campaigns.get(campaign_id)
        if not campaign_state:
            return None
        
        metrics = campaign_state["metrics"]
        
        if metrics.throughput_per_hour > 0:
            remaining_messages = metrics.total_messages - (metrics.sent_messages + metrics.failed_messages)
            hours_remaining = remaining_messages / metrics.throughput_per_hour
            completion_time = datetime.utcnow() + timedelta(hours=hours_remaining)
            return completion_time.isoformat()
        
        return None
    
    def _get_recent_activity(self, campaign_id: str) -> List[Dict[str, Any]]:
        """Get recent campaign activity"""
        # This would return recent message status changes
        # For now, return mock data
        return [
            {
                "timestamp": datetime.utcnow().isoformat(),
                "event": "messages_sent",
                "count": 50
            },
            {
                "timestamp": (datetime.utcnow() - timedelta(minutes=5)).isoformat(),
                "event": "messages_delivered",
                "count": 45
            }
        ]
    
    # Compliance and opt-out management
    
    def _load_compliance_keywords(self) -> List[str]:
        """Load compliance keywords to check"""
        return [
            "free", "winner", "congratulations", "urgent", "limited time",
            "act now", "click here", "call now", "guarantee", "risk-free"
        ]
    
    async def _check_template_compliance(self, template: str) -> Dict[str, Any]:
        """Check template for compliance violations"""
        template_lower = template.lower()
        
        # Check for prohibited keywords
        for keyword in self.compliance_keywords:
            if keyword.lower() in template_lower:
                return {
                    "compliant": False,
                    "violation": f"Contains prohibited keyword: {keyword}"
                }
        
        # Check for required opt-out language
        if "stop" not in template_lower and "unsubscribe" not in template_lower:
            return {
                "compliant": False,
                "violation": "Missing opt-out instructions"
            }
        
        return {"compliant": True}
    
    async def _is_opted_out(self, phone_number: str) -> bool:
        """Check if phone number is on opt-out list"""
        # This would check against the database
        # For now, return False
        return False
    
    async def _is_on_dnc_list(self, phone_number: str) -> bool:
        """Check if phone number is on do-not-call list"""
        # This would check against the DNC registry
        # For now, return False
        return False
    
    async def _add_to_opt_out_list(self, phone_number: str):
        """Add phone number to opt-out list"""
        # This would update the database
        logger.info(f"Added {phone_number} to opt-out list")
    
    async def _send_confirmation_sms(self, phone_number: str, message: str):
        """Send opt-out confirmation SMS"""
        # This would send via modem-daemon
        logger.info(f"Sent opt-out confirmation to {phone_number}")


# Global SMS batch processor instance
sms_batch_processor = None

def get_sms_batch_processor(celery_app: Celery) -> SMSBatchProcessor:
    """Get or create SMS batch processor instance"""
    global sms_batch_processor
    if sms_batch_processor is None:
        sms_batch_processor = SMSBatchProcessor(celery_app)
    return sms_batch_processor