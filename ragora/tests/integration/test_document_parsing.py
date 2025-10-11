"""
Integration tests for end-to-end document parsing.
"""

import tempfile
from pathlib import Path

from ragora.utils.latex_parser import LatexParser


class TestEndToEndDocumentParsing:
    """Test complete document parsing workflows."""

    def test_parse_complete_document_with_bibliography(
        self, complex_latex_content, sample_bibliography_content
    ):
        """Test parsing a complete document with bibliography."""
        # Create temporary files
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".tex", delete=False
        ) as tex_file:
            tex_file.write(complex_latex_content)
            tex_file.flush()
            tex_path = tex_file.name

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".bib", delete=False
        ) as bib_file:
            bib_file.write(sample_bibliography_content)
            bib_file.flush()
            bib_path = bib_file.name

        try:
            # Parse document with bibliography
            parser = LatexParser(document_path=tex_path, bibliography_path=bib_path)

            document = parser.document

            # Verify document structure
            assert document is not None
            assert document.title == "Complex Scientific Document"
            assert document.author == "Dr. Jane Smith"
            assert document.year == "2024"

            # Verify chapters
            assert document.chapters is not None
            assert len(document.chapters) == 2

            # Check first chapter
            intro_chapter = document.chapters[0]
            assert intro_chapter.title == "Introduction"
            assert intro_chapter.label == "ch:intro"

            # Check sections in first chapter
            assert intro_chapter.sections is not None
            assert len(intro_chapter.sections) >= 2

            # Check background section
            background_section = None
            related_work = None
            for section in intro_chapter.sections:
                if section.title == "Background":
                    background_section = section
                elif section.title == "Related Work":
                    related_work = section
                if background_section is not None and related_work is not None:
                    break

            assert background_section is not None
            assert background_section.label == "sec:background"
            assert background_section.paragraphs is not None
            assert len(background_section.paragraphs) > 0

            assert related_work is not None
            assert related_work.title == "Related Work"
            assert related_work.label == "subsec:related"

            # Verify citations are processed
            paragraphs_with_citations = [
                p
                for p in background_section.paragraphs
                if p.citations is not None and len(p.citations) > 0
            ]
            assert len(paragraphs_with_citations) > 0

            # Check that citations are properly embedded
            for paragraph in paragraphs_with_citations:
                assert "\\cite{" not in paragraph.content
                assert "\\citep{" not in paragraph.content
                assert "\\citet{" not in paragraph.content

            # Verify tables
            assert document.tables is not None
            assert len(document.tables) == 1

            results_table = document.tables[0]
            assert results_table.caption == "Experimental Results"
            assert results_table.label == "tab:results"
            assert len(results_table.headers) == 3
            assert len(results_table.rows) == 2

            # Verify figures
            assert document.figures is not None
            assert len(document.figures) == 1

            architecture_figure = document.figures[0]
            assert architecture_figure.caption == "System Architecture"
            assert architecture_figure.label == "fig:architecture"

        finally:
            # Cleanup
            Path(tex_path).unlink(missing_ok=True)
            Path(bib_path).unlink(missing_ok=True)

    def test_parse_document_without_bibliography(self, complex_latex_content):
        """Test parsing a document without bibliography."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".tex", delete=False
        ) as tex_file:
            tex_file.write(complex_latex_content)
            tex_file.flush()
            tex_path = tex_file.name

        try:
            parser = LatexParser(document_path=tex_path)
            document = parser.document

            assert document is not None
            assert document.title == "Complex Scientific Document"

            # Citations should still be processed but with placeholder data
            paragraphs_with_citations = []
            for chapter in document.chapters or []:
                for section in chapter.sections or []:
                    for paragraph in section.paragraphs or []:
                        if paragraph.citations:
                            paragraphs_with_citations.extend(paragraph.citations)

            # Should have citations but with placeholder data
            assert len(paragraphs_with_citations) > 0
            for citation in paragraphs_with_citations:
                assert citation.author == "Unknown"
                assert citation.year == "Unknown"
                assert citation.title == "Unknown"

        finally:
            Path(tex_path).unlink(missing_ok=True)

    def test_parse_multiple_documents(
        self, sample_latex_content, complex_latex_content
    ):
        """Test parsing multiple documents sequentially."""
        # Create multiple temporary files
        files = []
        try:
            for i, content in enumerate([sample_latex_content, complex_latex_content]):
                with tempfile.NamedTemporaryFile(
                    mode="w", suffix=f"_{i}.tex", delete=False
                ) as f:
                    f.write(content)
                    f.flush()
                    files.append(f.name)

            # Parse each document
            documents = []
            for file_path in files:
                parser = LatexParser(document_path=file_path)
                documents.append(parser.document)

            # Verify both documents were parsed
            assert len(documents) == 2
            assert documents[0] is not None
            assert documents[1] is not None

            # Verify different document structures
            assert documents[0].title == "Sample Document"
            assert documents[1].title == "Complex Scientific Document"

            # First document should have sections
            assert documents[0].sections is not None
            assert len(documents[0].sections) >= 2

            # Second document should have chapters
            assert documents[1].chapters is not None
            assert len(documents[1].chapters) == 2

        finally:
            for file_path in files:
                Path(file_path).unlink(missing_ok=True)

    def test_parse_document_with_mixed_content(self):
        """Test parsing document with mixed content types."""
        mixed_content = r"""
\documentclass{article}
\title{Mixed Content Document}
\author{Test Author}
\date{2024}

\begin{document}
\maketitle

\section{Introduction}
This section has text with \cite{ref1} citations.

\subsection{Subsection with Table}
Here's a table:

\begin{table}[h]
\centering
\caption{Mixed Content Table}
\label{tab:mixed}
\begin{tabular}{|l|c|}
\hline
Type & Count \\
\hline
Text & 5 \\
Tables & 1 \\
Figures & 2 \\
\hline
\end{tabular}
\end{table}

\subsection{Subsection with Figure}
Here's a figure:

\begin{figure}[h]
\centering
\caption{Mixed Content Figure}
\label{fig:mixed}
\end{figure}

\section{Conclusion}
Final section with more \citep{ref2} citations.
\end{document}
"""

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".tex", delete=False
        ) as tex_file:
            tex_file.write(mixed_content)
            tex_file.flush()
            tex_path = tex_file.name

        try:
            parser = LatexParser(document_path=tex_path)
            document = parser.document

            assert document is not None
            assert document.title == "Mixed Content Document"

            # Verify sections
            assert document.sections is not None
            assert (
                len(document.sections) == 4
            )  # The parser puts all the section, subsections, subsubsections into the sections list

            intro_section = document.sections[0]
            assert intro_section.title == "Introduction"

            # Verify table
            assert document.tables is not None
            assert len(document.tables) == 1
            table = document.tables[0]
            assert table.caption == "Mixed Content Table"
            assert len(table.headers) == 2
            assert len(table.rows) == 3

            # Verify figure
            assert document.figures is not None
            assert len(document.figures) == 1
            figure = document.figures[0]
            assert figure.caption == "Mixed Content Figure"

            # Verify citations are processed
            all_paragraphs = []
            for section in document.sections:
                all_paragraphs.extend(section.paragraphs or [])

            paragraphs_with_citations = [p for p in all_paragraphs if p.citations]
            assert len(paragraphs_with_citations) > 0

        finally:
            Path(tex_path).unlink(missing_ok=True)

    def test_parse_document_error_recovery(self, malformed_latex_content):
        """Test parsing malformed document with error recovery."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".tex", delete=False
        ) as tex_file:
            tex_file.write(malformed_latex_content)
            tex_file.flush()
            tex_path = tex_file.name

        try:
            parser = LatexParser(document_path=tex_path)
            document = parser.document

            # Should handle malformed content gracefully
            assert document is not None
            assert document.title == "Malformed Document"

            # Should still extract what it can
            assert document.sections is not None
            assert len(document.sections) >= 1

            # Should handle unclosed structures
            first_section = document.sections[0]
            assert "Unclosed Section" in first_section.title

        finally:
            Path(tex_path).unlink(missing_ok=True)

    def test_parse_document_performance(self, complex_latex_content):
        """Test parsing performance with larger document."""
        # Create a larger document by repeating content
        large_content = complex_latex_content * 5  # 5x larger

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".tex", delete=False
        ) as tex_file:
            tex_file.write(large_content)
            tex_file.flush()
            tex_path = tex_file.name

        try:
            import time

            start_time = time.time()

            parser = LatexParser(document_path=tex_path)
            document = parser.document

            end_time = time.time()
            processing_time = end_time - start_time

            # Should complete within reasonable time (adjust threshold as needed)
            assert processing_time < 10.0  # 10 seconds max

            # Should still parse correctly
            assert document is not None
            assert document.title == "Complex Scientific Document"

            # Should have more content due to repetition
            assert document.chapters is not None
            assert len(document.chapters) >= 2

        finally:
            Path(tex_path).unlink(missing_ok=True)


class TestParserStateManagement:
    """Test parser state management and reusability."""

    def test_parser_reuse_with_different_documents(
        self, sample_latex_content, complex_latex_content
    ):
        """Test reusing parser instance with different documents."""
        parser = LatexParser()

        # Parse first document
        document1 = parser.parse_document_text(sample_latex_content)
        assert document1 is not None
        assert document1.title == "Sample Document"

        # Parse second document
        document2 = parser.parse_document_text(complex_latex_content)
        assert document2 is not None
        assert document2.title == "Complex Scientific Document"

        # Both documents should be parsed correctly
        assert document1 != document2
        assert document1.title != document2.title

    def test_parser_with_changing_bibliography(self, sample_latex_content):
        """Test parser behavior when bibliography changes."""
        # Create two different bibliography files
        bib1_content = """
@article{ref1,
    author = {Author One},
    title = {Title One},
    year = {2020}
}
"""

        bib2_content = """
@article{ref2,
    author = {Author Two},
    title = {Title Two},
    year = {2021}
}
"""

        with tempfile.NamedTemporaryFile(
            mode="w", suffix="1.bib", delete=False
        ) as bib1_file:
            bib1_file.write(bib1_content)
            bib1_file.flush()
            bib1_path = bib1_file.name

        with tempfile.NamedTemporaryFile(
            mode="w", suffix="2.bib", delete=False
        ) as bib2_file:
            bib2_file.write(bib2_content)
            bib2_file.flush()
            bib2_path = bib2_file.name

        try:
            # Parse with first bibliography
            parser1 = LatexParser(bibliography_path=bib1_path)
            assert len(parser1.bibliography_entries) == 1
            assert "ref1" in parser1.bibliography_entries

            # Parse with second bibliography
            parser2 = LatexParser(bibliography_path=bib2_path)
            assert len(parser2.bibliography_entries) == 1
            assert "ref2" in parser2.bibliography_entries

            # Verify different entries
            assert parser1.bibliography_entries != parser2.bibliography_entries

        finally:
            Path(bib1_path).unlink(missing_ok=True)
            Path(bib2_path).unlink(missing_ok=True)
