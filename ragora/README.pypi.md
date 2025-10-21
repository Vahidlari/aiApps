# Ragora

[![PyPI version](https://badge.fury.io/py/ragora.svg)](https://pypi.org/project/ragora/)
[![Python versions](https://img.shields.io/pypi/pyversions/ragora.svg)](https://pypi.org/project/ragora/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/Vahidlari/aiApps/blob/main/ragora/LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/vahidlari/aiapps.svg)](https://github.com/vahidlari/aiapps)

**Build smarter, grounded, and transparent AI with Ragora.**

Ragora is an open-source framework for building Retrieval-Augmented Generation (RAG) systems that connect your language models to real, reliable knowledge. It provides a clean, composable interface for managing knowledge bases, document retrieval, and grounding pipelines, so your AI can reason with context instead of guesswork.

The name Ragora blends RAG with the ancient Greek Agora, the public square where ideas were exchanged, debated, and refined. In the same spirit, Ragora is the meeting place of data and dialogue, where your information and your AI come together to think.

## ✨ Key Features

- **📄 Specialized Document Processing**: Native support for LaTeX parsing and email handling with more formats coming
- **🏗️ Clean Architecture**: Three-layer design (DatabaseManager → VectorStore → Retriever) for maintainability
- **🔍 Flexible Search**: Vector, keyword, and hybrid search modes for optimal retrieval
- **🧩 Composable Components**: Use high-level APIs or build custom pipelines with low-level components
- **⚡ Performance Optimized**: Batch processing, GPU acceleration, and efficient vector search with Weaviate
- **🔒 Privacy-First**: Run completely local with sentence-transformers and Weaviate

## 🚀 Installation

```bash
pip install ragora
```

### Prerequisites

You need a Weaviate instance running. Download the pre-configured Ragora database server:

```bash
# Download from GitHub releases
wget https://github.com/Vahidlari/aiApps/releases/download/v<x.y.z>/database_server-<x.y.z>.tar.gz

# Extract and start
tar -xzf database_server-<x.y.z>.tar.gz
cd ragora-database-server
./database-manager.sh start
```

Update `<x.y.z>` with the actual package version.
The database server is a zero-dependency solution (only requires Docker) that works on Windows, macOS, and Linux.

## 🎯 Quick Start

```python
from ragora import KnowledgeBaseManager

# Initialize the knowledge base manager
kbm = KnowledgeBaseManager(
    weaviate_url="http://localhost:8080",
    class_name="Documents",
    embedding_model="all-mpnet-base-v2"
)

# Process documents
document_paths = ["paper1.tex", "paper2.tex"]
chunk_ids = kbm.process_documents(document_paths)
print(f"Processed {len(chunk_ids)} chunks")

# Query the knowledge base
results = kbm.query(
    "What is quantum entanglement?",
    search_type="hybrid",
    top_k=5
)

# Display results
for result in results['chunks']:
    print(f"Score: {result['similarity_score']:.3f}")
    print(f"Content: {result['content'][:200]}...\n")
```

## 📚 Core Concepts

### Three-Layer Architecture

Ragora uses a clean three-layer architecture that separates concerns:

1. **DatabaseManager** (Infrastructure Layer): Low-level Weaviate operations
2. **VectorStore** (Storage Layer): Document storage and CRUD operations  
3. **Retriever** (Search Layer): Search algorithms and query processing

This design provides flexibility, testability, and makes it easy to extend or swap components.

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

# Chunk with configurable size and overlap
chunker = DataChunker(chunk_size=768, overlap=100)
chunks = chunker.chunk_text(document.content)
```

## 🔍 Search Modes

Ragora supports three search strategies:

```python
# Semantic search (best for conceptual queries)
results = kbm.query("explain machine learning", search_type="similar")

# Keyword search (best for exact terms)
results = kbm.query("Schrödinger equation", search_type="keyword")

# Hybrid search (recommended - combines both)
results = kbm.query("neural networks", search_type="hybrid", alpha=0.7)
```

## 🎯 Use Cases

- **📖 Academic Research**: Build knowledge bases from scientific papers and LaTeX documents
- **📝 Documentation Search**: Create searchable knowledge bases from technical documentation
- **🤖 AI Assistants**: Ground LLM responses in your specific domain knowledge
- **💬 Question Answering**: Build Q&A systems over your document collections
- **🔬 Literature Review**: Efficiently search and synthesize information from research papers

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
vector_store = VectorStore(db_manager, class_name="MyDocs")
retriever = Retriever(db_manager, class_name="MyDocs")
embedder = EmbeddingEngine(model_name="all-mpnet-base-v2")

# Build custom workflow
embeddings = embedder.embed_batch(texts)
vector_store.store_chunks(chunks)
results = retriever.search_hybrid(query, alpha=0.7, top_k=10)
```

### Multiple Search Strategies

Compare different search approaches:

```python
# Semantic search for conceptual similarity
semantic = retriever.search_similar(
    "artificial intelligence applications",
    top_k=5
)

# Keyword search for exact matches
keyword = retriever.search_keyword(
    "neural network architecture",
    top_k=5
)

# Hybrid search with custom weighting
hybrid = retriever.search_hybrid(
    "deep learning models",
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

## 📖 Documentation & Examples

- **[Getting Started Guide](https://github.com/vahidlari/aiapps/blob/main/ragora/docs/getting_started.md)**: Detailed installation and setup guide
- **[API Reference](https://github.com/vahidlari/aiapps/blob/main/ragora/docs/api_reference.md)**: Complete API documentation
- **[Examples Directory](https://github.com/vahidlari/aiapps/tree/main/ragora/ragora/examples)**: Working code examples
  - `advanced_usage.py`: Advanced features and custom pipelines
  - `basic_usage.py`: Basic usage examples
  - `email_usage_examples.py`: Email integration examples

## 📊 Requirements

- **Python**: 3.11 or higher
- **Weaviate**: 1.22.0 or higher (for vector storage)
- **Dependencies**: See [requirements.txt](https://github.com/vahidlari/aiapps/blob/main/ragora/requirements.txt)

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](https://github.com/vahidlari/aiapps/blob/main/ragora/docs/contributing.md) for:

- Setting up your development environment
- Code style and standards
- Writing tests
- Submitting pull requests

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/vahidlari/aiapps/blob/main/ragora/LICENSE) file for details.

## 🔗 Links

- **Repository**: [github.com/vahidlari/aiapps](https://github.com/vahidlari/aiapps)
- **Issues**: [GitHub Issues](https://github.com/vahidlari/aiapps/issues)
- **Discussions**: [GitHub Discussions](https://github.com/vahidlari/aiapps/discussions)

## 📮 Contact

For questions, feedback, or collaboration opportunities:
- Open an issue on GitHub
- Start a discussion in GitHub Discussions
- Contact the maintainers directly

---

**Build smarter, grounded, and transparent AI with Ragora.**
