# Development Guide

This guide covers development workflows, coding standards, and best practices for contributing to Ragora.

## 🔧 Development Workflow

### Setting Up Your Development Environment

1. **Clone the repository** and open in DevContainer (see [devcontainer.md](devcontainer.md))
2. **Install Ragora in development mode:**
   ```bash
   cd ragora
   pip install -e .
   ```
3. **Verify installation:**
   ```bash
   python -c "import ragora; print('✅ Ragora installed successfully')"
   ```

### Branch Strategy

We follow a feature branch workflow:

```bash
# Create a new branch for your work
git checkout -b feature/your-feature-name

# Make your changes and commit
git add .
git commit -m "feat: add your feature description"

# Push to GitHub
git push origin feature/your-feature-name

# Create a Pull Request on GitHub
```

### Commit Message Convention

We use [Conventional Commits](https://www.conventionalcommits.org/) for automatic versioning:

```bash
# Feature (minor version bump)
git commit -m "feat: add user authentication"

# Bug fix (patch version bump)
git commit -m "fix: resolve login timeout issue"

# Breaking change (major version bump)
git commit -m "feat!: redesign API endpoints"

# Other types (patch version bump)
git commit -m "docs: update installation guide"
git commit -m "test: add unit tests for auth module"
git commit -m "refactor: simplify API structure"
```

For detailed information, see [release.md](release.md).

## 🎨 Code Quality Standards

### Formatting and Linting

The project uses automated code quality tools:

- **Black** - Code formatting (runs on save in VS Code)
- **isort** - Import sorting
- **Flake8** - Linting

Run manually if needed:
```bash
# Format code with Black
black ragora/

# Sort imports
isort ragora/

# Check linting
flake8 ragora/
```

### Type Hints

Use type hints for all function signatures:

```python
from typing import List, Dict, Optional

def process_documents(
    documents: List[str],
    chunk_size: int = 768,
    overlap: Optional[int] = None
) -> Dict[str, any]:
    """Process documents and return results."""
    pass
```

### Docstrings

Use Google-style docstrings for all public functions and classes:

```python
def search_similar(query: str, top_k: int = 5) -> List[Dict]:
    """Search for similar documents using vector similarity.
    
    Args:
        query: The search query string
        top_k: Number of results to return
        
    Returns:
        List of dictionaries containing search results with scores
        
    Raises:
        ValueError: If query is empty or top_k is negative
        
    Example:
        >>> results = search_similar("machine learning", top_k=3)
        >>> print(len(results))
        3
    """
    pass
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
cd ragora
python -m pytest

# Run specific test types
python -m pytest tests/unit/          # Unit tests only
python -m pytest tests/integration/  # Integration tests only

# Run with coverage
python -m pytest --cov=ragora --cov-report=html
```

### Writing Tests

Place tests in the appropriate directory:
- `tests/unit/` - Unit tests for individual components
- `tests/integration/` - Integration tests for component interactions

Example test:
```python
import pytest
from ragora.core import DataChunker

def test_chunker_basic():
    """Test basic chunking functionality."""
    chunker = DataChunker()
    context = ChunkingContextBuilder().for_text().build()
    text = "This is a test document. " * 50
    chunks = chunker.chunk(text, context)
    
    assert len(chunks) > 0
    assert all(isinstance(chunk, DataChunk) for chunk in chunks)
```

For more details, see [testing.md](testing.md).

## 📦 Managing Dependencies

### Adding Python Dependencies

#### For Ragora Package

Add to `ragora/requirements.txt` for production dependencies:
```bash
cd ragora
echo "new-package>=1.0.0" >> requirements.txt
pip install -r requirements.txt
```

Add to `ragora/requirements-dev.txt` for development dependencies:
```bash
echo "dev-tool>=2.0.0" >> requirements-dev.txt
pip install -r requirements-dev.txt
```

#### For Development Environment

To add packages to the DevContainer image:
1. Edit `tools/docker/Pipfile`
2. Add the package: `new-package = ">=1.0.0"`
3. Create a PR with your changes
4. GitHub Actions will automatically build and publish the updated image

### Updating Dependencies

```bash
# Update specific package
pip install --upgrade package-name

# Regenerate requirements
pip freeze > requirements.txt

# For dev dependencies
pip freeze > requirements-dev.txt
```

## 🏗️ Project Structure

### Package Organization

```
ragora/
├── core/              # Core RAG components
│   ├── database_manager.py
│   ├── vector_store.py
│   └── retriever.py
├── utils/             # Utility functions
├── config/            # Configuration management
├── cli/               # Command-line interface
└── examples/          # Usage examples
```

### Adding New Modules

1. Create the module file in the appropriate directory
2. Add comprehensive docstrings and type hints
3. Write unit tests
4. Update relevant documentation
5. Add usage examples if applicable

## 🔍 Code Review Guidelines

### Before Submitting a PR

- [ ] All tests pass locally
- [ ] Code is formatted with Black
- [ ] Imports are sorted with isort
- [ ] No linting errors from Flake8
- [ ] Type hints are present
- [ ] Docstrings are complete
- [ ] Tests are added for new features
- [ ] Documentation is updated

### PR Template

When creating a PR, include:
- **Description:** What does this PR do?
- **Motivation:** Why is this change needed?
- **Testing:** How was this tested?
- **Related Issues:** Links to related issues

## 🐛 Debugging

### Using VS Code Debugger

The devcontainer includes debug configurations. To debug:
1. Set breakpoints in your code
2. Press F5 or use the Debug panel
3. Select the appropriate debug configuration

### Common Debug Configurations

- **Python: Current File** - Debug the currently open file
- **Python: pytest** - Debug tests
- **Python: Remote Attach** - Attach to running process

### Logging

Use Python's logging module for debugging:

```python
import logging

logger = logging.getLogger(__name__)

def process_data(data):
    logger.debug(f"Processing data: {data}")
    logger.info("Processing completed")
    logger.warning("Performance may be slow")
    logger.error("Failed to process data")
```

## 📊 Performance Profiling

### Profiling Code

```python
import cProfile
import pstats

def profile_function():
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Your code here
    
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)
```

### Memory Profiling

```bash
# Install memory profiler
pip install memory-profiler

# Run with memory profiling
python -m memory_profiler your_script.py
```

## 🔗 Related Documentation

- [Onboarding Guide](onboarding.md) - Getting started for new team members
- [DevContainer Guide](devcontainer.md) - Development environment setup
- [Release Process](release.md) - How to create releases
- [Contributing Guide](contributing.md) - Contribution guidelines

## 🆘 Getting Help

- **Documentation:** Check the docs in each directory
- **Issues:** Create GitHub issues for bugs or questions
- **Discussions:** Use GitHub Discussions for general questions
- **Code Review:** Request reviews from team members

