"""
Integration test fixtures.

These tests require a running PostgreSQL instance and are skipped by default.
Set INTEGRATION_TESTS=1 to enable them:

    INTEGRATION_TESTS=1 DATABASE_URL=postgresql+asyncpg://... pytest tests/integration/
"""

import os
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.logging import configure_logging
from app.infrastructure.database.connection import get_db_session
from app.infrastructure.database.models import Base
from app.main import app

configure_logging()

TEST_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://user:password@localhost:5432/querylens_test",
)


def pytest_collection_modifyitems(config, items):
    if os.getenv("INTEGRATION_TESTS") != "1":
        skip = pytest.mark.skip(reason="Set INTEGRATION_TESTS=1 to run integration tests")
        for item in items:
            if "integration" in str(item.fspath):
                item.add_marker(skip)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Provides a real async session backed by the test database.

    Schema is created on first use (idempotent). Data is wiped after each test
    so tests are fully isolated without savepoint tricks.
    """
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session = AsyncSession(engine, expire_on_commit=False)
    try:
        yield session
    finally:
        await session.close()
        # Wipe all rows so the next test starts clean.
        async with engine.begin() as conn:
            await conn.execute(text("TRUNCATE TABLE query_reviews"))
        await engine.dispose()


@pytest_asyncio.fixture
async def api_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """HTTP test client with the test DB session injected into all Depends."""

    async def override_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db_session] = override_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

    app.dependency_overrides.pop(get_db_session, None)
