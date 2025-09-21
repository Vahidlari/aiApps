# Weaviate Server Manager

This directory contains tools to easily manage a local Weaviate server using Docker Compose.

## Files

- `docker-compose.yml` - Docker Compose configuration for Weaviate server
- `weaviate_manager.sh` - Bash script to manage the Weaviate server
- `README.md` - This documentation file

## Quick Start

1. **Start Weaviate server:**
   ```bash
   ./weaviate_manager.sh start
   ```

2. **Check if it's running:**
   ```bash
   ./weaviate_manager.sh status
   ```

3. **Stop the server:**
   ```bash
   ./weaviate_manager.sh stop
   ```

## Available Commands

| Command | Description |
|---------|-------------|
| `start` | Start the Weaviate server |
| `stop` | Stop the Weaviate server |
| `restart` | Restart the Weaviate server |
| `remove` | Remove the Weaviate server and all data |
| `status` | Show the current status |
| `logs` | Show the server logs (follow mode) |
| `help` | Show help message |

## Configuration

The Weaviate server is configured with:

- **Port**: 8080 (accessible at http://localhost:8080)
- **Authentication**: Disabled for development
- **Data Persistence**: Enabled with Docker volume
- **Health Checks**: Enabled
- **Auto-restart**: Unless manually stopped

## Prerequisites

- Docker Desktop installed and running
- Docker Compose (usually included with Docker Desktop)

## Troubleshooting

### Check Docker Status
Make sure Docker Desktop is running:
```bash
docker info
```

### View Logs
If the server fails to start, check the logs:
```bash
./weaviate_manager.sh logs
```

### Reset Everything
To completely remove Weaviate and start fresh:
```bash
./weaviate_manager.sh remove
./weaviate_manager.sh start
```

### Manual Verification
You can manually verify Weaviate is running:
```bash
curl http://localhost:8080/v1/.well-known/ready
```

Expected response: `{"ready": true}`

## Configuration Management

The Weaviate server supports flexible configuration through YAML files:

### Quick Setup
```bash
# Create default configuration
./weaviate_manager.sh config

# Use a pre-configured setup
cp examples/config-development.yaml config.yaml
```

### Configuration Examples
- `config-development.yaml` - For local development
- `config-production.yaml` - For production deployments  
- `config-testing.yaml` - For CI/CD and testing

### Key Configuration Options
- **Authentication**: Enable/disable anonymous access or API keys
- **Modules**: Choose which Weaviate modules to enable
- **Resources**: Set memory and CPU limits
- **Logging**: Configure log level and format
- **Ports**: Customize port mappings

See `examples/README.md` for detailed configuration documentation.

## API Key Authentication

For production deployments, you should enable API key authentication for security. Here's how to set it up:

### Step 1: Generate Secure API Keys

**Using OpenSSL (Recommended):**
```bash
# Generate a secure random API key
openssl rand -hex 32
# Example output: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2
```

**Using Python:**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### Step 2: Configure API Keys

1. **Copy the production configuration:**
   ```bash
   cp examples/config-production.yaml config.yaml
   ```

2. **Edit the configuration file:**
   ```bash
   nano config.yaml
   ```

3. **Update the API keys section:**
   ```yaml
   authentication:
     anonymous_access_enabled: false
     api_key_enabled: true
     api_key_allowed_keys:
       - "your-generated-admin-key-here"
       - "your-generated-readonly-key-here"
     api_key_users:
       - "admin@yourcompany.com"
       - "readonly@yourcompany.com"
   ```

### Step 3: Start Weaviate with API Keys

```bash
./weaviate_manager.sh start
```

### Step 4: Test Authentication

**Test without API key (should fail):**
```bash
curl http://localhost:8080/v1/.well-known/ready
# Expected: Authentication error
```

**Test with API key (should succeed):**
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" http://localhost:8080/v1/.well-known/ready
# Expected: {"ready": true}
```

### Using API Keys in Applications

**Python Example:**
```python
import weaviate

# Connect with API key
client = weaviate.Client(
    url="http://localhost:8080",
    auth_client_secret=weaviate.AuthApiKey(api_key="YOUR_API_KEY")
)

# Test connection
print("Connected:", client.is_ready())
```

**JavaScript/Node.js Example:**
```javascript
const weaviate = require('weaviate-ts-client');

const client = weaviate.client({
  scheme: 'http',
  host: 'localhost:8080',
  apiKey: new weaviate.ApiKey('YOUR_API_KEY')
});

// Test connection
client.misc.liveChecker().do()
  .then(() => console.log('Connected successfully'))
  .catch(err => console.error('Connection failed:', err));
```

**cURL Example:**
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"class": "Article", "vectorizer": "text2vec-openai"}' \
     http://localhost:8080/v1/schema
```

### Quick Setup Commands

```bash
# Generate API keys
ADMIN_KEY=$(openssl rand -hex 32)
READONLY_KEY=$(openssl rand -hex 32)

# Create config with your keys
cp examples/config-production.yaml config.yaml
sed -i "s/your-secure-api-key-here/$ADMIN_KEY/g" config.yaml
sed -i "s/backup-api-key-here/$READONLY_KEY/g" config.yaml

# Start Weaviate
./weaviate_manager.sh start

# Test connection
curl -H "Authorization: Bearer $ADMIN_KEY" http://localhost:8080/v1/.well-known/ready
```

### API Key Best Practices

1. **Generate Strong Keys**: Use at least 32 characters with random hex
2. **Use Different Keys**: Separate keys for admin, read-only, and service accounts
3. **Store Securely**: Never commit API keys to version control
4. **Rotate Regularly**: Change keys periodically for security
5. **Use Environment Variables**: Store keys in `.env` files or environment variables
6. **Monitor Usage**: Log API key usage for security monitoring

## Integration with RAG System

Once Weaviate is running, you can use it with the RAG system by connecting to:
- **URL**: `http://localhost:8080` (or your configured port)
- **Authentication**: Depends on your configuration (anonymous or API key)
