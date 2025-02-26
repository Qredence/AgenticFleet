# Use Alpine as the base image
FROM python:3.12-alpine

# Build argument for version only
ARG VERSION=0.4.90

# Install system dependencies
RUN apk add --no-cache \
    gcc \
    git \
    curl \
    nodejs \
    npm

# Set the working directory
WORKDIR /workspace

# Copy the entire application code into the working directory
COPY . /workspace/

# Install Python dependencies (excluding dev and test)
RUN pip install --upgrade pip && \
    pip install hatch && \
    pip install . && \
    pip install playwright && \
    pip install --no-cache-dir build

# Install Playwright dependencies and Chromium
RUN npx playwright install-deps && \
    npx playwright install chromium

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/workspace
ENV PORT=8000
ENV VERSION=${VERSION}

# Default values for optional settings
ENV USE_OAUTH=false
ENV CHAINLIT_HOST=localhost
ENV CHAINLIT_PORT=8000

# Expose port
EXPOSE 8000

# Copy entrypoint script
COPY scripts/docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh
ENTRYPOINT ["docker-entrypoint.sh"]

# Default command
CMD ["agenticfleet", "start"]
