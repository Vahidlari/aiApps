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

# Parse command line arguments
UPDATE_LOCK=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -u|--update-pip-lock)
            UPDATE_LOCK=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -u, --update-pip-lock    Generate/update pip.lock file"
            echo "  -h, --help               Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                       # Build image only"
            echo "  $0 -u                    # Update pip.lock and build image"
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

# Update pip.lock if requested
if [ "$UPDATE_LOCK" = true ]; then
    echo "Updating pip.lock file..."
    ./generate-lock.sh
fi

# Build the Docker image
docker build -t "${FULL_IMAGE_NAME}:${DATE_TAG}" .

echo "Docker image built successfully!"
echo "Tags: ${DATE_TAG}, ${LATEST_TAG}"

echo "Done!"
