#!/bin/bash

# Weaviate Server Manager
# A bash script to manage Weaviate server using Docker Compose with flexible configuration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml"
CONFIG_FILE="$SCRIPT_DIR/config.yaml"

# Default configuration values
DEFAULT_CONFIG="{
  \"server\": {
    \"version\": \"1.22.4\",
    \"port\": 8080,
    \"container_name\": \"weaviate\",
    \"restart_policy\": \"unless-stopped\"
  },
  \"authentication\": {
    \"anonymous_access_enabled\": true,
    \"api_key_enabled\": false,
    \"api_key_allowed_keys\": [],
    \"api_key_users\": []
  },
  \"persistence\": {
    \"data_path\": \"/var/lib/weaviate\",
    \"volume_name\": \"weaviate_data\"
  },
  \"modules\": {
    \"enabled\": [\"text2vec-transformers\", \"text2vec-cohere\", \"text2vec-huggingface\", \"text2vec-palm\", \"text2vec-openai\", \"generative-openai\", \"qna-openai\"]
  },
  \"transformers\": {
    \"inference_api\": \"http://t2v-transformers:8080\",
    \"container_name\": \"t2v-transformers\",
    \"port\": 8081,
    \"restart_policy\": \"unless-stopped\",
    \"enable_cuda\": 0,
    \"health_check\": {
      \"enabled\": true,
      \"interval\": 30,
      \"timeout\": 10,
      \"retries\": 5,
      \"start_period\": 60
    }
  },
  \"cluster\": {
    \"hostname\": \"node1\"
  },
  \"health_check\": {
    \"enabled\": true,
    \"interval\": 30,
    \"timeout\": 10,
    \"retries\": 5,
    \"start_period\": 40
  },
  \"logging\": {
    \"level\": \"INFO\",
    \"format\": \"json\"
  },
  \"resources\": {
    \"memory_limit\": null,
    \"cpu_limit\": null
  },
  \"environment\": {}
}"

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

# Function to check if yq is installed
check_yq() {
    if ! command -v yq &> /dev/null; then
        print_error "yq is required to parse YAML configuration but is not installed."
        print_status "Please install yq:"
        print_status "  macOS: brew install yq"
        print_status "  Ubuntu: sudo apt-get install yq"
        print_status "  Or download from: https://github.com/mikefarah/yq"
        exit 1
    fi
}

# Function to load configuration from YAML file
load_config() {
    if [[ -f "$CONFIG_FILE" ]]; then
        print_status "Loading configuration from: $CONFIG_FILE"
        # Convert YAML to JSON and merge with defaults
        CONFIG=$(yq eval -o=json "$CONFIG_FILE" 2>/dev/null || echo "$DEFAULT_CONFIG")
    else
        print_warning "No config.yaml found, using default configuration"
        print_status "To customize, copy config.yaml.template to config.yaml and modify as needed"
        CONFIG="$DEFAULT_CONFIG"
    fi
    
    # Export configuration as environment variables for docker-compose
    export_config_vars
}

# Function to export configuration as environment variables
export_config_vars() {
    # Server configuration
    export WEAVIATE_VERSION=$(echo "$CONFIG" | jq -r '.server.version // "1.22.4"')
    export WEAVIATE_PORT=$(echo "$CONFIG" | jq -r '.server.port // 8080')
    export WEAVIATE_CONTAINER_NAME=$(echo "$CONFIG" | jq -r '.server.container_name // "weaviate"')
    export WEAVIATE_RESTART_POLICY=$(echo "$CONFIG" | jq -r '.server.restart_policy // "unless-stopped"')
    
    # Authentication configuration
    export AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=$(echo "$CONFIG" | jq -r '.authentication.anonymous_access_enabled // true')
    export AUTHENTICATION_APIKEY_ENABLED=$(echo "$CONFIG" | jq -r '.authentication.api_key_enabled // false')
    
    # Handle API key arrays
    local api_keys=$(echo "$CONFIG" | jq -r '.authentication.api_key_allowed_keys[]? // empty' | tr '\n' ',' | sed 's/,$//')
    export AUTHENTICATION_APIKEY_ALLOWED_KEYS="$api_keys"
    
    local api_users=$(echo "$CONFIG" | jq -r '.authentication.api_key_users[]? // empty' | tr '\n' ',' | sed 's/,$//')
    export AUTHENTICATION_APIKEY_USERS="$api_users"
    
    # Persistence configuration
    export PERSISTENCE_DATA_PATH=$(echo "$CONFIG" | jq -r '.persistence.data_path // "/var/lib/weaviate"')
    export WEAVIATE_VOLUME_NAME=$(echo "$CONFIG" | jq -r '.persistence.volume_name // "weaviate_data"')
    
    # Modules configuration
    local modules=$(echo "$CONFIG" | jq -r '.modules.enabled[]? // empty' | tr '\n' ',' | sed 's/,$//')
    export ENABLE_MODULES="$modules"
    
    # Transformers configuration
    export TRANSFORMERS_INFERENCE_API=$(echo "$CONFIG" | jq -r '.transformers.inference_api // "http://t2v-transformers:8080"')
    export TRANSFORMERS_CONTAINER_NAME=$(echo "$CONFIG" | jq -r '.transformers.container_name // "t2v-transformers"')
    export TRANSFORMERS_PORT=$(echo "$CONFIG" | jq -r '.transformers.port // 8081')
    export TRANSFORMERS_RESTART_POLICY=$(echo "$CONFIG" | jq -r '.transformers.restart_policy // "unless-stopped"')
    export ENABLE_CUDA=$(echo "$CONFIG" | jq -r '.transformers.enable_cuda // 0')
    
    # Transformers health check configuration
    export TRANSFORMERS_HEALTH_CHECK_INTERVAL="${TRANSFORMERS_HEALTH_CHECK_INTERVAL:-30s}"
    export TRANSFORMERS_HEALTH_CHECK_TIMEOUT="${TRANSFORMERS_HEALTH_CHECK_TIMEOUT:-10s}"
    export TRANSFORMERS_HEALTH_CHECK_RETRIES="${TRANSFORMERS_HEALTH_CHECK_RETRIES:-5}"
    export TRANSFORMERS_HEALTH_CHECK_START_PERIOD="${TRANSFORMERS_HEALTH_CHECK_START_PERIOD:-60s}"
    
    # Cluster configuration
    export CLUSTER_HOSTNAME=$(echo "$CONFIG" | jq -r '.cluster.hostname // "node1"')
    
    # Health check configuration
    export HEALTH_CHECK_INTERVAL="${HEALTH_CHECK_INTERVAL:-30s}"
    export HEALTH_CHECK_TIMEOUT="${HEALTH_CHECK_TIMEOUT:-10s}"
    export HEALTH_CHECK_RETRIES="${HEALTH_CHECK_RETRIES:-5}"
    export HEALTH_CHECK_START_PERIOD="${HEALTH_CHECK_START_PERIOD:-40s}"
    
    # Logging configuration
    export LOG_LEVEL=$(echo "$CONFIG" | jq -r '.logging.level // "INFO"')
    export LOG_FORMAT=$(echo "$CONFIG" | jq -r '.logging.format // "json"')
    
    # Resource limits
    local memory_limit=$(echo "$CONFIG" | jq -r '.resources.memory_limit // empty')
    local cpu_limit=$(echo "$CONFIG" | jq -r '.resources.cpu_limit // empty')
    
    if [[ -n "$memory_limit" ]]; then
        export MEMORY_LIMIT="$memory_limit"
    else
        unset MEMORY_LIMIT
    fi
    
    if [[ -n "$cpu_limit" ]]; then
        export CPU_LIMIT="$cpu_limit"
    else
        unset CPU_LIMIT
    fi
    
    # Additional environment variables
    local additional_env=""
    echo "$CONFIG" | jq -r '.environment | to_entries[]? | "\(.key)=\(.value)"' | while read -r env_var; do
        if [[ -n "$env_var" ]]; then
            additional_env="$additional_env$env_var\n"
        fi
    done
    
    # Only export if there are additional environment variables
    if [[ -n "$additional_env" ]]; then
        export ADDITIONAL_ENV_VARS=$(echo -e "$additional_env" | tr '\n' ' ')
    else
        unset ADDITIONAL_ENV_VARS
    fi
}

# Function to create default config file
create_default_config() {
    if [[ ! -f "$CONFIG_FILE" ]]; then
        print_status "Creating default configuration file: $CONFIG_FILE"
        cp "$SCRIPT_DIR/config.yaml.template" "$CONFIG_FILE"
        print_success "Default configuration created. Edit $CONFIG_FILE to customize settings."
    else
        print_warning "Configuration file already exists: $CONFIG_FILE"
    fi
}

# Function to validate configuration
validate_config() {
    # Check if required tools are available
    if ! command -v jq &> /dev/null; then
        print_error "jq is required to parse configuration but is not installed."
        print_status "Please install jq:"
        print_status "  macOS: brew install jq"
        print_status "  Ubuntu: sudo apt-get install jq"
        exit 1
    fi
    
    # Validate JSON configuration
    if ! echo "$CONFIG" | jq . >/dev/null 2>&1; then
        print_error "Invalid configuration JSON"
        exit 1
    fi
}

# Function to check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker Desktop and try again."
        exit 1
    fi
}

# Function to check if Weaviate is running
is_running() {
    docker compose -f "$COMPOSE_FILE" ps --services --filter "status=running" | grep -q "weaviate"
}

# Function to check if Weaviate is healthy
is_healthy() {
    local url="http://localhost:8080/v1/.well-known/ready"
    if curl -s -f "$url" >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to start Weaviate
start_weaviate() {
    print_status "Starting Weaviate server..."
    
    # Create temporary docker-compose file if needed
    local temp_compose_file="$COMPOSE_FILE"
    local needs_temp_file=false
    
    # Check if we need to modify the compose file
    # Always create temp file if no resource limits are set
    if [[ -n "$ADDITIONAL_ENV_VARS" ]] || [[ -z "${MEMORY_LIMIT:-}" && -z "${CPU_LIMIT:-}" ]]; then
        needs_temp_file=true
    fi
    
    if [[ "$needs_temp_file" == "true" ]]; then
        temp_compose_file="/tmp/weaviate-compose-$$.yml"
        cp "$COMPOSE_FILE" "$temp_compose_file"
        
        # Remove deploy section if no resource limits are set
        if [[ -z "$MEMORY_LIMIT" && -z "$CPU_LIMIT" ]]; then
            sed -i.bak '/^    deploy:/,/^$/d' "$temp_compose_file"
        fi
        
        # Add additional environment variables if needed
        if [[ -n "$ADDITIONAL_ENV_VARS" ]]; then
            local env_vars=()
            IFS=' ' read -ra ADDR <<< "$ADDITIONAL_ENV_VARS"
            for var in "${ADDR[@]}"; do
                if [[ -n "$var" ]]; then
                    env_vars+=("      - $var")
                fi
            done
            
            if [[ ${#env_vars[@]} -gt 0 ]]; then
                # Insert additional environment variables before the volumes section
                sed -i.bak "/^    volumes:/i\\
$(printf '%s\n' "${env_vars[@]}")
" "$temp_compose_file"
            fi
        fi
    fi
    
    # Check if running using the appropriate compose file
    if docker compose -f "$temp_compose_file" ps --services --filter "status=running" | grep -q "weaviate"; then
        print_warning "Weaviate is already running"
        # Clean up temporary file if created
        if [[ "$temp_compose_file" != "$COMPOSE_FILE" ]]; then
            rm -f "$temp_compose_file" "$temp_compose_file.bak"
        fi
        return 0
    fi
    
    docker compose -f "$temp_compose_file" up -d
    
    # Clean up temporary file if created
    if [[ "$temp_compose_file" != "$COMPOSE_FILE" ]]; then
        rm -f "$temp_compose_file" "$temp_compose_file.bak"
    fi
    
    # Wait for the service to be ready
    print_status "Waiting for Weaviate to be ready..."
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if is_healthy; then
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
    
    # Create temporary docker-compose file if needed (same logic as start)
    local temp_compose_file="$COMPOSE_FILE"
    local needs_temp_file=false
    
    if [[ -n "$ADDITIONAL_ENV_VARS" ]] || [[ -z "${MEMORY_LIMIT:-}" && -z "${CPU_LIMIT:-}" ]]; then
        needs_temp_file=true
    fi
    
    if [[ "$needs_temp_file" == "true" ]]; then
        temp_compose_file="/tmp/weaviate-compose-$$.yml"
        cp "$COMPOSE_FILE" "$temp_compose_file"
        
        # Remove deploy section if no resource limits are set
        if [[ -z "$MEMORY_LIMIT" && -z "$CPU_LIMIT" ]]; then
            sed -i.bak '/^    deploy:/,/^$/d' "$temp_compose_file"
        fi
    fi
    
    if ! docker compose -f "$temp_compose_file" ps --services --filter "status=running" | grep -q "weaviate"; then
        print_warning "Weaviate is not running"
        # Clean up temporary file if created
        if [[ "$temp_compose_file" != "$COMPOSE_FILE" ]]; then
            rm -f "$temp_compose_file" "$temp_compose_file.bak"
        fi
        return 0
    fi
    
    docker compose -f "$temp_compose_file" down
    
    # Clean up temporary file if created
    if [[ "$temp_compose_file" != "$COMPOSE_FILE" ]]; then
        rm -f "$temp_compose_file" "$temp_compose_file.bak"
    fi
    print_success "Weaviate server stopped"
}

# Function to restart Weaviate
restart_weaviate() {
    print_status "Restarting Weaviate server..."
    stop_weaviate
    sleep 2
    start_weaviate
}

# Function to remove Weaviate and its data
remove_weaviate() {
    print_warning "This will remove Weaviate container and all its data!"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Removing Weaviate server and data..."
        docker compose -f "$COMPOSE_FILE" down -v
        docker volume rm weaviate_server_weaviate_data 2>/dev/null || true
        print_success "Weaviate server and data removed"
    else
        print_status "Operation cancelled"
    fi
}

# Function to show status
show_status() {
    print_status "Weaviate Server Status:"
    echo
    
    # Create temporary docker-compose file if needed (same logic as start/stop)
    local temp_compose_file="$COMPOSE_FILE"
    local needs_temp_file=false
    
    if [[ -n "$ADDITIONAL_ENV_VARS" ]] || [[ -z "${MEMORY_LIMIT:-}" && -z "${CPU_LIMIT:-}" ]]; then
        needs_temp_file=true
    fi
    
    if [[ "$needs_temp_file" == "true" ]]; then
        temp_compose_file="/tmp/weaviate-compose-$$.yml"
        cp "$COMPOSE_FILE" "$temp_compose_file"
        
        # Remove deploy section if no resource limits are set
        if [[ -z "$MEMORY_LIMIT" && -z "$CPU_LIMIT" ]]; then
            sed -i.bak '/^    deploy:/,/^$/d' "$temp_compose_file"
        fi
    fi
    
    if docker compose -f "$temp_compose_file" ps --services --filter "status=running" | grep -q "weaviate"; then
        print_success "Container Status: RUNNING"
        
        if curl -s http://localhost:8080/v1/.well-known/ready >/dev/null 2>&1; then
            print_success "Health Check: HEALTHY"
            print_status "Access URL: http://localhost:8080"
        else
            print_warning "Health Check: NOT HEALTHY (still initializing)"
        fi
        
        echo
        print_status "Container Details:"
        docker compose -f "$temp_compose_file" ps
    else
        print_error "Container Status: NOT RUNNING"
    fi
    
    # Clean up temporary file if created
    if [[ "$temp_compose_file" != "$COMPOSE_FILE" ]]; then
        rm -f "$temp_compose_file" "$temp_compose_file.bak"
    fi
}

# Function to show logs
show_logs() {
    print_status "Showing Weaviate logs (press Ctrl+C to exit):"
    docker compose -f "$COMPOSE_FILE" logs -f
}

# Function to show help
show_help() {
    echo "Weaviate Server Manager"
    echo
    echo "Usage: $0 [COMMAND]"
    echo
    echo "Commands:"
    echo "  start     Start the Weaviate server"
    echo "  stop      Stop the Weaviate server"
    echo "  restart   Restart the Weaviate server"
    echo "  remove    Remove the Weaviate server and all data"
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
    echo "Configuration:"
    echo "  The script uses config.yaml for configuration. If not found, it uses defaults."
    echo "  Copy config.yaml.template to config.yaml and modify as needed."
}

# Main script logic
main() {
    case "${1:-help}" in
        config)
            create_default_config
            ;;
        help|--help|-h)
            show_help
            exit 0
            ;;
        *)
            # For all other commands, check dependencies and load config
            check_docker
            check_yq
            load_config
            validate_config
            ;;
    esac
    
    case "${1:-help}" in
        start)
            start_weaviate
            ;;
        stop)
            stop_weaviate
            ;;
        restart)
            restart_weaviate
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
            # Already handled above, but show current config if it exists
            if [[ -f "$CONFIG_FILE" ]]; then
                print_status "Current configuration:"
                cat "$CONFIG_FILE"
            else
                print_status "No configuration file found. Run '$0 config' to create one."
            fi
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
