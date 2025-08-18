#!/bin/bash

# Exit on any error
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color


# Navigate to the docker directory
cd "$(dirname "$0")"

# Check for .env file and create if it doesn't exist
if [ ! -f .env ]; then
    echo -e "${YELLOW}No .env file found. Creating from template...${NC}"
    if [ ! -f env.template ]; then
        echo -e "${RED}No env.template file found. Please check the repository.${NC}"
        exit 1
    fi
    cp env.template .env
    echo -e "${GREEN}Created .env file. Please edit it with your credentials.${NC}"
    echo -e "${YELLOW}Opening .env file for editing...${NC}"
    ${EDITOR:-vi} .env
fi

# Load environment variables
set -a
source .env
set +a


# Configuration
IMAGE_NAME=${IMAGE_NAME:-ai-dev}
REGISTRY="ghcr.io"

REPOSITORY_NAME=$(basename -s .git $(git remote get-url origin) | tr "[:upper:]" "[:lower:]")
REPOSITORY="${GITHUB_USERNAME}/${REPOSITORY_NAME}"
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

    if [ -n "$GITHUB_USERNAME" ] && [ -n "$GITHUB_CR_PAT" ]; then
        echo "Logging in to GitHub Container Registry..."
        echo "${GITHUB_CR_PAT}" | docker login ghcr.io -u "${GITHUB_USERNAME}" --password-stdin
    else
        echo "GITHUB_USERNAME or GITHUB_CR_PAT is not set in .env file. Please set it."
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
