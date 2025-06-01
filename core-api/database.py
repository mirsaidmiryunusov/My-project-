"""
Database Management Module

This module provides comprehensive database management functionality for
the core-api microservice, implementing connection management, session
handling, and database initialization for Project GeminiVoiceConnect.
"""

import asyncio
import logging
from typing import AsyncGenerator, Optional, Dict, Any
from contextlib import asynccontextmanager

from sqlmodel import SQLModel, create_engine, Session, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import event, text
import structlog

from config import CoreAPIConfig


logger = structlog.get_logger(__name__)


class DatabaseManager:
    """
    Comprehensive database management system.
    
    Provides connection pooling, session management, health monitoring,
    and database initialization for optimal performance and reliability.
    """
    
    def __init__(self, config: CoreAPIConfig):
        """
        Initialize database manager.
        
        Args:
            config: Core-API configuration
        """
        self.config = config
        self.engine = None
        self.async_engine = None
        self.session_factory = None
        self.async_session_factory = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize database connections and create tables."""
        try:
            # Create synchronous engine
            self.engine = create_engine(
                self.config.database_url,
                pool_size=self.config.db_pool_size,
                max_overflow=self.config.db_max_overflow,
                echo=self.config.db_echo,
                pool_pre_ping=True,
                pool_recycle=3600
            )
            
            # Create asynchronous engine if using async database URL
            if "postgresql" in self.config.database_url:
                async_url = self.config.database_url.replace("postgresql://", "postgresql+asyncpg://")
                self.async_engine = create_async_engine(
                    async_url,
                    pool_size=self.config.db_pool_size,
                    max_overflow=self.config.db_max_overflow,
                    echo=self.config.db_echo,
                    pool_pre_ping=True,
                    pool_recycle=3600
                )
                
                self.async_session_factory = async_sessionmaker(
                    self.async_engine,
                    class_=AsyncSession,
                    expire_on_commit=False
                )
            
            # Setup event listeners
            self._setup_event_listeners()
            
            # Create all tables
            await self._create_tables()
            
            self._initialized = True
            logger.info("Database manager initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize database manager", error=str(e))
            raise
    
    def _setup_event_listeners(self) -> None:
        """Setup database event listeners for monitoring and optimization."""
        
        @event.listens_for(self.engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """Set SQLite pragmas for optimal performance."""
            if "sqlite" in self.config.database_url:
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.execute("PRAGMA cache_size=10000")
                cursor.execute("PRAGMA temp_store=MEMORY")
                cursor.close()
        
        @event.listens_for(self.engine, "checkout")
        def receive_checkout(dbapi_connection, connection_record, connection_proxy):
            """Log database connection checkout."""
            logger.debug("Database connection checked out")
        
        @event.listens_for(self.engine, "checkin")
        def receive_checkin(dbapi_connection, connection_record):
            """Log database connection checkin."""
            logger.debug("Database connection checked in")
    
    async def _create_tables(self) -> None:
        """Create all database tables."""
        try:
            # Import all models to ensure they're registered
            from models import *
            
            if self.async_engine:
                async with self.async_engine.begin() as conn:
                    await conn.run_sync(SQLModel.metadata.create_all)
            else:
                SQLModel.metadata.create_all(self.engine)
            
            logger.info("Database tables created successfully")
            
        except Exception as e:
            logger.error("Failed to create database tables", error=str(e))
            raise
    
    def get_session(self) -> Session:
        """
        Get a synchronous database session.
        
        Returns:
            Database session
        """
        if not self._initialized:
            raise RuntimeError("Database manager not initialized")
        
        return Session(self.engine)
    
    @asynccontextmanager
    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get an asynchronous database session.
        
        Yields:
            Async database session
        """
        if not self._initialized or not self.async_session_factory:
            raise RuntimeError("Async database manager not initialized")
        
        async with self.async_session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform database health check.
        
        Returns:
            Health check results
        """
        try:
            # Test synchronous connection
            with self.get_session() as session:
                result = session.exec(text("SELECT 1")).first()
                sync_healthy = result == 1
            
            # Test asynchronous connection if available
            async_healthy = True
            if self.async_engine:
                async with self.get_async_session() as session:
                    result = await session.exec(text("SELECT 1"))
                    async_healthy = result.first() == 1
            
            # Get connection pool status
            pool_status = self._get_pool_status()
            
            return {
                "status": "healthy" if sync_healthy and async_healthy else "unhealthy",
                "sync_connection": sync_healthy,
                "async_connection": async_healthy,
                "pool_status": pool_status,
                "initialized": self._initialized
            }
            
        except Exception as e:
            logger.error("Database health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e),
                "initialized": self._initialized
            }
    
    def _get_pool_status(self) -> Dict[str, Any]:
        """Get database connection pool status."""
        try:
            pool = self.engine.pool
            return {
                "size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "invalid": pool.invalid()
            }
        except Exception as e:
            logger.error("Failed to get pool status", error=str(e))
            return {"error": str(e)}
    
    async def cleanup(self) -> None:
        """Cleanup database connections."""
        try:
            if self.engine:
                self.engine.dispose()
            
            if self.async_engine:
                await self.async_engine.dispose()
            
            self._initialized = False
            logger.info("Database manager cleanup completed")
            
        except Exception as e:
            logger.error("Database cleanup failed", error=str(e))


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


async def init_db(config: CoreAPIConfig) -> DatabaseManager:
    """
    Initialize global database manager.
    
    Args:
        config: Core-API configuration
        
    Returns:
        Database manager instance
    """
    global _db_manager
    
    if _db_manager is None:
        _db_manager = DatabaseManager(config)
        await _db_manager.initialize()
    
    return _db_manager


def get_db_manager() -> DatabaseManager:
    """
    Get global database manager instance.
    
    Returns:
        Database manager instance
    """
    if _db_manager is None:
        raise RuntimeError("Database manager not initialized")
    
    return _db_manager


def get_session() -> Session:
    """
    Get database session dependency for FastAPI.
    
    Yields:
        Database session
    """
    db_manager = get_db_manager()
    with db_manager.get_session() as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get async database session dependency for FastAPI.
    
    Yields:
        Async database session
    """
    db_manager = get_db_manager()
    async with db_manager.get_async_session() as session:
        yield session


class DatabaseTransaction:
    """
    Database transaction context manager for complex operations.
    
    Provides automatic transaction management with rollback on errors
    and commit on success.
    """
    
    def __init__(self, session: Session):
        """
        Initialize transaction manager.
        
        Args:
            session: Database session
        """
        self.session = session
        self._transaction = None
    
    def __enter__(self):
        """Enter transaction context."""
        self._transaction = self.session.begin()
        return self.session
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit transaction context."""
        if exc_type is not None:
            self._transaction.rollback()
            logger.error("Transaction rolled back due to error", 
                        error_type=exc_type.__name__ if exc_type else None)
        else:
            self._transaction.commit()
            logger.debug("Transaction committed successfully")


class AsyncDatabaseTransaction:
    """
    Async database transaction context manager.
    
    Provides automatic async transaction management with rollback on errors
    and commit on success.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize async transaction manager.
        
        Args:
            session: Async database session
        """
        self.session = session
        self._transaction = None
    
    async def __aenter__(self):
        """Enter async transaction context."""
        self._transaction = await self.session.begin()
        return self.session
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async transaction context."""
        if exc_type is not None:
            await self._transaction.rollback()
            logger.error("Async transaction rolled back due to error",
                        error_type=exc_type.__name__ if exc_type else None)
        else:
            await self._transaction.commit()
            logger.debug("Async transaction committed successfully")