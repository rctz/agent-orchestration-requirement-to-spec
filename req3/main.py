"""Application factory + entrypoint (`python -m req3.main`)."""
from __future__ import annotations

import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

import req3

from .api import rest
from .api.errors import ApiError, error_body
from .config import Config, load_roles, roles_requirements
from .executor.base import get_executor
from .store.db import Database


def create_app(config: Config | None = None) -> FastAPI:
    config = config or Config.load()
    roles = load_roles(config.roles_path)
    if config.executor == "opencode" and not roles.get("roles"):
        raise RuntimeError(
            f"roles.yaml not found or empty at {config.roles_path!r} — refusing "
            "to start the opencode executor without required agents "
            "(design §10 startup self-check)"
        )
    required_agents, required_models = roles_requirements(roles)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        db = Database(Path(config.data_dir) / "req3.db")
        await db.open()
        app.state.db = db
        app.state.workspace_root = Path(config.data_dir) / "jobs"
        app.state.executor = get_executor(config, required_agents, required_models)
        app.state.health_cache = None
        report = await app.state.executor.health()
        print(
            f"req3 startup self-check: executor={config.executor} "
            f"ok={report.ok} {report.detail}",
            file=sys.stderr,
        )
        try:
            yield
        finally:
            aclose = getattr(app.state.executor, "aclose", None)
            if aclose is not None:
                await aclose()
            await db.close()

    app = FastAPI(
        title="req3",
        version=req3.__version__,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,  # we serve it ourselves at /v1/openapi.json
        lifespan=lifespan,
    )
    app.state.config = config

    @app.exception_handler(ApiError)
    async def api_error_handler(
        request: Request, exc: ApiError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code, content=error_body(exc.code, exc.message)
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        messages = "; ".join(
            f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}"
            for err in exc.errors()[:5]
        )
        return JSONResponse(
            status_code=422,
            content=error_body("invalid_request", f"validation failed: {messages}"),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        code = "not_found" if exc.status_code == 404 else "http_error"
        return JSONResponse(
            status_code=exc.status_code, content=error_body(code, str(exc.detail))
        )

    @app.get("/healthz")
    async def healthz() -> JSONResponse:
        """Liveness + executor health (design §9). Open: no auth."""
        report = await app.state.executor.health()
        body: dict[str, Any] = {
            "status": "ok" if report.ok else "degraded",
            "version": req3.__version__,
            "executor": {
                "ok": report.ok,
                "agents": report.agents,
                "models": report.models,
                "detail": report.detail,
            },
        }
        return JSONResponse(body, status_code=200 if report.ok else 503)

    app.include_router(rest.router)
    return app


def main() -> None:
    config = Config.load()
    if not config.api_key:
        sys.exit("error: REQ3_API_KEY is required (set it in .env, mode 600)")
    import uvicorn

    host, port = config.host_port
    uvicorn.run(create_app(config), host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
