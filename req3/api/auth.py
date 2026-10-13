"""Bearer API-key auth (design §9): every route except /healthz."""
from __future__ import annotations

import hmac

from fastapi import Request

from .errors import ApiError


async def require_api_key(request: Request) -> None:
    config = request.app.state.config
    provided = request.headers.get("authorization", "")
    expected_bearer = f"Bearer {config.api_key}"
    ok = bool(config.api_key) and hmac.compare_digest(
        provided.encode(), expected_bearer.encode()
    )
    if not ok:
        # v2-client compatibility: X-API-Key header (req-lab-v2 contract)
        provided_key = request.headers.get("x-api-key", "")
        ok = bool(config.api_key) and hmac.compare_digest(
            provided_key.encode(), config.api_key.encode()
        )
    if not ok:
        raise ApiError(
            401, "unauthorized",
            "missing or invalid API key (Authorization: Bearer ... or X-API-Key)",
        )
