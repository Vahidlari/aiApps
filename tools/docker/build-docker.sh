#!/bin/bash

# Exit on any error
set -e

# Configuration
IMAGE_NAME="ai-dev"
REGISTRY="ghcr.io"
# Convert repository name to lowercase (Docker requirement)
REPOSITORY=$(echo "${GITHUB_REPOSITORY:-vahidlari/aiapps}" | tr "[:upper:]" "[:lower:]")
FULL_IMAGE_NAME="${REGISTRY}/${REPOSITORY}/${IMAGE_NAME}"

# Get current date for tagging
DATE_TAG=$(date +%Y%m%d)
LATEST_TAG="latest"

# Parse command line arguments
UPDATE_LOCK=false
PUSH_IMAGE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -u|--update-pip-lock)
            UPDATE_LOCK=true
            shift
            ;;
        -p|--push)
            PUSH_IMAGE=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -u, --update-pip-lock    Generate/update pip.lock file"
            echo "  -p, --push               Push image to GitHub Container Registry"
            echo "  -h, --help               Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                       # Build image only"
            echo "  $0 -u                    # Update pip.lock and build image"
            echo "  $0 -p                    # Build and push image"
            echo "  $0 -u -p                 # Update pip.lock, build and push image"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

echo "Building Docker image..."
echo "Repository: ${REPOSITORY}"
echo "Image name: ${IMAGE_NAME}"
echo "Date tag: ${DATE_TAG}"
echo "Update pip.lock: ${UPDATE_LOCK}"
echo "Push to registry: ${PUSH_IMAGE}"

# Update pip.lock if requested
if [ "$UPDATE_LOCK" = true ]; then
    echo "Updating pip.lock file..."
    ./generate-lock.sh
fi

# Build the Docker image
docker build -t "${FULL_IMAGE_NAME}:${DATE_TAG}" -t "${FULL_IMAGE_NAME}:${LATEST_TAG}" .

echo "Docker image built successfully!"
echo "Tags: ${DATE_TAG}, ${LATEST_TAG}"

# Push to registry if requested
if [ "$PUSH_IMAGE" = true ]; then
    echo "Pushing to GitHub Container Registry..."
    
    # Check if user is logged in to ghcr.io
    if ! docker info | grep -q "ghcr.io"; then
        echo "Please login to GitHub Container Registry first:"
        echo "echo \$GITHUB_TOKEN | docker login ghcr.io -u \$GITHUB_USERNAME --password-stdin"
        echo "Or use: docker login ghcr.io"
        exit 1
    fi
    
    # Push both tags
    docker push "${FULL_IMAGE_NAME}:${DATE_TAG}"
    docker push "${FULL_IMAGE_NAME}:${LATEST_TAG}"
    
    echo "Successfully pushed to GitHub Container Registry!"
    echo "Image: ${FULL_IMAGE_NAME}:${DATE_TAG}"
    echo "Latest: ${FULL_IMAGE_NAME}:${LATEST_TAG}"
else
    echo "To push to registry, use: $0 -p or $0 --push"
fi

echo "Done!"
