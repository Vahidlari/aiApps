#!/bin/bash
# Check for release-worthy commits since last tag
# Usage: check-release-commits.sh <last_tag> [target_ref]

set -euo pipefail

# Check arguments
if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <last_tag> [target_ref]" >&2
    echo "Example: $0 v1.0.0 HEAD" >&2
    exit 1
fi

LAST_TAG="$1"
TARGET_REF="${2:-HEAD}"

# If last tag is v0.0.0, treat it as no previous tag (check all commits)
if [ "$LAST_TAG" = "v0.0.0" ]; then
    COMMITS_SINCE_TAG=$(git log "$TARGET_REF" --oneline 2>/dev/null || echo "")
else
    # Check if the tag exists
    if ! git rev-parse "$LAST_TAG" >/dev/null 2>&1; then
        echo "Warning: Tag '$LAST_TAG' not found, checking all commits" >&2
        COMMITS_SINCE_TAG=$(git log "$TARGET_REF" --oneline 2>/dev/null || echo "")
    else
        COMMITS_SINCE_TAG=$(git log "${LAST_TAG}..${TARGET_REF}" --oneline 2>/dev/null || echo "")
    fi
fi

# Check if there are any commits
if [ -z "$COMMITS_SINCE_TAG" ]; then
    echo "No commits since last tag" >&2
    exit 1
fi

# Check for conventional commits that would trigger a release
# Match: <hash> <type>[(scope)][!]: <description> OR BREAKING CHANGE anywhere
RELEASE_COMMITS=$(echo "$COMMITS_SINCE_TAG" | grep -E "^[0-9a-f]{7,40} (feat|fix|perf|refactor|style|docs|test|build|ci|chore)(\(.+\))?(!)?:|\bBREAKING CHANGE\b" || true)

if [ -z "$RELEASE_COMMITS" ]; then
    echo "No release-worthy commits found" >&2
    exit 1
fi

# Print the release-worthy commits
echo "Found release-worthy commits:"
echo "$RELEASE_COMMITS"

exit 0

