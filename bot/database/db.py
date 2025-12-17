"""
Database connection and session management
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
    AsyncEngine
)
from sqlalchemy.pool import NullPool
from loguru import logger

from bot.config import settings
from bot.database.models import Base


class Database:
    """Database manager"""
    
    def __init__(self):
        self.engine: AsyncEngine | None = None
        self.session_factory: async_sessionmaker[AsyncSession] | None = None
    
    async def connect(self):
        """Initialize database connection"""
        try:
            # Create async engine
            self.engine = create_async_engine(
                settings.database_url,
                echo=settings.debug,
                poolclass=NullPool,  # Railway works better with NullPool
                pool_pre_ping=True
            )
            
            # Create session factory
            self.session_factory = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False,
                autocommit=False
            )
            
            logger.info("✅ Database connected successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to database: {e}")
            raise
    
    async def disconnect(self):
        """Close database connection"""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connection closed")
    
    async def create_tables(self):
        """Create all tables"""
        if not self.engine:
            raise RuntimeError("Database not connected")
        
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("✅ Database tables created")
        except Exception as e:
            logger.error(f"❌ Failed to create tables: {e}")
            raise
    
    async def drop_tables(self):
        """Drop all tables (use with caution!)"""
        if not self.engine:
            raise RuntimeError("Database not connected")
        
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        logger.warning("⚠️ All tables dropped")
    
    def get_session(self) -> AsyncSession:
        """Get a new database session"""
        if not self.session_factory:
            raise RuntimeError("Database not connected")
        return self.session_factory()
    
    async def session_generator(self) -> AsyncGenerator[AsyncSession, None]:
        """Generate database session (for dependencies)"""
        async with self.get_session() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()


# Global database instance
db = Database()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database session"""
    async for session in db.session_generator():
        yield session
