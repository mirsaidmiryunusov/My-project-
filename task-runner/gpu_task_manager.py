"""
GPU Task Manager for Project GeminiVoiceConnect

This module provides comprehensive GPU resource management and task execution
capabilities for the AI Call Center Agent system. It implements intelligent
GPU workload distribution, memory management, and performance optimization
for maximum computational efficiency.

Key Features:
- Intelligent GPU resource allocation and management
- Multi-GPU support with automatic load balancing
- Memory optimization and garbage collection
- Task queuing and priority management
- Performance monitoring and optimization
- Fault tolerance and error recovery
- Dynamic scaling based on workload
- GPU-accelerated ML model inference and training
"""

from typing import Dict, List, Optional, Any, Callable, Union, Tuple
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import json
import logging
from dataclasses import dataclass, asdict
import threading
import queue
import time
from concurrent.futures import ThreadPoolExecutor, Future
import psutil
import numpy as np

# GPU libraries
try:
    import torch
    import torch.cuda
    import cupy as cp
    import pynvml
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False
    torch = None
    cp = None
    pynvml = None

logger = logging.getLogger(__name__)


class TaskPriority(str, Enum):
    """GPU task priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class TaskStatus(str, Enum):
    """GPU task execution status"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class GPUMemoryStrategy(str, Enum):
    """GPU memory management strategies"""
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"
    DYNAMIC = "dynamic"


@dataclass
class GPUInfo:
    """GPU device information"""
    device_id: int
    name: str
    total_memory: int
    free_memory: int
    used_memory: int
    utilization: float
    temperature: float
    power_usage: float
    compute_capability: Tuple[int, int]
    is_available: bool


@dataclass
class GPUTask:
    """GPU task definition"""
    task_id: str
    function: Callable
    args: Tuple
    kwargs: Dict[str, Any]
    priority: TaskPriority
    device_preference: Optional[int]
    memory_requirement: Optional[int]
    estimated_duration: Optional[float]
    created_time: datetime
    status: TaskStatus = TaskStatus.PENDING
    assigned_device: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None


@dataclass
class GPUMetrics:
    """GPU performance metrics"""
    device_id: int
    timestamp: datetime
    utilization: float
    memory_used: int
    memory_total: int
    temperature: float
    power_usage: float
    tasks_completed: int
    tasks_failed: int
    average_task_duration: float


class GPUTaskManager:
    """
    Advanced GPU task management system with intelligent resource allocation.
    
    This manager handles GPU resource allocation, task scheduling, memory management,
    and performance optimization across multiple GPU devices. It provides a unified
    interface for GPU-accelerated computations with automatic load balancing and
    fault tolerance.
    """
    
    def __init__(self, memory_strategy: GPUMemoryStrategy = GPUMemoryStrategy.BALANCED):
        self.memory_strategy = memory_strategy
        self.is_initialized = False
        
        # GPU state
        self.gpu_devices = {}
        self.device_locks = {}
        self.device_queues = {}
        self.device_executors = {}
        
        # Task management
        self.task_queue = queue.PriorityQueue()
        self.active_tasks = {}
        self.completed_tasks = {}
        self.task_history = []
        
        # Performance tracking
        self.metrics_history = {}
        self.performance_stats = {}
        
        # Configuration
        self.max_concurrent_tasks_per_gpu = 2
        self.memory_threshold = 0.8  # 80% memory usage threshold
        self.temperature_threshold = 80  # 80°C temperature threshold
        
        # Threading
        self.scheduler_thread = None
        self.monitor_thread = None
        self.is_running = False
        
        # Initialize GPU resources
        self._initialize_gpu_resources()
        
        logger.info(f"GPU Task Manager initialized with {len(self.gpu_devices)} devices")
    
    def _initialize_gpu_resources(self):
        """Initialize GPU resources and monitoring"""
        if not GPU_AVAILABLE:
            logger.warning("GPU libraries not available, running in CPU-only mode")
            return
        
        try:
            # Initialize NVIDIA ML
            pynvml.nvmlInit()
            
            # Detect GPU devices
            device_count = torch.cuda.device_count() if torch.cuda.is_available() else 0
            
            for device_id in range(device_count):
                try:
                    # Get device properties
                    device_props = torch.cuda.get_device_properties(device_id)
                    handle = pynvml.nvmlDeviceGetHandleByIndex(device_id)
                    
                    # Get memory info
                    memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                    
                    # Get utilization
                    utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
                    
                    # Get temperature
                    temperature = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                    
                    # Get power usage
                    try:
                        power_usage = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0  # Convert to watts
                    except:
                        power_usage = 0.0
                    
                    gpu_info = GPUInfo(
                        device_id=device_id,
                        name=device_props.name,
                        total_memory=memory_info.total,
                        free_memory=memory_info.free,
                        used_memory=memory_info.used,
                        utilization=utilization.gpu,
                        temperature=temperature,
                        power_usage=power_usage,
                        compute_capability=(device_props.major, device_props.minor),
                        is_available=True
                    )
                    
                    self.gpu_devices[device_id] = gpu_info
                    self.device_locks[device_id] = threading.Lock()
                    self.device_queues[device_id] = queue.Queue()
                    self.device_executors[device_id] = ThreadPoolExecutor(
                        max_workers=self.max_concurrent_tasks_per_gpu,
                        thread_name_prefix=f"gpu_{device_id}"
                    )
                    
                    logger.info(f"Initialized GPU {device_id}: {device_props.name}")
                    
                except Exception as e:
                    logger.error(f"Failed to initialize GPU {device_id}: {str(e)}")
            
            self.is_initialized = True
            
        except Exception as e:
            logger.error(f"Failed to initialize GPU resources: {str(e)}")
    
    def start(self):
        """Start GPU task manager"""
        if not self.is_initialized:
            logger.warning("GPU Task Manager not properly initialized")
            return
        
        self.is_running = True
        
        # Start scheduler thread
        self.scheduler_thread = threading.Thread(
            target=self._scheduler_loop,
            name="gpu_scheduler",
            daemon=True
        )
        self.scheduler_thread.start()
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            name="gpu_monitor",
            daemon=True
        )
        self.monitor_thread.start()
        
        logger.info("GPU Task Manager started")
    
    def stop(self):
        """Stop GPU task manager"""
        self.is_running = False
        
        # Wait for threads to finish
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        # Shutdown executors
        for executor in self.device_executors.values():
            executor.shutdown(wait=True)
        
        logger.info("GPU Task Manager stopped")
    
    async def execute_task(
        self,
        function: Callable,
        *args,
        device: Optional[Union[int, str]] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        memory_requirement: Optional[int] = None,
        estimated_duration: Optional[float] = None,
        **kwargs
    ) -> Any:
        """
        Execute a GPU task asynchronously.
        
        Args:
            function: Function to execute on GPU
            *args: Function arguments
            device: Preferred GPU device (int) or 'auto' for automatic selection
            priority: Task priority
            memory_requirement: Required GPU memory in bytes
            estimated_duration: Estimated execution time in seconds
            **kwargs: Function keyword arguments
            
        Returns:
            Task result
        """
        if not self.is_initialized:
            # Fallback to CPU execution
            logger.warning("GPU not available, executing on CPU")
            return await self._execute_cpu_fallback(function, *args, **kwargs)
        
        # Create task
        task = GPUTask(
            task_id=f"task_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}",
            function=function,
            args=args,
            kwargs=kwargs,
            priority=priority,
            device_preference=device if isinstance(device, int) else None,
            memory_requirement=memory_requirement,
            estimated_duration=estimated_duration,
            created_time=datetime.utcnow()
        )
        
        # Submit task
        return await self._submit_task(task)
    
    async def _submit_task(self, task: GPUTask) -> Any:
        """Submit task for execution"""
        try:
            # Add to task queue with priority
            priority_value = self._get_priority_value(task.priority)
            self.task_queue.put((priority_value, task.created_time, task))
            
            task.status = TaskStatus.QUEUED
            self.active_tasks[task.task_id] = task
            
            logger.debug(f"Task {task.task_id} queued with priority {task.priority}")
            
            # Wait for task completion
            while task.status in [TaskStatus.PENDING, TaskStatus.QUEUED, TaskStatus.RUNNING]:
                await asyncio.sleep(0.1)
            
            if task.status == TaskStatus.COMPLETED:
                return task.result
            elif task.status == TaskStatus.FAILED:
                raise Exception(task.error)
            else:
                raise Exception(f"Task {task.task_id} was cancelled")
                
        except Exception as e:
            logger.error(f"Failed to submit task {task.task_id}: {str(e)}")
            raise
    
    def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.is_running:
            try:
                # Get next task from queue
                try:
                    priority, created_time, task = self.task_queue.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                # Find available GPU
                device_id = self._select_optimal_device(task)
                
                if device_id is not None:
                    # Execute task
                    self._execute_task_on_device(task, device_id)
                else:
                    # No available device, put task back in queue
                    self.task_queue.put((priority, created_time, task))
                    time.sleep(0.5)  # Wait before retrying
                
            except Exception as e:
                logger.error(f"Error in scheduler loop: {str(e)}")
                time.sleep(1.0)
    
    def _monitor_loop(self):
        """GPU monitoring loop"""
        while self.is_running:
            try:
                # Update GPU metrics
                self._update_gpu_metrics()
                
                # Check for overheating or memory issues
                self._check_gpu_health()
                
                # Clean up completed tasks
                self._cleanup_completed_tasks()
                
                time.sleep(5.0)  # Monitor every 5 seconds
                
            except Exception as e:
                logger.error(f"Error in monitor loop: {str(e)}")
                time.sleep(5.0)
    
    def _select_optimal_device(self, task: GPUTask) -> Optional[int]:
        """Select optimal GPU device for task"""
        if not self.gpu_devices:
            return None
        
        # Check device preference
        if task.device_preference is not None:
            if (task.device_preference in self.gpu_devices and
                self._is_device_available(task.device_preference, task)):
                return task.device_preference
        
        # Find best available device
        best_device = None
        best_score = -1
        
        for device_id, gpu_info in self.gpu_devices.items():
            if not self._is_device_available(device_id, task):
                continue
            
            # Calculate device score
            score = self._calculate_device_score(device_id, task)
            
            if score > best_score:
                best_score = score
                best_device = device_id
        
        return best_device
    
    def _is_device_available(self, device_id: int, task: GPUTask) -> bool:
        """Check if device is available for task"""
        gpu_info = self.gpu_devices.get(device_id)
        if not gpu_info or not gpu_info.is_available:
            return False
        
        # Check temperature
        if gpu_info.temperature > self.temperature_threshold:
            return False
        
        # Check memory requirement
        if task.memory_requirement:
            if gpu_info.free_memory < task.memory_requirement:
                return False
        
        # Check current load
        current_tasks = sum(1 for t in self.active_tasks.values() 
                          if t.assigned_device == device_id and t.status == TaskStatus.RUNNING)
        
        if current_tasks >= self.max_concurrent_tasks_per_gpu:
            return False
        
        return True
    
    def _calculate_device_score(self, device_id: int, task: GPUTask) -> float:
        """Calculate device suitability score for task"""
        gpu_info = self.gpu_devices[device_id]
        
        score = 0.0
        
        # Memory availability (40% weight)
        memory_ratio = gpu_info.free_memory / gpu_info.total_memory
        score += memory_ratio * 0.4
        
        # Utilization (30% weight) - prefer less utilized devices
        utilization_score = (100 - gpu_info.utilization) / 100.0
        score += utilization_score * 0.3
        
        # Temperature (20% weight) - prefer cooler devices
        temp_score = max(0, (self.temperature_threshold - gpu_info.temperature) / self.temperature_threshold)
        score += temp_score * 0.2
        
        # Current load (10% weight)
        current_tasks = sum(1 for t in self.active_tasks.values() 
                          if t.assigned_device == device_id and t.status == TaskStatus.RUNNING)
        load_score = max(0, (self.max_concurrent_tasks_per_gpu - current_tasks) / self.max_concurrent_tasks_per_gpu)
        score += load_score * 0.1
        
        return score
    
    def _execute_task_on_device(self, task: GPUTask, device_id: int):
        """Execute task on specific GPU device"""
        try:
            task.assigned_device = device_id
            task.status = TaskStatus.RUNNING
            task.start_time = datetime.utcnow()
            
            # Submit to device executor
            executor = self.device_executors[device_id]
            future = executor.submit(self._run_task_on_gpu, task, device_id)
            
            # Store future for monitoring
            task.future = future
            
            logger.debug(f"Task {task.task_id} started on GPU {device_id}")
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.end_time = datetime.utcnow()
            logger.error(f"Failed to execute task {task.task_id} on GPU {device_id}: {str(e)}")
    
    def _run_task_on_gpu(self, task: GPUTask, device_id: int) -> Any:
        """Run task on GPU device (executed in thread)"""
        try:
            # Set GPU device
            if torch and torch.cuda.is_available():
                torch.cuda.set_device(device_id)
            
            # Execute function
            result = task.function(*task.args, **task.kwargs)
            
            # Update task status
            task.result = result
            task.status = TaskStatus.COMPLETED
            task.end_time = datetime.utcnow()
            
            # Clean up GPU memory
            self._cleanup_gpu_memory(device_id)
            
            logger.debug(f"Task {task.task_id} completed on GPU {device_id}")
            
            return result
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.end_time = datetime.utcnow()
            
            logger.error(f"Task {task.task_id} failed on GPU {device_id}: {str(e)}")
            raise
    
    def _cleanup_gpu_memory(self, device_id: int):
        """Clean up GPU memory after task completion"""
        try:
            if torch and torch.cuda.is_available():
                with torch.cuda.device(device_id):
                    if self.memory_strategy in [GPUMemoryStrategy.AGGRESSIVE, GPUMemoryStrategy.DYNAMIC]:
                        torch.cuda.empty_cache()
                        torch.cuda.synchronize()
            
            if cp:
                with cp.cuda.Device(device_id):
                    if self.memory_strategy in [GPUMemoryStrategy.AGGRESSIVE, GPUMemoryStrategy.DYNAMIC]:
                        cp.get_default_memory_pool().free_all_blocks()
                        
        except Exception as e:
            logger.warning(f"Failed to cleanup GPU memory on device {device_id}: {str(e)}")
    
    def _update_gpu_metrics(self):
        """Update GPU metrics"""
        if not GPU_AVAILABLE:
            return
        
        try:
            for device_id in self.gpu_devices:
                handle = pynvml.nvmlDeviceGetHandleByIndex(device_id)
                
                # Get current metrics
                memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
                temperature = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                
                try:
                    power_usage = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0
                except:
                    power_usage = 0.0
                
                # Update GPU info
                gpu_info = self.gpu_devices[device_id]
                gpu_info.free_memory = memory_info.free
                gpu_info.used_memory = memory_info.used
                gpu_info.utilization = utilization.gpu
                gpu_info.temperature = temperature
                gpu_info.power_usage = power_usage
                
                # Store metrics history
                metrics = GPUMetrics(
                    device_id=device_id,
                    timestamp=datetime.utcnow(),
                    utilization=utilization.gpu,
                    memory_used=memory_info.used,
                    memory_total=memory_info.total,
                    temperature=temperature,
                    power_usage=power_usage,
                    tasks_completed=self._count_completed_tasks(device_id),
                    tasks_failed=self._count_failed_tasks(device_id),
                    average_task_duration=self._calculate_average_task_duration(device_id)
                )
                
                if device_id not in self.metrics_history:
                    self.metrics_history[device_id] = []
                
                self.metrics_history[device_id].append(metrics)
                
                # Keep only last 1000 metrics
                if len(self.metrics_history[device_id]) > 1000:
                    self.metrics_history[device_id] = self.metrics_history[device_id][-1000:]
                
        except Exception as e:
            logger.error(f"Failed to update GPU metrics: {str(e)}")
    
    def _check_gpu_health(self):
        """Check GPU health and take corrective actions"""
        for device_id, gpu_info in self.gpu_devices.items():
            # Check temperature
            if gpu_info.temperature > self.temperature_threshold:
                logger.warning(f"GPU {device_id} overheating: {gpu_info.temperature}°C")
                gpu_info.is_available = False
                
                # Cancel running tasks on overheated GPU
                self._cancel_tasks_on_device(device_id, "GPU overheating")
            
            # Check memory usage
            memory_usage_ratio = gpu_info.used_memory / gpu_info.total_memory
            if memory_usage_ratio > self.memory_threshold:
                logger.warning(f"GPU {device_id} high memory usage: {memory_usage_ratio:.1%}")
                
                # Trigger aggressive memory cleanup
                self._cleanup_gpu_memory(device_id)
            
            # Re-enable GPU if temperature is back to normal
            if not gpu_info.is_available and gpu_info.temperature < self.temperature_threshold - 5:
                logger.info(f"GPU {device_id} temperature normalized, re-enabling")
                gpu_info.is_available = True
    
    def _cancel_tasks_on_device(self, device_id: int, reason: str):
        """Cancel all tasks running on a specific device"""
        for task in self.active_tasks.values():
            if task.assigned_device == device_id and task.status == TaskStatus.RUNNING:
                task.status = TaskStatus.CANCELLED
                task.error = reason
                task.end_time = datetime.utcnow()
                
                # Cancel future if possible
                if hasattr(task, 'future'):
                    task.future.cancel()
                
                logger.warning(f"Cancelled task {task.task_id} on GPU {device_id}: {reason}")
    
    def _cleanup_completed_tasks(self):
        """Clean up completed tasks from active list"""
        completed_task_ids = []
        
        for task_id, task in self.active_tasks.items():
            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                completed_task_ids.append(task_id)
                
                # Move to completed tasks
                self.completed_tasks[task_id] = task
                self.task_history.append(task)
        
        # Remove from active tasks
        for task_id in completed_task_ids:
            del self.active_tasks[task_id]
        
        # Keep only last 1000 completed tasks
        if len(self.completed_tasks) > 1000:
            oldest_tasks = sorted(self.completed_tasks.values(), key=lambda x: x.end_time)[:100]
            for task in oldest_tasks:
                del self.completed_tasks[task.task_id]
    
    def _count_completed_tasks(self, device_id: int) -> int:
        """Count completed tasks for device"""
        return sum(1 for task in self.task_history 
                  if task.assigned_device == device_id and task.status == TaskStatus.COMPLETED)
    
    def _count_failed_tasks(self, device_id: int) -> int:
        """Count failed tasks for device"""
        return sum(1 for task in self.task_history 
                  if task.assigned_device == device_id and task.status == TaskStatus.FAILED)
    
    def _calculate_average_task_duration(self, device_id: int) -> float:
        """Calculate average task duration for device"""
        completed_tasks = [task for task in self.task_history 
                          if (task.assigned_device == device_id and 
                              task.status == TaskStatus.COMPLETED and 
                              task.start_time and task.end_time)]
        
        if not completed_tasks:
            return 0.0
        
        durations = [(task.end_time - task.start_time).total_seconds() for task in completed_tasks]
        return sum(durations) / len(durations)
    
    def _get_priority_value(self, priority: TaskPriority) -> int:
        """Get numeric priority value for queue ordering"""
        priority_map = {
            TaskPriority.URGENT: 1,
            TaskPriority.HIGH: 2,
            TaskPriority.NORMAL: 3,
            TaskPriority.LOW: 4
        }
        return priority_map.get(priority, 3)
    
    async def _execute_cpu_fallback(self, function: Callable, *args, **kwargs) -> Any:
        """Execute function on CPU as fallback"""
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, function, *args, **kwargs)
            return result
        except Exception as e:
            logger.error(f"CPU fallback execution failed: {str(e)}")
            raise
    
    # Public API methods
    
    def get_gpu_status(self) -> Dict[str, Any]:
        """Get current GPU status"""
        if not self.is_initialized:
            return {"error": "GPU Task Manager not initialized"}
        
        status = {
            "total_devices": len(self.gpu_devices),
            "available_devices": sum(1 for gpu in self.gpu_devices.values() if gpu.is_available),
            "active_tasks": len(self.active_tasks),
            "queued_tasks": self.task_queue.qsize(),
            "completed_tasks": len(self.completed_tasks),
            "devices": {}
        }
        
        for device_id, gpu_info in self.gpu_devices.items():
            device_status = {
                "name": gpu_info.name,
                "available": gpu_info.is_available,
                "utilization": gpu_info.utilization,
                "memory_used": gpu_info.used_memory,
                "memory_total": gpu_info.total_memory,
                "memory_free": gpu_info.free_memory,
                "temperature": gpu_info.temperature,
                "power_usage": gpu_info.power_usage,
                "active_tasks": sum(1 for t in self.active_tasks.values() 
                                  if t.assigned_device == device_id and t.status == TaskStatus.RUNNING)
            }
            status["devices"][device_id] = device_status
        
        return status
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of specific task"""
        task = self.active_tasks.get(task_id) or self.completed_tasks.get(task_id)
        
        if not task:
            return None
        
        return {
            "task_id": task.task_id,
            "status": task.status,
            "priority": task.priority,
            "assigned_device": task.assigned_device,
            "created_time": task.created_time.isoformat(),
            "start_time": task.start_time.isoformat() if task.start_time else None,
            "end_time": task.end_time.isoformat() if task.end_time else None,
            "duration": (task.end_time - task.start_time).total_seconds() if task.start_time and task.end_time else None,
            "error": task.error
        }
    
    def get_performance_metrics(self, device_id: Optional[int] = None) -> Dict[str, Any]:
        """Get performance metrics"""
        if device_id is not None:
            if device_id not in self.metrics_history:
                return {"error": f"No metrics for device {device_id}"}
            
            recent_metrics = self.metrics_history[device_id][-100:]  # Last 100 metrics
            
            if not recent_metrics:
                return {"error": f"No recent metrics for device {device_id}"}
            
            return {
                "device_id": device_id,
                "average_utilization": sum(m.utilization for m in recent_metrics) / len(recent_metrics),
                "average_temperature": sum(m.temperature for m in recent_metrics) / len(recent_metrics),
                "average_power_usage": sum(m.power_usage for m in recent_metrics) / len(recent_metrics),
                "total_tasks_completed": recent_metrics[-1].tasks_completed,
                "total_tasks_failed": recent_metrics[-1].tasks_failed,
                "average_task_duration": recent_metrics[-1].average_task_duration,
                "memory_usage_trend": [m.memory_used / m.memory_total for m in recent_metrics[-10:]]
            }
        else:
            # Return metrics for all devices
            all_metrics = {}
            for dev_id in self.gpu_devices:
                all_metrics[dev_id] = self.get_performance_metrics(dev_id)
            return all_metrics
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a specific task"""
        task = self.active_tasks.get(task_id)
        
        if not task:
            return False
        
        if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            return False
        
        task.status = TaskStatus.CANCELLED
        task.error = "Task cancelled by user"
        task.end_time = datetime.utcnow()
        
        # Cancel future if possible
        if hasattr(task, 'future'):
            task.future.cancel()
        
        logger.info(f"Cancelled task {task_id}")
        return True
    
    def set_memory_strategy(self, strategy: GPUMemoryStrategy):
        """Set GPU memory management strategy"""
        self.memory_strategy = strategy
        logger.info(f"GPU memory strategy set to {strategy}")
    
    def optimize_memory_usage(self):
        """Optimize GPU memory usage across all devices"""
        for device_id in self.gpu_devices:
            self._cleanup_gpu_memory(device_id)
        
        logger.info("GPU memory optimization completed")


# Global GPU task manager instance
gpu_task_manager = None

def get_gpu_task_manager() -> GPUTaskManager:
    """Get or create GPU task manager instance"""
    global gpu_task_manager
    if gpu_task_manager is None:
        gpu_task_manager = GPUTaskManager()
        gpu_task_manager.start()
    return gpu_task_manager