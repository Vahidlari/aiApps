#!/bin/bash
# Master test runner for release scripts
# Runs both bash tests and Python tests, provides comprehensive summary

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
SKIPPED_TESTS=0

# Track test results
FAILED_TEST_NAMES=()

echo "======================================================================="
echo "                   Release Scripts Test Runner                         "
echo "======================================================================="
echo ""

# Parse command line arguments
VERBOSE=false
SPECIFIC_TEST=""
PYTHON_ONLY=false
BASH_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -t|--test)
            SPECIFIC_TEST="$2"
            shift 2
            ;;
        --python-only)
            PYTHON_ONLY=true
            shift
            ;;
        --bash-only)
            BASH_ONLY=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -v, --verbose      Run tests in verbose mode"
            echo "  -t, --test NAME    Run specific test (e.g., test-check-commits.sh)"
            echo "  --python-only      Run only Python tests"
            echo "  --bash-only        Run only Bash tests"
            echo "  -h, --help         Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

# Function to run bash tests
run_bash_tests() {
    echo -e "${BLUE}Running Bash Tests...${NC}"
    echo ""
    
    # Find all bash test files
    BASH_TESTS=$(find . -maxdepth 1 -name "test-*.sh" -type f | sort)
    
    if [ -z "$BASH_TESTS" ]; then
        echo -e "${YELLOW}No bash tests found${NC}"
        return
    fi
    
    for test_file in $BASH_TESTS; do
        test_name=$(basename "$test_file")
        
        # Skip if specific test requested and this isn't it
        if [ -n "$SPECIFIC_TEST" ] && [ "$SPECIFIC_TEST" != "$test_name" ]; then
            continue
        fi
        
        TOTAL_TESTS=$((TOTAL_TESTS + 1))
        
        echo -e "${BLUE}Running: ${test_name}${NC}"
        
        if [ "$VERBOSE" = true ]; then
            if bash "$test_file"; then
                PASSED_TESTS=$((PASSED_TESTS + 1))
                echo -e "${GREEN}✓ $test_name PASSED${NC}"
            else
                FAILED_TESTS=$((FAILED_TESTS + 1))
                FAILED_TEST_NAMES+=("$test_name")
                echo -e "${RED}✗ $test_name FAILED${NC}"
            fi
        else
            if bash "$test_file" > /dev/null 2>&1; then
                PASSED_TESTS=$((PASSED_TESTS + 1))
                echo -e "${GREEN}✓ $test_name PASSED${NC}"
            else
                FAILED_TESTS=$((FAILED_TESTS + 1))
                FAILED_TEST_NAMES+=("$test_name")
                echo -e "${RED}✗ $test_name FAILED${NC}"
                # Show output on failure even in non-verbose mode
                echo "  Running again with output:"
                bash "$test_file" 2>&1 | sed 's/^/    /'
            fi
        fi
        echo ""
    done
}

# Function to run Python tests
run_python_tests() {
    echo -e "${BLUE}Running Python Tests...${NC}"
    echo ""
    
    # Check if pytest is available
    if ! command -v pytest &> /dev/null; then
        echo -e "${YELLOW}pytest not found, skipping Python tests${NC}"
        echo -e "${YELLOW}Install with: pip install pytest${NC}"
        echo ""
        return
    fi
    
    # Find Python test files
    PYTHON_TESTS=$(find . -maxdepth 1 -name "test_*.py" -type f | sort)
    
    if [ -z "$PYTHON_TESTS" ]; then
        echo -e "${YELLOW}No Python tests found${NC}"
        return
    fi
    
    # Run pytest
    if [ -n "$SPECIFIC_TEST" ]; then
        # Run specific test file
        if [ -f "$SPECIFIC_TEST" ]; then
            if [ "$VERBOSE" = true ]; then
                pytest -v "$SPECIFIC_TEST"
            else
                pytest "$SPECIFIC_TEST"
            fi
            PYTEST_EXIT=$?
        else
            echo -e "${RED}Test file not found: $SPECIFIC_TEST${NC}"
            PYTEST_EXIT=1
        fi
    else
        # Run all Python tests
        if [ "$VERBOSE" = true ]; then
            pytest -v test_*.py
        else
            pytest test_*.py
        fi
        PYTEST_EXIT=$?
    fi
    
    # Count pytest results (simple approximation)
    if [ $PYTEST_EXIT -eq 0 ]; then
        # All passed
        PYTHON_TEST_COUNT=$(echo "$PYTHON_TESTS" | wc -l)
        TOTAL_TESTS=$((TOTAL_TESTS + PYTHON_TEST_COUNT))
        PASSED_TESTS=$((PASSED_TESTS + PYTHON_TEST_COUNT))
        echo -e "${GREEN}All Python tests passed${NC}"
    else
        PYTHON_TEST_COUNT=$(echo "$PYTHON_TESTS" | wc -l)
        TOTAL_TESTS=$((TOTAL_TESTS + PYTHON_TEST_COUNT))
        FAILED_TESTS=$((FAILED_TESTS + 1))
        FAILED_TEST_NAMES+=("Python tests")
        echo -e "${RED}Some Python tests failed${NC}"
    fi
    echo ""
}

# Run tests based on options
if [ "$PYTHON_ONLY" = true ]; then
    run_python_tests
elif [ "$BASH_ONLY" = true ]; then
    run_bash_tests
else
    run_bash_tests
    run_python_tests
fi

# Print summary
echo "======================================================================="
echo "                          Test Summary                                  "
echo "======================================================================="
echo ""
echo -e "Total Tests:  ${BLUE}${TOTAL_TESTS}${NC}"
echo -e "Passed:       ${GREEN}${PASSED_TESTS}${NC}"
echo -e "Failed:       ${RED}${FAILED_TESTS}${NC}"

if [ ${FAILED_TESTS} -gt 0 ]; then
    echo ""
    echo -e "${RED}Failed Tests:${NC}"
    for failed_test in "${FAILED_TEST_NAMES[@]}"; do
        echo -e "  ${RED}✗${NC} $failed_test"
    done
fi

echo ""
echo "======================================================================="

# Exit with appropriate code
if [ ${FAILED_TESTS} -gt 0 ]; then
    echo -e "${RED}TESTS FAILED${NC}"
    exit 1
else
    echo -e "${GREEN}ALL TESTS PASSED${NC}"
    exit 0
fi

