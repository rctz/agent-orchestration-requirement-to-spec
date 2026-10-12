"""Bearer API-key auth (design §9): every route except /healthz."""
from __future__ import annotations

import hmac

from fastapi import Request

from .errors import ApiError


async def require_api_key(request: Request) -> None:
    config = request.app.state.config
    auth = request.headers.get("authorization", "")
    expected = f"Bearer {config.api_key}"
    if not config.api_key or not hmac.compare_digest(
        auth.encode(), expected.encode()
    ):
        raise ApiError(401, "unauthorized", "missing or invalid API key")
