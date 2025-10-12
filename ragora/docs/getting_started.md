# Getting Started with Ragora

This guide will help you get started with Ragora, from installation to building your first RAG system.

## 📋 Prerequisites

### System Requirements

- **Python**: 3.11 or higher
- **Memory**: 8GB RAM minimum (16GB recommended for larger models)
- **Storage**: 5GB free space for models and data
- **OS**: Linux, macOS, or Windows with WSL

### Required Software

1. **Docker** (for Weaviate database)
   - [Docker Desktop](https://www.docker.com/products/docker-desktop/) for Windows/macOS
   - Docker Engine for Linux

2. **Python Environment**
   - Python 3.11+
   - pip or conda for package management

## 🚀 Installation

### Option 1: Install from PyPI (Recommended)

```bash
# Install the latest version
pip install ragora

# Or install a specific version
pip install ragora==1.0.0
```

### Option 2: Install from Source

```bash
# Clone the repository
git clone https://github.com/vahidlari/aiapps.git
cd aiapps/ragora

# Install in development mode
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

### Verify Installation

```bash
python -c "import ragora; print(f'Ragora version: {ragora.__version__}')"
```

## 🗄️ Database Setup

Ragora uses Weaviate as its vector database. You need to start a Weaviate instance before using Ragora.

### Using the Ragora Database Server (Recommended)

Download the pre-configured database server from the latest release:

```bash
# Download from GitHub releases
wget https://github.com/vahidlari/aiapps/releases/latest/download/ragora-database-server.tar.gz

# Extract
tar -xzf ragora-database-server.tar.gz
cd ragora-database-server

# Start the server
./database-manager.sh start

# Check if it's running
./database-manager.sh status
```

The database will be available at `http://localhost:8080`.

**Features:**
- Zero dependencies (only requires Docker)
- Pre-configured for Ragora
- Includes sentence-transformers inference API
- Works on Windows, macOS, and Linux

For detailed documentation, see the included README.md in the database server package.

### Alternative: Manual Docker Setup

If you prefer to set up Weaviate manually:

```bash
docker run -d \
  --name weaviate \
  -p 8080:8080 \
  -e QUERY_DEFAULTS_LIMIT=25 \
  -e AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED=true \
  -e PERSISTENCE_DATA_PATH='/var/lib/weaviate' \
  semitechnologies/weaviate:1.22.4
```

## 🎯 Quick Start

### Basic Usage

Here's a simple example to get you started:

```python
from ragora import KnowledgeBaseManager

# Initialize the knowledge base manager
kbm = KnowledgeBaseManager(
    weaviate_url="http://localhost:8080",
    class_name="Documents",
    embedding_model="all-mpnet-base-v2",
    chunk_size=768,
    chunk_overlap=100
)

# Process documents
document_paths = [
    "path/to/document1.tex",
    "path/to/document2.tex"
]
chunk_ids = kbm.process_documents(document_paths)
print(f"Processed {len(chunk_ids)} chunks")

# Query the knowledge base
results = kbm.query(
    "What is quantum entanglement?",
    search_type="hybrid",
    top_k=5
)

# Display results
for i, result in enumerate(results['chunks'], 1):
    print(f"\n{i}. Score: {result['similarity_score']:.3f}")
    print(f"   Content: {result['content'][:200]}...")
```

### Document Processing

```python
from ragora.core import (
    DocumentPreprocessor,
    DataChunker,
    EmbeddingEngine
)

# Initialize components
preprocessor = DocumentPreprocessor()
chunker = DataChunker(chunk_size=768, overlap=100)
embedder = EmbeddingEngine(model_name="all-mpnet-base-v2")

# Process a LaTeX document
document = preprocessor.parse_latex("document.tex", "references.bib")

# Chunk the content
chunks = []
for section in document.sections:
    for paragraph in section.paragraphs:
        paragraph_chunks = chunker.chunk_text(paragraph.content)
        chunks.extend(paragraph_chunks)

# Generate embeddings
embeddings = embedder.embed_batch([chunk.content for chunk in chunks])

print(f"Created {len(chunks)} chunks with embeddings")
```

### Search and Retrieval

```python
from ragora.core import DatabaseManager, Retriever

# Initialize database connection
db_manager = DatabaseManager(url="http://localhost:8080")

# Create retriever
retriever = Retriever(
    db_manager=db_manager,
    class_name="Documents"
)

# Semantic search
results = retriever.search_similar(
    query="machine learning algorithms",
    top_k=5
)

# Hybrid search (recommended)
results = retriever.search_hybrid(
    query="deep learning neural networks",
    alpha=0.7,  # 0.0 = pure keyword, 1.0 = pure vector
    top_k=5
)

# Keyword search
results = retriever.search_keyword(
    query="Schrödinger equation",
    top_k=5
)

# Search with filters
results = retriever.search_with_filter(
    query="quantum mechanics",
    filters={"author": "Feynman"},
    top_k=5
)

# Display results
for result in results:
    print(f"Score: {result['similarity_score']:.3f}")
    print(f"Content: {result['content'][:150]}...")
    print(f"Metadata: {result.get('metadata', {})}\n")
```

## 🔧 Configuration

### Embedding Models

Ragora supports multiple embedding models. Choose based on your needs:

```python
# Recommended: Best quality
kbm = KnowledgeBaseManager(
    weaviate_url="http://localhost:8080",
    embedding_model="all-mpnet-base-v2"
)

# Faster, smaller
kbm = KnowledgeBaseManager(
    weaviate_url="http://localhost:8080",
    embedding_model="all-MiniLM-L6-v2"
)

# Optimized for Q&A
kbm = KnowledgeBaseManager(
    weaviate_url="http://localhost:8080",
    embedding_model="multi-qa-MiniLM-L6-v2"
)
```

### Chunking Configuration

```python
# Default configuration
kbm = KnowledgeBaseManager(
    weaviate_url="http://localhost:8080",
    chunk_size=768,      # Tokens per chunk
    chunk_overlap=100    # Overlap between chunks
)

# Smaller chunks (faster, less context)
kbm = KnowledgeBaseManager(
    weaviate_url="http://localhost:8080",
    chunk_size=512,
    chunk_overlap=50
)

# Larger chunks (slower, more context)
kbm = KnowledgeBaseManager(
    weaviate_url="http://localhost:8080",
    chunk_size=1024,
    chunk_overlap=150
)
```

### Search Configuration

```python
# Configure search types
results = kbm.query(
    "your query here",
    search_type="hybrid",  # Options: "similar", "keyword", "hybrid"
    top_k=10,              # Number of results
    alpha=0.7              # Hybrid search weight (0.0-1.0)
)
```

## 📚 Examples

### Example 1: LaTeX Document Processing

```python
from ragora import KnowledgeBaseManager

# Initialize
kbm = KnowledgeBaseManager(
    weaviate_url="http://localhost:8080",
    class_name="AcademicPapers"
)

# Process LaTeX documents
papers = [
    "papers/quantum_mechanics.tex",
    "papers/statistical_physics.tex"
]
kbm.process_documents(papers)

# Query with technical terms
results = kbm.query(
    "What is the Heisenberg uncertainty principle?",
    search_type="hybrid",
    top_k=5
)
```

### Example 2: Multi-Document Knowledge Base

```python
import glob
from ragora import KnowledgeBaseManager

# Initialize
kbm = KnowledgeBaseManager(
    weaviate_url="http://localhost:8080",
    class_name="Documentation"
)

# Process all documents in a directory
documents = glob.glob("docs/**/*.tex", recursive=True)
chunk_ids = kbm.process_documents(documents)

# Get system statistics
stats = kbm.get_system_stats()
print(f"Total chunks: {stats['vector_store']['total_objects']}")
```

### Example 3: Custom Pipeline

See the [examples directory](../../../examples/) for more detailed examples:
- `latex_loading_example.py` - Document loading and processing
- `latex_retriever_example.py` - Search and retrieval
- `advanced_usage.py` - Advanced features

## 🐛 Troubleshooting

### Common Issues

**Issue: "Cannot connect to Weaviate"**
```bash
# Check if Weaviate is running
curl http://localhost:8080/v1/.well-known/ready

# Restart Weaviate
cd tools/database_server
./database-manager.sh restart
```

**Issue: "Out of memory during embedding"**
```python
# Reduce batch size
embedder = EmbeddingEngine(
    model_name="all-mpnet-base-v2",
    batch_size=16  # Default is 32
)
```

**Issue: "Slow embedding generation"**
```python
# Use GPU if available
embedder = EmbeddingEngine(
    model_name="all-mpnet-base-v2",
    device="cuda"  # or "cpu"
)
```

**Issue: "Poor search results"**
```python
# Try hybrid search with different alpha values
results = kbm.query(
    "your query",
    search_type="hybrid",
    alpha=0.7  # Try values between 0.5-0.8
)

# Or increase chunk overlap
kbm = KnowledgeBaseManager(
    weaviate_url="http://localhost:8080",
    chunk_overlap=150  # Increase from default 100
)
```

## 📖 Next Steps

- **Read the [Architecture](architecture.md)** to understand how Ragora works
- **Explore [Design Decisions](design_decisions.md)** to learn about design choices
- **Check [API Reference](api_reference.md)** for detailed API documentation
- **See [Examples](../../../examples/)** for more usage examples
- **Read [Testing](testing.md)** to learn about testing your RAG system

## 🆘 Getting Help

- **Documentation**: Browse the docs in this directory
- **Examples**: Check the examples directory
- **Issues**: Report bugs or request features on GitHub
- **Discussions**: Ask questions in GitHub Discussions

## 🔗 Related Documentation

- [Architecture](architecture.md) - System architecture
- [Design Decisions](design_decisions.md) - Design rationale
- [API Reference](api_reference.md) - Complete API docs
- [Contributing](contributing.md) - How to contribute

