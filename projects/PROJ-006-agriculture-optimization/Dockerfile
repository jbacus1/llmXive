# Multi-stage build for Climate-Smart Agricultural Practices project
# Stage 1: Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    libspatialindex-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages to a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime stage
FROM python:3.11-slim as runtime

WORKDIR /app

# Install runtime dependencies for GIS libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgdal32 \
    libgeos-3.11.1 \
    libproj25 \
    libspatialindex7 \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser

# Copy project files
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser tests/ ./tests/
COPY --chown=appuser:appuser data/ ./data/
COPY --chown=appuser:appuser contracts/ ./contracts/
COPY --chown=appuser:appuser docs/ ./docs/
COPY --chown=appuser:appuser code/ ./code/
COPY --chown=appuser:appuser paper/ ./paper/
COPY --chown=appuser:appuser requirements.txt .
COPY --chown=appuser:appuser pytest.ini .
COPY --chown=appuser:appuser .env.example .env.example

# Set working directory and user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import src.cli.validate; print('OK')" || exit 1

# Default command
CMD ["python", "-m", "pytest", "tests/", "-v"]
