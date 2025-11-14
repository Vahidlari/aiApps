# Ragora Development Repository

This repository hosts the development of **Ragora**, an open-source RAG (Retrieval-Augmented Generation) library for Python, along with examples and use cases demonstrating its capabilities.

## 🎯 What is Ragora?

Ragora is a framework for building RAG systems that connect language models to real, reliable knowledge. It provides clean, composable interfaces for managing knowledge bases, document retrieval, and grounding pipelines. The name blends "RAG" with the ancient Greek "Agora", the public square where ideas were exchanged and refined.

**Key Features:**
- 🏗️ Clean three-layer architecture for flexibility
- 🔍 Multiple search modes: vector, keyword, and hybrid
- 🧩 Composable components for custom pipelines
- ⚡ Performance-optimized with batch processing and GPU support
- 📄 Utilities to process different types of documents


## 🚀 Quick Start

### For Users

Install Ragora from PyPI:

```bash
pip install ragora
```

See the [Ragora README](ragora/README.md) for installation and usage guide.

### For Contributors

Set up the development environment:

```bash
# Clone the repository
git clone https://github.com/vahidlari/ragora-core.git
cd aiapps

# Open in DevContainer (recommended)
code .
# Click "Reopen in Container" when prompted
```

See [docs/onboarding.md](docs/onboarding.md) for detailed setup instructions.

## 📁 Repository Structure

```
aiApps/
├── ragora/                    # Main Ragora package
│   ├── ragora/               # Source code
│   ├── tests/                # Test suite
│   ├── docs/                 # Package documentation
│   └── README.md             # Package overview (PyPI)
├── examples/                  # Usage examples
│   ├── latex_loading_example.py
│   ├── latex_retriever_example.py
│   └── README.md             # Examples guide
├── tools/                     # Development tools
│   ├── docker/               # Docker image management
│   ├── database_server/      # Weaviate server setup
│   └── scripts/              # Utility scripts
├── docs/                      # Repository documentation
│   ├── onboarding.md         # Team onboarding guide
│   ├── devcontainer.md       # DevContainer setup
│   ├── development.md        # Development workflow
│   └── release.md            # Release process
└── README.md                  # This file
```

## 🐳 Development Environment

### Using DevContainer (Recommended)

The easiest way to get started:

1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop/)
2. Install [VS Code](https://code.visualstudio.com/) with [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
3. Open the repository in VS Code
4. Click "Reopen in Container"

The DevContainer includes:
- Python 3.11 with all development tools
- AI/ML libraries (PyTorch, Transformers, Sentence Transformers)
- Code quality tools (Black, Flake8, isort, pytest)
- Jupyter Lab for interactive development

See [docs/devcontainer.md](docs/devcontainer.md) for details.

### Docker Images

Pre-built Docker images are available from GitHub Container Registry. See [tools/docker/README.md](tools/docker/README.md) for building and managing images.

### Database Setup

Ragora uses Weaviate as its vector database. For users, download the pre-configured database server from releases:

```bash
# Download from GitHub releases
wget https://github.com/vahidlari/ragora-core/releases/latest/download/ragora-database-server.tar.gz
tar -xzf ragora-database-server.tar.gz
cd ragora-database-server
./database-manager.sh start
```

**For contributors:** Use the database server from this repository:
```bash
cd tools/database_server
./database-manager.sh start
```

See [tools/database_server/README.md](tools/database_server/README.md) for details.

## 🧪 Running Examples

```bash
# Navigate to examples
cd examples

# Run LaTeX document loading
python latex_loading_example.py

# Run document retrieval
python latex_retriever_example.py
```

**Note:** Examples assume Weaviate is running running in DevContainer with Weaviate on the host, update the URL to `http://host.docker.internal:8080`. Alternatively, you may run it natively on your host machine, at `http://localhost:8080`.

See [examples/README.md](examples/README.md) for detailed examples documentation.

## 🧪 Running Tests

```bash
# Navigate to Ragora package
cd ragora

# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=ragora --cov-report=html

# Run specific test types
python -m pytest tests/unit/          # Unit tests
python -m pytest tests/integration/  # Integration tests
```

See [ragora/docs/testing.md](ragora/docs/testing.md) for testing guidelines.

## 📚 Documentation

### Repository Documentation

- **[onboarding.md](docs/onboarding.md)** - Getting started for new team members
- **[devcontainer.md](docs/devcontainer.md)** - DevContainer setup and Docker image management
- **[development.md](docs/development.md)** - Development workflow and best practices
- **[release.md](docs/release.md)** - Release process and versioning

### Ragora Package Documentation

- **[Getting Started](ragora/docs/getting_started.md)** - Installation and setup
- **[Architecture](ragora/docs/architecture.md)** - System design and components
- **[Design Decisions](ragora/docs/design_decisions.md)** - Design rationale
- **[API Reference](ragora/docs/api-reference.md)** - Complete API documentation
- **[Deployment](ragora/docs/deployment.md)** - Production deployment guide
- **[Testing](ragora/docs/testing.md)** - Testing strategy and guidelines
- **[Contributing](ragora/docs/contributing.md)** - How to contribute

### Tools Documentation

- **[Docker Tools](tools/docker/README.md)** - Building and managing Docker images
- **[Database Server](tools/database_server/README.md)** - Weaviate setup and management
- **[Scripts](tools/scripts/README.md)** - Utility scripts

## 🤝 Contributing

We welcome contributions! Please see:

1. **[onboarding.md](docs/onboarding.md)** - Set up your development environment
2. **[development.md](docs/development.md)** - Learn the development workflow
3. **[ragora/docs/contributing.md](ragora/docs/contributing.md)** - Contribution guidelines
4. **[release.md](docs/release.md)** - Understanding releases

### Quick Contribution Guide

```bash
# Create a feature branch
git checkout -b feature/your-feature

# Make your changes following coding standards
# Run tests and ensure they pass
python -m pytest

# Commit using conventional commit format
git commit -m "feat: add your feature description"

# Push and create a pull request
git push origin feature/your-feature
```

## 🔄 Release Process

Ragora uses milestone-driven releases with automatic versioning based on conventional commits. See [docs/release.md](docs/release.md) for details.

## 📦 Publishing

The Ragora package is published to:
- **PyPI**: `pip install ragora`
- **GitHub Packages**: Available through GitHub Package Registry

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](ragora/LICENSE) file for details.

## 🔗 Links

- **PyPI Package**: [pypi.org/project/ragora](https://pypi.org/project/ragora) (coming soon)
- **GitHub Repository**: [github.com/vahidlari/ragora-core](https://github.com/vahidlari/ragora-core)
- **Issues**: [GitHub Issues](https://github.com/vahidlari/ragora-core/issues)
- **Discussions**: [GitHub Discussions](https://github.com/vahidlari/ragora-core/discussions)

## 🆘 Getting Help

- **Documentation**: Browse the docs in this repository
- **Issues**: Report bugs or request features
- **Discussions**: Ask questions and share ideas
- **Examples**: Check the examples directory for practical usage

---

**Build smarter, grounded, and transparent AI with Ragora.**
