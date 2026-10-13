"""Bearer API-key auth (design §9): every route except /healthz."""
from __future__ import annotations

import hmac

from fastapi import Request

from .errors import ApiError


async def require_api_key(request: Request) -> None:
    import os

    config = request.app.state.config
    accepted = [config.api_key] + [
        k.strip() for k in os.environ.get("REQ3_API_KEYS", "").split(",") if k.strip()
    ]
    provided = request.headers.get("authorization", "")
    provided_key = request.headers.get("x-api-key", "")
    ok = any(
        key and (
            hmac.compare_digest(provided.encode(), f"Bearer {key}".encode())
            or hmac.compare_digest(provided_key.encode(), key.encode())
        )
        for key in accepted
    )
    if not ok:
        raise ApiError(
            401, "unauthorized",
            "missing or invalid API key (Authorization: Bearer ... or X-API-Key)",
        )
