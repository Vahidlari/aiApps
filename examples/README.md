# Ragora Examples

This directory contains practical examples demonstrating how to use Ragora for various RAG (Retrieval-Augmented Generation) tasks.

## 📋 Available Examples

### 1. LaTeX Document Loading (`latex_loading_example.py`)

Demonstrates how to process and load LaTeX documents into the knowledge base.

**What it does:**
- Parses LaTeX documents with bibliography
- Extracts sections, equations, and citations
- Chunks documents into manageable pieces
- Stores processed content in vector database

**Run:**
```bash
python latex_loading_example.py
```

### 2. LaTeX Document Retrieval (`latex_retriever_example.py`)

Shows how to search and retrieve information from processed documents.

**What it does:**
- Performs semantic search on processed documents
- Demonstrates different search modes (vector, keyword, hybrid)
- Shows how to filter results by metadata
- Displays relevance scores and content

**Run:**
```bash
python latex_retriever_example.py
```

### 3. Advanced Usage (`advanced_usage.py`)

Illustrates advanced features and custom pipelines.

**What it demonstrates:**
- Building custom RAG pipelines
- Using individual components directly
- Configuring embedding models
- Custom chunking strategies
- Batch processing optimization

**Run:**
```bash
cd ragora/examples
python advanced_usage.py
```

### 4. Email Integration (`email_usage_examples.py`)

Examples of integrating Ragora with email systems.

**What it covers:**
- IMAP email provider
- Microsoft Graph API integration
- Processing email content
- Building email-based knowledge bases

**Run:**
```bash
cd ragora/examples
python email_usage_examples.py
```

## 🚀 Prerequisites

### 1. Install Ragora

```bash
# From PyPI
pip install ragora

# Or from source (development)
cd ragora
pip install -e .
```

### 2. Start Weaviate Database

The examples require a running Weaviate instance. Download the pre-configured database server from releases:

```bash
# Download from GitHub releases
wget https://github.com/vahidlari/ragora-core/releases/latest/download/ragora-database-server.tar.gz

# Extract and start
tar -xzf ragora-database-server.tar.gz
cd ragora-database-server
./database-manager.sh start
```

Verify Weaviate is running:
```bash
./database-manager.sh status
# Or check directly:
curl http://localhost:8080/v1/.well-known/ready
```

**Note:** If you're developing in this repository, you can use the database server from `tools/database_server/` directly.

### 3. Configure Connection

Most examples default to `http://localhost:8080` for Weaviate. If your setup is different, update the connection URL:

```python
# In the example files, modify:
kbm = KnowledgeBaseManager(
    weaviate_url="http://your-weaviate-host:8080",  # Update this
    class_name="Documents"
)
```

**Note for DevContainer Users:** If running examples inside a DevContainer while Weaviate runs on the host machine, use `http://host.docker.internal:8080` as the Weaviate URL.

## 📖 Usage Guide

### Running Your First Example

1. **Ensure Weaviate is running:**
   ```bash
   cd tools/database_server
   ./database-manager.sh status
   ```

2. **Navigate to examples directory:**
   ```bash
   cd examples
   ```

3. **Run the loading example:**
   ```bash
   python latex_loading_example.py
   ```

4. **Run the retrieval example:**
   ```bash
   python latex_retriever_example.py
   ```

### Sample LaTeX Files

The `latex_samples/` directory contains sample files for testing:

- **`sample_chapter.tex`**: A sample LaTeX chapter with sections and equations
- **`references.bib`**: Sample bibliography file with citations

You can use these files to test the examples without preparing your own documents.

### Customizing Examples

#### Change Document Paths

```python
# Modify file paths in the examples
document_paths = [
    "path/to/your/document1.tex",
    "path/to/your/document2.tex"
]
```

#### Adjust Chunking Parameters

```python
# Modify chunk size and overlap
kbm = KnowledgeBaseManager(
    weaviate_url="http://localhost:8080",
    chunk_size=512,   # Smaller chunks
    chunk_overlap=50  # Less overlap
)
```

#### Try Different Search Modes

```python
# Semantic search (conceptual similarity)
results = kbm.query("quantum mechanics", search_type="similar")

# Keyword search (exact matches)
results = kbm.query("Schrödinger equation", search_type="keyword")

# Hybrid search (combines both - recommended)
results = kbm.query("wave function", search_type="hybrid", alpha=0.7)
```

#### Change Embedding Models

```python
# Use a different embedding model
kbm = KnowledgeBaseManager(
    weaviate_url="http://localhost:8080",
    embedding_model="all-MiniLM-L6-v2"  # Smaller, faster model
)
```

## 🔧 Troubleshooting

### Common Issues

**Issue: "Cannot connect to Weaviate"**

```bash
# Check if Weaviate is running
curl http://localhost:8080/v1/.well-known/ready

# If not running, start it
cd tools/database_server
./database-manager.sh start

# Check logs if issues persist
./database-manager.sh logs
```

**Issue: "Module 'ragora' not found"**

```bash
# Ensure Ragora is installed
pip list | grep ragora

# Install if needed
pip install ragora

# Or install from source
cd ragora
pip install -e .
```

**Issue: "Connection refused" in DevContainer**

If running examples in a DevContainer but Weaviate is on the host:

```python
# Use host.docker.internal instead of localhost
kbm = KnowledgeBaseManager(
    weaviate_url="http://host.docker.internal:8080",
    class_name="Documents"
)
```

**Issue: "Out of memory" during processing**

```python
# Reduce batch size or use smaller embedding model
kbm = KnowledgeBaseManager(
    weaviate_url="http://localhost:8080",
    embedding_model="all-MiniLM-L6-v2",  # Smaller model
    chunk_size=512  # Smaller chunks
)
```

**Issue: "Poor search results"**

```python
# Try different search modes or adjust hybrid alpha
results = kbm.query(
    "your query",
    search_type="hybrid",
    alpha=0.7,  # Try values between 0.5-0.9
    top_k=10    # Return more results
)
```

## 📚 Expected Output

### Document Loading Example

```
Processing documents...
✓ Parsed document: sample_chapter.tex
✓ Extracted 3 sections
✓ Found 5 equations
✓ Identified 8 citations
✓ Generated 24 chunks
✓ Stored in vector database

Total chunks processed: 24
```

### Retrieval Example

```
Querying: "What is quantum entanglement?"

Results:
1. Score: 0.892
   Content: Quantum entanglement is a physical phenomenon that occurs when...
   Source: sample_chapter.tex, Section 2.1

2. Score: 0.847
   Content: The phenomenon of entanglement was first described by Einstein...
   Source: sample_chapter.tex, Section 2.3

3. Score: 0.823
   Content: Entangled particles remain connected regardless of distance...
   Source: sample_chapter.tex, Section 2.2

Found 3 relevant results
```

## 🎯 Next Steps

After running the examples, you can:

1. **Explore the Code**: Read through the example files to understand the implementation
2. **Modify Examples**: Adapt the examples to your specific use case
3. **Read Documentation**: Check [`ragora/docs/`](../ragora/docs/) for detailed guides
4. **Build Your Own**: Create custom RAG applications using Ragora

## 📖 Additional Resources

- **[Getting Started Guide](../ragora/docs/getting_started.md)**: Comprehensive setup guide
- **[Architecture Overview](../ragora/docs/architecture.md)**: Understanding Ragora's design
- **[API Reference](../ragora/docs/api-reference.md)**: Complete API documentation
- **[Main Repository](../README.md)**: Repository overview and setup

## 🆘 Getting Help

If you encounter issues or have questions:

- **Check Documentation**: See [ragora/docs/](../ragora/docs/)
- **Review Issues**: Search [GitHub Issues](https://github.com/vahidlari/ragora-core/issues)
- **Ask Questions**: Start a [GitHub Discussion](https://github.com/vahidlari/ragora-core/discussions)
- **Report Bugs**: Create a new issue with detailed information

## 🤝 Contributing Examples

Have a useful example to share? We'd love to include it! See [contributing.md](../ragora/docs/contributing.md) for guidelines on contributing.
