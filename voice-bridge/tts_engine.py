"""
Edge-TTS Engine Module

This module implements advanced text-to-speech capabilities using Microsoft's
Edge-TTS service for high-quality, natural-sounding voice synthesis. The engine
provides multi-language support, voice customization, and streaming optimization
for real-time voice generation in conversational AI applications.

The TTS engine serves as the voice output component of the voice-bridge system,
delivering human-like speech synthesis with minimal latency and maximum quality.
"""

import asyncio
import logging
import time
import io
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

import edge_tts
import numpy as np
import soundfile as sf
from pydub import AudioSegment
from pydub.effects import normalize

from config import VoiceBridgeConfig


class VoiceGender(Enum):
    """Enumeration of voice genders."""
    MALE = "male"
    FEMALE = "female"
    NEUTRAL = "neutral"


class VoiceStyle(Enum):
    """Enumeration of voice styles."""
    NEUTRAL = "neutral"
    CHEERFUL = "cheerful"
    EMPATHETIC = "empathetic"
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    CALM = "calm"
    EXCITED = "excited"


@dataclass
class VoiceProfile:
    """Data class for voice profile configuration."""
    name: str
    language: str
    gender: VoiceGender
    style: VoiceStyle
    rate: str
    pitch: str
    volume: str


@dataclass
class TTSResult:
    """Data class for TTS generation results."""
    audio_data: np.ndarray
    sample_rate: int
    duration: float
    voice_profile: VoiceProfile
    processing_time: float
    metadata: Dict[str, Any]


class EdgeTTSEngine:
    """
    Advanced Edge-TTS engine for high-quality speech synthesis.
    
    Provides comprehensive text-to-speech capabilities including multi-language
    support, voice customization, emotional expression, and streaming optimization
    for real-time conversational AI applications.
    """
    
    def __init__(self, config: VoiceBridgeConfig):
        """
        Initialize Edge-TTS engine.
        
        Args:
            config: Voice-bridge configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # TTS configuration
        self.default_voice = config.edge_tts_voice
        self.default_rate = config.edge_tts_rate
        self.default_pitch = config.edge_tts_pitch
        self.default_volume = config.edge_tts_volume
        
        # Voice management
        self.available_voices: Dict[str, Dict[str, Any]] = {}
        self.voice_profiles: Dict[str, VoiceProfile] = {}
        self.session_voices: Dict[str, str] = {}
        
        # Performance tracking
        self.synthesis_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "avg_processing_time": 0.0,
            "total_audio_duration": 0.0
        }
        
        # Audio processing
        self.target_sample_rate = config.audio_sample_rate
        self.audio_format = "wav"
        
        # Caching
        self.enable_caching = True
        self.audio_cache: Dict[str, TTSResult] = {}
        self.max_cache_size = 1000
        
        # Advanced features
        self.enable_ssml = True
        self.enable_emotion_synthesis = True
        self.enable_prosody_control = True
        
        # Language support
        self.supported_languages = config.supported_languages
        self.language_voice_mapping = {}
    
    async def initialize(self) -> None:
        """
        Initialize TTS engine and discover available voices.
        
        Loads available voices, configures voice profiles, and
        sets up language mappings for optimal voice selection.
        """
        self.logger.info("Initializing Edge-TTS engine")
        
        try:
            # Discover available voices
            await self._discover_available_voices()
            
            # Initialize voice profiles
            await self._initialize_voice_profiles()
            
            # Setup language mappings
            await self._setup_language_mappings()
            
            # Test TTS functionality
            await self._test_tts_functionality()
            
            self.logger.info("Edge-TTS engine initialized successfully",
                           extra={"available_voices": len(self.available_voices),
                                 "voice_profiles": len(self.voice_profiles)})
            
        except Exception as e:
            self.logger.error(f"TTS engine initialization failed: {e}")
            raise
    
    async def _discover_available_voices(self) -> None:
        """
        Discover and catalog available Edge-TTS voices.
        
        Retrieves the complete list of available voices and their
        characteristics for intelligent voice selection.
        """
        try:
            # Get list of available voices
            voices = await edge_tts.list_voices()
            
            for voice in voices:
                voice_id = voice["ShortName"]
                self.available_voices[voice_id] = {
                    "name": voice["FriendlyName"],
                    "language": voice["Locale"],
                    "gender": voice["Gender"].lower(),
                    "voice_type": voice.get("VoiceType", "Standard"),
                    "styles": voice.get("StyleList", []),
                    "roles": voice.get("RolePlayList", [])
                }
            
            self.logger.info("Voice discovery completed",
                           extra={"total_voices": len(self.available_voices)})
            
        except Exception as e:
            self.logger.error(f"Voice discovery failed: {e}")
            # Continue with default voice only
            self.available_voices[self.default_voice] = {
                "name": "Default Voice",
                "language": "en-US",
                "gender": "female",
                "voice_type": "Standard",
                "styles": [],
                "roles": []
            }
    
    async def _initialize_voice_profiles(self) -> None:
        """
        Initialize predefined voice profiles for different scenarios.
        
        Creates optimized voice profiles for various conversation contexts
        and emotional states to enhance user experience.
        """
        try:
            # Professional customer service profile
            self.voice_profiles["professional"] = VoiceProfile(
                name="en-US-AriaNeural",
                language="en-US",
                gender=VoiceGender.FEMALE,
                style=VoiceStyle.PROFESSIONAL,
                rate="+0%",
                pitch="+0Hz",
                volume="+0%"
            )
            
            # Friendly support profile
            self.voice_profiles["friendly"] = VoiceProfile(
                name="en-US-JennyNeural",
                language="en-US",
                gender=VoiceGender.FEMALE,
                style=VoiceStyle.FRIENDLY,
                rate="-5%",
                pitch="+50Hz",
                volume="+0%"
            )
            
            # Calm technical support profile
            self.voice_profiles["technical"] = VoiceProfile(
                name="en-US-GuyNeural",
                language="en-US",
                gender=VoiceGender.MALE,
                style=VoiceStyle.CALM,
                rate="-10%",
                pitch="-25Hz",
                volume="+0%"
            )
            
            # Empathetic customer care profile
            self.voice_profiles["empathetic"] = VoiceProfile(
                name="en-US-SaraNeural",
                language="en-US",
                gender=VoiceGender.FEMALE,
                style=VoiceStyle.EMPATHETIC,
                rate="-15%",
                pitch="+25Hz",
                volume="-5%"
            )
            
            # Excited sales profile
            self.voice_profiles["sales"] = VoiceProfile(
                name="en-US-DavisNeural",
                language="en-US",
                gender=VoiceGender.MALE,
                style=VoiceStyle.EXCITED,
                rate="+5%",
                pitch="+75Hz",
                volume="+5%"
            )
            
            self.logger.info("Voice profiles initialized",
                           extra={"profiles": list(self.voice_profiles.keys())})
            
        except Exception as e:
            self.logger.error(f"Voice profile initialization failed: {e}")
    
    async def _setup_language_mappings(self) -> None:
        """
        Setup language-to-voice mappings for multi-language support.
        
        Creates intelligent mappings between languages and optimal
        voices for natural-sounding multi-language conversations.
        """
        try:
            # Default language mappings
            self.language_voice_mapping = {
                "en": "en-US-AriaNeural",
                "es": "es-ES-ElviraNeural",
                "fr": "fr-FR-DeniseNeural",
                "de": "de-DE-KatjaNeural",
                "it": "it-IT-ElsaNeural",
                "pt": "pt-BR-FranciscaNeural",
                "ru": "ru-RU-SvetlanaNeural",
                "zh": "zh-CN-XiaoxiaoNeural",
                "ja": "ja-JP-NanamiNeural",
                "ko": "ko-KR-SunHiNeural"
            }
            
            # Filter mappings based on available voices
            available_mappings = {}
            for lang, voice in self.language_voice_mapping.items():
                if voice in self.available_voices:
                    available_mappings[lang] = voice
                else:
                    # Fallback to default voice
                    available_mappings[lang] = self.default_voice
            
            self.language_voice_mapping = available_mappings
            
            self.logger.info("Language mappings configured",
                           extra={"mappings": len(self.language_voice_mapping)})
            
        except Exception as e:
            self.logger.error(f"Language mapping setup failed: {e}")
    
    async def _test_tts_functionality(self) -> None:
        """
        Test TTS functionality with a simple synthesis request.
        
        Raises:
            Exception: If TTS functionality test fails
        """
        try:
            test_text = "Hello, this is a TTS functionality test."
            result = await self.synthesize_speech(test_text, "test_session")
            
            if result is None or len(result) == 0:
                raise Exception("TTS functionality test failed - no audio generated")
            
            self.logger.info("TTS functionality test successful")
            
        except Exception as e:
            self.logger.error(f"TTS functionality test failed: {e}")
            raise
    
    async def synthesize_speech(self, text: str, session_id: str,
                              voice_profile: Optional[str] = None,
                              language: Optional[str] = None,
                              emotion: Optional[str] = None) -> Optional[np.ndarray]:
        """
        Synthesize speech from text with advanced customization options.
        
        Args:
            text: Text to synthesize
            session_id: Session identifier for voice consistency
            voice_profile: Optional voice profile name
            language: Optional language override
            emotion: Optional emotion for synthesis
            
        Returns:
            Audio data as numpy array or None if synthesis fails
        """
        start_time = time.time()
        
        try:
            # Generate cache key
            cache_key = self._generate_cache_key(text, voice_profile, language, emotion)
            
            # Check cache
            if self.enable_caching and cache_key in self.audio_cache:
                cached_result = self.audio_cache[cache_key]
                self.logger.debug("Using cached TTS result", extra={"session_id": session_id})
                return cached_result.audio_data
            
            # Determine voice configuration
            voice_config = await self._determine_voice_config(
                session_id, voice_profile, language, emotion
            )
            
            # Prepare text for synthesis
            prepared_text = await self._prepare_text_for_synthesis(text, emotion)
            
            # Perform synthesis
            audio_data = await self._perform_synthesis(prepared_text, voice_config)
            
            if audio_data is not None:
                # Post-process audio
                processed_audio = await self._post_process_audio(audio_data)
                
                # Create result object
                result = TTSResult(
                    audio_data=processed_audio,
                    sample_rate=self.target_sample_rate,
                    duration=len(processed_audio) / self.target_sample_rate,
                    voice_profile=voice_config,
                    processing_time=time.time() - start_time,
                    metadata={
                        "session_id": session_id,
                        "text_length": len(text),
                        "cache_key": cache_key
                    }
                )
                
                # Cache result
                if self.enable_caching:
                    await self._cache_result(cache_key, result)
                
                # Update statistics
                self.synthesis_stats["total_requests"] += 1
                self.synthesis_stats["successful_requests"] += 1
                self.synthesis_stats["total_audio_duration"] += result.duration
                
                processing_time = time.time() - start_time
                self._update_avg_processing_time(processing_time)
                
                self.logger.debug("Speech synthesis successful",
                                extra={"session_id": session_id,
                                      "duration": result.duration,
                                      "processing_time": processing_time})
                
                return processed_audio
            
            return None
            
        except Exception as e:
            self.logger.error(f"Speech synthesis failed: {e}",
                            extra={"session_id": session_id, "text": text[:100]})
            self.synthesis_stats["total_requests"] += 1
            self.synthesis_stats["failed_requests"] += 1
            return None
    
    async def _determine_voice_config(self, session_id: str,
                                    voice_profile: Optional[str] = None,
                                    language: Optional[str] = None,
                                    emotion: Optional[str] = None) -> VoiceProfile:
        """
        Determine optimal voice configuration for synthesis.
        
        Args:
            session_id: Session identifier
            voice_profile: Optional voice profile name
            language: Optional language override
            emotion: Optional emotion for synthesis
            
        Returns:
            VoiceProfile configuration
        """
        try:
            # Use session-specific voice if available
            if session_id in self.session_voices and not voice_profile:
                voice_name = self.session_voices[session_id]
            else:
                # Determine voice based on profile or language
                if voice_profile and voice_profile in self.voice_profiles:
                    profile = self.voice_profiles[voice_profile]
                    voice_name = profile.name
                elif language and language in self.language_voice_mapping:
                    voice_name = self.language_voice_mapping[language]
                else:
                    voice_name = self.default_voice
                
                # Store voice for session consistency
                self.session_voices[session_id] = voice_name
            
            # Get voice information
            voice_info = self.available_voices.get(voice_name, {})
            
            # Determine style based on emotion
            style = VoiceStyle.NEUTRAL
            if emotion:
                emotion_style_mapping = {
                    "happy": VoiceStyle.CHEERFUL,
                    "sad": VoiceStyle.EMPATHETIC,
                    "angry": VoiceStyle.CALM,
                    "excited": VoiceStyle.EXCITED,
                    "frustrated": VoiceStyle.EMPATHETIC,
                    "neutral": VoiceStyle.NEUTRAL
                }
                style = emotion_style_mapping.get(emotion.lower(), VoiceStyle.NEUTRAL)
            
            # Create voice profile
            profile = VoiceProfile(
                name=voice_name,
                language=voice_info.get("language", "en-US"),
                gender=VoiceGender(voice_info.get("gender", "female")),
                style=style,
                rate=self.default_rate,
                pitch=self.default_pitch,
                volume=self.default_volume
            )
            
            # Adjust parameters based on emotion
            if emotion:
                profile = await self._adjust_voice_for_emotion(profile, emotion)
            
            return profile
            
        except Exception as e:
            self.logger.error(f"Voice configuration determination failed: {e}")
            # Return default profile
            return VoiceProfile(
                name=self.default_voice,
                language="en-US",
                gender=VoiceGender.FEMALE,
                style=VoiceStyle.NEUTRAL,
                rate=self.default_rate,
                pitch=self.default_pitch,
                volume=self.default_volume
            )
    
    async def _adjust_voice_for_emotion(self, profile: VoiceProfile, emotion: str) -> VoiceProfile:
        """
        Adjust voice parameters based on emotional context.
        
        Args:
            profile: Base voice profile
            emotion: Emotion to express
            
        Returns:
            Adjusted voice profile
        """
        try:
            emotion_adjustments = {
                "happy": {"rate": "+10%", "pitch": "+100Hz", "volume": "+5%"},
                "sad": {"rate": "-20%", "pitch": "-50Hz", "volume": "-10%"},
                "angry": {"rate": "+5%", "pitch": "+25Hz", "volume": "+10%"},
                "excited": {"rate": "+15%", "pitch": "+150Hz", "volume": "+10%"},
                "frustrated": {"rate": "-10%", "pitch": "+50Hz", "volume": "+5%"},
                "calm": {"rate": "-15%", "pitch": "-25Hz", "volume": "-5%"},
                "empathetic": {"rate": "-10%", "pitch": "+25Hz", "volume": "-5%"}
            }
            
            adjustments = emotion_adjustments.get(emotion.lower(), {})
            
            if adjustments:
                profile.rate = adjustments.get("rate", profile.rate)
                profile.pitch = adjustments.get("pitch", profile.pitch)
                profile.volume = adjustments.get("volume", profile.volume)
            
            return profile
            
        except Exception as e:
            self.logger.error(f"Voice emotion adjustment failed: {e}")
            return profile
    
    async def _prepare_text_for_synthesis(self, text: str, emotion: Optional[str] = None) -> str:
        """
        Prepare text for synthesis with SSML enhancements.
        
        Args:
            text: Input text
            emotion: Optional emotion for SSML styling
            
        Returns:
            Prepared text with SSML markup
        """
        try:
            if not self.enable_ssml:
                return text
            
            # Clean and normalize text
            cleaned_text = text.strip()
            
            # Add emotion-based SSML styling
            if emotion and self.enable_emotion_synthesis:
                emotion_ssml_mapping = {
                    "happy": '<prosody rate="fast" pitch="high">',
                    "sad": '<prosody rate="slow" pitch="low">',
                    "excited": '<prosody rate="fast" pitch="x-high" volume="loud">',
                    "calm": '<prosody rate="slow" pitch="low" volume="soft">',
                    "empathetic": '<prosody rate="medium" pitch="medium" volume="soft">'
                }
                
                if emotion.lower() in emotion_ssml_mapping:
                    opening_tag = emotion_ssml_mapping[emotion.lower()]
                    cleaned_text = f"{opening_tag}{cleaned_text}</prosody>"
            
            # Add pauses for natural speech
            if self.enable_prosody_control:
                # Add brief pauses after punctuation
                cleaned_text = cleaned_text.replace('. ', '. <break time="300ms"/>')
                cleaned_text = cleaned_text.replace('! ', '! <break time="400ms"/>')
                cleaned_text = cleaned_text.replace('? ', '? <break time="400ms"/>')
                cleaned_text = cleaned_text.replace(', ', ', <break time="200ms"/>')
            
            return cleaned_text
            
        except Exception as e:
            self.logger.error(f"Text preparation failed: {e}")
            return text
    
    async def _perform_synthesis(self, text: str, voice_config: VoiceProfile) -> Optional[np.ndarray]:
        """
        Perform the actual speech synthesis using Edge-TTS.
        
        Args:
            text: Prepared text for synthesis
            voice_config: Voice configuration
            
        Returns:
            Audio data as numpy array or None if synthesis fails
        """
        try:
            # Create TTS communicator
            communicate = edge_tts.Communicate(text, voice_config.name)
            
            # Set voice parameters
            if hasattr(communicate, 'set_rate'):
                communicate.set_rate(voice_config.rate)
            if hasattr(communicate, 'set_pitch'):
                communicate.set_pitch(voice_config.pitch)
            if hasattr(communicate, 'set_volume'):
                communicate.set_volume(voice_config.volume)
            
            # Generate audio
            audio_data = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data += chunk["data"]
            
            if not audio_data:
                return None
            
            # Convert to numpy array
            audio_segment = AudioSegment.from_file(io.BytesIO(audio_data), format="mp3")
            
            # Convert to target sample rate and format
            if audio_segment.frame_rate != self.target_sample_rate:
                audio_segment = audio_segment.set_frame_rate(self.target_sample_rate)
            
            # Convert to mono if needed
            if audio_segment.channels > 1:
                audio_segment = audio_segment.set_channels(1)
            
            # Convert to numpy array
            audio_array = np.array(audio_segment.get_array_of_samples(), dtype=np.float32)
            
            # Normalize to [-1, 1] range
            if audio_array.dtype == np.int16:
                audio_array = audio_array / 32768.0
            elif audio_array.dtype == np.int32:
                audio_array = audio_array / 2147483648.0
            
            return audio_array
            
        except Exception as e:
            self.logger.error(f"Speech synthesis failed: {e}")
            return None
    
    async def _post_process_audio(self, audio_data: np.ndarray) -> np.ndarray:
        """
        Post-process synthesized audio for optimal quality.
        
        Args:
            audio_data: Raw synthesized audio
            
        Returns:
            Post-processed audio data
        """
        try:
            # Normalize audio levels
            max_amplitude = np.max(np.abs(audio_data))
            if max_amplitude > 0:
                # Normalize to 90% of maximum to prevent clipping
                audio_data = audio_data * (0.9 / max_amplitude)
            
            # Apply gentle compression to improve consistency
            threshold = 0.7
            ratio = 3.0
            
            # Simple compression algorithm
            compressed = np.where(
                np.abs(audio_data) > threshold,
                np.sign(audio_data) * (
                    threshold + (np.abs(audio_data) - threshold) / ratio
                ),
                audio_data
            )
            
            # Apply gentle high-pass filter to remove low-frequency noise
            from scipy.signal import butter, filtfilt
            
            nyquist = self.target_sample_rate / 2
            low_cutoff = 80 / nyquist
            b, a = butter(2, low_cutoff, btype='high')
            filtered_audio = filtfilt(b, a, compressed)
            
            return filtered_audio.astype(np.float32)
            
        except Exception as e:
            self.logger.error(f"Audio post-processing failed: {e}")
            return audio_data
    
    def _generate_cache_key(self, text: str, voice_profile: Optional[str] = None,
                          language: Optional[str] = None, emotion: Optional[str] = None) -> str:
        """
        Generate cache key for TTS result caching.
        
        Args:
            text: Input text
            voice_profile: Voice profile name
            language: Language code
            emotion: Emotion name
            
        Returns:
            Cache key string
        """
        import hashlib
        
        # Create hash of text and parameters
        cache_components = [
            text,
            voice_profile or "default",
            language or "en",
            emotion or "neutral"
        ]
        
        cache_string = "|".join(cache_components)
        cache_hash = hashlib.md5(cache_string.encode()).hexdigest()
        
        return f"tts_{cache_hash}"
    
    async def _cache_result(self, cache_key: str, result: TTSResult) -> None:
        """
        Cache TTS result for future use.
        
        Args:
            cache_key: Cache key
            result: TTS result to cache
        """
        try:
            # Check cache size limit
            if len(self.audio_cache) >= self.max_cache_size:
                # Remove oldest entries (simple FIFO)
                oldest_keys = list(self.audio_cache.keys())[:10]
                for key in oldest_keys:
                    del self.audio_cache[key]
            
            self.audio_cache[cache_key] = result
            
        except Exception as e:
            self.logger.error(f"Result caching failed: {e}")
    
    def _update_avg_processing_time(self, processing_time: float) -> None:
        """
        Update average processing time statistics.
        
        Args:
            processing_time: Processing time in seconds
        """
        total_requests = self.synthesis_stats["successful_requests"]
        if total_requests > 0:
            current_avg = self.synthesis_stats["avg_processing_time"]
            self.synthesis_stats["avg_processing_time"] = (
                (current_avg * (total_requests - 1) + processing_time) / total_requests
            )
    
    async def get_available_voices(self, language: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get list of available voices, optionally filtered by language.
        
        Args:
            language: Optional language filter
            
        Returns:
            List of available voice information
        """
        try:
            voices = []
            
            for voice_id, voice_info in self.available_voices.items():
                if language is None or voice_info["language"].startswith(language):
                    voices.append({
                        "id": voice_id,
                        "name": voice_info["name"],
                        "language": voice_info["language"],
                        "gender": voice_info["gender"],
                        "voice_type": voice_info["voice_type"],
                        "styles": voice_info["styles"],
                        "roles": voice_info["roles"]
                    })
            
            return voices
            
        except Exception as e:
            self.logger.error(f"Failed to get available voices: {e}")
            return []
    
    async def set_session_voice(self, session_id: str, voice_name: str) -> bool:
        """
        Set voice for a specific session.
        
        Args:
            session_id: Session identifier
            voice_name: Voice name to use
            
        Returns:
            True if voice was set successfully, False otherwise
        """
        try:
            if voice_name in self.available_voices:
                self.session_voices[session_id] = voice_name
                self.logger.debug("Session voice set",
                                extra={"session_id": session_id, "voice": voice_name})
                return True
            else:
                self.logger.warning("Voice not available",
                                  extra={"voice": voice_name})
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to set session voice: {e}")
            return False
    
    async def get_synthesis_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive synthesis statistics.
        
        Returns:
            Dict containing synthesis statistics
        """
        try:
            stats = self.synthesis_stats.copy()
            
            # Calculate success rate
            if stats["total_requests"] > 0:
                stats["success_rate"] = stats["successful_requests"] / stats["total_requests"]
            else:
                stats["success_rate"] = 0.0
            
            # Add cache information
            stats["cache_size"] = len(self.audio_cache)
            stats["cache_hit_rate"] = 0.0  # Would need to track cache hits
            
            # Add session information
            stats["active_sessions"] = len(self.session_voices)
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Failed to get synthesis statistics: {e}")
            return {}
    
    async def get_health_status(self) -> Dict[str, Any]:
        """
        Get TTS engine health status.
        
        Returns:
            Dict containing health status and performance metrics
        """
        try:
            status = {
                "status": "healthy",
                "available_voices": len(self.available_voices),
                "voice_profiles": len(self.voice_profiles),
                "synthesis_statistics": await self.get_synthesis_statistics(),
                "capabilities": {
                    "ssml_enabled": self.enable_ssml,
                    "emotion_synthesis": self.enable_emotion_synthesis,
                    "prosody_control": self.enable_prosody_control,
                    "caching_enabled": self.enable_caching
                },
                "configuration": {
                    "default_voice": self.default_voice,
                    "target_sample_rate": self.target_sample_rate,
                    "supported_languages": len(self.language_voice_mapping)
                }
            }
            
            # Check for issues
            synthesis_stats = status["synthesis_statistics"]
            if synthesis_stats.get("total_requests", 0) > 0:
                success_rate = synthesis_stats.get("success_rate", 0)
                if success_rate < 0.9:  # Less than 90% success rate
                    status["status"] = "degraded"
                    status["issues"] = [f"Low synthesis success rate: {success_rate:.2%}"]
                
                avg_processing_time = synthesis_stats.get("avg_processing_time", 0)
                if avg_processing_time > 3.0:  # More than 3 seconds average
                    if status["status"] == "healthy":
                        status["status"] = "degraded"
                        status["issues"] = []
                    status["issues"].append(f"High average processing time: {avg_processing_time:.2f}s")
            
            return status
            
        except Exception as e:
            self.logger.error(f"Health status check failed: {e}")
            return {"status": "error", "error": str(e)}
    
    async def cleanup(self) -> None:
        """
        Cleanup TTS engine resources.
        
        Clears caches, session data, and releases resources.
        """
        self.logger.info("Cleaning up TTS engine")
        
        try:
            # Clear audio cache
            self.audio_cache.clear()
            
            # Clear session voices
            self.session_voices.clear()
            
            # Clear voice profiles
            self.voice_profiles.clear()
            
            self.logger.info("TTS engine cleanup completed")
            
        except Exception as e:
            self.logger.error(f"TTS engine cleanup failed: {e}")