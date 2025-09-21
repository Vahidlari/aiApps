"""
Unit tests for DocumentPreprocessor in the RAG system.
"""

from unittest.mock import Mock, patch

import pytest
from ragnarock import DataChunk, DataChunker, DocumentPreprocessor
from ragnarock.utils.latex_parser import (
    LatexChapter,
    LatexDocument,
    LatexParagraph,
    LatexSection,
    LatexTable,
)


class TestDocumentPreprocessor:
    """Test DocumentPreprocessor class."""

    def test_init_default_parameters(self):
        """Test DocumentPreprocessor initialization with default parameters."""
        preprocessor = DocumentPreprocessor()

        assert preprocessor.chunker is not None
        assert isinstance(preprocessor.chunker, DataChunker)
        assert preprocessor.chunker.chunk_size == 768
        assert preprocessor.chunker.overlap_size == 100
        assert preprocessor.latex_parser is not None

    def test_init_custom_parameters(self):
        """Test DocumentPreprocessor initialization with custom parameters."""
        custom_chunker = DataChunker(chunk_size=512, overlap_size=50)
        preprocessor = DocumentPreprocessor(
            chunker=custom_chunker, chunk_size=1024, overlap_size=150
        )

        assert preprocessor.chunker is custom_chunker
        assert preprocessor.chunker.chunk_size == 512
        assert preprocessor.chunker.overlap_size == 50
        assert preprocessor.latex_parser is not None

    def test_init_custom_chunker_only(self):
        """Test DocumentPreprocessor initialization with custom chunker."""
        custom_chunker = DataChunker(chunk_size=256, overlap_size=25)
        preprocessor = DocumentPreprocessor(chunker=custom_chunker)

        assert preprocessor.chunker is custom_chunker
        assert preprocessor.chunker.chunk_size == 256
        assert preprocessor.chunker.overlap_size == 25

    @patch("ragnarock.core.document_preprocessor.LatexParser")
    def test_preprocess_document_success(self, mock_latex_parser_class):
        """Test preprocess_document method with successful parsing."""
        # Setup mocks
        mock_parser = Mock()
        mock_latex_parser_class.return_value = mock_parser

        # Create mock document
        mock_document = LatexDocument(
            title="Test Document",
            author="Test Author",
            year="2024",
            doi="10.1000/test",
            source_document="test.tex",
            page_reference="1-10",
        )
        mock_parser.parse_document.return_value = mock_document

        # Create mock chunks
        expected_chunks = [
            DataChunk(
                text="Test content",
                start_idx=0,
                end_idx=12,
                metadata={"source": "test.tex"},
            )
        ]

        # Mock the chunker
        mock_chunker = Mock()
        mock_chunker.chunk.return_value = expected_chunks

        # Create preprocessor with mocked chunker
        preprocessor = DocumentPreprocessor(chunker=mock_chunker)
        preprocessor.latex_parser = mock_parser

        # Test
        result = preprocessor.preprocess_document("test.tex")

        # Assertions
        mock_parser.parse_document.assert_called_once_with("test.tex")
        mock_chunker.chunk.assert_called_once()
        assert result == expected_chunks

    @patch("ragnarock.core.document_preprocessor.LatexParser")
    def test_preprocess_document_file_not_found(self, mock_latex_parser_class):
        """Test preprocess_document method with file not found."""
        # Setup mocks
        mock_parser = Mock()
        mock_latex_parser_class.return_value = mock_parser
        mock_parser.parse_document.return_value = None

        mock_chunker = Mock()
        mock_chunker.chunk.return_value = []

        preprocessor = DocumentPreprocessor(chunker=mock_chunker)
        preprocessor.latex_parser = mock_parser

        # Test - this should raise an AttributeError since None doesn't have
        # chapters
        with pytest.raises(AttributeError):
            preprocessor.preprocess_document("nonexistent.tex")

    @patch("ragnarock.core.document_preprocessor.LatexParser")
    def test_preprocess_documents_success(self, mock_latex_parser_class):
        """Test preprocess_documents method with multiple files."""
        # Setup mocks
        mock_parser = Mock()
        mock_latex_parser_class.return_value = mock_parser

        # Create mock documents
        mock_doc1 = LatexDocument(
            title="Document 1",
            author="Author 1",
            year="2024",
            doi="10.1000/doc1",
            source_document="doc1.tex",
            page_reference="1-5",
        )
        mock_doc2 = LatexDocument(
            title="Document 2",
            author="Author 2",
            year="2024",
            doi="10.1000/doc2",
            source_document="doc2.tex",
            page_reference="6-10",
        )
        mock_parser.parse_document.side_effect = [mock_doc1, mock_doc2]

        # Create mock chunks
        expected_chunks = [
            DataChunk(
                text="Combined content",
                start_idx=0,
                end_idx=16,
                metadata={"source": "combined"},
            )
        ]

        mock_chunker = Mock()
        mock_chunker.chunk.return_value = expected_chunks

        preprocessor = DocumentPreprocessor(chunker=mock_chunker)
        preprocessor.latex_parser = mock_parser

        # Test
        file_paths = ["doc1.tex", "doc2.tex"]
        result = preprocessor.preprocess_documents(file_paths)

        # Assertions
        assert mock_parser.parse_document.call_count == 2
        mock_parser.parse_document.assert_any_call("doc1.tex")
        mock_parser.parse_document.assert_any_call("doc2.tex")
        mock_chunker.chunk.assert_called_once()
        assert result == expected_chunks

    @patch("ragnarock.core.document_preprocessor.LatexParser")
    def test_preprocess_documents_empty_list(self, mock_latex_parser_class):
        """Test preprocess_documents method with empty file list."""
        mock_parser = Mock()
        mock_latex_parser_class.return_value = mock_parser

        mock_chunker = Mock()
        mock_chunker.chunk.return_value = []

        preprocessor = DocumentPreprocessor(chunker=mock_chunker)
        preprocessor.latex_parser = mock_parser

        # Test
        result = preprocessor.preprocess_documents([])

        # Assertions
        mock_parser.parse_document.assert_not_called()
        mock_chunker.chunk.assert_called_once_with("")
        assert result == []

    @patch("os.listdir")
    @patch("os.path.join")
    @patch("ragnarock.core.document_preprocessor.LatexParser")
    def test_preprocess_document_folder_success(
        self, mock_latex_parser_class, mock_join, mock_listdir
    ):
        """Test preprocess_document_folder method with valid folder."""
        # Setup mocks
        mock_listdir.return_value = ["doc1.tex", "doc2.tex"]
        mock_join.side_effect = lambda folder, file: f"{folder}/{file}"

        mock_parser = Mock()
        mock_latex_parser_class.return_value = mock_parser

        mock_doc1 = LatexDocument(
            title="Document 1",
            author="Author 1",
            year="2024",
            doi="10.1000/doc1",
            source_document="doc1.tex",
            page_reference="1-5",
        )
        mock_doc2 = LatexDocument(
            title="Document 2",
            author="Author 2",
            year="2024",
            doi="10.1000/doc2",
            source_document="doc2.tex",
            page_reference="6-10",
        )
        mock_parser.parse_document.side_effect = [mock_doc1, mock_doc2]

        expected_chunks = [
            DataChunk(
                text="Folder content",
                start_idx=0,
                end_idx=14,
                metadata={"source": "folder"},
            )
        ]

        mock_chunker = Mock()
        mock_chunker.chunk.return_value = expected_chunks

        preprocessor = DocumentPreprocessor(chunker=mock_chunker)
        preprocessor.latex_parser = mock_parser

        # Test
        result = preprocessor.preprocess_document_folder("/test/folder")

        # Assertions
        mock_listdir.assert_called_once_with("/test/folder")
        assert mock_join.call_count == 2
        mock_join.assert_any_call("/test/folder", "doc1.tex")
        mock_join.assert_any_call("/test/folder", "doc2.tex")
        assert mock_parser.parse_document.call_count == 2
        assert result == expected_chunks

    @patch("os.listdir")
    def test_preprocess_document_folder_not_found(self, mock_listdir):
        """Test preprocess_document_folder method with non-existent folder."""
        mock_listdir.side_effect = FileNotFoundError("Folder not found")

        preprocessor = DocumentPreprocessor()

        # Test
        with pytest.raises(FileNotFoundError):
            preprocessor.preprocess_document_folder("/nonexistent/folder")

    def test_extract_document_text_with_chapters(self):
        """Test _extract_document_text method with chapters."""
        # Create mock document with chapters
        chapter1 = LatexChapter(
            title="Chapter 1",
            label="ch1",
            paragraphs=[
                LatexParagraph(content="Chapter 1 paragraph 1"),
                LatexParagraph(content="Chapter 1 paragraph 2"),
            ],
            sections=[
                LatexSection(
                    title="Section 1.1",
                    label="sec1.1",
                    paragraphs=[LatexParagraph(content="Section 1.1 paragraph")],
                )
            ],
        )

        chapter2 = LatexChapter(
            title="Chapter 2",
            label="ch2",
            paragraphs=[LatexParagraph(content="Chapter 2 paragraph")],
        )

        document = LatexDocument(
            title="Test Document",
            author="Test Author",
            year="2024",
            doi="10.1000/test",
            source_document="test.tex",
            page_reference="1-10",
            chapters=[chapter1, chapter2],
        )

        preprocessor = DocumentPreprocessor()
        result = preprocessor._extract_document_text([document])

        expected = (
            "# Chapter 1\n\n"
            "Chapter 1 paragraph 1\n\n"
            "Chapter 1 paragraph 2\n\n"
            "## Section 1.1\n\n"
            "Section 1.1 paragraph\n\n"
            "# Chapter 2\n\n"
            "Chapter 2 paragraph"
        )

        assert result == expected

    def test_extract_document_text_with_sections(self):
        """Test _extract_document_text method with standalone sections."""
        section1 = LatexSection(
            title="Section 1",
            label="sec1",
            paragraphs=[
                LatexParagraph(content="Section 1 paragraph 1"),
                LatexParagraph(content="Section 1 paragraph 2"),
            ],
        )

        section2 = LatexSection(
            title="Section 2",
            label="sec2",
            paragraphs=[LatexParagraph(content="Section 2 paragraph")],
        )

        document = LatexDocument(
            title="Test Document",
            author="Test Author",
            year="2024",
            doi="10.1000/test",
            source_document="test.tex",
            page_reference="1-10",
            sections=[section1, section2],
        )

        preprocessor = DocumentPreprocessor()
        result = preprocessor._extract_document_text([document])

        expected = (
            "## Section 1\n\n"
            "Section 1 paragraph 1\n\n"
            "Section 1 paragraph 2\n\n"
            "## Section 2\n\n"
            "Section 2 paragraph"
        )

        assert result == expected

    def test_extract_document_text_with_paragraphs(self):
        """Test _extract_document_text method with standalone paragraphs."""
        document = LatexDocument(
            title="Test Document",
            author="Test Author",
            year="2024",
            doi="10.1000/test",
            source_document="test.tex",
            page_reference="1-10",
            paragraphs=[
                LatexParagraph(content="Standalone paragraph 1"),
                LatexParagraph(content="Standalone paragraph 2"),
            ],
        )

        preprocessor = DocumentPreprocessor()
        result = preprocessor._extract_document_text([document])

        expected = "Standalone paragraph 1\n\nStandalone paragraph 2"

        assert result == expected

    def test_extract_document_text_with_tables(self):
        """Test _extract_document_text method with tables."""
        table1 = LatexTable(
            caption="Table 1",
            label="tab1",
            headers=["Header 1", "Header 2"],
            rows=[["Row 1 Col 1", "Row 1 Col 2"], ["Row 2 Col 1", "Row 2 Col 2"]],
        )

        table2 = LatexTable(
            caption="Table 2", label="tab2", headers=["A", "B"], rows=[["1", "2"]]
        )

        document = LatexDocument(
            title="Test Document",
            author="Test Author",
            year="2024",
            doi="10.1000/test",
            source_document="test.tex",
            page_reference="1-10",
            tables=[table1, table2],
        )

        preprocessor = DocumentPreprocessor()
        result = preprocessor._extract_document_text([document])

        expected = (
            "Table: Table 1\n"
            "Header 1 | Header 2\n"
            "-------- | --------\n"
            "Row 1 Col 1 | Row 1 Col 2\n"
            "Row 2 Col 1 | Row 2 Col 2\n\n\n"
            "Table: Table 2\n"
            "A | B\n"
            "- | -\n"
            "1 | 2\n"
        )

        assert result == expected

    def test_extract_document_text_empty_document(self):
        """Test _extract_document_text method with empty document."""
        document = LatexDocument(
            title="Empty Document",
            author="Test Author",
            year="2024",
            doi="10.1000/test",
            source_document="empty.tex",
            page_reference="1",
        )

        preprocessor = DocumentPreprocessor()
        result = preprocessor._extract_document_text([document])

        assert result == ""

    def test_extract_document_text_multiple_documents(self):
        """Test _extract_document_text method with multiple documents."""
        doc1 = LatexDocument(
            title="Document 1",
            author="Author 1",
            year="2024",
            doi="10.1000/doc1",
            source_document="doc1.tex",
            page_reference="1-5",
            paragraphs=[LatexParagraph(content="Doc 1 content")],
        )

        doc2 = LatexDocument(
            title="Document 2",
            author="Author 2",
            year="2024",
            doi="10.1000/doc2",
            source_document="doc2.tex",
            page_reference="6-10",
            paragraphs=[LatexParagraph(content="Doc 2 content")],
        )

        preprocessor = DocumentPreprocessor()
        result = preprocessor._extract_document_text([doc1, doc2])

        expected = "Doc 1 content\n\nDoc 2 content"

        assert result == expected

    def test_extract_document_text_mixed_content(self):
        """Test _extract_document_text method with mixed content types."""
        # Create document with chapters, sections, paragraphs, and tables
        chapter = LatexChapter(
            title="Main Chapter",
            label="main",
            paragraphs=[LatexParagraph(content="Chapter paragraph")],
            sections=[
                LatexSection(
                    title="Chapter Section",
                    label="chsec",
                    paragraphs=[LatexParagraph(content="Chapter section paragraph")],
                )
            ],
        )

        standalone_section = LatexSection(
            title="Standalone Section",
            label="standalone",
            paragraphs=[LatexParagraph(content="Standalone section paragraph")],
        )

        standalone_paragraph = LatexParagraph(content="Standalone paragraph")

        table = LatexTable(
            caption="Data Table",
            label="data",
            headers=["X", "Y"],
            rows=[["1", "2"], ["3", "4"]],
        )

        document = LatexDocument(
            title="Mixed Document",
            author="Test Author",
            year="2024",
            doi="10.1000/mixed",
            source_document="mixed.tex",
            page_reference="1-20",
            chapters=[chapter],
            sections=[standalone_section],
            paragraphs=[standalone_paragraph],
            tables=[table],
        )

        preprocessor = DocumentPreprocessor()
        result = preprocessor._extract_document_text([document])

        expected = (
            "# Main Chapter\n\n"
            "Chapter paragraph\n\n"
            "## Chapter Section\n\n"
            "Chapter section paragraph\n\n"
            "## Standalone Section\n\n"
            "Standalone section paragraph\n\n"
            "Standalone paragraph\n\n"
            "Table: Data Table\n"
            "X | Y\n"
            "- | -\n"
            "1 | 2\n"
            "3 | 4\n"
        )

        assert result == expected
