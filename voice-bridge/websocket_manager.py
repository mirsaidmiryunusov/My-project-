"""
WebSocket Manager Module

This module implements comprehensive WebSocket connection management for
real-time voice communication, providing connection pooling, message routing,
real-time metrics broadcasting, and robust error handling. The manager
ensures optimal performance and reliability for voice-based interactions.

The WebSocket manager serves as the communication backbone for the voice-bridge
system, orchestrating real-time data exchange between clients and the AI
processing pipeline with minimal latency and maximum reliability.
"""

import asyncio
import logging
import time
import json
from typing import Dict, List, Optional, Any, Set, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from collections import defaultdict, deque

from fastapi import WebSocket, WebSocketDisconnect
import redis.asyncio as redis

from config import VoiceBridgeConfig


class MessageType(Enum):
    """Enumeration of WebSocket message types."""
    AUDIO_DATA = "audio_data"
    CONTROL = "control"
    METRICS = "metrics"
    STATUS = "status"
    ERROR = "error"
    HEARTBEAT = "heartbeat"
    CONFIGURATION = "configuration"


class ConnectionState(Enum):
    """Enumeration of connection states."""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    AUTHENTICATED = "authenticated"
    ACTIVE = "active"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"
    ERROR = "error"


@dataclass
class ConnectionInfo:
    """Data class for WebSocket connection information."""
    session_id: str
    websocket: WebSocket
    state: ConnectionState
    connected_at: float
    last_activity: float
    client_info: Dict[str, Any]
    metrics: Dict[str, Any]


@dataclass
class MessageMetrics:
    """Data class for message metrics."""
    total_messages: int
    messages_by_type: Dict[str, int]
    avg_message_size: float
    last_message_time: float
    error_count: int


class WebSocketManager:
    """
    Advanced WebSocket connection manager for real-time voice communication.
    
    Provides comprehensive connection management including connection pooling,
    message routing, real-time metrics broadcasting, heartbeat monitoring,
    and robust error handling for optimal voice communication performance.
    """
    
    def __init__(self, config: VoiceBridgeConfig):
        """
        Initialize WebSocket manager.
        
        Args:
            config: Voice-bridge configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Connection management
        self.connections: Dict[str, ConnectionInfo] = {}
        self.connection_groups: Dict[str, Set[str]] = defaultdict(set)
        self.message_handlers: Dict[MessageType, List[Callable]] = defaultdict(list)
        
        # Performance tracking
        self.connection_stats = {
            "total_connections": 0,
            "active_connections": 0,
            "peak_connections": 0,
            "total_messages": 0,
            "avg_connection_duration": 0.0,
            "connection_errors": 0
        }
        
        # Message metrics
        self.message_metrics: Dict[str, MessageMetrics] = {}
        self.global_message_stats = {
            "messages_per_second": 0.0,
            "avg_message_size": 0.0,
            "message_queue_size": 0
        }
        
        # Configuration
        self.max_connections = config.max_concurrent_connections
        self.connection_timeout = config.connection_timeout
        self.heartbeat_interval = 30  # seconds
        self.metrics_broadcast_interval = 5  # seconds
        
        # Background tasks
        self.heartbeat_task: Optional[asyncio.Task] = None
        self.metrics_task: Optional[asyncio.Task] = None
        self.cleanup_task: Optional[asyncio.Task] = None
        
        # Message queuing
        self.message_queues: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.broadcast_queue: deque = deque(maxlen=10000)
        
        # Redis integration for scaling
        self.redis_client: Optional[redis.Redis] = None
        self.enable_redis_scaling = False
        
        # Security and rate limiting
        self.rate_limits: Dict[str, Dict[str, Any]] = {}
        self.blocked_connections: Set[str] = set()
        
        # Advanced features
        self.enable_compression = True
        self.enable_metrics_broadcasting = True
        self.enable_connection_grouping = True
    
    async def initialize(self) -> None:
        """
        Initialize WebSocket manager and start background tasks.
        
        Sets up connection monitoring, metrics collection, and
        background maintenance tasks for optimal performance.
        """
        self.logger.info("Initializing WebSocket manager")
        
        try:
            # Start background tasks
            self.heartbeat_task = asyncio.create_task(self._heartbeat_monitor())
            self.metrics_task = asyncio.create_task(self._metrics_broadcaster())
            self.cleanup_task = asyncio.create_task(self._connection_cleanup())
            
            # Initialize Redis if configured
            if hasattr(self.config, 'redis_url') and self.config.redis_url:
                try:
                    self.redis_client = redis.Redis.from_url(str(self.config.redis_url))
                    await self.redis_client.ping()
                    self.enable_redis_scaling = True
                    self.logger.info("Redis scaling enabled")
                except Exception as e:
                    self.logger.warning(f"Redis initialization failed: {e}")
            
            self.logger.info("WebSocket manager initialized successfully")
            
        except Exception as e:
            self.logger.error(f"WebSocket manager initialization failed: {e}")
            raise
    
    async def register_connection(self, session_id: str, websocket: WebSocket,
                                client_info: Optional[Dict[str, Any]] = None) -> bool:
        """
        Register a new WebSocket connection.
        
        Args:
            session_id: Unique session identifier
            websocket: WebSocket connection instance
            client_info: Optional client information
            
        Returns:
            True if registration successful, False otherwise
        """
        try:
            # Check connection limits
            if len(self.connections) >= self.max_connections:
                self.logger.warning("Connection limit reached",
                                  extra={"session_id": session_id,
                                        "current_connections": len(self.connections)})
                return False
            
            # Check if session already exists
            if session_id in self.connections:
                self.logger.warning("Session already exists",
                                  extra={"session_id": session_id})
                await self.unregister_connection(session_id)
            
            # Create connection info
            connection_info = ConnectionInfo(
                session_id=session_id,
                websocket=websocket,
                state=ConnectionState.CONNECTED,
                connected_at=time.time(),
                last_activity=time.time(),
                client_info=client_info or {},
                metrics=self._initialize_connection_metrics()
            )
            
            # Register connection
            self.connections[session_id] = connection_info
            
            # Initialize message metrics
            self.message_metrics[session_id] = MessageMetrics(
                total_messages=0,
                messages_by_type={},
                avg_message_size=0.0,
                last_message_time=time.time(),
                error_count=0
            )
            
            # Update statistics
            self.connection_stats["total_connections"] += 1
            self.connection_stats["active_connections"] = len(self.connections)
            self.connection_stats["peak_connections"] = max(
                self.connection_stats["peak_connections"],
                len(self.connections)
            )
            
            # Add to default group
            if self.enable_connection_grouping:
                self.connection_groups["default"].add(session_id)
            
            # Initialize rate limiting
            self._initialize_rate_limiting(session_id)
            
            # Broadcast connection event
            if self.enable_redis_scaling and self.redis_client:
                await self._broadcast_connection_event("connected", session_id)
            
            self.logger.info("WebSocket connection registered",
                           extra={"session_id": session_id,
                                 "total_connections": len(self.connections)})
            
            return True
            
        except Exception as e:
            self.logger.error(f"Connection registration failed: {e}",
                            extra={"session_id": session_id})
            return False
    
    async def unregister_connection(self, session_id: str) -> None:
        """
        Unregister a WebSocket connection.
        
        Args:
            session_id: Session identifier to unregister
        """
        try:
            if session_id not in self.connections:
                return
            
            connection_info = self.connections[session_id]
            
            # Update connection duration statistics
            connection_duration = time.time() - connection_info.connected_at
            self._update_avg_connection_duration(connection_duration)
            
            # Close WebSocket if still open
            try:
                if connection_info.websocket:
                    await connection_info.websocket.close()
            except Exception as e:
                self.logger.debug(f"WebSocket close error: {e}")
            
            # Remove from connections
            del self.connections[session_id]
            
            # Remove from groups
            for group_sessions in self.connection_groups.values():
                group_sessions.discard(session_id)
            
            # Clean up message metrics
            if session_id in self.message_metrics:
                del self.message_metrics[session_id]
            
            # Clean up message queue
            if session_id in self.message_queues:
                del self.message_queues[session_id]
            
            # Clean up rate limiting
            if session_id in self.rate_limits:
                del self.rate_limits[session_id]
            
            # Update statistics
            self.connection_stats["active_connections"] = len(self.connections)
            
            # Broadcast disconnection event
            if self.enable_redis_scaling and self.redis_client:
                await self._broadcast_connection_event("disconnected", session_id)
            
            self.logger.info("WebSocket connection unregistered",
                           extra={"session_id": session_id,
                                 "duration": connection_duration,
                                 "remaining_connections": len(self.connections)})
            
        except Exception as e:
            self.logger.error(f"Connection unregistration failed: {e}",
                            extra={"session_id": session_id})
    
    def _initialize_connection_metrics(self) -> Dict[str, Any]:
        """
        Initialize metrics for a new connection.
        
        Returns:
            Dict containing initial metrics
        """
        return {
            "bytes_sent": 0,
            "bytes_received": 0,
            "messages_sent": 0,
            "messages_received": 0,
            "errors": 0,
            "last_heartbeat": time.time(),
            "latency_ms": 0.0,
            "quality_score": 1.0
        }
    
    def _initialize_rate_limiting(self, session_id: str) -> None:
        """
        Initialize rate limiting for a connection.
        
        Args:
            session_id: Session identifier
        """
        self.rate_limits[session_id] = {
            "messages_per_minute": 0,
            "bytes_per_minute": 0,
            "last_reset": time.time(),
            "violations": 0
        }
    
    async def send_message(self, session_id: str, message_type: MessageType,
                          data: Any, priority: int = 1) -> bool:
        """
        Send message to a specific WebSocket connection.
        
        Args:
            session_id: Target session identifier
            message_type: Type of message
            data: Message data
            priority: Message priority (higher = more important)
            
        Returns:
            True if message sent successfully, False otherwise
        """
        try:
            if session_id not in self.connections:
                self.logger.warning("Connection not found for message",
                                  extra={"session_id": session_id})
                return False
            
            connection_info = self.connections[session_id]
            
            # Check rate limiting
            if not await self._check_rate_limit(session_id):
                self.logger.warning("Rate limit exceeded",
                                  extra={"session_id": session_id})
                return False
            
            # Prepare message
            message = {
                "type": message_type.value,
                "data": data,
                "timestamp": time.time(),
                "session_id": session_id
            }
            
            # Send message based on type
            if message_type == MessageType.AUDIO_DATA:
                # Send binary data directly
                await connection_info.websocket.send_bytes(data)
            else:
                # Send JSON message
                message_json = json.dumps(message)
                await connection_info.websocket.send_text(message_json)
            
            # Update metrics
            await self._update_send_metrics(session_id, message, len(str(data)))
            
            # Update connection activity
            connection_info.last_activity = time.time()
            
            return True
            
        except WebSocketDisconnect:
            self.logger.info("WebSocket disconnected during send",
                           extra={"session_id": session_id})
            await self.unregister_connection(session_id)
            return False
            
        except Exception as e:
            self.logger.error(f"Message send failed: {e}",
                            extra={"session_id": session_id,
                                  "message_type": message_type.value})
            await self._update_error_metrics(session_id)
            return False
    
    async def broadcast_message(self, message_type: MessageType, data: Any,
                              group: Optional[str] = None,
                              exclude_sessions: Optional[Set[str]] = None) -> int:
        """
        Broadcast message to multiple connections.
        
        Args:
            message_type: Type of message
            data: Message data
            group: Optional group to broadcast to
            exclude_sessions: Optional set of sessions to exclude
            
        Returns:
            Number of successful sends
        """
        try:
            # Determine target sessions
            if group and group in self.connection_groups:
                target_sessions = self.connection_groups[group].copy()
            else:
                target_sessions = set(self.connections.keys())
            
            # Exclude specified sessions
            if exclude_sessions:
                target_sessions -= exclude_sessions
            
            # Send to all target sessions
            successful_sends = 0
            send_tasks = []
            
            for session_id in target_sessions:
                task = asyncio.create_task(
                    self.send_message(session_id, message_type, data)
                )
                send_tasks.append(task)
            
            # Wait for all sends to complete
            results = await asyncio.gather(*send_tasks, return_exceptions=True)
            
            # Count successful sends
            for result in results:
                if result is True:
                    successful_sends += 1
            
            self.logger.debug("Message broadcast completed",
                            extra={"message_type": message_type.value,
                                  "target_count": len(target_sessions),
                                  "successful_sends": successful_sends})
            
            return successful_sends
            
        except Exception as e:
            self.logger.error(f"Message broadcast failed: {e}")
            return 0
    
    async def send_metrics_update(self, session_id: str, metrics: Dict[str, Any]) -> bool:
        """
        Send real-time metrics update to a connection.
        
        Args:
            session_id: Target session identifier
            metrics: Metrics data to send
            
        Returns:
            True if sent successfully, False otherwise
        """
        return await self.send_message(
            session_id,
            MessageType.METRICS,
            metrics,
            priority=2
        )
    
    async def send_status_update(self, session_id: str, status: Dict[str, Any]) -> bool:
        """
        Send status update to a connection.
        
        Args:
            session_id: Target session identifier
            status: Status data to send
            
        Returns:
            True if sent successfully, False otherwise
        """
        return await self.send_message(
            session_id,
            MessageType.STATUS,
            status,
            priority=3
        )
    
    async def add_to_group(self, session_id: str, group: str) -> bool:
        """
        Add connection to a group for targeted broadcasting.
        
        Args:
            session_id: Session identifier
            group: Group name
            
        Returns:
            True if added successfully, False otherwise
        """
        try:
            if session_id in self.connections:
                self.connection_groups[group].add(session_id)
                self.logger.debug("Connection added to group",
                                extra={"session_id": session_id, "group": group})
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to add connection to group: {e}")
            return False
    
    async def remove_from_group(self, session_id: str, group: str) -> bool:
        """
        Remove connection from a group.
        
        Args:
            session_id: Session identifier
            group: Group name
            
        Returns:
            True if removed successfully, False otherwise
        """
        try:
            if group in self.connection_groups:
                self.connection_groups[group].discard(session_id)
                self.logger.debug("Connection removed from group",
                                extra={"session_id": session_id, "group": group})
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to remove connection from group: {e}")
            return False
    
    async def _check_rate_limit(self, session_id: str) -> bool:
        """
        Check if connection is within rate limits.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if within limits, False otherwise
        """
        try:
            if session_id not in self.rate_limits:
                return True
            
            rate_limit = self.rate_limits[session_id]
            current_time = time.time()
            
            # Reset counters if minute has passed
            if current_time - rate_limit["last_reset"] >= 60:
                rate_limit["messages_per_minute"] = 0
                rate_limit["bytes_per_minute"] = 0
                rate_limit["last_reset"] = current_time
            
            # Check limits (configurable thresholds)
            max_messages_per_minute = 1000
            max_bytes_per_minute = 10 * 1024 * 1024  # 10MB
            
            if (rate_limit["messages_per_minute"] >= max_messages_per_minute or
                rate_limit["bytes_per_minute"] >= max_bytes_per_minute):
                rate_limit["violations"] += 1
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Rate limit check failed: {e}")
            return True  # Allow on error
    
    async def _update_send_metrics(self, session_id: str, message: Dict[str, Any],
                                 message_size: int) -> None:
        """
        Update metrics for sent message.
        
        Args:
            session_id: Session identifier
            message: Message data
            message_size: Size of message in bytes
        """
        try:
            # Update connection metrics
            if session_id in self.connections:
                connection_info = self.connections[session_id]
                connection_info.metrics["bytes_sent"] += message_size
                connection_info.metrics["messages_sent"] += 1
            
            # Update message metrics
            if session_id in self.message_metrics:
                metrics = self.message_metrics[session_id]
                metrics.total_messages += 1
                
                message_type = message.get("type", "unknown")
                metrics.messages_by_type[message_type] = (
                    metrics.messages_by_type.get(message_type, 0) + 1
                )
                
                # Update average message size
                total_size = metrics.avg_message_size * (metrics.total_messages - 1) + message_size
                metrics.avg_message_size = total_size / metrics.total_messages
                
                metrics.last_message_time = time.time()
            
            # Update rate limiting
            if session_id in self.rate_limits:
                rate_limit = self.rate_limits[session_id]
                rate_limit["messages_per_minute"] += 1
                rate_limit["bytes_per_minute"] += message_size
            
            # Update global statistics
            self.connection_stats["total_messages"] += 1
            
        except Exception as e:
            self.logger.error(f"Send metrics update failed: {e}")
    
    async def _update_error_metrics(self, session_id: str) -> None:
        """
        Update error metrics for a connection.
        
        Args:
            session_id: Session identifier
        """
        try:
            if session_id in self.connections:
                self.connections[session_id].metrics["errors"] += 1
            
            if session_id in self.message_metrics:
                self.message_metrics[session_id].error_count += 1
            
            self.connection_stats["connection_errors"] += 1
            
        except Exception as e:
            self.logger.error(f"Error metrics update failed: {e}")
    
    def _update_avg_connection_duration(self, duration: float) -> None:
        """
        Update average connection duration statistics.
        
        Args:
            duration: Connection duration in seconds
        """
        total_connections = self.connection_stats["total_connections"]
        if total_connections > 0:
            current_avg = self.connection_stats["avg_connection_duration"]
            self.connection_stats["avg_connection_duration"] = (
                (current_avg * (total_connections - 1) + duration) / total_connections
            )
    
    async def _heartbeat_monitor(self) -> None:
        """
        Background task for monitoring connection health via heartbeats.
        
        Sends periodic heartbeat messages and monitors connection responsiveness
        to detect and handle stale connections.
        """
        while True:
            try:
                current_time = time.time()
                stale_connections = []
                
                for session_id, connection_info in self.connections.items():
                    # Check for stale connections
                    if current_time - connection_info.last_activity > self.connection_timeout:
                        stale_connections.append(session_id)
                        continue
                    
                    # Send heartbeat
                    try:
                        await self.send_message(
                            session_id,
                            MessageType.HEARTBEAT,
                            {"timestamp": current_time},
                            priority=0
                        )
                        connection_info.metrics["last_heartbeat"] = current_time
                        
                    except Exception as e:
                        self.logger.debug(f"Heartbeat failed for {session_id}: {e}")
                        stale_connections.append(session_id)
                
                # Clean up stale connections
                for session_id in stale_connections:
                    self.logger.info("Removing stale connection",
                                   extra={"session_id": session_id})
                    await self.unregister_connection(session_id)
                
                await asyncio.sleep(self.heartbeat_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Heartbeat monitor error: {e}")
                await asyncio.sleep(5)
    
    async def _metrics_broadcaster(self) -> None:
        """
        Background task for broadcasting real-time metrics.
        
        Periodically broadcasts system metrics and performance data
        to connected clients for monitoring and analytics.
        """
        while True:
            try:
                if self.enable_metrics_broadcasting and self.connections:
                    # Collect current metrics
                    metrics_data = {
                        "timestamp": time.time(),
                        "connection_stats": self.connection_stats.copy(),
                        "active_connections": len(self.connections),
                        "message_stats": self.global_message_stats.copy(),
                        "system_health": "healthy"  # Could be enhanced with actual health checks
                    }
                    
                    # Broadcast to interested connections
                    await self.broadcast_message(
                        MessageType.METRICS,
                        metrics_data,
                        group="metrics_subscribers"
                    )
                
                await asyncio.sleep(self.metrics_broadcast_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Metrics broadcaster error: {e}")
                await asyncio.sleep(5)
    
    async def _connection_cleanup(self) -> None:
        """
        Background task for periodic connection cleanup.
        
        Performs maintenance tasks including cache cleanup, metrics
        aggregation, and resource optimization.
        """
        while True:
            try:
                # Clean up old message queues
                current_time = time.time()
                cleanup_threshold = current_time - 3600  # 1 hour
                
                for session_id in list(self.message_queues.keys()):
                    if session_id not in self.connections:
                        del self.message_queues[session_id]
                
                # Clean up old rate limit data
                for session_id in list(self.rate_limits.keys()):
                    if session_id not in self.connections:
                        del self.rate_limits[session_id]
                
                # Update global message statistics
                self._update_global_message_stats()
                
                await asyncio.sleep(300)  # 5 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Connection cleanup error: {e}")
                await asyncio.sleep(60)
    
    def _update_global_message_stats(self) -> None:
        """Update global message statistics."""
        try:
            total_messages = sum(
                metrics.total_messages for metrics in self.message_metrics.values()
            )
            
            if total_messages > 0:
                total_size = sum(
                    metrics.avg_message_size * metrics.total_messages
                    for metrics in self.message_metrics.values()
                )
                self.global_message_stats["avg_message_size"] = total_size / total_messages
            
            # Calculate messages per second (simplified)
            current_time = time.time()
            recent_messages = sum(
                1 for metrics in self.message_metrics.values()
                if current_time - metrics.last_message_time < 60
            )
            self.global_message_stats["messages_per_second"] = recent_messages / 60
            
        except Exception as e:
            self.logger.error(f"Global stats update failed: {e}")
    
    async def _broadcast_connection_event(self, event_type: str, session_id: str) -> None:
        """
        Broadcast connection event via Redis for scaling.
        
        Args:
            event_type: Type of event (connected/disconnected)
            session_id: Session identifier
        """
        try:
            if self.redis_client:
                event_data = {
                    "event_type": event_type,
                    "session_id": session_id,
                    "timestamp": time.time(),
                    "instance_id": "voice-bridge-1"  # Could be dynamic
                }
                
                await self.redis_client.publish(
                    "websocket_events",
                    json.dumps(event_data)
                )
                
        except Exception as e:
            self.logger.error(f"Connection event broadcast failed: {e}")
    
    def get_connection_count(self) -> int:
        """
        Get current number of active connections.
        
        Returns:
            Number of active connections
        """
        return len(self.connections)
    
    def get_connection_details(self) -> List[Dict[str, Any]]:
        """
        Get detailed information about all connections.
        
        Returns:
            List of connection details
        """
        try:
            details = []
            
            for session_id, connection_info in self.connections.items():
                detail = {
                    "session_id": session_id,
                    "state": connection_info.state.value,
                    "connected_at": connection_info.connected_at,
                    "last_activity": connection_info.last_activity,
                    "duration": time.time() - connection_info.connected_at,
                    "client_info": connection_info.client_info,
                    "metrics": connection_info.metrics
                }
                details.append(detail)
            
            return details
            
        except Exception as e:
            self.logger.error(f"Failed to get connection details: {e}")
            return []
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive WebSocket manager statistics.
        
        Returns:
            Dict containing detailed statistics
        """
        try:
            stats = {
                "connection_stats": self.connection_stats.copy(),
                "message_stats": self.global_message_stats.copy(),
                "active_connections": len(self.connections),
                "connection_groups": {
                    group: len(sessions) for group, sessions in self.connection_groups.items()
                },
                "rate_limit_violations": sum(
                    limits.get("violations", 0) for limits in self.rate_limits.values()
                ),
                "blocked_connections": len(self.blocked_connections),
                "message_queue_sizes": {
                    session_id: len(queue) for session_id, queue in self.message_queues.items()
                }
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get statistics: {e}")
            return {}
    
    async def cleanup(self) -> None:
        """
        Cleanup WebSocket manager resources.
        
        Stops background tasks, closes connections, and releases resources.
        """
        self.logger.info("Cleaning up WebSocket manager")
        
        try:
            # Cancel background tasks
            for task in [self.heartbeat_task, self.metrics_task, self.cleanup_task]:
                if task and not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            
            # Close all connections
            close_tasks = []
            for session_id in list(self.connections.keys()):
                task = asyncio.create_task(self.unregister_connection(session_id))
                close_tasks.append(task)
            
            if close_tasks:
                await asyncio.gather(*close_tasks, return_exceptions=True)
            
            # Close Redis connection
            if self.redis_client:
                await self.redis_client.close()
            
            # Clear data structures
            self.connections.clear()
            self.connection_groups.clear()
            self.message_metrics.clear()
            self.message_queues.clear()
            self.rate_limits.clear()
            self.blocked_connections.clear()
            
            self.logger.info("WebSocket manager cleanup completed")
            
        except Exception as e:
            self.logger.error(f"WebSocket manager cleanup failed: {e}")