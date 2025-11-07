#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

cd "${REPO_ROOT}"

if ! command -v mkdocs >/dev/null 2>&1; then
  echo "mkdocs is not installed. Please run 'pip install -e \"ragora[docs]\"' first." >&2
  exit 1
fi

echo "Running mkdocs build..."
mkdocs build
echo "Documentation generated in ${REPO_ROOT}/docs"

