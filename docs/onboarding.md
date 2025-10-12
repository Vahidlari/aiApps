# Team Onboarding Guide

Welcome to the Ragora development team! This guide will help you get up and running quickly with our development environment.

## 🎯 Quick Start (5 minutes)

### Prerequisites Check

- [ ] Docker Desktop installed and running
- [ ] VS Code installed
- [ ] Dev Containers extension installed in VS Code
- [ ] GitHub account with repository access

### Authentication Setup (if needed)

- [ ] GitHub account added as collaborator to the repository
- [ ] If Docker image is private, you may need a Personal Access Token (see below)

### Clone and Open

```bash
git clone https://github.com/vahidlari/aiapps.git
cd aiapps
code .
```

### Open in DevContainer

- When prompted, click "Reopen in Container"
- Or use `Ctrl+Shift+P` → "Dev Containers: Reopen in Container"
- Wait for the container to build (first time takes 5-10 minutes)

### Verify Setup

```bash
# Check Python environment
python --version  # Should show Python 3.11

# Check if Ragora package is installed
python -c "import ragora; print('✅ Ragora installed successfully')"
```

## 🔐 Authentication Setup

### Repository Access

- **Repository**: The repository should be accessible to you as a collaborator
- **No additional setup needed** for public repositories
- **For private repositories**: Ensure you're added as a collaborator with appropriate permissions

### Docker Image Access

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

## 🧪 Running Examples

### LaTeX Document Processing and Vectorization

```bash
# Navigate to examples
cd examples

# Run LaTeX loading example
python latex_loading_example.py

# Run LaTeX retrieval example
python latex_retriever_example.py
```

**Note:** You may need to update the URL for the Weaviate server, based on your own setup. The current implementation assumes that you are running the code in a devcontainer and a server is running outside of the devcontainer.

## 🧪 Running Tests

### Run Test Suites

```bash
# Navigate to Ragora directory
cd ragora

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

### Test Coverage

```bash
# Install coverage tools (if not already installed)
pip install pytest-cov

# Run tests with coverage
python -m pytest --cov=ragora --cov-report=html

# View coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## 🗄️ Database Setup (Optional)

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

For more details, see [`tools/database_server/README.md`](../tools/database_server/README.md).

## 🔧 Development Workflow

### Code Quality Tools

The environment comes pre-configured with:
- **Black** for code formatting (auto-runs on save)
- **Flake8** for linting
- **isort** for import sorting

### Git Workflow

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

For commit message guidelines, see [`docs/release.md`](release.md).

### Adding Dependencies

```bash
# For Ragora package dependencies
cd ragora
pip install your-new-package
pip freeze > requirements.txt

# For development environment dependencies
cd tools/docker
# Edit Pipfile to add new packages
# The GitHub Actions will automatically update the Docker image
```

For more details, see [`docs/development.md`](development.md).

## 🐛 Troubleshooting

### Common Issues

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
cd ragora
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
# Ensure Ragora is installed in development mode
cd ragora
pip install -e .
```

## 📚 Learning Resources

### Understanding the Codebase

1. **Start with Examples:** Run the examples in [`examples/`](../examples/) directory
2. **Read Ragora Docs:** Check [`ragora/docs/`](../ragora/docs/) for detailed system architecture
3. **Explore Tests:** Look at [`ragora/tests/`](../ragora/tests/) to understand expected behavior

### Key Concepts

- **RAG System:** Retrieval-Augmented Generation for LaTeX documents
- **Three-Layer Architecture:** DatabaseManager → VectorStore → Retriever
- **Weaviate Integration:** Vector database for document storage
- **LaTeX Processing:** Specialized document preprocessing for academic papers

## 🆘 Getting Help

- **Documentation:** Check the README files in each directory
- **Issues:** Create GitHub issues for bugs or questions
- **Code Review:** All changes go through Pull Request review process
- **Team Chat:** Use your team's communication channels for quick questions

## ✅ Onboarding Checklist

- [ ] DevContainer opens successfully
- [ ] Python 3.11 environment is active
- [ ] Ragora package imports without errors
- [ ] Examples run successfully
- [ ] Tests pass (at least the basic ones)
- [ ] Git is configured with your name and email
- [ ] You can create and push branches
- [ ] You understand the project structure

**🎉 Welcome to the team! You're ready to start contributing to Ragora.**