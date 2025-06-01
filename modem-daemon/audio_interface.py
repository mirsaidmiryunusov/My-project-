"""
Audio Interface Module

This module implements comprehensive audio interface functionality for
SIM900 modems, providing high-quality audio capture, playback, and
processing for Project GeminiVoiceConnect voice communications.
"""

import asyncio
import threading
import time
import wave
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable, Tuple
from enum import Enum
from dataclasses import dataclass

import pyaudio
import numpy as np
from scipy import signal
from scipy.io import wavfile
import structlog

from config import ModemDaemonConfig


logger = structlog.get_logger(__name__)


class AudioState(str, Enum):
    """Audio interface state."""
    IDLE = "idle"
    RECORDING = "recording"
    PLAYING = "playing"
    PROCESSING = "processing"
    ERROR = "error"


class AudioFormat(str, Enum):
    """Audio format enumeration."""
    PCM_16 = "pcm_16"
    PCM_24 = "pcm_24"
    PCM_32 = "pcm_32"
    FLOAT_32 = "float_32"


@dataclass
class AudioConfig:
    """Audio configuration container."""
    sample_rate: int
    channels: int
    chunk_size: int
    format: AudioFormat
    device_index: Optional[int] = None


@dataclass
class AudioBuffer:
    """Audio buffer container."""
    data: np.ndarray
    timestamp: datetime
    sample_rate: int
    channels: int
    duration_seconds: float
    
    def to_bytes(self) -> bytes:
        """Convert audio data to bytes."""
        if self.data.dtype == np.float32:
            # Convert float32 to int16
            audio_int16 = (self.data * 32767).astype(np.int16)
            return audio_int16.tobytes()
        return self.data.tobytes()
    
    def save_to_file(self, filename: str) -> None:
        """Save audio buffer to WAV file."""
        try:
            if self.data.dtype == np.float32:
                # Convert float32 to int16 for WAV
                audio_int16 = (self.data * 32767).astype(np.int16)
            else:
                audio_int16 = self.data
            
            wavfile.write(filename, self.sample_rate, audio_int16)
            logger.debug("Audio saved to file", filename=filename)
            
        except Exception as e:
            logger.error("Failed to save audio file", filename=filename, error=str(e))


class AudioProcessor:
    """
    Advanced audio processing for voice enhancement.
    
    Provides echo cancellation, noise reduction, automatic gain control,
    and voice activity detection for optimal call quality.
    """
    
    def __init__(self, config: ModemDaemonConfig):
        """
        Initialize audio processor.
        
        Args:
            config: Modem daemon configuration
        """
        self.config = config
        self.sample_rate = config.audio_sample_rate
        
        # Processing parameters
        self.frame_size = 512
        self.hop_size = 256
        self.noise_floor = -40  # dB
        self.vad_threshold = 0.02
        
        # Filters and buffers
        self.noise_profile = None
        self.echo_buffer = np.zeros(self.sample_rate)  # 1 second buffer
        self.gain_history = []
        
        # Initialize filters
        self._initialize_filters()
    
    def _initialize_filters(self) -> None:
        """Initialize audio processing filters."""
        # High-pass filter for removing DC offset
        self.highpass_filter = signal.butter(
            4, 80, btype='high', fs=self.sample_rate, output='sos'
        )
        
        # Low-pass filter for anti-aliasing
        self.lowpass_filter = signal.butter(
            4, self.sample_rate // 2 - 1000, btype='low', fs=self.sample_rate, output='sos'
        )
        
        # Notch filter for 50/60 Hz noise
        self.notch_filter = signal.iirnotch(50, 30, fs=self.sample_rate)
    
    def process_audio(self, audio_data: np.ndarray, 
                     enable_aec: bool = True,
                     enable_nr: bool = True,
                     enable_agc: bool = True,
                     enable_vad: bool = True) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Process audio with advanced algorithms.
        
        Args:
            audio_data: Input audio data
            enable_aec: Enable echo cancellation
            enable_nr: Enable noise reduction
            enable_agc: Enable automatic gain control
            enable_vad: Enable voice activity detection
            
        Returns:
            Processed audio data and metadata
        """
        try:
            processed_audio = audio_data.copy()
            metadata = {}
            
            # Apply high-pass filter
            processed_audio = signal.sosfilt(self.highpass_filter, processed_audio)
            
            # Echo cancellation
            if enable_aec:
                processed_audio, aec_info = self._apply_echo_cancellation(processed_audio)
                metadata['echo_cancellation'] = aec_info
            
            # Noise reduction
            if enable_nr:
                processed_audio, nr_info = self._apply_noise_reduction(processed_audio)
                metadata['noise_reduction'] = nr_info
            
            # Automatic gain control
            if enable_agc:
                processed_audio, agc_info = self._apply_automatic_gain_control(processed_audio)
                metadata['automatic_gain_control'] = agc_info
            
            # Voice activity detection
            if enable_vad:
                vad_result = self._detect_voice_activity(processed_audio)
                metadata['voice_activity'] = vad_result
            
            # Apply low-pass filter
            processed_audio = signal.sosfilt(self.lowpass_filter, processed_audio)
            
            # Calculate quality metrics
            metadata['quality_metrics'] = self._calculate_quality_metrics(
                audio_data, processed_audio
            )
            
            return processed_audio, metadata
            
        except Exception as e:
            logger.error("Audio processing failed", error=str(e))
            return audio_data, {'error': str(e)}
    
    def _apply_echo_cancellation(self, audio_data: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Apply echo cancellation algorithm."""
        try:
            # Simple adaptive echo cancellation
            # In production, would use more sophisticated algorithms like NLMS or RLS
            
            # Update echo buffer
            if len(audio_data) <= len(self.echo_buffer):
                self.echo_buffer[:-len(audio_data)] = self.echo_buffer[len(audio_data):]
                self.echo_buffer[-len(audio_data):] = audio_data
            
            # Estimate echo using correlation
            correlation = np.correlate(audio_data, self.echo_buffer, mode='valid')
            echo_delay = np.argmax(np.abs(correlation))
            
            # Apply echo cancellation
            if echo_delay > 0 and echo_delay < len(audio_data):
                echo_estimate = 0.3 * np.roll(audio_data, echo_delay)
                processed_audio = audio_data - echo_estimate
            else:
                processed_audio = audio_data
            
            aec_info = {
                'echo_delay_samples': int(echo_delay),
                'echo_delay_ms': float(echo_delay / self.sample_rate * 1000),
                'echo_reduction_db': float(20 * np.log10(np.std(audio_data) / np.std(processed_audio)))
            }
            
            return processed_audio, aec_info
            
        except Exception as e:
            logger.error("Echo cancellation failed", error=str(e))
            return audio_data, {'error': str(e)}
    
    def _apply_noise_reduction(self, audio_data: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Apply noise reduction algorithm."""
        try:
            # Spectral subtraction noise reduction
            
            # Convert to frequency domain
            fft_data = np.fft.fft(audio_data)
            magnitude = np.abs(fft_data)
            phase = np.angle(fft_data)
            
            # Estimate noise floor if not available
            if self.noise_profile is None:
                self.noise_profile = magnitude * 0.1  # Initial estimate
            else:
                # Update noise profile during silence
                if np.max(magnitude) < np.mean(self.noise_profile) * 2:
                    self.noise_profile = 0.9 * self.noise_profile + 0.1 * magnitude
            
            # Apply spectral subtraction
            alpha = 2.0  # Over-subtraction factor
            beta = 0.01  # Spectral floor
            
            noise_power = self.noise_profile ** 2
            signal_power = magnitude ** 2
            
            # Calculate gain
            gain = 1 - alpha * (noise_power / signal_power)
            gain = np.maximum(gain, beta)
            
            # Apply gain
            processed_magnitude = magnitude * gain
            
            # Convert back to time domain
            processed_fft = processed_magnitude * np.exp(1j * phase)
            processed_audio = np.real(np.fft.ifft(processed_fft))
            
            nr_info = {
                'noise_floor_db': float(20 * np.log10(np.mean(self.noise_profile))),
                'snr_improvement_db': float(20 * np.log10(np.std(processed_audio) / np.std(audio_data))),
                'noise_reduction_applied': True
            }
            
            return processed_audio, nr_info
            
        except Exception as e:
            logger.error("Noise reduction failed", error=str(e))
            return audio_data, {'error': str(e)}
    
    def _apply_automatic_gain_control(self, audio_data: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Apply automatic gain control."""
        try:
            # Calculate RMS level
            rms_level = np.sqrt(np.mean(audio_data ** 2))
            
            # Target RMS level (normalized)
            target_rms = 0.1
            
            # Calculate required gain
            if rms_level > 0:
                required_gain = target_rms / rms_level
            else:
                required_gain = 1.0
            
            # Limit gain range
            max_gain = 10.0
            min_gain = 0.1
            required_gain = np.clip(required_gain, min_gain, max_gain)
            
            # Smooth gain changes
            if self.gain_history:
                smoothing_factor = 0.1
                smoothed_gain = (1 - smoothing_factor) * self.gain_history[-1] + smoothing_factor * required_gain
            else:
                smoothed_gain = required_gain
            
            # Update gain history
            self.gain_history.append(smoothed_gain)
            if len(self.gain_history) > 100:
                self.gain_history.pop(0)
            
            # Apply gain
            processed_audio = audio_data * smoothed_gain
            
            # Prevent clipping
            max_amplitude = np.max(np.abs(processed_audio))
            if max_amplitude > 0.95:
                processed_audio = processed_audio * (0.95 / max_amplitude)
            
            agc_info = {
                'input_rms_db': float(20 * np.log10(rms_level)) if rms_level > 0 else -60,
                'output_rms_db': float(20 * np.log10(np.sqrt(np.mean(processed_audio ** 2)))),
                'gain_applied_db': float(20 * np.log10(smoothed_gain)),
                'clipping_applied': max_amplitude > 0.95
            }
            
            return processed_audio, agc_info
            
        except Exception as e:
            logger.error("Automatic gain control failed", error=str(e))
            return audio_data, {'error': str(e)}
    
    def _detect_voice_activity(self, audio_data: np.ndarray) -> Dict[str, Any]:
        """Detect voice activity in audio."""
        try:
            # Calculate energy
            energy = np.sum(audio_data ** 2) / len(audio_data)
            
            # Calculate zero crossing rate
            zero_crossings = np.sum(np.diff(np.sign(audio_data)) != 0)
            zcr = zero_crossings / len(audio_data)
            
            # Calculate spectral centroid
            fft_data = np.fft.fft(audio_data)
            magnitude = np.abs(fft_data[:len(fft_data)//2])
            freqs = np.fft.fftfreq(len(audio_data), 1/self.sample_rate)[:len(magnitude)]
            
            if np.sum(magnitude) > 0:
                spectral_centroid = np.sum(freqs * magnitude) / np.sum(magnitude)
            else:
                spectral_centroid = 0
            
            # Voice activity decision
            voice_detected = (
                energy > self.vad_threshold and
                zcr > 0.01 and zcr < 0.3 and
                spectral_centroid > 200 and spectral_centroid < 4000
            )
            
            vad_info = {
                'voice_detected': bool(voice_detected),
                'energy': float(energy),
                'zero_crossing_rate': float(zcr),
                'spectral_centroid': float(spectral_centroid),
                'confidence': float(min(energy / self.vad_threshold, 1.0))
            }
            
            return vad_info
            
        except Exception as e:
            logger.error("Voice activity detection failed", error=str(e))
            return {'voice_detected': False, 'error': str(e)}
    
    def _calculate_quality_metrics(self, original: np.ndarray, processed: np.ndarray) -> Dict[str, Any]:
        """Calculate audio quality metrics."""
        try:
            # Signal-to-noise ratio
            signal_power = np.mean(processed ** 2)
            noise_power = np.mean((original - processed) ** 2)
            
            if noise_power > 0:
                snr_db = 10 * np.log10(signal_power / noise_power)
            else:
                snr_db = 60  # Very high SNR
            
            # Total harmonic distortion
            fft_processed = np.fft.fft(processed)
            magnitude = np.abs(fft_processed)
            
            # Find fundamental frequency (simplified)
            fundamental_idx = np.argmax(magnitude[1:len(magnitude)//4]) + 1
            fundamental_power = magnitude[fundamental_idx] ** 2
            
            # Calculate harmonic power
            harmonic_power = 0
            for harmonic in range(2, 6):  # 2nd to 5th harmonics
                harmonic_idx = fundamental_idx * harmonic
                if harmonic_idx < len(magnitude):
                    harmonic_power += magnitude[harmonic_idx] ** 2
            
            if fundamental_power > 0:
                thd = np.sqrt(harmonic_power / fundamental_power)
            else:
                thd = 0
            
            # Dynamic range
            max_amplitude = np.max(np.abs(processed))
            min_amplitude = np.min(np.abs(processed[np.abs(processed) > 0]))
            
            if min_amplitude > 0:
                dynamic_range_db = 20 * np.log10(max_amplitude / min_amplitude)
            else:
                dynamic_range_db = 60
            
            quality_metrics = {
                'snr_db': float(snr_db),
                'thd_percent': float(thd * 100),
                'dynamic_range_db': float(dynamic_range_db),
                'peak_amplitude': float(max_amplitude),
                'rms_level': float(np.sqrt(np.mean(processed ** 2)))
            }
            
            return quality_metrics
            
        except Exception as e:
            logger.error("Quality metrics calculation failed", error=str(e))
            return {'error': str(e)}


class AudioInterface:
    """
    Comprehensive audio interface for SIM900 modems.
    
    Provides high-quality audio capture, playback, and real-time
    processing for voice communications with advanced audio
    enhancement and monitoring capabilities.
    """
    
    def __init__(self, config: ModemDaemonConfig):
        """
        Initialize audio interface.
        
        Args:
            config: Modem daemon configuration
        """
        self.config = config
        self.audio_config = AudioConfig(
            sample_rate=config.audio_sample_rate,
            channels=config.audio_channels,
            chunk_size=config.audio_chunk_size,
            format=AudioFormat(config.audio_format)
        )
        
        # PyAudio instance
        self.pyaudio = None
        self.input_stream = None
        self.output_stream = None
        
        # Audio processor
        self.processor = AudioProcessor(config)
        
        # State management
        self.state = AudioState.IDLE
        self.recording_active = False
        self.playback_active = False
        
        # Buffers and callbacks
        self.audio_buffers = []
        self.audio_callback = None
        self.max_buffer_size = 100
        
        # Threading
        self.audio_thread = None
        self.stop_event = threading.Event()
        
        # Statistics
        self.stats = {
            'total_recorded_seconds': 0,
            'total_played_seconds': 0,
            'buffer_overruns': 0,
            'buffer_underruns': 0,
            'processing_errors': 0
        }
    
    async def initialize(self) -> bool:
        """
        Initialize audio interface and detect devices.
        
        Returns:
            True if initialization successful
        """
        try:
            logger.info("Initializing audio interface", modem_id=self.config.modem_id)
            
            # Initialize PyAudio
            self.pyaudio = pyaudio.PyAudio()
            
            # Detect and configure audio devices
            if not await self._detect_audio_devices():
                return False
            
            # Test audio functionality
            if not await self._test_audio_functionality():
                return False
            
            self.state = AudioState.IDLE
            
            logger.info("Audio interface initialized successfully",
                       modem_id=self.config.modem_id,
                       sample_rate=self.audio_config.sample_rate,
                       channels=self.audio_config.channels)
            
            return True
            
        except Exception as e:
            logger.error("Audio interface initialization failed",
                        modem_id=self.config.modem_id,
                        error=str(e))
            self.state = AudioState.ERROR
            return False
    
    async def _detect_audio_devices(self) -> bool:
        """Detect and configure audio devices."""
        try:
            device_count = self.pyaudio.get_device_count()
            logger.info("Detecting audio devices", device_count=device_count)
            
            input_device = None
            output_device = None
            
            for i in range(device_count):
                device_info = self.pyaudio.get_device_info_by_index(i)
                
                logger.debug("Audio device found",
                           index=i,
                           name=device_info['name'],
                           channels=device_info['maxInputChannels'],
                           sample_rate=device_info['defaultSampleRate'])
                
                # Look for USB audio devices (likely connected to modem)
                if 'USB' in device_info['name'].upper() or 'MODEM' in device_info['name'].upper():
                    if device_info['maxInputChannels'] > 0 and input_device is None:
                        input_device = i
                    if device_info['maxOutputChannels'] > 0 and output_device is None:
                        output_device = i
            
            # Use default devices if USB devices not found
            if input_device is None:
                input_device = self.pyaudio.get_default_input_device_info()['index']
            if output_device is None:
                output_device = self.pyaudio.get_default_output_device_info()['index']
            
            self.input_device_index = input_device
            self.output_device_index = output_device
            
            logger.info("Audio devices configured",
                       input_device=input_device,
                       output_device=output_device)
            
            return True
            
        except Exception as e:
            logger.error("Audio device detection failed", error=str(e))
            return False
    
    async def _test_audio_functionality(self) -> bool:
        """Test basic audio functionality."""
        try:
            # Test input stream
            test_stream = self.pyaudio.open(
                format=self._get_pyaudio_format(),
                channels=self.audio_config.channels,
                rate=self.audio_config.sample_rate,
                input=True,
                input_device_index=self.input_device_index,
                frames_per_buffer=self.audio_config.chunk_size
            )
            
            # Record a small test sample
            test_data = test_stream.read(self.audio_config.chunk_size)
            test_stream.close()
            
            # Test output stream
            test_stream = self.pyaudio.open(
                format=self._get_pyaudio_format(),
                channels=self.audio_config.channels,
                rate=self.audio_config.sample_rate,
                output=True,
                output_device_index=self.output_device_index,
                frames_per_buffer=self.audio_config.chunk_size
            )
            
            # Play silence
            silence = b'\x00' * len(test_data)
            test_stream.write(silence)
            test_stream.close()
            
            logger.info("Audio functionality test passed")
            return True
            
        except Exception as e:
            logger.error("Audio functionality test failed", error=str(e))
            return False
    
    def start_recording(self, callback: Optional[Callable[[AudioBuffer], None]] = None) -> bool:
        """
        Start audio recording.
        
        Args:
            callback: Optional callback for audio data
            
        Returns:
            True if recording started successfully
        """
        try:
            if self.recording_active:
                logger.warning("Recording already active")
                return True
            
            self.audio_callback = callback
            self.stop_event.clear()
            
            # Create input stream
            self.input_stream = self.pyaudio.open(
                format=self._get_pyaudio_format(),
                channels=self.audio_config.channels,
                rate=self.audio_config.sample_rate,
                input=True,
                input_device_index=self.input_device_index,
                frames_per_buffer=self.audio_config.chunk_size,
                stream_callback=self._input_callback
            )
            
            self.input_stream.start_stream()
            self.recording_active = True
            self.state = AudioState.RECORDING
            
            logger.info("Audio recording started", modem_id=self.config.modem_id)
            return True
            
        except Exception as e:
            logger.error("Failed to start recording", error=str(e))
            self.state = AudioState.ERROR
            return False
    
    def stop_recording(self) -> bool:
        """
        Stop audio recording.
        
        Returns:
            True if recording stopped successfully
        """
        try:
            if not self.recording_active:
                return True
            
            self.recording_active = False
            self.stop_event.set()
            
            if self.input_stream:
                self.input_stream.stop_stream()
                self.input_stream.close()
                self.input_stream = None
            
            self.state = AudioState.IDLE
            
            logger.info("Audio recording stopped", modem_id=self.config.modem_id)
            return True
            
        except Exception as e:
            logger.error("Failed to stop recording", error=str(e))
            return False
    
    def start_playback(self, audio_data: bytes) -> bool:
        """
        Start audio playback.
        
        Args:
            audio_data: Audio data to play
            
        Returns:
            True if playback started successfully
        """
        try:
            if self.playback_active:
                logger.warning("Playback already active")
                return False
            
            # Create output stream
            self.output_stream = self.pyaudio.open(
                format=self._get_pyaudio_format(),
                channels=self.audio_config.channels,
                rate=self.audio_config.sample_rate,
                output=True,
                output_device_index=self.output_device_index,
                frames_per_buffer=self.audio_config.chunk_size
            )
            
            self.playback_active = True
            self.state = AudioState.PLAYING
            
            # Start playback in separate thread
            self.audio_thread = threading.Thread(
                target=self._playback_thread,
                args=(audio_data,)
            )
            self.audio_thread.start()
            
            logger.info("Audio playback started", modem_id=self.config.modem_id)
            return True
            
        except Exception as e:
            logger.error("Failed to start playback", error=str(e))
            self.state = AudioState.ERROR
            return False
    
    def stop_playback(self) -> bool:
        """
        Stop audio playback.
        
        Returns:
            True if playback stopped successfully
        """
        try:
            if not self.playback_active:
                return True
            
            self.playback_active = False
            self.stop_event.set()
            
            if self.audio_thread:
                self.audio_thread.join(timeout=5.0)
            
            if self.output_stream:
                self.output_stream.stop_stream()
                self.output_stream.close()
                self.output_stream = None
            
            self.state = AudioState.IDLE
            
            logger.info("Audio playback stopped", modem_id=self.config.modem_id)
            return True
            
        except Exception as e:
            logger.error("Failed to stop playback", error=str(e))
            return False
    
    def _input_callback(self, in_data, frame_count, time_info, status):
        """PyAudio input stream callback."""
        try:
            if status:
                logger.warning("Audio input status", status=status)
                self.stats['buffer_overruns'] += 1
            
            # Convert bytes to numpy array
            audio_array = np.frombuffer(in_data, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Process audio
            if self.config.enable_echo_cancellation or self.config.enable_noise_reduction:
                self.state = AudioState.PROCESSING
                processed_audio, metadata = self.processor.process_audio(
                    audio_array,
                    enable_aec=self.config.enable_echo_cancellation,
                    enable_nr=self.config.enable_noise_reduction,
                    enable_agc=self.config.enable_automatic_gain_control,
                    enable_vad=self.config.enable_voice_activity_detection
                )
                self.state = AudioState.RECORDING
            else:
                processed_audio = audio_array
                metadata = {}
            
            # Create audio buffer
            duration = len(processed_audio) / self.audio_config.sample_rate
            audio_buffer = AudioBuffer(
                data=processed_audio,
                timestamp=datetime.utcnow(),
                sample_rate=self.audio_config.sample_rate,
                channels=self.audio_config.channels,
                duration_seconds=duration
            )
            
            # Add to buffer queue
            self.audio_buffers.append(audio_buffer)
            if len(self.audio_buffers) > self.max_buffer_size:
                self.audio_buffers.pop(0)
                self.stats['buffer_overruns'] += 1
            
            # Call callback if provided
            if self.audio_callback:
                try:
                    self.audio_callback(audio_buffer)
                except Exception as e:
                    logger.error("Audio callback error", error=str(e))
            
            # Update statistics
            self.stats['total_recorded_seconds'] += duration
            
            return (None, pyaudio.paContinue)
            
        except Exception as e:
            logger.error("Audio input callback error", error=str(e))
            self.stats['processing_errors'] += 1
            return (None, pyaudio.paAbort)
    
    def _playback_thread(self, audio_data: bytes) -> None:
        """Audio playback thread."""
        try:
            chunk_size = self.audio_config.chunk_size * 2  # 2 bytes per sample for int16
            
            for i in range(0, len(audio_data), chunk_size):
                if self.stop_event.is_set() or not self.playback_active:
                    break
                
                chunk = audio_data[i:i + chunk_size]
                
                # Pad last chunk if necessary
                if len(chunk) < chunk_size:
                    chunk += b'\x00' * (chunk_size - len(chunk))
                
                self.output_stream.write(chunk)
                
                # Update statistics
                duration = len(chunk) / (self.audio_config.sample_rate * 2)
                self.stats['total_played_seconds'] += duration
            
            self.playback_active = False
            self.state = AudioState.IDLE
            
        except Exception as e:
            logger.error("Playback thread error", error=str(e))
            self.playback_active = False
            self.state = AudioState.ERROR
    
    def _get_pyaudio_format(self):
        """Get PyAudio format constant."""
        format_map = {
            AudioFormat.PCM_16: pyaudio.paInt16,
            AudioFormat.PCM_24: pyaudio.paInt24,
            AudioFormat.PCM_32: pyaudio.paInt32,
            AudioFormat.FLOAT_32: pyaudio.paFloat32
        }
        return format_map.get(self.audio_config.format, pyaudio.paInt16)
    
    def get_audio_status(self) -> Dict[str, Any]:
        """Get current audio interface status."""
        return {
            'state': self.state.value,
            'recording_active': self.recording_active,
            'playback_active': self.playback_active,
            'buffer_count': len(self.audio_buffers),
            'statistics': self.stats.copy(),
            'audio_config': {
                'sample_rate': self.audio_config.sample_rate,
                'channels': self.audio_config.channels,
                'chunk_size': self.audio_config.chunk_size,
                'format': self.audio_config.format.value
            }
        }
    
    def get_latest_audio_buffer(self) -> Optional[AudioBuffer]:
        """Get the latest audio buffer."""
        return self.audio_buffers[-1] if self.audio_buffers else None
    
    async def cleanup(self) -> None:
        """Cleanup audio interface resources."""
        try:
            # Stop recording and playback
            self.stop_recording()
            self.stop_playback()
            
            # Cleanup PyAudio
            if self.pyaudio:
                self.pyaudio.terminate()
                self.pyaudio = None
            
            # Clear buffers
            self.audio_buffers.clear()
            
            self.state = AudioState.IDLE
            
            logger.info("Audio interface cleanup completed",
                       modem_id=self.config.modem_id)
            
        except Exception as e:
            logger.error("Audio interface cleanup error", error=str(e))