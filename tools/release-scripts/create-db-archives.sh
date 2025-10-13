#!/bin/bash
# Create database server archives
# Usage: create-db-archives.sh <version>

set -euo pipefail

# Check arguments
if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <version>" >&2
    echo "Example: $0 1.2.0" >&2
    exit 1
fi

VERSION="$1"

# Validate version is not empty
if [ -z "$VERSION" ]; then
    echo "Error: Version cannot be empty" >&2
    exit 1
fi

# Determine script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DB_SERVER_DIR="$SCRIPT_DIR/../database_server"

# Check if database_server directory exists
if [ ! -d "$DB_SERVER_DIR" ]; then
    echo "❌ Database server directory not found: $DB_SERVER_DIR" >&2
    exit 1
fi

echo "📦 Creating database server archives for version $VERSION"
echo ""

# Define archive names
TAR_ARCHIVE="database_server-${VERSION}.tar.gz"
ZIP_ARCHIVE="database_server-${VERSION}.zip"

# Create tar.gz archive excluding unnecessary files
echo "Creating tar.gz archive..."
tar --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='node_modules' \
    --exclude='*.log' \
    --exclude='*.tmp' \
    -czf "$TAR_ARCHIVE" \
    -C "$SCRIPT_DIR/.." database_server

echo "✅ Created: $TAR_ARCHIVE"

# Create zip archive with same exclusions (if zip is available)
if command -v zip &> /dev/null; then
    echo "Creating zip archive..."
    cd "$SCRIPT_DIR/.."
    zip -q -r "$ZIP_ARCHIVE" database_server \
        -x "*.pyc" \
        -x "*__pycache__*" \
        -x "*.git*" \
        -x "*node_modules*" \
        -x "*.log" \
        -x "*.tmp"
    cd - > /dev/null
    
    echo "✅ Created: $ZIP_ARCHIVE"
    echo ""
    echo "📦 Archives created successfully:"
    echo "$TAR_ARCHIVE"
    echo "$ZIP_ARCHIVE"
else
    echo "⚠️  zip command not available, skipping zip archive"
    echo ""
    echo "📦 Archive created successfully:"
    echo "$TAR_ARCHIVE"
fi

