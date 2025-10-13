#!/bin/bash
# Test script for create-version-metadata.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARENT_DIR="$(dirname "$SCRIPT_DIR")"
SCRIPT="$PARENT_DIR/create-version-metadata.sh"

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

echo "Testing create-version-metadata.sh"
echo "===================================="

# Create temporary test directory
TEST_DIR=$(mktemp -d)
trap "rm -rf $TEST_DIR" EXIT

# Copy script to temp location so it can find database_server correctly
mkdir -p "$TEST_DIR/release-scripts"
cp "$SCRIPT" "$TEST_DIR/release-scripts/"
TEST_SCRIPT="$TEST_DIR/release-scripts/create-version-metadata.sh"

# Setup mock database server structure (relative to script location)
mkdir -p "$TEST_DIR/database_server/config"

# Test 1: Check script exists and is executable
run_test "Script exists" "[ -f '$SCRIPT' ]"
run_test "Script is executable" "[ -x '$SCRIPT' ]"

# Test 2: Run script with valid arguments
cd "$TEST_DIR/release-scripts"
run_test "Script runs with valid args" "bash './create-version-metadata.sh' '1.0.0' 'abc123' 'main' 'Test/Repo' > /dev/null 2>&1"

# Test 3: Check VERSION file was created
run_test "VERSION file created" "[ -f '../database_server/config/VERSION' ]"

# Test 4: Check VERSION file content
run_test "VERSION file has correct content" "grep -q '1.0.0' '../database_server/config/VERSION'"

# Test 5: Check release-info.json was created
run_test "release-info.json created" "[ -f '../database_server/config/release-info.json' ]"

# Test 6: Check JSON content
run_test "JSON contains version" "grep -q '\"version\": \"1.0.0\"' '../database_server/config/release-info.json'"
run_test "JSON contains git_commit" "grep -q '\"git_commit\": \"abc123\"' '../database_server/config/release-info.json'"
run_test "JSON contains git_branch" "grep -q '\"git_branch\": \"main\"' '../database_server/config/release-info.json'"
run_test "JSON contains repository" "grep -q '\"repository\": \"Test/Repo\"' '../database_server/config/release-info.json'"

# Test 7: Test with different version
bash "./create-version-metadata.sh" "2.5.3" "def456" "develop" "Another/Repo" > /dev/null 2>&1
run_test "Different version in VERSION" "grep -q '2.5.3' '../database_server/config/VERSION'"
run_test "Different version in JSON" "grep -q '\"version\": \"2.5.3\"' '../database_server/config/release-info.json'"

# Test 8: Check for missing config directory
rm -rf "$TEST_DIR/database_server/config"
run_test "Fails gracefully with missing config dir" "! bash './create-version-metadata.sh' '1.0.0' 'abc' 'main' 'Test/Repo' > /dev/null 2>&1"

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

