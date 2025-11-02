#!/bin/bash
#
# Clean diffhunk links from CHANGELOG.md
# This script removes GitHub diffhunk-style links that semantic-release
# incorrectly includes in the changelog entries.
#
# Usage: clean-changelog-diffhunks.sh [CHANGELOG_FILE]
#
# Examples of links to remove:
#   [/#diff-2bd056728f63a345f91e168708b7cebb6c7d3ca07cbf6892ab2b7325e545f5cdL20-R23](https://github.com/...)
#   [[1]](diffhunk://#diff-...)

set -euo pipefail

CHANGELOG_FILE="${1:-CHANGELOG.md}"

if [ ! -f "$CHANGELOG_FILE" ]; then
    echo "Warning: $CHANGELOG_FILE not found, skipping cleanup"
    exit 0
fi

echo "🧹 Cleaning diffhunk links from $CHANGELOG_FILE..."

# Create a backup
cp "$CHANGELOG_FILE" "${CHANGELOG_FILE}.bak"

# Remove diffhunk-style links:
# Pattern 1: [/#diff-...](https://...)
# Pattern 2: [[1]](diffhunk://...)
# Pattern 3: [[1]](https://.../issues/diff-...)

# Remove markdown links that contain diffhunk URLs or /#diff- patterns
# Pattern 1: [/#diff-...](https://.../issues/diff-...) - malformed URLs with triple slashes
# Pattern 2: [/#diff-...](https://.../issues/diff-...) - normal diffhunk URLs
# Pattern 3: [[1]](diffhunk://#diff-...) - numbered diffhunk links
# Pattern 4: Any link with /#diff- in the text or /issues/diff- in the URL

sed -i.tmp \
    -e 's|\[/#diff-[^]]*\](https://[^)]*/issues/diff-[^)]*)||g' \
    -e 's|\[/#diff-[^]]*\](https://[^)]*///issues/diff-[^)]*)||g' \
    -e 's|\[/#diff-[^]]*\](https://[^)]*//issues/diff-[^)]*)||g' \
    -e 's|\[/#diff-[^]]*\](https://[^)]*diff[^)]*)||g' \
    -e 's|\[\[[0-9]+\]\](diffhunk://[^)]*)||g' \
    -e 's|\[\[[0-9]+\]\](https://[^)]*/issues/diff-[^)]*)||g' \
    -e 's|\[/#diff-[^]]*\]([^)]*)||g' \
    "$CHANGELOG_FILE"

# Clean up trailing commas and extra spaces that might be left behind
sed -i.tmp \
    -e 's|, *\[#|, [#|g' \
    -e 's|closes *,|closes |g' \
    -e 's|closes *\[/#|closes [#|g' \
    -e 's|closes  \+\[#|closes [#|g' \
    -e 's|closes \+\[#|closes [#|g' \
    "$CHANGELOG_FILE"

# Remove the temporary file created by sed
rm -f "${CHANGELOG_FILE}.tmp"

# Count how many diffhunk references were removed
DIFF_COUNT=$(diff -u "${CHANGELOG_FILE}.bak" "$CHANGELOG_FILE" | grep -c "^-\\[" || true)

if [ "$DIFF_COUNT" -gt 0 ]; then
    echo "✅ Cleaned $DIFF_COUNT diffhunk link(s) from $CHANGELOG_FILE"
else
    echo "✅ No diffhunk links found in $CHANGELOG_FILE"
fi

# Remove backup
rm -f "${CHANGELOG_FILE}.bak"

