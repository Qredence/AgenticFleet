# This is a symlink to the production Dockerfile
# For development, use docker-compose with the dev service
# For production, use docker-compose with the prod service
# For more information, see the README.md file

# Production Dockerfile for AgenticFleet
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app/src

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install playwright dependencies
RUN pip install playwright && python -m playwright install-deps

# Copy the project files
COPY . .

# Install the package
RUN pip install .

# Expose the port Chainlit runs on
EXPOSE 8000

# Set environment variables (using ARG for build-time flexibility)
ARG OPENAI_API_KEY=""
ARG AZURE_OPENAI_ENDPOINT=""
ARG AZURE_OPENAI_API_KEY=""
ARG AZURE_OPENAI_API_VERSION=""
ARG USE_OAUTH=""

# Set environment variables
ENV OPENAI_API_KEY=${OPENAI_API_KEY} \
    AZURE_OPENAI_ENDPOINT=${AZURE_OPENAI_ENDPOINT} \
    AZURE_OPENAI_API_KEY=${AZURE_OPENAI_API_KEY} \
    AZURE_OPENAI_API_VERSION=${AZURE_OPENAI_API_VERSION} \
    USE_OAUTH=${USE_OAUTH}

# Copy and set the entrypoint script
COPY scripts/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

# Set the default command to run the Chainlit application
CMD ["chainlit", "run", "src/agentic_fleet/app.py", "--host", "0.0.0.0", "--port", "8000"]
