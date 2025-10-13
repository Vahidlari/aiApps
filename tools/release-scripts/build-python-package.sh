#!/bin/bash
# Build Python package with proper version handling for dry-run mode
# Usage: build-python-package.sh <version> <dry_run_flag> [work_dir]

set -euo pipefail

# Check arguments
if [ "$#" -lt 2 ]; then
    echo "Usage: $0 <version> <dry_run_flag> [work_dir]" >&2
    echo "Example: $0 1.2.0 true ./ragora" >&2
    echo "Example: $0 1.2.0 false" >&2
    exit 1
fi

VERSION="$1"
DRY_RUN="$2"
WORK_DIR="${3:-.}"

# Validate working directory
if [ ! -d "$WORK_DIR" ]; then
    echo "Error: Working directory not found: $WORK_DIR" >&2
    exit 1
fi

# Change to working directory
cd "$WORK_DIR"

# Check if this looks like a Python package directory
if [ ! -f "pyproject.toml" ] && [ ! -f "setup.py" ]; then
    echo "Error: Not a Python package directory (no pyproject.toml or setup.py found)" >&2
    exit 1
fi

# Clean up any previous build artifacts
if [ -d "dist" ]; then
    echo "🧹 Cleaning up previous build artifacts..."
    rm -rf dist/
fi

# Track if we created a temporary tag
TEMP_TAG_CREATED=false
CLEANUP_TAG=""

# Cleanup function
cleanup() {
    if [ "$TEMP_TAG_CREATED" = true ] && [ -n "$CLEANUP_TAG" ]; then
        echo "🧹 Cleaning up temporary tag: $CLEANUP_TAG"
        git tag -d "$CLEANUP_TAG" > /dev/null 2>&1 || true
    fi
}

trap cleanup EXIT

# In dry-run mode, semantic-release doesn't create tags
# We need to temporarily create a local tag for setuptools_scm
if [ "$DRY_RUN" = "true" ] && [ -n "$VERSION" ]; then
    TAG_NAME="v${VERSION}"
    echo "🧪 DRY RUN: Creating temporary tag for version $VERSION"
    
    # Create the tag (use -f to force, in case it exists)
    git tag -f "$TAG_NAME" > /dev/null 2>&1 || {
        echo "Warning: Could not create temporary tag, proceeding anyway" >&2
    }
    
    TEMP_TAG_CREATED=true
    CLEANUP_TAG="$TAG_NAME"
fi

# Build the package
echo "📦 Building Python package..."
echo ""

# Temporarily disable exit-on-error for build command
# This allows us to check if artifacts were created even if there were warnings
set +e
python -m build
BUILD_EXIT_CODE=$?
set -e

# Check if build produced artifacts (this is the real success indicator)
echo ""
echo "📦 Checking build artifacts..."
if [ -d "dist" ] && ls dist/*.whl dist/*.tar.gz >/dev/null 2>&1; then
    echo "✅ Package build completed successfully"
    echo ""
    echo "Built packages:"
    ls -lh dist/
    
    # If build command had non-zero exit but produced artifacts, just warn
    if [ $BUILD_EXIT_CODE -ne 0 ]; then
        echo ""
        echo "⚠️  Note: Build command exited with code $BUILD_EXIT_CODE but artifacts were created" >&2
    fi
else
    echo "❌ Build failed - no package files found in dist/ directory" >&2
    if [ $BUILD_EXIT_CODE -ne 0 ]; then
        echo "Build command exited with code $BUILD_EXIT_CODE" >&2
    fi
    exit 1
fi

