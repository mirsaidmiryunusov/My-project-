"""
GPU Resource Manager Module

This module implements comprehensive GPU resource management for the voice-bridge
microservice, providing intelligent allocation, monitoring, and optimization of
GPU resources for audio processing and machine learning tasks. The manager
ensures optimal utilization while preventing resource conflicts and memory leaks.

The GPU manager serves as the central authority for all GPU operations,
implementing sophisticated load balancing, memory management, and performance
optimization strategies to maximize the efficiency of GPU-accelerated processing.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import Enum

import cupy as cp
import GPUtil
import psutil
import torch
import numpy as np
from concurrent.futures import ThreadPoolExecutor

from config import VoiceBridgeConfig


class GPUTaskType(Enum):
    """Enumeration of GPU task types for resource allocation."""
    AUDIO_PROCESSING = "audio_processing"
    NLU_INFERENCE = "nlu_inference"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    SPEECH_SYNTHESIS = "speech_synthesis"
    GENERAL_COMPUTE = "general_compute"


@dataclass
class GPUResourceAllocation:
    """Data class representing GPU resource allocation."""
    task_id: str
    task_type: GPUTaskType
    memory_mb: int
    compute_units: int
    priority: int
    allocated_at: float
    estimated_duration: float


@dataclass
class GPUPerformanceMetrics:
    """Data class for GPU performance metrics."""
    utilization_percent: float
    memory_used_mb: int
    memory_total_mb: int
    memory_free_mb: int
    temperature_celsius: float
    power_draw_watts: float
    compute_capability: Tuple[int, int]
    driver_version: str
    cuda_version: str


class GPUResourceManager:
    """
    Comprehensive GPU resource management system.
    
    Provides intelligent allocation, monitoring, and optimization of GPU resources
    for various computational tasks including audio processing, machine learning
    inference, and real-time analytics. Implements sophisticated scheduling
    algorithms and memory management strategies.
    """
    
    def __init__(self, config: VoiceBridgeConfig):
        """
        Initialize GPU resource manager.
        
        Args:
            config: Voice-bridge configuration instance
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # GPU configuration
        self.gpu_enabled = config.gpu_enabled
        self.device_id = config.gpu_device_id
        self.memory_fraction = config.gpu_memory_fraction
        self.allow_growth = config.gpu_allow_growth
        self.fallback_to_cpu = config.gpu_fallback_to_cpu
        
        # Resource tracking
        self.active_allocations: Dict[str, GPUResourceAllocation] = {}
        self.allocation_history: List[GPUResourceAllocation] = []
        self.performance_history: List[GPUPerformanceMetrics] = []
        
        # Synchronization
        self._allocation_lock = asyncio.Lock()
        self._monitoring_task: Optional[asyncio.Task] = None
        
        # Thread pool for blocking operations
        self._executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="gpu_manager")
        
        # GPU device information
        self.device_info: Optional[Dict[str, Any]] = None
        self.cuda_available = False
        self.cupy_available = False
        
        # Performance optimization
        self.memory_pool = None
        self.stream_pool: List[cp.cuda.Stream] = []
        self.optimization_enabled = config.experimental_gpu_optimization
    
    async def initialize(self) -> None:
        """
        Initialize GPU resources and start monitoring.
        
        Performs GPU detection, memory pool initialization, and starts
        background monitoring tasks for performance tracking and optimization.
        """
        self.logger.info("Initializing GPU resource manager")
        
        try:
            # Check GPU availability
            await self._detect_gpu_capabilities()
            
            if self.gpu_enabled and self.cuda_available:
                # Initialize CUDA context
                await self._initialize_cuda_context()
                
                # Setup memory management
                await self._setup_memory_management()
                
                # Initialize stream pool for concurrent operations
                await self._initialize_stream_pool()
                
                # Start performance monitoring
                self._monitoring_task = asyncio.create_task(self._monitor_performance())
                
                self.logger.info("GPU resource manager initialized successfully",
                               extra={"device_id": self.device_id,
                                     "memory_fraction": self.memory_fraction})
            else:
                self.logger.warning("GPU not available, falling back to CPU processing")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize GPU resource manager: {e}")
            if not self.fallback_to_cpu:
                raise
    
    async def _detect_gpu_capabilities(self) -> None:
        """
        Detect and analyze GPU capabilities.
        
        Performs comprehensive GPU detection including CUDA availability,
        device specifications, and compatibility assessment.
        """
        try:
            # Check CUDA availability
            self.cuda_available = torch.cuda.is_available()
            
            if self.cuda_available:
                # Get device information
                device_count = torch.cuda.device_count()
                
                if self.device_id >= device_count:
                    raise ValueError(f"GPU device {self.device_id} not available. "
                                   f"Only {device_count} devices found.")
                
                # Get detailed device information
                device_props = torch.cuda.get_device_properties(self.device_id)
                
                self.device_info = {
                    "name": device_props.name,
                    "compute_capability": (device_props.major, device_props.minor),
                    "total_memory": device_props.total_memory,
                    "multiprocessor_count": device_props.multi_processor_count,
                    "max_threads_per_multiprocessor": device_props.max_threads_per_multiprocessor,
                    "max_shared_memory_per_multiprocessor": device_props.max_shared_memory_per_multiprocessor
                }
                
                # Check CuPy availability
                try:
                    cp.cuda.runtime.getDeviceCount()
                    self.cupy_available = True
                except Exception:
                    self.cupy_available = False
                    self.logger.warning("CuPy not available, some GPU features disabled")
                
                self.logger.info("GPU capabilities detected",
                               extra={"device_info": self.device_info,
                                     "cupy_available": self.cupy_available})
            else:
                self.logger.warning("CUDA not available on this system")
                
        except Exception as e:
            self.logger.error(f"GPU capability detection failed: {e}")
            self.cuda_available = False
            self.cupy_available = False
    
    async def _initialize_cuda_context(self) -> None:
        """
        Initialize CUDA context with optimal settings.
        
        Sets up CUDA context with memory management, device selection,
        and performance optimization configurations.
        """
        try:
            # Set device
            torch.cuda.set_device(self.device_id)
            
            if self.cupy_available:
                cp.cuda.Device(self.device_id).use()
            
            # Initialize context with a dummy operation
            dummy_tensor = torch.zeros(1, device=f'cuda:{self.device_id}')
            del dummy_tensor
            
            # Clear cache to start fresh
            torch.cuda.empty_cache()
            
            self.logger.info("CUDA context initialized successfully")
            
        except Exception as e:
            self.logger.error(f"CUDA context initialization failed: {e}")
            raise
    
    async def _setup_memory_management(self) -> None:
        """
        Setup advanced GPU memory management.
        
        Configures memory pools, allocation strategies, and garbage collection
        for optimal memory utilization and performance.
        """
        try:
            if self.cupy_available:
                # Setup CuPy memory pool
                self.memory_pool = cp.get_default_memory_pool()
                
                # Set memory pool limit based on configuration
                total_memory = self.device_info["total_memory"]
                memory_limit = int(total_memory * self.memory_fraction)
                self.memory_pool.set_limit(size=memory_limit)
                
                self.logger.info("GPU memory pool configured",
                               extra={"memory_limit_mb": memory_limit // (1024 * 1024)})
            
            # Configure PyTorch memory management
            if self.allow_growth:
                # Enable memory growth for PyTorch
                torch.cuda.set_per_process_memory_fraction(self.memory_fraction, self.device_id)
            
        except Exception as e:
            self.logger.error(f"Memory management setup failed: {e}")
            raise
    
    async def _initialize_stream_pool(self) -> None:
        """
        Initialize CUDA stream pool for concurrent operations.
        
        Creates a pool of CUDA streams to enable parallel execution of
        GPU operations and improve overall throughput.
        """
        try:
            if self.cupy_available:
                # Create stream pool for concurrent operations
                stream_count = min(8, self.device_info["multiprocessor_count"])
                
                for i in range(stream_count):
                    stream = cp.cuda.Stream()
                    self.stream_pool.append(stream)
                
                self.logger.info("CUDA stream pool initialized",
                               extra={"stream_count": stream_count})
            
        except Exception as e:
            self.logger.error(f"Stream pool initialization failed: {e}")
            raise
    
    @asynccontextmanager
    async def allocate_resources(self, 
                                task_id: str,
                                task_type: GPUTaskType,
                                memory_mb: int,
                                compute_units: int = 1,
                                priority: int = 1,
                                estimated_duration: float = 1.0):
        """
        Context manager for GPU resource allocation.
        
        Provides intelligent resource allocation with automatic cleanup,
        priority-based scheduling, and resource conflict resolution.
        
        Args:
            task_id: Unique identifier for the task
            task_type: Type of GPU task for optimization
            memory_mb: Required memory in megabytes
            compute_units: Number of compute units required
            priority: Task priority (higher values = higher priority)
            estimated_duration: Estimated task duration in seconds
            
        Yields:
            Dict containing allocated GPU resources and configuration
        """
        allocation = None
        
        try:
            async with self._allocation_lock:
                # Check resource availability
                if not await self._check_resource_availability(memory_mb, compute_units):
                    if self.fallback_to_cpu:
                        self.logger.warning("GPU resources unavailable, falling back to CPU",
                                          extra={"task_id": task_id})
                        yield {"device": "cpu", "fallback": True}
                        return
                    else:
                        raise RuntimeError("Insufficient GPU resources available")
                
                # Create allocation record
                allocation = GPUResourceAllocation(
                    task_id=task_id,
                    task_type=task_type,
                    memory_mb=memory_mb,
                    compute_units=compute_units,
                    priority=priority,
                    allocated_at=time.time(),
                    estimated_duration=estimated_duration
                )
                
                # Register allocation
                self.active_allocations[task_id] = allocation
                self.allocation_history.append(allocation)
                
                self.logger.debug("GPU resources allocated",
                                extra={"task_id": task_id, "allocation": allocation})
            
            # Prepare resource configuration
            resource_config = await self._prepare_resource_config(allocation)
            
            yield resource_config
            
        except Exception as e:
            self.logger.error(f"GPU resource allocation failed: {e}",
                            extra={"task_id": task_id})
            raise
            
        finally:
            # Cleanup resources
            if allocation and task_id in self.active_allocations:
                async with self._allocation_lock:
                    del self.active_allocations[task_id]
                    
                    # Trigger garbage collection if needed
                    await self._cleanup_memory()
                    
                    self.logger.debug("GPU resources deallocated",
                                    extra={"task_id": task_id})
    
    async def _check_resource_availability(self, memory_mb: int, compute_units: int) -> bool:
        """
        Check if requested GPU resources are available.
        
        Args:
            memory_mb: Required memory in megabytes
            compute_units: Required compute units
            
        Returns:
            True if resources are available, False otherwise
        """
        if not self.cuda_available:
            return False
        
        try:
            # Check memory availability
            if self.cupy_available:
                memory_info = cp.cuda.MemoryInfo()
                available_memory_mb = memory_info.free // (1024 * 1024)
            else:
                available_memory_mb = torch.cuda.get_device_properties(self.device_id).total_memory // (1024 * 1024)
                allocated_memory_mb = torch.cuda.memory_allocated(self.device_id) // (1024 * 1024)
                available_memory_mb -= allocated_memory_mb
            
            if memory_mb > available_memory_mb:
                return False
            
            # Check compute unit availability (simplified check)
            active_compute_units = sum(alloc.compute_units for alloc in self.active_allocations.values())
            max_compute_units = self.device_info["multiprocessor_count"] if self.device_info else 8
            
            if active_compute_units + compute_units > max_compute_units:
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Resource availability check failed: {e}")
            return False
    
    async def _prepare_resource_config(self, allocation: GPUResourceAllocation) -> Dict[str, Any]:
        """
        Prepare GPU resource configuration for allocated task.
        
        Args:
            allocation: Resource allocation record
            
        Returns:
            Dict containing GPU configuration and resources
        """
        config = {
            "device": f"cuda:{self.device_id}",
            "device_id": self.device_id,
            "task_type": allocation.task_type,
            "memory_mb": allocation.memory_mb,
            "compute_units": allocation.compute_units,
            "fallback": False
        }
        
        # Add task-specific optimizations
        if allocation.task_type == GPUTaskType.AUDIO_PROCESSING:
            config.update({
                "stream": self._get_available_stream(),
                "memory_pool": self.memory_pool,
                "optimization_level": "audio"
            })
        elif allocation.task_type == GPUTaskType.NLU_INFERENCE:
            config.update({
                "stream": self._get_available_stream(),
                "batch_size": self.config.nlu_batch_size,
                "optimization_level": "inference"
            })
        
        return config
    
    def _get_available_stream(self) -> Optional[cp.cuda.Stream]:
        """
        Get an available CUDA stream from the pool.
        
        Returns:
            Available CUDA stream or None if pool is empty
        """
        if self.stream_pool:
            # Simple round-robin selection
            return self.stream_pool[len(self.active_allocations) % len(self.stream_pool)]
        return None
    
    async def _cleanup_memory(self) -> None:
        """
        Perform GPU memory cleanup and garbage collection.
        
        Implements intelligent memory management including cache clearing,
        memory pool optimization, and garbage collection triggering.
        """
        try:
            # Clear PyTorch cache
            torch.cuda.empty_cache()
            
            # CuPy memory pool cleanup
            if self.memory_pool:
                self.memory_pool.free_all_blocks()
            
            # Force garbage collection if memory usage is high
            if self.cupy_available:
                memory_info = cp.cuda.MemoryInfo()
                memory_usage = 1.0 - (memory_info.free / memory_info.total)
                
                if memory_usage > 0.8:  # 80% memory usage threshold
                    import gc
                    gc.collect()
                    
                    self.logger.debug("GPU memory cleanup performed",
                                    extra={"memory_usage": memory_usage})
            
        except Exception as e:
            self.logger.error(f"GPU memory cleanup failed: {e}")
    
    async def _monitor_performance(self) -> None:
        """
        Background task for continuous GPU performance monitoring.
        
        Collects performance metrics, detects anomalies, and triggers
        optimization actions based on system behavior patterns.
        """
        while True:
            try:
                metrics = await self._collect_performance_metrics()
                self.performance_history.append(metrics)
                
                # Keep only recent history (last 1000 entries)
                if len(self.performance_history) > 1000:
                    self.performance_history = self.performance_history[-1000:]
                
                # Check for performance issues
                await self._analyze_performance_trends(metrics)
                
                # Sleep before next monitoring cycle
                await asyncio.sleep(self.config.health_check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Performance monitoring error: {e}")
                await asyncio.sleep(5)  # Brief pause before retry
    
    async def _collect_performance_metrics(self) -> GPUPerformanceMetrics:
        """
        Collect comprehensive GPU performance metrics.
        
        Returns:
            GPUPerformanceMetrics containing current system state
        """
        try:
            # Get GPU utilization using GPUtil
            gpus = GPUtil.getGPUs()
            gpu = gpus[self.device_id] if self.device_id < len(gpus) else None
            
            if gpu:
                metrics = GPUPerformanceMetrics(
                    utilization_percent=gpu.load * 100,
                    memory_used_mb=gpu.memoryUsed,
                    memory_total_mb=gpu.memoryTotal,
                    memory_free_mb=gpu.memoryFree,
                    temperature_celsius=gpu.temperature,
                    power_draw_watts=getattr(gpu, 'powerDraw', 0),
                    compute_capability=self.device_info.get("compute_capability", (0, 0)),
                    driver_version=gpu.driver,
                    cuda_version=torch.version.cuda or "unknown"
                )
            else:
                # Fallback metrics if GPUtil fails
                metrics = GPUPerformanceMetrics(
                    utilization_percent=0.0,
                    memory_used_mb=0,
                    memory_total_mb=0,
                    memory_free_mb=0,
                    temperature_celsius=0.0,
                    power_draw_watts=0.0,
                    compute_capability=(0, 0),
                    driver_version="unknown",
                    cuda_version="unknown"
                )
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Performance metrics collection failed: {e}")
            # Return empty metrics on failure
            return GPUPerformanceMetrics(
                utilization_percent=0.0,
                memory_used_mb=0,
                memory_total_mb=0,
                memory_free_mb=0,
                temperature_celsius=0.0,
                power_draw_watts=0.0,
                compute_capability=(0, 0),
                driver_version="unknown",
                cuda_version="unknown"
            )
    
    async def _analyze_performance_trends(self, current_metrics: GPUPerformanceMetrics) -> None:
        """
        Analyze performance trends and trigger optimizations.
        
        Args:
            current_metrics: Current performance metrics
        """
        try:
            # Check for high memory usage
            memory_usage = current_metrics.memory_used_mb / max(current_metrics.memory_total_mb, 1)
            
            if memory_usage > 0.9:  # 90% memory usage
                self.logger.warning("High GPU memory usage detected",
                                  extra={"memory_usage": memory_usage})
                await self._cleanup_memory()
            
            # Check for thermal throttling
            if current_metrics.temperature_celsius > 80:  # 80°C threshold
                self.logger.warning("High GPU temperature detected",
                                  extra={"temperature": current_metrics.temperature_celsius})
            
            # Check for low utilization
            if (len(self.active_allocations) > 0 and 
                current_metrics.utilization_percent < 10):  # 10% utilization
                self.logger.debug("Low GPU utilization with active allocations",
                                extra={"utilization": current_metrics.utilization_percent,
                                      "active_allocations": len(self.active_allocations)})
            
        except Exception as e:
            self.logger.error(f"Performance trend analysis failed: {e}")
    
    async def get_health_status(self) -> Dict[str, Any]:
        """
        Get comprehensive GPU health status.
        
        Returns:
            Dict containing detailed health and performance information
        """
        try:
            if not self.cuda_available:
                return {
                    "status": "unavailable",
                    "message": "CUDA not available",
                    "fallback_enabled": self.fallback_to_cpu
                }
            
            current_metrics = await self._collect_performance_metrics()
            
            # Determine health status
            status = "healthy"
            issues = []
            
            # Check memory usage
            memory_usage = current_metrics.memory_used_mb / max(current_metrics.memory_total_mb, 1)
            if memory_usage > 0.95:
                status = "critical"
                issues.append("Critical memory usage")
            elif memory_usage > 0.85:
                status = "warning"
                issues.append("High memory usage")
            
            # Check temperature
            if current_metrics.temperature_celsius > 85:
                status = "critical"
                issues.append("Critical temperature")
            elif current_metrics.temperature_celsius > 75:
                if status == "healthy":
                    status = "warning"
                issues.append("High temperature")
            
            return {
                "status": status,
                "issues": issues,
                "metrics": {
                    "utilization_percent": current_metrics.utilization_percent,
                    "memory_usage_percent": memory_usage * 100,
                    "temperature_celsius": current_metrics.temperature_celsius,
                    "active_allocations": len(self.active_allocations)
                },
                "device_info": self.device_info,
                "capabilities": {
                    "cuda_available": self.cuda_available,
                    "cupy_available": self.cupy_available
                }
            }
            
        except Exception as e:
            self.logger.error(f"Health status check failed: {e}")
            return {
                "status": "error",
                "message": str(e),
                "fallback_enabled": self.fallback_to_cpu
            }
    
    async def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get performance summary and statistics.
        
        Returns:
            Dict containing performance statistics and trends
        """
        try:
            if not self.performance_history:
                return {"message": "No performance data available"}
            
            recent_metrics = self.performance_history[-10:]  # Last 10 measurements
            
            # Calculate averages
            avg_utilization = sum(m.utilization_percent for m in recent_metrics) / len(recent_metrics)
            avg_memory_usage = sum(m.memory_used_mb for m in recent_metrics) / len(recent_metrics)
            avg_temperature = sum(m.temperature_celsius for m in recent_metrics) / len(recent_metrics)
            
            # Calculate trends
            if len(recent_metrics) >= 2:
                utilization_trend = recent_metrics[-1].utilization_percent - recent_metrics[0].utilization_percent
                memory_trend = recent_metrics[-1].memory_used_mb - recent_metrics[0].memory_used_mb
                temperature_trend = recent_metrics[-1].temperature_celsius - recent_metrics[0].temperature_celsius
            else:
                utilization_trend = memory_trend = temperature_trend = 0.0
            
            return {
                "averages": {
                    "utilization_percent": avg_utilization,
                    "memory_used_mb": avg_memory_usage,
                    "temperature_celsius": avg_temperature
                },
                "trends": {
                    "utilization_change": utilization_trend,
                    "memory_change_mb": memory_trend,
                    "temperature_change": temperature_trend
                },
                "allocation_stats": {
                    "total_allocations": len(self.allocation_history),
                    "active_allocations": len(self.active_allocations),
                    "allocation_types": {
                        task_type.value: sum(1 for alloc in self.allocation_history 
                                           if alloc.task_type == task_type)
                        for task_type in GPUTaskType
                    }
                }
            }
            
        except Exception as e:
            self.logger.error(f"Performance summary generation failed: {e}")
            return {"error": str(e)}
    
    async def cleanup(self) -> None:
        """
        Cleanup GPU resources and stop monitoring.
        
        Performs comprehensive cleanup including stopping monitoring tasks,
        releasing allocations, and cleaning up GPU memory.
        """
        self.logger.info("Cleaning up GPU resource manager")
        
        try:
            # Stop monitoring task
            if self._monitoring_task:
                self._monitoring_task.cancel()
                try:
                    await self._monitoring_task
                except asyncio.CancelledError:
                    pass
            
            # Clear all active allocations
            async with self._allocation_lock:
                self.active_allocations.clear()
            
            # Cleanup GPU memory
            await self._cleanup_memory()
            
            # Cleanup stream pool
            self.stream_pool.clear()
            
            # Shutdown thread pool
            self._executor.shutdown(wait=True)
            
            self.logger.info("GPU resource manager cleanup completed")
            
        except Exception as e:
            self.logger.error(f"GPU cleanup failed: {e}")
    
    def __del__(self):
        """Destructor to ensure cleanup on object deletion."""
        if hasattr(self, '_executor'):
            self._executor.shutdown(wait=False)