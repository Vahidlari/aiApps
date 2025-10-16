#!/bin/bash
# Create database server archives
# Usage: create-db-archives.sh <version> [output_dir]

set -euo pipefail

# Check arguments
if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <version> [output_dir]" >&2
    echo "Example: $0 1.2.0 artifacts" >&2
    exit 1
fi

VERSION="$1"
# Determine output directory (default to current directory)
OUTPUT_DIR="${2:-.}"

# Validate version is not empty
if [ -z "$VERSION" ]; then
    echo "Error: Version cannot be empty" >&2
    exit 1
fi

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"
OUTPUT_DIR="$(cd "$OUTPUT_DIR" && pwd)"  # Get absolute path

# Determine script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOLS_DIR="$SCRIPT_DIR/.."
DB_SERVER_DIR="$TOOLS_DIR/database_server"

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
    -czf "$OUTPUT_DIR/$TAR_ARCHIVE" \
    -C "$TOOLS_DIR" database_server

echo "✅ Created: $OUTPUT_DIR/$TAR_ARCHIVE"

# Create zip archive with same exclusions (if zip is available)
if command -v zip &> /dev/null; then
    echo "Creating zip archive..."
    cd "$TOOLS_DIR"
    zip -q -r "$OUTPUT_DIR/$ZIP_ARCHIVE" database_server \
        -x "*.pyc" \
        -x "*__pycache__*" \
        -x "*.git*" \
        -x "*node_modules*" \
        -x "*.log" \
        -x "*.tmp"
    cd - > /dev/null
    
    echo "✅ Created: $OUTPUT_DIR/$ZIP_ARCHIVE"
    echo ""
    echo "📦 Archives created successfully:"
    echo "$OUTPUT_DIR/$TAR_ARCHIVE"
    echo "$OUTPUT_DIR/$ZIP_ARCHIVE"
else
    echo "⚠️  zip command not available, skipping zip archive"
    echo ""
    echo "📦 Archive created successfully:"
    echo "$OUTPUT_DIR/$TAR_ARCHIVE"
fi

