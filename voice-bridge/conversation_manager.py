"""
Conversation Manager Module

This module implements comprehensive conversation state management for
voice-based interactions, providing context preservation, conversation
flow orchestration, and intelligent session handling. The manager
ensures coherent and contextually aware conversations across extended
interactions while maintaining optimal performance and scalability.

The conversation manager serves as the memory and context engine for
the voice-bridge system, enabling sophisticated conversation management
with persistent state and intelligent context analysis.
"""

import asyncio
import logging
import time
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from collections import deque, defaultdict

import redis.asyncio as redis

from config import VoiceBridgeConfig
from nlu_extractor import NLUResults


class ConversationStage(Enum):
    """Enumeration of conversation stages."""
    OPENING = "opening"
    INFORMATION_GATHERING = "information_gathering"
    PROBLEM_SOLVING = "problem_solving"
    SOLUTION_IMPLEMENTATION = "solution_implementation"
    CONFIRMATION = "confirmation"
    CLOSING = "closing"
    ESCALATION = "escalation"


class MessageRole(Enum):
    """Enumeration of message roles."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class ConversationMessage:
    """Data class for conversation messages."""
    role: MessageRole
    content: str
    timestamp: float
    nlu_results: Optional[NLUResults]
    metadata: Dict[str, Any]


@dataclass
class ConversationContext:
    """Data class for conversation context."""
    session_id: str
    stage: ConversationStage
    topic: str
    urgency_level: float
    customer_satisfaction: float
    key_entities: Dict[str, Any]
    unresolved_issues: List[str]
    conversation_goals: List[str]
    customer_profile: Dict[str, Any]
    interaction_history: List[str]


@dataclass
class ConversationSession:
    """Data class for complete conversation session."""
    session_id: str
    created_at: float
    last_activity: float
    messages: deque
    context: ConversationContext
    metrics: Dict[str, Any]
    configuration: Dict[str, Any]


class ConversationManager:
    """
    Advanced conversation state management system.
    
    Provides comprehensive conversation management including context
    preservation, conversation flow orchestration, intelligent session
    handling, and persistent state management for voice-based interactions.
    """
    
    def __init__(self, config: VoiceBridgeConfig, redis_client: redis.Redis):
        """
        Initialize conversation manager.
        
        Args:
            config: Voice-bridge configuration
            redis_client: Redis client for persistent storage
        """
        self.config = config
        self.redis_client = redis_client
        self.logger = logging.getLogger(__name__)
        
        # Session management
        self.active_sessions: Dict[str, ConversationSession] = {}
        self.session_timeouts: Dict[str, float] = {}
        
        # Configuration
        self.max_message_history = config.nlu_context_window * 2
        self.session_timeout = config.connection_timeout
        self.enable_persistence = True
        self.enable_context_analysis = True
        
        # Performance tracking
        self.conversation_stats = {
            "total_sessions": 0,
            "active_sessions": 0,
            "avg_session_duration": 0.0,
            "avg_messages_per_session": 0.0,
            "total_messages": 0
        }
        
        # Context analysis
        self.context_patterns = self._initialize_context_patterns()
        self.conversation_flows = self._initialize_conversation_flows()
        
        # Background tasks
        self.cleanup_task: Optional[asyncio.Task] = None
        self.analytics_task: Optional[asyncio.Task] = None
        
        # Advanced features
        self.enable_predictive_context = True
        self.enable_conversation_analytics = True
        self.enable_auto_escalation = True
        
        # Customer profiling
        self.customer_profiles: Dict[str, Dict[str, Any]] = {}
        self.interaction_patterns: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    
    async def initialize(self) -> None:
        """
        Initialize conversation manager and start background tasks.
        
        Sets up persistent storage, context analysis, and background
        maintenance tasks for optimal conversation management.
        """
        self.logger.info("Initializing conversation manager")
        
        try:
            # Test Redis connectivity
            await self.redis_client.ping()
            
            # Load existing sessions from Redis
            await self._load_persistent_sessions()
            
            # Start background tasks
            self.cleanup_task = asyncio.create_task(self._session_cleanup())
            self.analytics_task = asyncio.create_task(self._conversation_analytics())
            
            self.logger.info("Conversation manager initialized successfully",
                           extra={"active_sessions": len(self.active_sessions)})
            
        except Exception as e:
            self.logger.error(f"Conversation manager initialization failed: {e}")
            raise
    
    def _initialize_context_patterns(self) -> Dict[str, List[str]]:
        """
        Initialize context patterns for conversation analysis.
        
        Returns:
            Dict containing context patterns
        """
        return {
            "greeting_patterns": [
                "hello", "hi", "hey", "good morning", "good afternoon", "good evening"
            ],
            "problem_indicators": [
                "problem", "issue", "error", "not working", "broken", "help"
            ],
            "satisfaction_indicators": [
                "thank you", "thanks", "great", "perfect", "excellent", "satisfied"
            ],
            "escalation_triggers": [
                "manager", "supervisor", "escalate", "complaint", "unacceptable"
            ],
            "closing_patterns": [
                "goodbye", "bye", "thank you", "that's all", "nothing else"
            ]
        }
    
    def _initialize_conversation_flows(self) -> Dict[str, Dict[str, Any]]:
        """
        Initialize conversation flow templates.
        
        Returns:
            Dict containing conversation flow definitions
        """
        return {
            "customer_service": {
                "stages": [
                    ConversationStage.OPENING,
                    ConversationStage.INFORMATION_GATHERING,
                    ConversationStage.PROBLEM_SOLVING,
                    ConversationStage.SOLUTION_IMPLEMENTATION,
                    ConversationStage.CONFIRMATION,
                    ConversationStage.CLOSING
                ],
                "goals": [
                    "understand_customer_issue",
                    "provide_solution",
                    "ensure_satisfaction",
                    "resolve_completely"
                ]
            },
            "sales_support": {
                "stages": [
                    ConversationStage.OPENING,
                    ConversationStage.INFORMATION_GATHERING,
                    ConversationStage.PROBLEM_SOLVING,
                    ConversationStage.CONFIRMATION,
                    ConversationStage.CLOSING
                ],
                "goals": [
                    "understand_customer_needs",
                    "present_solutions",
                    "address_objections",
                    "close_sale"
                ]
            },
            "technical_support": {
                "stages": [
                    ConversationStage.OPENING,
                    ConversationStage.INFORMATION_GATHERING,
                    ConversationStage.PROBLEM_SOLVING,
                    ConversationStage.SOLUTION_IMPLEMENTATION,
                    ConversationStage.CONFIRMATION,
                    ConversationStage.CLOSING
                ],
                "goals": [
                    "diagnose_technical_issue",
                    "provide_step_by_step_solution",
                    "verify_resolution",
                    "prevent_future_issues"
                ]
            }
        }
    
    async def create_session(self, session_id: str, 
                           conversation_type: str = "customer_service",
                           customer_info: Optional[Dict[str, Any]] = None) -> bool:
        """
        Create a new conversation session.
        
        Args:
            session_id: Unique session identifier
            conversation_type: Type of conversation flow
            customer_info: Optional customer information
            
        Returns:
            True if session created successfully, False otherwise
        """
        try:
            if session_id in self.active_sessions:
                self.logger.warning("Session already exists",
                                  extra={"session_id": session_id})
                return False
            
            # Create conversation context
            context = ConversationContext(
                session_id=session_id,
                stage=ConversationStage.OPENING,
                topic="general",
                urgency_level=0.0,
                customer_satisfaction=0.5,
                key_entities={},
                unresolved_issues=[],
                conversation_goals=self.conversation_flows.get(
                    conversation_type, {}
                ).get("goals", []),
                customer_profile=customer_info or {},
                interaction_history=[]
            )
            
            # Create session
            session = ConversationSession(
                session_id=session_id,
                created_at=time.time(),
                last_activity=time.time(),
                messages=deque(maxlen=self.max_message_history),
                context=context,
                metrics=self._initialize_session_metrics(),
                configuration={
                    "conversation_type": conversation_type,
                    "max_messages": self.max_message_history,
                    "timeout": self.session_timeout
                }
            )
            
            # Store session
            self.active_sessions[session_id] = session
            self.session_timeouts[session_id] = time.time() + self.session_timeout
            
            # Persist to Redis
            if self.enable_persistence:
                await self._persist_session(session)
            
            # Update statistics
            self.conversation_stats["total_sessions"] += 1
            self.conversation_stats["active_sessions"] = len(self.active_sessions)
            
            self.logger.info("Conversation session created",
                           extra={"session_id": session_id,
                                 "conversation_type": conversation_type})
            
            return True
            
        except Exception as e:
            self.logger.error(f"Session creation failed: {e}",
                            extra={"session_id": session_id})
            return False
    
    async def add_message(self, session_id: str, role: MessageRole, 
                         content: str, nlu_results: Optional[NLUResults] = None,
                         metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Add a message to the conversation session.
        
        Args:
            session_id: Session identifier
            role: Message role (user/assistant/system)
            content: Message content
            nlu_results: Optional NLU analysis results
            metadata: Optional message metadata
            
        Returns:
            True if message added successfully, False otherwise
        """
        try:
            if session_id not in self.active_sessions:
                self.logger.warning("Session not found for message",
                                  extra={"session_id": session_id})
                return False
            
            session = self.active_sessions[session_id]
            
            # Create message
            message = ConversationMessage(
                role=role,
                content=content,
                timestamp=time.time(),
                nlu_results=nlu_results,
                metadata=metadata or {}
            )
            
            # Add to session
            session.messages.append(message)
            session.last_activity = time.time()
            
            # Update session timeout
            self.session_timeouts[session_id] = time.time() + self.session_timeout
            
            # Update context based on message
            if nlu_results:
                await self._update_context_from_nlu(session, nlu_results)
            
            # Analyze conversation flow
            await self._analyze_conversation_flow(session, message)
            
            # Update metrics
            await self._update_session_metrics(session, message)
            
            # Persist changes
            if self.enable_persistence:
                await self._persist_session(session)
            
            # Update global statistics
            self.conversation_stats["total_messages"] += 1
            
            self.logger.debug("Message added to conversation",
                            extra={"session_id": session_id,
                                  "role": role.value,
                                  "content_length": len(content)})
            
            return True
            
        except Exception as e:
            self.logger.error(f"Message addition failed: {e}",
                            extra={"session_id": session_id})
            return False
    
    async def _update_context_from_nlu(self, session: ConversationSession, 
                                     nlu_results: NLUResults) -> None:
        """
        Update conversation context based on NLU results.
        
        Args:
            session: Conversation session
            nlu_results: NLU analysis results
        """
        try:
            context = session.context
            
            # Update topic
            if nlu_results.context.topic != "general":
                context.topic = nlu_results.context.topic
            
            # Update urgency level
            context.urgency_level = max(
                context.urgency_level,
                nlu_results.context.urgency_level
            )
            
            # Update customer satisfaction
            context.customer_satisfaction = (
                context.customer_satisfaction * 0.7 +
                nlu_results.context.customer_satisfaction * 0.3
            )
            
            # Update key entities
            for entity in nlu_results.entities:
                context.key_entities[entity.label] = {
                    "value": entity.text,
                    "confidence": entity.confidence,
                    "normalized": entity.normalized_value,
                    "timestamp": time.time()
                }
            
            # Update unresolved issues
            context.unresolved_issues.extend(
                nlu_results.context.unresolved_issues
            )
            # Remove duplicates
            context.unresolved_issues = list(set(context.unresolved_issues))
            
            # Update interaction history
            context.interaction_history.append(
                f"{nlu_results.intent.intent.value}:{nlu_results.sentiment.sentiment.value}"
            )
            
            # Keep only recent history
            if len(context.interaction_history) > 20:
                context.interaction_history = context.interaction_history[-20:]
            
        except Exception as e:
            self.logger.error(f"Context update from NLU failed: {e}")
    
    async def _analyze_conversation_flow(self, session: ConversationSession,
                                       message: ConversationMessage) -> None:
        """
        Analyze and update conversation flow stage.
        
        Args:
            session: Conversation session
            message: Latest message
        """
        try:
            context = session.context
            content_lower = message.content.lower()
            
            # Determine stage based on patterns and context
            current_stage = context.stage
            new_stage = current_stage
            
            # Check for stage transitions
            if current_stage == ConversationStage.OPENING:
                # Look for problem indicators or information requests
                if any(pattern in content_lower for pattern in 
                      self.context_patterns["problem_indicators"]):
                    new_stage = ConversationStage.PROBLEM_SOLVING
                elif len(session.messages) > 2:
                    new_stage = ConversationStage.INFORMATION_GATHERING
            
            elif current_stage == ConversationStage.INFORMATION_GATHERING:
                # Look for problem indicators
                if any(pattern in content_lower for pattern in 
                      self.context_patterns["problem_indicators"]):
                    new_stage = ConversationStage.PROBLEM_SOLVING
            
            elif current_stage == ConversationStage.PROBLEM_SOLVING:
                # Look for satisfaction indicators
                if any(pattern in content_lower for pattern in 
                      self.context_patterns["satisfaction_indicators"]):
                    new_stage = ConversationStage.CONFIRMATION
                # Look for escalation triggers
                elif any(pattern in content_lower for pattern in 
                        self.context_patterns["escalation_triggers"]):
                    new_stage = ConversationStage.ESCALATION
            
            elif current_stage == ConversationStage.CONFIRMATION:
                # Look for closing patterns
                if any(pattern in content_lower for pattern in 
                      self.context_patterns["closing_patterns"]):
                    new_stage = ConversationStage.CLOSING
            
            # Update stage if changed
            if new_stage != current_stage:
                context.stage = new_stage
                self.logger.debug("Conversation stage updated",
                                extra={"session_id": session.session_id,
                                      "old_stage": current_stage.value,
                                      "new_stage": new_stage.value})
            
            # Check for auto-escalation conditions
            if self.enable_auto_escalation:
                await self._check_escalation_conditions(session)
            
        except Exception as e:
            self.logger.error(f"Conversation flow analysis failed: {e}")
    
    async def _check_escalation_conditions(self, session: ConversationSession) -> None:
        """
        Check if conversation should be escalated.
        
        Args:
            session: Conversation session
        """
        try:
            context = session.context
            
            # Escalation conditions
            should_escalate = False
            escalation_reason = ""
            
            # High urgency and low satisfaction
            if (context.urgency_level > 0.8 and 
                context.customer_satisfaction < 0.3):
                should_escalate = True
                escalation_reason = "High urgency with low satisfaction"
            
            # Too many unresolved issues
            elif len(context.unresolved_issues) > 3:
                should_escalate = True
                escalation_reason = "Multiple unresolved issues"
            
            # Long conversation without resolution
            elif (len(session.messages) > 20 and 
                  context.stage not in [ConversationStage.CONFIRMATION, 
                                       ConversationStage.CLOSING]):
                should_escalate = True
                escalation_reason = "Extended conversation without resolution"
            
            # Explicit escalation request
            elif any("escalat" in msg.content.lower() or "manager" in msg.content.lower()
                    for msg in list(session.messages)[-3:] 
                    if msg.role == MessageRole.USER):
                should_escalate = True
                escalation_reason = "Customer requested escalation"
            
            if should_escalate:
                context.stage = ConversationStage.ESCALATION
                session.metrics["escalation_triggered"] = True
                session.metrics["escalation_reason"] = escalation_reason
                session.metrics["escalation_time"] = time.time()
                
                self.logger.info("Conversation escalation triggered",
                               extra={"session_id": session.session_id,
                                     "reason": escalation_reason})
            
        except Exception as e:
            self.logger.error(f"Escalation check failed: {e}")
    
    def _initialize_session_metrics(self) -> Dict[str, Any]:
        """
        Initialize metrics for a new session.
        
        Returns:
            Dict containing initial metrics
        """
        return {
            "message_count": 0,
            "user_messages": 0,
            "assistant_messages": 0,
            "avg_response_time": 0.0,
            "sentiment_trend": [],
            "satisfaction_trend": [],
            "escalation_triggered": False,
            "escalation_reason": None,
            "escalation_time": None,
            "resolution_achieved": False,
            "resolution_time": None
        }
    
    async def _update_session_metrics(self, session: ConversationSession,
                                    message: ConversationMessage) -> None:
        """
        Update session metrics based on new message.
        
        Args:
            session: Conversation session
            message: New message
        """
        try:
            metrics = session.metrics
            
            # Update message counts
            metrics["message_count"] += 1
            if message.role == MessageRole.USER:
                metrics["user_messages"] += 1
            elif message.role == MessageRole.ASSISTANT:
                metrics["assistant_messages"] += 1
            
            # Update sentiment and satisfaction trends
            if message.nlu_results:
                metrics["sentiment_trend"].append({
                    "timestamp": message.timestamp,
                    "sentiment": message.nlu_results.sentiment.sentiment.value,
                    "polarity": message.nlu_results.sentiment.polarity
                })
                
                metrics["satisfaction_trend"].append({
                    "timestamp": message.timestamp,
                    "satisfaction": message.nlu_results.context.customer_satisfaction
                })
                
                # Keep only recent trends
                if len(metrics["sentiment_trend"]) > 20:
                    metrics["sentiment_trend"] = metrics["sentiment_trend"][-20:]
                if len(metrics["satisfaction_trend"]) > 20:
                    metrics["satisfaction_trend"] = metrics["satisfaction_trend"][-20:]
            
            # Check for resolution
            if (session.context.stage == ConversationStage.CONFIRMATION and
                not metrics["resolution_achieved"]):
                metrics["resolution_achieved"] = True
                metrics["resolution_time"] = time.time()
            
        except Exception as e:
            self.logger.error(f"Session metrics update failed: {e}")
    
    async def get_conversation_history(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get complete conversation history for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dict containing conversation history or None if not found
        """
        try:
            if session_id not in self.active_sessions:
                # Try to load from Redis
                session = await self._load_session_from_redis(session_id)
                if not session:
                    return None
            else:
                session = self.active_sessions[session_id]
            
            # Convert messages to serializable format
            messages = []
            for msg in session.messages:
                message_dict = {
                    "role": msg.role.value,
                    "content": msg.content,
                    "timestamp": msg.timestamp,
                    "metadata": msg.metadata
                }
                
                if msg.nlu_results:
                    message_dict["nlu_results"] = {
                        "intent": msg.nlu_results.intent.intent.value,
                        "sentiment": msg.nlu_results.sentiment.sentiment.value,
                        "confidence": msg.nlu_results.confidence_score,
                        "entities": [
                            {
                                "text": e.text,
                                "label": e.label,
                                "confidence": e.confidence
                            }
                            for e in msg.nlu_results.entities
                        ]
                    }
                
                messages.append(message_dict)
            
            return {
                "session_id": session_id,
                "created_at": session.created_at,
                "last_activity": session.last_activity,
                "duration": time.time() - session.created_at,
                "messages": messages,
                "context": {
                    "stage": session.context.stage.value,
                    "topic": session.context.topic,
                    "urgency_level": session.context.urgency_level,
                    "customer_satisfaction": session.context.customer_satisfaction,
                    "key_entities": session.context.key_entities,
                    "unresolved_issues": session.context.unresolved_issues,
                    "conversation_goals": session.context.conversation_goals
                },
                "metrics": session.metrics,
                "configuration": session.configuration
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get conversation history: {e}",
                            extra={"session_id": session_id})
            return None
    
    async def end_session(self, session_id: str) -> bool:
        """
        End a conversation session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if session ended successfully, False otherwise
        """
        try:
            if session_id not in self.active_sessions:
                return False
            
            session = self.active_sessions[session_id]
            
            # Update final metrics
            session_duration = time.time() - session.created_at
            self._update_avg_session_duration(session_duration)
            
            # Calculate final statistics
            if session.metrics["message_count"] > 0:
                avg_messages = (
                    self.conversation_stats["avg_messages_per_session"] * 
                    (self.conversation_stats["total_sessions"] - 1) +
                    session.metrics["message_count"]
                ) / self.conversation_stats["total_sessions"]
                self.conversation_stats["avg_messages_per_session"] = avg_messages
            
            # Archive session to Redis
            if self.enable_persistence:
                await self._archive_session(session)
            
            # Remove from active sessions
            del self.active_sessions[session_id]
            if session_id in self.session_timeouts:
                del self.session_timeouts[session_id]
            
            # Update statistics
            self.conversation_stats["active_sessions"] = len(self.active_sessions)
            
            self.logger.info("Conversation session ended",
                           extra={"session_id": session_id,
                                 "duration": session_duration,
                                 "message_count": session.metrics["message_count"]})
            
            return True
            
        except Exception as e:
            self.logger.error(f"Session end failed: {e}",
                            extra={"session_id": session_id})
            return False
    
    def _update_avg_session_duration(self, duration: float) -> None:
        """
        Update average session duration statistics.
        
        Args:
            duration: Session duration in seconds
        """
        total_sessions = self.conversation_stats["total_sessions"]
        if total_sessions > 0:
            current_avg = self.conversation_stats["avg_session_duration"]
            self.conversation_stats["avg_session_duration"] = (
                (current_avg * (total_sessions - 1) + duration) / total_sessions
            )
    
    async def _persist_session(self, session: ConversationSession) -> None:
        """
        Persist session to Redis.
        
        Args:
            session: Session to persist
        """
        try:
            session_data = {
                "session_id": session.session_id,
                "created_at": session.created_at,
                "last_activity": session.last_activity,
                "messages": [
                    {
                        "role": msg.role.value,
                        "content": msg.content,
                        "timestamp": msg.timestamp,
                        "metadata": msg.metadata
                    }
                    for msg in session.messages
                ],
                "context": asdict(session.context),
                "metrics": session.metrics,
                "configuration": session.configuration
            }
            
            # Store in Redis with expiration
            await self.redis_client.setex(
                f"conversation:{session.session_id}",
                self.session_timeout * 2,  # Double timeout for persistence
                json.dumps(session_data, default=str)
            )
            
        except Exception as e:
            self.logger.error(f"Session persistence failed: {e}")
    
    async def _load_session_from_redis(self, session_id: str) -> Optional[ConversationSession]:
        """
        Load session from Redis.
        
        Args:
            session_id: Session identifier
            
        Returns:
            ConversationSession or None if not found
        """
        try:
            session_data = await self.redis_client.get(f"conversation:{session_id}")
            if not session_data:
                return None
            
            data = json.loads(session_data)
            
            # Reconstruct session
            messages = deque(maxlen=self.max_message_history)
            for msg_data in data["messages"]:
                message = ConversationMessage(
                    role=MessageRole(msg_data["role"]),
                    content=msg_data["content"],
                    timestamp=msg_data["timestamp"],
                    nlu_results=None,  # NLU results not persisted
                    metadata=msg_data["metadata"]
                )
                messages.append(message)
            
            context_data = data["context"]
            context = ConversationContext(
                session_id=context_data["session_id"],
                stage=ConversationStage(context_data["stage"]),
                topic=context_data["topic"],
                urgency_level=context_data["urgency_level"],
                customer_satisfaction=context_data["customer_satisfaction"],
                key_entities=context_data["key_entities"],
                unresolved_issues=context_data["unresolved_issues"],
                conversation_goals=context_data["conversation_goals"],
                customer_profile=context_data["customer_profile"],
                interaction_history=context_data["interaction_history"]
            )
            
            session = ConversationSession(
                session_id=data["session_id"],
                created_at=data["created_at"],
                last_activity=data["last_activity"],
                messages=messages,
                context=context,
                metrics=data["metrics"],
                configuration=data["configuration"]
            )
            
            return session
            
        except Exception as e:
            self.logger.error(f"Session loading from Redis failed: {e}")
            return None
    
    async def _load_persistent_sessions(self) -> None:
        """Load existing sessions from Redis on startup."""
        try:
            # Get all conversation keys
            keys = await self.redis_client.keys("conversation:*")
            
            for key in keys:
                session_id = key.decode().split(":", 1)[1]
                session = await self._load_session_from_redis(session_id)
                
                if session:
                    self.active_sessions[session_id] = session
                    self.session_timeouts[session_id] = time.time() + self.session_timeout
            
            self.logger.info("Persistent sessions loaded",
                           extra={"loaded_sessions": len(self.active_sessions)})
            
        except Exception as e:
            self.logger.error(f"Persistent session loading failed: {e}")
    
    async def _archive_session(self, session: ConversationSession) -> None:
        """
        Archive completed session for analytics.
        
        Args:
            session: Session to archive
        """
        try:
            archive_data = {
                "session_id": session.session_id,
                "created_at": session.created_at,
                "ended_at": time.time(),
                "duration": time.time() - session.created_at,
                "message_count": session.metrics["message_count"],
                "final_stage": session.context.stage.value,
                "final_satisfaction": session.context.customer_satisfaction,
                "resolution_achieved": session.metrics.get("resolution_achieved", False),
                "escalation_triggered": session.metrics.get("escalation_triggered", False),
                "topic": session.context.topic,
                "key_entities": session.context.key_entities
            }
            
            # Store in Redis archive with longer expiration
            await self.redis_client.setex(
                f"conversation_archive:{session.session_id}",
                86400 * 30,  # 30 days
                json.dumps(archive_data, default=str)
            )
            
        except Exception as e:
            self.logger.error(f"Session archiving failed: {e}")
    
    async def _session_cleanup(self) -> None:
        """
        Background task for cleaning up expired sessions.
        
        Removes sessions that have exceeded their timeout period
        and performs maintenance on conversation data.
        """
        while True:
            try:
                current_time = time.time()
                expired_sessions = []
                
                # Check for expired sessions
                for session_id, timeout_time in self.session_timeouts.items():
                    if current_time > timeout_time:
                        expired_sessions.append(session_id)
                
                # Clean up expired sessions
                for session_id in expired_sessions:
                    self.logger.info("Cleaning up expired session",
                                   extra={"session_id": session_id})
                    await self.end_session(session_id)
                
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Session cleanup error: {e}")
                await asyncio.sleep(60)
    
    async def _conversation_analytics(self) -> None:
        """
        Background task for conversation analytics and insights.
        
        Analyzes conversation patterns, generates insights, and
        updates performance metrics for system optimization.
        """
        while True:
            try:
                if self.enable_conversation_analytics:
                    # Analyze active conversations
                    await self._analyze_conversation_patterns()
                    
                    # Update performance metrics
                    await self._update_performance_metrics()
                
                await asyncio.sleep(300)  # Every 5 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Conversation analytics error: {e}")
                await asyncio.sleep(300)
    
    async def _analyze_conversation_patterns(self) -> None:
        """Analyze patterns in active conversations."""
        try:
            if not self.active_sessions:
                return
            
            # Analyze stage distribution
            stage_counts = defaultdict(int)
            satisfaction_levels = []
            urgency_levels = []
            
            for session in self.active_sessions.values():
                stage_counts[session.context.stage.value] += 1
                satisfaction_levels.append(session.context.customer_satisfaction)
                urgency_levels.append(session.context.urgency_level)
            
            # Calculate averages
            avg_satisfaction = sum(satisfaction_levels) / len(satisfaction_levels)
            avg_urgency = sum(urgency_levels) / len(urgency_levels)
            
            # Log insights
            self.logger.debug("Conversation pattern analysis",
                            extra={
                                "stage_distribution": dict(stage_counts),
                                "avg_satisfaction": avg_satisfaction,
                                "avg_urgency": avg_urgency,
                                "active_sessions": len(self.active_sessions)
                            })
            
        except Exception as e:
            self.logger.error(f"Conversation pattern analysis failed: {e}")
    
    async def _update_performance_metrics(self) -> None:
        """Update performance metrics for monitoring."""
        try:
            # Update active session count
            self.conversation_stats["active_sessions"] = len(self.active_sessions)
            
            # Calculate session health metrics
            if self.active_sessions:
                escalated_sessions = sum(
                    1 for session in self.active_sessions.values()
                    if session.context.stage == ConversationStage.ESCALATION
                )
                
                escalation_rate = escalated_sessions / len(self.active_sessions)
                
                # Log performance metrics
                self.logger.debug("Performance metrics update",
                                extra={
                                    "escalation_rate": escalation_rate,
                                    "active_sessions": len(self.active_sessions)
                                })
            
        except Exception as e:
            self.logger.error(f"Performance metrics update failed: {e}")
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive conversation manager statistics.
        
        Returns:
            Dict containing detailed statistics
        """
        try:
            stats = self.conversation_stats.copy()
            
            # Add current session information
            if self.active_sessions:
                current_stages = defaultdict(int)
                current_topics = defaultdict(int)
                satisfaction_scores = []
                urgency_scores = []
                
                for session in self.active_sessions.values():
                    current_stages[session.context.stage.value] += 1
                    current_topics[session.context.topic] += 1
                    satisfaction_scores.append(session.context.customer_satisfaction)
                    urgency_scores.append(session.context.urgency_level)
                
                stats["current_stage_distribution"] = dict(current_stages)
                stats["current_topic_distribution"] = dict(current_topics)
                stats["avg_current_satisfaction"] = sum(satisfaction_scores) / len(satisfaction_scores)
                stats["avg_current_urgency"] = sum(urgency_scores) / len(urgency_scores)
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get statistics: {e}")
            return {}
    
    async def cleanup(self) -> None:
        """
        Cleanup conversation manager resources.
        
        Stops background tasks, persists active sessions, and releases resources.
        """
        self.logger.info("Cleaning up conversation manager")
        
        try:
            # Cancel background tasks
            for task in [self.cleanup_task, self.analytics_task]:
                if task and not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            
            # Persist all active sessions
            persist_tasks = []
            for session in self.active_sessions.values():
                if self.enable_persistence:
                    task = asyncio.create_task(self._persist_session(session))
                    persist_tasks.append(task)
            
            if persist_tasks:
                await asyncio.gather(*persist_tasks, return_exceptions=True)
            
            # Clear data structures
            self.active_sessions.clear()
            self.session_timeouts.clear()
            self.customer_profiles.clear()
            self.interaction_patterns.clear()
            
            self.logger.info("Conversation manager cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Conversation manager cleanup failed: {e}")