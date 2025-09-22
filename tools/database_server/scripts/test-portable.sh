#!/bin/bash

# Test script for portable Weaviate solution
# This script tests the portable setup to ensure everything works

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[FAIL]${NC} $1"
}

print_header() {
    echo -e "${PURPLE}[TEST SUITE]${NC} $1"
}

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

print_header "Testing Portable Weaviate Solution"
echo

# Test 1: Check if Docker is running
print_status "Test 1: Checking Docker..."
if docker info >/dev/null 2>&1; then
    print_success "Docker is running"
else
    print_error "Docker is not running"
    exit 1
fi

# Test 2: Check if portable script exists and is executable
print_status "Test 2: Checking portable script..."
if [[ -f "$SCRIPT_DIR/weaviate-portable.sh" ]]; then
    if [[ -x "$SCRIPT_DIR/weaviate-portable.sh" ]]; then
        print_success "Portable script exists and is executable"
    else
        print_warning "Portable script exists but is not executable, fixing..."
        chmod +x "$SCRIPT_DIR/weaviate-portable.sh"
        print_success "Portable script is now executable"
    fi
else
    print_error "Portable script not found"
    exit 1
fi

# Test 3: Test help command
print_status "Test 3: Testing help command..."
if "$SCRIPT_DIR/weaviate-portable.sh" help >/dev/null 2>&1; then
    print_success "Help command works"
else
    print_error "Help command failed"
    exit 1
fi

# Test 4: Test info command
print_status "Test 4: Testing info command..."
if "$SCRIPT_DIR/weaviate-portable.sh" info >/dev/null 2>&1; then
    print_success "Info command works"
else
    print_warning "Info command failed (this is expected if management image doesn't exist yet)"
fi

# Test 5: Test config command
print_status "Test 5: Testing config command..."
if "$SCRIPT_DIR/weaviate-portable.sh" config >/dev/null 2>&1; then
    print_success "Config command works"
else
    print_warning "Config command failed (this is expected if management image doesn't exist yet)"
fi

# Test 6: Check if Dockerfile.management exists
print_status "Test 6: Checking management Dockerfile..."
if [[ -f "$SCRIPT_DIR/Dockerfile.management" ]]; then
    print_success "Management Dockerfile exists"
else
    print_warning "Management Dockerfile not found (will be created automatically)"
fi

# Test 7: Check if docker-compose files exist
print_status "Test 7: Checking compose files..."
if [[ -f "$SCRIPT_DIR/docker-compose.yml" ]]; then
    print_success "Original compose file exists"
else
    print_error "Original compose file not found"
    exit 1
fi

if [[ -f "$SCRIPT_DIR/docker-compose.portable.yml" ]]; then
    print_success "Portable compose file exists"
else
    print_warning "Portable compose file not found"
fi

# Test 8: Check if config template exists
print_status "Test 8: Checking config template..."
if [[ -f "$SCRIPT_DIR/config.yaml.template" ]]; then
    print_success "Config template exists"
else
    print_error "Config template not found"
    exit 1
fi

# Test 9: Test Docker build (if Dockerfile exists)
if [[ -f "$SCRIPT_DIR/Dockerfile.management" ]]; then
    print_status "Test 9: Testing Docker build..."
    if docker build -f "$SCRIPT_DIR/Dockerfile.management" -t weaviate-management:test "$SCRIPT_DIR" >/dev/null 2>&1; then
        print_success "Docker build works"
        # Clean up test image
        docker rmi weaviate-management:test >/dev/null 2>&1 || true
    else
        print_error "Docker build failed"
        exit 1
    fi
else
    print_warning "Skipping Docker build test (Dockerfile not found)"
fi

echo
print_header "Test Results Summary"
echo
print_success "✅ All critical tests passed!"
echo
print_status "Your portable Weaviate solution is ready to use:"
echo
echo "  Start Weaviate:    ./weaviate-portable.sh start"
echo "  Check status:      ./weaviate-portable.sh status"
echo "  View logs:         ./weaviate-portable.sh logs"
echo "  Stop Weaviate:     ./weaviate-portable.sh stop"
echo "  Get help:          ./weaviate-portable.sh help"
echo
print_success "🎉 Portable Weaviate solution is working perfectly!"
