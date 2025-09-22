# Configuration Examples

This directory contains example configuration files for different Weaviate deployment scenarios.

## Available Configurations

### `config-development.yaml`
**Use case**: Local development and experimentation
- ✅ Anonymous access enabled for easy testing
- ✅ Debug logging enabled
- ✅ Minimal resource usage
- ✅ Basic modules only
- ✅ Human-readable log format

### `config-production.yaml`
**Use case**: Production deployments
- 🔒 API key authentication required
- 📊 Structured JSON logging
- 🚀 Full module set enabled
- 💾 Generous resource allocation
- 🔧 Production-optimized settings

### `config-testing.yaml`
**Use case**: CI/CD pipelines and automated testing
- ⚡ Fast startup and health checks
- 🔄 Minimal resource usage
- 🚫 No auto-restart policy
- 📝 Minimal logging
- 🧪 Testing-specific environment variables

## How to Use

1. **Choose the appropriate configuration** for your use case
2. **Copy it to the main directory** as `config.yaml`:
   ```bash
   cp examples/config-development.yaml config.yaml
   ```
3. **Customize as needed** by editing the copied file
4. **Run the manager script** as usual:
   ```bash
   ./weaviate_manager.sh start
   ```

## Configuration Parameters

### Server Settings
- `version`: Weaviate Docker image version
- `port`: Host port mapping
- `container_name`: Docker container name
- `restart_policy`: Container restart behavior

### Authentication
- `anonymous_access_enabled`: Allow unauthenticated access
- `api_key_enabled`: Enable API key authentication
- `api_key_allowed_keys`: List of valid API keys
- `api_key_users`: List of associated users

### Persistence
- `data_path`: Data storage path inside container
- `volume_name`: Docker volume name for data persistence

### Modules
- `enabled`: List of Weaviate modules to enable
  - `text2vec-cohere`: Cohere text embeddings
  - `text2vec-huggingface`: Hugging Face text embeddings
  - `text2vec-palm`: Google PaLM text embeddings
  - `text2vec-openai`: OpenAI text embeddings
  - `generative-openai`: OpenAI text generation
  - `qna-openai`: OpenAI Q&A

### Health Checks
- `enabled`: Enable health checks
- `interval`: Check interval in seconds
- `timeout`: Check timeout in seconds
- `retries`: Number of retries
- `start_period`: Initial grace period in seconds

### Logging
- `level`: Log level (DEBUG, INFO, WARN, ERROR)
- `format`: Log format (text, json)

### Resources
- `memory_limit`: Memory limit (e.g., "512m", "1g")
- `cpu_limit`: CPU limit (e.g., "0.5", "1.0")

### Environment Variables
- `environment`: Additional custom environment variables

## Best Practices

1. **Development**: Use `config-development.yaml` for local work
2. **Testing**: Use `config-testing.yaml` for CI/CD
3. **Production**: Use `config-production.yaml` as a starting point
4. **Security**: Always use API keys in production
5. **Monitoring**: Use JSON logging in production for better monitoring
6. **Resources**: Adjust memory and CPU limits based on your workload
