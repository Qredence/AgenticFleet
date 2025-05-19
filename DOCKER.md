# Docker Setup for AgenticFleet

This project uses Docker for development and deployment. Here's how the Docker files are organized:

## Development with VS Code

For the best development experience, we recommend using VS Code with the Remote Containers extension.
Simply open this project in VS Code, and it will prompt you to "Reopen in Container".

The development container configuration is in the `.devcontainer` directory.

## Production Deployment

For production deployment, use the Docker files in the `docker/` directory:

```bash
# Build and run the production container
cd /path/to/agenticfleet
docker-compose up -d prod
```

## Docker File Structure

- `.devcontainer/` - Files for VS Code development container
- `docker/` - Production Docker files
  - `base.Dockerfile` - Base image for development and production
  - `dev.Dockerfile` - Development image
  - `prod.Dockerfile` - Production image
  - `docker-compose.yml` - Docker Compose configuration

## Symlinks

For convenience, we provide symlinks in the root directory:

- `Dockerfile` → `docker/prod.Dockerfile`
- `docker-compose.yml` → `docker/docker-compose.yml`
- `.dockerignore` → `docker/.dockerignore`

These symlinks allow you to run Docker commands from the root directory.
