"""
Task-Runner Main Application Module

This module implements the comprehensive background task processing system
using Celery for Project GeminiVoiceConnect. The task-runner handles all
asynchronous operations including campaign execution, SMS batch processing,
analytics computation, revenue optimization, and system maintenance tasks.

The task-runner leverages advanced GPU acceleration for computationally
intensive tasks such as batch audio analysis, machine learning model
training, and complex data processing operations.
"""

import asyncio
import logging
import os
import signal
import sys
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

import structlog
import celery
from celery import Celery, Task
from celery.signals import worker_ready, worker_shutdown
import redis
from sqlmodel import create_engine, Session
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import torch
import cupy as cp

from config import TaskRunnerConfig
from database import get_session
from models import *
from analytics_processor import AnalyticsProcessor
from campaign_executor import CampaignExecutor
from revenue_optimizer import RevenueOptimizer
from sms_batch_processor import SMSBatchProcessor
from report_generator import ReportGenerator
from data_archiver import DataArchiver
from ml_trainer import MLModelTrainer
from gpu_task_manager import GPUTaskManager


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

# Load configuration
config = TaskRunnerConfig()

# Initialize Celery application with comprehensive configuration
celery_app = Celery(
    'gemini-task-runner',
    broker=config.celery_broker_url,
    backend=config.celery_result_backend,
    include=[
        'tasks.campaign_tasks',
        'tasks.sms_tasks',
        'tasks.analytics_tasks',
        'tasks.revenue_tasks',
        'tasks.ml_tasks',
        'tasks.maintenance_tasks'
    ]
)

# Celery configuration for optimal performance and GPU utilization
celery_app.conf.update(
    # Task routing and execution
    task_routes={
        'tasks.ml_tasks.*': {'queue': 'gpu_queue'},
        'tasks.analytics_tasks.complex_*': {'queue': 'gpu_queue'},
        'tasks.campaign_tasks.*': {'queue': 'campaign_queue'},
        'tasks.sms_tasks.*': {'queue': 'sms_queue'},
        'tasks.revenue_tasks.*': {'queue': 'revenue_queue'},
        'tasks.maintenance_tasks.*': {'queue': 'maintenance_queue'},
    },
    
    # Worker configuration
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=False,
    
    # Task execution settings
    task_soft_time_limit=300,  # 5 minutes
    task_time_limit=600,       # 10 minutes
    task_max_retries=3,
    task_default_retry_delay=60,
    
    # Result backend settings
    result_expires=3600,  # 1 hour
    result_persistent=True,
    
    # Serialization
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    
    # Timezone
    timezone='UTC',
    enable_utc=True,
    
    # Beat schedule for periodic tasks
    beat_schedule={
        'process-pending-campaigns': {
            'task': 'tasks.campaign_tasks.process_pending_campaigns',
            'schedule': 60.0,  # Every minute
        },
        'send-batch-sms': {
            'task': 'tasks.sms_tasks.send_batch_sms',
            'schedule': 30.0,  # Every 30 seconds
        },
        'update-analytics': {
            'task': 'tasks.analytics_tasks.update_real_time_analytics',
            'schedule': 300.0,  # Every 5 minutes
        },
        'optimize-revenue': {
            'task': 'tasks.revenue_tasks.optimize_revenue_strategies',
            'schedule': 3600.0,  # Every hour
        },
        'train-ml-models': {
            'task': 'tasks.ml_tasks.train_predictive_models',
            'schedule': 86400.0,  # Daily
        },
        'archive-old-data': {
            'task': 'tasks.maintenance_tasks.archive_old_data',
            'schedule': 86400.0,  # Daily
        },
        'generate-daily-reports': {
            'task': 'tasks.analytics_tasks.generate_daily_reports',
            'schedule': celery.schedules.crontab(hour=6, minute=0),  # 6 AM daily
        },
        'cleanup-temp-files': {
            'task': 'tasks.maintenance_tasks.cleanup_temp_files',
            'schedule': 3600.0,  # Every hour
        },
    },
)

# Global application state
app_state: Dict[str, Any] = {}


class GPUAwareTask(Task):
    """
    Custom Celery task class with GPU resource management.
    
    Provides automatic GPU resource allocation, monitoring, and cleanup
    for tasks requiring GPU acceleration.
    """
    
    def __init__(self):
        self.gpu_manager = None
        self.gpu_allocated = False
    
    def __call__(self, *args, **kwargs):
        """Execute task with GPU resource management."""
        try:
            # Allocate GPU resources if needed
            if self.requires_gpu():
                self.gpu_manager = app_state.get('gpu_task_manager')
                if self.gpu_manager:
                    self.gpu_allocated = self.gpu_manager.allocate_gpu_resources(self.name)
                    if not self.gpu_allocated:
                        logger.warning("GPU allocation failed, falling back to CPU", task=self.name)
            
            # Execute the task
            result = super().__call__(*args, **kwargs)
            
            return result
            
        finally:
            # Clean up GPU resources
            if self.gpu_allocated and self.gpu_manager:
                self.gpu_manager.release_gpu_resources(self.name)
                self.gpu_allocated = False
    
    def requires_gpu(self) -> bool:
        """Check if task requires GPU resources."""
        return any(keyword in self.name for keyword in ['ml_', 'complex_', 'gpu_'])


# Set custom task class
celery_app.Task = GPUAwareTask


@worker_ready.connect
def worker_ready_handler(sender=None, **kwargs):
    """
    Worker initialization handler.
    
    Initializes all necessary components when a Celery worker starts,
    including database connections, GPU resources, and service managers.
    """
    logger.info("Initializing Celery worker")
    
    try:
        # Initialize database connection
        engine = create_engine(config.database_url)
        app_state['engine'] = engine
        
        # Initialize Redis connection
        redis_client = redis.Redis.from_url(config.redis_url)
        app_state['redis'] = redis_client
        
        # Initialize GPU task manager
        gpu_task_manager = GPUTaskManager(config)
        gpu_task_manager.initialize()
        app_state['gpu_task_manager'] = gpu_task_manager
        
        # Initialize service components
        analytics_processor = AnalyticsProcessor(config, engine, redis_client)
        app_state['analytics_processor'] = analytics_processor
        
        campaign_executor = CampaignExecutor(config, engine, redis_client)
        app_state['campaign_executor'] = campaign_executor
        
        revenue_optimizer = RevenueOptimizer(config, engine, redis_client)
        app_state['revenue_optimizer'] = revenue_optimizer
        
        sms_batch_processor = SMSBatchProcessor(config, engine, redis_client)
        app_state['sms_batch_processor'] = sms_batch_processor
        
        report_generator = ReportGenerator(config, engine)
        app_state['report_generator'] = report_generator
        
        data_archiver = DataArchiver(config, engine)
        app_state['data_archiver'] = data_archiver
        
        ml_trainer = MLModelTrainer(config, engine, gpu_task_manager)
        app_state['ml_trainer'] = ml_trainer
        
        logger.info("Celery worker initialized successfully")
        
    except Exception as e:
        logger.error("Failed to initialize Celery worker", error=str(e))
        raise


@worker_shutdown.connect
def worker_shutdown_handler(sender=None, **kwargs):
    """
    Worker shutdown handler.
    
    Performs cleanup of resources when a Celery worker shuts down,
    ensuring proper cleanup of GPU resources and database connections.
    """
    logger.info("Shutting down Celery worker")
    
    try:
        # Cleanup GPU resources
        gpu_task_manager = app_state.get('gpu_task_manager')
        if gpu_task_manager:
            gpu_task_manager.cleanup()
        
        # Close Redis connection
        redis_client = app_state.get('redis')
        if redis_client:
            redis_client.close()
        
        logger.info("Celery worker shutdown complete")
        
    except Exception as e:
        logger.error("Error during worker shutdown", error=str(e))


# Campaign Management Tasks
@celery_app.task(bind=True, name='tasks.campaign_tasks.process_pending_campaigns')
def process_pending_campaigns(self):
    """
    Process pending campaign executions with intelligent scheduling.
    
    Analyzes pending campaigns, optimizes execution timing, and initiates
    calls based on AI-driven optimization algorithms.
    """
    try:
        campaign_executor = app_state.get('campaign_executor')
        if not campaign_executor:
            raise Exception("Campaign executor not initialized")
        
        # Get pending campaigns
        pending_campaigns = campaign_executor.get_pending_campaigns()
        
        processed_count = 0
        for campaign in pending_campaigns:
            try:
                # Execute campaign with intelligent optimization
                result = campaign_executor.execute_campaign(campaign)
                
                if result.get('success'):
                    processed_count += 1
                    logger.info("Campaign processed successfully",
                               campaign_id=campaign.id,
                               calls_initiated=result.get('calls_initiated', 0))
                
            except Exception as e:
                logger.error("Campaign processing failed",
                           campaign_id=campaign.id,
                           error=str(e))
        
        return {
            'processed_campaigns': processed_count,
            'total_pending': len(pending_campaigns),
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Campaign processing task failed", error=str(e))
        raise self.retry(countdown=60, max_retries=3)


@celery_app.task(bind=True, name='tasks.sms_tasks.send_batch_sms')
def send_batch_sms(self):
    """
    Process batch SMS sending with intelligent modem distribution.
    
    Optimizes SMS distribution across available modems, handles delivery
    confirmations, and manages retry logic for failed messages.
    """
    try:
        sms_processor = app_state.get('sms_batch_processor')
        if not sms_processor:
            raise Exception("SMS batch processor not initialized")
        
        # Process pending SMS messages
        result = sms_processor.process_batch_sms()
        
        logger.info("SMS batch processing completed",
                   messages_sent=result.get('messages_sent', 0),
                   messages_failed=result.get('messages_failed', 0))
        
        return result
        
    except Exception as e:
        logger.error("SMS batch processing failed", error=str(e))
        raise self.retry(countdown=30, max_retries=5)


@celery_app.task(bind=True, name='tasks.analytics_tasks.update_real_time_analytics')
def update_real_time_analytics(self):
    """
    Update real-time analytics and business intelligence metrics.
    
    Processes recent call data, calculates KPIs, updates dashboards,
    and generates predictive insights for business optimization.
    """
    try:
        analytics_processor = app_state.get('analytics_processor')
        if not analytics_processor:
            raise Exception("Analytics processor not initialized")
        
        # Update real-time metrics
        result = analytics_processor.update_real_time_metrics()
        
        logger.info("Real-time analytics updated",
                   metrics_updated=result.get('metrics_updated', 0))
        
        return result
        
    except Exception as e:
        logger.error("Analytics update failed", error=str(e))
        raise self.retry(countdown=60, max_retries=3)


@celery_app.task(bind=True, name='tasks.analytics_tasks.complex_data_analysis')
def complex_data_analysis(self, analysis_type: str, data_params: Dict[str, Any]):
    """
    Perform complex data analysis using GPU acceleration.
    
    Executes sophisticated analytics operations including customer
    segmentation, churn prediction, and revenue optimization using
    GPU-accelerated machine learning algorithms.
    """
    try:
        analytics_processor = app_state.get('analytics_processor')
        gpu_manager = app_state.get('gpu_task_manager')
        
        if not analytics_processor:
            raise Exception("Analytics processor not initialized")
        
        # Perform GPU-accelerated analysis
        with gpu_manager.gpu_context() if gpu_manager else nullcontext():
            result = analytics_processor.perform_complex_analysis(
                analysis_type=analysis_type,
                params=data_params,
                use_gpu=gpu_manager is not None
            )
        
        logger.info("Complex data analysis completed",
                   analysis_type=analysis_type,
                   processing_time=result.get('processing_time'))
        
        return result
        
    except Exception as e:
        logger.error("Complex data analysis failed", error=str(e))
        raise self.retry(countdown=120, max_retries=2)


@celery_app.task(bind=True, name='tasks.revenue_tasks.optimize_revenue_strategies')
def optimize_revenue_strategies(self):
    """
    Optimize revenue generation strategies using AI algorithms.
    
    Analyzes conversion patterns, optimizes pricing strategies,
    and adjusts campaign parameters for maximum revenue generation.
    """
    try:
        revenue_optimizer = app_state.get('revenue_optimizer')
        if not revenue_optimizer:
            raise Exception("Revenue optimizer not initialized")
        
        # Perform revenue optimization
        result = revenue_optimizer.optimize_strategies()
        
        logger.info("Revenue optimization completed",
                   strategies_updated=result.get('strategies_updated', 0),
                   projected_improvement=result.get('projected_improvement', 0))
        
        return result
        
    except Exception as e:
        logger.error("Revenue optimization failed", error=str(e))
        raise self.retry(countdown=300, max_retries=2)


@celery_app.task(bind=True, name='tasks.ml_tasks.train_predictive_models')
def train_predictive_models(self):
    """
    Train machine learning models using GPU acceleration.
    
    Trains and updates predictive models for customer behavior,
    churn prediction, lead scoring, and revenue optimization
    using advanced GPU-accelerated machine learning techniques.
    """
    try:
        ml_trainer = app_state.get('ml_trainer')
        if not ml_trainer:
            raise Exception("ML trainer not initialized")
        
        # Train models with GPU acceleration
        result = ml_trainer.train_all_models()
        
        logger.info("ML model training completed",
                   models_trained=result.get('models_trained', 0),
                   training_time=result.get('training_time'))
        
        return result
        
    except Exception as e:
        logger.error("ML model training failed", error=str(e))
        raise self.retry(countdown=600, max_retries=1)


@celery_app.task(bind=True, name='tasks.analytics_tasks.generate_daily_reports')
def generate_daily_reports(self):
    """
    Generate comprehensive daily business reports.
    
    Creates detailed reports including revenue analytics, campaign
    performance, customer insights, and operational metrics.
    """
    try:
        report_generator = app_state.get('report_generator')
        if not report_generator:
            raise Exception("Report generator not initialized")
        
        # Generate daily reports
        result = report_generator.generate_daily_reports()
        
        logger.info("Daily reports generated",
                   reports_created=result.get('reports_created', 0))
        
        return result
        
    except Exception as e:
        logger.error("Daily report generation failed", error=str(e))
        raise self.retry(countdown=300, max_retries=2)


@celery_app.task(bind=True, name='tasks.maintenance_tasks.archive_old_data')
def archive_old_data(self):
    """
    Archive old data to optimize database performance.
    
    Moves historical data to archive storage while maintaining
    data integrity and accessibility for reporting purposes.
    """
    try:
        data_archiver = app_state.get('data_archiver')
        if not data_archiver:
            raise Exception("Data archiver not initialized")
        
        # Archive old data
        result = data_archiver.archive_old_data()
        
        logger.info("Data archiving completed",
                   records_archived=result.get('records_archived', 0))
        
        return result
        
    except Exception as e:
        logger.error("Data archiving failed", error=str(e))
        raise self.retry(countdown=600, max_retries=1)


@celery_app.task(bind=True, name='tasks.maintenance_tasks.cleanup_temp_files')
def cleanup_temp_files(self):
    """
    Clean up temporary files and optimize system resources.
    
    Removes temporary files, clears caches, and optimizes
    system performance for continued operation.
    """
    try:
        # Clean up temporary files
        temp_dirs = ['/tmp/voice-bridge', '/tmp/task-runner', '/tmp/reports']
        cleaned_files = 0
        
        for temp_dir in temp_dirs:
            if os.path.exists(temp_dir):
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # Remove files older than 24 hours
                        if os.path.getmtime(file_path) < time.time() - 86400:
                            os.remove(file_path)
                            cleaned_files += 1
        
        logger.info("Temporary file cleanup completed",
                   files_cleaned=cleaned_files)
        
        return {
            'files_cleaned': cleaned_files,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Temporary file cleanup failed", error=str(e))
        raise self.retry(countdown=300, max_retries=2)


def signal_handler(signum, frame):
    """
    Graceful shutdown signal handler.
    
    Ensures proper cleanup of resources when the task runner
    receives termination signals.
    """
    logger.info("Received shutdown signal", signal=signum)
    
    # Cleanup GPU resources
    gpu_manager = app_state.get('gpu_task_manager')
    if gpu_manager:
        gpu_manager.cleanup()
    
    sys.exit(0)


if __name__ == "__main__":
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start Celery worker
    celery_app.start()