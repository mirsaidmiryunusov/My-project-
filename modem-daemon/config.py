"""
Modem-Daemon Configuration Module

This module provides comprehensive configuration management for the modem-daemon
microservice, implementing type-safe configuration loading, validation, and
hardware-specific settings for SIM900 modem management.
"""

import os
from typing import Optional, Dict, Any, List
from pydantic import BaseSettings, validator, Field
from pydantic_settings import BaseSettings as PydanticBaseSettings


class ModemDaemonConfig(PydanticBaseSettings):
    """
    Comprehensive configuration class for modem-daemon microservice.
    
    Provides type-safe configuration management with validation,
    environment variable loading, and hardware-specific settings
    for SIM900 modem operations.
    """
    
    # Application Settings
    app_name: str = Field(default="GeminiVoiceConnect Modem-Daemon", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    
    # Modem Identification
    modem_id: str = Field(..., description="Unique modem identifier")
    modem_device: str = Field(..., description="Modem device path (e.g., /dev/ttyUSB0)")
    
    # Server Configuration
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8002, description="Server port")
    
    # Hardware Configuration
    baudrate: int = Field(default=115200, description="Serial communication baud rate")
    timeout: float = Field(default=5.0, description="Serial communication timeout")
    data_bits: int = Field(default=8, description="Serial data bits")
    stop_bits: int = Field(default=1, description="Serial stop bits")
    parity: str = Field(default="N", description="Serial parity (N/E/O)")
    
    # AT Command Configuration
    at_command_timeout: float = Field(default=10.0, description="AT command timeout")
    at_command_retries: int = Field(default=3, description="AT command retry attempts")
    initialization_timeout: float = Field(default=30.0, description="Modem initialization timeout")
    
    # Audio Configuration
    audio_sample_rate: int = Field(default=8000, description="Audio sample rate")
    audio_channels: int = Field(default=1, description="Audio channels (mono)")
    audio_chunk_size: int = Field(default=1024, description="Audio chunk size")
    audio_format: str = Field(default="PCM_16", description="Audio format")
    
    # Call Management
    max_call_duration: int = Field(default=3600, description="Maximum call duration in seconds")
    call_timeout: int = Field(default=60, description="Call connection timeout")
    dtmf_duration: float = Field(default=0.1, description="DTMF tone duration")
    dtmf_pause: float = Field(default=0.1, description="DTMF pause duration")
    
    # SMS Configuration
    sms_timeout: float = Field(default=30.0, description="SMS operation timeout")
    sms_retry_attempts: int = Field(default=3, description="SMS retry attempts")
    sms_max_length: int = Field(default=160, description="Maximum SMS length")
    
    # Network Configuration
    network_registration_timeout: float = Field(default=60.0, description="Network registration timeout")
    signal_strength_threshold: int = Field(default=10, description="Minimum signal strength")
    
    # External Services
    redis_url: str = Field(default="redis://redis:6379/3", description="Redis connection URL")
    core_api_url: str = Field(default="http://core-api:8001", description="Core-API service URL")
    voice_bridge_url: str = Field(default="http://voice-bridge:8000", description="Voice-bridge service URL")
    
    # Health Monitoring
    health_check_interval: int = Field(default=30, description="Health check interval in seconds")
    signal_check_interval: int = Field(default=60, description="Signal strength check interval")
    temperature_check_interval: int = Field(default=300, description="Temperature check interval")
    
    # Performance Configuration
    command_queue_size: int = Field(default=100, description="AT command queue size")
    event_buffer_size: int = Field(default=1000, description="Event buffer size")
    log_rotation_size: int = Field(default=10 * 1024 * 1024, description="Log rotation size in bytes")
    
    # Error Handling
    max_consecutive_errors: int = Field(default=5, description="Maximum consecutive errors before reset")
    error_recovery_delay: float = Field(default=5.0, description="Error recovery delay in seconds")
    modem_reset_timeout: float = Field(default=30.0, description="Modem reset timeout")
    
    # Security Configuration
    enable_encryption: bool = Field(default=True, description="Enable audio encryption")
    encryption_key: Optional[str] = Field(default=None, description="Encryption key")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format (json/text)")
    enable_call_logging: bool = Field(default=True, description="Enable call event logging")
    enable_sms_logging: bool = Field(default=True, description="Enable SMS event logging")
    
    # Feature Flags
    enable_voice_calls: bool = Field(default=True, description="Enable voice call functionality")
    enable_sms: bool = Field(default=True, description="Enable SMS functionality")
    enable_ussd: bool = Field(default=False, description="Enable USSD functionality")
    enable_data: bool = Field(default=False, description="Enable data connection")
    
    # Advanced Features
    enable_echo_cancellation: bool = Field(default=True, description="Enable echo cancellation")
    enable_noise_reduction: bool = Field(default=True, description="Enable noise reduction")
    enable_automatic_gain_control: bool = Field(default=True, description="Enable AGC")
    enable_voice_activity_detection: bool = Field(default=True, description="Enable VAD")
    
    @validator('modem_device')
    def validate_modem_device(cls, v):
        """Validate modem device path."""
        if not v.startswith('/dev/'):
            raise ValueError('Modem device must be a valid device path starting with /dev/')
        return v
    
    @validator('baudrate')
    def validate_baudrate(cls, v):
        """Validate baud rate."""
        valid_rates = [9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600]
        if v not in valid_rates:
            raise ValueError(f'Baud rate must be one of: {valid_rates}')
        return v
    
    @validator('parity')
    def validate_parity(cls, v):
        """Validate parity setting."""
        if v.upper() not in ['N', 'E', 'O']:
            raise ValueError('Parity must be N (None), E (Even), or O (Odd)')
        return v.upper()
    
    @validator('log_level')
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of: {valid_levels}')
        return v.upper()
    
    @validator('audio_sample_rate')
    def validate_sample_rate(cls, v):
        """Validate audio sample rate."""
        valid_rates = [8000, 16000, 22050, 44100, 48000]
        if v not in valid_rates:
            raise ValueError(f'Sample rate must be one of: {valid_rates}')
        return v
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    def get_serial_config(self) -> Dict[str, Any]:
        """Get serial port configuration."""
        return {
            'port': self.modem_device,
            'baudrate': self.baudrate,
            'timeout': self.timeout,
            'bytesize': self.data_bits,
            'stopbits': self.stop_bits,
            'parity': self.parity,
            'rtscts': False,
            'dsrdtr': False
        }
    
    def get_audio_config(self) -> Dict[str, Any]:
        """Get audio configuration."""
        return {
            'sample_rate': self.audio_sample_rate,
            'channels': self.audio_channels,
            'chunk_size': self.audio_chunk_size,
            'format': self.audio_format
        }
    
    def get_at_config(self) -> Dict[str, Any]:
        """Get AT command configuration."""
        return {
            'timeout': self.at_command_timeout,
            'retries': self.at_command_retries,
            'initialization_timeout': self.initialization_timeout
        }
    
    def get_health_config(self) -> Dict[str, Any]:
        """Get health monitoring configuration."""
        return {
            'health_check_interval': self.health_check_interval,
            'signal_check_interval': self.signal_check_interval,
            'temperature_check_interval': self.temperature_check_interval,
            'signal_threshold': self.signal_strength_threshold
        }
    
    def get_feature_flags(self) -> Dict[str, bool]:
        """Get feature flags."""
        return {
            'voice_calls': self.enable_voice_calls,
            'sms': self.enable_sms,
            'ussd': self.enable_ussd,
            'data': self.enable_data,
            'echo_cancellation': self.enable_echo_cancellation,
            'noise_reduction': self.enable_noise_reduction,
            'automatic_gain_control': self.enable_automatic_gain_control,
            'voice_activity_detection': self.enable_voice_activity_detection
        }
    
    def is_feature_enabled(self, feature: str) -> bool:
        """Check if a feature is enabled."""
        feature_flags = self.get_feature_flags()
        return feature_flags.get(feature, False)