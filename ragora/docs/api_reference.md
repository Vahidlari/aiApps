# API Reference

This document provides an overview of the Ragora APIs. Detailed API documentation will be generated automatically from code docstrings using Sphinx by the next releases of the package.


## 🎯 Quick API Overview

### Core Modules

#### `ragora.KnowledgeBaseManager`

Main entry point for retrieval operations.

```python
from ragora import KnowledgeBaseManager

kbm = KnowledgeBaseManager(
    config: Optional[KnowledgeBaseManagerConfig] = None,
    weaviate_url: str = "http://localhost:8080"
)
```

Arguments

- **config**: Optional `KnowledgeBaseManagerConfig` that customizes the underlying components. When provided, it is used to instantiate and configure:
  - Embedding engine (model, device, max length)
  - Chunking strategy (chunk size, overlap, type)
  - Database manager (URL, timeouts, retries)
  If omitted, sensible defaults are used.
- **weaviate_url**: Base URL for the Weaviate instance. Used when `config.database_manager_config` is not specified.

About KnowledgeBaseManagerConfig

`KnowledgeBaseManagerConfig` lets you declaratively configure the system. Its fields are optional; supply only what you want to override.

- `chunk_config: ChunkConfig`
  - `chunk_size` (int, default 768): Target characters per chunk
  - `overlap_size` (int, default 100): Characters of overlap between chunks
  - `chunk_type` (str, default "document"): Default strategy kind
  Effect: Creates a `DocumentChunkingStrategy` with your sizes and wires it into `DataChunker` used by preprocessors.

- `embedding_config: EmbeddingConfig`
  - `model_name` (str, default "all-mpnet-base-v2"): Sentence-transformers model
  - `device` (Optional[str], default None): e.g., "cuda", "cpu"; auto if None
  - `max_length` (int, default 512): Truncation length for inputs
  Effect: Initializes `EmbeddingEngine` accordingly and passes it to `VectorStore` and `Retriever`.

- `database_manager_config: DatabaseManagerConfig`
  - `url` (str, default "http://localhost:8080"): Weaviate URL
  - `grpc_port` (int, default 50051)
  - `timeout` (int, default 30)
  - `retry_attempts` (int, default 3)
  Effect: Configures `DatabaseManager` connectivity used by `VectorStore` and `Retriever`.

Key Methods (brief)

- `process_document(document_path, document_type="latex", collection="Document") -> List[str]`
  Parses, chunks, embeds, and stores a single document. Returns stored chunk IDs.
- `process_documents(document_paths, document_type="latex", collection="Document") -> List[str]`
  Batch variant for multiple documents; returns all stored chunk IDs.
- `search(query, collection="Document", strategy=SearchStrategy.HYBRID, top_k=5, filter: Optional[Filter] = None, **kwargs) -> SearchResult`
  Unified retrieval with SIMILAR (vector), KEYWORD (BM25), or HYBRID strategies. Optional `filter` parameter allows filtering results by properties (e.g., chunk type, date ranges, source documents). Returns rich `SearchResult` with timing and totals.
- `get_chunk(chunk_id: str, collection: str) -> Optional[RetrievalResultItem]`
  Retrieve a specific chunk by its ID. Returns structured `RetrievalResultItem` with content, metadata, and properties.
- `get_collection_stats(collection: str) -> Dict`
  Aggregated statistics for the specified collection (e.g., counts, schema info).
- `check_new_emails(email_provider, folder=None, include_body=True, limit=50) -> Dict`
  Lists new emails from the provider with optional body retrieval; does not store.
- `process_new_emails(email_provider, email_ids, collection="Email") -> List[str]`
  Fetches specified emails, chunks, embeds, and stores them; returns chunk IDs.
- `process_email_account(email_provider, folder=None, unread_only=False, collection="Email") -> List[str]`
  Scans a mailbox (optionally unread only) and stores processed email chunks.


#### `ragora.core.DatabaseManager`

Low-level database operations.

```python
from ragora.core import DatabaseManager

db_manager = DatabaseManager(url: str)
```

**Key Methods:**
- `connect() -> None` - Establish database connection
- `create_collection(name: str, schema: Dict) -> None` - Create collection
- `delete_collection(name: str) -> None` - Delete collection
- `get_client() -> weaviate.Client` - Get Weaviate client

#### `ragora.core.VectorStore`

Document storage operations with support for multiple content types and flexible metadata.

```python
from ragora.core import VectorStore

vector_store = VectorStore(
    db_manager: DatabaseManager,
    embedding_engine: Optional[EmbeddingEngine] = None,
    collection: str = "Document"
)
```

**Schema Fields:**

The vector store supports 24 fields organized into categories:

**Core Fields (6):**
- `content` - The actual chunk content
- `chunk_id` - Deterministic chunk identifier
- `chunk_key` - UUID5 for Weaviate operations
- `source_document` - Source file/document name
- `chunk_type` - Content type (text, document, email, etc.)
- `created_at` - Creation timestamp

**Document-Specific Fields (6):**
- `metadata_chunk_idx` - Chunk index in sequence
- `metadata_chunk_size` - Chunk size in characters
- `metadata_total_chunks` - Total chunks in document
- `metadata_created_at` - Created at timestamp from metadata
- `page_number` - Page number in source document
- `section_title` - Section or chapter title

**Email-Specific Fields (6):**
- `email_subject` - Email subject line
- `email_sender` - Email sender address
- `email_recipient` - Email recipient address
- `email_date` - Email timestamp
- `email_id` - Unique email identifier
- `email_folder` - Email folder/path

**Custom Metadata Fields (7):**
- `custom_metadata` - Custom metadata as JSON string
- `language` - Content language (e.g., en, es, fr)
- `domain` - Content domain (e.g., scientific, legal, medical)
- `confidence` - Processing confidence score (0.0-1.0)
- `tags` - Comma-separated tags/categories
- `priority` - Content priority/importance level
- `content_category` - Fine-grained content categorization

**Key Methods:**
- `store_chunks(chunks: List[Chunk]) -> List[str]` - Store document chunks
- `get_chunk_by_id(chunk_id: str, collection: str) -> Optional[RetrievalResultItem]` - Retrieve a chunk by ID
- `update_chunk(chunk_id: str, properties: Dict, collection: str) -> bool` - Update chunk
- `delete_chunk(chunk_id: str, collection: str) -> bool` - Delete chunk
- `get_stats(collection: str) -> Dict` - Get storage statistics
- `create_schema(collection: str, force_recreate: bool) -> None` - Create collection schema

### Custom Metadata Support

The vector store supports flexible metadata through a hybrid approach:
- **JSON blob**: Store any custom metadata as JSON string in `custom_metadata` field
- **Common fields**: Extract frequently-queried fields for efficient filtering

**Example Usage:**

```python
from ragora import ChunkingContextBuilder, DataChunker

# Create chunker
chunker = DataChunker()

# Document with custom metadata
context = (ChunkingContextBuilder()
    .for_document()
    .with_source("research_paper.pdf")
    .with_custom_metadata({
        "language": "en",
        "domain": "scientific",
        "confidence": 0.95,
        "tags": ["physics", "relativity"],
        "priority": 5,
        "content_category": "research_paper",
        "author": "Einstein",
        "year": 1905
    })
    .build())

chunks = chunker.chunk(document_text, context)

# Store chunks - custom metadata will be automatically handled
vector_store.store_chunks(chunks, "Document")
```

**Email Example:**

```python
# Email with full metadata
context = (ChunkingContextBuilder()
    .for_email()
    .with_email_info(
        subject="Project Update",
        sender="manager@company.com",
        recipient="team@company.com",
        email_id="msg_12345",
        email_date="2024-01-15T14:30:00Z",
        email_folder="work"
    )
    .with_custom_metadata({
        "language": "en",
        "domain": "business",
        "priority": 3,
        "tags": ["project", "update"]
    })
    .build())

chunks = chunker.chunk(email_body, context)
vector_store.store_chunks(chunks, "Email")
```

#### `ragora.core.Retriever`

Search and retrieval operations.

```python
from ragora.core import Retriever

retriever = Retriever(
    db_manager: DatabaseManager,
    embedding_engine: Optional[EmbeddingEngine] = None
)
```

**Key Methods:**
- `search_similar(query: str, collection: str, top_k: int, filter: Optional[Filter] = None) -> List[SearchResultItem]` - Semantic search with optional filter
- `search_keyword(query: str, collection: str, top_k: int, filter: Optional[Filter] = None) -> List[SearchResultItem]` - Keyword search with optional filter
- `search_hybrid(query: str, collection: str, alpha: float, top_k: int, filter: Optional[Filter] = None) -> List[SearchResultItem]` - Hybrid search with optional filter

**Return Types:**

The retriever methods return structured Pydantic models:

- **`RetrievalResultItem`** (base class): Base class for chunk retrieval results
  - `content: str` - Text content of the chunk
  - `chunk_id: str` - Unique chunk identifier
  - `properties: Dict[str, Any]` - All stored properties from the vector database
  - `metadata: RetrievalMetadata` - Structured metadata (source, page, email fields, etc.)

- **`SearchResultItem`** (extends `RetrievalResultItem`): Search results with scores
  - Inherits all fields from `RetrievalResultItem`
  - `similarity_score: float` - Similarity score (0.0-1.0)
  - `retrieval_method: str` - Method used ("vector_similarity", "hybrid_search", "keyword_search")
  - `retrieval_timestamp: datetime` - When retrieval occurred
  - Additional score fields: `distance`, `hybrid_score`, `bm25_score`

**Example Usage:**

```python
# Direct chunk retrieval returns RetrievalResultItem
chunk = kbm.get_chunk("chunk_123", "Document")
if chunk:
    print(chunk.content)
    print(chunk.metadata.source_document)

# Search returns SearchResultItem (extends RetrievalResultItem)
results = kbm.search("query", collection="Document")
for result in results.results:
    print(result.content)  # Base class field
    print(result.similarity_score)  # Search-specific field
```

#### `ragora.FilterBuilder`

Helper class for constructing Weaviate filters using domain model semantics.

```python
from ragora import FilterBuilder
from weaviate.classes.query import Filter
```

**Overview:**

FilterBuilder provides convenience methods for creating Weaviate Filter objects that align with your domain model (`RetrievalMetadata`, `DataChunk`). This eliminates the need to know exact Weaviate property names and makes filtering more intuitive.

**Key Methods:**

**Simple Filters:**
- `by_chunk_type(value: str) -> Filter` - Filter by chunk type (e.g., "text", "equation")
- `by_source_document(value: str) -> Filter` - Filter by source document filename
- `by_page_number(value: int) -> Filter` - Filter by page number
- `by_section_title(value: str) -> Filter` - Filter by section/chapter title
- `by_chunk_idx(value: int) -> Filter` - Filter by chunk index

**Email Filters:**
- `by_email_sender(value: str) -> Filter` - Filter by email sender address
- `by_email_subject(value: str) -> Filter` - Filter by email subject
- `by_email_recipient(value: str) -> Filter` - Filter by email recipient
- `by_email_folder(value: str) -> Filter` - Filter by email folder

**Date Range Filters:**
- `by_date_range(start: Optional[str] = None, end: Optional[str] = None) -> Optional[Filter]` - Filter by creation date range
- `by_email_date_range(start: Optional[str] = None, end: Optional[str] = None) -> Optional[Filter]` - Filter by email date range

**Combination Methods:**
- `combine_and(*filters: Filter) -> Filter` - Combine filters with AND logic
- `combine_or(*filters: Filter) -> Filter` - Combine filters with OR logic

**Example Usage:**

```python
from ragora import KnowledgeBaseManager, FilterBuilder, SearchStrategy

kbm = KnowledgeBaseManager()

# Simple filter: only text chunks
filter = FilterBuilder.by_chunk_type("text")
results = kbm.search("machine learning", filter=filter)

# Date range filter: documents from 2024
date_filter = FilterBuilder.by_date_range(start="2024-01-01", end="2024-12-31")
results = kbm.search("quantum mechanics", filter=date_filter)

# Combined filter: text chunks from specific document
type_filter = FilterBuilder.by_chunk_type("text")
doc_filter = FilterBuilder.by_source_document("research.pdf")
combined = FilterBuilder.combine_and(type_filter, doc_filter)
results = kbm.search("research findings", filter=combined)

# Email filters
email_filter = FilterBuilder.by_email_sender("colleague@example.com")
results = kbm.search("project update", collection="Email", filter=email_filter)

# Using raw Weaviate Filter (advanced)
from weaviate.classes.query import Filter
raw_filter = Filter.by_property("chunk_type").equal("text")
results = kbm.search("query", filter=raw_filter)
```

**Filter Properties Available:**

The following Weaviate properties can be filtered (mapped by FilterBuilder):

- **Text properties**: `chunk_type`, `source_document`, `created_at`, `section_title`, `email_subject`, `email_sender`, `email_recipient`, `email_date`, `email_folder`
- **Integer properties**: `metadata_chunk_idx`, `metadata_chunk_size`, `metadata_total_chunks`, `page_number`

For advanced filtering needs, you can use Weaviate's Filter API directly. See [Weaviate Filter Documentation](https://weaviate.io/developers/weaviate/search/filters) for more details.

#### `ragora.core.DocumentPreprocessor`

Document parsing and preprocessing.

```python
from ragora.core import DocumentPreprocessor

preprocessor = DocumentPreprocessor()
```

**Key Methods:**
- `parse_latex(file_path: str, bib_path: Optional[str]) -> Document` - Parse LaTeX
- `extract_citations(content: str) -> List[Citation]` - Extract citations
- `clean_text(text: str) -> str` - Clean text content

#### `ragora.core.EmailPreprocessor`

Email preprocessing for RAG system.

```python
from ragora.core import EmailPreprocessor

preprocessor = EmailPreprocessor()
```

**Key Methods:**
- `preprocess_email(email: EmailMessage, start_sequence_idx: int = 0) -> List[DataChunk]` - Process single email
- `preprocess_emails(emails: List[EmailMessage], start_sequence_idx: int = 0) -> List[DataChunk]` - Process multiple emails

#### `ragora.core.DataChunker`

Text chunking operations.

```python
from ragora.core import DataChunker, ChunkingContextBuilder

chunker = DataChunker()
context = ChunkingContextBuilder().for_document().build()
chunks = chunker.chunk(text, context)
```

**Key Methods:**
- `chunk(text: str, context: ChunkingContext) -> List[DataChunk]` - Chunk text with context
- `register_strategy(chunk_type: str, strategy: ChunkingStrategy)` - Register custom strategy

#### `ragora.core.EmbeddingEngine`

Vector embedding generation.

```python
from ragora.core import EmbeddingEngine

embedder = EmbeddingEngine(
    model_name: str = "all-mpnet-base-v2",
    device: str = "cpu",
    batch_size: int = 32
)
```

**Key Methods:**
- `embed_text(text: str) -> np.ndarray` - Embed single text
- `embed_batch(texts: List[str]) -> List[np.ndarray]` - Embed multiple texts

### Utility Modules

#### `ragora.utils.latex_parser`

LaTeX parsing utilities.

**Key Functions:**
- `parse_latex_file(file_path: str) -> Dict` - Parse LaTeX file
- `extract_equations(content: str) -> List[str]` - Extract equations
- `clean_latex_commands(content: str) -> str` - Remove LaTeX commands

#### `ragora.utils.device_utils`

Device detection utilities.

**Key Functions:**
- `get_device() -> str` - Get optimal device (cuda/cpu)
- `is_cuda_available() -> bool` - Check CUDA availability

#### `ragora.utils.email_utils`

Email integration utilities.

**Key Classes:**
- `EmailProvider` - Abstract base class for email providers
- `IMAPProvider` - IMAP email provider implementation
- `GraphProvider` - Microsoft Graph email provider implementation
- `EmailProviderFactory` - Factory for creating email providers

**Key Models:**
- `EmailMessage` - Email message data model
- `EmailAddress` - Email address data model
- `IMAPCredentials` - IMAP connection credentials
- `GraphCredentials` - Microsoft Graph connection credentials

**Key Functions:**
- `create_provider(provider_type: ProviderType, credentials: EmailCredentials) -> EmailProvider` - Create email provider

### Configuration

#### `ragora.config.settings`

Configuration management.

```python
from ragora.config import Settings

settings = Settings()
```

## 📖 Usage Examples

### Example 1: Basic RAG Pipeline

```python
from ragora import KnowledgeBaseManager

# Initialize
kbm = KnowledgeBaseManager(
    weaviate_url="http://localhost:8080"
)

# Process and query
kbm.process_documents(["document.tex"])  # stores into collection "Document" by default
results = kbm.search("What is quantum mechanics?", collection="Document", strategy=SearchStrategy.HYBRID, top_k=5)
```

### Example 2: Email Knowledge Base

```python
from ragora import KnowledgeBaseManager
from ragora.utils.email_utils import EmailProviderFactory, ProviderType, IMAPCredentials

# Setup email provider
credentials = IMAPCredentials(
    imap_server="imap.gmail.com",
    username="user@gmail.com",
    password="app_password"
)
email_provider = EmailProviderFactory.create_provider(ProviderType.IMAP, credentials)

# Initialize knowledge base
kbm = KnowledgeBaseManager(weaviate_url="http://localhost:8080")

# Check for new emails
new_emails = kbm.check_new_emails(email_provider, folder="INBOX", limit=10)

# Process specific emails
email_ids = [email["email_id"] for email in new_emails["emails"][:5]]
stored_ids = kbm.process_new_emails(email_provider, email_ids)

# Search emails
results = kbm.search("meeting notes", collection="Email", top_k=5)
```

### Example 3: Custom Component Usage

```python
from ragora.core import (
    DatabaseManager,
    VectorStore,
    Retriever,
    EmbeddingEngine,
    EmailPreprocessor
)

# Setup components
db = DatabaseManager("http://localhost:8080")
store = VectorStore(db, collection="MyDocs")
embedder = EmbeddingEngine(model_name="all-mpnet-base-v2")
retriever = Retriever(db, embedding_engine=embedder)
email_preprocessor = EmailPreprocessor()

# Use components
results = retriever.search_similar("query", collection="MyDocs", top_k=5)
```

## 🔍 Data Models

### Chunk

```python
@dataclass
class Chunk:
    content: str
    metadata: Dict[str, Any]
    chunk_id: Optional[str] = None
    embedding: Optional[np.ndarray] = None
```

### Document

```python
@dataclass
class Document:
    title: str
    sections: List[Section]
    citations: List[Citation]
    metadata: Dict[str, Any]
```

### Citation

```python
@dataclass
class Citation:
    author: str
    year: int
    title: str
    doi: Optional[str]
    content: Optional[str]
```

### EmailMessage

```python
@dataclass
class EmailMessage:
    message_id: str
    subject: str
    sender: EmailAddress
    recipients: List[EmailAddress]
    body_text: Optional[str]
    body_html: Optional[str]
    date_sent: Optional[datetime]
    attachments: List[Attachment]
    thread_id: Optional[str]
    conversation_id: Optional[str]
    folder: Optional[str]
    metadata: Dict[str, Any]
```

### EmailAddress

```python
@dataclass
class EmailAddress:
    email: str
    name: Optional[str]
```

## 🔗 Related Documentation

- [Getting Started](getting_started.md) - Setup and basic usage
- [Architecture](architecture.md) - System architecture
- [Design Decisions](design_decisions.md) - Design rationale
- [Examples](../../../examples/) - Usage examples

## 📝 Note on Sphinx Documentation

This is a high-level overview. For detailed API documentation with all parameters, return types, and examples, please refer to the Sphinx-generated documentation or the inline docstrings in the source code.

To view docstrings directly:

```python
from ragora import KnowledgeBaseManager
help(KnowledgeBaseManager)

from ragora.core import Retriever
help(Retriever.search_hybrid)
```