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

### Building and Pushing the Docker Image

To update the Docker image:

```bash
cd tools/docker
./build-docker.sh -u -p
```

For detailed instructions, see [tools/docker/README.md](tools/docker/README.md).

## 📁 Project Structure

```
aiApps/
├── .devcontainer/          # DevContainer configuration
├── tools/
│   └── docker/            # Docker image build scripts
│   ├── Pipfile            # Python dependencies
│   ├── Pipfile.locks
└── README.md              # This file
```

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
