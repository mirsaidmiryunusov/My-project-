"""
Monitoring and Metrics Collection Module

This module implements comprehensive monitoring and metrics collection for
the voice-bridge microservice, providing real-time performance tracking,
health monitoring, and business intelligence generation. The metrics collector
ensures optimal system performance through continuous monitoring and alerting.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

import psutil
import GPUtil
from prometheus_client import Counter, Histogram, Gauge, generate_latest

from config import VoiceBridgeConfig
from gpu_manager import GPUResourceManager


@dataclass
class SystemMetrics:
    """Data class for system metrics."""
    cpu_usage: float
    memory_usage: float
    gpu_usage: float
    gpu_memory: float
    disk_usage: float
    network_io: Dict[str, float]


class MetricsCollector:
    """
    Comprehensive metrics collection and monitoring system.
    
    Provides real-time monitoring of system performance, GPU utilization,
    and business metrics for optimal system operation and alerting.
    """
    
    def __init__(self, config: VoiceBridgeConfig, gpu_manager: GPUResourceManager):
        """
        Initialize metrics collector.
        
        Args:
            config: Voice-bridge configuration
            gpu_manager: GPU resource manager instance
        """
        self.config = config
        self.gpu_manager = gpu_manager
        self.logger = logging.getLogger(__name__)
        
        # Monitoring configuration
        self.collection_interval = config.health_check_interval
        self.enable_metrics = config.metrics_enabled
        
        # Metrics storage
        self.metrics_history: List[SystemMetrics] = []
        self.performance_data: Dict[str, List[float]] = {}
        
        # Background task
        self.collection_task: Optional[asyncio.Task] = None
        
        # Prometheus metrics
        self.setup_prometheus_metrics()
    
    def setup_prometheus_metrics(self) -> None:
        """Setup Prometheus metrics."""
        self.cpu_usage_gauge = Gauge('voice_bridge_cpu_usage_percent', 'CPU usage percentage')
        self.memory_usage_gauge = Gauge('voice_bridge_memory_usage_percent', 'Memory usage percentage')
        self.gpu_usage_gauge = Gauge('voice_bridge_gpu_usage_percent', 'GPU usage percentage')
        self.active_connections_gauge = Gauge('voice_bridge_active_connections', 'Active WebSocket connections')
        self.processing_time_histogram = Histogram('voice_bridge_processing_seconds', 'Processing time in seconds')
        self.error_counter = Counter('voice_bridge_errors_total', 'Total number of errors')
    
    async def start(self) -> None:
        """Start metrics collection."""
        if self.enable_metrics:
            self.collection_task = asyncio.create_task(self._collect_metrics())
            self.logger.info("Metrics collection started")
    
    async def stop(self) -> None:
        """Stop metrics collection."""
        if self.collection_task:
            self.collection_task.cancel()
            try:
                await self.collection_task
            except asyncio.CancelledError:
                pass
            self.logger.info("Metrics collection stopped")
    
    async def _collect_metrics(self) -> None:
        """Background metrics collection task."""
        while True:
            try:
                # Collect system metrics
                metrics = await self._collect_system_metrics()
                self.metrics_history.append(metrics)
                
                # Update Prometheus metrics
                self._update_prometheus_metrics(metrics)
                
                # Keep only recent history
                if len(self.metrics_history) > 1000:
                    self.metrics_history = self.metrics_history[-500:]
                
                await asyncio.sleep(self.collection_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Metrics collection error: {e}")
                await asyncio.sleep(self.collection_interval)
    
    async def _collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics."""
        try:
            # CPU and Memory
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_usage = (disk.used / disk.total) * 100
            
            # Network I/O
            network = psutil.net_io_counters()
            network_io = {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv
            }
            
            # GPU metrics
            gpu_usage = 0.0
            gpu_memory = 0.0
            
            if self.gpu_manager.cuda_available:
                try:
                    gpus = GPUtil.getGPUs()
                    if gpus and len(gpus) > self.gpu_manager.device_id:
                        gpu = gpus[self.gpu_manager.device_id]
                        gpu_usage = gpu.load * 100
                        gpu_memory = (gpu.memoryUsed / gpu.memoryTotal) * 100
                except Exception as e:
                    self.logger.debug(f"GPU metrics collection failed: {e}")
            
            return SystemMetrics(
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                gpu_usage=gpu_usage,
                gpu_memory=gpu_memory,
                disk_usage=disk_usage,
                network_io=network_io
            )
            
        except Exception as e:
            self.logger.error(f"System metrics collection failed: {e}")
            return SystemMetrics(0, 0, 0, 0, 0, {})
    
    def _update_prometheus_metrics(self, metrics: SystemMetrics) -> None:
        """Update Prometheus metrics."""
        try:
            self.cpu_usage_gauge.set(metrics.cpu_usage)
            self.memory_usage_gauge.set(metrics.memory_usage)
            self.gpu_usage_gauge.set(metrics.gpu_usage)
            
        except Exception as e:
            self.logger.error(f"Prometheus metrics update failed: {e}")
    
    async def get_comprehensive_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        try:
            current_metrics = await self._collect_system_metrics()
            
            # Calculate averages from recent history
            recent_metrics = self.metrics_history[-10:] if self.metrics_history else [current_metrics]
            
            avg_cpu = sum(m.cpu_usage for m in recent_metrics) / len(recent_metrics)
            avg_memory = sum(m.memory_usage for m in recent_metrics) / len(recent_metrics)
            avg_gpu = sum(m.gpu_usage for m in recent_metrics) / len(recent_metrics)
            
            return {
                "current_metrics": {
                    "cpu_usage": current_metrics.cpu_usage,
                    "memory_usage": current_metrics.memory_usage,
                    "gpu_usage": current_metrics.gpu_usage,
                    "gpu_memory": current_metrics.gpu_memory,
                    "disk_usage": current_metrics.disk_usage
                },
                "averages": {
                    "cpu_usage": avg_cpu,
                    "memory_usage": avg_memory,
                    "gpu_usage": avg_gpu
                },
                "system_info": {
                    "cpu_count": psutil.cpu_count(),
                    "total_memory_gb": psutil.virtual_memory().total / (1024**3),
                    "gpu_available": self.gpu_manager.cuda_available
                },
                "collection_enabled": self.enable_metrics,
                "metrics_count": len(self.metrics_history)
            }
            
        except Exception as e:
            self.logger.error(f"Status retrieval failed: {e}")
            return {"error": str(e)}
    
    def get_prometheus_metrics(self) -> str:
        """Get Prometheus metrics in text format."""
        try:
            return generate_latest().decode('utf-8')
        except Exception as e:
            self.logger.error(f"Prometheus metrics generation failed: {e}")
            return ""