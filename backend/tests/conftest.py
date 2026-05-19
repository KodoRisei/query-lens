import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from app.core.logging import configure_logging
from app.main import app

# Structlog must be configured before any module-level logger is called.
# Without this, `add_logger_name` fails because tests use PrintLogger, not stdlib Logger.
configure_logging()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
async def async_client() -> AsyncClient:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
