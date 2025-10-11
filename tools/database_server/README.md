# Database Server Manager

A portable, easy-to-use Weaviate server management solution that only requires Docker. Perfect for development, testing, and production environments.

## 🚀 Quick Start

**Only requires Docker - works everywhere!**

```bash
# Start Weaviate server
./database-manager.sh start

# Check if it's running
./database-manager.sh status

# Stop the server
./database-manager.sh stop
```

## ✨ Key Features

- **🔧 Zero Dependencies**: Only requires Docker - no `yq`, `jq`, `curl` needed
- **🌍 Universal Compatibility**: Works on Windows, WSL, macOS, and Linux
- **📦 Self-Contained**: All tools included in Docker container
- **⚡ Easy Setup**: No complex installation or configuration
- **🔄 Portable**: Copy the directory and it works anywhere

## 📋 Available Commands

The `database-manager.sh` script provides the following commands:

| Command | Description |
|---------|-------------|
| `start` | Start the Weaviate server and transformers API |
| `stop` | Stop the Weaviate server and transformers API |
| `restart` | Restart the Weaviate server and transformers API |
| `remove` | Remove the Weaviate server and all data |
| `status` | Show the current status of all services |
| `logs` | Show the server logs (follow mode) |
| `config` | Create or show configuration file |
| `info` | Show system information |
| `help` | Show help message |

## 🏗️ Services Managed

This solution manages a complete Weaviate setup with the following services:

### Weaviate Server
- **Container**: `weaviate`
- **Port**: 8080 (configurable)
- **Features**: Vector database with multiple embedding modules
- **Modules**: text2vec-transformers, text2vec-cohere, text2vec-huggingface, text2vec-palm, text2vec-openai, generative-openai, qna-openai

### Transformers Inference API
- **Container**: `t2v-transformers`
- **Port**: 8081 (configurable)
- **Model**: sentence-transformers-multi-qa-MiniLM-L6-cos-v1
- **Purpose**: Provides local text embedding capabilities

### Management Container
- **Container**: `database-management`
- **Purpose**: Handles all management operations without requiring external tools

## 🛠️ Installation & Setup

### Prerequisites
- **Docker Desktop** (Windows/macOS) or **Docker Engine** (Linux)
- That's it! No other dependencies required.

### Setup Steps

1. **Clone or download this directory**
2. **Make scripts executable** (if needed):
   ```bash
   chmod +x database-manager.sh
   ```
3. **Start Weaviate**:
   ```bash
   ./database-manager.sh start
   ```

## 🎯 Perfect For

### Windows Development
- **Windows 10/11** with Docker Desktop
- **WSL (Windows Subsystem for Linux)** environments
- **Git Bash** or **PowerShell** terminals

### Cross-Platform Development
- **macOS** with Docker Desktop
- **Linux** with Docker Engine
- **CI/CD pipelines** (GitHub Actions, GitLab CI, etc.)

### Team Collaboration
- **Consistent environment** across all team members
- **No dependency conflicts** between different systems
- **Easy onboarding** for new team members

## 🚀 Usage Examples

### Basic Operations
```bash
# Start Weaviate
./database-manager.sh start

# Check if it's running
./database-manager.sh status

# View logs
./database-manager.sh logs

# Stop Weaviate
./database-manager.sh stop
```

### Configuration Management
```bash
# Create default configuration
./database-manager.sh config

# Use a pre-configured setup
cp examples/config-development.yaml config.yaml
./database-manager.sh start
```

### Development Workflow
```bash
# Start development environment
./database-manager.sh start

# Check status
./database-manager.sh status

# View logs if issues
./database-manager.sh logs

# Restart if needed
./database-manager.sh restart

# Clean up when done
./database-manager.sh remove
```

## 🔍 Troubleshooting

### Docker Not Running
```bash
# Check Docker status
docker info

# Start Docker Desktop (Windows/macOS)
# Or start Docker daemon (Linux)
sudo systemctl start docker
```

### Permission Issues (Linux/WSL)
```bash
# Add user to docker group
sudo usermod -aG docker $USER
# Log out and back in
```

### Port Already in Use
```bash
# Check what's using port 8080
netstat -tulpn | grep :8080

# Stop conflicting service or change port in config.yaml
```

### Management Image Issues
```bash
# Rebuild management image
docker rmi database-management:latest
./database-manager.sh start
```

## 🔧 Configuration

### Quick Configuration
```bash
# Create default config
./database-manager.sh config

# Edit configuration
nano config.yaml

# Restart with new config
./database-manager.sh restart
```

### Configuration Examples
- `examples/config-development.yaml` - Development settings
- `examples/config-production.yaml` - Production settings
- `examples/config-testing.yaml` - Testing/CI settings

### Key Configuration Options
- **Port**: Change Weaviate port (default: 8080)
- **Authentication**: Enable/disable API keys
- **Modules**: Choose which Weaviate modules to enable
- **Resources**: Set memory and CPU limits
- **Logging**: Configure log level and format

## 🚀 Advanced Usage

### Custom Management
```bash
# Run management commands directly in container
docker run --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v $(pwd):/app \
  -w /app \
  database-management:latest \
  status
```

### Multiple Environments
```bash
# Development
cp examples/config-development.yaml config.yaml
./database-manager.sh start

# Production
cp examples/config-production.yaml config.yaml
./database-manager.sh start
```

### CI/CD Integration
```yaml
# GitHub Actions example
- name: Start Weaviate
  run: |
    chmod +x database-manager.sh
    ./database-manager.sh start
    ./database-manager.sh status
```

## 🔄 Migration from Original Script

If you're currently using the original `weaviate_manager.sh`:

1. **Backup your config**: `cp config.yaml config.yaml.backup`
2. **Switch to portable**: Use `database-manager.sh` instead
3. **Same commands**: All commands work the same way
4. **No data loss**: Your data and configuration are preserved

## 🆚 Comparison

| Feature | Original Script | Database Management Script |
|---------|----------------|----------------------------|
| Dependencies | yq, jq, curl, docker | Docker only |
| Windows Support | Limited (WSL required) | Full support |
| WSL Support | Yes | Yes |
| macOS Support | Yes | Yes |
| Linux Support | Yes | Yes |
| CI/CD Friendly | Limited | Excellent |
| Setup Complexity | High | Low |
| Portability | Limited | Excellent |

## 📁 Directory Structure

```
database_server/
├── database-manager.sh        # 🚀 Main database management script (USE THIS)
├── config.yaml                   # Your configuration file
├── examples/                     # Configuration examples
│   ├── config-development.yaml
│   ├── config-production.yaml
│   └── config-testing.yaml
├── scripts/                      # Helper scripts (internal)
│   ├── config-loader.sh
│   └── test-portable.sh
└── config/                       # Configuration templates (internal)
    ├── docker-compose.yml
    ├── Dockerfile.management
    ├── config.yaml.template
    └── user-config.yaml
```

## 🔧 How It Works

The portable solution uses a **containerized management approach**:

1. **Management Container**: Contains all required tools (`yq`, `jq`, `curl`, `docker-compose`)
2. **Docker-in-Docker**: Management container controls Docker daemon via socket mounting
3. **Volume Mounting**: Configuration and data persist on host system
4. **Self-Building**: Automatically builds management image when needed
5. **Multi-Service Setup**: Manages both Weaviate server and transformers inference API

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**
3. **Make your changes**
4. **Test on multiple platforms**
5. **Submit a pull request**

## 📝 License

This project is part of the Ragora AI system. See the main project for license information.

## 🆘 Support

- **Issues**: Create an issue in the repository
- **Documentation**: Check this README and examples
- **Community**: Join the project discussions

---

**🎉 Enjoy your portable Database server! No more dependency headaches!**