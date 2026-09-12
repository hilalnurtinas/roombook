import os
from collections.abc import AsyncIterator

import pytest
from dotenv import load_dotenv
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import get_session
from app.main import app

load_dotenv()

TEST_DATABASE_URL = os.environ["TEST_DATABASE_URL"]


@pytest.fixture
async def test_session() -> AsyncIterator[AsyncSession]:
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.connect() as connection:
        transaction = await connection.begin()
        session_factory = async_sessionmaker(bind=connection, expire_on_commit=False)
        session = session_factory()
        try:
            yield session
        finally:
            await session.close()
            await transaction.rollback()
    await engine.dispose()


@pytest.fixture
async def two_real_sessions() -> AsyncIterator[tuple[AsyncSession, AsyncSession]]:
    """Two independent, really-committing DB connections for testing true concurrency —
    `test_session` shares one rolled-back transaction and can't model two concurrent
    transactions racing against the exclusion constraint (see plan 0002's risk note).
    """
    engine = create_async_engine(TEST_DATABASE_URL)
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    session_a = session_factory()
    session_b = session_factory()
    try:
        yield session_a, session_b
    finally:
        await session_a.close()
        await session_b.close()
        async with engine.connect() as conn:
            await conn.execute(text("DELETE FROM bookings"))
            await conn.execute(text("DELETE FROM rooms"))
            await conn.execute(text("DELETE FROM users"))
            await conn.commit()
        await engine.dispose()


@pytest.fixture
async def client(test_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    async def override_get_session() -> AsyncIterator[AsyncSession]:
        yield test_session

    app.dependency_overrides[get_session] = override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
