# Ragora

**Build smarter, grounded, and transparent AI with Ragora.**

Ragora is an open-source framework for building Retrieval-Augmented Generation (RAG) systems that connect your language models to real, reliable knowledge. It provides a clean, composable interface for managing knowledge bases, document retrieval, and grounding pipelines, so your AI can reason with context instead of guesswork.

The name Ragora blends RAG with the ancient Greek Agora, the public square where ideas were exchanged, debated, and refined. In the same spirit, Ragora is the meeting place of data and dialogue, where your information and your AI come together to think.

## ✨ Key Features

- **📄 Specialized Document Processing**: Native support for processing different document formats through different utility modules. The current release supports LaTeX parsing, as well as EMail handling. Further document formats are planned to be added incrementally. 
- **🏗️ Clean Architecture**: Three-layer design (DatabaseManager → VectorStore → Retriever) for maintainability and flexibility
- **🔍 Flexible Search**: Vector, keyword, and hybrid search modes for optimal retrieval
- **🧩 Composable Components**: Use high-level APIs or build custom pipelines with low-level components
- **⚡ Performance Optimized**: Batch processing, GPU acceleration, and efficient vector search with Weaviate
- **🔒 Privacy-First**: Run completely local with sentence-transformers and Weaviate
- **🧪 Well-Tested**: Comprehensive test suite with 80%+ coverage

## 🚀 Quick Start

### Installation

```bash
pip install ragora
```

### Basic Usage

```python
from ragora import KnowledgeBaseManager

# Initialize the knowledge base manager
kbm = KnowledgeBaseManager(
    weaviate_url="http://localhost:8080"
)

# Process documents
document_paths = ["paper1.tex", "paper2.tex"]
chunk_ids = kbm.process_documents(document_paths)
print(f"Processed {len(chunk_ids)} chunks")

# Query the knowledge base
from ragora import SearchStrategy

results = kbm.search(
    "What is quantum entanglement?",
    strategy=SearchStrategy.HYBRID,
    top_k=5
)

# Display results
for result in results.results:
    print(f"Score: {result.get('similarity_score', 0):.3f}")
    print(f"Content: {result['content'][:200]}...\n")
```

### Prerequisites

You need a Weaviate instance running. Download the pre-configured Ragora database server:

```bash
# Download from GitHub releases
wget https://github.com/vahidlari/aiapps/releases/latest/download/ragora-database-server.tar.gz

# Extract and start
tar -xzf ragora-database-server.tar.gz
cd ragora-database-server
./database-manager.sh start
```

The database server is a zero-dependency solution (only requires Docker) that works on Windows, macOS, and Linux.

## 📚 Core Concepts

### Three-Layer Architecture

Ragora uses a clean three-layer architecture that separates concerns:

1. **DatabaseManager** (Infrastructure Layer): Low-level Weaviate operations
2. **VectorStore** (Storage Layer): Document storage and CRUD operations
3. **Retriever** (Search Layer): Search algorithms and query processing

This design provides flexibility, testability, and makes it easy to extend or swap components.

### Search Modes

Ragora supports three search strategies:

```python
from ragora import SearchStrategy

# Semantic search (best for conceptual queries)
results = kbm.search("explain machine learning", strategy=SearchStrategy.SIMILAR)

# Keyword search (best for exact terms)
results = kbm.search("Schrödinger equation", strategy=SearchStrategy.KEYWORD)

# Hybrid search (recommended - combines both)
results = kbm.search("neural networks", strategy=SearchStrategy.HYBRID, alpha=0.7)
```

### Document Processing

Process LaTeX documents with specialized handling:

```python
from ragora.core import DocumentPreprocessor, DataChunker

# Parse LaTeX with citations
preprocessor = DocumentPreprocessor()
document = preprocessor.parse_latex(
    "paper.tex",
    bibliography_path="references.bib"
)

# Chunk with configurable size and overlap using new API
from ragora import DataChunker, ChunkingContextBuilder

chunker = DataChunker()
context = ChunkingContextBuilder().for_document().build()
chunks = chunker.chunk(document.content, context)
```

## 🎯 Use Cases

- **📖 Academic Research**: Build knowledge bases from scientific papers and LaTeX documents
- **📝 Documentation Search**: Create searchable knowledge bases from technical documentation
- **🤖 AI Assistants**: Ground LLM responses in your specific domain knowledge
- **💬 Question Answering**: Build Q&A systems over your document collections
- **🔬 Literature Review**: Efficiently search and synthesize information from research papers

## 📖 Documentation

- **[Getting Started](docs/getting_started.md)**: Detailed installation and setup guide
- **[Architecture](docs/architecture.md)**: System design and components
- **[Design Decisions](docs/design_decisions.md)**: Rationale behind key choices
- **[API Reference](docs/api_reference.md)**: Complete API documentation
- **[Deployment](docs/deployment.md)**: Production deployment guide
- **[Testing](docs/testing.md)**: Testing guidelines
- **[Contributing](docs/contributing.md)**: How to contribute

## 🔧 Advanced Usage

### Custom Pipeline

Build custom RAG pipelines with low-level components:

```python
from ragora.core import (
    DatabaseManager,
    VectorStore,
    Retriever,
    EmbeddingEngine
)

# Initialize components
db_manager = DatabaseManager(url="http://localhost:8080")
vector_store = VectorStore(db_manager, collection="MyDocs")
retriever = Retriever(db_manager, collection="MyDocs")
embedder = EmbeddingEngine(model_name="all-mpnet-base-v2")

# Build custom workflow
embeddings = embedder.embed_batch(texts)
vector_store.store_chunks(chunks)
results = retriever.search_hybrid(query, collection="MyDocs", alpha=0.7, top_k=10)
```

### Multiple Search Strategies

Compare different search approaches:

```python
# Semantic search for conceptual similarity
semantic = retriever.search_similar(
    "artificial intelligence applications",
    collection="MyDocs",
    top_k=5
)

# Keyword search for exact matches
keyword = retriever.search_keyword(
    "neural network architecture",
    collection="MyDocs",
    top_k=5
)

# Hybrid search with custom weighting
hybrid = retriever.search_hybrid(
    "deep learning models",
    collection="MyDocs",
    alpha=0.7,  # 70% vector, 30% keyword
    top_k=5
)

# Search with metadata filters
filtered = retriever.search_with_filter(
    "quantum mechanics",
    filters={"author": "Feynman", "year": 1965},
    top_k=5
)
```

## 💡 Examples

Check out the [`ragora/examples/`](ragora/examples/) directory for more detailed examples:

- **`basic_usage.py`**: Basic usage examples and getting started
- **`advanced_usage.py`**: Advanced features and custom pipelines
- **`email_usage_examples.py`**: Email integration examples

## 🏗️ Development

### Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/vahidlari/aiapps.git
cd aiapps/ragora

# Install in development mode
pip install -e ".[dev]"

# Run tests
python -m pytest

# Run with coverage
python -m pytest --cov=ragora --cov-report=html
```

### Running Tests

```bash
# All tests
python -m pytest

# Unit tests only
python -m pytest tests/unit/

# Integration tests only
python -m pytest tests/integration/

# With coverage
python -m pytest --cov=ragora --cov-report=html
```

See [docs/testing.md](docs/testing.md) for comprehensive testing documentation.

## 🤝 Contributing

We welcome contributions! Please see [docs/contributing.md](docs/contributing.md) for guidelines on:

- Setting up your development environment
- Code style and standards
- Writing tests
- Submitting pull requests
- Commit message conventions

## 📊 Requirements

- **Python**: 3.11 or higher
- **Weaviate**: 1.22.0 or higher (for vector storage)
- **Dependencies**: See `requirements.txt`

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

Ragora builds on excellent open-source projects:

- **[Weaviate](https://weaviate.io/)**: Vector database with powerful search capabilities
- **[Sentence Transformers](https://www.sbert.net/)**: State-of-the-art text embeddings
- **[PyTorch](https://pytorch.org/)**: Deep learning framework

## 🔗 Links

- **Repository**: [github.com/vahidlari/aiapps](https://github.com/vahidlari/aiapps)
- **Documentation**: [docs/](docs/)
- **Examples**: [examples/](../examples/)
- **Issues**: [GitHub Issues](https://github.com/vahidlari/aiapps/issues)
- **Discussions**: [GitHub Discussions](https://github.com/vahidlari/aiapps/discussions)

## 📮 Contact

For questions, feedback, or collaboration opportunities, please:
- Open an issue on GitHub
- Start a discussion in GitHub Discussions
- Contact the maintainers directly

---

**Build smarter, grounded, and transparent AI with Ragora.**
