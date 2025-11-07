"""Markdown and plain text parser utilities for Ragora.

This module provides lightweight parsing utilities that leverage the
``markdown-it-py`` package to convert Markdown or plain text documents into
structured representations that can be consumed by the document preprocessor
module.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import List, Optional

from markdown_it import MarkdownIt

logger = logging.getLogger(__name__)


@dataclass
class MarkdownParagraph:
    """Represents a paragraph or block of text within a Markdown document."""

    content: str


@dataclass
class MarkdownSection:
    """Represents a Markdown section (heading level >= 2)."""

    title: str
    level: int
    paragraphs: List[MarkdownParagraph] = field(default_factory=list)


@dataclass
class MarkdownChapter:
    """Represents a top-level Markdown heading (level 1)."""

    title: str
    paragraphs: List[MarkdownParagraph] = field(default_factory=list)
    sections: List[MarkdownSection] = field(default_factory=list)


@dataclass
class MarkdownDocument:
    """Structured representation of a Markdown/plain text document."""

    source_document: str
    title: Optional[str] = None
    paragraphs: List[MarkdownParagraph] = field(default_factory=list)
    chapters: List[MarkdownChapter] = field(default_factory=list)
    sections: List[MarkdownSection] = field(default_factory=list)


class MarkdownParser:
    """Parser that converts Markdown or plain text into structured objects."""

    def __init__(self, enable_tables: bool = True, enable_fenced_code: bool = True):
        self._markdown = MarkdownIt("commonmark")
        if enable_tables:
            self._markdown.enable("table")
        if enable_fenced_code:
            self._markdown.enable("fence")

    def parse_document(self, file_path: str) -> MarkdownDocument:
        """Parse a Markdown document from disk."""

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Markdown file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()

        return self.parse_text(content, source_document=os.path.basename(file_path))

    def parse_text(self, text: str, source_document: Optional[str] = None) -> MarkdownDocument:
        """Parse provided Markdown/plain text content."""

        source_name = source_document or ""
        default_title = (
            os.path.splitext(os.path.basename(source_name))[0]
            if source_name
            else None
        )
        document = MarkdownDocument(source_document=source_name, title=default_title)

        tokens = self._markdown.parse(text)
        current_chapter: Optional[MarkdownChapter] = None
        current_section: Optional[MarkdownSection] = None
        block_context: Optional[str] = None
        blockquote_level = 0
        list_stack: List[dict] = []
        in_list_item = False

        def add_paragraph(raw_text: str):
            text_to_add = raw_text.strip()
            if not text_to_add:
                return

            if blockquote_level:
                prefix = "> " * blockquote_level
                text_to_add = f"{prefix}{text_to_add}"

            paragraph = MarkdownParagraph(content=text_to_add)

            if current_section is not None:
                current_section.paragraphs.append(paragraph)
            elif current_chapter is not None:
                current_chapter.paragraphs.append(paragraph)
            else:
                document.paragraphs.append(paragraph)

        index = 0
        while index < len(tokens):
            token = tokens[index]

            if token.type == "heading_open":
                level = int(token.tag[-1]) if token.tag and token.tag[-1].isdigit() else 1
                title = ""
                lookahead = index + 1
                while lookahead < len(tokens) and tokens[lookahead].type != "heading_close":
                    if tokens[lookahead].type == "inline":
                        title = tokens[lookahead].content.strip()
                    lookahead += 1

                if level <= 1:
                    current_chapter = MarkdownChapter(title=title)
                    document.chapters.append(current_chapter)
                    current_section = None
                    if not document.title:
                        document.title = title
                elif level == 2:
                    section = MarkdownSection(title=title, level=level)
                    if current_chapter is not None:
                        current_chapter.sections.append(section)
                    else:
                        document.sections.append(section)
                    current_section = section
                else:
                    add_paragraph(f"{'#' * level} {title}")

                index = lookahead  # Skip inline tokens handled above
                block_context = None
            elif token.type == "paragraph_open":
                block_context = "paragraph"
            elif token.type == "paragraph_close":
                block_context = None
            elif token.type == "blockquote_open":
                blockquote_level += 1
            elif token.type == "blockquote_close":
                blockquote_level = max(0, blockquote_level - 1)
            elif token.type == "bullet_list_open":
                list_stack.append({"type": "bullet"})
            elif token.type == "bullet_list_close":
                if list_stack:
                    list_stack.pop()
            elif token.type == "ordered_list_open":
                start_attr = token.attrGet("start")
                start_index = int(start_attr) if start_attr else 1
                list_stack.append({"type": "ordered", "index": start_index})
            elif token.type == "ordered_list_close":
                if list_stack:
                    list_stack.pop()
            elif token.type == "list_item_open":
                block_context = "list_item"
                in_list_item = True
            elif token.type == "list_item_close":
                if list_stack and list_stack[-1]["type"] == "ordered":
                    list_stack[-1]["index"] += 1
                block_context = None
                in_list_item = False
            elif token.type in {"fence", "code_block"}:
                code_text = token.content.rstrip("\n")
                add_paragraph(f"```\n{code_text}\n```")
            elif token.type == "inline":
                inline_text = token.content.strip()
                if not inline_text:
                    index += 1
                    continue

                if in_list_item and list_stack:
                    current_list = list_stack[-1]
                    if current_list["type"] == "bullet":
                        formatted_text = f"- {inline_text}"
                    else:
                        formatted_text = f"{current_list['index']}. {inline_text}"
                    add_paragraph(formatted_text)
                else:
                    add_paragraph(inline_text)

            index += 1

        return document


