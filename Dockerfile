# ==============================================================================
# Dockerfile — Market Intelligence Agent (FastAPI Backend)
# ==============================================================================
#
# Build:
#   docker build -t market-intelligence-agent:latest .
#
# Run (minimum):
#   docker run -d -p 8000:8000 --env-file .env market-intelligence-agent:latest
#
# Run (production):
#   docker run -d -p 8000:8000 \
#     -e APP_ENV=production \
#     -e SUPABASE_URL=... \
#     -e SUPABASE_KEY=... \
#     -e OPENAI_API_KEY=... \
#     market-intelligence-agent:latest
#
# ==============================================================================

# ------------------------------------------------------------------------------
# STAGE 1 — Builder
# ------------------------------------------------------------------------------
FROM python:3.11-slim AS builder

# Prevent Python from writing .pyc / buffering stdout
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build-time system dependencies required by some Python wheels
# (chromadb → grpcio, hnswlib; torch → numpy; scikit-learn → joblib, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    build-essential \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Copy only the requirements file first (maximises Docker layer caching)
COPY requirements.txt .

# Install all Python dependencies into a temporary directory so the runtime
# stage can COPY —only what's needed without carrying over build tools.
RUN pip install --no-cache-dir \
    --prefix=/install \
    -r requirements.txt

# ------------------------------------------------------------------------------
# STAGE 2 — Runtime
# ------------------------------------------------------------------------------
FROM python:3.11-slim AS runtime

# ── Labels (Open Containers Initiative) ─────────────────────────────────────
LABEL org.opencontainers.image.title="Market Intelligence Agent"
LABEL org.opencontainers.image.description="Multi-market financial intelligence orchestrator with AI-powered analysis"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.licenses="MIT"

# ── Python runtime tuning ───────────────────────────────────────────────────
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=production \
    PYTHONPATH=/app

# Install ONLY runtime system dependencies (things torch/chromadb need at runtime)
# ca-certificates: SSL for API calls
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from the builder stage (keeps the runtime image free
# of gcc, headers, and other build-only cruft).
COPY --from=builder /install /usr/local

# ── Application code ────────────────────────────────────────────────────────
WORKDIR /app
COPY src/ ./src/

# ── Runtime directories ─────────────────────────────────────────────────────
# These paths are expected by the orchestrator and can be overridden via env
# vars or volume mounts at deployment time.
RUN mkdir -p /app/data/raw /app/data/processed /app/logs

# ── Health check ────────────────────────────────────────────────────────────
# The /api/health endpoint returns 200 as soon as the app is reachable,
# regardless of orchestrator readiness (orchestrator init is deferred).
HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" || exit 1

# ── User — run as non-root ──────────────────────────────────────────────────
RUN addgroup --system --gid 1001 app && \
    adduser --system --uid 1001 --gid 1001 app && \
    chown -R app:app /app
USER app

# ── Expose & launch ─────────────────────────────────────────────────────────
EXPOSE 8000

CMD ["uvicorn", "src.api.app:create_app", "--host", "0.0.0.0", "--port", "8000", "--factory", "--workers", "1"]
