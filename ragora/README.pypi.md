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
cd database-server
./database-manager.sh start
```

Update `<x.y.z>` with the actual package version- For example use `1.0.0` for version `v1.0.0`.
The database server is a zero-dependency solution (only requires Docker) that works on Windows, macOS, and Linux.

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

## 🔍 Search Modes

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

## 🎯 Use Cases

- **📖 Academic Research**: Build knowledge bases from scientific papers and LaTeX documents
- **📝 Documentation Search**: Create searchable knowledge bases from technical documentation
- **🤖 AI Assistants**: Ground LLM responses in your specific domain knowledge
- **💬 Question Answering**: Build Q&A systems over your document collections
- **🔬 Literature Review**: Efficiently search and synthesize information from research papers

## 📖 Documentation & Examples

- **[Getting Started Guide](https://github.com/vahidlari/aiapps/blob/main/ragora/docs/getting_started.md)**: Detailed installation and setup guide
- **[API Reference](https://github.com/vahidlari/aiapps/blob/main/ragora/docs/api_reference.md)**: Complete API documentation
- **[Examples Directory](https://github.com/vahidlari/aiapps/tree/main/ragora/ragora/examples)**: Working code examples
  - `basic_usage.py`: Basic usage examples and getting started
  - `advanced_usage.py`: Advanced features and custom pipelines
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
