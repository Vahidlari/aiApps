"""
Test utilities and helper functions.
"""

import json
import tempfile
from pathlib import Path
from typing import Any, Dict, List

from ragora.utils.latex_parser import LatexDocument, LatexFigure, LatexTable


def create_temp_latex_file(content: str, suffix: str = ".tex") -> Path:
    """Create a temporary LaTeX file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False) as f:
        f.write(content)
        f.flush()
        return Path(f.name)


def create_temp_bibliography_file(content: str) -> Path:
    """Create a temporary bibliography file for testing."""
    return create_temp_latex_file(content, ".bib")


def cleanup_temp_file(file_path: Path) -> None:
    """Clean up a temporary file."""
    if file_path.exists():
        file_path.unlink(missing_ok=True)


def assert_document_structure(
    document: LatexDocument, expected_sections: int = None
) -> None:
    """Assert basic document structure."""
    assert document is not None
    assert document.title is not None
    assert document.author is not None
    assert document.year is not None

    if expected_sections is not None:
        if document.sections:
            assert len(document.sections) == expected_sections
        elif document.chapters:
            total_sections = sum(
                len(chapter.sections or []) for chapter in document.chapters
            )
            assert total_sections == expected_sections


def assert_table_structure(
    table: LatexTable, expected_headers: int = None, expected_rows: int = None
) -> None:
    """Assert basic table structure."""
    assert table is not None
    assert table.caption is not None
    assert table.label is not None
    assert table.headers is not None
    assert table.rows is not None

    if expected_headers is not None:
        assert len(table.headers) == expected_headers

    if expected_rows is not None:
        assert len(table.rows) == expected_rows


def assert_figure_structure(figure: LatexFigure) -> None:
    """Assert basic figure structure."""
    assert figure is not None
    assert figure.caption is not None
    assert figure.label is not None


def count_citations_in_document(document: LatexDocument) -> int:
    """Count total citations in a document."""
    citation_count = 0

    def count_paragraph_citations(paragraphs):
        nonlocal citation_count
        if paragraphs:
            for paragraph in paragraphs:
                if paragraph.citations:
                    citation_count += len(paragraph.citations)

    # Count in sections
    if document.sections:
        for section in document.sections:
            count_paragraph_citations(section.paragraphs)
            if section.subsections:
                for subsection in section.subsections:
                    count_paragraph_citations(subsection.paragraphs)
                    if subsection.subsubsections:
                        for subsubsection in subsection.subsubsections:
                            count_paragraph_citations(subsubsection.paragraphs)

    # Count in chapters
    if document.chapters:
        for chapter in document.chapters:
            count_paragraph_citations(chapter.paragraphs)
            if chapter.sections:
                for section in chapter.sections:
                    count_paragraph_citations(section.paragraphs)
                    if section.subsections:
                        for subsection in section.subsections:
                            count_paragraph_citations(subsection.paragraphs)
                            if subsection.subsubsections:
                                for subsubsection in subsection.subsubsections:
                                    count_paragraph_citations(subsubsection.paragraphs)

    return citation_count


def extract_all_paragraphs(document: LatexDocument) -> List[str]:
    """Extract all paragraph content from a document."""
    paragraphs = []

    def extract_paragraphs(paragraph_list):
        if paragraph_list:
            for paragraph in paragraph_list:
                paragraphs.append(paragraph.content)

    # Extract from sections
    if document.sections:
        for section in document.sections:
            extract_paragraphs(section.paragraphs)
            if section.subsections:
                for subsection in section.subsections:
                    extract_paragraphs(subsection.paragraphs)
                    if subsection.subsubsections:
                        for subsubsection in subsection.subsubsections:
                            extract_paragraphs(subsubsection.paragraphs)

    # Extract from chapters
    if document.chapters:
        for chapter in document.chapters:
            extract_paragraphs(chapter.paragraphs)
            if chapter.sections:
                for section in chapter.sections:
                    extract_paragraphs(section.paragraphs)
                    if section.subsections:
                        for subsection in section.subsections:
                            extract_paragraphs(subsection.paragraphs)
                            if subsection.subsubsections:
                                for subsubsection in subsection.subsubsections:
                                    extract_paragraphs(subsubsection.paragraphs)

    return paragraphs


def assert_no_latex_commands_in_content(content: str) -> None:
    """Assert that content doesn't contain LaTeX commands."""
    latex_commands = [
        "\\section",
        "\\subsection",
        "\\subsubsection",
        "\\cite",
        "\\citep",
        "\\citet",
        "\\citeauthor",
        "\\citeyear",
        "\\begin{table}",
        "\\end{table}",
        "\\begin{figure}",
        "\\end{figure}",
        "\\label",
        "\\ref",
    ]

    for command in latex_commands:
        assert command not in content, f"Found LaTeX command '{command}' in content"


def load_expected_output(file_path: Path) -> Dict[str, Any]:
    """Load expected output from JSON file."""
    with open(file_path, "r") as f:
        return json.load(f)


def compare_document_with_expected(
    document: LatexDocument, expected: Dict[str, Any]
) -> None:
    """Compare parsed document with expected output."""
    assert document.title == expected["title"]
    assert document.author == expected["author"]
    assert document.year == expected["year"]

    # Compare sections
    if expected.get("sections"):
        assert document.sections is not None
        assert len(document.sections) == len(expected["sections"])

        for i, expected_section in enumerate(expected["sections"]):
            actual_section = document.sections[i]
            assert actual_section.title == expected_section["title"]
            assert actual_section.label == expected_section["label"]

    # Compare tables
    if expected.get("tables"):
        assert document.tables is not None
        assert len(document.tables) == len(expected["tables"])

        for i, expected_table in enumerate(expected["tables"]):
            actual_table = document.tables[i]
            assert actual_table.caption == expected_table["caption"]
            assert actual_table.label == expected_table["label"]
            assert actual_table.headers == expected_table["headers"]
            assert actual_table.rows == expected_table["rows"]

    # Compare figures
    if expected.get("figures"):
        assert document.figures is not None
        assert len(document.figures) == len(expected["figures"])

        for i, expected_figure in enumerate(expected["figures"]):
            actual_figure = document.figures[i]
            assert actual_figure.caption == expected_figure["caption"]
            assert actual_figure.label == expected_figure["label"]


def create_mock_latex_content(
    title: str = "Test Document",
    author: str = "Test Author",
    year: str = "2024",
    sections: List[str] = None,
) -> str:
    """Create mock LaTeX content for testing."""
    if sections is None:
        sections = ["Introduction", "Methodology", "Results", "Conclusion"]

    content = f"""\\documentclass{{article}}
\\title{{{title}}}
\\author{{{author}}}
\\date{{{year}}}

\\begin{{document}}
\\maketitle
"""

    for i, section_title in enumerate(sections, 1):
        content += f"""
\\section{{{section_title}}}
This is the content of section {i}.
"""

    content += """
\\end{document}
"""

    return content


def create_mock_bibliography_content(entries: List[Dict[str, str]] = None) -> str:
    """Create mock bibliography content for testing."""
    if entries is None:
        entries = [
            {
                "key": "test2024",
                "author": "Test Author",
                "title": "Test Title",
                "year": "2024",
                "journal": "Test Journal",
            }
        ]

    content = ""
    for entry in entries:
        content += f"""@article{{{entry['key']},
    author = {{{entry['author']}}},
    title = {{{entry['title']}}},
    journal = {{{entry['journal']}}},
    year = {{{entry['year']}}}
}}

"""

    return content
