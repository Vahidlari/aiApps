# LaTeX RAG System - Design Documentation

## 🎯 Project Overview

This project implements a Retrieval-Augmented Generation (RAG) system specifically designed for creating knowledge bases from LaTeX documents. The system is built with modularity and reusability in mind, using modern AI/ML technologies and best practices.

## 🏗️ System Architecture

### Core Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Document       │    │   Embedding     │    │   Vector        │
│  Processor      │───▶│   Engine        │───▶│   Database      │
│  (LaTeX)        │    │  (Sentence      │    │  (Weaviate)     │
└─────────────────┘    │   Transformers) │    └─────────────────┘
                       └─────────────────┘              │
                                                        │
┌─────────────────┐    ┌─────────────────┐              │
│  Generation     │    │   Retrieval     │◀─────────────┘
│  System         │◀───│   System        │
│  (Ollama +      │    │  (Hybrid        │
│   Mistral 7B)   │    │   Search)       │
└─────────────────┘    └─────────────────┘
```

## 📁 Project Structure

```
rag_system/
├── core/
│   ├── __init__.py
│   ├── document_preprocessor.py    # LaTeX parsing and preprocessing
│   ├── data_chunker.py            # Format-agnostic chunking
│   ├── embedding_engine.py        # Vector embeddings
│   ├── vector_store.py            # Weaviate database interface
│   ├── retriever.py               # Hybrid search and retrieval
│   └── generator.py               # Answer generation with Ollama
├── utils/
│   ├── __init__.py
│   ├── latex_parser.py            # LaTeX-specific utilities
│   ├── text_processing.py         # Text cleaning and preprocessing
│   └── config_validator.py        # Configuration validation
├── config/
│   ├── __init__.py
│   ├── settings.py                # Configuration management
│   └── default_config.yaml        # Default configuration
├── examples/
│   ├── __init__.py
│   ├── sample_queries.py          # Example usage
│   └── latex_samples/             # Sample LaTeX files for testing
├── tests/
│   ├── __init__.py
│   ├── test_document_processor.py
│   ├── test_data_chunker.py
│   ├── test_embedding_engine.py
│   ├── test_vector_store.py
│   ├── test_retriever.py
│   └── test_generator.py
├── docs/
│   ├── design_decisions.md        # This file
│   ├── api_reference.md           # API documentation
│   └── deployment_guide.md        # Deployment instructions
├── requirements.txt               # Python dependencies
├── setup.py                       # Package setup
└── README.md                      # Main project README
```

## 🎯 Design Decisions

### A. Document Processing Strategy

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

### B. Embedding & Storage

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

### C. Retrieval Strategy

#### Hybrid Search
- **Vector Search**: Dense embeddings for semantic similarity
- **BM25 Search**: Sparse keyword matching for exact terms
- **Configurable Weights**: Adjustable alpha parameter (0.0-1.0)
- **Fusion Type**: Relative score combination

#### Query Processing
- **Technical Term Handling**: Preserve mathematical notation and technical terms
- **Citation Queries**: Special handling for author/year queries
- **Equation Queries**: Support for mathematical concept searches

### D. Generation System

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
cd rag_system

# Install dependencies
pip install -r requirements.txt

# Start Weaviate
docker run -d --name weaviate -p 8080:8080 semitechnologies/weaviate:1.22.4

# Install Ollama and Mistral 7B
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull mistral:7b
```

### Quick Start
```python
from rag_system.core import RAGSystem
from rag_system.config import ChunkConfig

# Initialize the system
config = ChunkConfig(chunk_size=768, overlap=100)
rag = RAGSystem(config)

# Process a LaTeX document
rag.process_document("path/to/document.tex")

# Query the knowledge base
response = rag.query("What is the main equation in chapter 2?")
print(response)
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
