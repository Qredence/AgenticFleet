# Production Dockerfile for AgenticFleet

# Builder stage
FROM python:3.13.7-slim AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set the working directory
WORKDIR /app

# Install system dependencies for building
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies from requirements.txt
RUN pip install --no-cache-dir --prefix="/install" -r requirements.txt

# Install playwright, its system dependencies, and then the local package
# Combining these RUN steps to reduce layers.
# First, copy necessary files for local package installation.
# Assuming standard Python package structure: setup.py, src, potentially pyproject.toml, README.md
COPY setup.py pyproject.toml README.md ./
COPY src ./src/

RUN /install/bin/pip install playwright \
    && /install/bin/python -m playwright install-deps \
    && /install/bin/pip install .

# Production stage
FROM python:3.13.7-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    PATH="/usr/local/bin:$PATH"

# Create a non-root user and group.
# Install runtime system dependencies & clean up in a single layer.
RUN groupadd -r appgroup && useradd --no-log-init -r -g appgroup -d /home/appuser -s /sbin/nologin appuser \
    && apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy Python environment from the builder stage
COPY --from=builder /install /usr/local

# Re-install Playwright's system dependencies in the final stage
# This is run as root and installs system-wide libraries.
RUN python -m playwright install-deps

# Copy only necessary application files
COPY src /app/src/
COPY chainlit.md /app/
# Assuming 'config' is a directory at the root of the build context.
# If it's a file, it should be COPY config /app/config
# If it's inside src, then it's already covered by `COPY src /app/src/`
COPY config /app/config/

# Change ownership of the /app directory and its contents to appuser
RUN chown -R appuser:appgroup /app && \
    # Ensure home directory exists and is writable by appuser for playwright cache
    mkdir -p /home/appuser/.cache/ms-playwright && \
    chown -R appuser:appgroup /home/appuser

# Switch to the non-root user
USER appuser

# Expose the port Chainlit runs on
EXPOSE 8000

# Add HEALTHCHECK instruction
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:8000/ || exit 1

# Set the default command
CMD ["chainlit", "run", "src/agentic_fleet/app.py", "--host", "0.0.0.0", "--port", "8000"]
