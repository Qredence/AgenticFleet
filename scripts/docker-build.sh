#!/bin/bash
set -e

# Get version from pyproject.toml
VERSION=$(grep '^version = ' pyproject.toml | cut -d'"' -f2 | tr -d '\n')
IMAGE_NAME="qredenceai/agenticfleet"
BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
BUILD_TYPE=${1:-"prod"}  # Default to prod if not specified

echo "Building AgenticFleet Docker image"
echo "Version: ${VERSION}"
echo "Branch: ${BRANCH}"
echo "Image: ${IMAGE_NAME}"
echo "Build Type: ${BUILD_TYPE}"

# Set tags based on branch and build type
if [ "$BRANCH" = "main" ]; then
    if [ "$BUILD_TYPE" = "prod" ]; then
        TAGS="-t ${IMAGE_NAME}:${VERSION} -t ${IMAGE_NAME}:latest"
        DOCKERFILE="docker/prod.Dockerfile"
    elif [ "$BUILD_TYPE" = "dev" ]; then
        TAGS="-t ${IMAGE_NAME}-dev:${VERSION} -t ${IMAGE_NAME}-dev:latest"
        DOCKERFILE="docker/dev.Dockerfile"
    elif [ "$BUILD_TYPE" = "base" ]; then
        TAGS="-t ${IMAGE_NAME}-base:${VERSION} -t ${IMAGE_NAME}-base:latest"
        DOCKERFILE="docker/base.Dockerfile"
    else
        echo "Invalid build type: ${BUILD_TYPE}. Must be 'base', 'dev', or 'prod'."
        exit 1
    fi
else
    if [ "$BUILD_TYPE" = "prod" ]; then
        TAGS="-t ${IMAGE_NAME}:${VERSION}-dev -t ${IMAGE_NAME}:dev"
        DOCKERFILE="docker/prod.Dockerfile"
    elif [ "$BUILD_TYPE" = "dev" ]; then
        TAGS="-t ${IMAGE_NAME}-dev:${VERSION}-dev -t ${IMAGE_NAME}-dev:dev"
        DOCKERFILE="docker/dev.Dockerfile"
    elif [ "$BUILD_TYPE" = "base" ]; then
        TAGS="-t ${IMAGE_NAME}-base:${VERSION}-dev -t ${IMAGE_NAME}-base:dev"
        DOCKERFILE="docker/base.Dockerfile"
    else
        echo "Invalid build type: ${BUILD_TYPE}. Must be 'base', 'dev', or 'prod'."
        exit 1
    fi
fi

# Use Docker BuildKit for better performance
export DOCKER_BUILDKIT=1

# Build the Docker image
echo "Building with Dockerfile: ${DOCKERFILE}"
docker build \
    -f ${DOCKERFILE} \
    --build-arg VERSION="${VERSION}" \
    --build-arg BUILDKIT_INLINE_CACHE=1 \
    ${TAGS} \
    .

# If --push flag is provided, push the images to Docker Hub
if [ "$2" = "--push" ]; then
    echo "Pushing images to Docker Hub..."

    # Extract the tags from the TAGS variable
    TAG1=$(echo ${TAGS} | cut -d' ' -f2)
    TAG2=$(echo ${TAGS} | cut -d' ' -f4)

    # Remove the -t prefix
    TAG1=${TAG1:2}
    TAG2=${TAG2:2}

    docker push "${TAG1}"
    docker push "${TAG2}"
fi

echo "Build complete!"

# Usage instructions
if [ "$2" != "--push" ]; then
    echo ""
    echo "Usage:"
    echo "  ./scripts/docker-build.sh [base|dev|prod] [--push]"
    echo ""
    echo "Examples:"
    echo "  ./scripts/docker-build.sh base      # Build the base image"
    echo "  ./scripts/docker-build.sh dev       # Build the development image"
    echo "  ./scripts/docker-build.sh prod      # Build the production image"
    echo "  ./scripts/docker-build.sh prod --push  # Build and push the production image"
    echo ""
    echo "Or use docker-compose:"
    echo "  docker-compose build base           # Build the base image"
    echo "  docker-compose build dev            # Build the development image"
    echo "  docker-compose build prod           # Build the production image"
    echo "  docker-compose up -d dev            # Run the development environment"
    echo "  docker-compose up -d prod           # Run the production environment"
fi
