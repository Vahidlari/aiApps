"""Tests for the MarkdownParser utility."""

from pathlib import Path

import pytest

from ragora.utils.markdown_parser import MarkdownParser


@pytest.fixture
def parser() -> MarkdownParser:
    """Return a configured MarkdownParser instance for tests."""

    return MarkdownParser()


def test_parse_markdown_document_structure(tmp_path: Path, parser: MarkdownParser):
    """Markdown documents should produce chapters, sections, and paragraphs."""

    markdown_content = """# Sample Title

## Overview

This is an introduction paragraph.

- Bullet item one
- Bullet item two

```python
print("hello world")
```
"""

    markdown_path = tmp_path / "sample.md"
    markdown_path.write_text(markdown_content, encoding="utf-8")

    document = parser.parse_document(str(markdown_path))

    assert document.source_document == markdown_path.name
    assert document.title == markdown_path.stem
    assert document.chapters and document.chapters[0].title == "Sample Title"

    chapter = document.chapters[0]
    assert chapter.sections and chapter.sections[0].title == "Overview"

    section = chapter.sections[0]
    section_text = [paragraph.content for paragraph in section.paragraphs]
    assert "This is an introduction paragraph." in section_text
    assert any(text.startswith("- Bullet item") for text in section_text)
    assert any("```" in text for text in section_text)


def test_parse_plain_text_document(tmp_path: Path, parser: MarkdownParser):
    """Plain text should be parsed into top-level paragraphs."""

    plain_text = "Plain text paragraph one.\n\nPlain text paragraph two."
    text_path = tmp_path / "notes.txt"
    text_path.write_text(plain_text, encoding="utf-8")

    document = parser.parse_document(str(text_path))

    paragraphs = [paragraph.content for paragraph in document.paragraphs]
    assert len(paragraphs) == 2
    assert "Plain text paragraph one." in paragraphs[0]
    assert "Plain text paragraph two." in paragraphs[1]
    assert document.chapters == []
    assert document.sections == []
