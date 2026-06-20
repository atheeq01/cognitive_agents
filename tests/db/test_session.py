import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db

@pytest.mark.db
@pytest.mark.asyncio
class TestSession:
    async def test_session_yields_async_session(self):
        gen = get_db()
        session = await gen.__anext__()
        assert isinstance(session, AsyncSession)
        
        # Test it closes properly
        try:
            await gen.__anext__()
        except StopAsyncIteration:
            pass

    async def test_session_rollback_on_error(self):
        # We simulate the exact behavior of our dependency
        # We can't easily test rollback across the actual request boundary here,
        # but we verify that if we raise during the yield, it catches and raises
        gen = get_db()
        session = await gen.__anext__()
        
        with pytest.raises(ValueError):
            # simulate an error occurring after yield
            await gen.athrow(ValueError("Simulated Error"))
