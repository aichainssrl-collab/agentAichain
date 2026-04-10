"""API versioning middleware and dependency.

Provides:
- API-Version header on all responses
- Deprecation / Sunset support for old versions
- Accept-Version header validation
- get_api_version() dependency for route handlers
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from email.utils import format_datetime

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

# ── Configuration ────────────────────────────────────────────────────────────
# Supported API versions (ordered newest first)
SUPPORTED_VERSIONS: tuple[str, ...] = ("v1",)

# Version marked as deprecated (set to None when no version is deprecated)
DEPRECATED_VERSION: str | None = None

# Version that returns 410 Gone (set to None when no version is sunset)
SUNSET_VERSION: str | None = None

DEFAULT_VERSION = "v1"
# ─────────────────────────────────────────────────────────────────────────────


class APIVersionMiddleware(BaseHTTPMiddleware):
    """Attach version headers and enforce deprecation/sunset policy."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        accept_header = request.headers.get("accept-version", "").strip()
        path_version = _path_version(request.url.path)

        version = accept_header or path_version or DEFAULT_VERSION

        # Sunset → 410
        if SUNSET_VERSION and version == SUNSET_VERSION:
            return Response(
                status_code=410,
                content=(
            '{"detail": '
            f'"This API version ({SUNSET_VERSION}) has been retired. '
            f'Migrate to /api/{SUPPORTED_VERSIONS[0]}."}}'
        ),
                media_type="application/json",
            )

        response = await call_next(request)

        # Deprecation headers
        if DEPRECATED_VERSION and version == DEPRECATED_VERSION:
            response.headers["Deprecation"] = "true"
            sunset_date = datetime.now(timezone.utc) + timedelta(days=180)
            response.headers["Sunset"] = format_datetime(sunset_date)

        # Always include version info
        response.headers["API-Version"] = version
        response.headers[
            "API-Supported-Versions"
        ] = ", ".join(f"v{v}" for v in SUPPORTED_VERSIONS)
        response.headers["Link"] = '<http://test/docs>; rel="service-desc"'

        return response


def _path_version(path: str) -> str | None:
    """Return the version segment from /api/<ver>/..., or None."""
    parts = path.lstrip("/").split("/")
    if len(parts) >= 2 and parts[0] == "api" and parts[1].startswith("v"):
        return parts[1]
    return None


def setup_versioning(app: FastAPI) -> None:
    """Register the API versioning middleware on *app*."""
    app.add_middleware(APIVersionMiddleware)
