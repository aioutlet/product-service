# =============================================================================
# Multi-stage Dockerfile for Python Product Service (FastAPI)
# =============================================================================

# -----------------------------------------------------------------------------
# Base stage - Common setup for all stages
# -----------------------------------------------------------------------------
FROM python:3.14-slim AS base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# -----------------------------------------------------------------------------
# Dependencies stage - Install Python dependencies
# -----------------------------------------------------------------------------
FROM base AS dependencies

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# -----------------------------------------------------------------------------
# Development stage - For local development
# -----------------------------------------------------------------------------
FROM dependencies AS development

# Copy application code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Set environment variables
ENV PYTHONPATH=/app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run development server with hot reload
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# -----------------------------------------------------------------------------
# Production stage - Optimized for production deployment
# -----------------------------------------------------------------------------
FROM dependencies AS production

# Copy application code
COPY --chown=appuser:appuser . .

# Remove unnecessary files for production
RUN rm -rf tests/ .git/ .github/ .vscode/ *.md .env.* docker-compose* .ops/

# Switch to non-root user
USER appuser

# Set environment variables
ENV PYTHONPATH=/app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run the application with multiple workers
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# Labels for better image management
LABEL maintainer="AIOutlet Team"
LABEL service="product-service"
LABEL version="1.0.0"
