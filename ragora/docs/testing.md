# Testing Guide

This document provides comprehensive information about testing in Ragora, including test structure, running tests, and writing new tests.

## 🎯 Testing Philosophy

Ragora follows a comprehensive testing strategy with three levels of tests:

1. **Unit Tests**: Test individual components in isolation
2. **Integration Tests**: Test component interactions
3. **End-to-End Tests**: Test complete workflows

## 📁 Test Structure

```
tests/
├── conftest.py                    # Pytest configuration and shared fixtures
├── run_tests.py                   # Test runner script
├── unit/                          # Unit tests for individual components
│   ├── test_data_chunker.py
│   ├── test_database_manager.py
│   ├── test_document_preprocessor.py
│   ├── test_embedding_engine.py
│   ├── test_email_utils.py
│   ├── test_knowledge_base_manager.py
│   ├── test_latex_parser.py
│   ├── test_retriever.py
│   └── test_vector_store.py
├── integration/                   # Integration tests
│   ├── test_dbmng_retriever_vector_store.py
│   ├── test_document_parsing.py
│   ├── test_document_preprocessor.py
│   └── test_rag_pipeline.py
├── fixtures/                      # Test data and sample files
│   ├── sample_latex.tex
│   ├── sample_bibliography.bib
│   └── expected_outputs/
└── utils/                         # Test utilities
    └── test_helpers.py
```

## 🚀 Running Tests

### Quick Start

```bash
# Navigate to ragora directory
cd ragora

# Run all tests
python -m pytest

# Run with verbose output
python -m pytest -v

# Run with coverage
python -m pytest --cov=ragora --cov-report=html
```

### Test Categories

```bash
# Run unit tests only
python -m pytest tests/unit/

# Run integration tests only
python -m pytest tests/integration/

# Run specific test file
python -m pytest tests/unit/test_data_chunker.py

# Run specific test
python -m pytest tests/unit/test_data_chunker.py::test_basic_chunking

# Run tests matching pattern
python -m pytest -k "chunker"
```

### Using the Test Runner Script

```bash
# Run all tests
python tests/run_tests.py

# Run unit tests only
python tests/run_tests.py --type unit

# Run with coverage report
python tests/run_tests.py --coverage

# Run with HTML coverage report
python tests/run_tests.py --html-coverage

# Run tests in parallel (requires pytest-xdist)
python tests/run_tests.py --parallel 4

# Skip slow tests
python tests/run_tests.py --fast
```

### Test Markers

Tests can be marked for selective execution:

```bash
# Run only unit tests
python -m pytest -m unit

# Run only integration tests
python -m pytest -m integration

# Skip slow tests
python -m pytest -m "not slow"

# Run tests for specific component
python -m pytest -m retriever
```

## 🧪 Writing Tests

### Unit Test Example

```python
import pytest
from ragora.core import DataChunker

class TestDataChunker:
    """Tests for the DataChunker class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.chunker = DataChunker()
        self.context = ChunkingContextBuilder().for_text().build()
    
    def test_basic_chunking(self):
        """Test basic chunking functionality."""
        text = "This is a test document. " * 50
        chunks = self.chunker.chunk(text, self.context)
        
        assert len(chunks) > 0
        assert all(isinstance(chunk, DataChunk) for chunk in chunks)
    
    def test_chunk_overlap(self):
        """Test that chunks have proper overlap."""
        text = "Word " * 100
        chunks = self.chunker.chunk(text, self.context)
        
        # Verify overlap exists between consecutive chunks
        for i in range(len(chunks) - 1):
            overlap_content = chunks[i].text[-20:]
            assert overlap_content in chunks[i + 1].text
    
    def test_empty_input(self):
        """Test handling of empty input."""
        chunks = self.chunker.chunk("", self.context)
        assert len(chunks) == 0
    
    def test_very_short_text(self):
        """Test handling of text shorter than chunk size."""
        text = "Short text."
        chunks = self.chunker.chunk(text, self.context)
        
        assert len(chunks) == 1
        assert chunks[0].text == text
    
    @pytest.mark.parametrize("chunk_size,overlap", [
        (256, 50),
        (512, 100),
        (1024, 150),
    ])
    def test_different_configurations(self, chunk_size, overlap):
        """Test chunking with different configurations."""
        from ragora import TextChunkingStrategy
        custom_strategy = TextChunkingStrategy(chunk_size=chunk_size, overlap_size=overlap)
        chunker = DataChunker(default_strategy=custom_strategy)
        text = "Test content. " * 200
        
        chunks = chunker.chunk(text, self.context)
        
        assert len(chunks) > 0
        assert all(len(chunk.text) <= chunk_size for chunk in chunks)
```

### Integration Test Example

```python
import pytest
from ragora import KnowledgeBaseManager
from ragora.core import DatabaseManager

class TestRAGPipeline:
    """Integration tests for complete RAG pipeline."""
    
    @pytest.fixture
    def db_manager(self):
        """Provide database manager fixture."""
        manager = DatabaseManager(url="http://localhost:8080")
        yield manager
        # Cleanup after test
        manager.delete_collection("TestDocs")
    
    @pytest.fixture
    def knowledge_base(self, db_manager):
        """Provide knowledge base manager fixture."""
        return KnowledgeBaseManager(
            weaviate_url="http://localhost:8080",
            class_name="TestDocs",
            embedding_model="all-MiniLM-L6-v2",  # Smaller model for tests
            chunk_size=256,
            chunk_overlap=50
        )
    
    def test_document_ingestion_and_retrieval(self, knowledge_base, tmp_path):
        """Test complete document processing and retrieval."""
        # Create test document
        doc_path = tmp_path / "test.tex"
        doc_path.write_text("""
        \\documentclass{article}
        \\begin{document}
        \\section{Introduction}
        This is a test document about machine learning.
        \\end{document}
        """)
        
        # Process document
        chunk_ids = knowledge_base.process_documents([str(doc_path)])
        assert len(chunk_ids) > 0
        
        # Query for content
        results = knowledge_base.query(
            "machine learning",
            search_type="hybrid",
            top_k=5
        )
        
        assert len(results['chunks']) > 0
        assert 'machine learning' in results['chunks'][0]['content'].lower()
    
    def test_multiple_search_types(self, knowledge_base, tmp_path):
        """Test different search types produce results."""
        # Setup test data
        doc_path = tmp_path / "test.tex"
        doc_path.write_text("Test content about neural networks and deep learning.")
        knowledge_base.process_documents([str(doc_path)])
        
        # Test semantic search
        semantic_results = knowledge_base.query(
            "artificial intelligence",
            search_type="similar",
            top_k=3
        )
        
        # Test keyword search
        keyword_results = knowledge_base.query(
            "neural networks",
            search_type="keyword",
            top_k=3
        )
        
        # Test hybrid search
        hybrid_results = knowledge_base.query(
            "deep learning",
            search_type="hybrid",
            top_k=3
        )
        
        assert len(semantic_results['chunks']) > 0
        assert len(keyword_results['chunks']) > 0
        assert len(hybrid_results['chunks']) > 0
```

### Using Fixtures

```python
import pytest
from pathlib import Path

@pytest.fixture
def sample_latex_content():
    """Provide sample LaTeX content."""
    return """
    \\documentclass{article}
    \\begin{document}
    \\section{Test Section}
    This is test content with an equation: $E = mc^2$
    \\end{document}
    """

@pytest.fixture
def sample_bibliography():
    """Provide sample bibliography content."""
    return """
    @article{einstein1905,
        author = {Einstein, Albert},
        title = {On the Electrodynamics of Moving Bodies},
        year = {1905}
    }
    """

@pytest.fixture
def temp_latex_file(tmp_path, sample_latex_content):
    """Create temporary LaTeX file."""
    file_path = tmp_path / "test.tex"
    file_path.write_text(sample_latex_content)
    return file_path

def test_with_fixture(temp_latex_file):
    """Test using fixture."""
    from ragora.core import DocumentPreprocessor
    
    preprocessor = DocumentPreprocessor()
    document = preprocessor.parse_latex(str(temp_latex_file))
    
    assert document is not None
    assert document.title is not None
```

### Mocking External Dependencies

```python
import pytest
from unittest.mock import Mock, patch
from ragora.core import Retriever

class TestRetrieverMocking:
    """Tests using mocks for external dependencies."""
    
    def test_search_with_mocked_database(self):
        """Test search with mocked database connection."""
        # Create mock database manager
        mock_db = Mock()
        mock_db.execute_query.return_value = [
            {
                'content': 'Test content',
                'similarity_score': 0.95
            }
        ]
        
        # Create retriever with mocked dependency
        retriever = Retriever(db_manager=mock_db, class_name="TestDocs")
        
        # Perform search
        with patch.object(retriever, '_execute_search', return_value=mock_db.execute_query()):
            results = retriever.search_similar("test query", top_k=5)
        
        assert len(results) > 0
        assert results[0]['similarity_score'] == 0.95
```

### Parametrized Tests

```python
import pytest
from ragora.core import EmbeddingEngine

@pytest.mark.parametrize("model_name,expected_dim", [
    ("all-MiniLM-L6-v2", 384),
    ("all-mpnet-base-v2", 768),
    ("multi-qa-MiniLM-L6-v2", 384),
])
def test_embedding_dimensions(model_name, expected_dim):
    """Test embedding dimensions for different models."""
    embedder = EmbeddingEngine(model_name=model_name)
    text = "Test sentence for embedding."
    
    embedding = embedder.embed_text(text)
    
    assert embedding.shape[0] == expected_dim
```

## 📊 Test Coverage

### Viewing Coverage

```bash
# Generate HTML coverage report
python -m pytest --cov=ragora --cov-report=html

# Open the report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Coverage Goals

- **Overall Coverage**: 80%+ for the entire codebase
- **Core Modules**: 90%+ coverage
- **Utility Functions**: 80%+ coverage
- **Critical Paths**: 100% coverage

### Coverage Configuration

In `pytest.ini`:

```ini
[tool:pytest]
addopts = 
    --cov=ragora
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
```

## 🐛 Debugging Tests

### Running Tests in Debug Mode

```bash
# Run with full output
python -m pytest -vvv --tb=long

# Run specific test with output
python -m pytest tests/unit/test_chunker.py::test_basic -vvv -s

# Drop into debugger on failure
python -m pytest --pdb

# Drop into debugger on first failure
python -m pytest -x --pdb
```

### Using VS Code Debugger

1. Set breakpoints in test code
2. Open test file
3. Click "Debug Test" in the testing panel
4. Step through code with debugger

### Logging During Tests

```python
import logging

def test_with_logging(caplog):
    """Test with captured log output."""
    caplog.set_level(logging.DEBUG)
    
    # Your test code
    from ragora.core import DataChunker
    chunker = DataChunker()
    
    # Check log output
    assert "Initializing chunker" in caplog.text
```

## ⚡ Performance Testing

### Benchmarking

```python
import pytest
import time

def test_chunking_performance():
    """Benchmark chunking performance."""
    from ragora.core import DataChunker
    
    chunker = DataChunker(chunk_size=768)
    text = "Test content. " * 10000
    
    start_time = time.time()
    chunks = chunker.chunk_text(text)
    duration = time.time() - start_time
    
    assert duration < 1.0  # Should complete in less than 1 second
    assert len(chunks) > 0
```

### Using pytest-benchmark

```bash
# Install pytest-benchmark
pip install pytest-benchmark

# Run benchmarks
python -m pytest tests/benchmarks/ --benchmark-only
```

```python
def test_embedding_performance(benchmark):
    """Benchmark embedding generation."""
    from ragora.core import EmbeddingEngine
    
    embedder = EmbeddingEngine(model_name="all-MiniLM-L6-v2")
    texts = ["Test sentence"] * 100
    
    result = benchmark(embedder.embed_batch, texts)
    
    assert len(result) == 100
```

## 🔄 Continuous Integration

### GitHub Actions

Tests run automatically on:
- Every push to main
- Every pull request
- Nightly builds

### Local Pre-commit Checks

```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Run manually
pre-commit run --all-files
```

## 📝 Best Practices

### Test Organization

1. **One test file per module**: Mirror source code structure
2. **Descriptive test names**: Use clear, descriptive names
3. **Group related tests**: Use classes to organize tests
4. **Use fixtures**: Leverage pytest fixtures for setup

### Test Quality

1. **Test edge cases**: Include boundary conditions
2. **Test error handling**: Verify exceptions are raised correctly
3. **Use assertions wisely**: Make specific, meaningful assertions
4. **Clean up resources**: Ensure proper cleanup after tests

### Performance

1. **Mark slow tests**: Use `@pytest.mark.slow` for long tests
2. **Use parallel execution**: Run independent tests in parallel
3. **Optimize test data**: Use minimal data that covers functionality
4. **Mock external services**: Don't rely on external dependencies

## 🔗 Related Documentation

- [Contributing Guide](contributing.md) - How to contribute
- [Development Guide](development.md) - Development workflow
- [Architecture](architecture.md) - System architecture

## 🆘 Getting Help

- **Test failures**: Check CI logs for details
- **Writing tests**: See examples in tests directory
- **Test fixtures**: Check conftest.py for available fixtures
- **Questions**: Ask in GitHub Issues or Discussions

