#!/bin/bash
set -e

cd /workspaces/aiApps/ragora

# Try to get the latest version tag (sorted by version, not by commit history)
# This gets the highest version tag in the repo, regardless of which branch it's on
VERSION=$(git tag --sort=-version:refname 2>/dev/null | head -1 | sed 's/^v//' || echo "0.0.0")

echo "Installing ragora with version: $VERSION"

# Export both environment variable formats for setuptools-scm
export SETUPTOOLS_SCM_PRETEND_VERSION="$VERSION"
export SETUPTOOLS_SCM_PRETEND_VERSION_FOR_RAGORA="$VERSION"

# Install the package with dev dependencies (includes pytest, black, flake8, etc.)
echo "Installing ragora package with development dependencies..."
pip install -e ".[dev]"

# Add local bin to PATH
echo 'export PATH="/home/vscode/.local/bin:$PATH"' >> ~/.bashrc

echo "Ragora installation completed successfully!"

