#!/bin/bash
set -e

# Get version from pyproject.toml
VERSION=$(grep '^version = ' pyproject.toml | cut -d'"' -f2 | tr -d '\n')
IMAGE_NAME="qredence/agenticfleet"

# Login to Docker Hub (if not already logged in)
if ! docker info | grep -q "Username"; then
    echo "Please login to Docker Hub:"
    docker login
fi

# Build production images
echo "Building images for version ${VERSION}"
docker buildx create --use
docker buildx build \
    --platform linux/amd64,linux/arm64 \
    --build-arg VERSION="${VERSION}" \
    -t "${IMAGE_NAME}:${VERSION}" \
    -t "${IMAGE_NAME}:latest" \
    --push \
    .

echo "✨ Successfully published:"
echo "- ${IMAGE_NAME}:${VERSION}"
echo "- ${IMAGE_NAME}:latest"
