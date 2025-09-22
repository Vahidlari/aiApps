#!/bin/bash

# Database Server Manager
# This script provides a completely portable Database management solution
# Only requires Docker - works on Windows, WSL, macOS, and Linux

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORTABLE_COMPOSE_FILE="$SCRIPT_DIR/config/docker-compose.yml"
CONFIG_RELATIVE_PATH="config/user-config.yaml"
CONFIG_FILE="$SCRIPT_DIR/$CONFIG_RELATIVE_PATH"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${PURPLE}[WEAVIATE]${NC} $1"
}

# Function to check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker Desktop and try again."
        print_status "On Windows: Start Docker Desktop"
        print_status "On macOS: Start Docker Desktop"
        print_status "On Linux: Start Docker daemon (sudo systemctl start docker)"
        exit 1
    fi
}

# Function to load configuration using management container
load_config() {
    if [[ ! -f "$CONFIG_FILE" ]]; then
        print_error "Configuration file not found: $CONFIG_RELATIVE_PATH"
        print_status "Please create a $CONFIG_RELATIVE_PATH file first using: $0 config"
        exit 1
    fi
    
    print_status "Loading configuration from: $CONFIG_RELATIVE_PATH"
    
    # First, ensure the management image is built by docker-compose
    print_status "Building management image via Docker Compose..."
    if ! docker compose -f "$PORTABLE_COMPOSE_FILE" build database-management; then
        print_error "Failed to build management image"
        exit 1
    fi
    
    print_status "Using management container to load configuration..."
    
    # Use management container to load config and get environment variables
    local env_vars
    local docker_output
    local docker_exit_code
    
    # Run docker command and capture both output and exit code
    docker_output=$(docker run --rm \
        -v "$SCRIPT_DIR:/app" \
        -v "$(dirname "$CONFIG_FILE"):/config" \
        -w /app \
        database-management:latest \
        --config "/config/$(basename "$CONFIG_FILE")" 2>&1)
    
    docker_exit_code=$?
    
    if [[ $docker_exit_code -ne 0 ]]; then
        print_error "Failed to load configuration using management container"
        print_error "Docker command failed with exit code: $docker_exit_code"
        print_error "Docker output:"
        echo "$docker_output"
        exit 1
    fi
    
    # Extract environment variables from the output
    env_vars=$(echo "$docker_output" | grep "^export\|^unset" || true)
    
    if [[ -z "$env_vars" ]]; then
        print_error "No environment variables found in config loader output"
        print_error "Config loader output:"
        echo "$docker_output"
        exit 1
    fi
    
    print_status "Found environment variables, applying them..."
    
    # Source the environment variables
    local line_count=0
    while IFS= read -r line; do
        if [[ -n "$line" && ! "$line" =~ ^# ]]; then
            eval "$line"
            line_count=$((line_count + 1))
        fi
    done <<< "$env_vars"
    
    print_success "Configuration loaded successfully ($line_count environment variables set)"
}

# Function to check if Weaviate is running
is_weaviate_running() {
    docker ps --filter "name=weaviate" --filter "status=running" --format "{{.Names}}" | grep -q "weaviate"
}

# Function to check if Weaviate is healthy
is_weaviate_healthy() {
    local url="http://localhost:8080/v1/.well-known/ready"
    if curl -s -f "$url" >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to get Weaviate version
get_weaviate_version() {
    if is_weaviate_healthy; then
        local version=$(curl -s "http://localhost:8080/v1/meta" 2>/dev/null | grep -o '"version":"[^"]*"' | cut -d'"' -f4 2>/dev/null || echo "Unknown")
        echo "$version"
    else
        echo "Not available (service not healthy)"
    fi
}

# Function to get transformers version
get_transformers_version() {
    local transformers_url="http://localhost:8081/health"
    if curl -s -f "$transformers_url" >/dev/null 2>&1; then
        # Try to get version from health endpoint or container info
        local version=$(curl -s "http://localhost:8081/health" 2>/dev/null | grep -o '"version":"[^"]*"' | cut -d'"' -f4 2>/dev/null || echo "Unknown")
        if [ "$version" = "Unknown" ]; then
            # Fallback to container image version
            local container_id=$(docker ps --filter "name=t2v-transformers" --filter "status=running" --format "{{.ID}}" 2>/dev/null)
            if [ -n "$container_id" ]; then
                version=$(docker inspect "$container_id" --format='{{.Config.Image}}' 2>/dev/null | cut -d':' -f2 || echo "Unknown")
            fi
        fi
        echo "$version"
    else
        echo "Not available (service not running)"
    fi
}

# Function to get Docker image versions
get_docker_image_versions() {
    print_status "Docker Image Versions:"
    
    # Get Weaviate container image
    local weaviate_image=$(docker ps --filter "name=weaviate" --filter "status=running" --format "{{.Image}}" 2>/dev/null)
    if [ -n "$weaviate_image" ]; then
        echo "  Weaviate: $weaviate_image"
    else
        echo "  Weaviate: Not running"
    fi
    
    # Get Transformers container image
    local transformers_image=$(docker ps --filter "name=t2v-transformers" --filter "status=running" --format "{{.Image}}" 2>/dev/null)
    if [ -n "$transformers_image" ]; then
        echo "  Transformers: $transformers_image"
    else
        echo "  Transformers: Not running"
    fi
}

# Function to start Weaviate using portable compose
start_weaviate_portable() {
    print_status "Starting Weaviate server (portable mode)..."
    
    # Load configuration first
    load_config
    
    print_status "Starting Docker Compose services..."
    
    # Use portable compose file with environment variables
    if ! docker compose -f "$PORTABLE_COMPOSE_FILE" up -d weaviate t2v-transformers; then
        print_error "Failed to start Docker Compose services"
        exit 1
    fi
    
    # Wait for the service to be ready
    print_status "Waiting for Weaviate to be ready..."
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if is_weaviate_healthy; then
            print_success "Weaviate server is running and healthy!"
            print_status "Access Weaviate at: http://localhost:8080"
            return 0
        fi
        sleep 2
        attempt=$((attempt + 1))
        echo -n "."
    done
    
    echo ""
    print_warning "Weaviate started but may still be initializing. Check logs with: $0 logs"
}

# Function to stop Weaviate
stop_weaviate() {
    print_status "Stopping Weaviate server..."
    
    if ! is_weaviate_running; then
        print_warning "Weaviate is not running"
        return 0
    fi
    
    docker compose -f "$PORTABLE_COMPOSE_FILE" down
    print_success "Weaviate server stopped"
}

# Function to show status
show_status() {
    print_status "Database Server Status:"
    echo
    
    if is_weaviate_running; then
        print_success "Container Status: RUNNING"
        
        if is_weaviate_healthy; then
            print_success "Health Check: HEALTHY"
            print_status "Access URL: http://localhost:8080"
        else
            print_warning "Health Check: NOT HEALTHY (still initializing)"
        fi
        
        echo
        print_status "Server Versions:"
        local weaviate_version=$(get_weaviate_version)
        local transformers_version=$(get_transformers_version)
        echo "  Weaviate API Version: $weaviate_version"
        echo "  Transformers Version: $transformers_version"
        
        echo
        get_docker_image_versions
        
        echo
        print_status "Container Details:"
        docker compose -f "$PORTABLE_COMPOSE_FILE" ps
    else
        print_error "Container Status: NOT RUNNING"
    fi
}

# Function to show logs
show_logs() {
    print_status "Showing Weaviate logs (press Ctrl+C to exit):"
    docker compose -f "$PORTABLE_COMPOSE_FILE" logs -f
}

# Function to remove Weaviate
remove_weaviate() {
    print_warning "This will remove Weaviate container and all its data!"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Removing Weaviate server and data..."
        docker compose -f "$PORTABLE_COMPOSE_FILE" down -v
        docker volume rm weaviate_server_weaviate_data 2>/dev/null || true
        print_success "Weaviate server and data removed"
    else
        print_status "Operation cancelled"
    fi
}

# Function to create default config
create_config() {
    if [[ ! -f "$CONFIG_FILE" ]]; then
        print_status "Creating default configuration file..."
        cp "$SCRIPT_DIR/config/config.yaml.template" "$CONFIG_FILE"
        print_success "Default configuration created. Edit $CONFIG_RELATIVE_PATH to customize settings."
    else
        print_warning "Configuration file already exists: $CONFIG_RELATIVE_PATH"
        print_status "Current configuration:"
        cat "$CONFIG_FILE"
    fi
}

# Function to show help
show_help() {
    echo "Ultra-Portable Database Server Manager"
    echo
    echo "Usage: $0 [COMMAND]"
    echo
    echo "Commands:"
    echo "  start     Start the Database server"
    echo "  stop      Stop the Database server"
    echo "  restart   Restart the Database server"
    echo "  remove    Remove the Database server and all data"
    echo "  status    Show the current status"
    echo "  logs      Show the server logs"
    echo "  config    Create or show configuration file"
    echo "  help      Show this help message"
    echo
    echo "Examples:"
    echo "  $0 start"
    echo "  $0 status"
    echo "  $0 logs"
    echo "  $0 config"
    echo
    echo "Features:"
    echo "  ✅ Only requires Docker - no other dependencies"
    echo "  ✅ Works on Windows, WSL, macOS, and Linux"
    echo "  ✅ No need to install yq, jq, curl, or other tools"
    echo "  ✅ Completely portable and self-contained"
    echo
    echo "Perfect for:"
    echo "  - Windows development environments"
    echo "  - WSL (Windows Subsystem for Linux)"
    echo "  - CI/CD pipelines"
    echo "  - Any environment where installing dependencies is difficult"
}

# Function to show system info
show_system_info() {
    print_header "System Information"
    echo "Docker Version: $(docker --version)"
    echo "Docker Compose Version: $(docker compose version)"
    echo "Platform: $(uname -s) $(uname -m)"
    echo "Script Directory: $SCRIPT_DIR"
}

# Main script logic
main() {
    # Check Docker is running
    check_docker
    
    case "${1:-help}" in
        start)
            start_weaviate_portable
            ;;
        stop)
            stop_weaviate
            ;;
        restart)
            print_status "Restarting Database server..."
            stop_weaviate
            sleep 2
            start_weaviate_portable
            ;;
        remove)
            remove_weaviate
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs
            ;;
        config)
            create_config
            ;;
        info)
            show_system_info
            ;;
        help|--help|-h)
            show_help
            exit 0
            ;;
        *)
            print_error "Unknown command: $1"
            echo
            show_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
