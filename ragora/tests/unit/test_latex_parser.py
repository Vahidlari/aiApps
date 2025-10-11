"""
Unit tests for the LaTeX parser module.
"""

import tempfile
from pathlib import Path

from ragora.utils.latex_parser import LatexParser


class TestLatexParserInitialization:
    """Test LatexParser initialization."""

    def test_parser_init_without_arguments(self):
        """Test parser initialization without arguments."""
        parser = LatexParser()

        assert parser.document_path is None
        assert parser.bibliography_path is None
        assert parser.bibliography_entries == {}
        assert parser.document is None

    def test_parser_init_with_document_path(self, temp_latex_file):
        """Test parser initialization with document path."""
        parser = LatexParser(document_path=str(temp_latex_file))

        assert parser.document_path == str(temp_latex_file)
        assert parser.bibliography_path is None
        assert parser.bibliography_entries == {}
        assert parser.document is not None

    def test_parser_init_with_bibliography_path(self, temp_bibliography_file):
        """Test parser initialization with bibliography path."""
        parser = LatexParser(bibliography_path=str(temp_bibliography_file))

        assert parser.document_path is None
        assert parser.bibliography_path == str(temp_bibliography_file)
        assert len(parser.bibliography_entries) > 0
        assert parser.document is None

    def test_parser_init_with_both_paths(self, temp_latex_file, temp_bibliography_file):
        """Test parser initialization with both document and bibliography paths."""
        parser = LatexParser(
            document_path=str(temp_latex_file),
            bibliography_path=str(temp_bibliography_file),
        )

        assert parser.document_path == str(temp_latex_file)
        assert parser.bibliography_path == str(temp_bibliography_file)
        assert len(parser.bibliography_entries) > 0
        assert parser.document is not None


class TestBibliographyLoading:
    """Test bibliography loading functionality."""

    def test_load_bibliography_with_valid_file(self, temp_bibliography_file):
        """Test loading bibliography from valid file."""
        parser = LatexParser(bibliography_path=str(temp_bibliography_file))

        assert len(parser.bibliography_entries) == 2
        assert "einstein1905" in parser.bibliography_entries
        assert "newton1687" in parser.bibliography_entries

        einstein = parser.bibliography_entries["einstein1905"]
        assert einstein.author == "Einstein, Albert"
        assert einstein.year == "1905"
        assert einstein.title == "On the Electrodynamics of Moving Bodies"
        assert einstein.doi == "10.1002/andp.19053221004"

    def test_load_bibliography_with_invalid_file(self):
        """Test loading bibliography from invalid file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".bib", delete=False) as f:
            f.write("invalid bibtex content")
            f.flush()
            invalid_path = f.name

        try:
            parser = LatexParser(bibliography_path=invalid_path)
            # Should handle gracefully and return empty dict
            assert parser.bibliography_entries == {}
        finally:
            Path(invalid_path).unlink(missing_ok=True)

    def test_load_bibliography_with_missing_file(self):
        """Test loading bibliography from missing file."""
        parser = LatexParser(bibliography_path="nonexistent.bib")
        assert parser.bibliography_entries == {}

    def test_parse_bibtex_content(self, sample_bibliography_content):
        """Test parsing BibTeX content."""
        parser = LatexParser()
        entries = parser._parse_bibtex(sample_bibliography_content)

        assert len(entries) == 2
        assert "einstein1905" in entries
        assert "newton1687" in entries

        # Test Einstein entry
        einstein = entries["einstein1905"]
        assert einstein.author == "Einstein, Albert"
        assert einstein.year == "1905"
        assert einstein.title == "On the Electrodynamics of Moving Bodies"
        assert einstein.doi == "10.1002/andp.19053221004"
        assert einstein.citation_label == "einstein1905"

        # Test Newton entry
        newton = entries["newton1687"]
        assert newton.author == "Newton, Isaac"
        assert newton.year == "1687"
        assert newton.title == "Philosophiæ Naturalis Principia Mathematica"

    def test_parse_bibtex_with_invalid_content(self):
        """Test parsing invalid BibTeX content."""
        parser = LatexParser()
        invalid_content = "This is not valid BibTeX content"
        entries = parser._parse_bibtex(invalid_content)

        assert entries == {}

    def test_parse_bibtex_with_unsupported_entry_type(self):
        """Test parsing BibTeX with unsupported entry types."""
        parser = LatexParser()
        content = """
@misc{unsupported,
    author = {Test Author},
    title = {Test Title},
    year = {2024}
}

@article{supported,
    author = {Test Author},
    title = {Test Title},
    year = {2024}
}
"""
        entries = parser._parse_bibtex(content)

        # Should only include the article entry, not the misc entry
        assert len(entries) == 1
        assert "supported" in entries
        assert "unsupported" not in entries

    def test_extract_bib_field(self):
        """Test extracting specific fields from BibTeX entries."""
        parser = LatexParser()
        entry = """
@article{test2024,
    author = {Test Author},
    title = {Test Title},
    year = {2024},
    doi = {10.1000/test}
}
"""

        assert parser._extract_bib_field(entry, "author", "Unknown") == "Test Author"
        assert parser._extract_bib_field(entry, "title", "Unknown") == "Test Title"
        assert parser._extract_bib_field(entry, "year", "Unknown") == "2024"
        assert parser._extract_bib_field(entry, "doi", "") == "10.1000/test"
        assert parser._extract_bib_field(entry, "nonexistent", "Default") == "Default"


class TestDocumentParsing:
    """Test document parsing functionality."""

    def test_parse_document_with_valid_file(self, temp_latex_file):
        """Test parsing a valid LaTeX document."""
        parser = LatexParser()
        document = parser.parse_document(str(temp_latex_file))

        assert document is not None
        assert document.title == "Sample Document"
        assert document.author == "Test Author"
        assert document.year == "2024"
        assert len(document.sections) > 2
        assert document.source_document == str(temp_latex_file)

    def test_parse_document_with_valid_file_complex(self, temp_complex_latex_file):
        """Test parsing a valid LaTeX document."""
        parser = LatexParser()
        document = parser.parse_document(str(temp_complex_latex_file))

        assert document is not None
        assert document.title == "Complex Scientific Document"
        assert document.author == "Dr. Jane Smith"
        assert document.year == "2024"
        assert document.source_document == str(temp_complex_latex_file)
        assert len(document.chapters) > 1
        assert len(document.chapters[0].sections) > 2
        assert len(document.chapters[1].sections) > 0
        assert len(document.sections) == 0
        assert len(document.paragraphs) > 0

    def test_parse_document_with_missing_file(self):
        """Test parsing a missing document file."""
        parser = LatexParser()
        document = parser.parse_document("nonexistent.tex")

        assert document is None

    def test_parse_document_text(self, sample_latex_content):
        """Test parsing document from text content."""
        parser = LatexParser()
        document = parser.parse_document_text(sample_latex_content)

        assert document is not None
        assert document.title == "Sample Document"
        assert document.author == "Test Author"
        assert document.year == "2024"
        assert len(document.sections) > 0

    def test_parse_document_text_with_malformed_content(self, malformed_latex_content):
        """Test parsing malformed LaTeX content."""
        parser = LatexParser()
        document = parser.parse_document_text(malformed_latex_content)

        # Should handle gracefully and return a document with available information
        assert document is not None
        assert document.title == "Malformed Document"

    def test_remove_table_figure_environments(self):
        """Test removing table and figure environments."""
        parser = LatexParser()
        text = """
Some text before.

\\begin{table}[h]
\\centering
\\caption{Sample Table}
\\begin{tabular}{|c|c|}
\\hline
A & B \\\\
\\hline
1 & 2 \\\\
\\hline
\\end{tabular}
\\end{table}

Some text after.

\\begin{figure}[h]
\\centering
\\caption{Sample Figure}
\\end{figure}

More text.
"""
        tables, cleaned = parser._parse_tables(text)

        assert "\\begin{table}" not in cleaned
        assert "\\end{table}" not in cleaned
        assert "\\begin{figure}" in cleaned
        assert "\\end{figure}" in cleaned
        assert "Some text before." in cleaned
        assert "Some text after." in cleaned
        assert "More text." in cleaned

    def test_remove_document_preamble(self):
        """Test removing document preamble."""
        parser = LatexParser()
        text = "\\begin{document}\n\\title{Sample Title}\n\\author{Sample Author}\n\\date{2024}\n\\begin{abstract}\nThis is an abstract.\n\\end{abstract}\n\\begin{main}\nThis is the main content.\n\\end{main}\n\\end{document}"
        cleaned = parser._remove_document_preamble(text)
        assert "\\begin{document}" not in cleaned
        assert "\\end{document}" not in cleaned
        assert "Sample Title" in cleaned
        assert "Sample Author" in cleaned
        assert "2024" in cleaned
        assert "This is an abstract." in cleaned
        assert "This is the main content." in cleaned


class TestMetadataExtraction:
    """Test metadata extraction from LaTeX documents."""

    def test_extract_title(self):
        """Test extracting document title."""
        parser = LatexParser()
        text = "\\title{Sample Title}"
        title = parser._extract_title(text)
        assert title == "Sample Title"

    def test_extract_title_not_found(self):
        """Test extracting title when not present."""
        parser = LatexParser()
        text = "No title here"
        title = parser._extract_title(text)
        assert title == ""

    def test_extract_author(self):
        """Test extracting document author."""
        parser = LatexParser()
        text = "\\author{John Doe}"
        author = parser._extract_author(text)
        assert author == "John Doe"

    def test_extract_author_not_found(self):
        """Test extracting author when not present."""
        parser = LatexParser()
        text = "No author here"
        author = parser._extract_author(text)
        assert author == ""

    def test_extract_year(self):
        """Test extracting document year."""
        parser = LatexParser()
        text = "\\date{2024}"
        year = parser._extract_year(text)
        assert year == "2024"

    def test_extract_year_from_date_with_month(self):
        """Test extracting year from date with month."""
        parser = LatexParser()
        text = "\\date{January 2024}"
        year = parser._extract_year(text)
        assert year == "2024"

    def test_extract_year_not_found(self):
        """Test extracting year when not present."""
        parser = LatexParser()
        text = "No date here"
        year = parser._extract_year(text)
        assert year == ""

    def test_extract_doi(self):
        """Test extracting DOI."""
        parser = LatexParser()
        text = "\\doi{10.1000/test}"
        doi = parser._extract_doi(text)
        assert doi == "10.1000/test"

    def test_extract_doi_not_found(self):
        """Test extracting DOI when not present."""
        parser = LatexParser()
        text = "No DOI here"
        doi = parser._extract_doi(text)
        assert doi == ""


class TestChapterParsing:
    """Test chapter parsing functionality."""

    def test_parse_chapters(self, complex_latex_content):
        """Test parsing chapters from LaTeX content."""
        parser = LatexParser()
        chapters, remaining_text = parser._parse_chapters(complex_latex_content)

        assert len(chapters) >= 2  # Should have Introduction and Results chapters
        assert any(chapter.title == "Introduction" for chapter in chapters)
        assert any(chapter.title == "Results" for chapter in chapters)
        assert "\\chapter" not in remaining_text

    def test_parse_single_chapter(self):
        """Test parsing a single chapter."""
        parser = LatexParser()
        chapter_text = """
\\chapter{Test Chapter}
This is the content of the test chapter.
"""
        chapter = parser._parse_single_chapter(chapter_text)

        assert chapter is not None
        assert chapter.title == "Test Chapter"
        assert chapter.paragraphs is not None
        assert len(chapter.paragraphs) > 0

    def test_parse_single_chapter_invalid(self):
        """Test parsing invalid chapter text."""
        parser = LatexParser()
        invalid_text = "This is not a chapter"
        chapter = parser._parse_single_chapter(invalid_text)

        assert chapter is None

    def test_split_into_chapters(self):
        """Test splitting text into chapters."""
        parser = LatexParser()
        text = """
\\chapter{First Chapter}
Content of first chapter.

\\chapter{Second Chapter}
Content of second chapter.
"""
        chapters = parser._split_into_chapters(text)

        assert len(chapters) >= 1
        assert "First Chapter" in chapters[0]
        assert "Content of first chapter." in chapters[0]
        assert "Second Chapter" in chapters[1]
        assert "Content of second chapter." in chapters[1]


class TestSectionParsing:
    """Test section parsing functionality."""

    def test_parse_sections(self, sample_latex_content):
        """Test parsing sections from LaTeX content."""
        parser = LatexParser()

        sections, remaining_text = parser._parse_sections(sample_latex_content)

        assert len(sections) >= 2  # Should have Introduction and Results sections
        assert any(section.title == "Introduction" for section in sections)
        assert any(section.title == "Results" for section in sections)
        assert "\\documentclass" in remaining_text

    def test_parse_single_section(self):
        """Test parsing a single section."""
        parser = LatexParser()
        section_text = """
\\section{Test Section}
This is the content of the test section. 

this is a new paragraph. The paragraph ends here.
"""
        section = parser._parse_single_section(section_text)

        assert section is not None
        assert section.title == "Test Section"
        assert section.paragraphs is not None
        assert len(section.paragraphs) > 1

    def test_parse_single_section_invalid(self):
        """Test parsing invalid section text."""
        parser = LatexParser()
        invalid_text = "This is not a section"
        section = parser._parse_single_section(invalid_text)

        assert section is None

    def test_split_into_sections(self):
        """Test splitting text into sections."""
        parser = LatexParser()
        text = """
\\section{First Section}
Content of first section.

\\section{Second Section}
Content of second section.

\\subsection{Subsection}
Content of subsection.
"""
        sections = parser._split_into_sections(text)

        assert len(sections) >= 2
        assert any("First Section" in section for section in sections)
        assert any("Second Section" in section for section in sections)


class TestParagraphParsing:
    """Test paragraph parsing functionality."""

    def test_parse_paragraphs(self):
        """Test parsing paragraphs from text."""
        parser = LatexParser()
        text = """
This is the first paragraph.

This is the second paragraph.

\\section{Section Title}
This is a paragraph in a section.
"""
        paragraphs = parser._parse_paragraphs(text)

        assert len(paragraphs) >= 2
        assert any("first paragraph" in p.content for p in paragraphs)
        assert any("second paragraph" in p.content for p in paragraphs)

    def test_parse_paragraphs_with_citations(self, temp_bibliography_file):
        """Test parsing paragraphs with citations."""
        parser = LatexParser(bibliography_path=str(temp_bibliography_file))
        text = "This paragraph has a citation \\cite{einstein1905}."

        paragraphs = parser._parse_paragraphs(text)

        assert len(paragraphs) == 1
        paragraph = paragraphs[0]
        assert "einstein1905" in paragraph.content or "Einstein" in paragraph.content
        assert paragraph.citations is not None
        assert len(paragraph.citations) == 1
        assert paragraph.citations[0].citation_label == "einstein1905"


class TestCitationProcessing:
    """Test citation processing functionality."""

    def test_process_citations_in_text(self, temp_bibliography_file):
        """Test processing citations in text."""
        parser = LatexParser(bibliography_path=str(temp_bibliography_file))
        text = "This text has \\cite{einstein1905} and \\citep{newton1687}."

        processed_text, citations = parser._process_citations_in_text(text)

        assert len(citations) == 2
        assert "einstein1905" in [c.citation_label for c in citations]
        assert "newton1687" in [c.citation_label for c in citations]
        assert "\\cite{einstein1905}" not in processed_text
        assert "\\citep{newton1687}" not in processed_text

    def test_get_or_create_citation_existing(self, temp_bibliography_file):
        """Test getting existing citation from bibliography."""
        parser = LatexParser(bibliography_path=str(temp_bibliography_file))
        citation = parser._get_or_create_citation("einstein1905")

        assert citation.citation_label == "einstein1905"
        assert citation.author == "Einstein, Albert"
        assert citation.year == "1905"

    def test_get_or_create_citation_new(self):
        """Test creating new citation when not in bibliography."""
        parser = LatexParser()
        citation = parser._get_or_create_citation("newkey2024")

        assert citation.citation_label == "newkey2024"
        assert citation.author == "Unknown"
        assert citation.year == "Unknown"
        assert citation.title == "Unknown"

    def test_citation_to_text(self, sample_citation):
        """Test formatting citation to text."""
        parser = LatexParser()

        # Test different citation commands
        cite_format = sample_citation.to_text("\\cite")
        assert "Einstein" in cite_format
        assert "1905" in cite_format

        citep_format = sample_citation.to_text("\\citep")
        assert "Einstein" in citep_format
        assert "1905" in citep_format

        citet_format = sample_citation.to_text("\\citet")
        assert "Einstein" in citet_format
        assert "1905" in citet_format


class TestTableParsing:
    """Test table parsing functionality."""

    def test_parse_tables(self, sample_latex_content):
        """Test parsing tables from LaTeX content."""
        parser = LatexParser()
        tables, remaining_text = parser._parse_tables(sample_latex_content)

        assert len(tables) == 1
        table = tables[0]
        assert table.caption == "Sample Table"
        assert table.label == "tab:sample"
        assert len(table.headers) == 2
        assert len(table.rows) == 1
        assert "\\begin{table}" not in remaining_text
        assert "\\end{table}" not in remaining_text

    def test_parse_single_table(self):
        """Test parsing a single table."""
        parser = LatexParser()
        table_text = """
\\begin{table}[h]
\\centering
\\caption{Test Table}
\\label{tab:test}
\\begin{tabular}{|c|c|}
\\hline
Header 1 & Header 2 \\\\
\\hline
Value 1 & Value 2 \\\\
\\hline
\\end{tabular}
\\end{table}
"""
        table = parser._parse_single_table(table_text)

        assert table is not None
        assert table.caption == "Test Table"
        assert table.label == "tab:test"
        assert table.headers == ["Header 1", "Header 2"]
        assert table.rows == [["Value 1", "Value 2"]]

    def test_parse_single_table_invalid(self):
        """Test parsing invalid table text."""
        parser = LatexParser()
        invalid_text = "This is not a table"
        table = parser._parse_single_table(invalid_text)

        assert table is None


class TestFigureParsing:
    """Test figure parsing functionality."""

    def test_parse_figures(self, sample_latex_content):
        """Test parsing figures from LaTeX content."""
        parser = LatexParser()
        figures, remaining_text = parser._parse_figures(sample_latex_content)

        assert len(figures) == 1
        figure = figures[0]
        assert figure.caption == "Sample Figure"
        assert figure.label == "fig:sample"
        assert "\\begin{figure}" not in remaining_text
        assert "\\end{figure}" not in remaining_text

    def test_parse_single_figure(self):
        """Test parsing a single figure."""
        parser = LatexParser()
        figure_text = """
\\begin{figure}[h]
\\centering
\\caption{Test Figure}
\\label{fig:test}
\\includegraphics{test.png}
\\end{figure}
"""
        figure = parser._parse_single_figure(figure_text)

        assert figure is not None
        assert figure.caption == "Test Figure"
        assert figure.label == "fig:test"

    def test_parse_single_figure_invalid(self):
        """Test parsing invalid figure text."""
        parser = LatexParser()
        invalid_text = "This is not a figure"
        figure = parser._parse_single_figure(invalid_text)

        assert figure.caption == ""
        assert figure.label == ""
        assert figure.image_path == ""
