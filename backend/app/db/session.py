from typing import AsyncGenerator

from app.db.engine import async_session_factory


async def get_db() -> AsyncGenerator:
    """Get database session."""
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
