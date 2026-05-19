from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_liveness(async_client: AsyncClient) -> None:
    response = await async_client.get("/api/v1/health/liveness")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_health_check_db_ok(async_client: AsyncClient) -> None:
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock()

    with patch(
        "app.api.v1.health.get_db_session",
        return_value=_session_dependency(mock_session),
    ):
        response = await async_client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "environment" in data


async def _session_dependency(session):
    yield session
