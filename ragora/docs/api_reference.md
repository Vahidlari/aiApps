# API Reference

This document provides an overview of the Ragora API. Detailed API documentation will be generated automatically from code docstrings using Sphinx by the next release of the package.


## 🎯 Quick API Overview

### Core Modules

#### `ragora.KnowledgeBaseManager`

Main entry point for retrieval operations.

```python
from ragora import KnowledgeBaseManager

kbm = KnowledgeBaseManager(
    weaviate_url: str,
    class_name: str,
    embedding_model: str = "all-mpnet-base-v2",
    chunk_size: int = 768,
    chunk_overlap: int = 100
)
```

**Key Methods:**
- `process_documents(file_paths: List[str]) -> List[str]` - Process documents
- `query(query: str, search_type: str, top_k: int) -> Dict` - Query knowledge base
- `get_system_stats() -> Dict` - Get system statistics
- `check_new_emails(email_provider, folder=None, include_body=True, limit=50) -> Dict` - Check for new emails
- `process_new_emails(email_provider, email_ids, class_name="Email") -> List[str]` - Process specific emails
- `process_email_account(email_provider, folder=None, unread_only=False, class_name="Email") -> List[str]` - Bulk email processing
- `search_emails(query, search_type="similar", top_k=5, class_name="Email") -> List[Dict]` - Search emails

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

Document storage operations.

```python
from ragora.core import VectorStore

vector_store = VectorStore(
    db_manager: DatabaseManager,
    class_name: str
)
```

**Key Methods:**
- `store_chunks(chunks: List[Chunk]) -> List[str]` - Store document chunks
- `get_chunk(chunk_id: str) -> Optional[Chunk]` - Retrieve a chunk
- `update_chunk(chunk_id: str, data: Dict) -> None` - Update chunk
- `delete_chunk(chunk_id: str) -> None` - Delete chunk
- `get_stats() -> Dict` - Get storage statistics

#### `ragora.core.Retriever`

Search and retrieval operations.

```python
from ragora.core import Retriever

retriever = Retriever(
    db_manager: DatabaseManager,
    class_name: str
)
```

**Key Methods:**
- `search_similar(query: str, top_k: int) -> List[Dict]` - Semantic search
- `search_keyword(query: str, top_k: int) -> List[Dict]` - Keyword search
- `search_hybrid(query: str, alpha: float, top_k: int) -> List[Dict]` - Hybrid search
- `search_with_filter(query: str, filters: Dict, top_k: int) -> List[Dict]` - Filtered search

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
    weaviate_url="http://localhost:8080",
    class_name="Documents"
)

# Process and query
kbm.process_documents(["document.tex"])
results = kbm.query("What is quantum mechanics?", search_type="hybrid")
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
results = kbm.search_emails("meeting notes", top_k=5)
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
store = VectorStore(db, "MyDocs")
retriever = Retriever(db, "MyDocs")
embedder = EmbeddingEngine("all-mpnet-base-v2")
email_preprocessor = EmailPreprocessor()

# Use components
results = retriever.search_similar("query", top_k=5)
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