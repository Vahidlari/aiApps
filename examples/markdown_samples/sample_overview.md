# Markdown Processing Overview

## Introduction

This sample Markdown document demonstrates how Ragora processes Markdown
content alongside LaTeX and plain text sources. It includes headings,
paragraphs, lists, and code blocks so the parser can exercise multiple
structures.

## Key Capabilities

- Parse Markdown using `markdown-it-py`
- Preserve headings as chunk metadata
- Handle bullet and numbered lists
- Support fenced code blocks

### Sample Code Snippet

```python
def ragora_highlight(feature: str) -> str:
    """Return a short description of a Ragora feature."""
    return f"Ragora excels at {feature}."
```

## Summary

Ragora now supports Markdown ingestion through the knowledge base manager, making
it easier to mix documentation sources with scientific papers or notes.

