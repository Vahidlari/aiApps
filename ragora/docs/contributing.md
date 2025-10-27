# Contributing to Ragora

Thank you for your interest in contributing to Ragora! This document provides guidelines and instructions for contributing to the project.

## 🤝 How to Contribute

### Ways to Contribute

- **Report Bugs**: Submit detailed bug reports
- **Suggest Features**: Propose new features or improvements
- **Improve Documentation**: Fix typos, clarify instructions, add examples
- **Write Code**: Fix bugs, implement features, improve performance
- **Review Pull Requests**: Help review and test PRs
- **Answer Questions**: Help other users in Issues and Discussions

## 🚀 Getting Started

### 1. Set Up Development Environment

```bash
# Fork and clone the repository
git clone https://github.com/vahidlari/aiapps.git
cd aiapps

# Open in DevContainer (recommended)
code .
# Click "Reopen in Container"

# Or set up locally
pip install -e "ragora[dev]"

# Start Weaviate database
cd tools/database_server
./database-manager.sh start
```

### 2. Create a Branch

```bash
# Create a new branch for your work
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b fix/bug-description
```

### 3. Make Your Changes

Follow our coding standards (see below) and make your changes.

### 4. Test Your Changes

```bash
# Run all tests
cd ragora
python -m pytest

# Run specific tests
python -m pytest tests/unit/test_your_module.py

# Check test coverage
python -m pytest --cov=ragora --cov-report=html
```

### 5. Submit a Pull Request

```bash
# Commit your changes
git add .
git commit -m "feat: add your feature description"

# Push to your fork
git push origin feature/your-feature-name

# Create a Pull Request on GitHub
```

## 📝 Coding Standards

### Python Style Guide

We follow [PEP 8](https://pep8.org/) with the following tools:

**Black** - Code formatting
```bash
black ragora/
```

**isort** - Import sorting
```bash
isort ragora/
```

**Flake8** - Linting
```bash
flake8 ragora/
```

### Type Hints

Always use type hints for function signatures:

```python
from typing import List, Dict, Optional

def process_documents(
    documents: List[str],
    chunk_size: int = 768,
    overlap: Optional[int] = None
) -> Dict[str, any]:
    """Process documents and return results.
    
    Args:
        documents: List of document paths
        chunk_size: Size of chunks in tokens
        overlap: Overlap between chunks
        
    Returns:
        Dictionary containing processing results
    """
    pass
```

### Docstrings

Use Google-style docstrings for all public functions and classes:

```python
def search_hybrid(
    self,
    query: str,
    alpha: float = 0.7,
    top_k: int = 5
) -> List[Dict]:
    """Perform hybrid search combining vector and keyword search.
    
    Hybrid search uses both semantic similarity (vector search) and 
    keyword matching (BM25) to find relevant results.
    
    Args:
        query: The search query string
        alpha: Weight for vector vs keyword search (0.0-1.0)
               1.0 = pure vector, 0.0 = pure keyword
        top_k: Number of results to return
        
    Returns:
        List of dictionaries containing:
            - content: The chunk content
            - similarity_score: Relevance score
            - metadata: Additional metadata
            
    Raises:
        ValueError: If query is empty or alpha not in [0.0, 1.0]
        ConnectionError: If database connection fails
        
    Example:
        >>> retriever = Retriever(db_manager, "Documents")
        >>> results = retriever.search_hybrid("machine learning", alpha=0.7)
        >>> print(f"Found {len(results)} results")
        Found 5 results
    """
    pass
```

### Code Organization

```python
# Standard library imports
import os
import sys
from typing import List, Dict

# Third-party imports
import numpy as np
from sentence_transformers import SentenceTransformer

# Local imports
from ragora.core import DatabaseManager
from ragora.utils import get_device
```

## 🧪 Testing Guidelines

### Writing Tests

Place tests in the appropriate directory:
- `tests/unit/` - Unit tests for individual components
- `tests/integration/` - Integration tests for component interactions

### Test Structure

```python
import pytest
from ragora.core import DataChunker

class TestDataChunker:
    """Tests for the DataChunker class."""
    
    def test_basic_chunking(self):
        """Test basic chunking functionality."""
        chunker = DataChunker()
        context = ChunkingContextBuilder().for_text().build()
        text = "This is a test. " * 50
        
        chunks = chunker.chunk(text, context)
        
        assert len(chunks) > 0
        assert all(isinstance(chunk, DataChunk) for chunk in chunks)
    
    def test_chunking_with_overlap(self):
        """Test that overlap is correctly applied."""
        from ragora import TextChunkingStrategy
        custom_strategy = TextChunkingStrategy(chunk_size=100, overlap_size=20)
        chunker = DataChunker(default_strategy=custom_strategy)
        context = ChunkingContextBuilder().for_text().build()
        text = "Test content. " * 100
        
        chunks = chunker.chunk(text, context)
        
        # Verify overlap exists
        for i in range(len(chunks) - 1):
            assert chunks[i].text[-10:] in chunks[i + 1].text
    
    def test_empty_text(self):
        """Test handling of empty input."""
        chunker = DataChunker()
        context = ChunkingContextBuilder().for_text().build()
        
        chunks = chunker.chunk("", context)
        assert len(chunks) == 0
```

### Test Coverage

Aim for:
- **Unit tests**: 80%+ coverage
- **Integration tests**: Cover main workflows
- **Edge cases**: Test boundary conditions and error cases

### Running Tests

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=ragora --cov-report=html --cov-report=term

# Run specific test file
python -m pytest tests/unit/test_data_chunker.py

# Run specific test
python -m pytest tests/unit/test_data_chunker.py::TestDataChunker::test_basic_chunking

# Run tests matching pattern
python -m pytest -k "chunker"
```

For more details, see [testing.md](testing.md).

## 📋 Commit Message Convention

We use [Conventional Commits](https://www.conventionalcommits.org/) for automatic versioning.

### Format

```
type(scope): description

[optional body]

[optional footer]
```

### Types

- `feat:` - New feature (minor version bump)
- `fix:` - Bug fix (patch version bump)
- `docs:` - Documentation changes
- `test:` - Adding or updating tests
- `refactor:` - Code refactoring
- `perf:` - Performance improvements
- `style:` - Code style changes (formatting, etc.)
- `chore:` - Maintenance tasks
- `ci:` - CI/CD changes

### Examples

```bash
# Good commit messages
git commit -m "feat: add hybrid search functionality"
git commit -m "fix: resolve memory leak in embedding engine"
git commit -m "docs: update installation instructions"
git commit -m "test: add unit tests for retriever"

# With scope
git commit -m "feat(retriever): add filtered search capability"
git commit -m "fix(chunker): handle edge case with empty text"

# Breaking change (major version bump)
git commit -m "feat!: redesign API interface

BREAKING CHANGE: All search methods now return different format"
```

For more details, see the release documentation in the root folder of the development repository.

## 🔍 Pull Request Process

### Before Submitting

- [ ] Code follows style guidelines (Black, isort, Flake8)
- [ ] All tests pass
- [ ] New tests added for new features
- [ ] Documentation updated
- [ ] Commit messages follow convention
- [ ] Branch is up to date with main

### PR Template

```markdown
## Description
Brief description of changes

## Motivation
Why is this change needed?

## Changes
- List of specific changes
- Another change

## Testing
How was this tested?

## Related Issues
Closes #123
```

### Review Process

1. **Automated Checks**: CI/CD runs tests and linting
2. **Code Review**: Maintainers review code
3. **Feedback**: Address any requested changes
4. **Approval**: Approved by maintainer(s)
5. **Merge**: Merged to main branch

## 🐛 Reporting Bugs

### Before Reporting

1. Check existing issues
2. Verify bug in latest version
3. Test in clean environment

### Bug Report Template

```markdown
## Description
Clear description of the bug

## Steps to Reproduce
1. Step one
2. Step two
3. Step three

## Expected Behavior
What should happen

## Actual Behavior
What actually happens

## Environment
- Ragora version:
- Python version:
- OS:
- Weaviate version:

## Additional Context
Any other relevant information
```

## 💡 Suggesting Features

### Feature Request Template

```markdown
## Feature Description
Clear description of the feature

## Motivation
Why is this feature needed?

## Proposed Solution
How should this work?

## Alternatives Considered
Other approaches considered

## Additional Context
Any other relevant information
```

## 📚 Documentation

### Documentation Standards

- **Clear and Concise**: Easy to understand
- **Examples**: Include code examples
- **Complete**: Cover all use cases
- **Up-to-date**: Keep synchronized with code

### Where to Add Documentation

- **Code Comments**: For complex logic
- **Docstrings**: For all public APIs
- **README**: For package overview
- **docs/**: For detailed guides
- **Examples**: For usage demonstrations

### Documentation Types

- **API Reference**: Auto-generated from docstrings
- **Guides**: Step-by-step instructions
- **Tutorials**: Learning-oriented content
- **How-to**: Problem-solving focused

## 🏆 Recognition

Contributors are recognized in:
- CONTRIBUTORS.md file
- Release notes
- GitHub contributors page

## 📞 Getting Help

- **Documentation**: Check docs directory
- **Issues**: Ask in GitHub Issues
- **Discussions**: GitHub Discussions
- **Email**: Contact maintainers directly

## 📜 Code of Conduct

### Our Standards

- **Be Respectful**: Treat everyone with respect
- **Be Constructive**: Provide helpful feedback
- **Be Collaborative**: Work together effectively
- **Be Patient**: Help others learn

### Unacceptable Behavior

- Harassment or discrimination
- Trolling or insulting comments
- Public or private harassment
- Publishing private information

## 🔗 Related Documentation

- [Development Guide](development.md) - Development workflow
- [Testing Guide](testing.md) - Testing standards
- [Architecture](architecture.md) - System architecture

## 🙏 Thank You

Thank you for contributing to Ragora! Your contributions help make this project better for everyone.

