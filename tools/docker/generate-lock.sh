#!/bin/bash

# Exit on any error
set -e

echo "Generating pip.lock file..."

# Create a temporary virtual environment
python3.11 -m venv temp_venv
source temp_venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install packages and generate lock file
pip install -r requirements.txt
pip freeze > pip.lock

# Clean up
deactivate
rm -rf temp_venv

echo "pip.lock file generated successfully!"
echo "You can now build the Docker image with reproducible dependencies."
