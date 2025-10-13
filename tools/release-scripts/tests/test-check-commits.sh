#!/bin/bash
# Test script for check-release-commits.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARENT_DIR="$(dirname "$SCRIPT_DIR")"
SCRIPT="$PARENT_DIR/check-release-commits.sh"

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

echo "Testing check-release-commits.sh"
echo "===================================="

# Create temporary test directory with a git repo
TEST_DIR=$(mktemp -d)
trap "rm -rf $TEST_DIR" EXIT

cd "$TEST_DIR"
git init -q
git config user.email "test@example.com"
git config user.name "Test User"

# Test 1: Check script exists and is executable
run_test "Script exists" "[ -f '$SCRIPT' ]"
run_test "Script is executable" "[ -x '$SCRIPT' ]"

# Test 2: Script fails with no arguments
run_test "Fails with no arguments" "! bash '$SCRIPT' > /dev/null 2>&1"

# Test 3: Create initial commit and tag
echo "Initial" > file.txt
git add file.txt
git commit -q -m "Initial commit"
git tag v1.0.0

# Test 4: No commits since tag
run_test "No commits since tag returns error" "! bash '$SCRIPT' 'v1.0.0' 'HEAD' > /dev/null 2>&1"

# Test 5: Add conventional commit (feat)
echo "Feature" >> file.txt
git add file.txt
git commit -q -m "feat: add new feature"
run_test "Detects feat commit" "bash '$SCRIPT' 'v1.0.0' 'HEAD' > /dev/null 2>&1"

# Test 6: Check output contains the commit
OUTPUT=$(bash "$SCRIPT" "v1.0.0" "HEAD" 2>&1)
run_test "Output contains feat commit" "echo '$OUTPUT' | grep -q 'feat: add new feature'"

# Test 7: Add fix commit
echo "Fix" >> file.txt
git add file.txt
git commit -q -m "fix: resolve bug"
run_test "Detects fix commit" "bash '$SCRIPT' 'v1.0.0' 'HEAD' > /dev/null 2>&1"

# Test 8: Add non-conventional commit
git tag v1.1.0
echo "Other" >> file.txt
git add file.txt
git commit -q -m "random commit message"
run_test "Ignores non-conventional commit" "! bash '$SCRIPT' 'v1.1.0' 'HEAD' > /dev/null 2>&1"

# Test 9: Test with scope
git tag v1.2.0
echo "Scope" >> file.txt
git add file.txt
git commit -q -m "feat(api): add new endpoint"
run_test "Detects commit with scope" "bash '$SCRIPT' 'v1.2.0' 'HEAD' > /dev/null 2>&1"

# Test 10: Test with breaking change marker
git tag v1.3.0
echo "Breaking" >> file.txt
git add file.txt
git commit -q -m "feat!: breaking change"
run_test "Detects breaking change marker" "bash '$SCRIPT' 'v1.3.0' 'HEAD' > /dev/null 2>&1"

# Test 11: Test different commit types
git tag v1.4.0
for type in fix perf refactor style docs test build ci chore; do
    echo "$type" >> file.txt
    git add file.txt
    git commit -q -m "$type: test commit"
done
run_test "Detects multiple commit types" "bash '$SCRIPT' 'v1.4.0' 'HEAD' > /dev/null 2>&1"

# Test 12: Test with v0.0.0 (no previous tag)
run_test "Handles v0.0.0 tag" "bash '$SCRIPT' 'v0.0.0' 'HEAD' > /dev/null 2>&1"

# Test 13: Test with non-existent tag
run_test "Handles non-existent tag" "bash '$SCRIPT' 'v99.99.99' 'HEAD' > /dev/null 2>&1"

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

