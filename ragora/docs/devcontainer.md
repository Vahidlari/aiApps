# DevContainer Setup Guide

This guide provides detailed information about the DevContainer setup for Ragora development.

## 🚀 Quick Start with DevContainer

The easiest way to get started is using the development container:

### Prerequisites

- Install [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Install [VS Code](https://code.visualstudio.com/)
- Install the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) for VS Code

### Open in DevContainer

1. Clone this repository
2. Open the repository in VS Code
3. When prompted, click "Reopen in Container" or use `Ctrl+Shift+P` → "Dev Containers: Reopen in Container"

## 🐳 Docker Image Management

The development environment uses a custom Docker image hosted on GitHub Container Registry. The image includes:

- **Python 3.11** with all necessary development tools
- **Common AI/ML libraries** (numpy, pandas, scikit-learn, etc.)
- **RAG-specific packages** (langchain, chromadb, sentence-transformers)
- **Development tools** (black, flake8, isort, pytest)
- **Jupyter notebooks** support

### Building the Docker Image Locally

To update the Docker image:

```bash
cd tools/docker
./build-docker.sh -u
```

**Note:** The devContainer fetches the image from a GitHub registry, therefore, a local image build is normally not needed. In order to update the image, create a PR with changes in Dockerfile or Pipfile. A GitHub action is invoked to update the image. Once the image is updated, update the image tag in `.devcontainer/devcontainer.json`.

For detailed instructions, see [`tools/docker/README.md`](https://github.com/vahidlari/aiApps/blob/main/tools/docker/README.md).

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

## 🔄 Automatic Docker Builds

The repository includes GitHub Actions that automatically build and push the Docker image when changes are made to the Dockerfile. This ensures the devcontainer always uses the latest environment.

## 🐛 Troubleshooting

### DevContainer Issues

**Container won't start:**
```bash
# Check Docker is running
docker info

# Rebuild the container
Ctrl+Shift+P → "Dev Containers: Rebuild Container"
```

**Slow build times:**
- First-time builds can take 10-15 minutes
- Subsequent rebuilds are faster due to caching
- Consider using the pre-built image from GitHub Container Registry

**Permission issues:**
```bash
# On Linux/WSL, ensure user is in docker group
sudo usermod -aG docker $USER
# Log out and back in for changes to take effect
```

### Authentication Issues

If you encounter authentication errors when pulling the Docker image, see the [Authentication Setup](onboarding.md#authentication-setup) section in the onboarding guide.

## 🔧 Configuration

### DevContainer Configuration Location

The devcontainer configuration is located at `.devcontainer/devcontainer.json`.

### Customizing the Environment

To add VS Code extensions:
1. Edit `.devcontainer/devcontainer.json`
2. Add extension IDs to the `extensions` array
3. Rebuild the container

To add system packages:
1. Edit `tools/docker/Dockerfile`
2. Create a PR with your changes
3. GitHub Actions will build and publish the new image

To add Python packages:
1. Edit `tools/docker/Pipfile`
2. Create a PR with your changes
3. GitHub Actions will update the image

## 📝 Best Practices

- **Keep devcontainer.json minimal:** Most configuration should be in the Docker image
- **Version your image tags:** Use specific tags in production workflows
- **Test locally first:** Build and test Docker image changes locally before pushing
- **Document changes:** Update this guide when making significant environment changes

## 🔗 Related Documentation

- [Onboarding Guide](onboarding.md) - Getting started for new team members
- [Development Guide](development.md) - Development workflow and best practices
- [Docker Tools](https://github.com/vahidlari/aiApps/blob/main/tools/docker/README.md) - Docker image build scripts

