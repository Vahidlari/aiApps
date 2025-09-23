#!/bin/bash

# Configuration Loader
# A bash script to load configuration from YAML file and export as environment variables

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default configuration values
DEFAULT_CONFIG="{
  \"server\": {
    \"version\": \"1.23.7\",
    \"port\": 8080,
    \"grpc_port\": 50051,
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

# Function to show help
show_help() {
    echo "Configuration Loader"
    echo
    echo "Usage: $0 --config <config.yaml>"
    echo
    echo "Options:"
    echo "  --config FILE    Path to YAML configuration file"
    echo "  --help, -h       Show this help message"
    echo
    echo "Examples:"
    echo "  $0 --config config.yaml"
    echo "  $0 --config /path/to/config.yaml"
    echo
    echo "This script loads configuration from a YAML file and exports it as environment variables."
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

# Function to check if jq is installed
check_jq() {
    if ! command -v jq &> /dev/null; then
        print_error "jq is required to parse configuration but is not installed."
        print_status "Please install jq:"
        print_status "  macOS: brew install jq"
        print_status "  Ubuntu: sudo apt-get install jq"
        exit 1
    fi
}

# Function to load configuration from YAML file
load_config() {
    local config_file="$1"
    
    if [[ -f "$config_file" ]]; then
        print_status "Loading configuration from: $config_file"
        # Convert YAML to JSON and merge with defaults
        CONFIG=$(yq eval -o=json "$config_file" 2>/dev/null || echo "$DEFAULT_CONFIG")
    else
        print_error "Configuration file not found: $config_file"
        exit 1
    fi
    
    # Export configuration as environment variables
    export_config_vars
}

# Function to export configuration as environment variables
export_config_vars() {
    # Server configuration
    export WEAVIATE_VERSION=$(echo "$CONFIG" | jq -r '.server.version // "1.23.7"')
    export WEAVIATE_PORT=$(echo "$CONFIG" | jq -r '.server.port // 8080')
    export WEAVIATE_GRPC_PORT=$(echo "$CONFIG" | jq -r '.server.grpc_port // 50051')
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
    
    print_success "Configuration loaded and exported as environment variables"
    
    # Output environment variables in a format that can be sourced
    echo "# Environment variables for docker-compose"
    echo "export WEAVIATE_VERSION=\"$(echo "$CONFIG" | jq -r '.server.version // "1.23.7"')\""
    echo "export WEAVIATE_PORT=\"$(echo "$CONFIG" | jq -r '.server.port // 8080')\""
    echo "export WEAVIATE_GRPC_PORT=\"$(echo "$CONFIG" | jq -r '.server.grpc_port // 50051')\""
    echo "export WEAVIATE_CONTAINER_NAME=\"$(echo "$CONFIG" | jq -r '.server.container_name // "weaviate"')\""
    echo "export WEAVIATE_RESTART_POLICY=\"$(echo "$CONFIG" | jq -r '.server.restart_policy // "unless-stopped"')\""
    echo "export AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=\"$(echo "$CONFIG" | jq -r '.authentication.anonymous_access_enabled // true')\""
    echo "export AUTHENTICATION_APIKEY_ENABLED=\"$(echo "$CONFIG" | jq -r '.authentication.api_key_enabled // false')\""
    echo "export AUTHENTICATION_APIKEY_ALLOWED_KEYS=\"$(echo "$CONFIG" | jq -r '.authentication.api_key_allowed_keys[]? // empty' | tr '\n' ',' | sed 's/,$//')\""
    echo "export AUTHENTICATION_APIKEY_USERS=\"$(echo "$CONFIG" | jq -r '.authentication.api_key_users[]? // empty' | tr '\n' ',' | sed 's/,$//')\""
    echo "export PERSISTENCE_DATA_PATH=\"$(echo "$CONFIG" | jq -r '.persistence.data_path // "/var/lib/weaviate"')\""
    echo "export WEAVIATE_VOLUME_NAME=\"$(echo "$CONFIG" | jq -r '.persistence.volume_name // "weaviate_data"')\""
    echo "export ENABLE_MODULES=\"$(echo "$CONFIG" | jq -r '.modules.enabled[]? // empty' | tr '\n' ',' | sed 's/,$//')\""
    echo "export TRANSFORMERS_INFERENCE_API=\"$(echo "$CONFIG" | jq -r '.transformers.inference_api // "http://t2v-transformers:8080"')\""
    echo "export TRANSFORMERS_CONTAINER_NAME=\"$(echo "$CONFIG" | jq -r '.transformers.container_name // "t2v-transformers"')\""
    echo "export TRANSFORMERS_PORT=\"$(echo "$CONFIG" | jq -r '.transformers.port // 8081')\""
    echo "export TRANSFORMERS_RESTART_POLICY=\"$(echo "$CONFIG" | jq -r '.transformers.restart_policy // "unless-stopped"')\""
    echo "export ENABLE_CUDA=\"$(echo "$CONFIG" | jq -r '.transformers.enable_cuda // 0')\""
    echo "export CLUSTER_HOSTNAME=\"$(echo "$CONFIG" | jq -r '.cluster.hostname // "node1"')\""
    echo "export LOG_LEVEL=\"$(echo "$CONFIG" | jq -r '.logging.level // "INFO"')\""
    echo "export LOG_FORMAT=\"$(echo "$CONFIG" | jq -r '.logging.format // "json"')\""
    
    # Handle resource limits
    local memory_limit=$(echo "$CONFIG" | jq -r '.resources.memory_limit // empty')
    local cpu_limit=$(echo "$CONFIG" | jq -r '.resources.cpu_limit // empty')
    
    if [[ -n "$memory_limit" && "$memory_limit" != "null" ]]; then
        echo "export MEMORY_LIMIT=\"$memory_limit\""
    else
        echo "unset MEMORY_LIMIT"
    fi
    
    if [[ -n "$cpu_limit" && "$cpu_limit" != "null" ]]; then
        echo "export CPU_LIMIT=\"$cpu_limit\""
    else
        echo "unset CPU_LIMIT"
    fi
}

# Function to validate configuration
validate_config() {
    # Validate JSON configuration
    if ! echo "$CONFIG" | jq . >/dev/null 2>&1; then
        print_error "Invalid configuration JSON"
        exit 1
    fi
}

# Function to parse command line arguments
parse_args() {
    CONFIG_FILE=""
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --config)
                CONFIG_FILE="$2"
                shift 2
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                echo
                show_help
                exit 1
                ;;
        esac
    done
    
    if [[ -z "$CONFIG_FILE" ]]; then
        print_error "Configuration file is required. Use --config <file>"
        echo
        show_help
        exit 1
    fi
}

# Main script logic
main() {
    parse_args "$@"
    
    # Check dependencies
    check_yq
    check_jq
    
    # Load and validate configuration
    load_config "$CONFIG_FILE"
    validate_config
}

# Run main function with all arguments
main "$@"
