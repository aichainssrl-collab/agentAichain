"""Tests for API versioning middleware (B9)."""

import pytest
from httpx import ASGITransport, AsyncClient
from agent_aichain.main import app


@pytest.mark.asyncio
async def test_version_header_on_all_responses():
    """All /api/v1/ responses should include API-Version header."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/auth/token")
        assert resp.headers.get("api-version") == "v1"
        assert "v1" in resp.headers.get("api-supported-versions", "")


@pytest.mark.asyncio
async def test_accept_version_header_override():
    """Accept-Version header should override URL path version."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/api/v1/auth/token",
            headers={"Accept-Version": "v2"},
        )
        assert resp.headers.get("api-version") == "v2"


@pytest.mark.asyncio
async def test_non_versioned_path_still_gets_header():
    """Non-API-versioned paths (e.g. /health) still get the header."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.headers.get("api-version") == "v1"


@pytest.mark.asyncio
async def test_sunset_version_returns_410():
    """When SUNSET_VERSION is set, requests to that version return 410."""
    from agent_aichain.api import versioning

    original = versioning.SUNSET_VERSION
    versioning.SUNSET_VERSION = "v1"

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/auth/token")
            assert resp.status_code == 410
            assert "retired" in resp.json()["detail"]
    finally:
        versioning.SUNSET_VERSION = original


@pytest.mark.asyncio
async def test_deprecated_version_adds_deprecation_headers():
    """When DEPRECATED_VERSION is set, responses include Deprecation + Sunset."""
    from agent_aichain.api import versioning

    original_dep = versioning.DEPRECATED_VERSION
    versioning.DEPRECATED_VERSION = "v1"

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/auth/token")
            assert resp.headers.get("deprecation") == "true"
            assert "sunset" in resp.headers
    finally:
        versioning.DEPRECATED_VERSION = original_dep


@pytest.mark.asyncio
async def test_link_header_present():
    """Response should include Link header with docs relation."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/auth/token")
        assert "service-desc" in resp.headers.get("link", "")
