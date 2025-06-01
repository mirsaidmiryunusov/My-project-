"""
Voice-Bridge Main Application Module

This module serves as the entry point for the voice-bridge microservice, implementing
a revolutionary GPU-accelerated audio processing and advanced NLU system. The application
orchestrates real-time voice conversations between human callers and Gemini AI through
sophisticated audio enhancement, intelligent conversation management, and predictive
response generation.

The voice-bridge represents the technological core of Project GeminiVoiceConnect,
delivering unprecedented audio quality and conversational intelligence through
cutting-edge parallel processing techniques and advanced machine learning models.
"""

import asyncio
import logging
import signal
import sys
from contextlib import asynccontextmanager
from typing import Dict, Any

import structlog
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer
from prometheus_client import make_asgi_app, Counter, Histogram, Gauge
import redis.asyncio as redis

from config import VoiceBridgeConfig
from audio_processor import GPUAudioProcessor
from nlu_extractor import AdvancedNLUExtractor
from conversation_manager import ConversationManager
from gemini_client import GeminiClient
from tts_engine import EdgeTTSEngine
from websocket_manager import WebSocketManager
from security import SecurityManager
from monitoring import MetricsCollector
from gpu_manager import GPUResourceManager


# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Prometheus metrics
ACTIVE_CONNECTIONS = Gauge('voice_bridge_active_connections', 'Number of active WebSocket connections')
AUDIO_PROCESSING_TIME = Histogram('voice_bridge_audio_processing_seconds', 'Time spent processing audio')
NLU_PROCESSING_TIME = Histogram('voice_bridge_nlu_processing_seconds', 'Time spent on NLU processing')
GPU_UTILIZATION = Gauge('voice_bridge_gpu_utilization_percent', 'GPU utilization percentage')
CONVERSATION_COUNTER = Counter('voice_bridge_conversations_total', 'Total number of conversations processed')
ERROR_COUNTER = Counter('voice_bridge_errors_total', 'Total number of errors', ['error_type'])

# Global application state
app_state: Dict[str, Any] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager handling startup and shutdown procedures.
    
    Initializes all core components including GPU resources, Redis connections,
    and monitoring systems. Ensures graceful shutdown with proper resource cleanup.
    """
    logger.info("Starting voice-bridge application initialization")
    
    try:
        # Load configuration
        config = VoiceBridgeConfig()
        app_state['config'] = config
        
        # Initialize GPU resource manager
        gpu_manager = GPUResourceManager(config)
        await gpu_manager.initialize()
        app_state['gpu_manager'] = gpu_manager
        
        # Initialize Redis connection
        redis_client = redis.Redis.from_url(config.redis_url)
        await redis_client.ping()
        app_state['redis'] = redis_client
        
        # Initialize core components
        audio_processor = GPUAudioProcessor(config, gpu_manager)
        await audio_processor.initialize()
        app_state['audio_processor'] = audio_processor
        
        nlu_extractor = AdvancedNLUExtractor(config, gpu_manager)
        await nlu_extractor.initialize()
        app_state['nlu_extractor'] = nlu_extractor
        
        conversation_manager = ConversationManager(config, redis_client)
        await conversation_manager.initialize()
        app_state['conversation_manager'] = conversation_manager
        
        gemini_client = GeminiClient(config)
        await gemini_client.initialize()
        app_state['gemini_client'] = gemini_client
        
        tts_engine = EdgeTTSEngine(config)
        await tts_engine.initialize()
        app_state['tts_engine'] = tts_engine
        
        websocket_manager = WebSocketManager(config)
        app_state['websocket_manager'] = websocket_manager
        
        security_manager = SecurityManager(config)
        app_state['security_manager'] = security_manager
        
        metrics_collector = MetricsCollector(config, gpu_manager)
        await metrics_collector.start()
        app_state['metrics_collector'] = metrics_collector
        
        logger.info("Voice-bridge application initialized successfully")
        
        yield
        
    except Exception as e:
        logger.error("Failed to initialize voice-bridge application", error=str(e))
        raise
    
    finally:
        # Cleanup resources
        logger.info("Shutting down voice-bridge application")
        
        if 'metrics_collector' in app_state:
            await app_state['metrics_collector'].stop()
        
        if 'audio_processor' in app_state:
            await app_state['audio_processor'].cleanup()
        
        if 'nlu_extractor' in app_state:
            await app_state['nlu_extractor'].cleanup()
        
        if 'gpu_manager' in app_state:
            await app_state['gpu_manager'].cleanup()
        
        if 'redis' in app_state:
            await app_state['redis'].close()
        
        logger.info("Voice-bridge application shutdown complete")


# Initialize FastAPI application
app = FastAPI(
    title="Voice-Bridge: GPU-Accelerated Audio Processing & Advanced NLU Core",
    description="Revolutionary real-time voice processing system with GPU acceleration and advanced AI capabilities",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]
)

# Security
security = HTTPBearer()

# Add Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


async def get_current_user(token: str = Depends(security)):
    """
    Dependency for user authentication and authorization.
    
    Args:
        token: JWT token from Authorization header
        
    Returns:
        User information extracted from valid token
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    security_manager = app_state.get('security_manager')
    if not security_manager:
        raise HTTPException(status_code=500, detail="Security manager not initialized")
    
    try:
        user_info = await security_manager.verify_token(token.credentials)
        return user_info
    except Exception as e:
        logger.error("Token verification failed", error=str(e))
        raise HTTPException(status_code=401, detail="Invalid authentication token")


@app.get("/health")
async def health_check():
    """
    Comprehensive health check endpoint providing detailed system status.
    
    Returns:
        Dict containing health status of all system components including
        GPU utilization, Redis connectivity, and service availability.
    """
    try:
        health_status = {
            "status": "healthy",
            "timestamp": asyncio.get_event_loop().time(),
            "components": {}
        }
        
        # Check Redis connectivity
        redis_client = app_state.get('redis')
        if redis_client:
            try:
                await redis_client.ping()
                health_status["components"]["redis"] = "healthy"
            except Exception as e:
                health_status["components"]["redis"] = f"unhealthy: {str(e)}"
                health_status["status"] = "degraded"
        
        # Check GPU status
        gpu_manager = app_state.get('gpu_manager')
        if gpu_manager:
            gpu_status = await gpu_manager.get_health_status()
            health_status["components"]["gpu"] = gpu_status
            if gpu_status.get("status") != "healthy":
                health_status["status"] = "degraded"
        
        # Check audio processor
        audio_processor = app_state.get('audio_processor')
        if audio_processor:
            audio_status = await audio_processor.get_health_status()
            health_status["components"]["audio_processor"] = audio_status
        
        # Check NLU extractor
        nlu_extractor = app_state.get('nlu_extractor')
        if nlu_extractor:
            nlu_status = await nlu_extractor.get_health_status()
            health_status["components"]["nlu_extractor"] = nlu_status
        
        return health_status
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": asyncio.get_event_loop().time()
        }


@app.get("/status")
async def system_status(user=Depends(get_current_user)):
    """
    Detailed system status endpoint providing comprehensive metrics and performance data.
    
    Args:
        user: Authenticated user information
        
    Returns:
        Dict containing detailed system metrics, GPU utilization, active connections,
        and performance statistics.
    """
    try:
        metrics_collector = app_state.get('metrics_collector')
        if not metrics_collector:
            raise HTTPException(status_code=500, detail="Metrics collector not initialized")
        
        status_data = await metrics_collector.get_comprehensive_status()
        
        # Add real-time connection information
        websocket_manager = app_state.get('websocket_manager')
        if websocket_manager:
            status_data["active_connections"] = websocket_manager.get_connection_count()
            status_data["connection_details"] = websocket_manager.get_connection_details()
        
        return status_data
        
    except Exception as e:
        logger.error("Status retrieval failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve system status: {str(e)}")


@app.websocket("/ws/voice/{session_id}")
async def voice_websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    Primary WebSocket endpoint for real-time voice communication.
    
    Handles bidirectional audio streaming, real-time audio processing,
    NLU analysis, and conversation management. Implements sophisticated
    error handling and connection management for production reliability.
    
    Args:
        websocket: WebSocket connection instance
        session_id: Unique session identifier for conversation tracking
    """
    websocket_manager = app_state.get('websocket_manager')
    conversation_manager = app_state.get('conversation_manager')
    audio_processor = app_state.get('audio_processor')
    nlu_extractor = app_state.get('nlu_extractor')
    gemini_client = app_state.get('gemini_client')
    tts_engine = app_state.get('tts_engine')
    
    if not all([websocket_manager, conversation_manager, audio_processor, 
                nlu_extractor, gemini_client, tts_engine]):
        await websocket.close(code=1011, reason="Service components not initialized")
        return
    
    await websocket.accept()
    ACTIVE_CONNECTIONS.inc()
    
    try:
        # Register WebSocket connection
        await websocket_manager.register_connection(session_id, websocket)
        
        # Initialize conversation session
        await conversation_manager.create_session(session_id)
        
        logger.info("Voice WebSocket connection established", session_id=session_id)
        
        # Main message processing loop
        async for message in websocket.iter_bytes():
            try:
                # Process incoming audio data
                with AUDIO_PROCESSING_TIME.time():
                    processed_audio = await audio_processor.process_audio_chunk(
                        message, session_id
                    )
                
                if processed_audio.get('has_speech'):
                    # Send audio to Gemini for transcription
                    transcription = await gemini_client.transcribe_audio(
                        processed_audio['enhanced_audio']
                    )
                    
                    if transcription:
                        # Extract NLU insights
                        with NLU_PROCESSING_TIME.time():
                            nlu_results = await nlu_extractor.extract_insights(
                                transcription, session_id
                            )
                        
                        # Update conversation context
                        await conversation_manager.add_message(
                            session_id, "user", transcription, nlu_results
                        )
                        
                        # Generate AI response
                        ai_response = await gemini_client.generate_response(
                            session_id, transcription, nlu_results
                        )
                        
                        if ai_response:
                            # Convert response to speech
                            audio_response = await tts_engine.synthesize_speech(
                                ai_response, session_id
                            )
                            
                            # Send audio response back to client
                            await websocket.send_bytes(audio_response)
                            
                            # Update conversation context
                            await conversation_manager.add_message(
                                session_id, "assistant", ai_response
                            )
                
                # Send real-time metrics
                await websocket_manager.send_metrics_update(session_id, {
                    "audio_quality": processed_audio.get('quality_score', 0),
                    "sentiment": nlu_results.get('sentiment', 'neutral') if 'nlu_results' in locals() else 'neutral',
                    "processing_latency": processed_audio.get('processing_time', 0)
                })
                
            except Exception as e:
                logger.error("Error processing voice message", 
                           session_id=session_id, error=str(e))
                ERROR_COUNTER.labels(error_type="processing").inc()
                
                await websocket.send_json({
                    "type": "error",
                    "message": "Audio processing error",
                    "timestamp": asyncio.get_event_loop().time()
                })
    
    except WebSocketDisconnect:
        logger.info("Voice WebSocket disconnected", session_id=session_id)
    
    except Exception as e:
        logger.error("Voice WebSocket error", session_id=session_id, error=str(e))
        ERROR_COUNTER.labels(error_type="websocket").inc()
    
    finally:
        # Cleanup connection and session
        ACTIVE_CONNECTIONS.dec()
        await websocket_manager.unregister_connection(session_id)
        await conversation_manager.end_session(session_id)
        CONVERSATION_COUNTER.inc()
        
        logger.info("Voice WebSocket connection closed", session_id=session_id)


@app.post("/api/v1/process-audio")
async def process_audio_file(
    audio_file: bytes,
    session_id: str,
    user=Depends(get_current_user)
):
    """
    REST endpoint for processing uploaded audio files.
    
    Provides an alternative to WebSocket streaming for batch audio processing,
    useful for testing, integration, and scenarios where real-time streaming
    is not required.
    
    Args:
        audio_file: Raw audio data bytes
        session_id: Session identifier for conversation tracking
        user: Authenticated user information
        
    Returns:
        Dict containing transcription, NLU insights, and AI response
    """
    try:
        audio_processor = app_state.get('audio_processor')
        nlu_extractor = app_state.get('nlu_extractor')
        gemini_client = app_state.get('gemini_client')
        
        if not all([audio_processor, nlu_extractor, gemini_client]):
            raise HTTPException(status_code=500, detail="Service components not initialized")
        
        # Process audio file
        with AUDIO_PROCESSING_TIME.time():
            processed_audio = await audio_processor.process_audio_file(
                audio_file, session_id
            )
        
        # Transcribe audio
        transcription = await gemini_client.transcribe_audio(
            processed_audio['enhanced_audio']
        )
        
        if not transcription:
            return {"error": "No speech detected in audio file"}
        
        # Extract NLU insights
        with NLU_PROCESSING_TIME.time():
            nlu_results = await nlu_extractor.extract_insights(
                transcription, session_id
            )
        
        # Generate AI response
        ai_response = await gemini_client.generate_response(
            session_id, transcription, nlu_results
        )
        
        return {
            "transcription": transcription,
            "nlu_insights": nlu_results,
            "ai_response": ai_response,
            "audio_quality": processed_audio.get('quality_score', 0),
            "processing_time": processed_audio.get('processing_time', 0)
        }
        
    except Exception as e:
        logger.error("Audio file processing failed", error=str(e))
        ERROR_COUNTER.labels(error_type="file_processing").inc()
        raise HTTPException(status_code=500, detail=f"Audio processing failed: {str(e)}")


@app.get("/api/v1/conversation/{session_id}")
async def get_conversation_history(
    session_id: str,
    user=Depends(get_current_user)
):
    """
    Retrieve complete conversation history for a session.
    
    Args:
        session_id: Session identifier
        user: Authenticated user information
        
    Returns:
        Dict containing complete conversation history with metadata
    """
    try:
        conversation_manager = app_state.get('conversation_manager')
        if not conversation_manager:
            raise HTTPException(status_code=500, detail="Conversation manager not initialized")
        
        history = await conversation_manager.get_conversation_history(session_id)
        return history
        
    except Exception as e:
        logger.error("Failed to retrieve conversation history", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve conversation: {str(e)}")


def signal_handler(signum, frame):
    """
    Graceful shutdown signal handler.
    
    Ensures proper cleanup of resources when the application receives
    termination signals.
    """
    logger.info("Received shutdown signal", signal=signum)
    sys.exit(0)


if __name__ == "__main__":
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        workers=1,
        log_config=None,
        access_log=False
    )