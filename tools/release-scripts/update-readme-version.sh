#!/bin/bash
# Update database server README with version information
# Usage: update-readme-version.sh <version> <repository>

set -e

# Check arguments
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <version> <repository>"
    echo "Example: $0 1.0.0 vahidlari/ragora-core"
    exit 1
fi

VERSION="$1"
REPOSITORY="$2"

# Determine script and target directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DB_SERVER_DIR="$SCRIPT_DIR/../database_server"
README_FILE="$DB_SERVER_DIR/README.md"

# Check if README exists
if [ ! -f "$README_FILE" ]; then
    echo "⚠️  README not found: $README_FILE"
    echo "Skipping README update"
    exit 0
fi

echo "📝 Updating README with version $VERSION"

# Update or add version to header
if grep -q "^# Ragora Database Server\s*\(-\s*v[0-9.a-z-]*\)\?$" "$README_FILE"; then
    # Header exists, update it with version (match standalone or with existing version)
    sed -i "s/^# Ragora Database Server\s*\(-\s*v[0-9.a-z-]*\)\?$/# Ragora Database Server - v$VERSION/" "$README_FILE"
    echo "✅ Updated existing header with version"
else
    # No header found, add version header at beginning
    TEMP_FILE=$(mktemp)
    echo "# Ragora Database Server - v$VERSION" > "$TEMP_FILE"
    echo "" >> "$TEMP_FILE"
    cat "$README_FILE" >> "$TEMP_FILE"
    mv "$TEMP_FILE" "$README_FILE"
    echo "✅ Added version header to README"
fi

# Add release information section if not present
if ! grep -q "## Release Information" "$README_FILE"; then
    echo "" >> "$README_FILE"
    echo "## Release Information" >> "$README_FILE"
    echo "" >> "$README_FILE"
    echo "**Version:** See config/VERSION or run ./database-manager.sh --version" >> "$README_FILE"
    echo "**Release Date:** See config/release-info.json for full metadata" >> "$README_FILE"
    echo "**Documentation:** [Ragora Documentation](https://github.com/$REPOSITORY)" >> "$README_FILE"
    echo "✅ Added release information section"
else
    echo "ℹ️  Release information section already exists"
fi

echo "✅ README updated successfully: $README_FILE"

