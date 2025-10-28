# Design Decisions

This document explains the key design decisions made in building Ragora and the rationale behind them.

## 🎯 Architecture Decisions

### Three-Layer Architecture

**Decision:** Implement a three-layer architecture (DatabaseManager → VectorStore → Retriever)

**Rationale:**
- **Maintainability:** Each layer has a single, clear responsibility
- **Testability:** Components can be tested independently with clear mocking boundaries
- **Flexibility:** Easy to swap database backends by changing DatabaseManager
- **Performance:** Direct Weaviate API usage without unnecessary abstractions
- **Clarity:** Clear separation between infrastructure, storage, and search concerns

**Alternatives Considered:**
- **Two-layer approach:** Combining VectorStore and Retriever would have been simpler but less flexible
- **Single unified class:** Would have been easier to use but harder to test and maintain
- **Four+ layers:** Additional abstraction would have added complexity without clear benefits

### Direct Weaviate API Usage

**Decision:** Use Weaviate APIs directly in the Retriever layer instead of abstracting them

**Rationale:**
- **Performance:** Direct API access is faster than additional abstraction layers
- **Features:** Full access to Weaviate's rich query capabilities
- **Simplicity:** Less code to maintain
- **Flexibility:** Easy to leverage new Weaviate features as they're released

**Trade-offs:**
- Tighter coupling to Weaviate (acceptable for our use case)
- Would require more work to support other vector databases (not a current requirement)

## 🗄️ Vector Store Schema Design

### Hybrid Metadata Approach

**Decision:** Implement a hybrid approach combining dedicated fields with JSON blob for custom metadata

**Rationale:**
- **Query Performance:** Dedicated fields enable efficient filtering and indexing
- **Flexibility:** JSON blob supports arbitrary custom metadata without schema changes
- **Type Safety:** Dedicated fields provide compile-time validation for common use cases
- **Future-Proof:** New content types can be added without breaking existing data
- **Industry Standard:** 24 fields is well within production RAG system norms (typically 30-80+ fields)

**Schema Organization:**

**Core Fields (6):** Essential fields present in all chunk types
- `content`, `chunk_id`, `chunk_key`, `source_document`, `chunk_type`, `created_at`

**Content-Type Specific Fields (12):** 
- **Document fields (6):** `metadata_*`, `page_number`, `section_title`
- **Email fields (6):** `email_*` fields for sender, recipient, subject, etc.

**Custom Metadata Fields (7):**
- **JSON blob:** `custom_metadata` for arbitrary data
- **Common fields:** `language`, `domain`, `confidence`, `tags`, `priority`, `content_category`

**Design Benefits:**
- **Sparse Storage:** Unused fields don't consume significant space
- **Efficient Filtering:** Common queries use indexed dedicated fields
- **Extensibility:** New chunk types don't require schema changes
- **Backward Compatibility:** Sensible defaults prevent breaking changes

**Alternatives Considered:**
- **Pure JSON approach:** Would lose query performance benefits
- **Fully normalized:** Would require complex joins and lose simplicity
- **Separate collections:** Would complicate cross-type queries

### Content-Type Agnostic Design

**Decision:** Single collection supporting multiple content types rather than separate collections

**Rationale:**
- **Unified Search:** Enable cross-type queries (e.g., search emails and documents together)
- **Simplified Management:** Single schema to maintain and backup
- **Consistent API:** Same methods work for all content types
- **Resource Efficiency:** Shared vectorizer and indexing infrastructure

**Trade-offs:**
- **Schema Size:** 24 fields vs. smaller per-type schemas
- **Query Complexity:** Some fields irrelevant for certain content types
- **Storage:** Sparse fields still consume some space

**Mitigation Strategies:**
- Sensible defaults (empty strings, 0, null) minimize storage impact
- Weaviate handles sparse fields efficiently
- Clear field organization makes schema understandable

## 📄 Document Processing Strategy

### LaTeX Handling

**Decision:** Specialized LaTeX processing with equation preservation

**Rationale:**
- **Target Audience:** Primary use case is academic/scientific documents
- **Mathematical Content:** Equations contain critical semantic information
- **Citation Tracking:** Academic documents rely heavily on citations
- **Format Complexity:** LaTeX has specific structures that generic parsers miss

**Implementation Details:**

1. **Equation Preservation**
   - Keep mathematical equations intact (e.g., `$E = mc^2$`)
   - Preserve both inline and display equations
   - Maintain LaTeX math notation in embeddings
   
2. **Citation Strategy**
   - Extract citations as separate entities
   - Store with rich metadata (author, year, title, DOI)
   - Link citations to source chunks
   - Enable citation-based search

3. **Command Removal**
   - Strip formatting commands (`\textbf{}`, `\section{}`, etc.)
   - Preserve semantic content
   - Maintain document structure in metadata

**Citation Metadata Structure:**
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

### Chunking Strategy

**Decision:** Adaptive fixed-size chunking with configurable overlap

**Rationale:**
- **Predictability:** Fixed size ensures consistent embedding quality
- **Optimization:** Can tune chunk size for specific embedding models
- **Context:** Overlap preserves context across chunk boundaries
- **Flexibility:** Token-based with line boundary respect

**Parameters:**
- **Default Chunk Size:** 768 tokens (matches common embedding model limits)
- **Default Overlap:** 100-150 tokens (provides sufficient context)
- **Boundary Respect:** Respect line boundaries when possible

**Alternatives Considered:**
- **Semantic chunking:** More intelligent but less predictable
- **Paragraph-based:** Simple but variable sizes hurt embedding quality
- **Sentence-based:** Too granular, loses context
- **Sliding window:** More overlap but increased storage

**Object-Oriented Design:**
```python
class DataChunker:
    def __init__(self, chunk_size: int = 768, overlap: int = 100)
    def chunk_text(self, text: str) -> List[Chunk]
    def chunk_with_metadata(self, text: str, metadata: Dict) -> List[Chunk]
```

Benefits:
- Format-agnostic (works with any text)
- Easily configurable
- Reusable across different document types
- Testable in isolation

## 🔢 Embedding & Storage

### Embedding Model Selection

**Decision:** Sentence Transformers with `all-mpnet-base-v2` as default

**Rationale:**
- **Local Deployment:** No API costs or rate limits
- **Privacy:** Data never leaves your infrastructure
- **Performance:** Good balance of quality and speed
- **Dimensions:** 768 dimensions suitable for most use cases
- **Technical Content:** MPNet models perform well on scientific text

**Alternative Models:**
- `multi-qa-MiniLM-L6-v2`: Smaller, faster, optimized for Q&A
- `all-MiniLM-L12-v2`: Good general-purpose alternative
- `sentence-transformers/allenai-specter`: Specialized for scientific papers

**Configuration:**
```python
{
    "model": "all-mpnet-base-v2",
    "pooling_strategy": "mean",
    "normalize_embeddings": True
}
```

### Vector Database Choice

**Decision:** Weaviate as the vector database

**Rationale:**
- **Rich Features:** Hybrid search, filtering, graphQL API
- **Modularity:** Built-in vectorizer modules
- **Performance:** HNSW index for fast similarity search
- **Schema Flexibility:** Dynamic schema with rich property types
- **Active Development:** Regular updates and improvements
- **Open Source:** Can self-host

**Weaviate Configuration:**
```python
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

**Alternatives Considered:**
- **ChromaDB:** Simpler but less features
- **Qdrant:** Good alternative but less mature at time of decision
- **Pinecone:** Cloud-only, not suitable for self-hosted requirement
- **FAISS:** Lower-level, would need more custom implementation

## 🔍 Retrieval Strategy

### Hybrid Search

**Decision:** Support multiple search modes (vector, keyword, hybrid)

**Rationale:**
- **Flexibility:** Different queries benefit from different search strategies
- **Semantic + Exact:** Hybrid combines best of both worlds
- **Technical Terms:** Keyword search catches exact technical terms
- **Natural Language:** Vector search handles conceptual queries

**Search Modes:**

1. **Vector Search (Semantic)**
   - Dense embeddings for semantic similarity
   - Best for conceptual queries
   - Example: "What is quantum entanglement?"

2. **Keyword Search (BM25)**
   - Sparse keyword matching
   - Best for exact terms
   - Example: "Schrödinger equation"

3. **Hybrid Search**
   - Combines vector and keyword
   - Configurable alpha parameter (0.0-1.0)
   - Best for general use
   - Example: "explain machine learning algorithms"

**Alpha Parameter:**
- `alpha=1.0`: Pure vector search
- `alpha=0.0`: Pure keyword search
- `alpha=0.5`: Balanced hybrid (default)
- `alpha=0.7`: Favor semantic (recommended for most queries)

### Query Processing

**Decision:** Minimal query preprocessing

**Rationale:**
- **Preserve Intent:** Heavy preprocessing can distort query meaning
- **Technical Terms:** Preserve mathematical notation and technical terms
- **Simplicity:** Less processing means faster queries
- **Let Model Handle:** Modern embedding models handle variations well

**What We Do:**
- Preserve exact technical terms
- Keep mathematical notation
- Pass queries through largely unchanged

**What We Don't Do:**
- Heavy stemming/lemmatization
- Aggressive stopword removal
- Query expansion (let the embedding handle it)

## 🤖 Generation System

### LLM Integration

**Decision:** Support multiple LLM backends (Ollama, OpenAI, etc.)

**Rationale:**
- **Flexibility:** Users can choose based on their needs
- **Local Option:** Ollama for privacy-sensitive use cases
- **Cloud Option:** OpenAI/Anthropic for best quality
- **Cost Control:** Local models have no per-token costs

**Default: Ollama with Mistral 7B**
- Free and local
- Good performance on technical content
- 4096 token context window
- Easy to self-host

**Prompt Engineering:**
```python
def create_rag_prompt(query: str, context: List[str]) -> str:
    return f"""Based on the following context, answer the question.
    
Context:
{format_context(context)}

Question: {query}

Answer: """
```

**Design Principles:**
- Include citation information in responses
- Preserve mathematical notation
- Indicate confidence level
- Cite sources when possible

## 📊 Performance Considerations

### Chunk Size Optimization

**Decision:** Default 768 tokens with ability to configure

**Rationale:**
- **Embedding Models:** Most models work best with 512-768 tokens
- **Context Balance:** Large enough for context, small enough for relevance
- **Retrieval Quality:** Empirical testing showed good results
- **Flexibility:** Users can tune for their specific use case

**Testing Strategy:**
- Test range: 256, 512, 768, 1024 tokens
- Measure retrieval quality (MRR, Precision@K)
- Consider domain-specific optimization

### Batch Processing

**Decision:** Batch embedding and storage operations

**Rationale:**
- **Performance:** 5-10x faster than individual operations
- **GPU Utilization:** Better GPU usage with batched inference
- **Network Efficiency:** Fewer round trips to database
- **Resource Usage:** More efficient memory usage

**Implementation:**
```python
# Batch size tuned for typical GPU memory
EMBEDDING_BATCH_SIZE = 32
STORAGE_BATCH_SIZE = 100
```

## 🧪 Testing Strategy

**Decision:** Comprehensive three-tier testing approach

**Test Layers:**
1. **Unit Tests:** Individual component testing
2. **Integration Tests:** Component interaction testing
3. **End-to-End Tests:** Complete workflow testing

**Rationale:**
- **Quality Assurance:** Catch issues early
- **Refactoring Safety:** Confident code changes
- **Documentation:** Tests serve as usage examples
- **CI/CD:** Automated testing in pipeline

For more details, see [testing.md](testing.md).

## 🔄 Future Considerations

### Planned Improvements

1. **Multi-modal Support:** Images, tables, diagrams
2. **Advanced Chunking:** Semantic chunking options
3. **Fine-tuning:** Domain-specific embedding models
4. **Caching:** Query result caching
5. **Streaming:** Streaming LLM responses

### Extensibility Points

- Plugin system for custom document processors
- Custom embedding model integration
- Alternative vector database backends
- Custom retrieval algorithms

## 🔗 Related Documentation

- [Architecture](architecture.md) - System architecture overview
- [Getting Started](getting_started.md) - Setup and usage guide
- [Testing](testing.md) - Testing guidelines

