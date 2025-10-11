"""
Unit tests for dataclasses in the RAG system.
"""

from ragora.utils.latex_parser import (
    Citation,
    LatexChapter,
    LatexDocument,
    LatexFigure,
    LatexParagraph,
    LatexSection,
    LatexSubsection,
    LatexSubsubsection,
    LatexTable,
)


class TestCitation:
    """Test Citation dataclass."""

    def test_citation_creation(self, sample_citation):
        """Test basic Citation object creation."""
        assert sample_citation.author == "Einstein, Albert"
        assert sample_citation.year == "1905"
        assert sample_citation.title == "On the Electrodynamics of Moving Bodies"
        assert sample_citation.doi == "10.1002/andp.19053221004"
        assert sample_citation.source_document == "test.tex"
        assert sample_citation.page_reference == "17"
        assert sample_citation.citation_label == "einstein1905"
        assert isinstance(sample_citation.citation_hash, int)

    def test_citation_with_minimal_data(self):
        """Test Citation creation with minimal required data."""
        citation = Citation(
            author="Test Author",
            year="2024",
            title="Test Title",
            doi="",
            source_document="test.tex",
            page_reference="",
            citation_label="test2024",
            citation_hash=12345,
        )

        assert citation.author == "Test Author"
        assert citation.year == "2024"
        assert citation.title == "Test Title"
        assert citation.doi == ""
        assert citation.source_document == "test.tex"
        assert citation.page_reference == ""
        assert citation.citation_label == "test2024"
        assert citation.citation_hash == 12345

    def test_citation_hash_consistency(self):
        """Test that citation hash is consistent for same label."""
        citation1 = Citation(
            author="Author",
            year="2024",
            title="Title",
            doi="",
            source_document="doc.tex",
            page_reference="1",
            citation_label="test",
            citation_hash=hash("test"),
        )
        citation2 = Citation(
            author="Author",
            year="2024",
            title="Title",
            doi="",
            source_document="doc.tex",
            page_reference="1",
            citation_label="test",
            citation_hash=hash("test"),
        )

        assert citation1.citation_hash == citation2.citation_hash


class TestLatexParagraph:
    """Test LatexParagraph dataclass."""

    def test_paragraph_creation_without_citations(self):
        """Test LatexParagraph creation without citations."""
        paragraph = LatexParagraph(content="This is a test paragraph.")

        assert paragraph.content == "This is a test paragraph."
        assert paragraph.citations is None

    def test_paragraph_creation_with_citations(self, sample_citation):
        """Test LatexParagraph creation with citations."""
        citations = [sample_citation]
        paragraph = LatexParagraph(
            content="This paragraph has citations.", citations=citations
        )

        assert paragraph.content == "This paragraph has citations."
        assert len(paragraph.citations) == 1
        assert paragraph.citations[0] == sample_citation

    def test_paragraph_with_multiple_citations(self, sample_citation):
        """Test LatexParagraph with multiple citations."""
        citation2 = Citation(
            author="Newton, Isaac",
            year="1687",
            title="Principia",
            doi="",
            source_document="test.tex",
            page_reference="1",
            citation_label="newton1687",
            citation_hash=hash("newton1687"),
        )

        citations = [sample_citation, citation2]
        paragraph = LatexParagraph(
            content="Multiple citations here.", citations=citations
        )

        assert len(paragraph.citations) == 2
        assert paragraph.citations[0] == sample_citation
        assert paragraph.citations[1] == citation2


class TestLatexTable:
    """Test LatexTable dataclass."""

    def test_table_creation_basic(self):
        """Test basic LatexTable creation."""
        table = LatexTable(
            caption="Test Table",
            label="tab:test",
            headers=["Column 1", "Column 2"],
            rows=[["Value 1", "Value 2"], ["Value 3", "Value 4"]],
        )

        assert table.caption == "Test Table"
        assert table.label == "tab:test"
        assert table.headers == ["Column 1", "Column 2"]
        assert len(table.rows) == 2
        assert table.footnotes is None

    def test_table_creation_with_footnotes(self):
        """Test LatexTable creation with footnotes."""
        footnotes = ["Note 1", "Note 2"]
        table = LatexTable(
            caption="Table with Footnotes",
            label="tab:footnotes",
            headers=["A", "B"],
            rows=[["1", "2"]],
            footnotes=footnotes,
        )

        assert table.footnotes == footnotes
        assert len(table.footnotes) == 2

    def test_table_to_markdown_empty(self):
        """Test table to markdown conversion with empty table."""
        table = LatexTable(
            caption="Empty Table", label="tab:empty", headers=[], rows=[]
        )

        markdown = table.to_markdown()
        expected = "**Table: Empty Table**\n\n"
        assert markdown == expected

    def test_table_to_markdown_with_data(self):
        """Test table to markdown conversion with data."""
        table = LatexTable(
            caption="Sample Table",
            label="tab:sample",
            headers=["Name", "Age"],
            rows=[["Alice", "25"], ["Bob", "30"]],
        )

        markdown = table.to_markdown()
        expected = """**Table: Sample Table**

| Name | Age |
|---|---|
| Alice | 25 |
| Bob | 30 |
"""
        assert markdown == expected

    def test_table_to_plain_text_empty(self):
        """Test table to plain text conversion with empty table."""
        table = LatexTable(
            caption="Empty Table", label="tab:empty", headers=[], rows=[]
        )

        plain_text = table.to_plain_text()
        expected = "Table: Empty Table\n\n"
        assert plain_text == expected

    def test_table_to_plain_text_with_data(self):
        """Test table to plain text conversion with data."""
        table = LatexTable(
            caption="Sample Table",
            label="tab:sample",
            headers=["Name", "Age"],
            rows=[["Alice", "25"], ["Bob", "30"]],
        )

        plain_text = table.to_plain_text()
        expected = """Table: Sample Table
Name | Age
---- | ---
Alice | 25
Bob | 30
"""
        assert plain_text == expected


class TestLatexFigure:
    """Test LatexFigure dataclass."""

    def test_figure_creation(self):
        """Test LatexFigure creation."""
        figure = LatexFigure(
            caption="Sample Figure", label="fig:sample", image_path="/path/to/image.png"
        )

        assert figure.caption == "Sample Figure"
        assert figure.label == "fig:sample"
        assert figure.image_path == "/path/to/image.png"


class TestLatexSubsubsection:
    """Test LatexSubsubsection dataclass."""

    def test_subsubsection_creation_basic(self):
        """Test basic LatexSubsubsection creation."""
        subsubsection = LatexSubsubsection(
            title="Test Subsubsection", label="subsec:test"
        )

        assert subsubsection.title == "Test Subsubsection"
        assert subsubsection.label == "subsec:test"
        assert subsubsection.paragraphs is None

    def test_subsubsection_with_paragraphs(self, sample_citation):
        """Test LatexSubsubsection with paragraphs."""
        paragraph = LatexParagraph(
            content="Test paragraph content.", citations=[sample_citation]
        )

        subsubsection = LatexSubsubsection(
            title="Subsubsection with Content",
            label="subsec:content",
            paragraphs=[paragraph],
        )

        assert len(subsubsection.paragraphs) == 1
        assert subsubsection.paragraphs[0] == paragraph


class TestLatexSubsection:
    """Test LatexSubsection dataclass."""

    def test_subsection_creation_basic(self):
        """Test basic LatexSubsection creation."""
        subsection = LatexSubsection(title="Test Subsection", label="sec:test")

        assert subsection.title == "Test Subsection"
        assert subsection.label == "sec:test"
        assert subsection.paragraphs is None
        assert subsection.subsubsections is None

    def test_subsection_with_content(self, sample_citation):
        """Test LatexSubsection with paragraphs and subsubsections."""
        paragraph = LatexParagraph(
            content="Subsection paragraph.", citations=[sample_citation]
        )

        subsubsection = LatexSubsubsection(
            title="Nested Subsubsection", label="subsec:nested"
        )

        subsection = LatexSubsection(
            title="Subsection with Content",
            label="sec:content",
            paragraphs=[paragraph],
            subsubsections=[subsubsection],
        )

        assert len(subsection.paragraphs) == 1
        assert len(subsection.subsubsections) == 1
        assert subsection.paragraphs[0] == paragraph
        assert subsection.subsubsections[0] == subsubsection


class TestLatexSection:
    """Test LatexSection dataclass."""

    def test_section_creation_basic(self):
        """Test basic LatexSection creation."""
        section = LatexSection(title="Test Section", label="sec:test")

        assert section.title == "Test Section"
        assert section.label == "sec:test"
        assert section.paragraphs is None

    def test_section_with_hierarchy(self, sample_citation):
        """Test LatexSection with full hierarchy."""
        paragraph = LatexParagraph(
            content="Section paragraph.", citations=[sample_citation]
        )

        section = LatexSection(
            title="Section with Hierarchy",
            label="sec:hierarchy",
            paragraphs=[paragraph],
        )

        assert len(section.paragraphs) == 1
        assert section.paragraphs[0] == paragraph


class TestLatexChapter:
    """Test LatexChapter dataclass."""

    def test_chapter_creation_basic(self):
        """Test basic LatexChapter creation."""
        chapter = LatexChapter(title="Test Chapter", label="ch:test")

        assert chapter.title == "Test Chapter"
        assert chapter.label == "ch:test"
        assert chapter.paragraphs is None
        assert chapter.sections is None

    def test_chapter_with_sections(self, sample_citation):
        """Test LatexChapter with sections."""
        paragraph = LatexParagraph(
            content="Chapter paragraph.", citations=[sample_citation]
        )

        section = LatexSection(title="Chapter Section", label="sec:chapter")

        chapter = LatexChapter(
            title="Chapter with Sections",
            label="ch:sections",
            paragraphs=[paragraph],
            sections=[section],
        )

        assert len(chapter.paragraphs) == 1
        assert len(chapter.sections) == 1
        assert chapter.paragraphs[0] == paragraph
        assert chapter.sections[0] == section


class TestLatexDocument:
    """Test LatexDocument dataclass."""

    def test_document_creation_basic(self, sample_latex_document):
        """Test basic LatexDocument creation."""
        assert sample_latex_document.title == "Sample Document"
        assert sample_latex_document.author == "Test Author"
        assert sample_latex_document.year == "2024"
        assert sample_latex_document.doi == ""
        assert sample_latex_document.source_document == "test.tex"
        assert sample_latex_document.page_reference == "1"
        assert sample_latex_document.chapters is None
        assert sample_latex_document.sections is None

    def test_document_with_chapters(self, sample_citation):
        """Test LatexDocument with chapters."""
        paragraph = LatexParagraph(
            content="Document paragraph.", citations=[sample_citation]
        )

        chapter = LatexChapter(
            title="Document Chapter", label="ch:doc", paragraphs=[paragraph]
        )

        document = LatexDocument(
            title="Document with Chapters",
            author="Test Author",
            year="2024",
            doi="",
            source_document="test.tex",
            page_reference="1",
            chapters=[chapter],
        )

        assert len(document.chapters) == 1
        assert document.chapters[0] == chapter

    def test_document_with_sections(self, sample_citation):
        """Test LatexDocument with sections."""
        paragraph = LatexParagraph(
            content="Document section paragraph.", citations=[sample_citation]
        )

        section = LatexSection(
            title="Document Section",
            label="sec:doc",
            paragraphs=[paragraph],
        )

        document = LatexDocument(
            title="Document with Sections",
            author="Test Author",
            year="2024",
            doi="",
            source_document="test.tex",
            page_reference="1",
            sections=[section],
        )

        assert len(document.sections) == 1
        assert document.sections[0] == section

    def test_document_with_tables_and_figures(self):
        """Test LatexDocument with tables and figures."""
        table = LatexTable(
            caption="Document Table",
            label="tab:doc",
            headers=["A", "B"],
            rows=[["1", "2"]],
        )

        figure = LatexFigure(
            caption="Document Figure", label="fig:doc", image_path="/path/to/figure.png"
        )

        document = LatexDocument(
            title="Document with Tables and Figures",
            author="Test Author",
            year="2024",
            doi="",
            source_document="test.tex",
            page_reference="1",
            tables=[table],
            figures=[figure],
        )

        assert len(document.tables) == 1
        assert len(document.figures) == 1
        assert document.tables[0] == table
        assert document.figures[0] == figure
