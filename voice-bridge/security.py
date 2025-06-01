"""
Security Manager Module

This module implements comprehensive security measures for the voice-bridge
microservice, providing authentication, authorization, encryption, and
security monitoring capabilities. The security manager ensures enterprise-grade
protection for voice communications and sensitive data processing.

The security manager serves as the guardian of the voice-bridge system,
implementing multi-layered security controls and monitoring to protect
against threats while maintaining optimal performance.
"""

import asyncio
import logging
import time
import hashlib
import secrets
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta

import jwt
from passlib.context import CryptContext
from cryptography.fernet import Fernet
import redis.asyncio as redis

from config import VoiceBridgeConfig


class SecurityLevel(Enum):
    """Enumeration of security levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ThreatType(Enum):
    """Enumeration of threat types."""
    BRUTE_FORCE = "brute_force"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    DATA_BREACH_ATTEMPT = "data_breach_attempt"
    MALFORMED_REQUEST = "malformed_request"


@dataclass
class SecurityEvent:
    """Data class for security events."""
    event_id: str
    threat_type: ThreatType
    severity: SecurityLevel
    source_ip: str
    user_id: Optional[str]
    timestamp: float
    details: Dict[str, Any]
    resolved: bool


@dataclass
class UserSession:
    """Data class for user sessions."""
    session_id: str
    user_id: str
    created_at: float
    last_activity: float
    ip_address: str
    user_agent: str
    permissions: Set[str]
    security_level: SecurityLevel


class SecurityManager:
    """
    Comprehensive security management system.
    
    Provides enterprise-grade security including authentication, authorization,
    encryption, threat detection, and security monitoring for voice-bridge
    operations with real-time threat response capabilities.
    """
    
    def __init__(self, config: VoiceBridgeConfig):
        """
        Initialize security manager.
        
        Args:
            config: Voice-bridge configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Security configuration
        self.secret_key = config.secret_key.get_secret_value()
        self.jwt_algorithm = config.jwt_algorithm
        self.jwt_expiration = config.jwt_expiration_hours
        
        # Encryption
        self.encryption_key = self._generate_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)
        
        # Password hashing
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # Session management
        self.active_sessions: Dict[str, UserSession] = {}
        self.session_timeout = 3600  # 1 hour
        
        # Security monitoring
        self.security_events: List[SecurityEvent] = []
        self.threat_counters: Dict[str, Dict[str, int]] = {}
        self.blocked_ips: Set[str] = set()
        self.suspicious_activities: Dict[str, List[float]] = {}
        
        # Rate limiting
        self.rate_limits: Dict[str, Dict[str, Any]] = {}
        self.rate_limit_windows = {
            "requests_per_minute": 60,
            "requests_per_hour": 1000,
            "failed_attempts_per_hour": 10
        }
        
        # Security policies
        self.security_policies = self._initialize_security_policies()
        
        # Background tasks
        self.monitoring_task: Optional[asyncio.Task] = None
        self.cleanup_task: Optional[asyncio.Task] = None
        
        # Redis for distributed security
        self.redis_client: Optional[redis.Redis] = None
        
        # Advanced features
        self.enable_threat_detection = True
        self.enable_behavioral_analysis = True
        self.enable_real_time_monitoring = True
    
    async def initialize(self) -> None:
        """
        Initialize security manager and start monitoring.
        
        Sets up security policies, starts background monitoring tasks,
        and initializes threat detection systems.
        """
        self.logger.info("Initializing security manager")
        
        try:
            # Initialize Redis if available
            if hasattr(self.config, 'redis_url') and self.config.redis_url:
                try:
                    self.redis_client = redis.Redis.from_url(str(self.config.redis_url))
                    await self.redis_client.ping()
                    self.logger.info("Redis security backend initialized")
                except Exception as e:
                    self.logger.warning(f"Redis security initialization failed: {e}")
            
            # Start background tasks
            self.monitoring_task = asyncio.create_task(self._security_monitoring())
            self.cleanup_task = asyncio.create_task(self._security_cleanup())
            
            # Load existing security data
            await self._load_security_state()
            
            self.logger.info("Security manager initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Security manager initialization failed: {e}")
            raise
    
    def _generate_encryption_key(self) -> bytes:
        """
        Generate encryption key for data protection.
        
        Returns:
            Encryption key bytes
        """
        # In production, this should be loaded from secure storage
        key_material = self.secret_key + "encryption_salt"
        key_hash = hashlib.sha256(key_material.encode()).digest()
        return Fernet.generate_key()  # Use proper key derivation in production
    
    def _initialize_security_policies(self) -> Dict[str, Any]:
        """
        Initialize security policies and rules.
        
        Returns:
            Dict containing security policies
        """
        return {
            "password_policy": {
                "min_length": 8,
                "require_uppercase": True,
                "require_lowercase": True,
                "require_numbers": True,
                "require_special_chars": True,
                "max_age_days": 90
            },
            "session_policy": {
                "max_concurrent_sessions": 5,
                "idle_timeout_minutes": 30,
                "absolute_timeout_hours": 8,
                "require_reauth_for_sensitive": True
            },
            "access_policy": {
                "max_failed_attempts": 5,
                "lockout_duration_minutes": 15,
                "require_mfa_for_admin": True,
                "ip_whitelist_enabled": False
            },
            "data_policy": {
                "encrypt_sensitive_data": True,
                "log_data_access": True,
                "data_retention_days": 90,
                "anonymize_logs": True
            }
        }
    
    async def create_token(self, user_id: str, permissions: List[str],
                          additional_claims: Optional[Dict[str, Any]] = None) -> str:
        """
        Create JWT token for user authentication.
        
        Args:
            user_id: User identifier
            permissions: List of user permissions
            additional_claims: Optional additional JWT claims
            
        Returns:
            JWT token string
        """
        try:
            now = datetime.utcnow()
            expiration = now + timedelta(hours=self.jwt_expiration)
            
            payload = {
                "user_id": user_id,
                "permissions": permissions,
                "iat": now,
                "exp": expiration,
                "iss": "voice-bridge",
                "jti": secrets.token_urlsafe(16)  # JWT ID for revocation
            }
            
            if additional_claims:
                payload.update(additional_claims)
            
            token = jwt.encode(payload, self.secret_key, algorithm=self.jwt_algorithm)
            
            # Log token creation
            await self._log_security_event(
                ThreatType.UNAUTHORIZED_ACCESS,  # Will be overridden
                SecurityLevel.LOW,
                "system",
                user_id,
                {"action": "token_created", "permissions": permissions}
            )
            
            return token
            
        except Exception as e:
            self.logger.error(f"Token creation failed: {e}")
            raise
    
    async def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify and decode JWT token.
        
        Args:
            token: JWT token to verify
            
        Returns:
            Decoded token payload
            
        Raises:
            jwt.InvalidTokenError: If token is invalid
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.jwt_algorithm],
                options={"verify_exp": True}
            )
            
            # Check if token is revoked (if using Redis)
            if self.redis_client:
                jti = payload.get("jti")
                if jti:
                    revoked = await self.redis_client.get(f"revoked_token:{jti}")
                    if revoked:
                        raise jwt.InvalidTokenError("Token has been revoked")
            
            return payload
            
        except jwt.ExpiredSignatureError:
            self.logger.warning("Expired token verification attempt")
            raise
        except jwt.InvalidTokenError as e:
            self.logger.warning(f"Invalid token verification attempt: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Token verification failed: {e}")
            raise
    
    async def revoke_token(self, token: str) -> bool:
        """
        Revoke a JWT token.
        
        Args:
            token: JWT token to revoke
            
        Returns:
            True if revoked successfully, False otherwise
        """
        try:
            # Decode token to get JTI
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.jwt_algorithm],
                options={"verify_exp": False}  # Don't verify expiration for revocation
            )
            
            jti = payload.get("jti")
            if not jti:
                return False
            
            # Store revoked token in Redis
            if self.redis_client:
                exp = payload.get("exp")
                if exp:
                    ttl = max(0, exp - time.time())
                    await self.redis_client.setex(f"revoked_token:{jti}", int(ttl), "1")
            
            # Log revocation
            await self._log_security_event(
                ThreatType.UNAUTHORIZED_ACCESS,
                SecurityLevel.MEDIUM,
                "system",
                payload.get("user_id"),
                {"action": "token_revoked", "jti": jti}
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Token revocation failed: {e}")
            return False
    
    async def create_session(self, user_id: str, ip_address: str,
                           user_agent: str, permissions: Set[str]) -> UserSession:
        """
        Create a new user session.
        
        Args:
            user_id: User identifier
            ip_address: Client IP address
            user_agent: Client user agent
            permissions: User permissions
            
        Returns:
            UserSession object
        """
        try:
            session_id = secrets.token_urlsafe(32)
            
            session = UserSession(
                session_id=session_id,
                user_id=user_id,
                created_at=time.time(),
                last_activity=time.time(),
                ip_address=ip_address,
                user_agent=user_agent,
                permissions=permissions,
                security_level=SecurityLevel.MEDIUM
            )
            
            # Check concurrent session limits
            user_sessions = [s for s in self.active_sessions.values() if s.user_id == user_id]
            max_sessions = self.security_policies["session_policy"]["max_concurrent_sessions"]
            
            if len(user_sessions) >= max_sessions:
                # Remove oldest session
                oldest_session = min(user_sessions, key=lambda s: s.created_at)
                await self.end_session(oldest_session.session_id)
            
            self.active_sessions[session_id] = session
            
            # Log session creation
            await self._log_security_event(
                ThreatType.UNAUTHORIZED_ACCESS,
                SecurityLevel.LOW,
                ip_address,
                user_id,
                {"action": "session_created", "session_id": session_id}
            )
            
            return session
            
        except Exception as e:
            self.logger.error(f"Session creation failed: {e}")
            raise
    
    async def validate_session(self, session_id: str, ip_address: str) -> Optional[UserSession]:
        """
        Validate and update user session.
        
        Args:
            session_id: Session identifier
            ip_address: Client IP address
            
        Returns:
            UserSession if valid, None otherwise
        """
        try:
            if session_id not in self.active_sessions:
                return None
            
            session = self.active_sessions[session_id]
            current_time = time.time()
            
            # Check session timeout
            idle_timeout = self.security_policies["session_policy"]["idle_timeout_minutes"] * 60
            if current_time - session.last_activity > idle_timeout:
                await self.end_session(session_id)
                return None
            
            # Check absolute timeout
            absolute_timeout = self.security_policies["session_policy"]["absolute_timeout_hours"] * 3600
            if current_time - session.created_at > absolute_timeout:
                await self.end_session(session_id)
                return None
            
            # Check IP address consistency
            if session.ip_address != ip_address:
                await self._log_security_event(
                    ThreatType.SUSPICIOUS_ACTIVITY,
                    SecurityLevel.HIGH,
                    ip_address,
                    session.user_id,
                    {"action": "ip_address_change", "old_ip": session.ip_address, "new_ip": ip_address}
                )
                # Optionally end session for security
                # await self.end_session(session_id)
                # return None
            
            # Update last activity
            session.last_activity = current_time
            
            return session
            
        except Exception as e:
            self.logger.error(f"Session validation failed: {e}")
            return None
    
    async def end_session(self, session_id: str) -> bool:
        """
        End a user session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if session ended successfully, False otherwise
        """
        try:
            if session_id not in self.active_sessions:
                return False
            
            session = self.active_sessions[session_id]
            
            # Log session end
            await self._log_security_event(
                ThreatType.UNAUTHORIZED_ACCESS,
                SecurityLevel.LOW,
                session.ip_address,
                session.user_id,
                {"action": "session_ended", "session_id": session_id,
                 "duration": time.time() - session.created_at}
            )
            
            del self.active_sessions[session_id]
            return True
            
        except Exception as e:
            self.logger.error(f"Session end failed: {e}")
            return False
    
    async def check_rate_limit(self, identifier: str, action: str) -> bool:
        """
        Check if action is within rate limits.
        
        Args:
            identifier: Identifier for rate limiting (IP, user ID, etc.)
            action: Action being rate limited
            
        Returns:
            True if within limits, False otherwise
        """
        try:
            current_time = time.time()
            
            if identifier not in self.rate_limits:
                self.rate_limits[identifier] = {}
            
            if action not in self.rate_limits[identifier]:
                self.rate_limits[identifier][action] = {
                    "requests": [],
                    "violations": 0
                }
            
            rate_data = self.rate_limits[identifier][action]
            
            # Clean old requests
            minute_ago = current_time - 60
            hour_ago = current_time - 3600
            
            rate_data["requests"] = [
                req_time for req_time in rate_data["requests"]
                if req_time > hour_ago
            ]
            
            # Check limits
            recent_requests = [
                req_time for req_time in rate_data["requests"]
                if req_time > minute_ago
            ]
            
            requests_per_minute = len(recent_requests)
            requests_per_hour = len(rate_data["requests"])
            
            # Apply rate limits
            if action == "login_attempt":
                if requests_per_minute > 10 or requests_per_hour > 50:
                    rate_data["violations"] += 1
                    await self._log_security_event(
                        ThreatType.RATE_LIMIT_EXCEEDED,
                        SecurityLevel.HIGH,
                        identifier,
                        None,
                        {"action": action, "requests_per_minute": requests_per_minute}
                    )
                    return False
            else:
                # General rate limits
                if (requests_per_minute > self.rate_limit_windows["requests_per_minute"] or
                    requests_per_hour > self.rate_limit_windows["requests_per_hour"]):
                    rate_data["violations"] += 1
                    await self._log_security_event(
                        ThreatType.RATE_LIMIT_EXCEEDED,
                        SecurityLevel.MEDIUM,
                        identifier,
                        None,
                        {"action": action, "requests_per_minute": requests_per_minute}
                    )
                    return False
            
            # Add current request
            rate_data["requests"].append(current_time)
            return True
            
        except Exception as e:
            self.logger.error(f"Rate limit check failed: {e}")
            return True  # Allow on error
    
    async def detect_threats(self, ip_address: str, user_id: Optional[str],
                           request_data: Dict[str, Any]) -> List[ThreatType]:
        """
        Detect potential security threats.
        
        Args:
            ip_address: Client IP address
            user_id: Optional user identifier
            request_data: Request data for analysis
            
        Returns:
            List of detected threat types
        """
        threats = []
        
        try:
            if not self.enable_threat_detection:
                return threats
            
            # Check for blocked IPs
            if ip_address in self.blocked_ips:
                threats.append(ThreatType.UNAUTHORIZED_ACCESS)
            
            # Analyze request patterns
            if self.enable_behavioral_analysis:
                threats.extend(await self._analyze_behavioral_patterns(
                    ip_address, user_id, request_data
                ))
            
            # Check for malformed requests
            if await self._detect_malformed_requests(request_data):
                threats.append(ThreatType.MALFORMED_REQUEST)
            
            # Check for suspicious activity patterns
            if await self._detect_suspicious_activity(ip_address, user_id):
                threats.append(ThreatType.SUSPICIOUS_ACTIVITY)
            
            # Log detected threats
            if threats:
                await self._log_security_event(
                    threats[0],  # Primary threat
                    SecurityLevel.HIGH,
                    ip_address,
                    user_id,
                    {"detected_threats": [t.value for t in threats],
                     "request_data": request_data}
                )
            
            return threats
            
        except Exception as e:
            self.logger.error(f"Threat detection failed: {e}")
            return []
    
    async def _analyze_behavioral_patterns(self, ip_address: str, user_id: Optional[str],
                                         request_data: Dict[str, Any]) -> List[ThreatType]:
        """
        Analyze behavioral patterns for threat detection.
        
        Args:
            ip_address: Client IP address
            user_id: Optional user identifier
            request_data: Request data
            
        Returns:
            List of detected threat types
        """
        threats = []
        
        try:
            current_time = time.time()
            identifier = user_id or ip_address
            
            if identifier not in self.suspicious_activities:
                self.suspicious_activities[identifier] = []
            
            activity_log = self.suspicious_activities[identifier]
            
            # Add current activity
            activity_log.append(current_time)
            
            # Keep only recent activities (last hour)
            hour_ago = current_time - 3600
            activity_log[:] = [t for t in activity_log if t > hour_ago]
            
            # Detect rapid successive requests
            minute_ago = current_time - 60
            recent_activities = [t for t in activity_log if t > minute_ago]
            
            if len(recent_activities) > 100:  # More than 100 requests per minute
                threats.append(ThreatType.SUSPICIOUS_ACTIVITY)
            
            # Detect unusual request patterns
            if len(activity_log) > 1000:  # More than 1000 requests per hour
                threats.append(ThreatType.SUSPICIOUS_ACTIVITY)
            
            return threats
            
        except Exception as e:
            self.logger.error(f"Behavioral pattern analysis failed: {e}")
            return []
    
    async def _detect_malformed_requests(self, request_data: Dict[str, Any]) -> bool:
        """
        Detect malformed or suspicious requests.
        
        Args:
            request_data: Request data to analyze
            
        Returns:
            True if malformed request detected, False otherwise
        """
        try:
            # Check for common attack patterns
            suspicious_patterns = [
                "script", "javascript", "eval", "exec", "system",
                "union", "select", "drop", "delete", "insert",
                "../", "..\\", "/etc/passwd", "cmd.exe"
            ]
            
            # Convert request data to string for pattern matching
            request_str = str(request_data).lower()
            
            for pattern in suspicious_patterns:
                if pattern in request_str:
                    return True
            
            # Check for excessively large requests
            if len(request_str) > 100000:  # 100KB limit
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Malformed request detection failed: {e}")
            return False
    
    async def _detect_suspicious_activity(self, ip_address: str, user_id: Optional[str]) -> bool:
        """
        Detect suspicious activity patterns.
        
        Args:
            ip_address: Client IP address
            user_id: Optional user identifier
            
        Returns:
            True if suspicious activity detected, False otherwise
        """
        try:
            # Check recent security events for this IP/user
            recent_events = [
                event for event in self.security_events[-100:]  # Last 100 events
                if (event.source_ip == ip_address or event.user_id == user_id) and
                   time.time() - event.timestamp < 3600  # Last hour
            ]
            
            # Count different types of events
            event_counts = {}
            for event in recent_events:
                event_counts[event.threat_type] = event_counts.get(event.threat_type, 0) + 1
            
            # Detect patterns
            if event_counts.get(ThreatType.RATE_LIMIT_EXCEEDED, 0) > 5:
                return True
            
            if len(recent_events) > 20:  # More than 20 security events in an hour
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Suspicious activity detection failed: {e}")
            return False
    
    async def _log_security_event(self, threat_type: ThreatType, severity: SecurityLevel,
                                source_ip: str, user_id: Optional[str],
                                details: Dict[str, Any]) -> None:
        """
        Log a security event.
        
        Args:
            threat_type: Type of threat
            severity: Severity level
            source_ip: Source IP address
            user_id: Optional user identifier
            details: Event details
        """
        try:
            event = SecurityEvent(
                event_id=secrets.token_urlsafe(16),
                threat_type=threat_type,
                severity=severity,
                source_ip=source_ip,
                user_id=user_id,
                timestamp=time.time(),
                details=details,
                resolved=False
            )
            
            self.security_events.append(event)
            
            # Keep only recent events
            if len(self.security_events) > 10000:
                self.security_events = self.security_events[-5000:]
            
            # Log to system logger
            self.logger.warning(
                f"Security event: {threat_type.value}",
                extra={
                    "event_id": event.event_id,
                    "severity": severity.value,
                    "source_ip": source_ip,
                    "user_id": user_id,
                    "details": details
                }
            )
            
            # Store in Redis for distributed monitoring
            if self.redis_client:
                event_data = {
                    "event_id": event.event_id,
                    "threat_type": threat_type.value,
                    "severity": severity.value,
                    "source_ip": source_ip,
                    "user_id": user_id,
                    "timestamp": event.timestamp,
                    "details": details
                }
                
                await self.redis_client.lpush(
                    "security_events",
                    str(event_data)
                )
                
                # Keep only recent events in Redis
                await self.redis_client.ltrim("security_events", 0, 1000)
            
        except Exception as e:
            self.logger.error(f"Security event logging failed: {e}")
    
    def encrypt_data(self, data: str) -> str:
        """
        Encrypt sensitive data.
        
        Args:
            data: Data to encrypt
            
        Returns:
            Encrypted data as string
        """
        try:
            encrypted_bytes = self.cipher_suite.encrypt(data.encode())
            return encrypted_bytes.decode()
        except Exception as e:
            self.logger.error(f"Data encryption failed: {e}")
            raise
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """
        Decrypt sensitive data.
        
        Args:
            encrypted_data: Encrypted data string
            
        Returns:
            Decrypted data
        """
        try:
            decrypted_bytes = self.cipher_suite.decrypt(encrypted_data.encode())
            return decrypted_bytes.decode()
        except Exception as e:
            self.logger.error(f"Data decryption failed: {e}")
            raise
    
    def hash_password(self, password: str) -> str:
        """
        Hash a password securely.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        return self.pwd_context.hash(password)
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            password: Plain text password
            hashed_password: Hashed password
            
        Returns:
            True if password matches, False otherwise
        """
        return self.pwd_context.verify(password, hashed_password)
    
    async def _security_monitoring(self) -> None:
        """
        Background task for continuous security monitoring.
        
        Monitors security events, detects patterns, and triggers
        automated responses to security threats.
        """
        while True:
            try:
                if self.enable_real_time_monitoring:
                    # Analyze recent security events
                    await self._analyze_security_trends()
                    
                    # Update threat counters
                    await self._update_threat_counters()
                    
                    # Check for automated responses
                    await self._check_automated_responses()
                
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Security monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def _analyze_security_trends(self) -> None:
        """Analyze security event trends."""
        try:
            if not self.security_events:
                return
            
            # Analyze events from last hour
            hour_ago = time.time() - 3600
            recent_events = [
                event for event in self.security_events
                if event.timestamp > hour_ago
            ]
            
            if not recent_events:
                return
            
            # Count events by type
            event_counts = {}
            for event in recent_events:
                event_counts[event.threat_type] = event_counts.get(event.threat_type, 0) + 1
            
            # Log trends
            self.logger.debug("Security trends analysis",
                            extra={"event_counts": {k.value: v for k, v in event_counts.items()},
                                  "total_events": len(recent_events)})
            
        except Exception as e:
            self.logger.error(f"Security trends analysis failed: {e}")
    
    async def _update_threat_counters(self) -> None:
        """Update threat counters for monitoring."""
        try:
            current_time = time.time()
            hour_ago = current_time - 3600
            
            # Reset hourly counters
            for ip in list(self.threat_counters.keys()):
                if ip not in self.threat_counters:
                    continue
                
                # Clean old entries
                for threat_type in list(self.threat_counters[ip].keys()):
                    if self.threat_counters[ip][threat_type] == 0:
                        del self.threat_counters[ip][threat_type]
                
                if not self.threat_counters[ip]:
                    del self.threat_counters[ip]
            
        except Exception as e:
            self.logger.error(f"Threat counter update failed: {e}")
    
    async def _check_automated_responses(self) -> None:
        """Check for and execute automated security responses."""
        try:
            # Check for IPs that should be blocked
            for ip, counters in self.threat_counters.items():
                total_threats = sum(counters.values())
                
                if total_threats > 50:  # Threshold for auto-blocking
                    if ip not in self.blocked_ips:
                        self.blocked_ips.add(ip)
                        await self._log_security_event(
                            ThreatType.UNAUTHORIZED_ACCESS,
                            SecurityLevel.CRITICAL,
                            ip,
                            None,
                            {"action": "auto_blocked", "threat_count": total_threats}
                        )
            
        except Exception as e:
            self.logger.error(f"Automated response check failed: {e}")
    
    async def _security_cleanup(self) -> None:
        """
        Background task for security data cleanup.
        
        Cleans up old security events, expired sessions, and
        maintains optimal performance of security systems.
        """
        while True:
            try:
                current_time = time.time()
                
                # Clean up expired sessions
                expired_sessions = []
                for session_id, session in self.active_sessions.items():
                    if current_time - session.last_activity > self.session_timeout:
                        expired_sessions.append(session_id)
                
                for session_id in expired_sessions:
                    await self.end_session(session_id)
                
                # Clean up old security events
                day_ago = current_time - 86400
                self.security_events = [
                    event for event in self.security_events
                    if event.timestamp > day_ago
                ]
                
                # Clean up old rate limit data
                for identifier in list(self.rate_limits.keys()):
                    for action in list(self.rate_limits[identifier].keys()):
                        rate_data = self.rate_limits[identifier][action]
                        rate_data["requests"] = [
                            req_time for req_time in rate_data["requests"]
                            if req_time > day_ago
                        ]
                        
                        if not rate_data["requests"]:
                            del self.rate_limits[identifier][action]
                    
                    if not self.rate_limits[identifier]:
                        del self.rate_limits[identifier]
                
                await asyncio.sleep(3600)  # Clean up every hour
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Security cleanup error: {e}")
                await asyncio.sleep(3600)
    
    async def _load_security_state(self) -> None:
        """Load existing security state from Redis."""
        try:
            if not self.redis_client:
                return
            
            # Load blocked IPs
            blocked_ips = await self.redis_client.smembers("blocked_ips")
            self.blocked_ips = {ip.decode() for ip in blocked_ips}
            
            # Load recent security events
            events_data = await self.redis_client.lrange("security_events", 0, 100)
            for event_data in events_data:
                try:
                    event_dict = eval(event_data.decode())  # Use json.loads in production
                    # Reconstruct SecurityEvent objects if needed
                except Exception:
                    continue
            
            self.logger.info("Security state loaded from Redis")
            
        except Exception as e:
            self.logger.error(f"Security state loading failed: {e}")
    
    async def get_security_status(self) -> Dict[str, Any]:
        """
        Get comprehensive security status.
        
        Returns:
            Dict containing security status and metrics
        """
        try:
            current_time = time.time()
            hour_ago = current_time - 3600
            
            # Count recent events
            recent_events = [
                event for event in self.security_events
                if event.timestamp > hour_ago
            ]
            
            event_counts = {}
            for event in recent_events:
                event_counts[event.threat_type.value] = event_counts.get(event.threat_type.value, 0) + 1
            
            return {
                "status": "secure",
                "active_sessions": len(self.active_sessions),
                "blocked_ips": len(self.blocked_ips),
                "recent_events": len(recent_events),
                "event_breakdown": event_counts,
                "threat_detection_enabled": self.enable_threat_detection,
                "behavioral_analysis_enabled": self.enable_behavioral_analysis,
                "monitoring_enabled": self.enable_real_time_monitoring,
                "security_policies": self.security_policies
            }
            
        except Exception as e:
            self.logger.error(f"Security status retrieval failed: {e}")
            return {"status": "error", "error": str(e)}
    
    async def cleanup(self) -> None:
        """
        Cleanup security manager resources.
        
        Stops background tasks, saves security state, and releases resources.
        """
        self.logger.info("Cleaning up security manager")
        
        try:
            # Cancel background tasks
            for task in [self.monitoring_task, self.cleanup_task]:
                if task and not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            
            # Save security state to Redis
            if self.redis_client:
                # Save blocked IPs
                if self.blocked_ips:
                    await self.redis_client.delete("blocked_ips")
                    await self.redis_client.sadd("blocked_ips", *self.blocked_ips)
                
                await self.redis_client.close()
            
            # Clear sensitive data
            self.active_sessions.clear()
            self.security_events.clear()
            self.rate_limits.clear()
            self.threat_counters.clear()
            
            self.logger.info("Security manager cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Security manager cleanup failed: {e}")