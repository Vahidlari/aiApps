#!/bin/bash
# Create version metadata files for database server releases
# Usage: create-version-metadata.sh <version> <git_commit> <git_branch> <repository>

set -e

# Check arguments
if [ "$#" -ne 4 ]; then
    echo "Usage: $0 <version> <git_commit> <git_branch> <repository>"
    echo "Example: $0 1.0.0 abc123def main Vahidlari/aiApps"
    exit 1
fi

VERSION="$1"
GIT_COMMIT="$2"
GIT_BRANCH="$3"
REPOSITORY="$4"

# Determine script and target directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DB_SERVER_DIR="$SCRIPT_DIR/../database_server"
CONFIG_DIR="$DB_SERVER_DIR/config"

# Ensure config directory exists
if [ ! -d "$CONFIG_DIR" ]; then
    echo "Error: Database server config directory not found: $CONFIG_DIR"
    exit 1
fi

# Create simple VERSION file
echo "$VERSION" > "$CONFIG_DIR/VERSION"
echo "✅ Created VERSION file: $CONFIG_DIR/VERSION"

# Create release metadata JSON
cat > "$CONFIG_DIR/release-info.json" <<EOF
{
  "version": "$VERSION",
  "release_date": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "git_tag": "v$VERSION",
  "git_commit": "$GIT_COMMIT",
  "git_branch": "$GIT_BRANCH",
  "release_url": "https://github.com/$REPOSITORY/releases/tag/v$VERSION",
  "repository": "$REPOSITORY"
}
EOF

echo "✅ Created release-info.json: $CONFIG_DIR/release-info.json"
echo ""
echo "📋 Metadata content:"
cat "$CONFIG_DIR/release-info.json"

