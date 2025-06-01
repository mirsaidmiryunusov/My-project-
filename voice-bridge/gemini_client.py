"""
Gemini API Client Module

This module implements comprehensive integration with Google's Gemini API for
advanced speech-to-text, text generation, and multimodal AI capabilities.
The client provides intelligent conversation management, context preservation,
and optimized API usage for real-time voice processing applications.

The Gemini client serves as the AI brain of the voice-bridge system,
orchestrating sophisticated conversations while maintaining context
and delivering human-like responses with minimal latency.
"""

import asyncio
import logging
import time
import io
import json
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum

import httpx
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import numpy as np

from config import VoiceBridgeConfig
from nlu_extractor import NLUResults


class ConversationRole(Enum):
    """Enumeration of conversation roles."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class ConversationMessage:
    """Data class for conversation messages."""
    role: ConversationRole
    content: str
    timestamp: float
    metadata: Dict[str, Any]


@dataclass
class GeminiResponse:
    """Data class for Gemini API responses."""
    text: str
    confidence: float
    finish_reason: str
    usage_metadata: Dict[str, Any]
    safety_ratings: List[Dict[str, Any]]
    processing_time: float


class GeminiClient:
    """
    Advanced Gemini API client for conversational AI.
    
    Provides comprehensive integration with Google's Gemini API including
    speech-to-text, text generation, conversation management, and context
    preservation. Implements intelligent prompt engineering and response
    optimization for voice-based interactions.
    """
    
    def __init__(self, config: VoiceBridgeConfig):
        """
        Initialize Gemini API client.
        
        Args:
            config: Voice-bridge configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # API configuration
        self.api_key = config.gemini_api_key.get_secret_value()
        self.model_name = config.gemini_model
        self.max_tokens = config.gemini_max_tokens
        self.temperature = config.gemini_temperature
        self.timeout = config.gemini_timeout
        self.max_retries = config.gemini_max_retries
        
        # Client instances
        self.client = None
        self.model = None
        self.chat_sessions: Dict[str, Any] = {}
        
        # Conversation management
        self.conversation_histories: Dict[str, List[ConversationMessage]] = {}
        self.system_prompts: Dict[str, str] = {}
        
        # Performance tracking
        self.api_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "avg_response_time": 0.0,
            "total_tokens_used": 0
        }
        
        # Safety settings
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }
        
        # Advanced features
        self.enable_context_optimization = True
        self.enable_response_caching = True
        self.response_cache: Dict[str, GeminiResponse] = {}
        
        # Prompt templates
        self.prompt_templates = self._initialize_prompt_templates()
    
    async def initialize(self) -> None:
        """
        Initialize Gemini client and configure API access.
        
        Sets up API authentication, model configuration, and
        initializes conversation management systems.
        """
        self.logger.info("Initializing Gemini API client")
        
        try:
            if not self.api_key:
                raise ValueError("Gemini API key not provided")
            
            # Configure the API
            genai.configure(api_key=self.api_key)
            
            # Initialize the model
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                safety_settings=self.safety_settings
            )
            
            # Test API connectivity
            await self._test_api_connectivity()
            
            self.logger.info("Gemini API client initialized successfully",
                           extra={"model": self.model_name})
            
        except Exception as e:
            self.logger.error(f"Gemini client initialization failed: {e}")
            raise
    
    def _initialize_prompt_templates(self) -> Dict[str, str]:
        """
        Initialize prompt templates for different conversation scenarios.
        
        Returns:
            Dict containing prompt templates
        """
        return {
            "system_base": """You are an advanced AI assistant for a professional call center. 
            You provide helpful, accurate, and empathetic responses to customer inquiries. 
            Always maintain a professional tone while being friendly and understanding.
            
            Key guidelines:
            - Be concise but thorough in your responses
            - Show empathy for customer concerns
            - Provide actionable solutions when possible
            - Ask clarifying questions when needed
            - Maintain conversation context
            - Be proactive in offering assistance""",
            
            "customer_service": """You are a customer service representative helping customers 
            with their inquiries, complaints, and requests. Focus on:
            - Understanding the customer's issue completely
            - Providing clear solutions or next steps
            - Showing empathy and understanding
            - Escalating when necessary
            - Following up on unresolved issues""",
            
            "sales_support": """You are a sales support specialist helping customers with 
            product information, pricing, and purchase decisions. Focus on:
            - Understanding customer needs and requirements
            - Providing relevant product information
            - Explaining features and benefits clearly
            - Addressing concerns and objections
            - Guiding customers through the purchase process""",
            
            "technical_support": """You are a technical support specialist helping customers 
            with technical issues and troubleshooting. Focus on:
            - Diagnosing technical problems systematically
            - Providing step-by-step solutions
            - Using clear, non-technical language
            - Verifying solutions work for the customer
            - Documenting issues for future reference""",
            
            "appointment_booking": """You are an appointment booking specialist helping 
            customers schedule appointments and manage their calendar. Focus on:
            - Understanding scheduling preferences and constraints
            - Offering available time slots
            - Confirming appointment details
            - Handling rescheduling and cancellations
            - Sending confirmation and reminders"""
        }
    
    async def _test_api_connectivity(self) -> None:
        """
        Test API connectivity with a simple request.
        
        Raises:
            Exception: If API connectivity test fails
        """
        try:
            test_response = await self._generate_content_async(
                "Hello, this is a connectivity test.",
                max_tokens=10
            )
            
            if not test_response:
                raise Exception("API connectivity test failed - no response")
            
            self.logger.info("Gemini API connectivity test successful")
            
        except Exception as e:
            self.logger.error(f"API connectivity test failed: {e}")
            raise
    
    async def transcribe_audio(self, audio_data: np.ndarray) -> Optional[str]:
        """
        Transcribe audio data using Gemini's speech-to-text capabilities.
        
        Args:
            audio_data: Audio data as numpy array
            
        Returns:
            Transcribed text or None if transcription fails
        """
        start_time = time.time()
        
        try:
            # Convert numpy array to audio file format
            audio_bytes = await self._convert_audio_for_api(audio_data)
            
            # Create audio part for Gemini
            audio_part = {
                "mime_type": "audio/wav",
                "data": audio_bytes
            }
            
            # Generate transcription
            response = await self._generate_content_async(
                [
                    "Please transcribe the following audio accurately. "
                    "Only return the transcribed text without any additional commentary.",
                    audio_part
                ]
            )
            
            if response and response.text:
                transcription = response.text.strip()
                
                # Update statistics
                self.api_stats["total_requests"] += 1
                self.api_stats["successful_requests"] += 1
                
                processing_time = time.time() - start_time
                self._update_avg_response_time(processing_time)
                
                self.logger.debug("Audio transcription successful",
                                extra={"transcription_length": len(transcription),
                                      "processing_time": processing_time})
                
                return transcription
            
            return None
            
        except Exception as e:
            self.logger.error(f"Audio transcription failed: {e}")
            self.api_stats["total_requests"] += 1
            self.api_stats["failed_requests"] += 1
            return None
    
    async def _convert_audio_for_api(self, audio_data: np.ndarray) -> bytes:
        """
        Convert audio data to format suitable for Gemini API.
        
        Args:
            audio_data: Audio data as numpy array
            
        Returns:
            Audio data as bytes in WAV format
        """
        try:
            import soundfile as sf
            
            # Create in-memory WAV file
            audio_buffer = io.BytesIO()
            
            # Ensure audio is in correct format
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            
            # Normalize audio if needed
            if np.max(np.abs(audio_data)) > 1.0:
                audio_data = audio_data / np.max(np.abs(audio_data))
            
            # Write to buffer
            sf.write(audio_buffer, audio_data, self.config.audio_sample_rate, format='WAV')
            
            return audio_buffer.getvalue()
            
        except Exception as e:
            self.logger.error(f"Audio conversion failed: {e}")
            raise
    
    async def generate_response(self, session_id: str, user_message: str, 
                              nlu_results: Optional[NLUResults] = None) -> Optional[str]:
        """
        Generate AI response for user message with context awareness.
        
        Args:
            session_id: Session identifier for context tracking
            user_message: User's message text
            nlu_results: Optional NLU analysis results
            
        Returns:
            Generated response text or None if generation fails
        """
        start_time = time.time()
        
        try:
            # Get or create conversation history
            if session_id not in self.conversation_histories:
                self.conversation_histories[session_id] = []
                await self._initialize_conversation_context(session_id, nlu_results)
            
            # Add user message to history
            user_msg = ConversationMessage(
                role=ConversationRole.USER,
                content=user_message,
                timestamp=time.time(),
                metadata={"nlu_results": nlu_results.metadata if nlu_results else {}}
            )
            self.conversation_histories[session_id].append(user_msg)
            
            # Build conversation prompt
            prompt = await self._build_conversation_prompt(session_id, nlu_results)
            
            # Check response cache
            cache_key = self._generate_cache_key(prompt)
            if self.enable_response_caching and cache_key in self.response_cache:
                cached_response = self.response_cache[cache_key]
                self.logger.debug("Using cached response", extra={"session_id": session_id})
                return cached_response.text
            
            # Generate response
            response = await self._generate_content_async(prompt)
            
            if response and response.text:
                response_text = response.text.strip()
                
                # Add assistant response to history
                assistant_msg = ConversationMessage(
                    role=ConversationRole.ASSISTANT,
                    content=response_text,
                    timestamp=time.time(),
                    metadata={"gemini_response": response}
                )
                self.conversation_histories[session_id].append(assistant_msg)
                
                # Cache response
                if self.enable_response_caching:
                    self.response_cache[cache_key] = response
                
                # Update statistics
                self.api_stats["total_requests"] += 1
                self.api_stats["successful_requests"] += 1
                if hasattr(response, 'usage_metadata'):
                    self.api_stats["total_tokens_used"] += response.usage_metadata.get("total_token_count", 0)
                
                processing_time = time.time() - start_time
                self._update_avg_response_time(processing_time)
                
                self.logger.debug("Response generation successful",
                                extra={"session_id": session_id,
                                      "response_length": len(response_text),
                                      "processing_time": processing_time})
                
                return response_text
            
            return None
            
        except Exception as e:
            self.logger.error(f"Response generation failed: {e}",
                            extra={"session_id": session_id})
            self.api_stats["total_requests"] += 1
            self.api_stats["failed_requests"] += 1
            return None
    
    async def _initialize_conversation_context(self, session_id: str, 
                                             nlu_results: Optional[NLUResults] = None) -> None:
        """
        Initialize conversation context for a new session.
        
        Args:
            session_id: Session identifier
            nlu_results: Optional NLU analysis results for context
        """
        try:
            # Determine appropriate system prompt based on context
            if nlu_results:
                if nlu_results.context.topic == "support":
                    system_prompt = self.prompt_templates["technical_support"]
                elif nlu_results.context.topic == "sales":
                    system_prompt = self.prompt_templates["sales_support"]
                elif nlu_results.context.topic == "booking":
                    system_prompt = self.prompt_templates["appointment_booking"]
                else:
                    system_prompt = self.prompt_templates["customer_service"]
            else:
                system_prompt = self.prompt_templates["system_base"]
            
            # Store system prompt for session
            self.system_prompts[session_id] = system_prompt
            
            # Add system message to conversation history
            system_msg = ConversationMessage(
                role=ConversationRole.SYSTEM,
                content=system_prompt,
                timestamp=time.time(),
                metadata={"initialization": True}
            )
            self.conversation_histories[session_id].append(system_msg)
            
            self.logger.debug("Conversation context initialized",
                            extra={"session_id": session_id})
            
        except Exception as e:
            self.logger.error(f"Context initialization failed: {e}")
    
    async def _build_conversation_prompt(self, session_id: str, 
                                       nlu_results: Optional[NLUResults] = None) -> str:
        """
        Build comprehensive conversation prompt with context.
        
        Args:
            session_id: Session identifier
            nlu_results: Optional NLU analysis results
            
        Returns:
            Formatted conversation prompt
        """
        try:
            conversation_history = self.conversation_histories.get(session_id, [])
            
            # Start with system prompt
            prompt_parts = []
            
            # Add system context
            system_prompt = self.system_prompts.get(session_id, self.prompt_templates["system_base"])
            prompt_parts.append(f"System: {system_prompt}")
            
            # Add NLU context if available
            if nlu_results:
                context_info = self._format_nlu_context(nlu_results)
                prompt_parts.append(f"Context Analysis: {context_info}")
            
            # Add conversation history (last 10 messages to manage token usage)
            recent_history = conversation_history[-10:] if len(conversation_history) > 10 else conversation_history
            
            for msg in recent_history:
                if msg.role != ConversationRole.SYSTEM:  # Skip system messages in history
                    role_name = "Human" if msg.role == ConversationRole.USER else "Assistant"
                    prompt_parts.append(f"{role_name}: {msg.content}")
            
            # Add current context optimization
            if self.enable_context_optimization:
                optimization_context = await self._generate_context_optimization(session_id, nlu_results)
                if optimization_context:
                    prompt_parts.append(f"Optimization Context: {optimization_context}")
            
            # Add response guidelines
            prompt_parts.append(
                "Assistant: Please provide a helpful, empathetic, and professional response. "
                "Consider the conversation context and the customer's emotional state. "
                "Be concise but thorough, and ask clarifying questions if needed."
            )
            
            return "\n\n".join(prompt_parts)
            
        except Exception as e:
            self.logger.error(f"Prompt building failed: {e}")
            return "Please provide a helpful response to the customer's inquiry."
    
    def _format_nlu_context(self, nlu_results: NLUResults) -> str:
        """
        Format NLU results into context information.
        
        Args:
            nlu_results: NLU analysis results
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        # Intent information
        context_parts.append(f"Intent: {nlu_results.intent.intent.value} (confidence: {nlu_results.intent.confidence:.2f})")
        
        # Sentiment information
        context_parts.append(f"Sentiment: {nlu_results.sentiment.sentiment.value} (polarity: {nlu_results.sentiment.polarity:.2f})")
        
        # Emotion information
        context_parts.append(f"Emotion: {nlu_results.sentiment.emotion.value} (confidence: {nlu_results.sentiment.emotion_confidence:.2f})")
        
        # Topic and urgency
        context_parts.append(f"Topic: {nlu_results.context.topic}")
        context_parts.append(f"Urgency Level: {nlu_results.context.urgency_level:.2f}")
        context_parts.append(f"Customer Satisfaction: {nlu_results.context.customer_satisfaction:.2f}")
        
        # Key entities
        if nlu_results.entities:
            entities_str = ", ".join([f"{e.label}: {e.text}" for e in nlu_results.entities[:3]])
            context_parts.append(f"Key Entities: {entities_str}")
        
        # Unresolved issues
        if nlu_results.context.unresolved_issues:
            issues_str = "; ".join(nlu_results.context.unresolved_issues[:2])
            context_parts.append(f"Unresolved Issues: {issues_str}")
        
        return " | ".join(context_parts)
    
    async def _generate_context_optimization(self, session_id: str, 
                                           nlu_results: Optional[NLUResults] = None) -> Optional[str]:
        """
        Generate context optimization suggestions.
        
        Args:
            session_id: Session identifier
            nlu_results: Optional NLU analysis results
            
        Returns:
            Context optimization string or None
        """
        try:
            conversation_history = self.conversation_histories.get(session_id, [])
            
            if len(conversation_history) < 2:
                return None
            
            optimization_hints = []
            
            # Analyze conversation patterns
            user_messages = [msg for msg in conversation_history if msg.role == ConversationRole.USER]
            
            if len(user_messages) >= 2:
                # Check for repeated issues
                recent_topics = []
                for msg in user_messages[-3:]:
                    if hasattr(msg.metadata.get('nlu_results', {}), 'context'):
                        recent_topics.append(msg.metadata['nlu_results']['context']['topic'])
                
                if len(set(recent_topics)) == 1 and len(recent_topics) > 1:
                    optimization_hints.append("Customer has repeated the same topic - may need escalation or different approach")
            
            # Check sentiment trends
            if nlu_results and len(user_messages) >= 2:
                if nlu_results.sentiment.polarity < -0.3:
                    optimization_hints.append("Customer sentiment is negative - prioritize empathy and solution-focused responses")
                elif nlu_results.context.urgency_level > 0.7:
                    optimization_hints.append("High urgency detected - provide immediate assistance and clear next steps")
            
            return " | ".join(optimization_hints) if optimization_hints else None
            
        except Exception as e:
            self.logger.error(f"Context optimization generation failed: {e}")
            return None
    
    async def _generate_content_async(self, prompt: Union[str, List], 
                                    max_tokens: Optional[int] = None) -> Optional[GeminiResponse]:
        """
        Generate content using Gemini API with async support.
        
        Args:
            prompt: Text prompt or multimodal content list
            max_tokens: Optional token limit override
            
        Returns:
            GeminiResponse or None if generation fails
        """
        start_time = time.time()
        
        try:
            # Configure generation parameters
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=max_tokens or self.max_tokens,
                temperature=self.temperature,
                top_p=0.8,
                top_k=40
            )
            
            # Generate content with retry logic
            for attempt in range(self.max_retries):
                try:
                    response = await asyncio.wait_for(
                        asyncio.to_thread(
                            self.model.generate_content,
                            prompt,
                            generation_config=generation_config,
                            safety_settings=self.safety_settings
                        ),
                        timeout=self.timeout
                    )
                    
                    if response and response.text:
                        # Create response object
                        gemini_response = GeminiResponse(
                            text=response.text,
                            confidence=1.0,  # Gemini doesn't provide confidence scores
                            finish_reason=getattr(response, 'finish_reason', 'STOP'),
                            usage_metadata=getattr(response, 'usage_metadata', {}),
                            safety_ratings=getattr(response, 'safety_ratings', []),
                            processing_time=time.time() - start_time
                        )
                        
                        return gemini_response
                    
                except asyncio.TimeoutError:
                    self.logger.warning(f"Gemini API timeout on attempt {attempt + 1}")
                    if attempt == self.max_retries - 1:
                        raise
                    await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff
                
                except Exception as e:
                    self.logger.warning(f"Gemini API error on attempt {attempt + 1}: {e}")
                    if attempt == self.max_retries - 1:
                        raise
                    await asyncio.sleep(1 * (attempt + 1))
            
            return None
            
        except Exception as e:
            self.logger.error(f"Content generation failed: {e}")
            return None
    
    def _generate_cache_key(self, prompt: str) -> str:
        """
        Generate cache key for response caching.
        
        Args:
            prompt: Input prompt
            
        Returns:
            Cache key string
        """
        import hashlib
        
        # Create hash of prompt for caching
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
        return f"{self.model_name}_{prompt_hash}_{self.temperature}"
    
    def _update_avg_response_time(self, response_time: float) -> None:
        """
        Update average response time statistics.
        
        Args:
            response_time: Response time in seconds
        """
        total_requests = self.api_stats["successful_requests"]
        if total_requests > 0:
            current_avg = self.api_stats["avg_response_time"]
            self.api_stats["avg_response_time"] = (
                (current_avg * (total_requests - 1) + response_time) / total_requests
            )
    
    async def get_conversation_history(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get conversation history for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of conversation messages
        """
        try:
            history = self.conversation_histories.get(session_id, [])
            
            return [
                {
                    "role": msg.role.value,
                    "content": msg.content,
                    "timestamp": msg.timestamp,
                    "metadata": msg.metadata
                }
                for msg in history
                if msg.role != ConversationRole.SYSTEM  # Exclude system messages
            ]
            
        except Exception as e:
            self.logger.error(f"Failed to get conversation history: {e}")
            return []
    
    async def clear_conversation_history(self, session_id: str) -> None:
        """
        Clear conversation history for a session.
        
        Args:
            session_id: Session identifier
        """
        try:
            if session_id in self.conversation_histories:
                del self.conversation_histories[session_id]
            
            if session_id in self.system_prompts:
                del self.system_prompts[session_id]
            
            self.logger.debug("Conversation history cleared",
                            extra={"session_id": session_id})
            
        except Exception as e:
            self.logger.error(f"Failed to clear conversation history: {e}")
    
    async def get_api_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive API usage statistics.
        
        Returns:
            Dict containing API statistics
        """
        try:
            stats = self.api_stats.copy()
            
            # Calculate success rate
            if stats["total_requests"] > 0:
                stats["success_rate"] = stats["successful_requests"] / stats["total_requests"]
            else:
                stats["success_rate"] = 0.0
            
            # Add session information
            stats["active_sessions"] = len(self.conversation_histories)
            stats["cached_responses"] = len(self.response_cache)
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get API statistics: {e}")
            return {}
    
    async def get_health_status(self) -> Dict[str, Any]:
        """
        Get Gemini client health status.
        
        Returns:
            Dict containing health status and performance metrics
        """
        try:
            status = {
                "status": "healthy",
                "model": self.model_name,
                "api_configured": bool(self.api_key),
                "model_initialized": self.model is not None,
                "api_statistics": await self.get_api_statistics(),
                "configuration": {
                    "max_tokens": self.max_tokens,
                    "temperature": self.temperature,
                    "timeout": self.timeout,
                    "max_retries": self.max_retries
                }
            }
            
            # Check for issues
            api_stats = status["api_statistics"]
            if api_stats.get("total_requests", 0) > 0:
                success_rate = api_stats.get("success_rate", 0)
                if success_rate < 0.8:  # Less than 80% success rate
                    status["status"] = "degraded"
                    status["issues"] = [f"Low API success rate: {success_rate:.2%}"]
                
                avg_response_time = api_stats.get("avg_response_time", 0)
                if avg_response_time > 5.0:  # More than 5 seconds average
                    if status["status"] == "healthy":
                        status["status"] = "degraded"
                        status["issues"] = []
                    status["issues"].append(f"High average response time: {avg_response_time:.2f}s")
            
            return status
            
        except Exception as e:
            self.logger.error(f"Health status check failed: {e}")
            return {"status": "error", "error": str(e)}
    
    async def cleanup(self) -> None:
        """
        Cleanup Gemini client resources.
        
        Clears conversation histories, caches, and releases resources.
        """
        self.logger.info("Cleaning up Gemini client")
        
        try:
            # Clear conversation histories
            self.conversation_histories.clear()
            self.system_prompts.clear()
            
            # Clear response cache
            self.response_cache.clear()
            
            # Clear chat sessions
            self.chat_sessions.clear()
            
            self.logger.info("Gemini client cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Gemini client cleanup failed: {e}")