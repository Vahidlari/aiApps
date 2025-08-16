#!/bin/bash

# Exit on any error
set -e

echo "Generating pip.lock file..."

# Convert requirements.txt to Pipfile
pipenv install -r requirements.txt
# Then generate lock file
pipenv lock

echo "pip.lock file generated successfully!"
echo "You can now build the Docker image with reproducible dependencies."
