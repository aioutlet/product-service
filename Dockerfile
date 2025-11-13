# =============================================================================
# Multi-stage Dockerfile for Python FastAPI Product Service
# =============================================================================

# -----------------------------------------------------------------------------
# Base stage - Common setup for all stages
# -----------------------------------------------------------------------------
FROM python:3.12-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r -g 1001 appgroup && \
    useradd -r -u 1001 -g appgroup -s /bin/bash productuser

# -----------------------------------------------------------------------------
# Dependencies stage - Install Python dependencies
# -----------------------------------------------------------------------------
FROM base AS dependencies

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# -----------------------------------------------------------------------------
# Development stage - For local development with hot reload
# -----------------------------------------------------------------------------
FROM dependencies AS development

# Copy application code
COPY --chown=productuser:appgroup . .

# Create logs directory
RUN mkdir -p logs && chown -R productuser:appgroup logs

# Switch to non-root user
USER productuser

# Expose port
EXPOSE 1001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:1001/readiness || exit 1

# Start development server with auto-reload
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "1001", "--reload"]

# -----------------------------------------------------------------------------
# Production stage - Optimized for production deployment
# -----------------------------------------------------------------------------
FROM base AS production

# Copy installed dependencies from dependencies stage
COPY --from=dependencies /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=productuser:appgroup . .

# Create logs directory
RUN mkdir -p logs && chown -R productuser:appgroup logs

# Remove unnecessary files for production
RUN rm -rf tests/ .git/ .github/ .vscode/ *.md .env.* docker-compose* __pycache__/ .pytest_cache/

# Switch to non-root user
USER productuser

# Expose port
EXPOSE 1001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:1001/readiness || exit 1

# Start production server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "1001", "--workers", "4"]

# Labels for better image management
LABEL maintainer="AIOutlet Team"
LABEL service="product-service"
LABEL version="1.0.0"
