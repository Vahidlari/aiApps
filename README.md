# AI Models Practice Repository

This repository is designed for practicing AI models and implementing RAG (Retrieval-Augmented Generation) systems. It includes a complete development container setup for a consistent development environment.

## 🚀 Quick Start with DevContainer

The easiest way to get started is using the development container:

1. **Prerequisites:**
   - Install [Docker Desktop](https://www.docker.com/products/docker-desktop/)
   - Install [VS Code](https://code.visualstudio.com/)
   - Install the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) for VS Code

2. **Open in DevContainer:**
   - Clone this repository
   - Open the repository in VS Code
   - When prompted, click "Reopen in Container" or use `Ctrl+Shift+P` → "Dev Containers: Reopen in Container"

## 🐳 Docker Image Management

The development environment uses a custom Docker image hosted on GitHub Container Registry. The image includes:

- **Python 3.11** with all necessary development tools
- **Common AI/ML libraries** (numpy, pandas, scikit-learn, etc.)
- **RAG-specific packages** (langchain, chromadb, sentence-transformers)
- **Development tools** (black, flake8, isort, pytest)
- **Jupyter notebooks** support

### Building the Docker Image locally

To update the Docker image:

```bash
cd tools/docker
./build-docker.sh -u
```
Note: The devContainer fetches the image from a github registery, therefore, a local image build is normally not needed.
In order to update the image, create a PR with changes in dockerfile or Pipfile. A github action is envoked to update the image. 
Once the image is updated, update the image tag in .devcontainer/devcontainer.json

For detailed instructions, see [tools/docker/README.md](tools/docker/README.md).

## 📁 Project Structure

```
aiApps/
├── .devcontainer/                    # DevContainer configuration
│   └── devcontainer.json            # Container setup with Python 3.11 and AI/ML tools
├── .github/                          # GitHub automation and CI/CD
│   └── workflows/
│       ├── docker-build.yml         # Automated Docker image builds
│       └── update-dependencies.yml   # Dependency update automation
├── .vscode/                          # VS Code development configuration
│   ├── launch.json                   # Debug configurations
│   └── settings.json                 # Workspace settings
├── examples/                         # AI model examples and demonstrations
│   ├── __init__.py
│   ├── latex_loading_example.py     # LaTeX document loading example
│   ├── latex_retriever_example.py   # LaTeX RAG retrieval example
│   ├── latex_samples/               # Sample LaTeX documents for testing
│   │   ├── references.bib           # Bibliography file
│   │   └── sample_chapter.tex       # Sample LaTeX chapter
│   └── README.md                     # Examples documentation
├── ragnarock/                        # Main RAG system package
│   ├── __init__.py
│   ├── install_dev.py               # Development installation script
│   ├── pyproject.toml               # Package configuration
│   ├── pytest.ini                  # Test configuration
│   ├── requirements.txt             # Production dependencies
│   ├── requirements-dev.txt         # Development dependencies
│   ├── setup.py                     # Package setup
│   ├── ragnarock/                   # Core package modules
│   │   ├── __init__.py
│   │   ├── cli/                     # Command-line interface
│   │   │   ├── __init__.py
│   │   │   └── main.py              # CLI entry point
│   │   ├── config/                  # Configuration management
│   │   │   ├── __init__.py
│   │   │   ├── default_config.yaml  # Default configuration
│   │   │   └── settings.py          # Settings management
│   │   ├── core/                    # Core RAG system components
│   │   │   ├── __init__.py
│   │   │   ├── data_chunker.py      # Document chunking logic
│   │   │   ├── database_manager.py  # Weaviate database management
│   │   │   ├── document_preprocessor.py # LaTeX document processing
│   │   │   ├── embedding_engine.py  # Vector embedding generation
│   │   │   ├── rag_system.py        # Main RAG system orchestrator
│   │   │   ├── retriever.py         # Document retrieval logic
│   │   │   └── vector_store.py      # Vector storage operations
│   │   ├── examples/                # Usage examples
│   │   │   ├── __init__.py
│   │   │   ├── advanced_usage.py    # Advanced RAG usage examples
│   │   │   └── basic_usage.py       # Basic RAG usage examples
│   │   ├── utils/                   # Utility functions
│   │   │   ├── __init__.py
│   │   │   ├── device_utils.py      # Device detection utilities
│   │   │   └── latex_parser.py      # LaTeX parsing utilities
│   │   ├── exceptions.py            # Custom exceptions
│   │   └── version.py               # Version information
│   ├── tests/                       # Comprehensive test suite
│   │   ├── __init__.py
│   │   ├── conftest.py              # Pytest configuration
│   │   ├── fixtures/                # Test fixtures and sample data
│   │   │   ├── __init__.py
│   │   │   ├── expected_outputs/   # Expected test outputs
│   │   │   ├── sample_bibliography.bib # Sample bibliography
│   │   │   └── sample_latex.tex     # Sample LaTeX document
│   │   ├── integration/             # Integration tests
│   │   │   ├── __init__.py
│   │   │   ├── test_dbmng_retriever_vector_store.py
│   │   │   ├── test_document_parsing.py
│   │   │   ├── test_document_preprocessor.py
│   │   │   └── test_rag_pipeline.py
│   │   ├── unit/                    # Unit tests
│   │   │   ├── __init__.py
│   │   │   ├── test_config.py
│   │   │   ├── test_data_chunker.py
│   │   │   ├── test_database_manager.py
│   │   │   ├── test_document_preprocessor.py
│   │   │   ├── test_embedding_engine.py
│   │   │   ├── test_latex_parser.py
│   │   │   ├── test_rag_system.py
│   │   │   ├── test_retriever.py
│   │   │   └── test_vector_store.py
│   │   ├── utils/                   # Test utilities
│   │   │   ├── __init__.py
│   │   │   └── test_helpers.py      # Test helper functions
│   │   ├── run_tests.py             # Test runner script
│   │   └── README.md                # Testing documentation
│   └── README.md                    # RAG system documentation
├── tools/                           # Development and deployment tools
│   ├── docker/                      # Docker image management
│   │   ├── build-docker.sh          # Docker image build script
│   │   ├── Dockerfile               # Development environment Dockerfile
│   │   ├── env.template             # Environment variables template
│   │   ├── generate-lock.sh         # Dependency lock generation
│   │   ├── Pipfile                  # Python dependencies (Pipenv)
│   │   ├── Pipfile.lock             # Locked dependencies
│   │   └── README.md                # Docker management documentation
│   ├── database_server/             # Weaviate database server management
│   │   ├── config.yaml              # Database configuration
│   │   ├── database-manager.sh      # Database management script
│   │   ├── examples/                # Configuration examples
│   │   │   ├── config-development.yaml
│   │   │   ├── config-production.yaml
│   │   │   ├── config-testing.yaml
│   │   │   └── README.md
│   │   ├── scripts/                 # Helper scripts
│   │   │   ├── config-loader.sh
│   │   │   └── test-portable.sh
│   │   └── config/                  # Configuration templates
│   │       ├── config.yaml.template
│   │       ├── docker-compose.yml
│   │       ├── Dockerfile.management
│   │       └── user-config.yaml
│   └── scripts/                     # Utility scripts
│       ├── verify_test_setup.py     # Test environment verification
│       └── README.md                # Scripts documentation
└── README.md                        # This file
```

### 🎯 Key Components

- **`.github/workflows/`** - Automated CI/CD pipelines for Docker image builds and dependency updates
- **`.vscode/`** - VS Code workspace configuration for debugging and development settings
- **`examples/`** - LaTeX document processing examples and sample documents for testing RAG systems
- **`ragnarock/`** - Complete RAG (Retrieval-Augmented Generation) system package with LaTeX support, featuring:
  - Three-layer architecture (DatabaseManager, VectorStore, Retriever)
  - Weaviate integration for vector storage
  - Sentence Transformers for embeddings
  - Comprehensive test suite with unit and integration tests
- **`tools/docker/`** - Docker image management with automated builds and GitHub Container Registry integration
- **`tools/database_server/`** - Portable Weaviate database server management with zero external dependencies
- **`tools/scripts/`** - Utility scripts for test environment verification and development automation

## 🔧 Development Environment Features

The devcontainer includes:

- **Python 3.11** as the default interpreter
- **VS Code extensions** for Python development, Jupyter notebooks, and Docker
- **Code formatting** with Black and import sorting with isort
- **Linting** with flake8
- **Git integration** with GitHub CLI
- **Jupyter Lab** for interactive development

## 📦 Python Dependencies

The environment comes pre-installed with:

- **Core ML libraries:** numpy, pandas, matplotlib, seaborn, scikit-learn
- **Deep Learning:** PyTorch, Transformers, Datasets
- **RAG systems:** LangChain, ChromaDB, FAISS, Sentence Transformers
- **AI APIs:** OpenAI, Anthropic
- **Development tools:** Black, flake8, isort, pytest

## 🚀 Getting Started

1. **Open the repository in VS Code with DevContainer**
2. **Install additional dependencies** (if needed):
   ```bash
   pip install -r requirements.txt
   ```
3. **Start coding!** The environment is ready for AI model development

## 👥 Team Onboarding Guide

Welcome to the AI Apps team! This guide will help you get up and running quickly with our development environment.

### 🎯 Quick Start (5 minutes)

1. **Prerequisites Check:**
   - [ ] Docker Desktop installed and running
   - [ ] VS Code installed
   - [ ] Dev Containers extension installed in VS Code
   - [ ] GitHub account with repository access

2. **Authentication Setup (if needed):**
   - [ ] GitHub account added as collaborator to the repository
   - [ ] If Docker image is private, you may need a Personal Access Token (see below)

2. **Clone and Open:**
   ```bash
   git clone https://github.com/vahidlari/aiapps.git
   cd aiapps
   code .
   ```

3. **Open in DevContainer:**
   - When prompted, click "Reopen in Container"
   - Or use `Ctrl+Shift+P` → "Dev Containers: Reopen in Container"
   - Wait for the container to build (first time takes 5-10 minutes)

4. **Verify Setup:**
   ```bash
   # Check Python environment
   python --version  # Should show Python 3.11
   
   # Check if RAGnaROCK package is installed
   python -c "import ragnarock; print('✅ RAGnaROCK installed successfully')"
   ```

### 🔐 Authentication Setup

#### Repository Access
- **Repository**: The repository should be accessible to you as a collaborator
- **No additional setup needed** for public repositories
- **For private repositories**: Ensure you're added as a collaborator with appropriate permissions

#### Docker Image Access
The DevContainer uses a Docker image from GitHub Container Registry. You may need authentication if the image is private:

1. **Create a Personal Access Token:**
   - Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
   - Click "Generate new token (classic)"
   - Select scopes: `read:packages`
   - Copy the token (you won't see it again!)

2. **Authenticate Docker with GitHub:**
   ```bash
   # Login to GitHub Container Registry
   echo "YOUR_PAT_TOKEN" | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin
   ```

3. **Alternative: Configure VS Code to use GitHub token:**
   - In VS Code, go to Settings → Extensions → Dev Containers
   - Add your GitHub token to the settings
   - Or set environment variable: `GITHUB_TOKEN=your_token_here`

**Troubleshooting Authentication:**
```bash
# Test if you can pull the image manually
docker pull ghcr.io/vahidlari/aiapps/ai-dev:main-33e9578

# If this fails with authentication error, you need the PAT setup above
```

### 🧪 Running Examples

#### LaTeX Document Processing and vectorization on a RAG  
```bash
# Navigate to examples directory
cd examples

# Run LaTeX loading example
python latex_loading_example.py

# Run LaTeX retrieval example
python latex_retriever_example.py
```

Note: You may need to update the url for the Weaviate server, based on your own setup. 
The current implementation assumes that you are running the code in a devcontainer and a server is running 
outside of the devcontainer. 

### 🧪 Running Tests

#### Run Test Suites
```bash
# Navigate to RAGnaROCK directory
cd ragnarock

# Run all tests
python -m pytest

# Run specific test categories
python -m pytest tests/unit/          # Unit tests only
python -m pytest tests/integration/  # Integration tests only

# Run with verbose output
python -m pytest -v

# Run specific test file
python -m pytest tests/unit/test_rag_system.py
```

#### Test Coverage
```bash
# Install coverage tools (if not already installed)
pip install pytest-cov

# Run tests with coverage
python -m pytest --cov=ragnarock --cov-report=html

# View coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### 🗄️ Database Setup (Optional)

If you want to work with the full RAG system:

```bash
# Navigate to database tools
cd tools/database_server

# Start Weaviate database server
./database-manager.sh start

# Check if it's running
./database-manager.sh status

# Stop when done
./database-manager.sh stop
```

### 🔧 Development Workflow

#### Code Quality Tools
The environment comes pre-configured with:
- **Black** for code formatting (auto-runs on save)
- **Flake8** for linting
- **isort** for import sorting

#### Git Workflow
```bash
# Create a new branch for your work
git checkout -b feature/your-feature-name

# Make your changes, commit them
git add .
git commit -m "feat: add your feature description"

# Push to GitHub
git push origin feature/your-feature-name

# Create a Pull Request on GitHub
```

#### Adding Dependencies
```bash
# For RAGnaROCK package dependencies
cd ragnarock
pip install your-new-package
pip freeze > requirements.txt

# For development environment dependencies
cd tools/docker
# Edit Pipfile to add new packages
# The GitHub Actions will automatically update the Docker image
```

### 🐛 Troubleshooting

#### Common Issues

**DevContainer won't start:**
```bash
# Check Docker is running
docker info

# Rebuild the container
Ctrl+Shift+P → "Dev Containers: Rebuild Container"
```

**Authentication errors when opening DevContainer:**
```bash
# Test Docker image access
docker pull ghcr.io/vahidlari/aiapps/ai-dev:main-33e9578

# If authentication fails, set up Personal Access Token (see Authentication Setup section)
echo "YOUR_PAT_TOKEN" | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin
```

**Tests failing:**
```bash
# Verify test setup
python tools/scripts/verify_test_setup.py

# Check if all dependencies are installed
cd ragnarock
pip install -e .
```

**Database connection issues:**
```bash
# Check if Weaviate is running
cd tools/database_server
./database-manager.sh status

# Restart if needed
./database-manager.sh restart
```

**Import errors:**
```bash
# Ensure RAGnaROCK is installed in development mode
cd ragnarock
pip install -e .
```

### 📚 Learning Resources

#### Understanding the Codebase
1. **Start with Examples:** Run the examples in `examples/` directory
2. **Read RAGnaROCK Docs:** Check `ragnarock/README.md` for detailed system architecture
3. **Explore Tests:** Look at `ragnarock/tests/` to understand expected behavior

#### Key Concepts
- **RAG System:** Retrieval-Augmented Generation for LaTeX documents
- **Three-Layer Architecture:** DatabaseManager → VectorStore → Retriever
- **Weaviate Integration:** Vector database for document storage
- **LaTeX Processing:** Specialized document preprocessing for academic papers

### 🆘 Getting Help

- **Documentation:** Check the README files in each directory
- **Issues:** Create GitHub issues for bugs or questions
- **Code Review:** All changes go through Pull Request review process
- **Team Chat:** Use your team's communication channels for quick questions

### ✅ Onboarding Checklist

- [ ] DevContainer opens successfully
- [ ] Python 3.11 environment is active
- [ ] RAGnaROCK package imports without errors
- [ ] Examples run successfully
- [ ] Tests pass (at least the basic ones)
- [ ] Git is configured with your name and email
- [ ] You can create and push branches
- [ ] You understand the project structure

**🎉 Welcome to the team! You're ready to start contributing to the AI Apps project.**

## 🔄 Automatic Docker Builds

The repository includes GitHub Actions that automatically build and push the Docker image when changes are made to the Dockerfile. This ensures the devcontainer always uses the latest environment.

## 📝 Next Steps

- Create your AI model implementations in the repository
- Add RAG system examples
- Use Jupyter notebooks for experimentation
- Leverage the pre-configured development tools for code quality

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Ensure code quality with the pre-configured tools
5. Submit a pull request

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
