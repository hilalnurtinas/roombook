from collections.abc import AsyncIterator

from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import get_session
from app.main import app


async def test_health_returns_ok_and_connected(client: AsyncClient) -> None:
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "connected"}


async def test_health_returns_503_when_database_unreachable() -> None:
    unreachable_engine = create_async_engine(
        "postgresql+asyncpg://roombook:roombook@localhost:1/does_not_matter"
    )
    session_factory = async_sessionmaker(unreachable_engine, expire_on_commit=False)

    async def override_get_session() -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.get("/health")
    finally:
        app.dependency_overrides.clear()
        await unreachable_engine.dispose()

    assert response.status_code == 503
    assert response.json() == {"status": "error", "database": "unreachable"}
