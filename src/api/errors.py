"""Global exception handlers for FastAPI.

Ensures NO internal details are ever exposed to the client.
All errors are logged server-side with full context.
"""
from __future__ import annotations
import logging
from fastapi import Request
from fastapi.responses import JSONResponse

log = logging.getLogger("api.errors")


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global fallback for ALL unhandled exceptions.

    Logs the full error internally, returns generic 500 to client.
    NEVER exposes stack traces or internal paths.
    """
    log.error(
        "Unhandled exception: %s | Path: %s | Method: %s",
        exc, request.url.path, request.method,
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again later."},
    )
