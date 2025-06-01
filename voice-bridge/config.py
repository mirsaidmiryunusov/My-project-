"""
Voice-Bridge Configuration Module

This module provides comprehensive configuration management for the voice-bridge
microservice, implementing environment-based configuration with validation,
security best practices, and GPU-specific settings. The configuration system
supports development, testing, and production environments with appropriate
defaults and security measures.

The configuration architecture ensures type safety, validation, and secure
handling of sensitive credentials while providing extensive customization
options for performance tuning and feature enablement.
"""

import os
from typing import Optional, List, Dict, Any
from pathlib import Path

from pydantic import BaseSettings, Field, validator, SecretStr
from pydantic.networks import AnyHttpUrl, RedisDsn


class VoiceBridgeConfig(BaseSettings):
    """
    Comprehensive configuration class for voice-bridge microservice.
    
    Provides type-safe configuration management with validation, environment
    variable support, and secure credential handling. Includes GPU-specific
    settings, audio processing parameters, and integration configurations.
    """
    
    # Application Settings
    app_name: str = Field(
        default="voice-bridge",
        description="Application name for logging and monitoring"
    )
    
    app_version: str = Field(
        default="1.0.0",
        description="Application version"
    )
    
    environment: str = Field(
        default="development",
        description="Deployment environment (development, testing, production)"
    )
    
    debug: bool = Field(
        default=False,
        description="Enable debug mode for development"
    )
    
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    
    # Server Configuration
    host: str = Field(
        default="0.0.0.0",
        description="Server host address"
    )
    
    port: int = Field(
        default=8000,
        description="Server port number"
    )
    
    workers: int = Field(
        default=1,
        description="Number of worker processes"
    )
    
    # Security Configuration
    secret_key: SecretStr = Field(
        default="your-secret-key-change-in-production",
        description="Secret key for JWT token signing"
    )
    
    jwt_algorithm: str = Field(
        default="HS256",
        description="JWT signing algorithm"
    )
    
    jwt_expiration_hours: int = Field(
        default=24,
        description="JWT token expiration time in hours"
    )
    
    cors_origins: List[str] = Field(
        default=["*"],
        description="CORS allowed origins"
    )
    
    trusted_hosts: List[str] = Field(
        default=["*"],
        description="Trusted host names"
    )
    
    # Redis Configuration
    redis_url: RedisDsn = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )
    
    redis_max_connections: int = Field(
        default=20,
        description="Maximum Redis connection pool size"
    )
    
    redis_retry_on_timeout: bool = Field(
        default=True,
        description="Retry Redis operations on timeout"
    )
    
    # GPU Configuration
    gpu_enabled: bool = Field(
        default=True,
        description="Enable GPU acceleration"
    )
    
    gpu_device_id: int = Field(
        default=0,
        description="GPU device ID to use"
    )
    
    gpu_memory_fraction: float = Field(
        default=0.8,
        description="Fraction of GPU memory to allocate"
    )
    
    gpu_allow_growth: bool = Field(
        default=True,
        description="Allow GPU memory growth"
    )
    
    gpu_fallback_to_cpu: bool = Field(
        default=True,
        description="Fallback to CPU if GPU is unavailable"
    )
    
    # Audio Processing Configuration
    audio_sample_rate: int = Field(
        default=16000,
        description="Audio sample rate in Hz"
    )
    
    audio_channels: int = Field(
        default=1,
        description="Number of audio channels (1=mono, 2=stereo)"
    )
    
    audio_bit_depth: int = Field(
        default=16,
        description="Audio bit depth"
    )
    
    audio_chunk_size: int = Field(
        default=1024,
        description="Audio processing chunk size"
    )
    
    audio_buffer_size: int = Field(
        default=4096,
        description="Audio buffer size for streaming"
    )
    
    # Audio Enhancement Settings
    enable_aec: bool = Field(
        default=True,
        description="Enable Acoustic Echo Cancellation"
    )
    
    enable_nr: bool = Field(
        default=True,
        description="Enable Noise Reduction"
    )
    
    enable_agc: bool = Field(
        default=True,
        description="Enable Automatic Gain Control"
    )
    
    enable_vad: bool = Field(
        default=True,
        description="Enable Voice Activity Detection"
    )
    
    vad_aggressiveness: int = Field(
        default=2,
        description="VAD aggressiveness level (0-3)"
    )
    
    noise_reduction_strength: float = Field(
        default=0.7,
        description="Noise reduction strength (0.0-1.0)"
    )
    
    # Jitter Buffer Configuration
    jitter_buffer_min_delay: int = Field(
        default=20,
        description="Minimum jitter buffer delay in milliseconds"
    )
    
    jitter_buffer_max_delay: int = Field(
        default=200,
        description="Maximum jitter buffer delay in milliseconds"
    )
    
    jitter_buffer_target_delay: int = Field(
        default=60,
        description="Target jitter buffer delay in milliseconds"
    )
    
    adaptive_jitter_enabled: bool = Field(
        default=True,
        description="Enable adaptive jitter buffer algorithm"
    )
    
    # Gemini API Configuration
    gemini_api_key: SecretStr = Field(
        default="",
        description="Google Gemini API key"
    )
    
    gemini_model: str = Field(
        default="gemini-2.0-flash",
        description="Gemini model to use"
    )
    
    gemini_max_tokens: int = Field(
        default=2048,
        description="Maximum tokens for Gemini responses"
    )
    
    gemini_temperature: float = Field(
        default=0.7,
        description="Gemini response temperature"
    )
    
    gemini_timeout: int = Field(
        default=30,
        description="Gemini API timeout in seconds"
    )
    
    gemini_max_retries: int = Field(
        default=3,
        description="Maximum retry attempts for Gemini API"
    )
    
    # Edge-TTS Configuration
    edge_tts_voice: str = Field(
        default="en-US-AriaNeural",
        description="Default Edge-TTS voice"
    )
    
    edge_tts_rate: str = Field(
        default="+0%",
        description="Edge-TTS speech rate"
    )
    
    edge_tts_pitch: str = Field(
        default="+0Hz",
        description="Edge-TTS speech pitch"
    )
    
    edge_tts_volume: str = Field(
        default="+0%",
        description="Edge-TTS speech volume"
    )
    
    # NLU Configuration
    nlu_sentiment_threshold: float = Field(
        default=0.6,
        description="Sentiment classification confidence threshold"
    )
    
    nlu_intent_threshold: float = Field(
        default=0.7,
        description="Intent classification confidence threshold"
    )
    
    nlu_entity_threshold: float = Field(
        default=0.5,
        description="Entity extraction confidence threshold"
    )
    
    nlu_context_window: int = Field(
        default=10,
        description="Number of previous messages to consider for context"
    )
    
    nlu_batch_size: int = Field(
        default=32,
        description="Batch size for NLU processing"
    )
    
    # Performance Configuration
    max_concurrent_connections: int = Field(
        default=100,
        description="Maximum concurrent WebSocket connections"
    )
    
    connection_timeout: int = Field(
        default=300,
        description="WebSocket connection timeout in seconds"
    )
    
    processing_timeout: int = Field(
        default=30,
        description="Audio processing timeout in seconds"
    )
    
    max_audio_duration: int = Field(
        default=300,
        description="Maximum audio duration in seconds"
    )
    
    # Monitoring Configuration
    metrics_enabled: bool = Field(
        default=True,
        description="Enable Prometheus metrics collection"
    )
    
    metrics_port: int = Field(
        default=9090,
        description="Prometheus metrics port"
    )
    
    health_check_interval: int = Field(
        default=30,
        description="Health check interval in seconds"
    )
    
    # Storage Configuration
    temp_audio_dir: Path = Field(
        default=Path("/tmp/voice-bridge/audio"),
        description="Temporary audio storage directory"
    )
    
    max_temp_files: int = Field(
        default=1000,
        description="Maximum number of temporary files"
    )
    
    temp_file_ttl: int = Field(
        default=3600,
        description="Temporary file TTL in seconds"
    )
    
    # Advanced Features Configuration
    enable_audio_fingerprinting: bool = Field(
        default=True,
        description="Enable audio fingerprinting for caller identification"
    )
    
    enable_emotion_detection: bool = Field(
        default=True,
        description="Enable emotional state detection"
    )
    
    enable_predictive_responses: bool = Field(
        default=True,
        description="Enable predictive response generation"
    )
    
    enable_multilingual_support: bool = Field(
        default=True,
        description="Enable multi-language processing"
    )
    
    supported_languages: List[str] = Field(
        default=["en", "es", "fr", "de", "it", "pt", "ru", "zh", "ja", "ko"],
        description="List of supported language codes"
    )
    
    # Experimental Features
    enable_experimental_features: bool = Field(
        default=False,
        description="Enable experimental features"
    )
    
    experimental_gpu_optimization: bool = Field(
        default=False,
        description="Enable experimental GPU optimizations"
    )
    
    experimental_neural_enhancement: bool = Field(
        default=False,
        description="Enable experimental neural audio enhancement"
    )
    
    @validator('environment')
    def validate_environment(cls, v):
        """Validate environment setting."""
        allowed_environments = ['development', 'testing', 'production']
        if v not in allowed_environments:
            raise ValueError(f'Environment must be one of {allowed_environments}')
        return v
    
    @validator('log_level')
    def validate_log_level(cls, v):
        """Validate log level setting."""
        allowed_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in allowed_levels:
            raise ValueError(f'Log level must be one of {allowed_levels}')
        return v.upper()
    
    @validator('vad_aggressiveness')
    def validate_vad_aggressiveness(cls, v):
        """Validate VAD aggressiveness level."""
        if not 0 <= v <= 3:
            raise ValueError('VAD aggressiveness must be between 0 and 3')
        return v
    
    @validator('gpu_memory_fraction')
    def validate_gpu_memory_fraction(cls, v):
        """Validate GPU memory fraction."""
        if not 0.1 <= v <= 1.0:
            raise ValueError('GPU memory fraction must be between 0.1 and 1.0')
        return v
    
    @validator('noise_reduction_strength')
    def validate_noise_reduction_strength(cls, v):
        """Validate noise reduction strength."""
        if not 0.0 <= v <= 1.0:
            raise ValueError('Noise reduction strength must be between 0.0 and 1.0')
        return v
    
    @validator('temp_audio_dir')
    def validate_temp_audio_dir(cls, v):
        """Ensure temporary audio directory exists."""
        v.mkdir(parents=True, exist_ok=True)
        return v
    
    def get_gpu_config(self) -> Dict[str, Any]:
        """
        Get GPU-specific configuration settings.
        
        Returns:
            Dict containing GPU configuration parameters
        """
        return {
            'enabled': self.gpu_enabled,
            'device_id': self.gpu_device_id,
            'memory_fraction': self.gpu_memory_fraction,
            'allow_growth': self.gpu_allow_growth,
            'fallback_to_cpu': self.gpu_fallback_to_cpu
        }
    
    def get_audio_config(self) -> Dict[str, Any]:
        """
        Get audio processing configuration settings.
        
        Returns:
            Dict containing audio processing parameters
        """
        return {
            'sample_rate': self.audio_sample_rate,
            'channels': self.audio_channels,
            'bit_depth': self.audio_bit_depth,
            'chunk_size': self.audio_chunk_size,
            'buffer_size': self.audio_buffer_size,
            'enable_aec': self.enable_aec,
            'enable_nr': self.enable_nr,
            'enable_agc': self.enable_agc,
            'enable_vad': self.enable_vad,
            'vad_aggressiveness': self.vad_aggressiveness,
            'noise_reduction_strength': self.noise_reduction_strength
        }
    
    def get_jitter_buffer_config(self) -> Dict[str, Any]:
        """
        Get jitter buffer configuration settings.
        
        Returns:
            Dict containing jitter buffer parameters
        """
        return {
            'min_delay': self.jitter_buffer_min_delay,
            'max_delay': self.jitter_buffer_max_delay,
            'target_delay': self.jitter_buffer_target_delay,
            'adaptive_enabled': self.adaptive_jitter_enabled
        }
    
    def get_nlu_config(self) -> Dict[str, Any]:
        """
        Get NLU processing configuration settings.
        
        Returns:
            Dict containing NLU processing parameters
        """
        return {
            'sentiment_threshold': self.nlu_sentiment_threshold,
            'intent_threshold': self.nlu_intent_threshold,
            'entity_threshold': self.nlu_entity_threshold,
            'context_window': self.nlu_context_window,
            'batch_size': self.nlu_batch_size
        }
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"
    
    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.environment == "testing"
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        validate_assignment = True
        extra = "forbid"