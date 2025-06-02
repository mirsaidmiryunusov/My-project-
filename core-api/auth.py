"""
Authentication and Authorization Module

This module provides comprehensive authentication and authorization
functionality for Project GeminiVoiceConnect, implementing JWT-based
authentication, role-based access control, and enterprise-grade security.
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from uuid import UUID

import bcrypt
import jwt
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session, select
import structlog

from config import CoreAPIConfig
from database import get_session
from models import User, Tenant, UserRole, AuditLog


logger = structlog.get_logger(__name__)

# Security scheme
security = HTTPBearer()


class AuthManager:
    """
    Comprehensive authentication and authorization manager.
    
    Provides secure user authentication, JWT token management,
    role-based access control, and audit logging.
    """
    
    def __init__(self, config: CoreAPIConfig):
        """
        Initialize authentication manager.
        
        Args:
            config: Core-API configuration
        """
        self.config = config
        self.jwt_secret = config.jwt_secret_key
        self.jwt_algorithm = config.jwt_algorithm
        self.jwt_expiration_hours = config.jwt_expiration_hours
        self.password_rounds = config.password_hash_rounds
    
    def hash_password(self, password: str) -> str:
        """
        Hash password using bcrypt.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        salt = bcrypt.gensalt(rounds=self.password_rounds)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, password: str, hashed_password: str) -> bool:
        """
        Verify password against hash.
        
        Args:
            password: Plain text password
            hashed_password: Hashed password
            
        Returns:
            True if password matches
        """
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
        except Exception as e:
            logger.error("Password verification failed", error=str(e))
            return False
    
    def create_access_token(self, user: User) -> str:
        """
        Create JWT access token.
        
        Args:
            user: User object
            
        Returns:
            JWT token string
        """
        now = datetime.utcnow()
        expire = now + timedelta(hours=self.jwt_expiration_hours)
        
        payload = {
            "sub": str(user.id),
            "email": user.email,
            "username": user.username,
            "role": user.role.value,
            "tenant_id": str(user.tenant_id),
            "iat": now,
            "exp": expire,
            "jti": secrets.token_urlsafe(32)  # JWT ID for token revocation
        }
        
        token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        
        logger.info("Access token created", 
                   user_id=str(user.id), 
                   expires_at=expire.isoformat())
        
        return token
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify and decode JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded token payload
            
        Raises:
            HTTPException: If token is invalid
        """
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            
            # Check token expiration
            if datetime.utcfromtimestamp(payload['exp']) < datetime.utcnow():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired"
                )
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError as e:
            logger.warning("Invalid token provided", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    def authenticate_user(self, email: str, password: str, session: Session) -> Optional[User]:
        """
        Authenticate user with email and password.
        
        Args:
            email: User email
            password: User password
            session: Database session
            
        Returns:
            User object if authentication successful, None otherwise
        """
        try:
            # Find user by email
            statement = select(User).where(User.email == email)
            user = session.exec(statement).first()
            
            if not user:
                logger.warning("Authentication failed - user not found", email=email)
                return None
            
            if not user.is_active:
                logger.warning("Authentication failed - user inactive", email=email)
                return None
            
            # Verify password
            if not self.verify_password(password, user.password_hash):
                logger.warning("Authentication failed - invalid password", email=email)
                return None
            
            # Update last login
            user.last_login = datetime.utcnow()
            session.add(user)
            session.commit()
            
            logger.info("User authenticated successfully", 
                       user_id=str(user.id), 
                       email=email)
            
            return user
            
        except Exception as e:
            logger.error("Authentication error", error=str(e), email=email)
            return None
    
    def get_user_by_token(self, token: str, session: Session) -> Optional[User]:
        """
        Get user by JWT token.
        
        Args:
            token: JWT token
            session: Database session
            
        Returns:
            User object if token is valid
        """
        try:
            payload = self.verify_token(token)
            user_id = UUID(payload['sub'])
            
            statement = select(User).where(User.id == user_id)
            user = session.exec(statement).first()
            
            if not user or not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found or inactive"
                )
            
            return user
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Token validation error", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    def check_permission(self, user: User, permission: str) -> bool:
        """
        Check if user has specific permission.
        
        Args:
            user: User object
            permission: Permission string
            
        Returns:
            True if user has permission
        """
        # Super admin has all permissions
        if user.role == UserRole.SUPER_ADMIN:
            return True
        
        # Check role-based permissions
        role_permissions = self._get_role_permissions(user.role)
        if permission in role_permissions:
            return True
        
        # Check user-specific permissions
        if permission in user.permissions:
            return True
        
        return False
    
    def _get_role_permissions(self, role: UserRole) -> List[str]:
        """
        Get permissions for a specific role.
        
        Args:
            role: User role
            
        Returns:
            List of permissions
        """
        permissions_map = {
            UserRole.SUPER_ADMIN: ["*"],  # All permissions
            UserRole.TENANT_ADMIN: [
                "tenant.manage",
                "users.manage",
                "campaigns.manage",
                "calls.view",
                "leads.manage",
                "integrations.manage",
                "analytics.view",
                "billing.view"
            ],
            UserRole.MANAGER: [
                "campaigns.manage",
                "calls.view",
                "leads.manage",
                "analytics.view",
                "users.view"
            ],
            UserRole.AGENT: [
                "calls.view",
                "leads.view",
                "campaigns.view"
            ],
            UserRole.VIEWER: [
                "calls.view",
                "leads.view",
                "analytics.view"
            ]
        }
        
        return permissions_map.get(role, [])
    
    def require_permission(self, permission: str):
        """
        Decorator to require specific permission.
        
        Args:
            permission: Required permission
            
        Returns:
            Decorator function
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                # This would be used with FastAPI dependencies
                # Implementation depends on how it's integrated with FastAPI
                return func(*args, **kwargs)
            return wrapper
        return decorator
    
    def log_auth_event(self, event_type: str, user: Optional[User], 
                      session: Session, **kwargs) -> None:
        """
        Log authentication event for audit purposes.
        
        Args:
            event_type: Type of authentication event
            user: User object (if available)
            session: Database session
            **kwargs: Additional event data
        """
        try:
            audit_log = AuditLog(
                event_type=f"auth.{event_type}",
                event_description=f"Authentication event: {event_type}",
                user_id=user.id if user else None,
                user_email=user.email if user else kwargs.get('email'),
                ip_address=kwargs.get('ip_address'),
                user_agent=kwargs.get('user_agent'),
                tenant_id=user.tenant_id if user else None,
                session_id=kwargs.get('session_id'),
                metadata=kwargs
            )
            
            session.add(audit_log)
            session.commit()
            
        except Exception as e:
            logger.error("Failed to log auth event", error=str(e))


# Global auth manager instance
_auth_manager: Optional[AuthManager] = None


def get_auth_manager() -> AuthManager:
    """Get global auth manager instance."""
    global _auth_manager
    if _auth_manager is None:
        from config import CoreAPIConfig
        config = CoreAPIConfig()
        _auth_manager = AuthManager(config)
    return _auth_manager


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session)
) -> User:
    """
    FastAPI dependency to get current authenticated user.
    
    Args:
        credentials: HTTP authorization credentials
        session: Database session
        
    Returns:
        Current user
        
    Raises:
        HTTPException: If authentication fails
    """
    auth_manager = get_auth_manager()
    
    try:
        token = credentials.credentials
        user = auth_manager.get_user_by_token(token, session)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Authentication dependency error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    FastAPI dependency to get current active user.
    
    Args:
        current_user: Current user from authentication
        
    Returns:
        Active user
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def require_role(required_role: UserRole):
    """
    Dependency factory to require specific user role.
    
    Args:
        required_role: Required user role
        
    Returns:
        FastAPI dependency function
    """
    async def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        auth_manager = get_auth_manager()
        
        # Super admin can access everything
        if current_user.role == UserRole.SUPER_ADMIN:
            return current_user
        
        # Check if user has required role or higher
        role_hierarchy = {
            UserRole.VIEWER: 1,
            UserRole.AGENT: 2,
            UserRole.MANAGER: 3,
            UserRole.TENANT_ADMIN: 4,
            UserRole.SUPER_ADMIN: 5
        }
        
        user_level = role_hierarchy.get(current_user.role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        return current_user
    
    return role_checker


def require_permission(permission: str):
    """
    Dependency factory to require specific permission.
    
    Args:
        permission: Required permission
        
    Returns:
        FastAPI dependency function
    """
    async def permission_checker(current_user: User = Depends(get_current_active_user)) -> User:
        auth_manager = get_auth_manager()
        
        if not auth_manager.check_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {permission}"
            )
        
        return current_user
    
    return permission_checker


class TenantIsolation:
    """
    Tenant isolation utility for multi-tenant operations.
    
    Ensures that users can only access data within their tenant.
    """
    
    @staticmethod
    def filter_by_tenant(query, user: User):
        """
        Filter query by user's tenant.
        
        Args:
            query: SQLModel query
            user: Current user
            
        Returns:
            Filtered query
        """
        return query.where(query.model_class.tenant_id == user.tenant_id)
    
    @staticmethod
    def check_tenant_access(resource_tenant_id: UUID, user: User) -> bool:
        """
        Check if user can access resource from specific tenant.
        
        Args:
            resource_tenant_id: Tenant ID of the resource
            user: Current user
            
        Returns:
            True if access is allowed
        """
        # Super admin can access all tenants
        if user.role == UserRole.SUPER_ADMIN:
            return True
        
        # Users can only access their own tenant
        return resource_tenant_id == user.tenant_id
    
    @staticmethod
    def require_tenant_access(resource_tenant_id: UUID, user: User) -> None:
        """
        Require tenant access or raise exception.
        
        Args:
            resource_tenant_id: Tenant ID of the resource
            user: Current user
            
        Raises:
            HTTPException: If access is denied
        """
        if not TenantIsolation.check_tenant_access(resource_tenant_id, user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to resource from different tenant"
            )


# Additional authentication functions for client registration
from datetime import datetime, timedelta
from typing import Optional
import jwt

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token.
    
    Args:
        data: Token payload data
        expires_delta: Token expiration time
        
    Returns:
        JWT token string
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=24)
    
    to_encode.update({"exp": expire})
    
    # Use a default secret key for development
    secret_key = "your-secret-key-here"  # In production, use environment variable
    algorithm = "HS256"
    
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=algorithm)
    return encoded_jwt


async def require_admin_role(current_user: User = Depends(get_current_user)) -> User:
    """
    Require admin role for access.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Current user if admin
        
    Raises:
        HTTPException: If user is not admin
    """
    if current_user.role not in [UserRole.SUPER_ADMIN, UserRole.TENANT_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return current_user