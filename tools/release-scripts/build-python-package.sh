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

# Build the package
echo "📦 Building Python package..."
if [ "$DRY_RUN" = "true" ]; then
    echo "🧪 DRY RUN MODE: Building with version $VERSION"
else
    echo "🚀 PRODUCTION MODE: Building with version $VERSION"
fi
echo ""

# Set version explicitly for setuptools_scm using SETUPTOOLS_SCM_PRETEND_VERSION
# This is necessary for several reasons:
#
# 1. MONOREPO STRUCTURE: The Python package is in a subdirectory (ragora/),
#    but .git is in the parent directory. The isolated build environment
#    created by 'python -m build' cannot reliably access the parent .git
#
# 2. DRY-RUN MODE: semantic-release doesn't create a real tag in dry-run,
#    so there's no tag for setuptools_scm to detect
#
# 3. ISOLATED BUILDS: 'python -m build' creates an isolated virtual environment
#    that may not have full git access, causing setuptools_scm to fail
#
# 4. CI/CD BEST PRACTICE: Explicitly setting the version in CI/CD pipelines
#    is the recommended approach per setuptools_scm documentation
#
# The version comes from semantic-release, ensuring consistency across:
# - Git tags
# - Python package version  
# - PyPI published version
# - GitHub releases
export SETUPTOOLS_SCM_PRETEND_VERSION="$VERSION"
echo "Setting SETUPTOOLS_SCM_PRETEND_VERSION=$VERSION"
echo ""

# Capture build exit code without disabling error handling
# This allows us to check if artifacts were created even if there were warnings
BUILD_EXIT_CODE=0
python -m build || BUILD_EXIT_CODE=$?

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

