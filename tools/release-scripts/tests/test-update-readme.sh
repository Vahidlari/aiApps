#!/bin/bash
# Test script for update-readme-version.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARENT_DIR="$(dirname "$SCRIPT_DIR")"
SCRIPT="$PARENT_DIR/update-readme-version.sh"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

TESTS_PASSED=0
TESTS_FAILED=0

# Helper function to run a test
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    echo "  Running: $test_name"
    if eval "$test_command"; then
        echo -e "  ${GREEN}✓${NC} $test_name passed"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "  ${RED}✗${NC} $test_name failed"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

echo "Testing update-readme-version.sh"
echo "===================================="

# Create temporary test directory
TEST_DIR=$(mktemp -d)
trap "rm -rf $TEST_DIR" EXIT

# Copy script to temp location
mkdir -p "$TEST_DIR/release-scripts"
cp "$SCRIPT" "$TEST_DIR/release-scripts/"

# Setup mock database server structure (relative to script location)
mkdir -p "$TEST_DIR/database_server"

# Test 1: Check script exists and is executable
run_test "Script exists" "[ -f '$SCRIPT' ]"
run_test "Script is executable" "[ -x '$SCRIPT' ]"

# Test 2: Test with existing README (without header)
cd "$TEST_DIR/release-scripts"
cat > ../database_server/README.md <<'EOF'
# Database Server Manager

This is a test README.

## Features
- Feature 1
- Feature 2
EOF

bash "./update-readme-version.sh" "1.0.0" "Test/Repo" > /dev/null 2>&1
run_test "Header updated" "grep -q '# Ragora Database Server - v1.0.0' '../database_server/README.md'"
run_test "Release info section added" "grep -q '## Release Information' '../database_server/README.md'"
run_test "Version info present" "grep -q 'config/VERSION' '../database_server/README.md'"
run_test "Documentation link present" "grep -q 'Test/Repo' '../database_server/README.md'"

# Test 3: Test updating existing header
bash "./update-readme-version.sh" "2.0.0" "Test/Repo" > /dev/null 2>&1
run_test "Header updated to new version" "grep -q '# Ragora Database Server - v2.0.0' '../database_server/README.md'"
run_test "Old version not present" "! grep -q 'v1.0.0' '../database_server/README.md'"

# Test 4: Test with README that already has Ragora header
cat > ../database_server/README.md <<'EOF'
# Ragora Database Server - v0.5.0

Some content here.
EOF

bash "./update-readme-version.sh" "1.5.0" "Another/Repo" > /dev/null 2>&1
run_test "Existing header replaced" "grep -q '# Ragora Database Server - v1.5.0' '../database_server/README.md'"
run_test "New repository in link" "grep -q 'Another/Repo' '../database_server/README.md'"

# Test 5: Test with missing README (should not fail, just skip)
rm -f ../database_server/README.md
run_test "Handles missing README gracefully" "bash './update-readme-version.sh' '1.0.0' 'Test/Repo' > /dev/null 2>&1"

# Test 6: Test Release Information section is not duplicated
cat > ../database_server/README.md <<'EOF'
# Database Server

Content

## Release Information

Old info
EOF

bash "./update-readme-version.sh" "1.0.0" "Test/Repo" > /dev/null 2>&1
RELEASE_INFO_COUNT=$(grep -c "## Release Information" ../database_server/README.md || true)
run_test "Release Information section not duplicated" "[ $RELEASE_INFO_COUNT -eq 1 ]"

# Summary
echo ""
echo "===================================="
echo "Tests passed: $TESTS_PASSED"
echo "Tests failed: $TESTS_FAILED"
echo "===================================="

if [ $TESTS_FAILED -gt 0 ]; then
    exit 1
fi

exit 0

