from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings

# Async engine with PgBouncer connection pooling support
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True
)

# Async session factory
async_session_factory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_db() -> AsyncSession: # type: ignore
    """
    FastAPI dependency that provides an async session per request.
    This session will be used to set the RLS context.
    """
    async with async_session_factory() as session:
        yield session
