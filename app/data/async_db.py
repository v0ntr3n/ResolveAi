"""Async database layer using SQLAlchemy async support."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings


def get_async_engine():
    """Create async database engine.
    
    Converts sqlite:// to sqlite+aiosqlite:// for async support.
    """
    settings = get_settings()
    # Convert sqlite:// to sqlite+aiosqlite://
    db_url = settings.DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://")
    return create_async_engine(db_url, echo=False)


def get_async_session_factory() -> async_sessionmaker[AsyncSession]:
    """Create async session factory.
    
    Returns:
        async_sessionmaker for creating async database sessions.
    """
    engine = get_async_engine()
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for async database session.
    
    Yields:
        AsyncSession for database operations.
    
    Example:
        @router.post("/chat")
        async def chat(session: AsyncSession = Depends(get_async_db)):
            result = await session.execute(query)
    """
    async_session_factory = get_async_session_factory()
    async with async_session_factory() as session:
        yield session
