#!/bin/bash
# Create database server archives with version metadata
# Usage: create-db-archives.sh <version> <git_commit> <git_branch> <repository>

set -euo pipefail

# Check arguments
if [ "$#" -ne 4 ]; then
    echo "Usage: $0 <version> <git_commit> <git_branch> <repository>" >&2
    echo "Example: $0 1.2.0 abc123def main Vahidlari/aiApps" >&2
    exit 1
fi

VERSION="$1"
GIT_COMMIT="$2"
GIT_BRANCH="$3"
REPOSITORY="$4"

# Determine script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if database_server directory exists
if [ ! -d "$SCRIPT_DIR/../database_server" ]; then
    echo "❌ Database server directory not found: $SCRIPT_DIR/../database_server" >&2
    echo "Skipping archive creation" >&2
    exit 1
fi

echo "📦 Creating database server archives for version $VERSION"
echo ""

# Create version metadata using helper script
echo "📝 Creating version metadata..."
bash "$SCRIPT_DIR/create-version-metadata.sh" \
    "$VERSION" \
    "$GIT_COMMIT" \
    "$GIT_BRANCH" \
    "$REPOSITORY"

echo ""

# Update README with version info using helper script
echo "📝 Updating README with version information..."
bash "$SCRIPT_DIR/update-readme-version.sh" \
    "$VERSION" \
    "$REPOSITORY"

echo ""
echo "📦 Creating archives..."

# Define archive names
TAR_ARCHIVE="database_server-${VERSION}.tar.gz"
ZIP_ARCHIVE="database_server-${VERSION}.zip"

# Create tar.gz archive excluding unnecessary files
tar --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='node_modules' \
    --exclude='*.log' \
    --exclude='*.tmp' \
    -czf "$TAR_ARCHIVE" \
    -C "$SCRIPT_DIR/.." database_server

echo "✅ Created tar.gz: $TAR_ARCHIVE"

# Create zip archive with same exclusions (if zip is available)
if command -v zip &> /dev/null; then
    cd "$SCRIPT_DIR/.."
    zip -q -r "$TAR_ARCHIVE/../$ZIP_ARCHIVE" database_server \
        -x "*.pyc" \
        -x "*__pycache__*" \
        -x "*.git*" \
        -x "*node_modules*" \
        -x "*.log" \
        -x "*.tmp"
    
    echo "✅ Created zip: $ZIP_ARCHIVE"
    
    # Return to original directory
    cd - > /dev/null
    
    echo ""
    echo "📦 Archives created successfully:"
    echo "$TAR_ARCHIVE"
    echo "$ZIP_ARCHIVE"
else
    echo "⚠️  zip command not available, skipping zip archive creation"
    echo ""
    echo "📦 Archive created successfully:"
    echo "$TAR_ARCHIVE"
fi

