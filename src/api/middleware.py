"""
API Middleware — Request Logging
"""
from __future__ import annotations
import time
from fastapi import Request
from src.utils import get_logger

log = get_logger("api.middleware")


async def log_requests(request: Request, call_next):
    """Log incoming request method, path, status code, and duration."""
    start = time.perf_counter()
    response = await call_next(request)
    duration = int((time.perf_counter() - start) * 1000)
    log.info(f"{request.method} {request.url.path} — {response.status_code} ({duration}ms)")
    return response
