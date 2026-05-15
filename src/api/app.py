"""
FastAPI Application Factory for Market Intelligence Agent
"""
from __future__ import annotations
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from src.api.deps import init_orchestrator, shutdown_orchestrator
from src.api.errors import global_exception_handler
from src.api.middleware import log_requests
from src.api.routes import health, status, chat, conversations, auth
from src.api.auth.supabase_client import init_supabase, close_supabase
from src.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_supabase()
    try:
        await init_orchestrator()
    except Exception as e:
        # Orchestrator may fail (e.g., missing sentence_transformers) but
        # the API should still start for health checks. First request will retry.
        import logging
        logging.getLogger("api.app").warning(f"Orchestrator init failed (deferred): {e}")
    yield
    # Shutdown
    await shutdown_orchestrator()
    close_supabase()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Market Intelligence Agent API",
        version="1.0.0",
        lifespan=lifespan,
    )
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )
    # GZip compression (compress responses > 1000 bytes)
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    # Request logging middleware
    app.middleware("http")(log_requests)

    # Routers — auth BEFORE protected routes
    app.include_router(health.router, prefix="/api")
    app.include_router(auth.router, prefix="/api")
    app.include_router(status.router, prefix="/api")
    app.include_router(chat.router, prefix="/api")
    app.include_router(conversations.router, prefix="/api")

    # Global exception handler — catches anything that falls through
    app.add_exception_handler(Exception, global_exception_handler)

    return app
