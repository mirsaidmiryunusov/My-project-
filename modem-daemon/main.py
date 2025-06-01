"""
Modem-Daemon Main Application Module

This module implements the core modem management daemon responsible for controlling
SIM900 GSM modems, handling voice calls, SMS operations, and audio processing.
Each daemon instance manages a single modem with comprehensive AT command handling,
call state management, and integration with the voice-bridge for audio processing.

The modem-daemon serves as the hardware abstraction layer between physical SIM900
modems and the GeminiVoiceConnect platform, providing reliable communication,
fault tolerance, and optimal performance for voice and SMS operations.
"""

import asyncio
import logging
import signal
import sys
import time
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

import structlog
import uvicorn
import serial
import serial.tools.list_ports
import pyaudio
import redis.asyncio as redis
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, Gauge, make_asgi_app
import httpx

from config import ModemDaemonConfig
from at_handler import ATCommandHandler
from audio_interface import AudioInterface
from call_manager import CallManager
from sms_manager import SMSManager
from modem_monitor import ModemMonitor
from registration_service import RegistrationService


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


class ModemState(Enum):
    """Modem operational states."""
    INITIALIZING = "initializing"
    READY = "ready"
    CALLING = "calling"
    IN_CALL = "in_call"
    RECEIVING = "receiving"
    SMS_SENDING = "sms_sending"
    ERROR = "error"
    OFFLINE = "offline"


@dataclass
class ModemStatus:
    """Comprehensive modem status information."""
    modem_id: str
    state: ModemState
    signal_strength: int
    network_registration: str
    battery_level: int
    temperature: float
    active_call: Optional[str]
    last_activity: float
    error_count: int
    uptime: float


# Prometheus metrics
MODEM_STATE_GAUGE = Gauge('modem_daemon_state', 'Current modem state', ['modem_id', 'state'])
SIGNAL_STRENGTH_GAUGE = Gauge('modem_daemon_signal_strength', 'Signal strength', ['modem_id'])
CALL_DURATION_HISTOGRAM = Histogram('modem_daemon_call_duration_seconds', 'Call duration', ['modem_id'])
SMS_SENT_COUNTER = Counter('modem_daemon_sms_sent_total', 'SMS messages sent', ['modem_id'])
ERROR_COUNTER = Counter('modem_daemon_errors_total', 'Total errors', ['modem_id', 'error_type'])
COMMAND_DURATION_HISTOGRAM = Histogram('modem_daemon_command_duration_seconds', 'AT command duration', ['modem_id', 'command'])

# Global application state
app_state: Dict[str, Any] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for modem daemon initialization and cleanup.
    
    Handles complete modem setup including hardware detection, AT command
    initialization, audio interface configuration, and service registration
    with the core platform.
    """
    logger.info("Starting modem daemon initialization")
    
    try:
        # Load configuration
        config = ModemDaemonConfig()
        app_state['config'] = config
        
        logger.info("Modem daemon configuration loaded",
                   modem_id=config.modem_id,
                   device=config.modem_device)
        
        # Initialize Redis connection
        redis_client = redis.Redis.from_url(config.redis_url)
        await redis_client.ping()
        app_state['redis'] = redis_client
        
        # Initialize serial connection to modem
        try:
            serial_conn = serial.Serial(
                port=config.modem_device,
                baudrate=config.modem_baudrate,
                timeout=config.modem_timeout,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS
            )
            app_state['serial'] = serial_conn
            logger.info("Serial connection established", device=config.modem_device)
            
        except serial.SerialException as e:
            logger.error("Failed to establish serial connection", error=str(e))
            raise
        
        # Initialize AT command handler
        at_handler = ATCommandHandler(config, serial_conn)
        await at_handler.initialize()
        app_state['at_handler'] = at_handler
        
        # Initialize audio interface
        audio_interface = AudioInterface(config)
        await audio_interface.initialize()
        app_state['audio_interface'] = audio_interface
        
        # Initialize call manager
        call_manager = CallManager(config, at_handler, audio_interface, redis_client)
        await call_manager.initialize()
        app_state['call_manager'] = call_manager
        
        # Initialize SMS manager
        sms_manager = SMSManager(config, at_handler, redis_client)
        await sms_manager.initialize()
        app_state['sms_manager'] = sms_manager
        
        # Initialize modem monitor
        modem_monitor = ModemMonitor(config, at_handler, redis_client)
        await modem_monitor.start()
        app_state['modem_monitor'] = modem_monitor
        
        # Initialize registration service
        registration_service = RegistrationService(config, redis_client)
        await registration_service.register_modem()
        app_state['registration_service'] = registration_service
        
        # Set initial state
        app_state['modem_state'] = ModemState.READY
        app_state['start_time'] = time.time()
        app_state['error_count'] = 0
        
        logger.info("Modem daemon initialized successfully", modem_id=config.modem_id)
        
        yield
        
    except Exception as e:
        logger.error("Failed to initialize modem daemon", error=str(e))
        raise
    
    finally:
        # Cleanup resources
        logger.info("Shutting down modem daemon")
        
        cleanup_tasks = []
        for component_name in ['registration_service', 'modem_monitor', 'sms_manager',
                              'call_manager', 'audio_interface', 'at_handler']:
            if component_name in app_state:
                component = app_state[component_name]
                if hasattr(component, 'cleanup'):
                    cleanup_tasks.append(component.cleanup())
        
        if cleanup_tasks:
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)
        
        # Close serial connection
        if 'serial' in app_state:
            app_state['serial'].close()
        
        # Close Redis connection
        if 'redis' in app_state:
            await app_state['redis'].close()
        
        logger.info("Modem daemon shutdown complete")


# Initialize FastAPI application
app = FastAPI(
    title=f"Modem-Daemon: SIM900 Hardware Management",
    description="Comprehensive SIM900 modem control with voice and SMS capabilities",
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

# Add Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


@app.get("/health")
async def health_check():
    """
    Comprehensive health check providing detailed modem status.
    
    Returns:
        Dict containing modem health status, signal strength, network
        registration, and operational metrics.
    """
    try:
        config = app_state.get('config')
        at_handler = app_state.get('at_handler')
        modem_monitor = app_state.get('modem_monitor')
        
        if not all([config, at_handler, modem_monitor]):
            return {
                "status": "unhealthy",
                "error": "Core components not initialized",
                "modem_id": config.modem_id if config else "unknown"
            }
        
        # Get current modem status
        status = await modem_monitor.get_comprehensive_status()
        
        # Update Prometheus metrics
        MODEM_STATE_GAUGE.labels(
            modem_id=config.modem_id,
            state=status.state.value
        ).set(1)
        
        SIGNAL_STRENGTH_GAUGE.labels(
            modem_id=config.modem_id
        ).set(status.signal_strength)
        
        return {
            "status": "healthy" if status.state != ModemState.ERROR else "unhealthy",
            "modem_id": status.modem_id,
            "state": status.state.value,
            "signal_strength": status.signal_strength,
            "network_registration": status.network_registration,
            "battery_level": status.battery_level,
            "temperature": status.temperature,
            "active_call": status.active_call,
            "uptime": status.uptime,
            "error_count": status.error_count,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }


@app.get("/status")
async def get_detailed_status():
    """
    Get comprehensive modem status and operational metrics.
    
    Returns:
        Detailed status information including hardware metrics,
        call statistics, and performance data.
    """
    try:
        config = app_state.get('config')
        modem_monitor = app_state.get('modem_monitor')
        call_manager = app_state.get('call_manager')
        sms_manager = app_state.get('sms_manager')
        
        status_data = {
            "modem_info": {
                "modem_id": config.modem_id,
                "device": config.modem_device,
                "state": app_state.get('modem_state', ModemState.OFFLINE).value,
                "uptime": time.time() - app_state.get('start_time', time.time())
            },
            "hardware_status": {},
            "call_statistics": {},
            "sms_statistics": {},
            "performance_metrics": {}
        }
        
        # Get hardware status
        if modem_monitor:
            hardware_status = await modem_monitor.get_hardware_metrics()
            status_data["hardware_status"] = hardware_status
        
        # Get call statistics
        if call_manager:
            call_stats = await call_manager.get_statistics()
            status_data["call_statistics"] = call_stats
        
        # Get SMS statistics
        if sms_manager:
            sms_stats = await sms_manager.get_statistics()
            status_data["sms_statistics"] = sms_stats
        
        return status_data
        
    except Exception as e:
        logger.error("Status retrieval failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to retrieve status: {str(e)}")


@app.post("/api/v1/call/initiate")
async def initiate_call(call_request: dict, background_tasks: BackgroundTasks):
    """
    Initiate an outbound call through the modem.
    
    Args:
        call_request: Call initiation request containing phone number and parameters
        background_tasks: Background task manager
        
    Returns:
        Call initiation result with call ID and status
    """
    try:
        call_manager = app_state.get('call_manager')
        if not call_manager:
            raise HTTPException(status_code=500, detail="Call manager not initialized")
        
        phone_number = call_request.get('phone_number')
        if not phone_number:
            raise HTTPException(status_code=400, detail="Phone number is required")
        
        # Initiate call
        call_id = await call_manager.initiate_call(
            phone_number=phone_number,
            tenant_id=call_request.get('tenant_id'),
            campaign_id=call_request.get('campaign_id'),
            call_data=call_request.get('call_data', {})
        )
        
        # Update state
        app_state['modem_state'] = ModemState.CALLING
        
        logger.info("Call initiated",
                   call_id=call_id,
                   phone_number=phone_number,
                   modem_id=app_state['config'].modem_id)
        
        return {
            "call_id": call_id,
            "status": "initiated",
            "phone_number": phone_number,
            "modem_id": app_state['config'].modem_id
        }
        
    except Exception as e:
        logger.error("Call initiation failed", error=str(e))
        ERROR_COUNTER.labels(
            modem_id=app_state['config'].modem_id,
            error_type="call_initiation"
        ).inc()
        raise HTTPException(status_code=500, detail=f"Call initiation failed: {str(e)}")


@app.post("/api/v1/call/answer")
async def answer_call(call_data: dict):
    """
    Answer an incoming call.
    
    Args:
        call_data: Call answer request data
        
    Returns:
        Call answer result
    """
    try:
        call_manager = app_state.get('call_manager')
        if not call_manager:
            raise HTTPException(status_code=500, detail="Call manager not initialized")
        
        result = await call_manager.answer_call(call_data)
        
        # Update state
        app_state['modem_state'] = ModemState.IN_CALL
        
        logger.info("Call answered", modem_id=app_state['config'].modem_id)
        
        return result
        
    except Exception as e:
        logger.error("Call answer failed", error=str(e))
        ERROR_COUNTER.labels(
            modem_id=app_state['config'].modem_id,
            error_type="call_answer"
        ).inc()
        raise HTTPException(status_code=500, detail=f"Call answer failed: {str(e)}")


@app.post("/api/v1/call/hangup")
async def hangup_call(call_data: dict):
    """
    Terminate an active call.
    
    Args:
        call_data: Call termination request data
        
    Returns:
        Call termination result
    """
    try:
        call_manager = app_state.get('call_manager')
        if not call_manager:
            raise HTTPException(status_code=500, detail="Call manager not initialized")
        
        result = await call_manager.hangup_call(call_data)
        
        # Update state
        app_state['modem_state'] = ModemState.READY
        
        logger.info("Call terminated", modem_id=app_state['config'].modem_id)
        
        return result
        
    except Exception as e:
        logger.error("Call hangup failed", error=str(e))
        ERROR_COUNTER.labels(
            modem_id=app_state['config'].modem_id,
            error_type="call_hangup"
        ).inc()
        raise HTTPException(status_code=500, detail=f"Call hangup failed: {str(e)}")


@app.post("/api/v1/sms/send")
async def send_sms(sms_request: dict):
    """
    Send an SMS message through the modem.
    
    Args:
        sms_request: SMS sending request containing recipient and message
        
    Returns:
        SMS sending result with message ID
    """
    try:
        sms_manager = app_state.get('sms_manager')
        if not sms_manager:
            raise HTTPException(status_code=500, detail="SMS manager not initialized")
        
        phone_number = sms_request.get('phone_number')
        message = sms_request.get('message')
        
        if not phone_number or not message:
            raise HTTPException(status_code=400, detail="Phone number and message are required")
        
        # Send SMS
        message_id = await sms_manager.send_sms(
            phone_number=phone_number,
            message=message,
            tenant_id=sms_request.get('tenant_id'),
            message_data=sms_request.get('message_data', {})
        )
        
        # Update metrics
        SMS_SENT_COUNTER.labels(modem_id=app_state['config'].modem_id).inc()
        
        logger.info("SMS sent",
                   message_id=message_id,
                   phone_number=phone_number,
                   modem_id=app_state['config'].modem_id)
        
        return {
            "message_id": message_id,
            "status": "sent",
            "phone_number": phone_number,
            "modem_id": app_state['config'].modem_id
        }
        
    except Exception as e:
        logger.error("SMS sending failed", error=str(e))
        ERROR_COUNTER.labels(
            modem_id=app_state['config'].modem_id,
            error_type="sms_send"
        ).inc()
        raise HTTPException(status_code=500, detail=f"SMS sending failed: {str(e)}")


@app.get("/api/v1/sms/received")
async def get_received_sms():
    """
    Retrieve received SMS messages.
    
    Returns:
        List of received SMS messages
    """
    try:
        sms_manager = app_state.get('sms_manager')
        if not sms_manager:
            raise HTTPException(status_code=500, detail="SMS manager not initialized")
        
        messages = await sms_manager.get_received_messages()
        return {"messages": messages}
        
    except Exception as e:
        logger.error("SMS retrieval failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"SMS retrieval failed: {str(e)}")


@app.post("/api/v1/modem/reset")
async def reset_modem():
    """
    Reset the modem to recover from error states.
    
    Returns:
        Reset operation result
    """
    try:
        at_handler = app_state.get('at_handler')
        if not at_handler:
            raise HTTPException(status_code=500, detail="AT handler not initialized")
        
        # Perform modem reset
        result = await at_handler.reset_modem()
        
        # Update state
        app_state['modem_state'] = ModemState.READY
        app_state['error_count'] = 0
        
        logger.info("Modem reset completed", modem_id=app_state['config'].modem_id)
        
        return {
            "status": "reset_completed",
            "modem_id": app_state['config'].modem_id,
            "result": result
        }
        
    except Exception as e:
        logger.error("Modem reset failed", error=str(e))
        ERROR_COUNTER.labels(
            modem_id=app_state['config'].modem_id,
            error_type="modem_reset"
        ).inc()
        raise HTTPException(status_code=500, detail=f"Modem reset failed: {str(e)}")


def signal_handler(signum, frame):
    """
    Graceful shutdown signal handler.
    
    Ensures proper cleanup of modem resources and connections
    when the daemon receives termination signals.
    """
    logger.info("Received shutdown signal", signal=signum)
    sys.exit(0)


if __name__ == "__main__":
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start the modem daemon
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8002,
        reload=False,
        workers=1,
        log_config=None,
        access_log=False
    )