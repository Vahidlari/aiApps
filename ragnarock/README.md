# RAGnaROCK - LaTeX RAG System - Design Documentation

## 🎯 Project Overview

This project implements a Retrieval-Augmented Generation (RAG) system specifically designed for creating knowledge bases from LaTeX documents. The system is built with modularity and reusability in mind, using modern AI/ML technologies and best practices.

## 🏗️ System Architecture

### Core Components 

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Document       │    │   Embedding     │    │   Database      │
│  Processor      │───▶│   Engine        │───▶│   Manager       │
│  (LaTeX)        │    │  (Sentence      │    │  (Infrastructure│
└─────────────────┘    │   Transformers) │    │   Layer)        │
                       └─────────────────┘    └─────────────────┘
                                                        │
                                                        │
┌─────────────────┐    ┌─────────────────┐              │
│  Generation     │    │   Retriever     │              │
│  System         │◀───│   (Search       │◀─────────────│
│  (Ollama +      │    │    Layer)       │              │
│   Mistral 7B)   │    └─────────────────┘              │
└─────────────────┘             │                       │
                                │                       │
                       ┌─────────────────┐              │
                       │   Vector Store  │◀─────────────┘
                       │   (Storage      │
                       │    Layer)       │
                       └─────────────────┘
```

**Three-Layer Architecture Design:**
1. **DatabaseManager** (Infrastructure Layer) - Low-level Weaviate operations
2. **VectorStore** (Storage Layer) - Document storage and retrieval operations  
3. **Retriever** (Search Layer) - Search logic using Weaviate APIs directly

## 📁 Project Structure

```
ragnarock/
├── core/
│   ├── __init__.py
│   ├── document_preprocessor.py    # LaTeX parsing and preprocessing
│   ├── data_chunker.py            # Format-agnostic chunking
│   ├── embedding_engine.py        # Vector embeddings
│   ├── database_manager.py        # Infrastructure layer for Weaviate
│   ├── vector_store.py            # Storage layer for documents
│   ├── retriever.py               # Search layer using Weaviate APIs
│   └── knowledge_base_manager.py  # Main knowledge base manager
├── utils/
│   ├── __init__.py
│   ├── latex_parser.py            # LaTeX-specific utilities
│   ├── text_processing.py         # Text cleaning and preprocessing
│   ├── config_validator.py        # Configuration validation
│   ├── email_provider_factory.py  # Email provider factory (main entry point)
│   └── email_utils/               # Email utilities implementation
│       ├── __init__.py
│       ├── models.py              # Email data models
│       ├── base.py                # Abstract EmailProvider interface
│       ├── imap_provider.py       # IMAP/SMTP implementation
│       └── graph_provider.py      # Microsoft Graph API implementation
├── config/
│   ├── __init__.py
│   └── ettings.py                 # Configuration management
├── examples/
│   ├── __init__.py
│   ├── sample_queries.py          # Example usage
│   ├── email_usage_examples.py    # Email utilities examples
│   └── latex_samples/             # Sample LaTeX files for testing
├── tests/
│   ├── unit/
│   │   ├── test_database_manager.py
│   │   ├── test_vector_store.py
│   │   ├── test_retriever.py
│   │   ├── test_document_processor.py
│   │   ├── test_data_chunker.py
│   │   ├── test_embedding_engine.py
│   │   ├── test_generator.py
│   │   └── test_email_utils.py       # Email utilities tests
│   └── integration/
│       └── test_dbmng_retriever_vector_store.py
├── docs/
│   ├── design_decisions.md        # This file
│   ├── api_reference.md           # API documentation
│   └── deployment_guide.md        # Deployment instructions
├── requirements.txt               # Python dependencies
├── setup.py                       # Package setup
└── README.md                      # Main project README
```

## 🎯 Design Decisions

### A. Three-Layer Architecture Design

#### Clean Separation of Concerns
The system implements a three-layer architecture that cleanly separates responsibilities:

1. **DatabaseManager (Infrastructure Layer)**
   - **Purpose**: Low-level Weaviate client operations and connection management
   - **Responsibilities**: Connection handling, collection management, raw query execution
   - **Benefits**: Centralized database access, connection pooling, error handling

2. **VectorStore (Storage Layer)**
   - **Purpose**: Document storage and retrieval operations
   - **Responsibilities**: Storing chunks, CRUD operations, schema management
   - **Benefits**: Focused on data persistence, clean storage interface

3. **Retriever (Search Layer)**
   - **Purpose**: Search logic and query orchestration
   - **Responsibilities**: Vector search, hybrid search, keyword search, result processing
   - **Benefits**: Uses Weaviate APIs directly, implements search algorithms

#### Architecture Benefits
- **Maintainability**: Each layer has a single, clear responsibility
- **Testability**: Components can be tested independently with clear mocking boundaries
- **Flexibility**: Easy to swap database backends by changing DatabaseManager
- **Performance**: Direct Weaviate API usage without unnecessary abstractions

### B. Document Processing Strategy

#### LaTeX Handling
- **Equation Preservation**: Keep mathematical equations intact while removing other LaTeX commands
- **Citation Strategy**: Store citations as separate database entries with rich metadata
- **Command Removal**: Strip LaTeX formatting commands (`\section{}`, `\textbf{}`, etc.) while preserving semantic content

#### Chunking Strategy
- **Adaptive Fixed-Size**: 768 tokens with line boundary respect
- **Overlap**: 100-150 tokens between chunks for context preservation
- **Object-Oriented Design**: Configurable `DataChunker` class for format-agnostic flexibility

#### Citation Metadata Structure
```python
{
    "type": "citation",
    "author": "Einstein, A.",
    "year": 1905,
    "title": "On the Electrodynamics of Moving Bodies",
    "doi": "10.1002/andp.19053221004",
    "content": "The theory of relativity...",
    "source_document": "chapter_1.tex",
    "page_reference": 15,
    "chunk_id": "chunk_001"
}
```

### C. Embedding & Storage

#### Embedding Model
- **Technology**: Sentence Transformers (local, free)
- **Model**: `all-mpnet-base-v2` (768 dimensions, good for technical content)
- **Alternative**: `multi-qa-MiniLM-L6-v2` (optimized for Q&A)

#### Vector Database
- **Technology**: Weaviate
- **Integration**: Built-in `text2vec-transformers` module
- **Features**: Rich querying, filtering, and metadata support

#### Configuration
```python
# Weaviate with Sentence Transformers
{
    "vectorizer": "text2vec-transformers",
    "moduleConfig": {
        "text2vec-transformers": {
            "model": "all-mpnet-base-v2",
            "poolingStrategy": "masked_mean",
            "vectorizeClassName": False
        }
    }
}
```

### D. Retrieval Strategy

#### Hybrid Search
- **Vector Search**: Dense embeddings for semantic similarity
- **BM25 Search**: Sparse keyword matching for exact terms
- **Configurable Weights**: Adjustable alpha parameter (0.0-1.0)
- **Fusion Type**: Relative score combination

#### Query Processing
- **Technical Term Handling**: Preserve mathematical notation and technical terms
- **Citation Queries**: Special handling for author/year queries
- **Equation Queries**: Support for mathematical concept searches

### E. Generation System

#### LLM Configuration
- **Technology**: Ollama + Mistral 7B
- **Deployment**: Local, free
- **Context Window**: 4096 tokens
- **Specialization**: Good performance on technical/scientific content

#### Prompt Engineering
- **RAG-Specific**: Structured prompts for context-aware generation
- **Citation Integration**: Include citation metadata in responses
- **Equation Handling**: Preserve mathematical notation in outputs

## 🔧 Implementation Plan

### Phase 1: Core Infrastructure
1. Project structure setup
2. Configuration management
3. Base classes and interfaces
4. Unit testing framework

### Phase 2: Document Processing
1. LaTeX parser implementation
2. Data chunker implementation
3. Citation extraction
4. Metadata handling

### Phase 3: Embedding & Storage
1. Weaviate integration
2. Sentence Transformers setup
3. Document indexing
4. Vector storage optimization

### Phase 4: Retrieval System
1. Hybrid search implementation
2. Query preprocessing
3. Result ranking
4. Performance optimization

### Phase 5: Generation System
1. Ollama integration
2. Prompt engineering
3. Response formatting
4. Quality evaluation

### Phase 6: Integration & Testing
1. End-to-end testing
2. Performance benchmarking
3. Documentation completion
4. Deployment preparation

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Docker (for Weaviate)
- Ollama (for Mistral 7B)
- Git

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd ragnarock

# Install dependencies
pip install -r requirements.txt

# Start Weaviate
docker run -d --name weaviate -p 8080:8080 semitechnologies/weaviate:1.22.4

# Install Ollama and Mistral 7B
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull mistral:7b
```

### Quick Start

#### Option 1: High-Level Knowledge Base Manager (Recommended)
```python
from ragnarock import KnowledgeBaseManager

# Initialize the knowledge base manager (automatically sets up three-layer architecture)
kbm = KnowledgeBaseManager(
    weaviate_url="http://localhost:8080",
    class_name="Document",
    embedding_model="all-mpnet-base-v2",
    chunk_size=768,
    chunk_overlap=100
)

# Process a LaTeX document
chunk_ids = kbm.process_documents(["path/to/document.tex"])

# Query the knowledge base
response = kbm.query("What is the main equation in chapter 2?", search_type="similar")
print(f"Found {response['num_chunks']} relevant chunks")

# Try different search types
hybrid_response = kbm.query("machine learning algorithms", search_type="hybrid", top_k=5)
keyword_response = kbm.query("neural networks", search_type="keyword", top_k=3)

# Get system statistics
stats = kbm.get_system_stats()
print(f"Database contains {stats['vector_store']['total_objects']} chunks")
```

#### Option 2: Direct Component Usage (Advanced)
```python
from ragnarock import DatabaseManager, VectorStore, Retriever

# Initialize the three-layer architecture manually
db_manager = DatabaseManager(url="http://localhost:8080")
vector_store = VectorStore(db_manager=db_manager, class_name="Document")
retriever = Retriever(db_manager=db_manager, class_name="Document")

# Use components directly
results = retriever.search_similar("machine learning algorithms", top_k=5)
hybrid_results = retriever.search_hybrid("deep learning", alpha=0.7, top_k=5)
keyword_results = retriever.search_keyword("neural networks", top_k=5)

for result in results:
    print(f"Score: {result['similarity_score']:.3f} - {result['content'][:100]}...")
```

## 📊 Performance Considerations

### Chunk Size Optimization
- **Default**: 768 tokens
- **Testing Range**: 512-1024 tokens
- **Optimization**: Empirical testing with domain-specific queries

### Embedding Quality
- **Model Selection**: Balance between speed and quality
- **Fine-tuning**: Consider domain-specific fine-tuning for better performance
- **Evaluation**: Use semantic similarity metrics for validation

### Retrieval Performance
- **Hybrid Weights**: Optimize alpha parameter for your use case
- **Caching**: Implement result caching for common queries
- **Indexing**: Optimize Weaviate schema for your query patterns

## 🔍 Evaluation Metrics

### Retrieval Quality
- **Precision@K**: Top-K retrieval accuracy
- **Recall@K**: Coverage of relevant documents
- **MRR**: Mean Reciprocal Rank for ranking quality

### Generation Quality
- **ROUGE**: Text similarity metrics
- **BLEU**: Translation quality metrics
- **Human Evaluation**: Manual assessment of answer quality

### System Performance
- **Latency**: Query response time
- **Throughput**: Queries per second
- **Resource Usage**: Memory and CPU utilization

## 🤝 Contributing

### Development Guidelines
1. Follow PEP 8 coding standards
2. Write comprehensive unit tests
3. Document all public APIs
4. Use type hints throughout
5. Implement proper error handling

### Testing Strategy
- **Unit Tests**: Individual component testing
- **Integration Tests**: Component interaction testing
- **End-to-End Tests**: Complete workflow testing
- **Performance Tests**: Load and stress testing

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Weaviate team for the excellent vector database
- Sentence Transformers for the embedding models
- Ollama team for the local LLM framework
- The open-source AI/ML community for inspiration and tools
