#!/bin/bash

# Exit on any error
set -e

echo "Generating Pipfile.lock from Pipfile..."

# Generate lock file from Pipfile
pipenv lock

echo "Pipfile.lock generated successfully!"
echo "You can now build the Docker image with reproducible dependencies."