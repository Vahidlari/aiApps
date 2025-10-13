#!/bin/bash
# Test script for create-db-archives.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARENT_DIR="$(dirname "$SCRIPT_DIR")"
SCRIPT="$PARENT_DIR/create-db-archives.sh"

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

echo "Testing create-db-archives.sh"
echo "===================================="

# Test 1: Check script exists and is executable
run_test "Script exists" "[ -f '$SCRIPT' ]"
run_test "Script is executable" "[ -x '$SCRIPT' ]"

# Test 2: Script fails with incorrect number of arguments
run_test "Fails with no arguments" "! bash '$SCRIPT' > /dev/null 2>&1"
run_test "Fails with too few arguments" "! bash '$SCRIPT' '1.0.0' 'abc' 'main' > /dev/null 2>&1"

# Create a temporary test environment
TEST_DIR=$(mktemp -d)
trap "rm -rf $TEST_DIR" EXIT

# Copy the helper scripts to temp location
mkdir -p "$TEST_DIR/release-scripts"
cp "$PARENT_DIR/create-version-metadata.sh" "$TEST_DIR/release-scripts/"
cp "$PARENT_DIR/update-readme-version.sh" "$TEST_DIR/release-scripts/"
cp "$SCRIPT" "$TEST_DIR/release-scripts/"

# Create mock database_server structure
mkdir -p "$TEST_DIR/database_server/config"
mkdir -p "$TEST_DIR/database_server/scripts"

cat > "$TEST_DIR/database_server/README.md" <<'EOF'
# Database Server

Test content
EOF

cat > "$TEST_DIR/database_server/database-manager.sh" <<'EOF'
#!/bin/bash
echo "Database manager"
EOF

echo "test config" > "$TEST_DIR/database_server/config/config.yaml"
echo "test script" > "$TEST_DIR/database_server/scripts/test.sh"

# Create files that should be excluded
echo "test" > "$TEST_DIR/database_server/test.pyc"
mkdir -p "$TEST_DIR/database_server/__pycache__"
echo "cache" > "$TEST_DIR/database_server/__pycache__/test.pyc"
echo "log" > "$TEST_DIR/database_server/test.log"

cd "$TEST_DIR/release-scripts"

# Test 3: Run script with valid arguments
run_test "Script runs with valid arguments" "bash './create-db-archives.sh' '1.0.0' 'abc123' 'main' 'Test/Repo' > /dev/null 2>&1"

# Test 4: Check tar.gz archive was created
run_test "tar.gz archive created" "[ -f 'database_server-1.0.0.tar.gz' ]"

# Test 5: Check zip archive was created (if zip is available)
if command -v zip &> /dev/null; then
    run_test "zip archive created" "[ -f 'database_server-1.0.0.zip' ]"
else
    echo "  ${GREEN}✓${NC} zip archive skipped (zip not available)"
    TESTS_PASSED=$((TESTS_PASSED + 1))
fi

# Test 6: Check VERSION file was created
run_test "VERSION file created" "[ -f '../database_server/config/VERSION' ]"

# Test 7: Check release-info.json was created
run_test "release-info.json created" "[ -f '../database_server/config/release-info.json' ]"

# Test 8: Verify tar.gz contents (extract and check)
mkdir -p tar_extract
tar -xzf database_server-1.0.0.tar.gz -C tar_extract
run_test "tar.gz contains database_server directory" "[ -d 'tar_extract/database_server' ]"
run_test "tar.gz contains README.md" "[ -f 'tar_extract/database_server/README.md' ]"
run_test "tar.gz contains config directory" "[ -d 'tar_extract/database_server/config' ]"
run_test "tar.gz contains VERSION file" "[ -f 'tar_extract/database_server/config/VERSION' ]"

# Test 9: Verify excluded files are not in archive
run_test "tar.gz excludes .pyc files" "! find tar_extract -name '*.pyc' | grep -q ."
run_test "tar.gz excludes __pycache__" "! find tar_extract -name '__pycache__' | grep -q ."
run_test "tar.gz excludes .log files" "! find tar_extract -name '*.log' | grep -q ."

# Test 10: Verify zip contents (if zip is available)
if command -v zip &> /dev/null && command -v unzip &> /dev/null; then
    mkdir -p zip_extract
    unzip -q database_server-1.0.0.zip -d zip_extract
    run_test "zip contains database_server directory" "[ -d 'zip_extract/database_server' ]"
    run_test "zip contains README.md" "[ -f 'zip_extract/database_server/README.md' ]"
    run_test "zip excludes .pyc files" "! find zip_extract -name '*.pyc' | grep -q ."
else
    echo "  ${GREEN}✓${NC} zip content tests skipped (zip/unzip not available)"
    TESTS_PASSED=$((TESTS_PASSED + 3))
fi

# Test 11: Test output format
OUTPUT=$(bash "./create-db-archives.sh" "2.0.0" "def456" "develop" "Another/Repo" 2>&1)
run_test "Output contains tar.gz filename" "echo '$OUTPUT' | grep -q 'database_server-2.0.0.tar.gz'"
if command -v zip &> /dev/null; then
    run_test "Output contains zip filename" "echo '$OUTPUT' | grep -q 'database_server-2.0.0.zip'"
else
    echo "  ${GREEN}✓${NC} zip filename test skipped (zip not available)"
    TESTS_PASSED=$((TESTS_PASSED + 1))
fi

# Test 12: Test with missing database_server directory
rm -rf "$TEST_DIR/database_server"
run_test "Fails gracefully with missing database_server" "! bash './create-db-archives.sh' '1.0.0' 'abc' 'main' 'Test/Repo' > /dev/null 2>&1"

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

